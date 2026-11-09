"""Read-only Excel input and explicit batch lookup. Existing UI remains intact."""
import csv,io,hashlib,sqlite3,zipfile
from pathlib import Path
try:
 from app.services import nts_lookup as client
except ModuleNotFoundError:
 import nts_lookup as client

LIMIT=500
class ExcelError(Exception):pass

def read_excel(data,suffix):
 if len(data)>5*1024*1024:raise ExcelError('파일은 5MB 이하로 올려 주세요.')
 try:
  if suffix.lower()=='.xlsx':
   from openpyxl import load_workbook
   with zipfile.ZipFile(io.BytesIO(data)) as z:
    if sum(x.file_size for x in z.infolist())>20*1024*1024:raise ExcelError('압축 해제 후 크기가 너무 큽니다. 필요한 행만 남겨 주세요.')
   wb=load_workbook(io.BytesIO(data),read_only=True,data_only=False,keep_links=False)
   try:
    sheets={}
    for ws in wb.worksheets:
     if len(sheets)>=20:raise ExcelError('시트는 20개 이하로 줄여 주세요.')
     if ws.max_row>LIMIT+1 or ws.max_column>50:raise ExcelError('각 시트를 500개 데이터 행과 50개 열 이하로 줄여 주세요.')
     rows=[]
     for row in ws.iter_rows(max_row=LIMIT+2,max_col=51,values_only=True):rows.append(list(row))
     sheets[ws.title]=rows
    return sheets
   finally:wb.close()
  if suffix.lower()=='.xls':
   import xlrd
   wb=xlrd.open_workbook(file_contents=data,on_demand=True)
   try:
    if any(wb.sheet_by_index(i).nrows>LIMIT+1 or wb.sheet_by_index(i).ncols>50 for i in range(wb.nsheets)):raise ExcelError('각 시트를 500개 데이터 행과 50개 열 이하로 줄여 주세요.')
    if wb.nsheets>20:raise ExcelError('시트는 20개 이하로 줄여 주세요.')
    return {s.name:[s.row_values(i)[:51] for i in range(min(s.nrows,LIMIT+2))] for s in (wb.sheet_by_index(i) for i in range(wb.nsheets))}
   finally:wb.release_resources()
  raise ExcelError('.xlsx 또는 .xls 파일을 올려 주세요.')
 except ImportError:raise ExcelError('엑셀 읽기 패키지가 없습니다. openpyxl 및 xlrd 설치를 확인해 주세요.') from None
 except ExcelError:raise
 except Exception:raise ExcelError('엑셀을 읽지 못했습니다. 암호 없는 정상 Excel 파일인지 확인해 주세요.') from None

