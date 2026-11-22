"""로컬 모델(Ollama) 학습용 데이터셋 — 운영하면서 쌓고, 사람이 확인하고, 내보내고, 견준다 (2026-11-21 사용자 요청).

왜 이 범위인가
* 대상은 **짧은 정리 작업만**(상품어·검색어·문장 뜻·보유량·재료량·인분·요리 이름 확인 — llm_client.CUSTOMER_FAST_TASKS).
  Mac mini 를 사면 로컬로 옮길 후보가 이 일들이고, 결과가 JSON 이라 맞고 틀림을 셀 수 있다.
  식품 지식·레시피 같은 '글 생성'은 넣지 않는다 — 외부 AI 의 글을 베껴 학습하는 것은 약관상 위험이 크고(경쟁 모델 학습 금지 조항),
  품질도 저장본 + 교차 검토 구조가 맡는다.
* 라벨 출처를 줄마다 남긴다(teacher = 'openai:gpt-5.4-mini' 등). 약관이 바뀌거나 특정 출처를 빼야 하면 내보낼 때 거른다.
  가장 안전한 라벨은 **사람이 확인한 gold** — 내보내기 기본은 gold 우선.

개인정보 (claude/privacy_policy_draft_2026-11-21.md 결정과 같게)
* 문장은 저장 전에 다시 가린다(pii.mask) — 가릴 것이 나오면 **아예 담지 않는다**. 300자 넘는 문장도 담지 않는다.
  2026-11-22 (검토 의견 3): 이미 가려진 문장만 다시 보면 원래 개인정보가 있었는지 놓친다 → 대화 입구에서 가린 일이
  있으면(PII_SEEN) 그 차례의 작업은 담지 않는다. 가리기는 일부 형식(전화·이메일 등)만 잡으므로 학습 칸도 익명 자료로
  보지 않는다 — 보관 기간·삭제 요청 대상.
* 세션 값은 '임시 칸'(staging)에만, 클릭 신호를 붙이는 데 쓰고 **90일 뒤 지운다**(대화 문장과 같은 기간).
  학습 칸(examples)에는 세션 값·시각 없이 문장·정답·출처·날짜(일)·횟수만 — 가명정보로 기술 개발에 쓰는 형태.
* 학습 칸 보관: 마지막으로 본 날부터 DATASET_KEEP_DAYS(기본 730일) — 사용자 결정 전 기본값, 처리방침에 적을 값.
* **기본 꺼짐** (2026-11-22 검토 의견: 목적·보유 기간·출력 이용 조건을 정한 뒤 DATASET_CAPTURE=1 로 켠다).
  저장소: DATASET_DB (기본 var/dataset/dataset.sqlite3, git 에 넣지 않음). 내보낸 파일은 var/dataset/export 에
  DATASET_EXPORT_KEEP_DAYS(기본 30일)만 두고 매일 지운다 — 학습 산출물(어댑터·GGUF)은 manifest 를 보고 함께 관리.

흐름: ① 고객 대화에서 짧은 작업 결과를 임시 칸에 담기(capture) → ② 매일 새벽 승격(promote): 그 차례에 보여 준 상품으로
30분 안에 판매처로 이동했으면 'silver', 아니면 'candidate', 같은 문장·정답은 횟수만 늘림 → ③ 관리자 'AI' 화면에서
확인(gold/고침/버림) → ④ 내보내기(export) → ⑤ 로컬 모델 견주기(scripts/eval_local_model.py).
  (클릭은 세션 전체가 아니라 **그 차례에 보여 준 상품**으로 간 것만 센다 — 운영자 시험 클릭 chat_internal 은 빼고.)
* silver 는 **'행동 신호가 있는 미검수 후보'** 일 뿐 정답 증거가 아니다 (클릭이 해석이 맞았다는 뜻은 아님).
  내보내기 기본은 gold 만, 시험 칸은 언제나 gold 만.
* 학습·시험 나눔은 문장 그대로가 아니라 **비슷한 문장 묶음**(띄어쓰기·숫자·문장부호를 뺀 모양) 단위 — 변형 문장이
  학습·시험 양쪽에 새지 않게.
* 사람이 고쳐도 원래 출처(teacher)는 덮어쓰지 않는다 — edited·reviewed_by 를 따로 남긴다 (검토가 이용 권한을 바꾸지 않음).
"""
from __future__ import annotations

