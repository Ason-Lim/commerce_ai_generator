def render_b2b_panel():
 import streamlit as st
 import sqlite3
 from app.services.b2b_evidence import suppliers,products
 st.title('B2B 업체·상품 근거')
 st.caption('자료상 영업상태와 현재 공급 가능 여부는 다릅니다. 조회 기준일 미확인은 별도로 확인하세요.')
 from app.ui.b2b_supplier_browser import render_supplier_browser,read_cached
 try:
  render_supplier_browser(st,suppliers)
  st.subheader('상품 비교 조건·공급사 확인 질문')
  st.caption('상품군에 맞는 확인 질문을 표시합니다. 현재 자료는 검증 전 보류 상태입니다.')
  result=read_cached(st, ('products',), products)
  for product in result['items']:
   with st.expander(product['name']+(' | '+product['option_raw'] if product.get('option_raw') else '')+' · 확인 필요'):
    st.write('확인 질문 유형: '+product.get('question_profile_label','분류 미확인'))
    st.write('출처 규격 표기: '+str(product.get('specification_claim') or '미확인'))
    st.caption('출처에 적힌 규격입니다. 포장재를 제외한 실제 중량과 현재 공급 조건은 별도 확인이 필요합니다.')
    st.write('포장재 제외 순중량(kg): '+str(product.get('net_weight_kg') if product.get('net_weight_kg') is not None else '미확인'))
    st.caption('규격에 적힌 중량을 실제 순중량으로 확정하지 않습니다. 중량 보장 기준과 증빙을 공급사에 확인해 주세요.')
    evidence=product.get('source_document_evidence')
    if evidence:
     st.markdown('**첨부 공급표에서 확인한 표기**')
     st.caption('원문 셀 대조 완료 · 현재 주문 가능 여부와 거래조건은 확인 전입니다.')
     for label,claim in evidence['claims'].items():
      st.write(label+': '+claim['value']+' ('+evidence['source']['sheet']+'!'+claim['cell']+')')
     st.write('원문 파일: '+evidence['source']['filename'])
     st.caption('원문 대조일: '+evidence['source']['reviewed_on']+' · 가격 유효일: 미확인')
     st.caption(evidence['source']['header_date_note'])
     st.caption('기존 전사값과 공급표 금액은 일치합니다. 같은 거래조건의 유효 견적 비교는 아직 미확립입니다.')
     st.caption('공급표의 해당 행에 포장방법·택배사·비고가 비어 있습니다. 배송비·재고·납기 등은 별도 확인이 필요합니다.')
    st.markdown('**공급사에 확인할 내용**')
    for question in product.get('supplier_questions',[]):
     st.write('• '+question)
    if st.checkbox('개발용 상세 보기', value=False, key='b2b_raw_'+str(product['product_id'])):
     st.json(product)
 except (ValueError,sqlite3.Error):st.info('B2B 근거 DB 설치·업체 자료 적재를 먼저 확인해 주세요.')
