def render_b2b_panel():
 import streamlit as st
 import sqlite3
 from app.services.b2b_evidence import suppliers,products
 st.title('B2B 업체·상품 근거')
 st.caption('자료상 영업상태와 현재 공급 가능 여부는 다릅니다. 조회 기준일 미확인은 별도로 확인하세요.')
 kind=st.selectbox('업종',['식육포장처리업','도축업','축산물유통전문판매업'])
 sources={'식육포장처리업':'mois_packing','도축업':'foodsafety_I2858','축산물유통전문판매업':'bupyeong_distribution'}
 region=st.text_input('업체 소재지 검색','')
 unknown=st.checkbox('영업상태 미확인 후보 포함',value=kind!='식육포장처리업')
 page=int(st.number_input('페이지',min_value=1,value=1,step=1))
 try:
  found=suppliers(kind,region,sources[kind],unknown,(page-1)*30,30)
  st.write('업체 탐색 후보',found['total'],'건')
  st.dataframe(found['items'],use_container_width=True)
  st.subheader('상품 비교 조건·공급사 확인 질문')
  st.caption('도매 부분육과 소매 소포장은 거래 유형을 구분합니다. 현재 자료는 검증 전 보류 상태입니다.')
  result=products()
  for product in result['items']:
   with st.expander(product['name']+(' | '+product['option_raw'] if product.get('option_raw') else '')+' · 확인 필요'):
    st.json(product)
 except (ValueError,sqlite3.Error):st.info('B2B 근거 DB 설치·업체 자료 적재를 먼저 확인해 주세요.')
