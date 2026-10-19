import concurrent.futures
import copy
import tempfile
import unittest
import uuid
import datetime as dt
import time
from unittest.mock import patch
from app import Intake, Problem, Salesforce, canonical, BUSINESS_TIMEZONE


class FakeSalesforce:
    def __init__(self):
        self.rows = {}
        self.creates = 0
        self.enabled = True
        self.interrupt_after_commit = False

    def ready(self):
        return self.enabled

    def lookup(self, reference):
        return self.rows.get(reference)

    def create(self, reference, values, name=None):
        self.creates += 1
        self.rows[reference] = {'Id': 'a00Qy0000000001AAA', 'Name': name or reference}
        if self.interrupt_after_commit:
            raise Problem(503, 'Lost response')

    def verify(self, enquiry):
        return {'enquiry_confirmed': True, 'contact_confirmed': True, 'estimator_task_confirmed': True,
            'quote_status': 'Pending', 'customer_accepted': False, 'job_created': False, 'job_status': None}


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.sf = FakeSalesforce()
        self.api = Intake(self.temp.name, self.sf, hourly=2, daily=3)
        self.body = {'submission_id': str(uuid.uuid4()), 'receipt_token': 'a' * 64, 'customer': 'Alex Demo',
            'email': 'alex@example.test', 'address': '26 Example Lane', 'service': 'House wash', 'website': ''}

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_submission_proves_handoff_and_keeps_approval_pending(self):
        result = self.api.submit(self.body, '192.0.2.1')
        self.assertEqual(result['status'], 'handoff_confirmed')
        self.assertEqual(result['quote_status'], 'Pending')
        self.assertFalse(result['job_created'])
        self.assertFalse(result['replayed'])
        self.assertEqual(result['verification_source'], 'Salesforce REST read-back')
        self.assertNotIn('a00Qy', str(result))

    def test_concurrent_replays_create_one_salesforce_enquiry(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.api.submit(self.body, '192.0.2.1'), range(4)))
        self.assertEqual(self.sf.creates, 1)
        self.assertEqual(len({r['reference'] for r in results}), 1)
        self.assertEqual(sum(r['replayed'] for r in results), 3)

    def test_daily_names_increment_once_and_survive_restart(self):
        first = self.api.submit(self.body, '192.0.2.1')
        self.assertRegex(first['reference'], r'^enq-\d{4}-\d{2}-\d{2}-001$')
        restarted = Intake(self.temp.name, self.sf, hourly=2, daily=3)
        replay = restarted.submit(self.body, '192.0.2.1')
        self.assertEqual(replay['reference'], first['reference'])
        second = restarted.submit(dict(self.body, submission_id=str(uuid.uuid4())), '192.0.2.1')
        self.assertEqual(second['reference'], first['reference'][:-3] + '002')

    def test_business_timezone_observes_los_angeles_daylight_saving(self):
        summer = dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc).astimezone(BUSINESS_TIMEZONE)
        winter = dt.datetime(2026, 12, 1, tzinfo=dt.timezone.utc).astimezone(BUSINESS_TIMEZONE)
        self.assertEqual(summer.utcoffset(), dt.timedelta(hours=-7))
        self.assertEqual(winter.utcoffset(), dt.timedelta(hours=-8))

    def test_daily_counter_resets_at_los_angeles_midnight(self):
        real_datetime = dt.datetime
        class Clock(real_datetime):
            instant = real_datetime(2026, 10, 20, 6, 59, tzinfo=dt.timezone.utc)
            @classmethod
            def now(cls, tz=None):
                return cls.instant.astimezone(tz)
        with patch('app.dt.datetime', Clock):
            first = self.api.submit(self.body, '192.0.2.1')
            Clock.instant = real_datetime(2026, 10, 20, 7, 0, tzinfo=dt.timezone.utc)
            second = self.api.submit(dict(self.body, submission_id=str(uuid.uuid4())), '192.0.2.1')
        self.assertEqual(first['reference'], 'enq-2026-10-19-001')
        self.assertEqual(second['reference'], 'enq-2026-10-20-001')

    def test_response_lost_after_commit_is_read_back_without_second_creation(self):
        self.sf.interrupt_after_commit = True
        result = self.api.submit(self.body, '192.0.2.1')
        self.assertTrue(result['enquiry_confirmed'])
        self.api.submit(self.body, '192.0.2.1')
        self.assertEqual(self.sf.creates, 1)

    def test_receipts_require_the_original_private_key(self):
        self.api.submit(self.body, '192.0.2.1')
        with self.assertRaises(Problem) as error:
            self.api.receipt(self.body['submission_id'], 'b' * 64)
        self.assertEqual(error.exception.status, 404)

    def test_replay_with_changed_details_is_refused(self):
        self.api.submit(self.body, '192.0.2.1')
        changed = dict(self.body, address='Another property')
        with self.assertRaises(Problem) as error:
            self.api.submit(changed, '192.0.2.1')
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(self.sf.creates, 1)

    def test_privileged_or_invalid_fields_cannot_reach_salesforce(self):
        for changes in [{'quote_status': 'Approved'}, {'email': 'invalid'}, {'service': 'arbitrary'}, {'address': ''}, {'website': 'spam'}]:
            with self.subTest(changes=changes), self.assertRaises(Problem):
                self.api.submit(dict(self.body, **changes), '192.0.2.1')
        self.assertEqual(self.sf.creates, 0)

    def test_disabled_integration_never_returns_success(self):
        self.sf.enabled = False
        with self.assertRaises(Problem) as error:
            self.api.submit(self.body, '192.0.2.1')
        self.assertEqual(error.exception.status, 503)
        self.assertEqual(self.sf.creates, 0)

    def test_limits_allow_replay_but_refuse_new_submissions(self):
        for _ in range(2):
            item = dict(self.body, submission_id=str(uuid.uuid4()))
            self.api.submit(item, '192.0.2.1')
        self.api.submit(item, '192.0.2.1')
        with self.assertRaises(Problem) as error:
            self.api.submit(dict(self.body, submission_id=str(uuid.uuid4())), '192.0.2.1')
        self.assertEqual(error.exception.status, 429)

    def test_hourly_reset_preserves_receipts_and_daily_sequence(self):
        first = self.api.submit(self.body, '192.0.2.1')
        self.api.submit(dict(self.body, submission_id=str(uuid.uuid4())), '192.0.2.1')
        with self.api.db() as db:
            db.execute("INSERT INTO quota_resets VALUES ('hourly', ?)", (time.time(),))
        third = self.api.submit(dict(self.body, submission_id=str(uuid.uuid4())), '192.0.2.1')
        self.assertTrue(third['reference'].endswith('-003'))
        replay = self.api.submit(self.body, '192.0.2.1')
        self.assertEqual(replay['reference'], first['reference'])
        self.assertTrue(replay['replayed'])
        with self.api.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM receipts').fetchone()[0], 3)
        with self.assertRaises(Problem) as error:
            self.api.submit(dict(self.body, submission_id=str(uuid.uuid4())), '192.0.2.1')
        self.assertEqual(error.exception.status, 429)  # Daily protection still applies.

    def test_database_keeps_hashes_not_customer_details_or_receipt_key(self):
        self.api.submit(self.body, '192.0.2.1')
        with self.api.db() as db:
            values = str([tuple(row) for row in db.execute('SELECT * FROM receipts')])
        for value in ['Alex Demo', 'alex@example.test', '26 Example Lane', self.body['receipt_token'], '192.0.2.1']:
            self.assertNotIn(value, values)

    def test_read_back_must_verify_task_relationships(self):
        sf = Salesforce('unused')
        enquiry = {'Id': 'a00Qy0000000001AAA', 'Contact__c': '003Qy0000000001AAA',
            'Estimator_Task_ID__c': '00TQy0000000001AAA', 'Quote_Status__c': 'Pending'}
        def query(sql):
            if 'FROM Contact' in sql:
                return [{'Id': enquiry['Contact__c']}]
            if 'FROM Task' in sql:
                return [{'Id': enquiry['Estimator_Task_ID__c'], 'WhatId': 'wrong', 'WhoId': enquiry['Contact__c']}]
            return []
        sf.query = query
        result = sf.verify(enquiry)
        self.assertTrue(result['contact_confirmed'])
        self.assertFalse(result['estimator_task_confirmed'])


if __name__ == '__main__':
    unittest.main()
