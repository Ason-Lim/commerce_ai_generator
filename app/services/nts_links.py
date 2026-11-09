"""User-reviewed registry-number evidence in a separate append-only SQLite store."""
import hashlib,json,re,sqlite3,unicodedata
from contextlib import closing
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlsplit
try:
 from app.services.nts_lookup import number,LookupError
except ModuleNotFoundError:
 from nts_lookup import number,LookupError

class LinkError(Exception):pass

def path_for(nts_path):return Path(nts_path).resolve().with_name('nts_company_links.sqlite3')
def identity(record):
 source=str(record.get('source') or '').strip();key=str(record.get('record_key') or record.get('management_no') or '').strip()
 if not source or not key:raise LinkError('업체의 명부 출처와 고유 식별자가 필요합니다.')
 return hashlib.sha256(json.dumps([source,key],ensure_ascii=False).encode()).hexdigest()
def fingerprint(record):
 vals=[unicodedata.normalize('NFKC',str(record.get(k) or '')).strip() for k in ('name','address')]
 if not all(vals):raise LinkError('업체명과 주소가 있어야 번호를 연결할 수 있습니다.')
 return hashlib.sha256(json.dumps(vals,ensure_ascii=False).encode()).hexdigest()
def index(nts_path):
 p=path_for(nts_path)
 if not p.is_file():return {}
 with closing(sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=2)) as c:
  rows=c.execute('SELECT entity_key,seq,payload FROM company_link_events WHERE seq IN (SELECT MAX(seq) FROM company_link_events GROUP BY entity_key)').fetchall()
 return {k:dict(json.loads(payload),seq=seq) for k,seq,payload in rows}
def state(record,nts_path,events=None):
 try:key=identity(record);fp=fingerprint(record)
 except LinkError as e:return None,str(e)
 event=(events if events is not None else index(nts_path)).get(key)
 if not event or event['action']=='revoke':return None,'번호 연결 없음'
 if event['fingerprint']!=fp:return None,'업체명 또는 주소 변경 — 번호 연결 재확인 필요'
 return event,'사용자 근거 확인으로 연결'
def validate(evidence):
 try:n=number(evidence.get('business_no'))
 except LookupError as e:raise LinkError(str(e)) from None
 if not evidence.get('confirmed'):raise LinkError('근거에 표시된 회사명·주소·사업자번호를 대조한 뒤 확인란을 선택해 주세요.')
 kind=evidence.get('evidence_type')
 if kind not in ('공식 사이트','사업자등록증','기타 확인 자료'):raise LinkError('확인 자료 종류를 선택해 주세요.')
 ref=str(evidence.get('reference') or '').strip()
 if len(ref)<5 or len(ref)>2000:raise LinkError('출처 URL 또는 문서명·보관 위치를 입력해 주세요.')
 if kind=='공식 사이트':
  url=urlsplit(ref)
  if url.scheme not in ('http','https') or not url.hostname or url.username or url.password:raise LinkError('공식 사이트 URL을 올바르게 입력해 주세요.')
 try:d=date.fromisoformat(str(evidence.get('reviewed_on')))
 except (ValueError,TypeError):raise LinkError('확인일은 YYYY-MM-DD 형식으로 입력해 주세요.') from None
 if d>datetime.now(timezone(timedelta(hours=9))).date():raise LinkError('확인일은 미래 날짜로 입력할 수 없습니다.')
 return dict(business_no=n,evidence_type=kind,reference=ref,reviewed_on=d.isoformat(),note=str(evidence.get('note') or '').strip()[:2000],confirmation='사용자가 회사명·주소·번호를 근거와 대조함',identity_verified_by_nts=False)

