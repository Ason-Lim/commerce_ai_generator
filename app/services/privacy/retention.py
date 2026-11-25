"""보존 기간 작업 — '접고 지우기' (2026-11-21 사용자 결정, claude/privacy_policy_draft_2026-11-21.md §3).

결정
* 대화 문장(대화 상태·레시피 대화 상태)·실수 신호: **90일** 뒤 지움. 대화 90일·보관함 1년은 **마지막 활동(updated_at)**부터,
  검색·클릭 1년은 **기록한 날(created_at)**부터, 실수 신호 90일은 파일 날짜부터 센다.
* 가명 흐름(1년 뒤 세션 값을 바꾼 원본 줄)은 기록한 날부터 PRIVACY_PSEUDO_KEEP_DAYS(기본 3년) 뒤 지움 (2026-11-22).
* 관심 상품 보관함: 마지막 사용 뒤 **1년** 지나면 지움.
* 세션이 붙은 검색·클릭·노출 기록과 클릭 선호: **1년** 원본, 그 뒤 세션 값을 가명 값으로 바꿔 흐름만 남김
  (가명 키 PRIVACY_PSEUDO_KEY 는 .env 에 따로 — 키가 없으면 가명 처리는 건너뛰고 알림).
* **집계(검색어·상품별 일별 숫자)는 계속 보관** — 세션 값이 없는 숫자만. 원본을 바꾸거나 지우기 전에 늘 먼저 접는다.
* 모든 단계는 privacy_job_log 에 남긴다(시각·대상·건수·기준 시각) — 가명 처리 기록 보관 의무 대비.

순서(매일 한 번, 같은 날 두 번 돌려도 결과가 같게): ① 어제까지 원본을 일별 집계로 접기(접은 위치를 기록해 두 번 세지 않음)
→ ② 1년 지난 세션 값 가명 처리 → ③ 90일·1년 지난 대화·보관함 지우기 → ④ 90일 지난 실수 신호 파일 접고 지우기.
DB 는 운영(PostgreSQL)·시험(SQLite) 모두 같은 SQL 로 — 날짜 계산은 파이썬에서 하고 기준 시각만 넘긴다.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import DateTime, bindparam, text

CHAT_DAYS = 90
SIGNAL_DAYS = 90
SAVED_DAYS = 365
LOG_DAYS = 365
# 2026-11-22 (검토 의견 6): 가명 흐름의 최종 삭제 — 만든 날부터 이 기간이 지나면 원본 줄을 지운다(집계는 남음).
# 사용자 결정 전 기본값 3년. PRIVACY_PSEUDO_KEEP_DAYS 로 바꿈 (처리방침 '가명정보 보유 기간' 칸과 같은 값).
PSEUDO_KEEP_DAYS_DEFAULT = 1095
AGG_TEXT_MAX = 40
AGG_HIDDEN = "(긴 문장·가린 문장)"
PSEUDO_PREFIX = "p_"

ROLLUP_DDL = (
    """CREATE TABLE IF NOT EXISTS search_daily (
        day TEXT NOT NULL, query TEXT NOT NULL, priority TEXT NOT NULL,
        searches INTEGER NOT NULL, zero_results INTEGER NOT NULL,
        PRIMARY KEY (day, query, priority))""",
    """CREATE TABLE IF NOT EXISTS click_daily (
        day TEXT NOT NULL, channel TEXT NOT NULL, product_name TEXT NOT NULL, platform TEXT NOT NULL,
        section TEXT NOT NULL, clicks INTEGER NOT NULL,
        PRIMARY KEY (day, channel, product_name, platform, section))""",
    """CREATE TABLE IF NOT EXISTS impression_daily (
        day TEXT NOT NULL, query TEXT NOT NULL, product_name TEXT NOT NULL, section TEXT NOT NULL,
        impressions INTEGER NOT NULL,
        PRIMARY KEY (day, query, product_name, section))""",
    """CREATE TABLE IF NOT EXISTS privacy_rollup_state (
        source TEXT PRIMARY KEY, rolled_until TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS privacy_job_log (
        run_at TEXT NOT NULL, step TEXT NOT NULL, target TEXT NOT NULL, rows INTEGER NOT NULL, cutoff TEXT)""",
)

# 원본 → 집계: (원본 표, 집계 표, 고르는 칼럼, 묶는 열쇠 만들기, 더하는 값들)
def agg_text(q: str | None) -> str:
    """집계 표에 남길 검색어 — 개인정보 모양이 있거나 너무 긴 문장(한 사람만 쓸 법한)은 '(긴 문장·가린 문장)' 하나로 묶는다.
    2026-11-22 검토 의견 6: 검색어별 집계에 드문 개인정보성 문장이 그대로 남지 않게."""
    from app.services.privacy import pii

    text = " ".join(str(q or "").split())
    masked, kinds = pii.mask(text)
    if kinds or masked != text or "***" in text or len(text) > AGG_TEXT_MAX:
        return AGG_HIDDEN
    return text


_ROLLUPS = {
    "search_log": ("search_daily", "query, priority, result_count",
                   lambda r: (agg_text(r["query"]), r["priority"] or ""),
                   lambda r: {"searches": 1, "zero_results": 1 if (r["result_count"] or 0) == 0 else 0},
                   ("query", "priority")),
    "product_click_log": ("click_daily", "query, product_name, platform, selected_section",
                          lambda r: (r["query"] or "", r["product_name"] or "", r["platform"] or "",
                                     r["selected_section"] or ""),
                          lambda r: {"clicks": 1}, ("channel", "product_name", "platform", "section")),
    "impression_log": ("impression_daily", "query, product_name, selected_section",
                       lambda r: (agg_text(r["query"]), r["product_name"] or "", r["selected_section"] or ""),
                       lambda r: {"impressions": 1}, ("query", "product_name", "section")),
}
# 1년 뒤 세션 값을 가명으로: (표, 시각 칼럼)
_PSEUDO = (("search_log", "created_at"), ("product_click_log", "created_at"), ("impression_log", "created_at"),
           ("user_product_preference", "updated_at"), ("user_fruit_preference", "updated_at"))


def _ts(name: str):
    return bindparam(name, type_=DateTime(timezone=False))


def pseudonym(session_id: str, key: bytes) -> str:
    return PSEUDO_PREFIX + hmac.new(key, session_id.encode(), hashlib.sha256).hexdigest()[:24]


class Retention:
    def __init__(self, engine, *, now: datetime | None = None, pseudo_key: str | None = None,
                 signal_dir: Path | str | None = None, dry_run: bool = False):
        self.engine = engine
        # DB 칼럼은 서버 지역 시각(TIMESTAMP) — 기준 시각도 시간대 없이 넘긴다
        self.now = (now or datetime.now()).replace(tzinfo=None, microsecond=0)
        raw = pseudo_key if pseudo_key is not None else os.environ.get("PRIVACY_PSEUDO_KEY", "")
        self.key = raw.strip().encode() if raw and len(raw.strip()) >= 16 else None
        self.signal_dir = Path(signal_dir) if signal_dir else Path(__file__).resolve().parents[3] / "var" / "signals"
        self.dry_run = dry_run
        self.report: list[dict] = []

    # ── 공통 ──
    def _tables(self, conn) -> set[str]:
        from sqlalchemy import inspect

        return set(inspect(conn).get_table_names())

    def _log(self, conn, step: str, target: str, rows: int, cutoff: datetime | None) -> None:
        self.report.append({"step": step, "target": target, "rows": rows,
                            "cutoff": cutoff.isoformat(sep=" ") if cutoff else None})
        if not self.dry_run:
            conn.execute(text("INSERT INTO privacy_job_log (run_at, step, target, rows, cutoff) VALUES (:a,:s,:t,:r,:c)"),
                         {"a": self.now.isoformat(sep=" "), "s": step, "t": target, "r": rows,
                          "c": cutoff.isoformat(sep=" ") if cutoff else None})

    def run(self) -> list[dict]:
        with self.engine.begin() as conn:
            for ddl in ROLLUP_DDL:
                conn.execute(text(ddl))
            have = self._tables(conn)
            self.rollup(conn, have)
            self.pseudonymize(conn, have)
            self.delete_chat(conn, have)
            self.strip_cards(conn, have)
            self.delete_pseudo(conn, have)
        self.signals()
        self.cs_tickets()
        return self.report

    # ── ⑥ 문의 티켓 (2026-11-23 창 4 ③): 요약 90일 · 티켓 1년 ──
    def cs_tickets(self) -> None:
        from app.services.cs import tickets as cs_tickets

        if self.dry_run:
            return
        try:
            got = cs_tickets.prune(self.now.replace(tzinfo=cs_tickets.KST))
        except Exception:  # noqa: BLE001
            return
        self.report.append({"step": "cs_tickets", "target": "var/cs/tickets.json", "rows": got["cleared"] + got["removed"],
                            "cutoff": None})
        try:                                     # 2026-11-24 B2B 폐쇄몰: 배송 완료 뒤 보존 기간 지난 배송 정보
            from app.services.corpmall import store as corpmall

            m = corpmall.purge(corpmall.engine(), self.now.replace(tzinfo=corpmall.KST))
            self.report.append({"step": "corpmall_shipping", "target": "corpmall_order.ship_enc", "rows": m, "cutoff": None})
        except Exception:  # noqa: BLE001
            pass
        try:                                     # 2026-11-25 셀러 센터: 계약 종료 뒤 1년 지난 담당자 연락처
            from app.services.seller import store as seller

            m = seller.purge(seller.engine(), self.now.replace(tzinfo=seller.KST))
            self.report.append({"step": "seller_contact", "target": "seller_account.contact_enc", "rows": m, "cutoff": None})
            from app.services.seller import scm as seller_scm  # ③ 주문 받는 분(출고 뒤 30일·미출고 90일)·공급사 연락처

            m = seller_scm.purge(seller_scm.engine(), self.now.replace(tzinfo=seller.KST))
            self.report.append({"step": "seller_orders", "target": "seller_order.ship_enc", "rows": m, "cutoff": None})
            from app.services.seller import health as seller_health  # 죽은 셀러몰 — 새 후보만 운영자 알림(개인정보 아님)

            h = seller_health.daily_check(seller_scm.engine())
            self.report.append({"step": "seller_dormant", "target": "seller_event", "rows": len(h["flagged"]), "cutoff": None})
        except Exception:  # noqa: BLE001
            pass
        try:                                     # 2026-11-24 B2B 문의: 종결 뒤 180일 지난 담당자 연락처
            from app.services.b2b_inquiry import store as b2b_inquiry

            m = b2b_inquiry.purge(b2b_inquiry.engine(), self.now.replace(tzinfo=b2b_inquiry.KST))
            self.report.append({"step": "b2b_inquiry_contact", "target": "b2b_inquiry.contact_enc", "rows": m, "cutoff": None})
        except Exception:  # noqa: BLE001
            pass
        try:                                     # 2026-11-23 창 4 ④: 분야 검수 샘플 문장 90일
            from app.services.cs import review as cs_review

            n = cs_review.prune(self.now.replace(tzinfo=cs_review.KST))
        except Exception:  # noqa: BLE001
            return
        self.report.append({"step": "cs_review", "target": "var/cs/review/*.jsonl", "rows": n, "cutoff": None})

    # ── ① 일별 집계로 접기 ──
    def rollup(self, conn, have: set[str]) -> None:
        today = datetime.combine(self.now.date(), datetime.min.time())
        for source, (target, cols, key_of, vals_of, key_names) in _ROLLUPS.items():
            if source not in have:
                continue
            state = conn.execute(text("SELECT rolled_until FROM privacy_rollup_state WHERE source=:s"),
                                 {"s": source}).scalar()
            start = datetime.fromisoformat(state) if state else datetime(2000, 1, 1)
            if start >= today:
                continue
            rows = conn.execute(text(f"SELECT created_at, {cols} FROM {source} "  # noqa: S608 — 고정 이름
                                     "WHERE created_at >= :a AND created_at < :b").bindparams(_ts("a"), _ts("b")),
                                {"a": start, "b": today}).mappings().all()
            sums: dict[tuple, Counter] = {}
            for r in rows:
                day = _day(r["created_at"])
                sums.setdefault((day, *key_of(r)), Counter()).update(vals_of(r))
            if not self.dry_run:
                for k, v in sums.items():
                    names = ("day", *key_names)
                    params = dict(zip(names, k)) | dict(v)
                    sets = ", ".join(f"{c} = {target}.{c} + excluded.{c}" for c in v)
                    conn.execute(text(
                        f"INSERT INTO {target} ({', '.join(params)}) VALUES ({', '.join(':' + p for p in params)}) "
                        f"ON CONFLICT ({', '.join(names)}) DO UPDATE SET {sets}"), params)
                upd = conn.execute(text("UPDATE privacy_rollup_state SET rolled_until=:u WHERE source=:s"),
                                   {"u": today.isoformat(sep=" "), "s": source})
                if upd.rowcount == 0:
                    conn.execute(text("INSERT INTO privacy_rollup_state (source, rolled_until) VALUES (:s, :u)"),
                                 {"s": source, "u": today.isoformat(sep=" ")})
            self._log(conn, "rollup", f"{source}→{target}", len(rows), today)

    # ── ② 1년 지난 세션 값 가명 처리 ──
    def pseudonymize(self, conn, have: set[str]) -> None:
        cut = self.now - timedelta(days=LOG_DAYS)
        if self.key is None:
            self.report.append({"step": "pseudonymize", "target": "(건너뜀)", "rows": 0, "cutoff": None,
                                "note": ".env PRIVACY_PSEUDO_KEY(16자 이상)가 없어 1년 지난 세션 값을 바꾸지 못했어요"})
            return
        for table, col in _PSEUDO:
            if table not in have:
                continue
            sids = [r[0] for r in conn.execute(text(
                f"SELECT DISTINCT session_id FROM {table} WHERE {col} < :c "  # noqa: S608
                f"AND session_id IS NOT NULL AND session_id NOT LIKE '{PSEUDO_PREFIX}%'").bindparams(_ts("c")),
                {"c": cut}).all()]
            n = 0
            for sid in sids:
                if self.dry_run:
                    continue
                n += conn.execute(text(f"UPDATE {table} SET session_id=:p WHERE session_id=:s AND {col} < :c"  # noqa: S608
                                       ).bindparams(_ts("c")),
                                  {"p": pseudonym(str(sid), self.key), "s": sid, "c": cut}).rowcount or 0
            self._log(conn, "pseudonymize", table, n if not self.dry_run else len(sids), cut)

    # ── ③ 대화 문장·보관함 지우기 ──
    def delete_chat(self, conn, have: set[str]) -> None:
        chat_cut = self.now - timedelta(days=CHAT_DAYS)
        saved_cut = self.now - timedelta(days=SAVED_DAYS)
        jobs = (("recipe_chat_session", "session_id NOT LIKE 'saved:%'", chat_cut, "대화·레시피 대화 상태"),
                ("recipe_chat_session", "session_id LIKE 'saved:%'", saved_cut, "관심 상품 보관함"),
                ("recipe_followup_state", "1=1", chat_cut, "레시피 보유량 상태"),
                ("recipe_material_review", "1=1", chat_cut, "레시피 재료 검토"))
        for table, where, cut, label in jobs:
            if table not in have:
                continue
            sql = f"FROM {table} WHERE {where} AND updated_at < :c"  # noqa: S608 — 고정 이름
            if self.dry_run:
                n = conn.execute(text("SELECT COUNT(*) " + sql).bindparams(_ts("c")), {"c": cut}).scalar() or 0
            else:
                n = conn.execute(text("DELETE " + sql).bindparams(_ts("c")), {"c": cut}).rowcount or 0
            self._log(conn, "delete", f"{table} ({label})", n, cut)

    # ── ③-2 대화 상태 안 쿠팡 상품 카드 줄이기 (2026-11-23 — 쿠팡 오픈 API 약관 제5조 ③) ──
    def strip_cards(self, conn, have: set[str]) -> None:
        """마지막 활동 24시간 지난 대화의 상품 카드는 키·순위·링크만 남긴다 (app/services/chat/card_expiry.py).
        관심 상품 보관함(saved:…)은 그대로 (사용자 결정 11-23). updated_at 은 바꾸지 않는다(대화 90일 기준 유지)."""
        if "recipe_chat_session" not in have:
            return
        import json as _json

        from app.services.chat import card_expiry

        cut = self.now - timedelta(hours=card_expiry.hours())
        rows = conn.execute(text("SELECT session_id, state_json FROM recipe_chat_session "
                                 "WHERE session_id NOT LIKE 'saved:%' AND updated_at < :c").bindparams(_ts("c")),
                            {"c": cut}).mappings().all()
        n = 0
        for row in rows:
            try:
                state = _json.loads(row["state_json"])
            except (TypeError, ValueError):
                continue
            if not isinstance(state, dict) or not card_expiry.has_cards(state):
                continue
            n += 1
            if not self.dry_run:
                conn.execute(text("UPDATE recipe_chat_session SET state_json=:j WHERE session_id=:s"),
                             {"j": _json.dumps(card_expiry.strip(state), ensure_ascii=False), "s": row["session_id"]})
        self._log(conn, "strip_cards", "recipe_chat_session (쿠팡 상품 카드)", n, cut)

    # ── ⑤ 가명 흐름 최종 삭제 (2026-11-22) ──
    def delete_pseudo(self, conn, have: set[str]) -> None:
        raw = os.environ.get("PRIVACY_PSEUDO_KEEP_DAYS", "").strip()
        try:
            keep = int(raw) if raw else PSEUDO_KEEP_DAYS_DEFAULT
        except ValueError:
            keep = PSEUDO_KEEP_DAYS_DEFAULT
        if keep <= LOG_DAYS:                     # 가명 처리보다 먼저 지우지 않는다 (집계는 매일 먼저 접혀 있음)
            keep = LOG_DAYS + 1
        cut = self.now - timedelta(days=keep)
        for table, col in _PSEUDO:
            if table not in have:
                continue
            sql = f"FROM {table} WHERE {col} < :c"  # noqa: S608 — 고정 이름
            if self.dry_run:
                n = conn.execute(text("SELECT COUNT(*) " + sql).bindparams(_ts("c")), {"c": cut}).scalar() or 0
            else:
                n = conn.execute(text("DELETE " + sql).bindparams(_ts("c")), {"c": cut}).rowcount or 0
            self._log(conn, "delete_pseudo", table, n, cut)

    # ── ④ 실수 신호 파일 ──
    def signals(self) -> None:
        if not self.signal_dir.is_dir():
            return
        cut = self.now.date() - timedelta(days=SIGNAL_DAYS)
        summary = self.signal_dir / "summary.csv"
        old = sorted(p for p in self.signal_dir.glob("*.jsonl") if _file_day(p) and _file_day(p) < cut)
        rows = []
        for p in old:
            kinds: Counter = Counter()
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    kinds[str(json.loads(line).get("kind") or "?")] += 1
                except ValueError:
                    kinds["(읽기 실패)"] += 1
            rows += [(p.stem, k, n) for k, n in sorted(kinds.items())]
        if old and not self.dry_run:
            new = not summary.exists()
            with summary.open("a", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(["day", "kind", "n"])
                w.writerows(rows)
            for p in old:
                p.unlink()
        self.report.append({"step": "signals", "target": str(self.signal_dir.name), "rows": len(old),
                            "cutoff": cut.isoformat()})


def _day(v) -> str:
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return str(v)[:10]


def _file_day(p: Path) -> date | None:
    try:
        return date.fromisoformat(p.stem[:10])
    except ValueError:
        return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
