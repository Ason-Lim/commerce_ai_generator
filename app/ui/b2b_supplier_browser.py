"""Read-only supplier discovery UI. No product linkage or eligibility writes."""
import hashlib, os, time
from pathlib import Path
PAGE_SIZE = 30
from app.services.b2b_evidence import REGISTRY_SOURCES
SOURCES = {'전체':None, **REGISTRY_SOURCES}
SOURCE_LABELS = {'mois_packing':'전국 식육포장처리업 명부', 'foodsafety_I2858':'식품안전나라 I2858', 'bupyeong_distribution':'부평구 유통전문판매업 명부', 'localdata_livestock_processing_csv':'전국 축산가공업 CSV 명부', 'localdata_food_manufacturing_csv':'전국 식품제조가공업 CSV 명부'}
STATUS_LABELS = {'active':'자료상 영업 중','inactive':'자료상 영업 종료'}
def shown(value):
    return '미확인' if value is None or value == '' else str(value)
def page_count(total):
    return max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
def table_rows(items, offset):
    return [{'번호':offset+i+1,'업체명':shown(p.get('name')),'업종':shown(p.get('business_type')),
      '주소':shown(p.get('address')),'전화번호':shown(p.get('phone')),
      '자료상 영업상태':STATUS_LABELS.get(p.get('operation_status'),'미확인')}
      for i,p in enumerate(items)]
def selection_label(p):
    return ' | '.join([shown(p.get('name')),shown(p.get('address')),shown(p.get('management_no') or p.get('license_no') or p.get('record_key'))])
def render_supplier_browser(st, suppliers):
    # NTS_EVIDENCE_CONNECT_V1
    from app.services.nts_evidence import render_saved_checks, render_company_status
    render_saved_checks(st)
    kind=st.selectbox('업종',list(SOURCES),key='b2b_browser_kind')
    region=st.text_input('업체 소재지 검색','',key='b2b_browser_region').strip()
    unknown=st.checkbox('영업상태 미확인 후보 포함',value=kind!='식육포장처리업',key='b2b_browser_unknown_'+str(SOURCES[kind]))
    signature=(kind,region,unknown)
    state=st.session_state
    if state.get('b2b_browser_conditions')!=signature:
        state['b2b_browser_page']=1
        state['b2b_browser_page_text']='1'
        state['b2b_browser_conditions']=signature
    from app.services.b2b_evidence import supplier_candidates
    rows=read_cached(st, ('suppliers',signature), lambda: supplier_candidates(kind,region,SOURCES[kind],unknown))
    total=len(rows);last=page_count(total)
    state['b2b_browser_page']=max(1,min(int(state.get('b2b_browser_page',1)),last))
    st.caption('페이지 번호를 직접 입력하고 Enter를 누르세요. + / − 버튼을 반복해서 누를 필요가 없습니다.')
    entered=st.text_input('이동할 페이지',key='b2b_browser_page_text',value='1')
    if state.get('b2b_browser_page_text_context')!=signature:
        # Widget state is reset before rendering below in the filter-change block.
        state['b2b_browser_page_text_context']=signature
    if not entered.strip().isascii() or not entered.strip().isdigit():
        st.info('페이지는 1 이상의 숫자로 입력해 주세요.')
        page=state['b2b_browser_page']
    else:
        page=max(1,min(int(entered.strip()),last))
        if page!=int(entered.strip()):st.info('입력 범위를 벗어나 {}페이지를 표시합니다.'.format(page))
    state['b2b_browser_page']=page
    offset=(page-1)*PAGE_SIZE;items=rows[offset:offset+PAGE_SIZE]
    st.write('업체 탐색 후보 {:,}건'.format(total))
    if total==0:
        st.caption('표시 0건 · 현재 1 / 1페이지')
        st.info('검색 조건에 맞는 업체가 없습니다. 소재지 검색어 또는 업종을 바꿔 주세요.')
        return
    st.caption('전체 {:,}건 중 {:,}–{:,}번째 · 현재 {} / {}페이지 · 페이지당 {}건'.format(total,offset+1,offset+len(items),page,last,PAGE_SIZE))
    if kind=='전체':st.caption('전체는 연결된 업종별 대표 출처를 함께 표시한 기록 수입니다. 출처 간 고유 업체 수로 확정하지 않습니다.')
    st.caption('공식 명부의 탐색 후보입니다. 현재 영업·취급 품목·공급 가능 여부가 확인된 추천 목록은 아닙니다.')
    st.dataframe(table_rows(items,offset),use_container_width=True)
    # Reset selection when filters/page/data change; no automatic first-company selection.
    token=hashlib.sha256(repr((signature,page,[(p.get('source'),p.get('record_key')) for p in items])).encode()).hexdigest()[:20]
    if state.get('b2b_browser_selection_context')!=token:
        state['b2b_browser_selected']=0
        state['b2b_browser_selection_context']=token
    index=st.selectbox('현재 페이지에서 업체 상세 보기',list(range(len(items)+1)),
       format_func=lambda n:'업체를 선택해 주세요.' if n==0 else '{}. {}'.format(offset+n,selection_label(items[n-1])),key='b2b_browser_selected')
    if not index:return
    p=items[index-1]
    st.markdown('**선택 업체 상세**')
    for label,field in [('업체명','name'),('업종','business_type'),('원본 세부업태','business_subtype'),('주소','address'),('전화번호','phone'),('관리번호','management_no'),('인허가번호','license_no'),('출처 내 기록 식별값','record_key')]:
        st.write(label+': '+shown(p.get(field)))
    st.write('자료상 영업상태: '+STATUS_LABELS.get(p.get('operation_status'),'미확인'))
    render_company_status(st,p)
    st.write('자료 출처: '+SOURCE_LABELS.get(p.get('source'),shown(p.get('source'))))
    st.write('자료 수신·참조일: '+shown(p.get('received_or_reference_date')))
    st.write('자료 기준일: '+shown(p.get('dataset_effective_date')))
    st.caption('수신·참조일은 이 업체의 영업상태를 다시 확인한 날짜가 아닙니다.')
    st.markdown('**공급사에 확인할 내용**')
    for question in p.get('questions') or ['현재 영업상태와 자료 기준일','취급 품목','규격·수량·납기·유효 견적']:
        st.write('• '+question)
    st.info('업체 탐색 후보입니다. 이 선택으로 상품과 연결되거나 추천 적격으로 전환되지 않습니다.')


def read_cached(st, tag, loader):
    from app.services.b2b_evidence import DEFAULT_DB
    db=Path(os.getenv('B2B_EVIDENCE_DB',str(DEFAULT_DB))).resolve()
    def stamp(p):
        try:
            s=p.stat();return (s.st_mtime_ns,s.st_size)
        except FileNotFoundError:return None
    fingerprint=(str(db),stamp(db),stamp(Path(str(db)+'-wal')))
    bucket='b2b_read_cache_'+tag[0]
    old=st.session_state.get(bucket)
    now=time.monotonic()
    if old and old[0]==(tag,fingerprint) and now-old[1]<60:return old[2]
    result=loader()
    st.session_state[bucket]=((tag,fingerprint),now,result)
    return result