def current_record(record,registry_path):
 if not Path(registry_path).is_file():raise LinkError('업체 원본 명부를 찾지 못했습니다.')
 with closing(sqlite3.connect(Path(registry_path).resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as c:
  row=c.execute('''SELECT o.payload FROM registry_observations o JOIN registry_snapshots s USING(snapshot_id)
   WHERE s.source=? AND o.record_key=? ORDER BY s.as_of DESC,s.rowid DESC LIMIT 1''',(record['source'],record.get('record_key') or record.get('management_no'))).fetchone()
 if not row:raise LinkError('선택한 업체가 현재 명부에 없습니다. 다시 검색해 주세요.')
 p=json.loads(row[0]);p['source']=record['source'];p['record_key']=record.get('record_key') or record.get('management_no')
 if fingerprint(p)!=fingerprint(record):raise LinkError('선택 후 업체명 또는 주소가 바뀌었습니다. 다시 검색해 주세요.')
 return p

def write(record,nts_path,evidence=None,action='link',expected_seq=0,allow_replace=False,reason='',registry_path=None):
 if action not in ('link','revoke'):raise LinkError('지원하지 않는 작업입니다.')
 key=identity(record);fp=fingerprint(record)
 if action=='link' and registry_path is None:raise LinkError('연결 저장에는 원본 명부 확인이 필요합니다.')
 if registry_path is not None:current_record(record,registry_path)
 details=validate(evidence or {}) if action=='link' else {}
 if action=='revoke' and len(reason.strip())<2:raise LinkError('연결 해제 사유를 입력해 주세요.')
 p=path_for(nts_path);p.parent.mkdir(parents=True,exist_ok=True)
 with closing(sqlite3.connect(p,timeout=3)) as c:
  c.execute('CREATE TABLE IF NOT EXISTS company_link_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,entity_key TEXT NOT NULL,payload TEXT NOT NULL)')
  c.execute('BEGIN IMMEDIATE')
  try:
   prior=c.execute('SELECT seq,payload FROM company_link_events WHERE entity_key=? ORDER BY seq DESC LIMIT 1',(key,)).fetchone()
   if (prior[0] if prior else 0)!=expected_seq:raise LinkError('다른 화면에서 연결이 변경됐습니다. 다시 조회해 주세요.')
   old=json.loads(prior[1]) if prior else None
   if action=='link' and old and old['action']=='link' and not allow_replace:raise LinkError('기존 연결 수정 확인란을 선택해 주세요.')
   if action=='revoke' and (not old or old['action']!='link'):raise LinkError('해제할 연결이 없습니다.')
   payload=dict(details,action=action,source=record['source'],record_key=record.get('record_key') or record.get('management_no'),name=record['name'],address=record['address'],fingerprint=fp,recorded_at=datetime.now(timezone.utc).isoformat(),reason=reason.strip(),previous_seq=expected_seq)
   cur=c.execute('INSERT INTO company_link_events(entity_key,payload) VALUES(?,?)',(key,json.dumps(payload,ensure_ascii=False,sort_keys=True)));c.commit()
   return dict(payload,seq=cur.lastrowid)
  except Exception:c.rollback();raise

def registry_path():
 import os
 return Path(os.getenv('B2B_EVIDENCE_DB',str(Path(__file__).resolve().parents[2]/'data/b2b_evidence/b2b_evidence.sqlite3'))).resolve()

def render_link(st,record,nts_path,namespace="supplier"):
 try:
  key=identity(record);fingerprint(record);events=index(nts_path);active,label=state(record,nts_path,events)
 except LinkError as e:
  st.warning('번호 등록 양식을 표시할 수 없습니다: '+str(e))
  return None
 except (sqlite3.Error,OSError,ValueError):
  st.error('번호 연결 이력을 읽지 못해 등록 양식을 표시할 수 없습니다. 저장 파일과 접근 권한을 확인해 주세요.')
  return None
 last=events.get(key);seq=last['seq'] if last else 0;token='company_link_'+namespace+'_'+key+'_'+str(seq)
 if active:
  st.write('등록 번호 확인 근거: '+active['evidence_type']+' / '+active['reference'])
  st.caption('확인일: '+active['reviewed_on']+' · 사용자가 회사명·주소·번호를 대조함')
 elif last and last['action']=='link':st.warning(label)
 with st.expander('사업자번호 연결 근거 등록 / 수정',expanded=(namespace=='search')):
  st.write('연결 대상: '+record['name']);st.write('주소: '+record['address'])
  with st.form(token+'_form'):
   n=st.text_input('연결할 사업자등록번호',value=active['business_no'] if active else '',key=token+'_number')
   kinds=['공식 사이트','사업자등록증','기타 확인 자료']
   prior_kind=active.get('evidence_type') if active else None
   kind=st.selectbox('확인 자료 종류',kinds,index=kinds.index(prior_kind) if prior_kind in kinds else 0,key=token+'_type')
   ref=st.text_input('출처 URL 또는 문서명·보관 위치',value=active.get('reference','') if active else '',key=token+'_ref')
   reviewed=st.text_input('근거 확인일 (YYYY-MM-DD)',value=active['reviewed_on'] if active else datetime.now(timezone(timedelta(hours=9))).date().isoformat(),key=token+'_date')
   note=st.text_input('확인 메모 (선택)',value=active.get('note','') if active else '',key=token+'_note')
   confirmed=st.checkbox('자료의 회사명·주소·사업자번호가 위 업체와 일치함을 직접 확인했습니다.',key=token+'_confirmed')
   replace=st.checkbox('기존 연결을 수정하고 이전 기록을 이력으로 보존합니다.',key=token+'_replace') if last and last['action']=='link' else False
   submitted=st.form_submit_button('연결 근거 저장')
  if submitted:
   try:
    write(record,nts_path,dict(business_no=n,evidence_type=kind,reference=ref,reviewed_on=reviewed,note=note,confirmed=confirmed),expected_seq=seq,allow_replace=replace,registry_path=registry_path())
    st.success('번호 연결 근거를 저장했습니다.');st.rerun()
   except LinkError as e:st.error(str(e))
   except (OSError,sqlite3.Error,ValueError):st.error('연결 근거를 저장하지 못했습니다.')
 if last and last['action']=='link':
  with st.expander('이 업체의 번호 연결 해제',expanded=False):
   with st.form(token+'_revoke'):
    reason=st.text_input('해제 사유',key=token+'_reason')
    confirm=st.checkbox('이 업체의 번호 연결을 해제합니다.',key=token+'_revoke_confirm')
    revoke=st.form_submit_button('연결 해제')
   if revoke:
    if not confirm:st.warning('연결 해제 확인란을 선택해 주세요.')
    else:
     try:
      write(record,nts_path,action='revoke',expected_seq=seq,reason=reason)
      st.success('연결을 해제했습니다. 이전 근거와 국세청 조회 기록은 보존됩니다.');st.rerun()
     except LinkError as e:st.error(str(e))
     except (OSError,sqlite3.Error,ValueError):st.error('연결을 해제하지 못했습니다.')
 st.caption('사용자가 등록한 연결 근거입니다. 국세청 진위확인이나 식품 인허가·공급 가능 확인을 뜻하지 않습니다.')
 return active

def overlay_candidate(candidate,nts_path,events=None):
 p=dict(candidate);record=p.get('registry_record')
 if not record:return p
 original=p.get('original_business_no',p.get('business_no',''));p['original_business_no']=original
 active,label=state(record,nts_path,events);p['number_evidence']=label
 if active and original and original!=active['business_no']:
  p['business_no']='';p['number_evidence']='원본 번호와 등록한 번호가 다름 — 연결 재확인 필요';p['link_conflict']=True
 else:
  p['business_no']=original or (active['business_no'] if active else '')
  p['link_conflict']=False
 return p
