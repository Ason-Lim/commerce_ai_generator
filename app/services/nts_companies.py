"""Company candidates from local evidence; never infer identity from NTS status."""
import json,sqlite3,re,unicodedata,os,time
from pathlib import Path
from contextlib import closing

def normalize(value):
 value=unicodedata.normalize('NFKC',str(value or '')).lower()
 for token in ('주식회사','유한회사','(주)','(유)','㈜','㈲'):value=value.replace(token,'')
 return re.sub(r'[^a-z0-9가-힣]','',value)

def root():return Path(__file__).resolve().parents[2]
def profiles(nts_path):
 rows=json.loads(Path(__file__).with_name('company_profiles.json').read_text(encoding='utf-8'))
 path=Path(nts_path)
 if path.exists():
  with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as con:
   if con.execute("SELECT 1 FROM sqlite_master WHERE name='nts_company_evidence'").fetchone():
    for n,payload in con.execute('SELECT b_no,payload FROM nts_company_evidence'):
     p=json.loads(payload)
     rows.append(dict(company_name=p['company_name'],business_no=n,products='미확인',location='미확인',scale='미확인',source='공식 사이트 표기',source_url=p.get('source_url',''),reviewed_on=p.get('reviewed_on',''),aliases={'1048609535':['CJ','씨제이제일제당'],'1188103914':['농심'],'4038161113':['하림']}.get(n,[])))
 return rows

def matches(p,name,number):
 names=[p.get('company_name','')]+p.get('aliases',[])
 return (not name or any(normalize(name) in normalize(n) for n in names)) and (not number or p.get('business_no')==number)

def _links():
 try:
  from app.services import nts_links
 except ModuleNotFoundError:
  import nts_links
 return nts_links

class SearchTimeout(Exception):pass

def search(name,number,nts_path,registry_path=None,include_registry=False):
    try:
        from app.services.nts_lookup import registry_number
    except ModuleNotFoundError:
        from nts_lookup import registry_number
    links=_links();events=links.index(nts_path)
    found=[p for p in profiles(nts_path) if matches(p,name,number)]
    if found and not include_registry:return found[:100]
    reg=Path(registry_path) if registry_path else Path(os.getenv('B2B_EVIDENCE_DB',str(root()/'data/b2b_evidence/b2b_evidence.sqlite3')))
    if not reg.is_file():raise FileNotFoundError('registry unavailable')
    with closing(sqlite3.connect(reg.resolve().as_uri()+'?mode=ro',uri=True,timeout=1)) as con:
        deadline=time.monotonic()+30.0
        con.set_progress_handler(lambda: int(time.monotonic()>deadline),1000)
        con.create_function('company_normalize',1,normalize)
        linked={(p['source'],p['record_key']):p['business_no'] for p in events.values() if p['action']=='link'}
        con.create_function('linked_number',2,lambda source,key:linked.get((source,key),''))
        terms=[];args=[]
        if normalize(name):
            terms.append("instr(company_normalize(json_extract(payload,'$.name')),?)>0")
            args.append(normalize(name))
        if number:
            terms.append("(instr(replace(payload,'-',''),?)>0 OR linked_number(l.source,o.record_key)=?)")
            args.extend([number,number])
        if not terms:return found[:100]
        sql="""WITH latest AS (
          SELECT o.rowid observation_rowid,s.source,s.as_of,ROW_NUMBER() OVER(
            PARTITION BY s.source,o.record_key ORDER BY s.as_of DESC,s.rowid DESC) rn
          FROM registry_observations o JOIN registry_snapshots s USING(snapshot_id)
        ) SELECT o.payload,l.source,l.as_of,o.record_key FROM latest l
        JOIN registry_observations o ON o.rowid=l.observation_rowid
        WHERE l.rn=1 AND """+' AND '.join(terms)
        try:
            for payload,source,as_of,record_key in con.execute(sql,args):
                p=json.loads(payload);n,reason=registry_number(p)
                item=dict(company_name=p.get('name') or '업체명 미확인',business_no=n or '',products=p.get('main_products') or p.get('products') or '미확인',location=p.get('address') or '미확인',scale='미확인',source='B2B 명부: '+source,source_url='',reviewed_on=as_of,license_status=p.get('status_raw') or p.get('operation_status') or '미확인',operation_status=p.get('operation_status'),business_type=p.get('business_type') or '')
                item['registry_record']=dict(source=source,record_key=record_key,name=p.get('name') or '',address=p.get('address') or '')
                item=links.overlay_candidate(item,nts_path,events)
                if matches(item,name,number):found.append(item)
                if len(found)>=100:break
        except sqlite3.OperationalError as e:
            if 'interrupt' in str(e).lower():raise SearchTimeout() from None
            raise
    return found[:100]

