"""클릭·구매 연결 — 측정 기록 (2026-11-24, 병행 창 '클릭·구매 연결'). 설계 claude/click_purchase_link_design_2026-11-16.md.

**측정용이다. 추천 순위에 쓰지 않는다.** (순위 동결 — 기준점 s10/d10)

무엇을 남기나 (쿠팡 약관 제5조 ③: 상품명·가격은 남기지 않음)
* 노출(impression): 대화 답에 보여 준 상품 — 날짜·시각, 세션(가명 해시), 채널, 자리(main·collapsed·extra), 순위, 상품 번호, 판매처 종류.
* 클릭(click): /go 로 판매처에 보낸 클릭 — 같은 칸 + 자리(chat·chat_extra·saved·search_link·trend·home_*).
* 채널: ``site``(손님) · ``test``(가족·지인 시험 — 브라우저에 /test-mode/on 쿠키) · ``internal``(관리자로 로그인한 브라우저).
  주간 보고는 site 만 기본으로 세고 test·internal 은 따로 보여 준다.
* 상품 번호는 쿠팡 리포트의 ``ctag`` 와 맞출 열쇠다(리포트는 상품 단위). 사람 단위 연결은 하지 않는다.

보존: 원본 줄은 1년(처리방침 '검색·클릭 1년'과 같게), 그 전에 날짜·채널·자리·판매처·상품 번호별 숫자로 접어 둔다(세션 값 없음).
세션 값은 원문이 아니라 키 해시(MEASURE_KEY 또는 데이터 폴더 measure.key) — 같은 날 노출과 클릭을 잇는 데만 쓴다.
기록 실패는 대화·이동을 막지 않는다.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import sqlalchemy
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    delete,
    func,
    select,
)

log = logging.getLogger(__name__)
KST = timezone(timedelta(hours=9))
KEEP_DAYS = 365
TEST_COOKIE = "cai_test"
CHANNELS = ("site", "test", "internal")

meta = MetaData()
t_event = Table(
    "measure_event",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("kind", String(10), nullable=False),  # impression · click
    Column("at", DateTime(timezone=True), nullable=False),
    Column("day", Date, index=True, nullable=False),
    Column("sid_h", String(16)),  # 세션 가명 해시
    Column("channel", String(8), nullable=False),
    Column("surface", String(24), nullable=False),
    Column("rank", Integer),
    Column("pid", String(24), index=True),  # 쿠팡 상품 번호(또는 판매처 상품 번호) — 모르면 None
    Column("platform", String(16)),  # coupang · naver · partner · other
)
t_daily = Table(
    "measure_daily",
    meta,  # 접어 둔 숫자 (세션 값 없음) — 원본을 지운 뒤에도 남는다
    Column("day", Date, primary_key=True),
    Column("kind", String(10), primary_key=True),
    Column("channel", String(8), primary_key=True),
    Column("surface", String(24), primary_key=True),
    Column("platform", String(16), primary_key=True),
    Column("pid", String(24), primary_key=True),  # 모르면 ''
    Column("n", Integer, nullable=False),
)
t_report = Table(
    "measure_coupang_report",
    meta,  # 쿠팡 파트너스 리포트 (매일 받아 최근 30일 덮어씀) — 금액은 여기에만, 문서·커밋에 쓰지 않음
    Column("day", Date, primary_key=True),
    Column("sub_id", String(32), primary_key=True),  # 채널 아이디 (사이트·블로그·시험)
    Column("kind", String(12), primary_key=True),  # clicks · orders · cancels · commission
    Column("pid", String(24), primary_key=True),  # ctag(상품 번호) — 날짜 합계 줄은 ''
    Column("line", Integer, primary_key=True),  # 같은 날·상품에 여러 줄(주문 여러 건)일 때 순번
    Column("clicks", Integer),
    Column("qty", Integer),
    Column("amount", Integer),  # 주문 금액(gmv) — 모르면 None
    Column("commission", Integer),
    Column("raw", Text),  # 원본 한 줄(JSON) — 필드가 아직 확정되지 않아 보관
    Column("fetched_at", DateTime(timezone=True)),
)
t_fetch = Table(
    "measure_coupang_fetch",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("at", DateTime(timezone=True)),
    Column("start", Date),
    Column("end", Date),
    Column("sub_id", String(32)),
    Column("kind", String(12)),
    Column("status", String(12)),  # ok · error · skipped
    Column("rows", Integer),
    Column("note", String(200)),
)

_ENGS: dict = {}


def now() -> datetime:
    return datetime.now(KST)


def engine(url: str | None = None):
    """측정 DB — MEASURE_DB_URL, 없으면 MEASURE_DIR(기본 var/measure)/measure.sqlite3 (운영 DB 표 구조를 바꾸지 않음)."""
    if not url:
        url = os.getenv("MEASURE_DB_URL") or ""
    if not url:
        d = Path(os.getenv("MEASURE_DIR", "var/measure"))
        d.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{d / 'measure.sqlite3'}"
    if url not in _ENGS:
        eng = sqlalchemy.create_engine(url, future=True)
        meta.create_all(eng)
        _ENGS[url] = eng
    return _ENGS[url]


def reset_engine() -> None:  # 시험용
    _ENGS.clear()


def enabled() -> bool:
    """MEASURE=off 면 기록하지 않는다(시험·비상용)."""
    return os.getenv("MEASURE", "on").lower() not in ("off", "0", "false", "no")


def _key() -> bytes:
    k = os.getenv("MEASURE_KEY")
    if k:
        return k.encode()
    p = Path(os.getenv("MEASURE_DIR", "var/measure")) / "measure.key"
    try:
        return p.read_bytes()
    except FileNotFoundError:
        p.parent.mkdir(parents=True, exist_ok=True)
        b = secrets.token_hex(32).encode()
        p.write_bytes(b)
        return b


def sid_hash(sid: str | None) -> str | None:
    if not sid:
        return None
    return hmac.new(_key(), str(sid).encode(), hashlib.sha256).hexdigest()[:16]


def channel(request) -> str:
    """요청의 채널 — 관리자 로그인 브라우저는 internal, 시험 쿠키가 있으면 test, 그 밖은 site."""
    try:
        from app.admin.auth import request_ok

        if request is not None and request_ok(request):
            return "internal"
    except Exception:  # noqa: BLE001
        pass
    try:
        if request is not None and request.cookies.get(TEST_COOKIE) == "1":
            return "test"
    except Exception:  # noqa: BLE001
        pass
    return "site"


_PID = re.compile(r"^[0-9A-Za-z_-]{1,24}$")


def _pid(card: dict | None, url: str | None = None) -> str | None:
    from app.services.cs import blocked

    pid = blocked.product_id(card or ({"url": url} if url else None))
    return pid if pid and _PID.fullmatch(pid) else None


def _platform(card: dict | None, url: str | None) -> str:
    u = str(url or (card or {}).get("url") or "")
    if (card or {}).get("affiliate") or "coupang.com" in u:
        return "coupang"
    if (card or {}).get("partner"):
        return "partner"
    if "naver" in u:
        return "naver"
    return "other"


def _insert(rows: list[dict]) -> None:
    if not rows:
        return
    try:
        with engine().begin() as c:
            c.execute(t_event.insert(), rows)
    except Exception:  # noqa: BLE001 — 기록이 대화·이동을 막지 않는다
        log.warning("measure record failed", exc_info=True)


def _row(kind: str, sid: str | None, ch: str, surface: str, rank, pid, platform, at: datetime | None) -> dict:
    at = at or now()
    return {
        "kind": kind,
        "at": at,
        "day": at.astimezone(KST).date(),
        "sid_h": sid_hash(sid),
        "channel": ch if ch in CHANNELS else "site",
        "surface": surface[:24],
        "rank": int(rank) if isinstance(rank, int) or (isinstance(rank, str) and rank.isdigit()) else None,
        "pid": pid,
        "platform": platform,
    }


def impressions_from_response(response: dict) -> list[tuple[str, dict]]:
    """대화 응답의 상품 칸 → [(자리, 카드)]. 자리: main(펼친 추천) · collapsed(접힌 다른 후보) · extra(추가 후보)."""
    from app.services.chat.miss_signals import EXTRA_TITLE

    out = []
    for b in response.get("blocks") or []:
        if b.get("type") != "product_list":
            continue
        data = b.get("data") or {}
        where = (
            "extra"
            if EXTRA_TITLE in str(data.get("title") or "")
            else ("collapsed" if data.get("collapsed") else "main")
        )
        for it in data.get("items") or []:
            if isinstance(it, dict) and (it.get("go") or it.get("url")):
                out.append((where, it))
    return out


def record_impressions(response: dict, ch: str, *, at: datetime | None = None) -> int:
    if not enabled():
        return 0
    try:
        sid = response.get("session_id")
        rows = [
            _row("impression", sid, ch, f"chat_{where}", it.get("rank"), _pid(it), _platform(it, it.get("url")), at)
            for where, it in impressions_from_response(response)
        ]
    except Exception:  # noqa: BLE001
        log.warning("measure impressions failed", exc_info=True)
        return 0
    _insert(rows)
    return len(rows)


def record_click(
    sid: str | None, ch: str, surface: str, *, card: dict | None = None, url: str | None = None, rank=None, at=None
) -> None:
    if not enabled():
        return
    try:
        row = _row("click", sid, ch, surface, rank if rank is not None else (card or {}).get("rank"),
                   _pid(card, url), _platform(card, url), at)  # fmt: skip
    except Exception:  # noqa: BLE001 — 기록이 이동을 막지 않는다
        log.warning("measure click failed", exc_info=True)
        return
    _insert([row])


# ── 접기·보존 ──
def fold(eng=None, *, until: date | None = None) -> int:
    """어제까지의 원본을 일별 숫자로 접는다 — 같은 날을 다시 접으면 덮어써 두 번 세지 않음."""
    eng = eng or engine()
    until = until or (now().date() - timedelta(days=1))
    with eng.begin() as c:
        days = [d for (d,) in c.execute(select(t_event.c.day).where(t_event.c.day <= until).distinct()).all()]
        for d in days:
            c.execute(delete(t_daily).where(t_daily.c.day == d))
            rows = c.execute(
                select(
                    t_event.c.kind,
                    t_event.c.channel,
                    t_event.c.surface,
                    t_event.c.platform,
                    func.coalesce(t_event.c.pid, ""),
                    func.count(),
                )
                .where(t_event.c.day == d)
                .group_by(t_event.c.kind, t_event.c.channel, t_event.c.surface, t_event.c.platform, t_event.c.pid)
            ).all()
            if rows:
                c.execute(
                    t_daily.insert(),
                    [
                        {"day": d, "kind": k, "channel": ch, "surface": s, "platform": pl or "other", "pid": p, "n": n}
                        for k, ch, s, pl, p, n in rows
                    ],
                )
    return len(days)


def purge(eng=None, *, today: date | None = None) -> int:
    """1년 지난 원본 줄을 지운다(먼저 접는다)."""
    eng = eng or engine()
    today = today or now().date()
    cut = today - timedelta(days=KEEP_DAYS)
    fold(eng, until=cut)
    with eng.begin() as c:
        return c.execute(delete(t_event).where(t_event.c.day < cut)).rowcount


def daily_counts(eng, start: date, end: date) -> list[dict]:
    """[start, end] 의 일별 숫자 — 접은 날은 measure_daily, 아직 안 접은 날은 원본에서."""
    with eng.connect() as c:
        folded = {
            d
            for (d,) in c.execute(
                select(t_daily.c.day).where(and_(t_daily.c.day >= start, t_daily.c.day <= end)).distinct()
            ).all()
        }
        out = [
            dict(r._mapping)
            for r in c.execute(select(t_daily).where(and_(t_daily.c.day >= start, t_daily.c.day <= end))).all()
        ]
        raw = c.execute(
            select(
                t_event.c.day,
                t_event.c.kind,
                t_event.c.channel,
                t_event.c.surface,
                t_event.c.platform,
                func.coalesce(t_event.c.pid, "").label("pid"),
                func.count().label("n"),
            )
            .where(and_(t_event.c.day >= start, t_event.c.day <= end))
            .group_by(
                t_event.c.day, t_event.c.kind, t_event.c.channel, t_event.c.surface, t_event.c.platform, t_event.c.pid
            )
        ).all()
    out += [dict(r._mapping) for r in raw if r.day not in folded]
    return out


__all__ = [
    "KST",
    "CHANNELS",
    "TEST_COOKIE",
    "engine",
    "reset_engine",
    "sid_hash",
    "channel",
    "impressions_from_response",
    "record_impressions",
    "record_click",
    "fold",
    "purge",
    "daily_counts",
    "t_event",
    "t_daily",
    "t_report",
    "t_fetch",
]