def prepare(rows,column,name_column=None,catalog=None):
 records=[];seen=set()
 for index,row in enumerate(rows[1:],2):
  if not any(v not in (None,'') for v in row):continue
  if len(records)>=LIMIT:raise ExcelError('선택한 시트는 500행 이하로 나누어 올려 주세요.')
  value=row[column] if column is not None and column<len(row) else None
  # Numeric Excel cells may have lost a leading zero: never invent digits.
  if isinstance(value,float) and value.is_integer():value=int(value)
  text='' if value is None else str(value).strip()
  name=str(row[name_column] or '').strip() if name_column is not None and name_column<len(row) else ''
  record={'회사명':name,'등록된 회사명':'미확인','주요 제품':'미확인','위치':'미확인','규모 참고':'미확인','회사 정보 출처':'엑셀 입력 · 회사명/번호 연결 확인 전','엑셀 행':index,'입력 번호':text,'사업자등록번호':'','입력 확인':'','국세청 상태':'미조회','과세유형':'','폐업일자':'','조회 시각':'','저장 상태':''}
  if not text and name and catalog:
   try:
    from app.services.nts_companies import normalize
   except ModuleNotFoundError:
    from nts_companies import normalize
   candidates=[p for p in catalog if normalize(p['company_name'])==normalize(name) and p.get('business_no')]
   nums=set(p['business_no'] for p in candidates)
   if len(nums)==1:text=next(iter(nums));record['회사 정보 출처']='회사명 정확일치 후보 · '+candidates[0]['source']
   elif len(nums)>1:record['입력 확인']='동명 회사의 번호가 여러 개입니다. 번호를 입력해 주세요.';record['국세청 상태']='조회 제외';records.append(record);continue
  for label in ('주요 제품','위치','규모 참고'):
   idx=next((j for j,h in enumerate(rows[0]) if str(h or '').replace(' ','')==label.replace(' ','')),None)
   if idx is not None and idx<len(row) and row[idx] not in (None,''):record[label]=str(row[idx])+' (엑셀 입력·확인 전)'
  try:
   n=client.number(text);record['사업자등록번호']=n
   record['입력 확인']='중복 (한 번만 조회)' if n in seen else '정상';seen.add(n)
  except client.LookupError as e:record['입력 확인']=str(e);record['국세청 상태']='조회 제외'
  if record['사업자등록번호'] and catalog:
   candidates=[p for p in catalog if p.get('business_no')==record['사업자등록번호']]
   if candidates:
    p=candidates[0]
    record['등록된 회사명']=p['company_name']
    if not record['회사명']:record['회사명']=p['company_name']
    for label,field in [('주요 제품','products'),('위치','location'),('규모 참고','scale')]:
     if record[label]=='미확인':record[label]=p.get(field) or '미확인'
    record['회사 정보 출처']=p['source']
  records.append(record)
 return records