def candidate_label(p):
 kind='명부' if p.get('registry_record') else '참고 정보'
 return '['+kind+'] '+p['company_name']+' | '+(p.get('business_no') or '번호 미확인')+' | '+p.get('location','')+' | '+p.get('source','출처 미확인')

def preferred_index(candidates):
 for i,p in enumerate(candidates):
  if p.get('registry_record') and p.get('business_no') and not p.get('link_conflict') and p.get('number_evidence')=='사용자 근거 확인으로 연결':return i
 return next((i for i,p in enumerate(candidates) if p.get('registry_record')),0)

def selection_token(candidates):
 import hashlib
 identities=[p.get('registry_record') or {k:p.get(k,'') for k in ('company_name','location','source')} for p in candidates]
 return hashlib.sha256(json.dumps(identities,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16]

def render_selected_link(st,p,nts_path):
 if p.get('registry_record'):
  st.info('현재 선택 자료: B2B 명부 업체 — 아래에서 사업자번호 연결 근거를 등록할 수 있습니다.')
  return _links().render_link(st,p['registry_record'],nts_path,namespace='search')
 st.warning('현재 선택 자료: '+str(p.get('source') or '참고 정보'))
 st.info('이 항목은 명부 출처·고유 식별자가 연결되지 않은 참고 정보이므로 번호 등록 양식을 표시하지 않습니다. 상세 선택 상자에서 [명부] 항목의 회사명·주소·출처를 대조해 선택해 주세요. 명부 후보가 없으면 B2B 명부에서도 추가 검색을 눌러 주세요.')
 return None

def render_companies(st,nts_path):
 try:
  from app.services import nts_lookup as client
  from app.services.nts_evidence import show_result,_query,shown_time
 except ModuleNotFoundError:
  import nts_lookup as client
  from nts_evidence import show_result,_query,shown_time
 st.markdown('**회사명·사업자등록번호로 회사 정보 찾기**')
 st.caption('연결된 B2B 명부와 저장된 회사 정보에서 찾습니다. 동명 업체는 주소·번호·출처로 구분해 선택하세요.')
 with st.form('nts_company_search'):
  name=st.text_input('회사명',placeholder='예: 매일식품',key='nts_company_name')
  value=st.text_input('사업자등록번호 (선택)',placeholder='번호를 알고 있으면 함께 입력',key='nts_company_number')
  submit=st.form_submit_button('회사 정보 검색')
 if submit:
  st.session_state.pop('nts_company_candidates',None)
  if not normalize(name) and not value.strip():st.warning('회사명 또는 사업자등록번호를 입력해 주세요.')
  else:
   try:
    n=client.number(value) if value.strip() else ''
    with st.spinner('회사 정보를 검색하고 있습니다…'):
     st.session_state['nts_company_candidates']=search(name,n,nts_path)
    st.session_state['nts_company_search_args']=(name,n)
   except SearchTimeout:st.warning('조회 미완료 — 명부 검색을 완료하지 못했습니다. 다시 조회해 주세요.')
   except client.LookupError as e:st.error(str(e))
   except (sqlite3.Error,OSError,ValueError):st.error('조회 실패 — 회사 정보 검색 자료를 읽지 못했습니다.')
 if 'nts_company_candidates' not in st.session_state:return
 candidates=[_links().overlay_candidate(p,nts_path) for p in st.session_state['nts_company_candidates']]
 st.session_state['nts_company_candidates']=candidates
 if candidates and st.button('B2B 명부에서도 추가 검색',key='nts_search_registry_extra'):
  name,n=st.session_state.get('nts_company_search_args',('',''))
  try:
   with st.spinner('B2B 명부를 검색하고 있습니다…'):
    candidates=search(name,n,nts_path,include_registry=True)
   st.session_state['nts_company_candidates']=candidates
  except SearchTimeout:st.warning('추가 조회 미완료 — 기존 회사 정보만 표시합니다.')
  except (sqlite3.Error,OSError,ValueError):st.warning('추가 조회 실패 — 기존 회사 정보만 표시합니다.')
 if not candidates:
  st.info('조회 결과 없음 — 현재 연결된 회사 정보와 B2B 명부에서 일치하는 업체를 찾지 못했습니다.');return
 st.success('조회 결과: '+str(len(candidates))+'건')
 table=[]
 for p in candidates:
  try:check=client.latest(p.get('business_no',''),nts_path) if p.get('business_no') else None
  except (sqlite3.Error,ValueError):check=None
  table.append({'회사명':p['company_name'],'사업자등록번호':p.get('business_no') or '미확인','번호 연결 근거':p.get('number_evidence','기존 회사 정보'),'주요 제품':p.get('products') or '미확인','위치':p.get('location') or '미확인','규모 참고':p.get('scale') or '미확인','국세청 상태':check['result']['business_status'] if check else '미조회','국세청 조회 시각':shown_time(check['checked_at']) if check else '', '명부 인허가 상태':p.get('license_status','미확인'),'정보 출처':p['source'],'확인일/기준일':p.get('reviewed_on') or '미확인'})
 st.dataframe(table,use_container_width=True)
 if len(candidates)==100:st.caption('최대 100개 후보입니다. 회사명과 번호를 함께 입력하면 범위를 줄일 수 있습니다.')
 st.caption('초기 상세는 번호 연결 근거가 있는 명부 업체를 우선 표시합니다. 없으면 명부 업체를 먼저 표시합니다. 동명 업체의 일치를 자동 판정하거나 번호를 자동 연결하지 않습니다.')
 st.caption('표의 셀 클릭은 상세 선택을 바꾸지 않습니다. 아래 선택 상자에서 업체를 선택하세요.')
 token=selection_token(candidates)
 selected=st.selectbox('상세 정보와 국세청 상태를 볼 회사',range(len(candidates)),index=preferred_index(candidates),format_func=lambda i:candidate_label(candidates[i]),key='nts_company_choice_'+token)
 p=candidates[selected]
 st.write('회사명: '+p['company_name'])
 for label,field in [('사업자등록번호','business_no'),('주요 제품','products'),('위치','location'),('규모 참고','scale'),('정보 출처','source')]:st.write(label+': '+str(p.get(field) or '미확인'))
 if p.get('source_url'):st.write('출처 URL: '+p['source_url'])
 if p.get('business_type'):st.write('명부 업종: '+p['business_type'])
 if p.get('registry_record'):
  status=p.get('license_status') or '미확인'
  if p.get('operation_status')=='inactive':st.warning('명부상 영업상태: '+status+' · 업체 탐색 후보에서는 제외됩니다.')
  else:st.write('명부상 영업상태: '+status)
  st.caption('회사 정보 검색은 비활성 명부도 표시합니다. 명부상 상태와 국세청 상태·현재 공급 가능 여부는 별개입니다.')
 st.caption('회사 정보 확인일/기준일: '+str(p.get('reviewed_on') or '미확인'))
 st.caption('종업원·매출은 기준연도와 출처가 필요합니다. 사용자 제공 정보와 국세청 조회 결과는 구분하여 표시합니다.')
 if p.get('registry_record'):
  try:
   from app.services.nts_addresses import render_addresses
  except ModuleNotFoundError:
   from nts_addresses import render_addresses
  render_addresses(st,p)
 render_selected_link(st,p,nts_path)
 if p.get('link_conflict'):st.warning(p['number_evidence'])
 n=p.get('business_no')
 if not n:st.info('사업자번호가 없어 국세청 상태는 조회할 수 없습니다.');return
 key='nts_profile_'+token+'_'+str(selected)
 if st.button('선택 회사의 국세청 상태조회 / 갱신',key=key+'_button'):_query(st,n,key)
 try:check=st.session_state.get(key) or client.latest(n,nts_path)
 except (sqlite3.Error,ValueError):check=None
 if check:show_result(st,check,expected_number=n)
 else:st.caption('국세청 미조회 — 위 버튼을 눌러 계속사업·휴업·폐업을 확인하세요.')
 from app.services.nts_evidence import read_checks
 with st.expander('선택한 사업자번호의 이전 조회 기록',expanded=False):
  if st.checkbox('이 번호의 저장된 이력을 표시합니다.',key=key+'_history',value=False):
   try:
    history=read_checks(nts_path,number=n)
    if not history:st.caption('이 번호의 저장된 조회 기록이 없습니다.')
    for item in history:show_result(st,item,expected_number=n)
   except (sqlite3.Error,OSError,ValueError):st.warning('선택 번호의 조회 기록을 읽지 못했습니다.')
 st.caption('이 상태는 선택한 사업자번호에 대한 결과입니다. 국세청이 회사명·번호의 일치를 진위확인한 결과는 아닙니다.')
