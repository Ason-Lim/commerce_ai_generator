"""
naver_shopping_connect.py — commerce_ai × 네이버 쇼핑커넥트 링크풀 (M3 큐레이션 링크풀형)

역할 (2026-11-02 정리)
  * 화면에 링크를 붙이는 것은 app/services/chat/service.py 의 connect_links() 하나뿐이다.
    2026-11-04 네이버 회신으로 사이트 노출은 기본 꺼짐(NAVER_CONNECT_ON_SITE). 링크는 블로그에서만 쓴다.
    이 모듈은 등록부 점검(import 거부 사유)·검색 확인(match)·발급 요청 대기열(queue) 도구다.
  * attach_links()/log_click() 은 예비 코드이며 화면 경로에 연결하지 않는다(중복 표시 방지).
  * 대기열은 .env 에 SC_REQUEST_QUEUE=1 일 때 대화 중 '등록 링크 없음' 검색어가 쌓인다.

구조(설계 원안)
  1) 사람이 브랜드커넥트에서 링크를 발급 → CSV로 정리 → import_issued_links()로 적재
  2) 추천 엔진이 순위를 '먼저' 확정 → attach_links()가 매칭되는 링크만 붙임
     (수수료율은 정렬에 쓰지 않음: 고객 신뢰 우선 원칙)
  3) 노출 채널: blog(M1) 항상 허용 / site(M2)는 SITE_DIRECT_ENABLED 플래그로 제어
  4) 링크 없는 상품·급부상 요리는 발급 요청 대기열에 적재(M5)
  5) 클릭 로그만 자체 수집, 정산 데이터는 나중에 백오피스에서 병합

규칙(기존 결정 반영)
  - 주류 관련 질의에는 쇼핑커넥트 링크를 붙이지 않음
  - 발급된 naver.me 링크를 직접 오픈(/go 리다이렉트 경유 X) → 클릭은 프런트 beacon으로 기록
  - 정기구독·렌탈·쇼핑윈도·장보기 상품은 실적 제외이므로 적재 거부
  - 상품 URL(smartstore.naver.com/...)은 실적 불인정 → 적재 거부

사용 예
  python -m app.services.affiliate.naver_shopping_connect init
  python -m app.services.affiliate.naver_shopping_connect import   (기본: data/naver_connect_links.csv)
  python -m app.services.affiliate.naver_shopping_connect match 두쫀쿠
  python -m app.services.affiliate.naver_shopping_connect queue
  python -m app.services.affiliate.naver_shopping_connect queue-trends   (최신 급상승 리포트 → 대기열)
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

def _load_dotenv(path: str = ".env") -> None:
    """외부 패키지 없이 .env의 SC_ 설정만 읽는다(이미 설정된 환경변수는 유지)."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k.startswith("SC_"):
                    os.environ.setdefault(k, v.strip().strip('"').strip("'"))
    except OSError:
        pass


_load_dotenv()

_ROOT = Path(__file__).resolve().parents[3]   # 저장소 루트 — 실행 위치와 상관없이 같은 DB


