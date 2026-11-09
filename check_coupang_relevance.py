# check_coupang_relevance.py — 읽기 전용 비교. DB를 바꾸지 않고, 판매처 API도 부르지 않는다. (2026-11-03 p39)
# 목적: 저장된 검색 결과(상품명)에 새 관련성 규칙(app/services/commerce/relevance.py)을 적용하면
#       무엇이 유지되고 무엇이 '확인 불가'로 바뀌는지 센다.  실제 경로에는 아직 적용하지 않았다.
# 자료: (1) online_food_price_snapshot 의 keyword·상품명  (2) 대화 기록(recipe_chat_session)의 '본 후보'(seen) 검색어·상품명
# 결과: 화면 요약 + Claude outputs/coupang_relevance_compare_20261103.csv  (세션 ID 등 개인 식별 정보는 넣지 않음)
# 사용: 저장소 폴더에서  python check_coupang_relevance.py
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import DATABASE_URL
from app.services.chat.service import shopping_terms
from app.services.commerce.relevance import LABELS, classify

eng = create_engine(DATABASE_URL, pool_pre_ping=True)
rows: list[tuple[str, str, str, str]] = []          # (자료, 검색어, 상품명, 판매처)
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    try:
        for kw, name, src, mall in c.execute(text(
                "SELECT DISTINCT keyword, product_name, coalesce(source_type,'(null)'), coalesce(mall_name,'') "
                "FROM online_food_price_snapshot WHERE keyword IS NOT NULL AND product_name IS NOT NULL")):
            rows.append((f"snapshot:{src}", kw, name, mall))
    except Exception as e:  # noqa: BLE001
        print("snapshot 읽기 실패:", type(e).__name__)
    try:
        seen = set()
        for (state_json,) in c.execute(text("SELECT state_json FROM recipe_chat_session")):
            try:
                state = json.loads(state_json)
            except (TypeError, ValueError):
                continue
            for s in state.get("seen") or []:
                for card in s.get("cards") or []:
                    k = (s.get("query") or "", card.get("title") or "")
                    if k[0] and k[1] and k not in seen:
                        seen.add(k)
                        rows.append(("chat_seen", k[0], k[1], card.get("mall") or ""))
    except Exception as e:  # noqa: BLE001
        print("대화 기록 읽기 실패:", type(e).__name__)

counts: dict[str, Counter] = defaultdict(Counter)
multi: Counter = Counter()
out = []
for source, query, title, mall in rows:
    _q, terms = shopping_terms(query)
    got = classify(title, terms)
    counts[source][got["verdict"]] += 1
    if terms and len(terms) >= 2:
        multi[source] += 1
    out.append({"자료": source, "검색어": query, "낱말": " ".join(terms or []), "상품명": title, "판매처": mall,
                "분류": LABELS[got["verdict"]], "확인 못 한 낱말": " ".join(got["missing"]),
                "동의어로 확인": " ".join(got["synonym"])})

print("\n== 자료별 분류 (새 규칙 적용 시) ==")
print("자료 | 행 | 낱말 2개 이상 | 유지 | 품목·부위 확인 불가 | 조건 확인 불가 | 기존에도 제외")
for src, cnt in sorted(counts.items(), key=lambda kv: -sum(kv[1].values())):
    print(f"{src} | {sum(cnt.values())} | {multi[src]} | {cnt['keep']} | {cnt['item_unconfirmed']} | "
          f"{cnt['condition_unconfirmed']} | {cnt['old_excluded']}")
print("\n== 바뀌는 예 (기존 통과 → 확인 불가, 최대 25) ==")
changed = [r for r in out if r["분류"] in (LABELS["item_unconfirmed"], LABELS["condition_unconfirmed"])]
for r in changed[:25]:
    print(f"{r['검색어']} | {r['상품명'][:45]} | {r['분류']} | 없음: {r['확인 못 한 낱말']}")
dest = Path("Claude outputs")
dest.mkdir(exist_ok=True)
path = dest / "coupang_relevance_compare_20261103.csv"
with path.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["자료"])
    w.writeheader()
    w.writerows(out)
print(f"\n저장: {path} ({len(out)}행, 바뀌는 행 {len(changed)})")
