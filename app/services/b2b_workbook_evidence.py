"""Original workbook claims, separate from verified commercial conditions."""
import hashlib
from functools import lru_cache
from pathlib import Path
SOURCE = {'filename': '농민연합 위탁리스트 (공개용).xlsx', 'sha256': '6cbec6a924616f2ad2854147010e245a319781a6d0844b0d3327011327e1e350', 'archive_path': 'data/b2b_evidence/source_files/6cbec6a924616f2ad2854147010e245a319781a6d0844b0d3327011327e1e350.xlsx', 'sheet': '🍇국내과일', 'reviewed_on': '2026-10-21', 'review_scope': '첨부 원본의 셀 대조', 'price_effective_date': None, 'header_date_cell': 'E2', 'header_date_formula': '=TODAY()', 'header_date_note': '표 상단 날짜는 TODAY() 자동 날짜입니다. 가격 갱신일·견적 유효일이 아닙니다.', 'current_supply_verified': False, 'registry_link_created': False}
ENTRIES = {'legacy-20261012-00': {'expected_name': '비가림 황금향', 'expected_option': '2kg 중소과 7–10입', 'expected_price': 10200.0, 'expected_source_id': '761b8aa0d04269c1e9765ede0196edcd86050c4e6eceb0df081b0c83f814ac0a', 'claims': {'상품명·규격': {'value': '명품 비가림황금향 2kg 중소과(7-10입)', 'cell': 'C20'}, '공급가(원)': {'value': '10200.0', 'cell': 'E20'}, '세금': {'value': '면세', 'cell': 'G20'}, '발주 마감시간': {'value': '08:30:00', 'cell': 'L20'}, '원산지': {'value': '제주', 'cell': 'M20'}, '판매예상기간': {'value': '10월~4월', 'cell': 'N20'}}, 'blank_cells': {'포장방법': 'H20', '소구포인트': 'I20', '비고': 'J20', '택배사': 'K20'}, 'matched_previous_price': True}, 'legacy-20261012-01': {'expected_name': '비가림 황금향', 'expected_option': '3kg 중소과 12–16입', 'expected_price': 13300.0, 'expected_source_id': '761b8aa0d04269c1e9765ede0196edcd86050c4e6eceb0df081b0c83f814ac0a', 'claims': {'상품명·규격': {'value': '명품 비가림황금향 3kg 중소과(12-16입)', 'cell': 'C21'}, '공급가(원)': {'value': '13300.0', 'cell': 'E21'}, '세금': {'value': '면세', 'cell': 'G21'}, '발주 마감시간': {'value': '08:30:00', 'cell': 'L21'}, '원산지': {'value': '제주', 'cell': 'M21'}, '판매예상기간': {'value': '10월~4월', 'cell': 'N21'}}, 'blank_cells': {'포장방법': 'H21', '소구포인트': 'I21', '비고': 'J21', '택배사': 'K21'}, 'matched_previous_price': True}, 'legacy-20261012-02': {'expected_name': '비가림 황금향', 'expected_option': '5kg 중소과 22–28입', 'expected_price': 20700.0, 'expected_source_id': '761b8aa0d04269c1e9765ede0196edcd86050c4e6eceb0df081b0c83f814ac0a', 'claims': {'상품명·규격': {'value': '명품 비가림황금향 5kg 중소과(22-28입)', 'cell': 'C22'}, '공급가(원)': {'value': '20700.0', 'cell': 'E22'}, '세금': {'value': '면세', 'cell': 'G22'}, '발주 마감시간': {'value': '08:30:00', 'cell': 'L22'}, '원산지': {'value': '제주', 'cell': 'M22'}, '판매예상기간': {'value': '10월~4월', 'cell': 'N22'}}, 'blank_cells': {'포장방법': 'H22', '소구포인트': 'I22', '비고': 'J22', '택배사': 'K22'}, 'matched_previous_price': True}}
@lru_cache(maxsize=2)
def _digest(path, modified, size):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def evidence_for(p, repo=None):
    e=ENTRIES.get(p.get('product_id'))
    if not e:return None
    if any(p.get(k)!=v for k,v in [('name',e['expected_name']),('option_raw',e['expected_option']),('observed_price_krw',e['expected_price']),('source_id',e['expected_source_id'])]):return None
    root=Path(repo) if repo is not None else Path(__file__).resolve().parents[2]
    path=root/SOURCE['archive_path']
    try:
        stat=path.stat()
        if _digest(str(path),stat.st_mtime_ns,stat.st_size)!=SOURCE['sha256']:return None
    except OSError:return None
    return dict(source=SOURCE,claims=e['claims'],blank_cells=e['blank_cells'],
      status='SOURCE_CELLS_MATCHED_ONLY',price_comparison='기존 전사값과 첨부 파일의 표기 금액 일치; 같은 거래조건의 유효 견적 비교는 미확립',
      commercial_verification='배송비·재고·공급 수량·납기·견적 유효기간·실제 판매업체 미확인')