def _from_root(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else _ROOT / path


DB_PATH = _from_root(os.getenv("SC_DB_PATH", "data/affiliate/shopping_connect.sqlite3"))
# 화면(chat.service.connect_links)과 같은 등록부를 쓴다
DEFAULT_CSV = os.getenv("NAVER_CONNECT_REGISTRY_CSV") or os.getenv("SC_LINKS_CSV", "data/naver_connect_links.csv")

# 네이버 회신 전까지 False. 허용 회신을 받으면 .env에서 1로 변경
SITE_DIRECT_ENABLED = os.getenv("SC_SITE_DIRECT_ENABLED", "0") == "1"

DISCLOSURE_SC = "이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 판매 발생 시 수수료를 제공받습니다."
DISCLOSURE_COUPANG = "* 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
DISCLOSURE_SITE_OPS = "발생한 수수료는 본 사이트의 무료 운영에 사용됩니다."

ALLOWED_LINK_HOSTS = {"naver.me", "brandconnect.naver.com"}
REJECT_LINK_HOSTS = {"smartstore.naver.com", "brand.naver.com", "shopping.naver.com"}

EXCLUDED_PRODUCT_KEYWORDS = ("정기구독", "정기배송", "렌탈", "쇼핑윈도", "장보기")
# chat.service.is_alcohol_request 와 같은 기준 (맛술·술빵 같은 조리 재료·음식은 제외)
_ALCOHOL = re.compile(r"와인|맥주|소주|막걸리|전통주|위스키|사케|하이볼|보드카|데킬라|리큐르|양주|청주|약주|과실주|"
                      r"칵테일|샴페인|브랜디|코냑|(?:^|[^가-힣])술(?![빵떡])|안주")


SCHEMA = """
CREATE TABLE IF NOT EXISTS sc_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name    TEXT NOT NULL,
    store_name      TEXT,
    category        TEXT,
    tags            TEXT,              -- 쉼표 구분 식재료/요리 태그
    link_url        TEXT NOT NULL UNIQUE,
    commission_rate REAL,              -- 참고용. 순위 계산에 사용 금지
    price           INTEGER,
    status          TEXT NOT NULL DEFAULT 'active',  -- active | paused | expired
    source          TEXT NOT NULL DEFAULT 'brandconnect_manual',
    issued_at       TEXT,
    updated_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sc_link_requests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword      TEXT NOT NULL,
    reason       TEXT,                 -- no_match | trend_dish | manual
    hit_count    INTEGER NOT NULL DEFAULT 1,
    status       TEXT NOT NULL DEFAULT 'open',      -- open | issued | skipped
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
-- 열린 요청만 키워드당 1건(완료·건너뜀 이력은 여러 건 허용)
CREATE UNIQUE INDEX IF NOT EXISTS uq_sc_req_open ON sc_link_requests(keyword) WHERE status='open';
CREATE TABLE IF NOT EXISTS affiliate_clicks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    network     TEXT NOT NULL,         -- naver_sc | coupang
    link_id     INTEGER,
    link_url    TEXT NOT NULL,
    channel     TEXT NOT NULL,         -- site | blog
    query       TEXT,
    session_key TEXT,                  -- 해시값만 저장
    clicked_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sc_links_status ON sc_links(status);
CREATE INDEX IF NOT EXISTS idx_clicks_time ON affiliate_clicks(clicked_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = Path(db_path or DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


# ---------------------------------------------------------------- 검증
def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[\s,/·()\[\]]+", text or "") if len(t) >= 2}


def is_alcohol_related(text: str) -> bool:
    t = re.sub(r"맛술|미림|술빵|술떡|요리술", "", text or "")
    return bool(_ALCOHOL.search(t))


def validate_link(url: str) -> str | None:
    """문제가 있으면 사유 문자열, 정상이면 None."""
    host = (urlparse(url).hostname or "").lower()
    if host in REJECT_LINK_HOSTS:
        return "상품 URL은 실적 불인정 — 브랜드커넥트 발급 링크 필요"
    if host not in ALLOWED_LINK_HOSTS:
        return f"허용되지 않은 링크 도메인: {host or '(없음)'}"
    return None


def validate_product(name: str, category: str = "") -> str | None:
    text = f"{name} {category}"
    for k in EXCLUDED_PRODUCT_KEYWORDS:
        if k in text:
            return f"실적 제외 유형({k})"
    if is_alcohol_related(text):
        return "주류 상품은 링크풀에서 제외"
    return None


# ---------------------------------------------------------------- 적재
# data/naver_connect_links.csv(한글 헤더)와 영문 헤더 모두 지원
COLUMN_ALIASES = {
    "product_name": ("product_name", "상품명"),
    "store_name": ("store_name", "스토어명"),
    "category": ("category", "카테고리"),
    "tags": ("tags", "키워드"),
    "link_url": ("link_url", "쇼핑커넥트 링크"),
    "commission_rate": ("commission_rate", "수수료율(%)"),
    "price": ("price", "판매가"),
    "issued_at": ("issued_at", "링크 발급일"),
    "channel": ("channel", "사용처(블로그/사이트)"),
    "memo": ("memo", "메모"),
}


def _normalize_row(raw: dict) -> dict:
    row = {}
    for key, names in COLUMN_ALIASES.items():
        for n in names:
            if n in raw and raw[n] not in (None, ""):
                row[key] = str(raw[n]).strip()
                break
    # '2026.11.2' → '2026-11-02'
    d = row.get("issued_at", "")
    m = re.match(r"^(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", d)
    if m:
        row["issued_at"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 숫자 정리: '598,000', '23%'
    for k in ("price", "commission_rate"):
        if k in row:
            row[k] = re.sub(r"[^\d.]", "", row[k])
    return row

@dataclass
class ImportResult:
    inserted: int = 0
    updated: int = 0
    rejected: list[tuple[int, str, str]] | None = None


def import_issued_links(conn: sqlite3.Connection, csv_path: str | Path) -> ImportResult:
    """
    CSV 컬럼: product_name, store_name, category, tags, link_url, commission_rate, price, issued_at
    (브랜드커넥트에서 수동 발급한 링크를 정리한 파일)
    """
    res = ImportResult(rejected=[])
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for i, raw in enumerate(csv.DictReader(f), start=2):
            row = _normalize_row(raw)
            name = (row.get("product_name") or "").strip()
            url = (row.get("link_url") or "").strip()
            reason = (not name and "상품명 없음") or validate_link(url) or validate_product(
                name, row.get("category", "")
            )
            if reason:
                res.rejected.append((i, name, reason))
                continue
            vals = (
                name,
                (row.get("store_name") or "").strip(),
                (row.get("category") or "").strip(),
                (row.get("tags") or "").strip(),
                url,
                float(row["commission_rate"]) if row.get("commission_rate") else None,
                int(float(row["price"])) if row.get("price") else None,
                (row.get("issued_at") or "").strip() or None,
                _now(),
            )
            cur = conn.execute("SELECT id FROM sc_links WHERE link_url = ?", (url,))
            if cur.fetchone():
                conn.execute(
                    """UPDATE sc_links SET product_name=?, store_name=?, category=?, tags=?,
                       commission_rate=?, price=?, issued_at=COALESCE(?, issued_at),
                       updated_at=?, status='active' WHERE link_url=?""",
                    (*vals[:4], *vals[5:], url),
                )
                res.updated += 1
            else:
                conn.execute(
                    """INSERT INTO sc_links (product_name, store_name, category, tags, link_url,
                       commission_rate, price, issued_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)""",
                    vals,
                )
                res.inserted += 1
            # 발급 요청 대기열에서 해결된 키워드 정리
            for tag in _tokens(row.get("tags", "")):
                conn.execute(
                    "UPDATE sc_link_requests SET status='issued', updated_at=? "
                    "WHERE keyword=? AND status='open'",
                    (_now(), tag),
                )
    conn.commit()
    return res


# ---------------------------------------------------------------- 매칭
def _score(link: sqlite3.Row, terms: set[str]) -> int:
    """링크-질의 연관도. 수수료는 절대 포함하지 않는다."""
    tags = _tokens(link["tags"] or "")
    name = link["product_name"] or ""
    s = 3 * len(tags & terms)
    s += sum(1 for t in terms if t in name)
    if link["category"] and link["category"] in terms:
        s += 1
    return s


def find_links(conn: sqlite3.Connection, text: str, limit: int = 3) -> list[dict]:
    terms = _tokens(text)
    if not terms:
        return []
    rows = conn.execute("SELECT * FROM sc_links WHERE status='active'").fetchall()
    scored = [(_score(r, terms), r) for r in rows]
    # 동점이면 최근 발급 우선(수수료 X)
    scored = [x for x in scored if x[0] > 0]
    scored.sort(key=lambda x: x[1]["id"])
    scored.sort(key=lambda x: x[1]["issued_at"] or "", reverse=True)
    scored.sort(key=lambda x: -x[0])  # 안정 정렬: 점수 → 최근 발급 → id
    return [
        {
            "link_id": r["id"],
            "product_name": r["product_name"],
            "store_name": r["store_name"],
            "price": r["price"],
            "url": r["link_url"],
            "network": "naver_sc",
        }
        for _, r in scored[:limit]
    ]


def queue_request(conn: sqlite3.Connection, keyword: str, reason: str = "no_match") -> None:
    conn.execute(
        """INSERT INTO sc_link_requests (keyword, reason, created_at, updated_at)
           VALUES (?,?,?,?)
           ON CONFLICT(keyword) WHERE status='open' DO UPDATE SET
             hit_count = hit_count + 1, updated_at = excluded.updated_at""",
        (keyword, reason, _now(), _now()),
    )
    conn.commit()


def attach_links(
    conn: sqlite3.Connection,
    query: str,
    ranked_items: list[dict],
    channel: str = "site",
    per_item: int = 1,
) -> dict:
    """
    ranked_items: 추천 엔진이 이미 순위를 확정한 항목 [{ 'name': ..., 'keywords': [...] }, ...]
    순서는 절대 바꾸지 않고 sc_links 필드만 덧붙인다.
    """
    out = {"items": [dict(it) for it in ranked_items], "disclosures": [], "sc_enabled": False}

    if channel == "site" and not SITE_DIRECT_ENABLED:
        out["blocked_reason"] = "site_direct_disabled"
        return out
    if is_alcohol_related(query):
        out["blocked_reason"] = "alcohol_query"
        return out

    attached = False
    for it in out["items"]:
        text = " ".join([it.get("name", ""), *it.get("keywords", [])])
        if is_alcohol_related(text):
            it["sc_links"] = []
            continue
        links = find_links(conn, text, limit=per_item)
        it["sc_links"] = links
        if links:
            attached = True
        else:
            queue_request(conn, it.get("name", "").strip() or query, "no_match")

    if attached:
        out["sc_enabled"] = True
        out["disclosures"] = [DISCLOSURE_SC, DISCLOSURE_SITE_OPS]
    return out


# ---------------------------------------------------------------- 급상승 요리 → 발급 요청(M5)
TREND_STATUSES = ("surging", "new")


def _registered(keyword: str) -> bool:
    """화면과 같은 기준(chat.service.registry_links)으로 등록부에 링크가 있는지 본다 (사이트 노출 여부와 무관)."""
    try:
        from app.services.chat.service import registry_links

        return bool(registry_links([keyword]))
    except Exception:  # noqa: BLE001 — 확인을 못 하면 '없음'으로 보고 요청을 남긴다
        return False


def queue_trends(conn: sqlite3.Connection, report: dict | None) -> list[str]:
    """급상승 리포트에서 등록 링크가 없는 식품 키워드를 발급 요청 대기열(reason=trend_dish)에 올린다."""
    queued = []
    for it in (report or {}).get("items") or []:
        kw = (it.get("keyword") or "").strip()
        if not kw or it.get("status") not in TREND_STATUSES or is_alcohol_related(kw):
            continue
        if _registered(kw):
            continue
        queue_request(conn, kw[:60], "trend_dish")
        queued.append(kw)
    return queued


def queue_trends_from_report(report: dict | None, enabled: bool | None = None) -> list[str]:
    """급상승 리포트 저장 직후 호출용. SC_REQUEST_QUEUE=1 일 때만, 실패해도 리포트에는 영향 없음."""
    if enabled is None:
        enabled = os.getenv("SC_REQUEST_QUEUE", "0") == "1"
    if not enabled:
        return []
    try:
        conn = connect()
        try:
            init_db(conn)
            return queue_trends(conn, report)
        finally:
            conn.close()
    except Exception:  # noqa: BLE001
        return []


# ---------------------------------------------------------------- 관리자 화면 (2026-11-02)
REASON_LABEL = {"no_match": "검색 미매칭", "trend_dish": "급상승", "manual": "직접"}
REQUEST_STATUSES = ("open", "issued", "skipped")


def list_requests(conn: sqlite3.Connection, status: str = "open", limit: int = 50) -> list[dict]:
    """발급 요청 목록 — 요청 많은 순.  registered=True 면 등록부에 이미 링크가 생긴 것(발급 완료로 정리하면 됨)."""
    rows = conn.execute(
        "SELECT id, keyword, reason, hit_count, status, created_at, updated_at FROM sc_link_requests "
        "WHERE status=? ORDER BY hit_count DESC, updated_at DESC LIMIT ?", (status, int(limit))).fetchall()
    return [dict(r, reason_label=REASON_LABEL.get(r["reason"], r["reason"]), registered=_registered(r["keyword"]))
            for r in rows]


def set_request_status(conn: sqlite3.Connection, req_id: int, status: str) -> bool:
    """open → issued(발급 완료) · skipped(건너뛰기), 또는 되돌리기(open).  같은 키워드의 열린 요청이 있으면 되돌리지 않는다."""
    if status not in REQUEST_STATUSES:
        raise ValueError(status)
    try:
        cur = conn.execute("UPDATE sc_link_requests SET status=?, updated_at=? WHERE id=?", (status, _now(), int(req_id)))
    except sqlite3.IntegrityError:
        return False
    conn.commit()
    return cur.rowcount == 1


def with_db(fn, *args, **kw):
    """관리자 API 용: 대기열 DB 를 열어 fn(conn, ...) 을 부르고 닫는다."""
    conn = connect()
    try:
        init_db(conn)
        return fn(conn, *args, **kw)
    finally:
        conn.close()


def link_needs(keywords: list[str]) -> dict:
    """블로그 초안의 키워드 중 쇼핑커넥트 등록 링크가 없는 것 / 있는 것 (주류는 링크를 넣지 않으므로 따로)."""
    need, have, alcohol = [], [], []
    for kw in keywords or []:
        kw = (kw or "").strip()
        if not kw:
            continue
        if is_alcohol_related(kw):
            alcohol.append(kw)
        elif _registered(kw):
            have.append(kw)
        else:
            need.append(kw)
    return {"need": need, "have": have, "alcohol": alcohol}


def operator_memo(needs: dict) -> str:
    """초안 파일 맨 위에 붙이는 운영 메모 (블로그에는 붙여 넣지 않는다)."""
    lines = ["[운영 메모 — 블로그에 붙여 넣지 마세요]"]
    lines.append("쇼핑커넥트 링크 발급이 필요한 키워드: " + (", ".join(needs["need"]) or "없음"))
    if needs["have"]:
        lines.append("등록부에 링크가 있는 키워드: " + ", ".join(needs["have"]))
    if needs["alcohol"]:
        lines.append("주류 키워드(쇼핑커넥트 링크 넣지 않음): " + ", ".join(needs["alcohol"]))
    lines.append("발급한 링크는 블로그 글에만 넣어요 (네이버 정책상 자체 사이트·앱에는 쓸 수 없음). 등록부 CSV 에도 적어 두면 다음 점검에 반영돼요.")
    lines.append("─" * 30)
    return "\n".join(lines)


# ---------------------------------------------------------------- 클릭 로그
def log_click(
    conn: sqlite3.Connection,
    link_url: str,
    channel: str,
    network: str = "naver_sc",
    link_id: int | None = None,
    query: str | None = None,
    session_id: str | None = None,
) -> None:
    """프런트에서 naver.me를 직접 여는 순간 beacon으로 호출(/go 리다이렉트 미사용)."""
    key = hashlib.sha256(session_id.encode()).hexdigest()[:16] if session_id else None
    conn.execute(
        """INSERT INTO affiliate_clicks (network, link_id, link_url, channel, query, session_key, clicked_at)
           VALUES (?,?,?,?,?,?,?)""",
        (network, link_id, link_url, channel, query, key, _now()),
    )
    conn.commit()


def blog_link_block(links: list[dict]) -> str:
    """블로그(M1) 원고에 붙일 텍스트 블록. 고지문은 상단·하단 모두 배치."""
    lines = [DISCLOSURE_SC, ""]
    for l in links:
        price = f" ({l['price']:,}원)" if l.get("price") else ""
        lines.append(f"- {l['product_name']}{price}: {l['url']}")
    lines += ["", DISCLOSURE_SC, DISCLOSURE_SITE_OPS]
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI
def _main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 0
    conn = connect()
    init_db(conn)
    cmd = argv[0]
    if cmd == "init":
        print(f"초기화 완료: {DB_PATH}")
    elif cmd == "import":
        path = argv[1] if len(argv) > 1 else str(_from_root(DEFAULT_CSV))
        r = import_issued_links(conn, path)
        print(f"CSV: {path}")
        print(f"추가 {r.inserted} · 갱신 {r.updated} · 거부 {len(r.rejected)}")
        for line, name, why in r.rejected:
            print(f"  {line}행 {name or '-'}: {why}")
    elif cmd == "match" and len(argv) > 1:
        q = " ".join(argv[1:])
        for l in find_links(conn, q, limit=5):
            print(f"{l['link_id']:>4}  {l['product_name']}  {l['url']}")
    elif cmd == "queue-trends":
        from app.services.trends import surge

        got = queue_trends(conn, surge.load(argv[1] if len(argv) > 1 else None))
        print(f"대기열에 올림 {len(got)}건: {', '.join(got) or '-'}")
    elif cmd == "queue":
        rows = conn.execute(
            "SELECT keyword, reason, hit_count FROM sc_link_requests "
            "WHERE status='open' ORDER BY hit_count DESC, updated_at DESC LIMIT 30"
        ).fetchall()
        if not rows:
            on = os.getenv("SC_REQUEST_QUEUE", "0") == "1"
            print("발급 요청 대기열이 비어 있어요."
                  + ("" if on else " (.env 에 SC_REQUEST_QUEUE=1 이 없어 대화·매일 리포트에서 쌓지 않는 중)")
                  + "\n최신 급상승 리포트에서 바로 채우려면: python -m app.services.affiliate.naver_shopping_connect queue-trends")
        label = {"no_match": "검색 미매칭", "trend_dish": "급상승", "manual": "직접"}
        for r in rows:
            print(f"{r['hit_count']:>3}회  {r['keyword']}  ({label.get(r['reason'], r['reason'])})")
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
