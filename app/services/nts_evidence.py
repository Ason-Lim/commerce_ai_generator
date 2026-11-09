"""Separate NTS evidence store; no automatic registry/company matching."""
import json,os,sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

def db_path():
 return Path(os.getenv('NTS_EVIDENCE_DB',str(Path(__file__).resolve().parents[2]/'data/b2b_evidence/nts_status.sqlite3'))).resolve()

def read_checks(path=None,number=None):
 p=Path(path) if path else db_path()
 if not p.is_file():return []
 with closing(sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True)) as c:
  if number is None:
   rows=c.execute('SELECT payload FROM nts_checks ORDER BY checked_at DESC,check_id DESC LIMIT 20').fetchall()
  else:
   rows=c.execute('SELECT payload FROM nts_checks WHERE b_no=? ORDER BY checked_at DESC,check_id DESC LIMIT 20',(number,)).fetchall()
 checks=[json.loads(r[0]) for r in rows]
 return checks if number is None else [v for v in checks if result_matches(v,number)]

def shown_time(value):
 try:
  from zoneinfo import ZoneInfo
  t=datetime.fromisoformat(value)
  if t.tzinfo is None:return value+' (시간대 미확인)'
  return t.astimezone(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S 한국시간')
 except (ValueError,TypeError):return value or '미확인'

def company_evidence(path=None):
 p=Path(path) if path else db_path()
 if not p.is_file():return {}
 with closing(sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True)) as c:
  exists=c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='nts_company_evidence'").fetchone()
  if not exists:return {}
  rows=c.execute('SELECT b_no,payload FROM nts_company_evidence').fetchall()
 return {n:json.loads(payload) for n,payload in rows}


def _client():
 from app.services import nts_lookup
 return nts_lookup

def result_matches(check,number):
 return isinstance(check,dict) and check.get('b_no')==number and isinstance(check.get('result'),dict) and check['result'].get('b_no')==number

def show_result(st,check,expected_number=None):
 if expected_number is not None and not result_matches(check,expected_number):
  st.warning('선택한 사업자번호와 조회 기록의 번호가 달라 표시하지 않습니다.');return
 r=check['result'];n=check['b_no']
 st.write('사업자등록번호: '+n[:3]+'-'+n[3:5]+'-'+n[5:])
 code=r.get('business_status_code')
 label={'01':'계속사업자 (사업 중)','02':'휴업자','03':'폐업자'}.get(code,'상태 미확인')
 getattr(st,{'01':'success','02':'warning','03':'error'}.get(code,'info'))('국세청 상태: '+label)
 st.write('과세유형: '+str(r.get('tax_type') or '미확인'))
 if r.get('closed_date'):st.write('폐업일자: '+r['closed_date'])
 st.caption('조회 시각: '+shown_time(check['checked_at']))

def _query(st,n,key):
 client=_client()
 try:
  with st.spinner('국세청 상태를 조회하고 있습니다…'):
   check,raw=client.lookup(n)
  st.session_state[key]=check
  try:client.save(check,raw,db_path())
  except (OSError,sqlite3.Error):st.warning('조회는 완료했지만 기록을 저장하지 못했습니다.')
 except client.LookupError as e:
  st.session_state.pop(key,None)
  st.error(str(e))

def render_saved_checks(st):
 st.markdown('**사업자등록번호로 국세청 상태조회**')
 with st.form('nts_number_lookup'):
  value=st.text_input('사업자등록번호',placeholder='123-45-67890',key='nts_number_input')
  submitted=st.form_submit_button('국세청 상태조회')
 if submitted:_query(st,value,'nts_lookup_result')
 if st.session_state.get('nts_lookup_result'):show_result(st,st.session_state['nts_lookup_result'])
 from app.services.nts_companies import render_companies
 render_companies(st,db_path())
 from app.services.nts_excel import render_excel
 render_excel(st,db_path())
 st.caption('계속사업·휴업·폐업을 조회합니다. 식품 영업 인허가와 공급 가능 여부는 별도 확인이 필요합니다.')
 st.markdown('**전체 번호 조회 이력 — 선택 업체와 별도**')
 st.caption('아래 이력은 여러 번호의 조회 기록이며 선택한 회사의 기록을 뜻하지 않습니다.')
 with st.expander('전체 번호 조회 이력 보기',expanded=False):
  if not st.checkbox('여러 사업자번호의 전체 조회 이력을 표시합니다.',key='nts_show_all_history',value=False):return
  try:
   checks=read_checks();names=company_evidence()
   if not checks:st.caption('저장된 조회 기록이 없습니다.')
   for check in checks:
    entity=names.get(check['b_no'])
    if entity:
     st.write('공식 사이트 표기 법인명: '+entity['company_name'])
     st.caption('법인명 근거: '+entity['source_url'])
    show_result(st,check)
  except (sqlite3.Error,ValueError,OSError):st.warning('저장된 조회 기록을 읽지 못했습니다.')

def render_company_status(st,p):
 client=_client();n,reason=client.registry_number(p)
 from app.services.nts_links import render_link
 linked=render_link(st,p,db_path())
 if linked and n and n!=linked['business_no']:
  st.warning('원본 번호와 등록한 번호가 다릅니다. 연결 근거를 다시 확인해 주세요.');return
 if linked:n=linked['business_no']
 if not n:
  st.caption('국세청 상태: '+reason);return
 st.write(('등록 근거의 사업자등록번호: ' if linked else '업체 데이터의 사업자등록번호: ')+n[:3]+'-'+n[3:5]+'-'+n[5:])
 # A number match links status to this registration number, not to a name.
 identity=str(p.get('record_key') or p.get('management_no') or p.get('name') or '')
 import hashlib
 key='nts_company_'+hashlib.sha256((str(p.get('source',''))+identity+n).encode()).hexdigest()[:24]
 if st.button('이 업체 국세청 상태조회 / 갱신',key=key+'_button'):_query(st,n,key)
 try:check=st.session_state.get(key) or client.latest(n,db_path())
 except (sqlite3.Error,ValueError,OSError):
  st.warning('조회 기록을 읽지 못했습니다.');return
 if check:
  st.caption('등록 근거와 조회 결과의 사업자번호 일치' if linked else '업체 데이터와 조회 결과의 사업자등록번호 일치')
  show_result(st,check,expected_number=n)
 else:st.info('국세청 미조회 — 위 버튼으로 사업 중·휴업·폐업 여부를 확인하세요.')
