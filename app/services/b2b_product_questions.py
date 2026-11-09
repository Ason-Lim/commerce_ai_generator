"""Display-only question profiles; never establish eligibility or verified weight."""
CATALOG = {
 '비가림 황금향':'fruit', '설향딸기':'fruit', '조생 노지감귤':'fruit',
 '극조생 노지감귤 대과':'fruit', '이룸팜스 사과배 혼합 선물세트 1호':'fruit',
 '황새치 뱃살 중':'seafood', '가다랑어 로인':'seafood', '국내산 완도 활전복 소':'seafood',
 '한우 우족선물세트 건강53호':'meat', '유정란 대란':'egg',
 '절임배추 / 김장밀키트':'prepared', '콩여울 기름 선물세트':'prepared',
}
LABELS={'fruit':'과일','seafood':'수산물','meat':'축산물','egg':'알류','prepared':'가공·구성 상품','unknown':'분류 미확인'}
COMMON={
 'actual_seller':'실제 판매업체와 식별번호를 확인해 주세요.',
 'origin':'원산지와 적용 상품·옵션을 확인해 주세요.',
 'net_weight_kg':'포장재 제외 순중량과 중량 보장 기준을 확인해 주세요.',
 'shipping_fee_krw':'주문 수량·배송지별 배송비를 확인해 주세요.',
 'transaction_stage':'도매·소매·공급표 중 실제 거래 조건과 최소 주문 수량을 확인해 주세요.',
}
EXTRA={
 'fruit':['품종·크기·과수와 허용 오차를 확인해 주세요.','흠집·부패 허용 기준과 교환 조건을 확인해 주세요.','당도 주장이 있다면 측정 방법·시점·적용 로트를 확인해 주세요.','수확·선별 시점과 보관·배송 조건을 확인해 주세요.'],
 'seafood':['어종·크기·마릿수와 손질·가식부 중량 기준을 확인해 주세요.','활어·냉장·냉동 상태와 보관·배송 조건을 확인해 주세요.'],
 'meat':['축종·부위·구성 비율을 확인해 주세요.','등급과 판정 근거를 확인해 주세요.','가공 작업장과 식별번호를 확인해 주세요.','냉장·냉동 상태와 손질·보관 기준을 확인해 주세요.'],
 'egg':['난중·개수와 파손 보상 기준을 확인해 주세요.','산란일·소비기한과 보관·배송 조건을 확인해 주세요.'],
 'prepared':['구성별 원재료·함량·알레르기 표시를 확인해 주세요.','제조업체·소비기한과 보관·배송 조건을 확인해 주세요.'],
 'unknown':['상품군과 정확한 옵션을 먼저 확인해 주세요.'],
}
def question_profile(p):
 # Exact known catalog names route questions only; this is not verified taxonomy.
 group=CATALOG.get(p.get('name'),'unknown')
 missing=[key for key in COMMON if p.get(key) in (None,'','unknown','unverified','supply_list')]
 questions=[COMMON[key] for key in missing]
 questions += EXTRA[group]
 questions += ['현재 옵션의 가격·공급 가능 수량·배송 완료일·견적 유효기간을 확인해 주세요.']
 return dict(question_profile=group,question_profile_label=LABELS[group],
  question_profile_basis='기존 상품명 정확 일치에 따른 질문용 분류; 검증된 상품 속성 아님',
  unknown_fields=missing,supplier_questions=questions,
  question_scope_note='unknown_fields는 공통 항목의 저장값 누락 목록입니다. 추가 질문은 확인 과제이며 답변·검증 완료를 뜻하지 않습니다.',
  specification_claim=p.get('option_raw'),
  specification_claim_status='저장된 출처의 규격 표기; 순중량 검증·현재 공급 확정 아님',
  net_weight_evidence_status='NOT_ESTABLISHED',
  net_weight_evidence_note='net_weight_kg는 저장값입니다. 이 패치는 검증 근거를 평가하거나 규격에서 순중량을 자동 확정하지 않습니다.')
