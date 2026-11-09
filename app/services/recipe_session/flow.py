"""Bounded ingredient-presence flow, no numeric conversions or shopping calls."""
from copy import deepcopy
from .store import context_key, RevisionConflict

CASES = {
    'RC089': dict(recipe_id='RC089', recipe_version='uploaded-evidence-v1',
                  servings='source_unspecified', ingredient_id='coin_filefish',
                  requirement_raw='동전쥐포 200g', evidence_raw='[재료] 동전쥐포 200g'),
    'RC067': dict(recipe_id='RC067', recipe_version='uploaded-evidence-v1',
                  servings='source_unspecified', ingredient_id='green_onion',
                  requirement_raw='대파 초록 부분, 손가락 길이 2~3개',
                  evidence_raw='대파 초록부분\x072-3\x07개\x07(손가락 길이)'),
}
# RC identifiers are pilot candidate identifiers, not verified recipe identifiers.

def fresh(session_id, context):
    context_key(context)
    return dict(session_id=session_id, context=deepcopy(context),
                status='ASK_PRESENCE', customer_observation=None, history=[],
                numeric_shortage=None, conversion=None, shopping_consent=None,
                shopping_dispatch=0, api_calls=0, purchase_candidate=False)

def transition(state, action):
    result=deepcopy(state)
    status=state['status']
    allowed={'ASK_PRESENCE': {'have','none','unknown','skip'},
             'ASK_SUFFICIENCY': {'enough','short','unknown','skip'}}
    if action == 'recheck':
        if status in allowed:
            raise ValueError('Question already open')
        result=fresh(state['session_id'],state['context'])
        result['history']=deepcopy(state['history'])
    elif action not in allowed.get(status,set()):
        raise ValueError('Invalid or stale action')
    elif status=='ASK_PRESENCE':
        result['customer_observation']=dict(presence=action, sufficiency=None,
                                             basis='EXPLICIT_CUSTOMER_SELECTION')
        result['status']={'have':'ASK_SUFFICIENCY','none':'CUSTOMER_REPORTED_ABSENT',
                          'unknown':'PRESENCE_UNRESOLVED','skip':'PRESENCE_DEFERRED'}[action]
        result['purchase_candidate']=action=='none'
    else:
        result['customer_observation']['sufficiency']=action
        result['status']={'enough':'CUSTOMER_REPORTED_ENOUGH','short':'CUSTOMER_REPORTED_SHORT',
                          'unknown':'SUFFICIENCY_UNRESOLVED','skip':'SUFFICIENCY_DEFERRED'}[action]
        result['purchase_candidate']=action=='short'
    result['history'].append(dict(action=action, previous_status=status,
                                  previous_observation=deepcopy(state['customer_observation'])))
    return result

def open_state(store,session_id,context):
    record=store.load(session_id,context['ingredient_id'])
    if record is None:
        return dict(state=fresh(session_id,context),revision=0)
    if record['state']['context']==context:
        return record
    old=record['state']
    state=fresh(session_id,context)
    state['history']=deepcopy(old.get('history',[]))+[
        dict(action='context_changed',previous_context=old['context'],
             previous_observation=old.get('customer_observation'))]
    return dict(state=state, revision=record['revision'])

def apply_action(store,session_id,context,action,expected_revision):
    record=open_state(store,session_id,context)
    if record['revision']!=expected_revision:
        raise RevisionConflict('Reload before applying this action')
    state=transition(record['state'],action)
    revision=store.save(session_id,context,state,expected_revision)
    return dict(state=state,revision=revision)
