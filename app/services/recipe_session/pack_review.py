"""Customer-entered single-pack volume; reference planning only."""
from decimal import Decimal, ROUND_CEILING
from .stock_clarify import number

def build_pack(comparison,pack_ml,confirmed):
    if not isinstance(comparison,dict) or comparison.get('status')!='REFERENCE_ONLY':
        raise ValueError('필요량과 참고 비교를 먼저 저장해 주세요.')
    if confirmed is not True:raise ValueError('포장 용량과 재료 종류를 확인해 주세요.')
    capacity=number(pack_ml,Decimal('0.001'),Decimal('1000000'))
    shortage=Decimal(comparison['reference_shortage_ml'])
    count=int((shortage/capacity).to_integral_value(rounding=ROUND_CEILING))
    return dict(status='CUSTOMER_CONFIRMED_REFERENCE_PLAN',pack_ml=str(capacity),pack_count=count,
        total_ml=str(capacity*count),reference_remainder_ml=str(capacity*count-shortage),
        comparison=comparison,customer_confirmed=True,shopping_consent=None)

def validate_pack(value,comparison):
    if not isinstance(value,dict) or value!=build_pack(comparison,value.get('pack_ml'),value.get('customer_confirmed')):
        raise ValueError('포장 수량과 참고 계산 근거가 일치하지 않습니다.')
