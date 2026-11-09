# check_naver_malls.py — 네이버 쇼핑 자료 확인. 읽기 전용 (DB 를 바꾸지 않음). (2026-11-04)
# 1) 네이버 쇼핑 검색 API(shop.json)가 지금 응답하는지 1회 확인 — 2026-11-04 확인 결과 HTTP 404 'SE05'
#    (네이버 공지: 검색 쇼핑·책·전문자료 API 2026-07-31 종료). 같은 키로 뉴스·블로그 검색은 정상.
# 2) DB(online_food_price_snapshot)에 남은 행이 언제 수집된 것인지 원천별로 센다 — 대화 DB 대체 경로가
#    API 종료 전의 오래된 네이버 가격을 섞어 보여 줄 수 있는지 확인용.
# 3) 예전에 쌓인 네이버 행에서 '감귤' 등 상품의 판매처(mallName) 분포 — SSG·홈플러스·롯데·GS·컬리·오아시스가
#    실제로 얼마나 있었는지 (어느 몰과 제휴를 문의할지 정하는 참고 자료).
# 결과: 화면 요약 + Claude outputs/naver_malls_20261104.csv.  키는 화면·파일에 남기지 않는다.
# 사용: 저장소 폴더에서  python check_naver_malls.py        (다른 상품: python check_naver_malls.py 사과 한라봉)
import csv
import os
import re
import sys
from collections import Counter
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(os.path.join(os.getcwd(), ".env"))
from app.core.config import DATABASE_URL  # noqa: E402

WORDS = sys.argv[1:] or ["감귤", "한우 등심", "삼겹살"]
TARGETS = {
    "SSG·신세계·이마트": r"ssg|신세계|이마트|emart",
    "홈플러스": r"홈플러스|homeplus",
    "롯데(ON·마트)": r"롯데|lotte",
    "GS(fresh·샵)": r"gs\s*fresh|gs프레시|gs샵|gsshop|gs리테일|gs더프레시",
    "컬리": r"컬리|kurly",
    "오아시스": r"오아시스|oasis",
    "쿠팡": r"쿠팡|coupang",
}


def group(mall: str, url: str = "") -> str:
    low = f"{mall or ''} {url or ''}".lower()
    return next((name for name, rx in TARGETS.items() if re.search(rx, low)), "기타")


# 1) API 확인 (1회)
headers = {"X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID") or "",
           "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET") or ""}
for api in ("shop.json", "news.json"):
    try:
        r = requests.get(f"https://openapi.naver.com/v1/search/{api}", headers=headers,
                         params={"query": WORDS[0], "display": 1}, timeout=10)
        code = re.search(r'"errorCode"\s*:\s*"([^"]+)"', r.text)
        print(f"[API] {api}: HTTP {r.status_code}" + (f" errorCode={code.group(1)}" if code else ""))
    except Exception as e:  # noqa: BLE001
        print(f"[API] {api}: 연결 실패 {type(e).__name__}")

# 2)·3) DB
eng = create_engine(DATABASE_URL, pool_pre_ping=True)
rows = []
with eng.connect() as c:
    c.execute(text("SET TRANSACTION READ ONLY"))
    print("\n== 원천별 저장 행 (수집 시각) ==")
    print("source_type | 행 | 가장 이른 수집 | 가장 늦은 수집 | 2026-07-31 이후")
    for st, n, lo, hi, after in c.execute(text(
            "SELECT coalesce(source_type,'(null)'), count(*), min(collected_at), max(collected_at), "
            "count(*) FILTER (WHERE collected_at >= '2026-07-31') FROM online_food_price_snapshot "
            "GROUP BY 1 ORDER BY 2 DESC")):
        print(f"{st} | {n} | {lo} | {hi} | {after}")
    for w in WORDS:
        like = "%" + w.replace(" ", "%") + "%"
        got = list(c.execute(text(
            "SELECT coalesce(source_type,'(null)'), coalesce(mall_name,''), product_name, price, collected_at, "
            "coalesce(product_url, redirect_url, raw_link, '') FROM online_food_price_snapshot "
            "WHERE product_name ILIKE :k ORDER BY collected_at DESC NULLS LAST LIMIT 2000"), {"k": like}))
        print(f"\n== '{w}' 저장 행 {len(got)}개 (최근 2,000개까지) — 판매처 묶음 ==")
        by = Counter(group(m, u) for _s, m, _n, _p, _t, u in got)
        for name in list(TARGETS) + ["기타"]:
            mine = [(m, t) for _s, m, _n, _p, t, u in got if group(m, u) == name]
            if mine:
                malls = ", ".join(f"{m or '(없음)'} {k}" for m, k in Counter(m for m, _t in mine).most_common(4))
                last = max((t for _m, t in mine if t), default=None)
                print(f"  {name}: {by[name]}개 (마지막 수집 {last}) — {malls}")
            else:
                print(f"  {name}: 0개")
        for s, m, n, p, t, u in got:
            rows.append({"상품어": w, "원천": s, "판매처": m, "판매처 묶음": group(m, u), "상품명": n, "가격": p,
                         "수집 시각": t})

dest = Path("Claude outputs")
dest.mkdir(exist_ok=True)
path = dest / "naver_malls_20261104.csv"
with path.open("w", newline="", encoding="utf-8-sig") as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["상품어"])
    wr.writeheader()
    wr.writerows(rows)
print(f"\n저장: {path} ({len(rows)}행)")
