"""Explicit customer-confirmed container volume only. Bounded note suggestions; no cup conversion."""
from decimal import Decimal,InvalidOperation


def number(raw,minimum,maximum):
    if not isinstance(raw,str) or len(raw)>32:raise ValueError('숫자를 입력해 주세요.')
    try:value=Decimal(raw.strip())
    except InvalidOperation:raise ValueError('숫자를 입력해 주세요.')
    if not value.is_finite() or not minimum<=value<=maximum:raise ValueError('입력 범위를 확인해 주세요.')
    return value


def build_stock(note,container_ml,remaining_percent,approximate,confirmed):
    if confirmed is not True:raise ValueError('포장 전체 용량과 남은 비율을 확인해 주세요.')
    if not isinstance(note,str) or not note.strip() or len(note)>300:raise ValueError('보유량 메모를 먼저 저장해 주세요.')
    if type(approximate) is not bool:raise ValueError('추정 여부를 확인해 주세요.')
    capacity=number(container_ml,Decimal('0.001'),Decimal('1000000'))
    percentage=number(remaining_percent,Decimal('0'),Decimal('100'))
    amount=capacity*percentage/Decimal('100')
    return dict(basis='EXPLICIT_CUSTOMER_CONFIRMED_CONTAINER_FRACTION',stock_note=note,
        container_ml=str(capacity),remaining_percent=str(percentage),available_ml=str(amount),
        approximate=approximate,customer_confirmed=True,numeric_shortage=None)


def validate_stock(value,note):
    if not isinstance(value,dict):raise ValueError('Invalid confirmation')
    expected=build_stock(note,value.get('container_ml'),value.get('remaining_percent'),value.get('approximate'),value.get('customer_confirmed'))
    if value!=expected:raise ValueError('Confirmation does not match the stock note or calculation')


def suggest_stock_inputs(note):
    """Accept only a complete, explicit total-mL/remaining-percent memo."""
    import re
    if not isinstance(note,str) or len(note)>300:return None
    match=re.fullmatch(r'\s*전체\s*용량\s*([0-9]+(?:\.[0-9]+)?)\s*m[lL]\s*[,，]\s*남은\s*비율\s*([0-9]+(?:\.[0-9]+)?)\s*%\s*',note,re.IGNORECASE)
    if match is None:return None
    try:
        capacity=number(match.group(1),Decimal('0.001'),Decimal('1000000'))
        remaining=number(match.group(2),Decimal('0'),Decimal('100'))
    except ValueError:return None
    return dict(container_ml=format(capacity,'f'),remaining_percent=format(remaining,'f'))


def preview_stock(container_ml,remaining_percent):
    capacity=number(container_ml,Decimal('0.001'),Decimal('1000000'))
    remaining=number(remaining_percent,Decimal('0'),Decimal('100'))
    return format((capacity*remaining/Decimal('100')).normalize(),'f')
