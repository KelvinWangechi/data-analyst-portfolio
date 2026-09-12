"""Validate model-produced coding before it can enter an analysis.

No inference service is required. Import any provider's JSON through validate().
The transparent keyword baseline is intentionally separate from source labels.
"""
import re

PATTERNS = {
    'affordability': r'\b(budget|afford|expensive|price)\b',
    'value': r'\b(worth|value|waste)\b',
    'delivery_flexibility': r'\b(switch|slot|rota|schedule|thursday|evening)\b',
    'pause_control': r'\b(skip|pause|restart|away)\b',
    'delivery_reliability': r'\b(late|promised|reliable|never came)\b',
    'billing_clarity': r'\b(charge|fee|invoice|checkout)\b',
    'food_quality': r'\b(taste|tasted|fresh|soggy|bland|dry|quality)\b',
    'portion_size': r'\b(portions|small|serving|amount of food)\b',
    'support': r'\b(support|help|replied|reply)\b',
    'packaging': r'\b(lid|plastic|trays|container|packaging|wrapping)\b',
}

def baseline(text):
    return [theme for theme,pattern in PATTERNS.items() if re.search(pattern,text,re.I)]

def validate(text, payload):
    if not isinstance(payload,dict) or set(payload) != {'status','assignments'}:
        raise ValueError('Expected status and assignments only')
    if not isinstance(payload['status'],str) or payload['status'] not in {'coded','needs_review','no_response'}:
        raise ValueError('Unknown coding status')
    if not isinstance(payload['assignments'],list):
        raise ValueError('Assignments must be a list')
    if not text.strip() and payload != {'status':'no_response','assignments':[]}:
        raise ValueError('Empty text must abstain')
    if text.strip() and payload['status']=='no_response':
        raise ValueError('Non-empty text is not a missing response')
    if payload['status']=='coded' and not payload['assignments']:
        raise ValueError('Coded requires evidence')
    seen=set()
    for item in payload['assignments']:
        if not isinstance(item,dict) or set(item) != {'theme_id','evidence_quote','sentiment'}:
            raise ValueError('Invalid assignment schema')
        if not isinstance(item['theme_id'],str) or item['theme_id'] not in PATTERNS or item['theme_id'] in seen:
            raise ValueError('Unknown or repeated theme')
        seen.add(item['theme_id'])
        if not isinstance(item['sentiment'],str) or item['sentiment'] not in {'positive','negative','mixed','neutral','unclear'}:
            raise ValueError('Unknown sentiment')
        q=item['evidence_quote']
        if not isinstance(q,str) or not q.strip() or q not in text:
            raise ValueError('Quote is not an exact source span')
    return payload
