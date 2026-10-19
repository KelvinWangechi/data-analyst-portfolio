"""Restricted public intake adapter for the Power Washing Salesforce playground.

Only enquiry creation and possession-protected read-back receipts are exposed.
Human quote review, customer acceptance and job creation remain in Salesforce.
"""
import datetime as dt
from contextlib import contextmanager
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ORG = '00DQy0000106bxF'
INSTANCE = 'https://empathetic-unicorn-skzy6q-dev-ed.trailblaze.my.salesforce.com'
ORIGIN = 'https://kelvinwangechi.github.io'
VERSION = 'v67.0'
SERVICES = {'House wash', 'Driveway cleaning', 'Gutter cleaning', 'Roof cleaning', 'Commercial wash'}
DATA = Path(os.environ.get('DATA_DIR', '/data'))
BUSINESS_TIMEZONE = ZoneInfo('America/Los_Angeles')


class Problem(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def canonical(body):
    if not isinstance(body, dict) or set(body) - {'submission_id', 'receipt_token', 'customer', 'email', 'address', 'service', 'demo_consent', 'website'}:
        raise Problem(422, 'Unexpected enquiry fields.')
    # Accept the retired checkbox field from cached clients without requiring it.
    if body.get('website', '') != '':
        raise Problem(422, 'Leave the optional website field blank.')
    try:
        submission_id = str(uuid.UUID(body.get('submission_id', '')))
    except (ValueError, TypeError, AttributeError):
        raise Problem(422, 'A valid submission reference is required.')
    token = body.get('receipt_token', '')
    if not isinstance(token, str) or not re.fullmatch(r'[a-f0-9]{64}', token):
        raise Problem(422, 'A valid private receipt key is required.')
    values = {}
    for key, limit in [('customer', 80), ('email', 80), ('address', 255), ('service', 40)]:
        value = body.get(key)
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit or any(ord(c) < 32 for c in value):
            raise Problem(422, 'Check the required name, email, address and service.')
        values[key] = value.strip()
    values['email'] = values['email'].lower()
    if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', values['email']) or values['service'] not in SERVICES:
        raise Problem(422, 'Enter a valid email and select an available service.')
    return submission_id, token, values


class Salesforce:
    def __init__(self, auth_path):
        self.auth_path = Path(auth_path)
        self.access_token = None
        self.lock = threading.Lock()

    def ready(self):
        return self.auth_path.is_file()

    def refresh(self):
        with self.lock:
            try:
                auth = json.loads(self.auth_path.read_text())
                if auth.get('org_id') != ORG or auth.get('instance_url') != INSTANCE:
                    raise ValueError('Wrong org')
                fields = {'grant_type': 'refresh_token', 'client_id': auth['client_id'], 'refresh_token': auth['refresh_token']}
                if auth.get('client_secret'):
                    fields['client_secret'] = auth['client_secret']
                req = urllib.request.Request(INSTANCE + '/services/oauth2/token', data=urllib.parse.urlencode(fields).encode())
                with urllib.request.urlopen(req, timeout=15) as response:
                    token = json.load(response)
                identity_path = urllib.parse.urlsplit(token.get('id', '')).path.strip('/').split('/')
                if len(identity_path) != 3 or identity_path[0] != 'id' or identity_path[1][:15] != ORG:
                    raise ValueError('Unexpected token identity')
                if token.get('refresh_token'):
                    auth['refresh_token'] = token['refresh_token']
                    temporary = self.auth_path.with_suffix('.new')
                    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                    with os.fdopen(descriptor, 'w') as output:
                        json.dump(auth, output)
                    os.replace(temporary, self.auth_path)
                self.access_token = token['access_token']
            except (OSError, ValueError, KeyError, urllib.error.URLError):
                self.access_token = None
                raise Problem(503, 'Salesforce authorization needs the demo owner’s attention. No success has been confirmed.')

    def request(self, method, path, body=None):
        if not path.startswith('/services/data/' + VERSION + '/'):
            raise ValueError('API path outside intake scope')
        for attempt in range(2):
            if not self.access_token:
                self.refresh()
            request = urllib.request.Request(INSTANCE + path, method=method,
                data=json.dumps(body).encode() if body is not None else None,
                headers={'Authorization': 'Bearer ' + self.access_token, 'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                if error.code == 401 and attempt == 0:
                    self.access_token = None
                    continue
                if error.code == 400 and method == 'POST':
                    raise Problem(422, 'Salesforce did not accept this enquiry. Check the demo details, then retry the same submission.')
                raise Problem(503, 'Salesforce could not confirm the request. Retry with the same submission reference.')
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                raise Problem(503, 'The Salesforce response was interrupted. Retry with the same submission reference.')

    def query(self, soql):
        result = self.request('GET', '/services/data/' + VERSION + '/query?' + urllib.parse.urlencode({'q': soql}))
        return result.get('records', [])

    def lookup(self, reference):
        if not re.fullmatch(r'WEB-[a-f0-9]{32}', reference):
            raise ValueError('Unexpected source reference')
        rows = self.query("SELECT Id,Name,Contact__c,Estimator_Task_ID__c,Quote_Status__c,Customer_Accepted__c,Outcome__c FROM Enquiry__c WHERE Source_Enquiry_ID__c = '" + reference + "' LIMIT 1")
        return rows[0] if rows else None

    def create(self, reference, values, name=None):
        today = name[4:14] if name else dt.datetime.now(BUSINESS_TIMEZONE).date().isoformat()
        return self.request('POST', '/services/data/' + VERSION + '/sobjects/Enquiry__c', {
            'Name': name or reference, 'Source_Enquiry_ID__c': reference,
            'Customer_Name__c': values['customer'], 'Email__c': values['email'],
            'Property_Address__c': values['address'], 'Service__c': values['service'],
            'Received_Date__c': today, 'Quote_Status__c': 'Pending', 'Outcome__c': 'Open'})

    def verify(self, enquiry):
        contact, task, job = None, None, None
        if re.fullmatch(r'003[a-zA-Z0-9]{12}(?:[a-zA-Z0-9]{3})?', enquiry.get('Contact__c') or ''):
            rows = self.query("SELECT Id FROM Contact WHERE Id = '" + enquiry['Contact__c'] + "' LIMIT 1")
            contact = rows[0] if rows else None
        task_id = enquiry.get('Estimator_Task_ID__c') or ''
        if re.fullmatch(r'00T[a-zA-Z0-9]{12}(?:[a-zA-Z0-9]{3})?', task_id):
            rows = self.query("SELECT Id,Subject,Status,WhatId,WhoId FROM Task WHERE Id = '" + task_id + "' LIMIT 1")
            task = rows[0] if rows else None
        if task and (task.get('WhatId') != enquiry['Id'] or task.get('WhoId') != enquiry.get('Contact__c')):
            task = None
        rows = self.query("SELECT Id,Status__c FROM Job__c WHERE Enquiry__c = '" + enquiry['Id'] + "' LIMIT 2")
        if len(rows) > 1:
            raise Problem(503, 'The demo owner needs to review the linked-job check.')
        job = rows[0] if rows else None
        return {'enquiry_confirmed': True, 'contact_confirmed': bool(contact), 'estimator_task_confirmed': bool(task),
            'task_status': task.get('Status') if task else None,
            'quote_status': enquiry.get('Quote_Status__c'), 'customer_accepted': bool(enquiry.get('Customer_Accepted__c')),
            'job_created': bool(job), 'job_status': job.get('Status__c') if job else None}


class Intake:
    def __init__(self, folder, salesforce, hourly=5, daily=50):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / 'receipts.sqlite'
        self.sf, self.hourly, self.daily = salesforce, hourly, daily
        self.lock = threading.RLock()
        secret_file = self.folder / 'receipt-secret'
        if not secret_file.exists():
            descriptor = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as output:
                output.write(secrets.token_bytes(32))
        self.secret = secret_file.read_bytes()
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS receipts (submission_id TEXT PRIMARY KEY, reference TEXT UNIQUE NOT NULL, token_hash TEXT NOT NULL, payload_hash TEXT NOT NULL, ip_hash TEXT NOT NULL, created REAL NOT NULL, confirmed INTEGER NOT NULL DEFAULT 0)')
            db.execute('CREATE TABLE IF NOT EXISTS attempts (ip_hash TEXT NOT NULL, created REAL NOT NULL)')
            if 'enquiry_name' not in {row['name'] for row in db.execute('PRAGMA table_info(receipts)')}:
                db.execute('ALTER TABLE receipts ADD COLUMN enquiry_name TEXT')
            db.execute('CREATE TABLE IF NOT EXISTS daily_sequence (day TEXT PRIMARY KEY, value INTEGER NOT NULL)')
        os.chmod(self.path, 0o600)

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def digest(self, value):
        return hmac.new(self.secret, value.encode(), hashlib.sha256).hexdigest()

    def throttle(self, ip):
        key, now = self.digest('ip:' + ip), time.time()
        with self.db() as db:
            db.execute('DELETE FROM attempts WHERE created < ?', (now - 3600,))
            count = db.execute('SELECT count(*) FROM attempts WHERE ip_hash = ? AND created > ?', (key, now - 60)).fetchone()[0]
            if count >= 30:
                raise Problem(429, 'Please wait a minute before checking this demo again.')
            db.execute('INSERT INTO attempts VALUES (?, ?)', (key, now))

    def receipt(self, submission_id, token):
        try:
            submission_id = str(uuid.UUID(submission_id))
        except (ValueError, TypeError, AttributeError):
            raise Problem(404, 'Receipt not found.')
        with self.db() as db:
            row = db.execute('SELECT * FROM receipts WHERE submission_id=?', (submission_id,)).fetchone()
        if not row or not hmac.compare_digest(row['token_hash'], self.digest('receipt:' + token)):
            raise Problem(404, 'Receipt not found.')
        enquiry = self.sf.lookup(row['reference'])
        if not enquiry:
            return {'reference': row['enquiry_name'] or row['reference'], 'status': 'awaiting_salesforce_confirmation', 'enquiry_confirmed': False}
        verified = self.sf.verify(enquiry)
        with self.db() as db:
            db.execute('UPDATE receipts SET confirmed=1 WHERE submission_id=?', (submission_id,))
        return dict(verified, reference=enquiry.get('Name') or row['enquiry_name'] or row['reference'], status='handoff_confirmed' if verified['contact_confirmed'] and verified['estimator_task_confirmed'] else 'handoff_pending',
            checked_at=dt.datetime.now(dt.timezone.utc).isoformat(), verification_source='Salesforce REST read-back',
            flow='Cleaning_Enquiry_Handoff', approval_location='Salesforce')

    def submit(self, body, ip):
        submission_id, token, values = canonical(body)
        if not self.sf.ready():
            raise Problem(503, 'Live Salesforce intake is not enabled yet. No enquiry has been confirmed.')
        fingerprint = self.digest(json.dumps(values, sort_keys=True))
        with self.lock:
            with self.db() as db:
                row = db.execute('SELECT * FROM receipts WHERE submission_id=?', (submission_id,)).fetchone()
                if row:
                    if not hmac.compare_digest(row['token_hash'], self.digest('receipt:' + token)):
                        raise Problem(404, 'Receipt not found.')
                    if not hmac.compare_digest(row['payload_hash'], fingerprint):
                        raise Problem(409, 'This reference belongs to different details. Start a new demo enquiry to change them.')
                else:
                    now, ip_hash = time.time(), self.digest('ip:' + ip)
                    hour_count = db.execute('SELECT count(*) FROM receipts WHERE ip_hash=? AND created>?', (ip_hash, now - 3600)).fetchone()[0]
                    day_count = db.execute('SELECT count(*) FROM receipts WHERE created>?', (now - 86400,)).fetchone()[0]
                    if hour_count >= self.hourly or day_count >= self.daily:
                        raise Problem(429, 'The demo intake limit has been reached. Please try again later.')
                    reference = 'WEB-' + uuid.UUID(submission_id).hex
                    day = dt.datetime.now(BUSINESS_TIMEZONE).date().isoformat()
                    db.execute('INSERT INTO daily_sequence VALUES (?,1) ON CONFLICT(day) DO UPDATE SET value=value+1', (day,))
                    sequence = db.execute('SELECT value FROM daily_sequence WHERE day=?', (day,)).fetchone()[0]
                    name = f'enq-{day}-{sequence:03d}'
                    db.execute('INSERT INTO receipts (submission_id,reference,token_hash,payload_hash,ip_hash,created,confirmed,enquiry_name) VALUES (?,?,?,?,?,?,0,?)', (submission_id, reference, self.digest('receipt:' + token), fingerprint, ip_hash, now, name))
                    row = {'reference': reference, 'enquiry_name': name}
            enquiry = self.sf.lookup(row['reference'])
            if not enquiry:
                try:
                    self.sf.create(row['reference'], values, row['enquiry_name'])
                except Problem:
                    # A lost response may hide a committed creation: read it back
                    # before reporting failure. The Salesforce external ID is unique.
                    if not self.sf.lookup(row['reference']):
                        raise
            result = self.receipt(submission_id, token)
            result['replayed'] = bool(enquiry)
            return result


class Handler(BaseHTTPRequestHandler):
    server_version = 'CleaningIntake'

    def log_message(self, *args):
        pass  # Do not write enquiry details, receipt keys or request paths to logs.

    def send_json(self, code, body):
        encoded = json.dumps(body).encode()
        self.send_response(code)
        if self.headers.get('Origin') == ORIGIN:
            self.send_header('Access-Control-Allow-Origin', ORIGIN)
            self.send_header('Vary', 'Origin')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):
        if self.headers.get('Origin') != ORIGIN:
            return self.send_json(403, {'error': 'Origin not allowed.'})
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', ORIGIN)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '600')
        self.end_headers()

    def handle_api(self):
        try:
            self.connection.settimeout(20)
            path = urllib.parse.urlsplit(self.path).path
            if self.command == 'GET' and path == '/health':
                return self.send_json(200, {'service': 'cleaning-live-intake', 'configured': self.server.intake.sf.ready()})
            if self.headers.get('Origin') not in (None, ORIGIN):
                raise Problem(403, 'Origin not allowed.')
            ip = (self.headers.get('X-Forwarded-For') or self.client_address[0]).split(',')[-1].strip()
            try:
                ip = str(ipaddress.ip_address(ip))
            except ValueError:
                raise Problem(400, 'Invalid client address.')
            self.server.intake.throttle(ip)
            if self.command == 'GET' and path.startswith('/v1/receipts/'):
                authorization = self.headers.get('Authorization', '')
                if not re.fullmatch(r'Bearer [a-f0-9]{64}', authorization):
                    raise Problem(404, 'Receipt not found.')
                return self.send_json(200, self.server.intake.receipt(path.rsplit('/', 1)[-1], authorization[7:]))
            if self.command == 'POST' and path == '/v1/enquiries':
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise Problem(415, 'JSON content is required.')
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                except ValueError:
                    raise Problem(400, 'Invalid request size.')
                if not 1 <= length <= 8192:
                    raise Problem(413, 'Enquiry is too large.')
                try:
                    body = json.loads(self.rfile.read(length))
                except (ValueError, UnicodeDecodeError):
                    raise Problem(400, 'Invalid JSON request.')
                return self.send_json(200, self.server.intake.submit(body, ip))
            raise Problem(404, 'Endpoint not found.')
        except Problem as error:
            self.send_json(error.status, {'error': error.message})
        except Exception:
            self.send_json(503, {'error': 'Live intake could not be confirmed. Keep your reference and retry.'})

    do_GET = handle_api
    do_POST = handle_api


if __name__ == '__main__':
    os.umask(0o077)
    sf = Salesforce(os.environ.get('SF_AUTH_FILE', str(DATA / 'salesforce-auth.json')))
    service = ThreadingHTTPServer(('0.0.0.0', 8080), Handler)
    service.intake = Intake(DATA, sf)
    print('Cleaning live intake adapter started. Credentials and submission contents are not logged.', flush=True)
    service.serve_forever()
