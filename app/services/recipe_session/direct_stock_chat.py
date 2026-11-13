"""Direct remaining quantity; never infers sufficiency, conversions or consent."""
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .flow import open_state
from .store import RevisionConflict


METRIC_UNITS=('mL','g','개')
# 2026-10-30: cups and spoons are stored as said; their size is unknown, so nothing converts or compares them
UNCLEAR_UNITS=('컵','큰술','작은술','숟가락')


def validate_proposal(value, materials, message):
    if not isinstance(value, dict) or set(value) != {'operation','ingredient','amount','unit'}:
        raise ValueError('재료 하나의 이름과 남아 있는 양을 입력해 주세요.')
    if value['operation'] != 'set':
        raise ValueError('이번에는 “생크림 100mL 남았어요”처럼 변경 후 전체 보유량을 입력해 주세요.')
    matches=[m for m in materials if m['name']==value['ingredient']]
    if len(matches)!=1:
        raise ValueError('레시피에 표시된 재료명을 사용해 주세요.')
    if value['ingredient'] not in message:
        raise ValueError('재료명도 함께 입력해 주세요.')
    raw=value['amount']
    if not isinstance(raw,str) or len(raw)>32:
        raise ValueError('수량을 확인해 주세요.')
    try: amount=Decimal(raw)
    except InvalidOperation: raise ValueError('수량을 확인해 주세요.')
    if not amount.is_finite() or not Decimal('0')<=amount<=Decimal('1000000'):
        raise ValueError('수량 범위를 확인해 주세요.')
    unit=value['unit']
    if unit not in METRIC_UNITS+UNCLEAR_UNITS:
        raise ValueError('단위는 mL, g, 개 또는 컵, 큰술, 작은술로 입력해 주세요.')
    return dict(ingredient_id=matches[0]['context']['ingredient_id'],name=matches[0]['name'],
                amount=format(amount,'f'),unit=unit,message=message)


def with_said(proposal, said):
    """Keep the customer's own words for a cup / spoon amount ('반 컵').  Only words that are in the message."""
    if proposal['unit'] in UNCLEAR_UNITS and isinstance(said,str) and 0<len(said)<=20 and said in proposal['message']:
        return dict(proposal,said=said)
    return proposal


def _settings():
    """os.environ first, then the repository .env (same lookup order as before)."""
    import os
    from dotenv import dotenv_values
    root=Path(__file__).resolve().parents[3]
    values=dotenv_values(root/'.env') if (root/'.env').is_file() else {}
    return lambda name: os.environ.get(name) or values.get(name)


def stock_prompt(materials):
    return ('한국어 재료 보유량 입력을 JSON으로 해석한다. 현재 남아 있는 전체 양의 명시적 설정만 set. '
            '추가/정정대상 불명/질문/복합요청/포장비율/단위누락/대략적 수량은 unsupported로 반환. '
            '사용자 문장에 없는 수량이나 단위를 만들지 않는다. 재료명은 다음 목록과 정확히 일치해야 한다: '
            +json.dumps([m['name'] for m in materials],ensure_ascii=False)
            +'. 단위는 mL, g, 개, 컵, 큰술, 작은술, 숟가락 중 하나(반 컵 → amount "0.5", unit "컵"). '
            'JSON 예시: {"operation":"set","ingredient":"생크림","amount":"100","unit":"mL"}. '
            '미지원 예시: {"operation":"unsupported","ingredient":null,"amount":null,"unit":null}')


def interpret(message, materials, client_factory=None):
    get=_settings()
    base=(get('DEEPSEEK_BASE_URL') or '').strip()
    official='https://'+'api.deepseek.com'
    if base.rstrip('/') not in (official,official+'/v1'):
        raise ValueError('DEEPSEEK_BASE_URL 설정을 확인해 주세요.')
    key=get('DEEPSEEK_API_KEY'); model=get('DEEPSEEK_MODEL')
    if not key or not model: raise ValueError('DeepSeek 설정을 확인해 주세요.')
    # Commerce-internal LLMClient (ported from food-nlu); FoodNLU DB dictionaries are not instantiated.
    # No external folder, sys.path change or os.environ mutation.
    from app.services.nlu.llm_client import LLMClient
    env=dict(LLM_PROVIDER='deepseek',DEEPSEEK_API_KEY=key,DEEPSEEK_MODEL=model,DEEPSEEK_BASE_URL=base)
    factory=client_factory or (lambda prompt: LLMClient(prompt,provider='deepseek',env=env,task='stock_chat'))
    value=factory(stock_prompt(materials)).chat_json(message)
    return validate_proposal(value,materials,message)


def save_direct(store,sid,material,proposal,expected_revision):
    record=open_state(store,sid,material['context'])
    if record['revision']!=expected_revision: raise RevisionConflict('Reload required')
    if proposal['ingredient_id']!=material['context']['ingredient_id']: raise ValueError('재료 불일치')
    checked=validate_proposal(dict(operation='set',ingredient=proposal['name'],amount=proposal['amount'],unit=proposal['unit']),[material],proposal['message'])
    stock=dict(amount=checked['amount'],unit=checked['unit'],basis='EXPLICIT_CUSTOMER_CONFIRMED_DIRECT_AMOUNT',raw=checked['message'])
    said=with_said(checked,proposal.get('said')).get('said')
    if said: stock['said']=said
    state=record['state']
    if state.get('direct_stock')==stock: return record['revision']
    state['direct_stock']=stock
    state['history'].append(dict(action='set_direct_stock',stock=stock))
    return store.save(sid,material['context'],state,expected_revision)
