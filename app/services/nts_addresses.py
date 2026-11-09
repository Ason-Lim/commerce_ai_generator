"""Source-specific address display. Never rewrites registry or number evidence."""
# Reviewed against the official manufacturer's product page on 2026-10-26.
VERIFIED=[dict(source='localdata_food_manufacturing_csv',record_key='localdata_food_manufacturing_csv:5790000-106-1955-00001',name='매일식품주식회사',registry_address='전남광주통합특별시 순천시 서면 산단1길 16',official_name='매일식품(주)',official_address='전라남도 순천시 서면 산단1길 16',url='https://maeilfoods.com/jin-ganjang/',checked_on='2026-10-26',section='제품정보 · 제조원 업소명 및 소재지')]

def comparison(p):
 r=p.get('registry_record')
 if not r:return None
 evidence=next((e for e in VERIFIED if all(r.get(k)==e[k] for k in ('source','record_key','name'))),None)
 if evidence and r.get('address')!=evidence['registry_address']:return dict(record=r,evidence=None,status='명부 주소 변경 — 공식 사이트 주소 재대조 필요')
 return dict(record=r,evidence=evidence,status=('표기 일치' if r.get('address')==evidence['official_address'] else '주소 표기 다름') if evidence else '공식 사이트 주소 미확인')

def render_addresses(st,p):
 data=comparison(p)
 if data is None:return
 r=data['record'];e=data['evidence'];unknown='미확인'
 st.markdown('**출처별 주소 비교**')
 st.table([
  {'항목':'주소','명부 원문 주소':r.get('address') or unknown,'회사 공식 사이트 표기 주소':e['official_address'] if e else unknown},
  {'항목':'업체명','명부 원문 주소':r.get('name') or unknown,'회사 공식 사이트 표기 주소':e['official_name'] if e else unknown},
  {'항목':'출처','명부 원문 주소':r.get('source') or unknown,'회사 공식 사이트 표기 주소':e['url'] if e else unknown},
  {'항목':'기준일 / 확인일','명부 원문 주소':p.get('reviewed_on') or unknown,'회사 공식 사이트 표기 주소':e['checked_on'] if e else unknown},
 ])
 st.caption('주소 비교: '+data['status']+' · 명부 원문은 수집 CSV에서 저장된 주소이며, 공식 사이트 주소는 별도 출처의 표기입니다.')
 if e:
  st.write('공식 사이트 주소 출처: '+e['url'])
  st.caption('확인 위치: '+e['section'])
 st.caption('표기 차이만으로 오류·행정구역 변경·동일 사업장 여부를 판정하지 않습니다. 주소와 사업자번호 연결 기록은 변경하지 않습니다.')
