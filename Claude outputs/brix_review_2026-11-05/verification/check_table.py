import sys, csv, itertools, importlib.util
from collections import defaultdict, Counter
P=sys.argv[1]
spec=importlib.util.spec_from_file_location("b","app/services/food_intelligence/brix_standards.py"); b=importlib.util.module_from_spec(spec); sys.modules["b"]=b; spec.loader.exec_module(b)
S=b.FRUIT_BRIX_STANDARDS; lab=lambda s:f"{s.fruit}/{s.variety or '공통'}"
print("# 기준표 모듈 점검 (app/services/food_intelligence/brix_standards.py)")
print("행 수:",len(S)); print("품목 수:",len({s.fruit for s in S}))
print("근거 유형:",dict(Counter(s.basis for s in S)))
print("출하 하한 없는 행:",sum(1 for s in S if s.floor is None),"/",len(S))
print("순서 오류(top<=high 또는 floor>high):",[lab(s) for s in S if not s.top>s.high or (s.floor is not None and s.floor>s.high)])
print("출처 키 누락:",[lab(s) for s in S if not set(s.sources)<=set(b.SOURCES)])
print("출처 없는 행:",[lab(s) for s in S if not s.sources])
kw=defaultdict(list)
for s in S:
    for k in s.keywords: kw[b._norm(k)].append(lab(s))
print("같은 키워드를 쓰는 행:",{k:v for k,v in kw.items() if len(v)>1} or "없음")
mis=[(k,lab(s),lab(r) if r else None) for s in S for k in s.keywords if (r:=b.find_standard(k+" 2kg")) is not s]
print("키워드 단독(+' 2kg')이 자기 행으로 가지 않는 경우:",mis or "없음")
print("\n## 다른 행 키워드 안에 들어 있는 키워드 (품종이 우선하므로 의도된 겹침)")
for a,c in itertools.permutations([(b._norm(k),s) for s in S for k in s.keywords],2):
    if a[0]!=c[0] and a[0] in c[0] and a[1] is not c[1]: print(f"  '{a[0]}'({lab(a[1])}) ⊂ '{c[0]}'({lab(c[1])})")
print("\n## 오판 위험 시험 (상품명 → 적용 행)")
for n in ["골든볼 황금사과 3kg","꿀사과 홍로 5kg","천하명품 제주 감귤 고당도 황금향 레드향 한라봉 천혜향","냉동딸기 1kg","복숭아 병조림 핑크백도 490g","사과즙 100포","딸기잼 500g","반도체","배송비 무료","샤인 머스캣 2kg","제주 귤 5kg"]:
    r=b.find_standard(n); print(f"  {n} → {lab(r) if r else '기준 없음'}")
with open(P+"/verification/brix_table_dump.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["품목","품종","키워드","조사범위","출하하한","고당도","최상","근거유형","출처키","비고"])
    for s in S: w.writerow([s.fruit,s.variety or "공통","|".join(s.keywords),s.typical,s.floor,s.high,s.top,s.basis,"|".join(s.sources),s.note])
