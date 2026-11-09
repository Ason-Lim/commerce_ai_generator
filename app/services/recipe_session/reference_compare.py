"""Bounded EPIS467 cream comparison. No app writes, network or implicit cup standard."""
from decimal import Decimal
from .stock_clarify import number,validate_stock


def compare(stock,*,cup_ml=None,assumption_accepted=False,same_liquid_cream_confirmed=False):
    validate_stock(stock,stock.get('stock_note'))
    result=dict(recipe_id='EPIS:467',ingredient_id='EPIS:467:5145',
        requirement_raw='1과1/2컵',requirement_cups='1.5',
        source_cup_basis='UNVERIFIED',available_ml=stock['available_ml'],
        stock_approximate=stock['approximate'],numeric_shortage=None,
        reference_requirement_ml=None,reference_shortage_ml=None,
        updates_customer_judgement=False,shopping_consent=None,
        status='WAITING_FOR_COMPARISON_BASIS')
    if cup_ml is None or assumption_accepted is not True:return result
    cup=number(cup_ml,Decimal('1'),Decimal('2000'))
    if same_liquid_cream_confirmed is not True:
        result['status']='WAITING_FOR_INGREDIENT_AND_STATE_CONFIRMATION';return result
    required=Decimal('1.5')*cup
    shortage=max(Decimal('0'),required-Decimal(stock['available_ml']))
    result.update(status='REFERENCE_ONLY',basis='EXPLICIT_USER_SELECTED_CUP_ASSUMPTION',
        selected_cup_ml=str(cup),reference_requirement_ml=str(required),
        reference_shortage_ml=str(shortage),
        display='1컵={}mL 가정 시 필요 {}mL, 참고 부족량 약 {}mL'.format(format(cup.normalize(),'f'),format(required.normalize(),'f'),format(shortage.normalize(),'f')),
        limits=['This is not the EPIS source cup definition.',
                'Do not mark the original recipe requirement as satisfied from this scenario.',
                'Do not overwrite customer judgement, numeric_shortage or shopping consent.'])
    return result


def validate_comparison(value,stock,item):
    if not isinstance(value,dict) or stock is None:raise ValueError('보유량 확인이 필요합니다.')
    if item['ingredient_id']!='EPIS:467:5145' or item['context'].get('recipe_id')!='EPIS:467' or item['context'].get('requirement_raw')!='생크림 1과1/2컵':
        raise ValueError('이 비교는 EPIS467 생크림에만 적용합니다.')
    expected=compare(stock,cup_ml=value.get('selected_cup_ml'),assumption_accepted=True,same_liquid_cream_confirmed=True)
    expected['stock_confirmation']=stock
    if value!=expected or value.get('status')!='REFERENCE_ONLY':raise ValueError('비교 근거와 계산 결과가 일치하지 않습니다.')


def build_comparison(stock,item,cup_ml,accepted,same_cream):
    value=compare(stock,cup_ml=cup_ml,assumption_accepted=accepted,same_liquid_cream_confirmed=same_cream)
    if value['status']!='REFERENCE_ONLY':raise ValueError('컵 용량 가정과 동일한 액상 생크림 기준을 확인해 주세요.')
    value['stock_confirmation']=stock
    validate_comparison(value,stock,item)
    return value
