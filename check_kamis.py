# check_kamis.py — KAMIS 키 동작 확인(읽기 전용). 키 값은 출력하지 않음.
# KAMIS Open API는 인증키(p_cert_key)와 신청 아이디(p_cert_id)를 함께 요구한다.
import json, os, sys, urllib.parse, urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(".env")
key = (os.getenv("KAMIS_API_KEY") or "").strip()
cid = (os.getenv("KAMIS_CERT_ID") or "").strip()
print("KAMIS_API_KEY:", "있음" if key else "없음", "| KAMIS_CERT_ID:", "있음" if cid else "없음 (.env에 KAMIS_CERT_ID=신청아이디 추가 필요)")
if not key:
    sys.exit(1)
q = urllib.parse.urlencode({"action": "dailySalesList", "p_cert_key": key, "p_cert_id": cid, "p_returntype": "json"})
try:
    with urllib.request.urlopen("https://www.kamis.or.kr/service/price/xml.do?" + q, timeout=20) as r:
        body = r.read().decode("utf-8", "replace")
        print("HTTP", r.status)
        out = Path("data/kamis"); out.mkdir(parents=True, exist_ok=True)
        (out / "sample_dailySalesList.json").write_text(body, encoding="utf-8")
        print("원본 저장: data/kamis/sample_dailySalesList.json")
except Exception as e:
    print("요청 실패:", type(e).__name__, e); sys.exit(1)
try:
    data = json.loads(body)
    items = data.get("price") or []
    print("결과 코드:", data.get("error_code"), "| 품목 수:", len(items))
    for it in items[:5]:
        print(" ", it.get("productName") or it.get("item_name"), it.get("unit"), it.get("dpr1"), it.get("lastest_day") or "")
except ValueError:
    print("JSON 아님 — 앞부분:", body[:300].replace(key, "***"))
