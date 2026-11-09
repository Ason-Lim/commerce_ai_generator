# inventory_paths.py — 읽기 전용 인벤토리. 저장소 파일을 수정하지 않음.
# 사용: python inventory_paths.py <저장소 경로> [출력 CSV]
import csv, re, sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").expanduser().resolve()
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "inventory.csv")
SKIP = {".git", "node_modules", ".venv", "venv", "dist", "__pycache__", ".pytest_cache", "ocr_results"}
EXT = {".py", ".ts", ".tsx", ".js", ".yml", ".yaml", ".sql", ".sh"}

PATTERNS = {
    "mall_domain": r"meatbox|herbon|onbrix|meatfriends|hanwooeats|hyun-deok|dodrammall|"
                   r"delicious-market|saenong|emart\.ssg|ssg\.com|lotteon|lottemartzetta|homeplus|"
                   r"coupang\.com|shopping\.naver|smartstore\.naver",
    "official_api": r"api-gateway\.coupang|openapi\.naver\.com|datalab|apis\.data\.go\.kr|"
                    r"foodsafetykorea|googleapis\.com/youtube",
    "http_client": r"\brequests\.(get|post)|httpx\.|aiohttp|urllib\.request|playwright|selenium|"
                   r"BeautifulSoup|scrapy|fetch\(",
    "user_agent": r"User-Agent|user_agent\s*=",
    "llm_call": r"deepseek|api\.openai|from openai|import openai|anthropic|chat\.completions|"
                r"images\.generate|chat_json\(",
    "storage": r"offer_observation|online_food_price_snapshot|INSERT INTO|UPDATE online_|to_csv|json\.dump",
}
RX = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}

def skipped(p: Path) -> bool:
    parts = p.relative_to(ROOT).parts
    return any(s in SKIP or "backup" in s.lower() for s in parts)

rows = []
for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or skipped(p) or p.name == Path(__file__).name:
        continue
    if p.suffix not in EXT and p.name != ".env.example":   # 실제 .env는 키 노출 방지를 위해 제외
        continue
    try:
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        continue
    for i, line in enumerate(lines, 1):
        for kind, rx in RX.items():
            m = rx.search(line)
            if m:
                rows.append([kind, str(p.relative_to(ROOT)), i, m.group(0), line.strip()[:160]])

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["kind", "file", "line", "match", "context"])
    w.writerows(rows)

# 요약: 같은 파일에 몰 도메인 + HTTP 클라이언트 → 페이지 수집 후보
by_file = {}
for kind, file, *_ in rows:
    by_file.setdefault(file, set()).add(kind)
scrape = sorted(f for f, k in by_file.items() if {"mall_domain", "http_client"} <= k and not f.startswith("tests/"))
llm = sorted(f for f, k in by_file.items() if "llm_call" in k and not f.startswith("tests/"))
print(f"{len(rows)} hits → {OUT}")
print("\n[페이지 수집 후보: 몰 도메인 + HTTP 클라이언트]"); print("\n".join("  " + f for f in scrape) or "  없음")
print("\n[외부 LLM 호출 파일]"); print("\n".join("  " + f for f in llm) or "  없음")