def run_batch(records,path,on_progress=None):
 from datetime import datetime
 from zoneinfo import ZoneInfo
 numbers=list(dict.fromkeys(r['사업자등록번호'] for r in records if r['사업자등록번호']))
 outcomes={};attempts=0;failure=''
 for start in range(0,len(numbers),100):
  chunk=numbers[start:start+100];attempts+=1
  try:checks=client.lookup_many(chunk)
  except client.LookupError as e:
   failure=str(e)
   for n in chunk:outcomes[n]={'국세청 상태':'조회 실패','저장 상태':'미저장'}
   break
  for check,raw in checks:
   r=check['result'];saved='저장 완료'
   try:client.save(check,raw,path)
   except (OSError,sqlite3.Error):saved='저장 실패 (조회 완료)'
   outcomes[check['b_no']]={'국세청 상태':{'01':'계속사업자 (사업 중)','02':'휴업자','03':'폐업자'}.get(r.get('business_status_code'),'상태 미확인'),'과세유형':r.get('tax_type') or '', '폐업일자':r.get('closed_date') or '', '조회 시각':datetime.fromisoformat(check['checked_at']).astimezone(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S 한국시간'),'저장 상태':saved}
  if on_progress:on_progress(min(start+100,len(numbers)),len(numbers))
 result=[]
 for original in records:
  row=dict(original);n=row['사업자등록번호']
  if n in outcomes:row.update(outcomes[n])
  elif n:row['국세청 상태']='미조회 (앞선 요청 실패로 중단)' if failure else '미조회'
  result.append(row)
 return result,attempts,failure

def csv_bytes(rows):
 out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(rows[0]) if rows else ['사업자등록번호']);writer.writeheader()
 # Prevent spreadsheet formula execution in downloaded user input.
 for row in rows:
  writer.writerow({k:("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v) for k,v in row.items()})
 return out.getvalue().encode('utf-8-sig')

def render_excel(st,path):
 with st.expander('엑셀로 여러 사업자등록번호 조회',expanded=False):
  st.caption('첫 행은 열 제목으로 작성하세요. 회사명만 있는 행은 저장된 회사 정보와 정확히 일치하고 번호가 하나인 경우 후보 번호를 표시합니다. 미리보기를 확인한 뒤 조회하세요. 시트당 500행, 파일 5MB까지 지원합니다. 같은 번호는 한 번만 조회합니다.')
  st.download_button('업로드 양식 받기 (CSV)',data='회사명,사업자등록번호\n'.encode('utf-8-sig'),file_name='사업자번호_업로드양식.csv',mime='text/csv',key='nts_excel_template')
  st.caption('양식에 번호를 입력한 뒤 Excel 통합 문서(.xlsx)로 저장해 올려 주세요. 번호 열은 텍스트 형식을 권장합니다.')
  file=st.file_uploader('사업자번호 엑셀 파일',type=['xlsx','xls'],key='nts_excel_upload')
  if file is None:return
  data=file.getvalue();fingerprint=hashlib.sha256(data).hexdigest()
  try:
   book=read_excel(data,Path(file.name).suffix)
   sheet=st.selectbox('조회할 시트',list(book),key='nts_excel_sheet_'+fingerprint)
   rows=book[sheet]
   if not rows or not any(x not in (None,'') for x in rows[0]):raise ExcelError('첫 행에 열 제목을 넣어 주세요.')
   if any(len(r)>50 and r[50] not in (None,'') for r in rows):raise ExcelError('열을 50개 이하로 줄여 주세요.')
   columns=[str(v or '제목 없음')+' (열 '+str(i+1)+')' for i,v in enumerate(rows[0][:50])]
   preferred=next((i+1 for i,v in enumerate(rows[0][:50]) if str(v).replace(' ','') in ('사업자등록번호','사업자번호','b_no','BRNO')),0)
   col=st.selectbox('사업자등록번호 열 (번호가 없으면 선택 안 함)',[None]+list(range(len(columns))),format_func=lambda i:'사용하지 않음' if i is None else columns[i],index=preferred,key='nts_excel_column_'+fingerprint+sheet)
   names=[i for i,v in enumerate(rows[0][:50]) if str(v).replace(' ','') in ('회사명','업체명','상호','상호명','기업명')]
   name_col=st.selectbox('회사명 열 (선택)',[None]+list(range(len(columns))),format_func=lambda i:'사용하지 않음' if i is None else columns[i],index=(names[0]+1 if names else 0),key='nts_excel_name_'+fingerprint+sheet)
   from app.services.nts_companies import profiles
   catalog=profiles(path)
   if col is None and name_col is None:raise ExcelError('사업자등록번호 열 또는 회사명 열을 선택해 주세요.')
   prepared=prepare(rows,col,name_col,catalog)
  except ExcelError as e:st.error(str(e));return
  key='nts_excel_result_'+fingerprint+hashlib.sha256((sheet+str(col)+str(name_col)).encode()).hexdigest()[:12]
  valid=len(set(r['사업자등록번호'] for r in prepared if r['사업자등록번호']))
  invalid=sum(not r['사업자등록번호'] for r in prepared)
  st.write('전체 '+str(len(prepared))+'행 · 조회할 고유 번호 '+str(valid)+'개 · 잘못된 번호 '+str(invalid)+'행')
  st.dataframe(prepared,use_container_width=True)
  if st.button('엑셀 번호 국세청 일괄조회',disabled=not valid,key=key+'_submit'):
   progress=st.progress(0)
   with st.spinner('국세청 상태를 조회하고 있습니다…'):
    result,calls,error=run_batch(prepared,path,lambda done,total:progress.progress(done/total))
   st.session_state[key]=(result,calls,error)
  if key in st.session_state:
   result,calls,error=st.session_state[key]
   st.markdown('**엑셀 조회 결과**')
   if error:st.error(error+' 이후 번호는 조회하지 않았습니다.')
   else:st.success('일괄조회를 마쳤습니다.')
   st.caption('국세청 요청 '+str(calls)+'회. 결과는 조회 시각 기준이며 업체명·인허가·공급 가능 여부를 확인하는 결과는 아닙니다.')
   st.dataframe(result,use_container_width=True)
   st.download_button('조회 결과 다운로드 (Excel에서 여는 CSV)',data=csv_bytes(result),file_name='국세청_사업자상태_조회결과.csv',mime='text/csv',key=key+'_download')
