# inventory_paths.py — 읽기 전용. 파일을 수정하지 않음.
import csv, re, sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "inventory.csv")
SKIP = {".git", "node_modules", ".venv", "venv", "dist", "__pycache__", "recipe_chat_api_backups"}
EXT = {".py", ".ts", ".tsx", ".js", ".yml", ".yaml", ".env.example", ".sql", ".sh"}

PATTERNS = {
    "mall_domain": r"meatbox|herbon|onbrix|meatfriends|hanwooeats|hyun-deok|dodrammall|"
                   r"delicious-market|saenong|emart\.ssg|ssg\.com|lotteon|lottemartzetta|homeplus|"
                   r"coupang\.com|shopping\.naver",
    "official_api": r"api-gateway\.coupang|openapi\.naver\.com|datalab|apis\.data\.go\.kr|"
                    r"foodsafetykorea|googleapis\.com/youtube",
    "http_client": r"\brequests\.(get|post)|httpx\.|aiohttp|urllib\.request|playwright|selenium|"
                   r"BeautifulSoup|scrapy|fetch\(",
    "llm_call": r"deepseek|api\.openai|openai\.|anthropic|chat\.completions|images\.generate|LLMClient",
    "storage": r"offer_observation|saved:|search_log|click_log|to_csv|json\.dump|INSERT INTO",
}
RX = {k: re.compile(v, re.I) for k, v in PATTERNS.items()}

rows = []
for p in ROOT.rglob("*"):
    if not p.is_file() or any(s in p.parts for s in SKIP):
        continue
    if p.suffix not in EXT and not p.name.endswith(".env.example"):
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
print(f"{len(rows)} hits → {OUT}")