import contextvars
import hashlib
import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

LABELS = ("candidate", "silver", "gold", "dropped")
MAX_INPUT = 300
STAGING_DAYS = 90
KEEP_DAYS_DEFAULT = 730
CLICK_WINDOW_MIN = 30

EXPORT_KEEP_DAYS_DEFAULT = 30

# 지금 처리 중인 대화의 세션 값 (ChatService 가 정한다) — 클릭 신호를 붙일 때만 쓴다
CURRENT_SESSION: contextvars.ContextVar[str | None] = contextvars.ContextVar("dataset_session", default=None)
# 지금 차례 id — 그 차례에서 찾은 검색어를 임시 칸에 붙여, 클릭을 세션 전체가 아니라 이 요청의 결과에만 잇는다
CURRENT_TURN: contextvars.ContextVar[str | None] = contextvars.ContextVar("dataset_turn", default=None)
# 이 차례 입력에서 개인정보 모양을 가린 일이 있었나 (대화 입구 pii.mask 결과)
PII_SEEN: contextvars.ContextVar[bool] = contextvars.ContextVar("dataset_pii_seen", default=False)

SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (hash TEXT PRIMARY KEY, text TEXT NOT NULL, first_day TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS staging (
  id INTEGER PRIMARY KEY, session_id TEXT, task TEXT NOT NULL, input TEXT NOT NULL, output TEXT NOT NULL,
  teacher TEXT NOT NULL, prompt_hash TEXT NOT NULL, created_at TEXT NOT NULL, promoted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS examples (
  id INTEGER PRIMARY KEY, task TEXT NOT NULL, input TEXT NOT NULL, output TEXT NOT NULL, teacher TEXT NOT NULL,
  prompt_hash TEXT NOT NULL, label TEXT NOT NULL, seen INTEGER NOT NULL, clicked INTEGER NOT NULL,
  first_day TEXT NOT NULL, last_day TEXT NOT NULL, reviewed_by TEXT, reviewed_at TEXT, note TEXT,
  UNIQUE (task, input, output)
);
"""
# 2026-11-22: 나중에 더한 칸 (이미 만든 파일에도 붙인다)
_ADDED = (("staging", "turn_id", "TEXT"), ("staging", "query", "TEXT"), ("staging", "shown", "TEXT"),
          ("examples", "edited", "INTEGER NOT NULL DEFAULT 0"))


class DatasetError(ValueError):
    pass


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def enabled() -> bool:
    """기본 꺼짐 (2026-11-22) — DATASET_CAPTURE=1 일 때만 담는다."""
    return _env("DATASET_CAPTURE", "0") in ("1", "on", "true")


def tasks() -> frozenset[str]:
    from app.services.nlu.llm_client import CUSTOMER_FAST_TASKS

    return CUSTOMER_FAST_TASKS


def default_path() -> Path:
    raw = _env("DATASET_DB")
    return Path(raw) if raw else Path(__file__).resolve().parents[3] / "var" / "dataset" / "dataset.sqlite3"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def group_of(text: str) -> str:
    """비슷한 문장 묶음 열쇠 — 띄어쓰기·숫자·문장부호·영문 대소문자를 뺀 모양 ('사과 3kg 주세요' ~ '사과5kg 주세요!')."""
    return re.sub(r"[\s\d\W_]+", "", (text or "").lower())


def split_of(task: str, text: str) -> str:
    """학습·시험 나눔 — 비슷한 문장 묶음 해시로 고정(10% 시험). 같은 묶음은 늘 같은 쪽."""
    h = int(hashlib.sha256(f"{task}|{group_of(text) or normalize(text)}".encode()).hexdigest()[:8], 16)
    return "test" if h % 10 == 0 else "train"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


class DatasetStore:
    def __init__(self, path: Path | str | None = None, clock=None):
        self.path = Path(path) if path else default_path()
        self.clock = clock or _now
        self._lock = threading.Lock()

    def _db(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.executescript(SCHEMA)
        for table, col, kind in _ADDED:
            if col not in {r[1] for r in con.execute(f"PRAGMA table_info({table})")}:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {kind}")
        return con

    # ① 담기 ──────────────────────────────────────────
    def capture(self, task: str | None, user_text: str, output: dict, teacher: str, system: str,
                session_id: str | None = None, turn_id: str | None = None) -> bool:
        if not task or task not in tasks() or not isinstance(output, dict):
            return False
        from app.services.privacy import pii

        text = normalize(user_text)
        if not text or len(text) > MAX_INPUT:
            return False
        masked, kinds = pii.mask(text)
        if kinds or "***" in masked:                 # 개인정보 모양이 있었던 문장은 담지 않는다
            return False
        phash = hashlib.sha256((system or "").encode()).hexdigest()[:16]
        now = self.clock()
        with self._lock, self._db() as con:
            con.execute("INSERT OR IGNORE INTO prompts (hash, text, first_day) VALUES (?,?,?)",
                        (phash, system or "", _iso(now)[:10]))
            con.execute("INSERT INTO staging (session_id, task, input, output, teacher, prompt_hash, created_at, turn_id)"
                        " VALUES (?,?,?,?,?,?,?,?)",
                        (session_id, task, masked, json.dumps(output, ensure_ascii=False, sort_keys=True), teacher,
                         phash, _iso(now), turn_id))
        return True

    def note_query(self, turn_id: str | None, query: str | None, shown: list[str] | None = None) -> int:
        """그 차례에서 찾은 검색어와 보여 준 상품 이름을 임시 칸에 붙인다 — 클릭은 이 상품들에서 난 것만 센다."""
        names = [str(t)[:200] for t in (shown or []) if t][:30]
        if not turn_id or not query or not names:
            return 0
        with self._lock, self._db() as con:
            return con.execute("UPDATE staging SET query=?, shown=? WHERE turn_id=? AND promoted=0",
                               (query[:100], json.dumps(names, ensure_ascii=False), turn_id)).rowcount

    # ② 승격 ──────────────────────────────────────────
    def promote(self, clicks=None, *, older_than_min: int = 60) -> dict:
        """clicks(session_id, start, end, shown_titles) -> bool : 그 차례에 보여 준 상품 중 하나로 그 사이에 판매처로
        이동했는지. DB 가 없으면 None → 신호 없음. 그 차례에 상품을 보여 주지 않았으면 클릭을 붙이지 않는다."""
        now = self.clock()
        cut = _iso(now - timedelta(minutes=older_than_min))
        done = {"promoted": 0, "silver": 0}
        with self._lock, self._db() as con:
            rows = con.execute("SELECT * FROM staging WHERE promoted=0 AND created_at < ? ORDER BY id", (cut,)).fetchall()
            for r in rows:
                at = datetime.fromisoformat(r["created_at"])
                clicked = False
                if clicks is not None and r["session_id"] and r["shown"]:
                    try:
                        clicked = bool(clicks(r["session_id"], at, at + timedelta(minutes=CLICK_WINDOW_MIN),
                                              json.loads(r["shown"])))
                    except Exception:  # noqa: BLE001 — 신호를 못 붙여도 승격은 한다
                        clicked = False
                day = r["created_at"][:10]
                con.execute(
                    "INSERT INTO examples (task, input, output, teacher, prompt_hash, label, seen, clicked, first_day,"
                    " last_day) VALUES (?,?,?,?,?,?,1,?,?,?) ON CONFLICT (task, input, output) DO UPDATE SET"
                    " seen = seen + 1, clicked = clicked + excluded.clicked, last_day = excluded.last_day,"
                    " label = CASE WHEN label IN ('gold','dropped') THEN label"
                    "              WHEN excluded.clicked > 0 OR clicked > 0 THEN 'silver' ELSE label END",
                    (r["task"], r["input"], r["output"], r["teacher"], r["prompt_hash"],
                     "silver" if clicked else "candidate", int(clicked), day, day))
                con.execute("UPDATE staging SET promoted=1 WHERE id=?", (r["id"],))
                done["promoted"] += 1
                done["silver"] += int(clicked)
        return done

    # 지우기 ──────────────────────────────────────────
    def purge(self) -> dict:
        now = self.clock()
        keep = int(_env("DATASET_KEEP_DAYS", str(KEEP_DAYS_DEFAULT)) or KEEP_DAYS_DEFAULT)
        with self._lock, self._db() as con:
            a = con.execute("DELETE FROM staging WHERE created_at < ?",
                            (_iso(now - timedelta(days=STAGING_DAYS)),)).rowcount
            b = con.execute("DELETE FROM examples WHERE last_day < ?",
                            (_iso(now - timedelta(days=keep))[:10],)).rowcount
        return {"staging_deleted": a, "examples_deleted": b, "keep_days": keep}

    # ③ 확인 ──────────────────────────────────────────
    def queue(self, task: str | None = None, limit: int = 50) -> list[dict]:
        sql = "SELECT * FROM examples WHERE label IN ('candidate','silver')"
        args: list = []
        if task:
            sql += " AND task=?"
            args.append(task)
        sql += " ORDER BY seen DESC, clicked DESC, id LIMIT ?"
        args.append(limit)
        with self._db() as con:
            return [dict(r, output=json.loads(r["output"])) for r in con.execute(sql, args).fetchall()]

    def review(self, eid: int, verdict: str, *, output: dict | None = None, reviewer: str = "operator",
               note: str | None = None) -> dict:
        if verdict not in ("ok", "fix", "drop"):
            raise DatasetError("확인 값은 ok·fix·drop 중 하나예요.")
        now = _iso(self.clock())
        with self._lock, self._db() as con:
            row = con.execute("SELECT * FROM examples WHERE id=?", (eid,)).fetchone()
            if row is None:
                raise DatasetError("없는 예시예요.")
            if verdict == "fix":
                if not isinstance(output, dict) or not output:
                    raise DatasetError("고친 정답(JSON 객체)을 넣어 주세요.")
                fixed = json.dumps(output, ensure_ascii=False, sort_keys=True)
                con.execute("UPDATE examples SET label='dropped', reviewed_by=?, reviewed_at=?, note=? WHERE id=?",
                            (reviewer, now, "고친 정답으로 바꿈", eid))
                # 2026-11-22 (검토 의견 5): 출처는 원래 AI 그대로 두고 '사람이 고침(edited=1)'을 따로 남긴다
                con.execute(
                    "INSERT INTO examples (task, input, output, teacher, prompt_hash, label, seen, clicked, first_day,"
                    " last_day, reviewed_by, reviewed_at, note, edited) VALUES (?,?,?,?,?,'gold',?,?,?,?,?,?,?,1)"
                    " ON CONFLICT (task, input, output) DO UPDATE SET label='gold', reviewed_by=excluded.reviewed_by,"
                    " reviewed_at=excluded.reviewed_at, edited=1",
                    (row["task"], row["input"], fixed, row["teacher"], row["prompt_hash"], row["seen"],
                     row["clicked"], row["first_day"], row["last_day"], reviewer, now, (note or "")[:200] or None))
            else:
                con.execute("UPDATE examples SET label=?, reviewed_by=?, reviewed_at=?, note=? WHERE id=?",
                            ("gold" if verdict == "ok" else "dropped", reviewer, now, (note or "")[:200] or None, eid))
        return {"ok": True}

    def stats(self) -> dict:
        with self._db() as con:
            by = [dict(r) for r in con.execute("SELECT task, label, COUNT(*) n, SUM(seen) seen FROM examples"
                                               " GROUP BY task, label ORDER BY task, label").fetchall()]
            staged = con.execute("SELECT COUNT(*) FROM staging WHERE promoted=0").fetchone()[0]
            teachers = [dict(r) for r in con.execute("SELECT teacher, COUNT(*) n FROM examples GROUP BY teacher"
                                                     " ORDER BY n DESC").fetchall()]
        return {"by_task": by, "waiting": staged, "teachers": teachers, "enabled": enabled(),
                "keep_days": int(_env("DATASET_KEEP_DAYS", str(KEEP_DAYS_DEFAULT)) or KEEP_DAYS_DEFAULT)}

    # ④ 내보내기 ───────────────────────────────────────
    def export(self, task: str, labels=("gold",), exclude_teachers: tuple[str, ...] = (),
               min_seen: int = 1) -> dict[str, list[dict]]:
        """{'train': [...], 'test': [...]} — 한 줄 = {'messages': [system, user, assistant], 'label', 'teacher',
        'edited', 'reviewed_by'}. 같은 문장에 정답이 여럿이면 gold > silver > 많이 본 것 하나만.
        기본은 gold 만. 시험 칸에는 언제나 사람이 확인한 gold 만 (silver 가 시험 묶음에 걸리면 학습에도 넣지 않는다)."""
        rank = {"gold": 0, "silver": 1, "candidate": 2}
        with self._db() as con:
            rows = con.execute(
                f"SELECT e.*, p.text AS system FROM examples e JOIN prompts p ON p.hash = e.prompt_hash"  # noqa: S608
                f" WHERE e.task=? AND e.label IN ({','.join('?' * len(labels))})", (task, *labels)).fetchall()
        best: dict[str, sqlite3.Row] = {}
        for r in rows:
            if any(r["teacher"].startswith(t) for t in exclude_teachers):
                continue
            if r["label"] != "gold" and r["seen"] < min_seen:
                continue
            cur = best.get(r["input"])
            key = (rank.get(r["label"], 9), -r["seen"])
            if cur is None or key < (rank.get(cur["label"], 9), -cur["seen"]):
                best[r["input"]] = r
        out: dict[str, list[dict]] = {"train": [], "test": []}
        for text, r in sorted(best.items()):
            side = split_of(task, text)
            if side == "test" and r["label"] != "gold":
                continue
            out[side].append({
                "messages": [{"role": "system", "content": r["system"]}, {"role": "user", "content": text},
                             {"role": "assistant", "content": r["output"]}],
                "label": r["label"], "teacher": r["teacher"], "edited": bool(r["edited"]),
                "reviewed_by": r["reviewed_by"]})
        return out


_STORE: DatasetStore | None = None


def store() -> DatasetStore:
    global _STORE
    if _STORE is None or _STORE.path != default_path():
        _STORE = DatasetStore()
    return _STORE


def capture(task: str | None, user_text: str, output: dict, teacher: str, system: str) -> None:
    """LLMClient 가 부른다 — 실패해도 대화에 영향 없음. 이 차례 입력에서 개인정보를 가렸으면 담지 않는다."""
    if not enabled() or PII_SEEN.get():
        return
    try:
        store().capture(task, user_text, output, teacher, system, session_id=CURRENT_SESSION.get(),
                        turn_id=CURRENT_TURN.get())
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning("dataset capture failed", exc_info=True)


def note_query(query: str | None, shown: list[str] | None) -> None:
    """ChatService 가 상품을 보여 준 뒤 부른다 — 이 차례 임시 칸에 검색어·보여 준 상품 이름을 붙인다."""
    if not enabled():
        return
    try:
        store().note_query(CURRENT_TURN.get(), query, shown)
    except Exception:  # noqa: BLE001
        import logging

        logging.getLogger(__name__).warning("dataset note_query failed", exc_info=True)


def purge_exports(export_dir: Path | None = None, now: datetime | None = None) -> int:
    """내보낸 JSONL 은 DATASET_EXPORT_KEEP_DAYS(기본 30일)만 둔다 — 학습 칸에서 지운 문장이 파일로 남지 않게."""
    d = export_dir or default_path().parent / "export"
    if not d.is_dir():
        return 0
    keep = int(_env("DATASET_EXPORT_KEEP_DAYS", str(EXPORT_KEEP_DAYS_DEFAULT)) or EXPORT_KEEP_DAYS_DEFAULT)
    cut = (now or _now()).timestamp() - keep * 86400
    n = 0
    for p in d.glob("*.jsonl"):
        if p.stat().st_mtime < cut:
            p.unlink()
            n += 1
    return n
