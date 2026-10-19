"""Read-only access to public registry and product evidence, without ranking claims."""
import json,os,sqlite3
from pathlib import Path
DEFAULT_DB=Path(__file__).resolve().parents[2]/'data/b2b_evidence/b2b_evidence.sqlite3'
QUESTIONS={'actual_seller':'실제 판매업체와 식별번호','processor':'가공 작업장과 식별번호','origin':'원산지','cut':'부위·세부 부위','grade':'등급과 판정 근거','temperature':'냉장·냉동','net_weight_kg':'순중량과 손질 기준','shipping_fee_krw':'수량·배송지별 배송비','observed_date':'현재 옵션·가격 조회일','transaction_stage':'도매 부분육 또는 소매 소포장 여부'}
def _connect():
 p=Path(os.getenv('B2B_EVIDENCE_DB',str(DEFAULT_DB))).resolve()
 if not p.is_file():raise ValueError('B2B_DB_NOT_INSTALLED')
 c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
 return c

def _registry(c):
 return [(json.loads(r['payload']),r['as_of']) for r in c.execute('''SELECT payload,as_of FROM (SELECT o.payload,s.as_of,ROW_NUMBER() OVER(PARTITION BY s.source,o.record_key ORDER BY s.as_of DESC,s.rowid DESC) rn FROM registry_observations o JOIN registry_snapshots s USING(snapshot_id)) WHERE rn=1''')]

def suppliers(kind='식육포장처리업',region='',source='mois_packing',include_unknown=False,offset=0,limit=30):
 if kind not in ('식육포장처리업','도축업','축산물유통전문판매업'):raise ValueError('INVALID_KIND')
 if not 1<=limit<=100 or offset<0:raise ValueError('INVALID_PAGINATION')
 with _connect() as c:records=_registry(c)
 rows=[]
 for p,received in records:
  if p.get('business_type')!=kind or source and p.get('source')!=source or region not in (p.get('address') or ''):continue
  if p.get('operation_status')=='inactive' or p.get('operation_status')!='active' and not include_unknown:continue
  rows.append({k:p.get(k) for k in ('record_key','name','business_type','license_no','management_no','address','phone','operation_status','source')})
  rows[-1].update(received_or_reference_date=received,dataset_effective_date=p.get('dataset_effective_date'),species=None,status='DISCOVERY_ONLY',questions=['현재 영업상태와 자료 기준일','소·돼지 취급 여부','가공 규격·수량·납기·유효 견적'])
 rows.sort(key=lambda p:(p['operation_status']!='active',p['name'],p['record_key']))
 return dict(status='OK',total=len(rows),offset=offset,items=rows[offset:offset+limit],scope='업체 탐색 후보. 현재 공급·품질·가격 추천 확정 아님')

def _links(product,registry):
 result=[]
 # A mapping must carry a source-scoped identifier and supporting evidence.
 for role,ref in product.get('registry_links',{}).items():
  if role not in ('actual_seller','processor') or not isinstance(ref,dict):continue
  if not ref.get('evidence_ref') or not ref.get('verified_on'):continue
  for p,received in registry:
   if ref.get('source')==p.get('source') and ref.get('record_key')==p.get('record_key'):
    result.append(dict(role=role,registry_record_key=p['record_key'],name=p['name'],operation_status=p.get('operation_status'),evidence_ref=ref['evidence_ref'],verified_on=ref['verified_on'],status='EXPLICIT_MAPPING_REQUIRES_CURRENT_VALIDATION'))
 return result

def products(species=None,stage=None,limit=30):
 if not 1<=limit<=100:raise ValueError('INVALID_LIMIT')
 with _connect() as c:
  raw=[json.loads(r[0]) for r in c.execute('SELECT payload FROM products ORDER BY product_id')]
  registry=_registry(c)
 result=[];excluded=0
 for p in raw:
  mismatch=species and p.get('species') is not None and p['species']!=species
  mismatch=mismatch or stage and p.get('transaction_stage') not in (None,'unverified','supply_list') and p['transaction_stage']!=stage
  if mismatch:excluded+=1;continue
  unknown=[f for f in QUESTIONS if p.get(f) in (None,'','unknown','unverified','supply_list')]
  item={k:p.get(k) for k in ('product_id','name','source_id','sales_channel','actual_seller','processor','origin','species','cut','grade','temperature','net_weight_kg','shipping_fee_krw','observed_date','transaction_stage','observed_price_krw','price_kind')}
  item.update(decision='HOLD',reason='최신 상품·옵션·견적·수량·납기와 항목별 근거 검증 필요',unknown_fields=unknown,supplier_questions=[QUESTIONS[x]+'를 확인해 주세요.' for x in unknown]+['현재 공급 가능 수량·배송 완료일·견적 유효기간을 확인해 주세요.'],registry_links=_links(p,registry),price_comparison_status='NOT_ESTABLISHED')
  result.append(item)
 return dict(status='OK',total=len(result),excluded_by_confirmed_condition=excluded,items=result[:limit],ranked_recommendations=[],scope='미확인은 보류. 관찰가격은 현재 유효 공급견적이 아님')
