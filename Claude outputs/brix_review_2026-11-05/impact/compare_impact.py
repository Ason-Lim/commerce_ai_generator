import json, csv, collections
b=json.load(open("impact_before.json",encoding="utf-8")); a=json.load(open("impact_after.json",encoding="utf-8"))
F=["fruit_brix_score","fruit_quality_score","ai_quality","brix_confidence","identity_score"]
rows=[]; changed=collections.Counter(); tiers=collections.Counter(); std=collections.Counter()
for x,y in zip(b["items"],a["items"]):
    assert x["name"]==y["name"]
    d={f:(x[f],y[f]) for f in F}
    ch=[f for f in F if x[f]!=y[f]]
    for f in ch: changed[f]+=1
    tiers[y["fruit_brix_tier"]]+=1; std["기준표 적용" if y["fruit_brix_standard"] else "기준표 없음(이전 구간)"]+=1
    rows.append([y["query"],y["name"],y["brix_name_parsed"],y["brix_get_value"],y["fruit_brix_standard"],y["fruit_brix_tier"]]+[v for f in F for v in d[f]]+[";".join(x["warnings"]),";".join(y["warnings"])])
with open("impact_items.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["query","name","brix(상품명)","brix(get_brix_value)","적용 기준","판정"]+[f"{f}_{s}" for f in F for s in ("before","after")]+["warnings_before","warnings_after"]); w.writerows(rows)
print("items",len(rows)); print("changed fields:",dict(changed)); print("tiers:",dict(tiers)); print("standard:",dict(std))
print("brix numeric in name:",sum(1 for r in rows if r[2]),"/",len(rows))
# rankings
rk=[]; moved=0; total=0
for key in b["rankings"]:
    B=[c["name"] for c in b["rankings"][key]]; A=[c["name"] for c in a["rankings"][key]]
    pos={n:i for i,n in enumerate(B)}
    top1=(B[:1]==A[:1]); top3=(B[:3]==A[:3]); same=(B==A)
    disp=sum(abs(pos[n]-i) for i,n in enumerate(A) if n in pos)
    rk.append([key,len(B),same,top1,top3,disp, B[0][:40] if B else "", A[0][:40] if A else ""])
with open("impact_rankings.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["query|mode","n","순서 동일","1위 동일","상위3 동일","순위 이동 합","1위(전)","1위(후)"]); w.writerows(rk)
print("rankings:",len(rk),"order changed:",sum(1 for r in rk if not r[2]),"top1 changed:",sum(1 for r in rk if not r[3]),"top3 changed:",sum(1 for r in rk if not r[4]))
for r in rk:
    if not r[2]: print("  ",r)
