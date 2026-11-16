"""Write the theme lookup table and the values the Power BI report must reproduce.

Standard library only. Run from the customer-voice folder:
    python powerbi/build_checks.py
Counts are computed here independently of the DAX in measures.dax.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent


def rows(name):
    with open(ROOT / 'data' / name, encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


customers = {r['customer_id']: r for r in rows('customers.csv')}
invitations = rows('invitations.csv')
responses = rows('responses.csv')
assignments = rows('assignments.csv')
orders = rows('orders.csv')
themes = json.loads((ROOT / 'data' / 'codebook.json').read_text(encoding='utf-8'))['themes']

with open(OUT / 'themes.csv', 'w', encoding='utf-8', newline='') as handle:
    writer = csv.writer(handle, lineterminator='\n')
    writer.writerow(['theme_id', 'theme', 'definition', 'sort_order'])
    for order, theme in enumerate(themes, 1):
        writer.writerow([theme['id'], theme['label'], theme['definition'], order])

checks = []


def add(page, measure, filters, value):
    checks.append([page, measure, filters, value])


schedules = ['Changing schedule', 'Regular schedule']
add('Participation', 'Customers', 'none', len(customers))
add('Participation', 'Invited', 'none', len(invitations))
add('Participation', 'Responded customers', 'none', sum(r['responded'] == '1' for r in invitations))
for schedule in schedules:
    group = [r for r in invitations if customers[r['customer_id']]['schedule'] == schedule]
    responded = sum(r['responded'] == '1' for r in group)
    add('Participation', 'Invited', f'schedule = {schedule}', len(group))
    add('Participation', 'Responded customers', f'schedule = {schedule}', responded)
    add('Participation', 'Response rate', f'schedule = {schedule}', round(responded / len(group), 4))

with_text = [r for r in responses if r['text'].strip()]
price = [r for r in with_text if r['reason'] == 'Too expensive']
add('Themes', 'Responses', 'none', len(responses))
add('Themes', 'Responses with text', 'none', len(with_text))
add('Themes', 'Responses with text', 'reason = Too expensive', len(price))
negative = {}
for a in assignments:
    if a['sentiment'] == 'negative':
        negative.setdefault(a['theme_id'], set()).add(a['response_id'])
for label, group in [('reason = Too expensive', price)] + [
        (f'reason = Too expensive; schedule = {s}',
         [r for r in price if customers[r['customer_id']]['schedule'] == s]) for s in schedules]:
    ids = {r['response_id'] for r in group}
    if label != 'reason = Too expensive':
        add('Themes', 'Responses with text', label, len(ids))
    for theme in themes:
        count = len(negative.get(theme['id'], set()) & ids)
        add('Themes', 'Responses mentioning issue', f"{label}; theme = {theme['label']}", count)
        add('Themes', 'Issue share', f"{label}; theme = {theme['label']}", round(count / len(ids), 4))
    union = (negative.get('delivery_flexibility', set()) | negative.get('pause_control', set())) & ids
    add('Themes', 'Flexibility or pause responses', label, len(union))

late = sum(o['status'] == 'late' for o in orders)
add('Orders', 'Customer weeks', 'none', len(orders))
add('Orders', 'Late weeks', 'none', late)
add('Orders', 'Late week rate', 'none', round(late / len(orders), 4))
add('Orders', 'Customers with a late week', 'none', len({o['customer_id'] for o in orders if o['status'] == 'late'}))
for schedule in schedules:
    group = [o for o in orders if customers[o['customer_id']]['schedule'] == schedule]
    add('Orders', 'Late week rate', f'schedule = {schedule}',
        round(sum(o['status'] == 'late' for o in group) / len(group), 4))
price_customers = {r['customer_id'] for r in price}
group = [o for o in orders if o['customer_id'] in price_customers]
add('Orders', 'Responder customer weeks', 'reason = Too expensive', len(group))
add('Orders', 'Responder late weeks', 'reason = Too expensive', sum(o['status'] == 'late' for o in group))

with open(OUT / 'expected-values.csv', 'w', encoding='utf-8', newline='') as handle:
    writer = csv.writer(handle, lineterminator='\n')
    writer.writerow(['page', 'measure', 'filters', 'expected'])
    writer.writerows(checks)
print(f'{len(checks)} expected values written')
