"""EPIS 467 snapshot-bound material review; no inferred quantity or state."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from .flow import open_state,transition
from .store import RevisionConflict

def recipe():
    return json.loads(Path(__file__).with_name('recipe_467.json').read_text(encoding='utf-8'))

def materials():
    source=recipe()
    version=hashlib.sha256(json.dumps(source,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    result=[]
    for item in source['ingredients']:
        result.append(dict(name=item['IRDNT_NM'],quantity=item['IRDNT_CPCTY'],
            source_kind='ingredient_table',source_role=item['IRDNT_TY_NM'],
            quantity_known=True,context=dict(recipe_id='EPIS:467',recipe_version=version,
            servings=source['basic']['QNT'],ingredient_id='EPIS:467:'+item['IRDNT_SN'],
            requirement_raw=item['IRDNT_NM']+' '+item['IRDNT_CPCTY'],
            evidence_raw=json.dumps(item,ensure_ascii=False,sort_keys=True))))
    # Explicit review of this snapshot's table/process inconsistency.
    for name,number in [('바질','3'),('식용유','4')]:
        step=next(s for s in source['steps'] if s['COOKING_NO']==number)
        if name not in step['COOKING_DC']:raise ValueError('Step evidence changed')
        quantity='조리 과정에 약간 표기 · 재료표 미기재' if name=='식용유' else '재료표·조리 과정에 분량 없음'
        result.append(dict(name=name,quantity=quantity,quantity_known=False,
            source_kind='step_only',source_role='과정에서만 확인',
            context=dict(recipe_id='EPIS:467',recipe_version=version,servings=source['basic']['QNT'],
            ingredient_id='EPIS:467:step:'+number+':'+name,
            requirement_raw=name+' — 재료표 분량 미확인',evidence_raw=step['COOKING_DC'])))
    return result

LABELS={'ASK_PRESENCE':'보유 여부 확인 전','ASK_SUFFICIENCY':'충분 여부 확인 중',
        'CUSTOMER_REPORTED_ENOUGH':'고객 판단: 충분', 'CUSTOMER_REPORTED_SHORT':'고객 판단: 부족',
        'CUSTOMER_REPORTED_ABSENT':'미보유','PRESENCE_UNRESOLVED':'보유 여부 미확인',
        'PRESENCE_DEFERRED':'보유 확인 보류','SUFFICIENCY_UNRESOLVED':'충분 여부 미확인',
        'SUFFICIENCY_DEFERRED':'충분 여부 확인 보류',
        'REQUIREMENT_UNRESOLVED':'보유 중 · 필요 분량 미확인'}

def load_review(store,sid):
    return [dict(material=m,record=open_state(store,sid,m['context'])) for m in materials()]

def next_pending(review):
    return next((i for i,r in enumerate(review) if r['record']['state']['status'] in
                 ('ASK_PRESENCE','ASK_SUFFICIENCY')),None)

def apply(store,sid,item,action,revision):
    record=open_state(store,sid,item['context'])
    if record['revision']!=revision:raise RevisionConflict('Reload required')
    if not item['quantity_known'] and action in ('enough','short'):
        raise ValueError('Required quantity is unresolved')
    state=transition(record['state'],action)
    if not item['quantity_known'] and action=='have':
        state['status']='REQUIREMENT_UNRESOLVED'
        state['purchase_candidate']=False
    return dict(state=state,revision=store.save(sid,item['context'],state,revision))

def summary(review):
    return [dict(재료=r['material']['name'],원문분량=r['material']['quantity'],
                 출처구분='재료표' if r['material']['quantity_known'] else '조리 과정 추가 확인',
                 확인상태=LABELS[r['record']['state']['status']],
                 구매검토후보='예' if r['record']['state']['purchase_candidate'] else '아니요')
            for r in review]
