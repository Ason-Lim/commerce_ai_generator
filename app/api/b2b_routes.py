import sqlite3
from fastapi import APIRouter,HTTPException,Query
from app.services.b2b_evidence import suppliers,products
router=APIRouter(prefix='/b2b',tags=['B2B evidence'])
def run(fn,**kwargs):
 try:return fn(**kwargs)
 except (ValueError,sqlite3.Error):raise HTTPException(status_code=503,detail='B2B 근거 DB 또는 요청 조건을 확인해 주세요.') from None
@router.get('/suppliers')
def get_suppliers(kind:str='식육포장처리업',region:str=Query('',max_length=50),source:str=Query('mois_packing',max_length=100),include_unknown:bool=False,offset:int=Query(0,ge=0),limit:int=Query(30,ge=1,le=100)):
 return run(suppliers,kind=kind,region=region,source=source,include_unknown=include_unknown,offset=offset,limit=limit)
@router.get('/products')
def get_products(species:str|None=Query(None,pattern='^(beef|pork)$'),stage:str|None=Query(None,pattern='^(wholesale_primal|retail_small_pack)$'),limit:int=Query(30,ge=1,le=100)):
 return run(products,species=species,stage=stage,limit=limit)
