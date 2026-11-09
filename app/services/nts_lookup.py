"""Explicit NTS requests; no registry mutation or name matching."""
import json, os, re, sqlite3, hashlib
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

ENDPOINT='https://api.odcloud.kr/api/nts-businessman/v1/status'
class LookupError(Exception): pass
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): return None

def number(value):
 n=re.sub(r'[-\s]','',str(value or ''))
 if not re.fullmatch('[0-9]{10}',n): raise LookupError('사업자등록번호 10자리를 입력해 주세요.')
 total=sum(int(x)*w for x,w in zip(n[:9],[1,3,7,1,3,7,1,3,5]))+int(n[8])*5//10
 if (10-total%10)%10!=int(n[9]): raise LookupError('사업자등록번호의 숫자를 다시 확인해 주세요.')
 return n

def parse(payload,n):
 if not isinstance(payload,dict) or payload.get('status_code')!='OK': raise LookupError('국세청 응답이 정상 처리되지 않았습니다.')
 rows=payload.get('data')
 if not isinstance(rows,list) or len(rows)!=1 or not isinstance(rows[0],dict) or rows[0].get('b_no')!=n: raise LookupError('조회 번호와 응답 번호가 일치하지 않습니다.')
 r=rows[0];code=r.get('b_stt_cd','')
 return dict(b_no=n,business_status={'01':'계속사업자','02':'휴업자','03':'폐업자'}.get(code,'상태 미확인'),business_status_code=code,status_raw=r.get('b_stt'),tax_type=r.get('tax_type'),tax_type_code=r.get('tax_type_cd'),closed_date=r.get('end_dt'),identity_verified=False,food_license_verified=False,supply_verified=False)

def lookup_many(values,repo=None,opener=None):
 numbers=list(dict.fromkeys(number(v) for v in values))
 if not numbers or len(numbers)>100:raise LookupError('한 번에 1~100개의 번호를 조회할 수 있습니다.')
 repo=Path(repo) if repo else Path(__file__).resolve().parents[2]
 key=os.getenv('NTS_SERVICE_KEY','').strip()
 if not key:
  try:
   from dotenv import dotenv_values
   key=(dotenv_values(repo/'.env').get('NTS_SERVICE_KEY') or '').strip()
  except ImportError: raise LookupError('python-dotenv 설치와 .env 설정을 확인해 주세요.') from None
 if not key: raise LookupError('프로젝트 .env의 NTS_SERVICE_KEY 설정을 확인하고 앱을 재시작해 주세요.')
 req=Request(ENDPOINT+'?'+urlencode({'serviceKey':key,'returnType':'JSON'}),data=json.dumps({'b_no':numbers}).encode(),headers={'Content-Type':'application/json'},method='POST')
 try:
  with (opener or build_opener(NoRedirect())).open(req,timeout=10) as response:
   raw=response.read(1048577)
  if len(raw)>1048576: raise LookupError('국세청 응답 크기가 예상 범위를 초과했습니다.')
  data=json.loads(raw)
 except HTTPError as e: raise LookupError('국세청 요청 실패 (HTTP '+str(e.code)+'). 인증키와 이용 승인을 확인해 주세요.') from None
 except (URLError,TimeoutError,OSError): raise LookupError('국세청에 연결하지 못했습니다. 잠시 후 조회 버튼을 다시 눌러 주세요.') from None
 except (ValueError,UnicodeError): raise LookupError('국세청 응답을 읽지 못했습니다.') from None
 if not isinstance(data,dict) or data.get('status_code')!='OK':raise LookupError('국세청 응답이 정상 처리되지 않았습니다.')
 rows=data.get('data')
 if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):raise LookupError('국세청 응답 형식을 확인할 수 없습니다.')
 got=[r.get('b_no') for r in rows]
 if len(got)!=len(numbers) or len(set(got))!=len(got) or set(got)!=set(numbers):raise LookupError('조회 번호와 응답 번호가 일치하지 않습니다.')
 indexed={r['b_no']:r for r in rows};when=datetime.now(timezone.utc).isoformat()
 return [(dict(provider='NTS',endpoint=ENDPOINT,b_no=n,checked_at=when,status='PROBE_OK',result=parse({'status_code':'OK','data':[indexed[n]]},n)),{'status_code':'OK','data':[indexed[n]]}) for n in numbers]

def lookup(value,repo=None,opener=None):
 return lookup_many([value],repo,opener)[0]

def save(check,raw,path):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 payload=json.dumps(check,ensure_ascii=False,sort_keys=True)
 uid=hashlib.sha256(payload.encode()).hexdigest()
 dest=path.parent/'nts_ui_queries'/uid;dest.mkdir(parents=True,exist_ok=True)
 (dest/'response.json').write_text(json.dumps(raw,ensure_ascii=False),encoding='utf-8')
 (dest/'receipt.json').write_text(payload,encoding='utf-8')
 with closing(sqlite3.connect(path)) as con:
  with con:
   con.execute('CREATE TABLE IF NOT EXISTS nts_checks(check_id TEXT PRIMARY KEY,b_no TEXT NOT NULL,checked_at TEXT NOT NULL,imported_at TEXT NOT NULL,raw_path TEXT NOT NULL,payload TEXT NOT NULL)')
   con.execute('INSERT OR IGNORE INTO nts_checks VALUES(?,?,?,?,?,?)',(uid,check['b_no'],check['checked_at'],datetime.now(timezone.utc).isoformat(),str(dest/'response.json'),payload))
 return uid

# Only fields explicitly representing business registration numbers qualify.
BUSINESS_FIELDS=('business_no','business_number','business_registration_number','business_registration_no','biz_no','bizr_no','b_no','BRNO','BIZRNO','BIZ_NO','BSN_NO','사업자등록번호','사업자번호')
def registry_number(record):
 found=set()
 for obj in (record,record.get('raw',{})):
  if not isinstance(obj,dict): continue
  for field in BUSINESS_FIELDS:
   if obj.get(field):
    try: found.add(number(obj[field]))
    except LookupError: return None,'업체 데이터의 사업자번호 형식 확인 필요'
 if len(found)>1: return None,'업체 데이터의 사업자번호가 서로 다릅니다'
 return (next(iter(found)),'번호 일치') if found else (None,'사업자번호 없음')

def latest(n,path):
 path=Path(path)
 if not path.is_file(): return None
 with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as con:
  row=con.execute('SELECT payload FROM nts_checks WHERE b_no=? ORDER BY checked_at DESC,check_id DESC LIMIT 1',(n,)).fetchone()
 return json.loads(row[0]) if row else None
