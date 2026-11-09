"""Read-only resume for local single-user EPIS467 trial. No cross-user authorization."""
import hashlib
import re
from .sequence_467 import materials, load_review, LABELS
from .store import RecipeSessionStore


def session_tag(sid):
    return '확인 '+hashlib.sha256(sid.encode()).hexdigest()[:12]


def restore_review(conn, sid, statement_factory=None):
    if not isinstance(sid,str) or not re.fullmatch(r'recipe:[0-9a-fA-F-]{36}',sid):
        raise ValueError('Unsupported trial identity')
    store=RecipeSessionStore(conn,statement_factory)
    saved=0
    for item in materials():
        record=store.load(sid,item['context']['ingredient_id'])
        if record is None:continue
        saved+=1
        state=record['state']
        if state['context']!=item['context'] or state['status'] not in LABELS:
            raise ValueError('Source/state mismatch')
        if len(state['history'])!=record['revision']:
            raise ValueError('History mismatch')
        if state['purchase_candidate'] != (state['status'] in ('CUSTOMER_REPORTED_SHORT','CUSTOMER_REPORTED_ABSENT')):
            raise ValueError('Candidate mismatch')
        if not item['quantity_known'] and state['status'] in ('ASK_SUFFICIENCY','CUSTOMER_REPORTED_ENOUGH','CUSTOMER_REPORTED_SHORT','SUFFICIENCY_UNRESOLVED','SUFFICIENCY_DEFERRED'):
            raise ValueError('Unresolved requirement')
    if not saved:raise ValueError('No saved responses')
    return load_review(store,sid)


def list_saved(conn,statement_factory=None):
    if statement_factory is None:
        from sqlalchemy import text
        statement_factory=text
    rows=conn.execute(statement_factory('''SELECT session_id, MAX(updated_at) AS last_updated
        FROM public.recipe_followup_state
        WHERE session_id LIKE :prefix AND ingredient_id LIKE :ingredient
        GROUP BY session_id ORDER BY MAX(updated_at) DESC,session_id LIMIT 20'''),
        {'prefix':'recipe:%','ingredient':'EPIS:467:%'}).mappings().all()
    result=[]
    for row in rows:
        try:review=restore_review(conn,row['session_id'],statement_factory)
        except (ValueError,KeyError,TypeError):continue
        answered=sum(r['record']['state']['status'] not in ('ASK_PRESENCE','ASK_SUFFICIENCY') for r in review)
        cream=review[1]['record']['state']
        label='{} · {} · 응답 {}/11 · 생크림 {}'.format(session_tag(row['session_id']),row['last_updated'],answered,LABELS[cream['status']])
        result.append(dict(session_id=row['session_id'],label=label,answered=answered,review=review))
    return result
