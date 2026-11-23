"""관리자 '개선 목록' (2026-11-23, 창 3-D ④ — 설계 claude/improve_without_training_proposal_2026-11-22.md §3·§8·§9).

네 칸:
  1. 주간 지표   scripts/weekly_improve.py 결과(var/improve/YYYY-Www.json) — 기간 탭 1주·2주·4주·누적
  2. 점검 후보   var/signals 의 실수 신호(0건·약한 일치·다시 묻기·뜻 읽기 버림·검토 의견 남음·불러오기 실패)를
                 같은 종류·같은 말끼리 묶어 보여 줌. **관리자가 확인하기 전에는 '점검 후보'** — 오류 확정이 아님 (§3)
  3. 확인 결과   오류 확인 / 오류 아님 / 판단 보류 + 관리자 메모
  4. 고침 기록   PR · 연결한 점검 후보 · 영향 질의(유형으로) · 확인 예정일 · 결과

개인정보: 손님 문장은 신호 파일(90일 보존)에서 화면에 그때그때 읽어 보여 줄 뿐 다른 파일로 옮기지 않는다.
확인 결과·고침 기록(var/improve/reviews.json · fixes.json)에는 후보 번호(소금 친 해시 — 문장을 되살릴 수 없음)·
종류·날짜·건수·관리자가 적은 메모만 남는다. 운영자 시험(served internal) 세션은 뺀다. 자동 수정은 하지 않는다.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
_LOCK = threading.RLock()       # 저장 중에 소금 파일을 읽는 경로가 있어 다시 들어갈 수 있게

# 영향 순 (§3 — 0건·조건 약화·안전 관련이 먼저). 숫자가 작을수록 위
KINDS = {
    "zero": ("0건", 1, "찾았는데 보여 줄 상품·글이 없음"),
    "weak_match": ("약한 일치", 2, "보여 준 상품명이 검색 낱말과 거의 안 겹침"),
    "requery": ("고객 다시 묻기", 3, "상품을 보여 준 뒤 3분 안에 비슷한 말로 다시 찾거나 '다른 거'"),
    "intent_rejected": ("뜻 읽기 버림", 4, "문장 뜻 읽기 답이 검사에서 버려져 규칙으로 넘어감"),
    "review_left": ("검토 의견 남음", 5, "레시피 카드에 검토 AI 의견이 남음"),
    "source_failed": ("불러오기 실패", 6, "쿠팡을 불러오지 못함 — 대개 장애, 반복될 때만 점검"),
}
VERDICTS = {"confirmed": "오류 확인", "not_error": "오류 아님", "hold": "판단 보류"}
RESULTS = {"pending": "확인 전", "better": "나아짐", "same": "변화 없음", "worse": "나빠짐", "reverted": "되돌림"}

# 첫 순환(11-23) 사례 — 손님 문장 없이 유형만
SEED_FIXES = [
    {"id": 1, "title": "요청 말이 상품어에 붙은 검색이 0건", "pr": "#69", "candidate_ids": [],
     "affected": "끝에 '추천' 등 요청 말이 붙어 쓰인 식품 검색어 (전후 비교: 식품 검색어 1,671 중 5개만 바뀜)",
     "check_on": "2026-11-30", "result": "pending", "at": "2026-11-23T11:50"},
    {"id": 2, "title": "대화 머리줄 단계 표시가 로고를 덮음", "pr": "#70", "candidate_ids": [],
     "affected": "화면 표시만 — 검색 결과 영향 없음", "check_on": "2026-11-30", "result": "pending", "at": "2026-11-23T12:30"},
]


def signal_dir() -> Path:
    return Path(os.getenv("MISS_SIGNALS_DIR", "var/signals"))


def improve_dir() -> Path:
    return Path(os.getenv("IMPROVE_DIR", "var/improve"))


def _read_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _salt() -> str:
    p = improve_dir() / ".salt"
    with _LOCK:
        if not p.is_file():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(secrets.token_hex(16), encoding="utf-8")
        return p.read_text(encoding="utf-8").strip()


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def candidate_id(kind: str, text: str, salt: str | None = None) -> str:
    """같은 종류·같은 말 → 같은 번호. 소금을 쳐서 번호로 문장을 짐작할 수 없게."""
    return hashlib.sha256(f"{salt or _salt()}|{kind}|{_norm(text)}".encode()).hexdigest()[:12]


# ── 1. 주간 지표 ───────────────────────────────────────────
def weekly(week: str | None = None) -> dict:
    d = improve_dir()
    weeks = sorted((p.stem for p in d.glob("????-W??.json")), reverse=True) if d.is_dir() else []
    pick = week if week in weeks else (weeks[0] if weeks else None)
    return {"weeks": weeks, "week": pick, "report": _read_json(d / f"{pick}.json", None) if pick else None}


def run_weekly(end: date | None = None) -> dict:
    """scripts/weekly_improve.py 를 이 서버 안에서 한 번 (오늘까지). 하루 숫자 파일을 덮어쓰고 주간 파일을 새로 씀."""
    import contextlib
    import importlib.util
    import io

    path = Path(__file__).resolve().parents[3] / "scripts" / "weekly_improve.py"
    spec = importlib.util.spec_from_file_location("_weekly_improve", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with contextlib.redirect_stdout(io.StringIO()):
        mod.main(["--end", (end or datetime.now(KST).date()).isoformat()])
    return weekly()


# ── 2. 점검 후보 ───────────────────────────────────────────
def _rows(day: date) -> list[dict]:
    p = signal_dir() / f"{day.isoformat()}.jsonl"
    out = []
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    except OSError:
        pass
    return out


def candidates(days: int = 7, *, today: date | None = None) -> dict:
    """최근 N일 실수 신호 → 종류·말별 묶음. 확인 결과가 있으면 붙인다."""
    today = today or datetime.now(KST).date()
    salt = _salt()
    reviews = load_reviews()
    groups: dict[str, dict] = {}
    for i in range(days):
        day = today - timedelta(days=i)
        rows = _rows(day)
        internal = {r.get("sid") for r in rows if r.get("kind") == "served" and r.get("internal")}
        for r in rows:
            kind = r.get("kind")
            if kind not in KINDS or r.get("sid") in internal:
                continue
            text = r.get("text") or ""
            cid = candidate_id(kind, text, salt)
            g = groups.setdefault(cid, {"id": cid, "kind": kind, "label": KINDS[kind][0], "text": text[:200],
                                        "count": 0, "sessions": set(), "first": r.get("at"), "last": r.get("at"),
                                        "examples": []})
            g["count"] += 1
            g["sessions"].add(r.get("sid"))
            at = r.get("at") or ""
            g["first"], g["last"] = min(g["first"] or at, at), max(g["last"] or at, at)
            ex = {k: r[k] for k in ("stage", "what", "items", "before", "field", "value", "shown") if r.get(k)}
            if ex and len(g["examples"]) < 3:
                g["examples"].append(ex)
    out = []
    for g in groups.values():
        g["sessions"] = len(g["sessions"])
        rv = reviews.get(g["id"])
        g["review"] = rv
        g["status"] = VERDICTS[rv["verdict"]] if rv else "점검 후보"
        out.append(g)
    # 확인 안 한 것 먼저 → 영향 순 → 세션 수
    out.sort(key=lambda g: (g["review"] is not None, KINDS[g["kind"]][1], -g["sessions"], -g["count"], g["last"] or ""))
    by_kind = defaultdict(int)
    for g in out:
        by_kind[g["kind"]] += 1
    return {"days": days, "end": today.isoformat(), "candidates": out,
            "kinds": [{"kind": k, "label": v[0], "order": v[1], "about": v[2], "n": by_kind.get(k, 0)} for k, v in KINDS.items()],
            "unreviewed": sum(g["review"] is None for g in out)}


# ── 3. 확인 결과 ───────────────────────────────────────────
def load_reviews() -> dict:
    return _read_json(improve_dir() / "reviews.json", {})


def review(cid: str, verdict: str, note: str | None = None, *, days: int = 28, today: date | None = None) -> dict:
    if verdict not in VERDICTS:
        raise ValueError("verdict")
    if not re.fullmatch(r"[0-9a-f]{12}", cid):
        raise ValueError("id")
    found = next((g for g in candidates(days, today=today)["candidates"] if g["id"] == cid), None)
    with _LOCK:
        data = load_reviews()
        old = data.get(cid) or {}
        if not found and not old:
            raise KeyError(cid)
        data[cid] = {"verdict": verdict, "note": (note or "").strip()[:300],
                     "kind": (found or old).get("kind"),
                     "first": ((found or {}).get("first") or old.get("first") or "")[:10],
                     "last": ((found or {}).get("last") or old.get("last") or "")[:10],
                     "count": (found or {}).get("count", old.get("count", 0)),
                     "at": datetime.now(KST).isoformat(timespec="minutes")}
        _write_json(improve_dir() / "reviews.json", data)
    return data[cid]


def reviewed_list() -> list[dict]:
    """확인 결과 칸 — 문장 없이 (신호 파일이 지워져도 남음)."""
    out = [{"id": k, **v, "verdict_label": VERDICTS.get(v.get("verdict"), "?"),
            "kind_label": KINDS.get(v.get("kind"), ("?",))[0]} for k, v in load_reviews().items()]
    return sorted(out, key=lambda x: x.get("at") or "", reverse=True)


# ── 4. 고침 기록 ───────────────────────────────────────────
def load_fixes() -> list[dict]:
    p = improve_dir() / "fixes.json"
    return _read_json(p, None) if p.is_file() else [dict(x) for x in SEED_FIXES]


def save_fix(body: dict, fid: int | None = None) -> dict:
    clean = {"title": str(body.get("title") or "").strip()[:120],
             "pr": str(body.get("pr") or "").strip()[:40],
             "candidate_ids": [c for c in (body.get("candidate_ids") or []) if re.fullmatch(r"[0-9a-f]{12}", str(c))][:20],
             "affected": str(body.get("affected") or "").strip()[:300],
             "check_on": str(body.get("check_on") or "").strip()[:10],
             "result": body.get("result") if body.get("result") in RESULTS else "pending",
             "result_note": str(body.get("result_note") or "").strip()[:300]}
    if not clean["title"]:
        raise ValueError("title")
    if clean["check_on"]:
        date.fromisoformat(clean["check_on"])
    with _LOCK:
        fixes = load_fixes()
        if fid is None:
            item = {"id": max([f["id"] for f in fixes] or [0]) + 1, **clean,
                    "at": datetime.now(KST).isoformat(timespec="minutes")}
            fixes.append(item)
        else:
            item = next((f for f in fixes if f["id"] == fid), None)
            if item is None:
                raise KeyError(fid)
            item.update(clean, updated=datetime.now(KST).isoformat(timespec="minutes"))
        _write_json(improve_dir() / "fixes.json", fixes)
    return item


def fixes_view(today: date | None = None) -> list[dict]:
    today = (today or datetime.now(KST).date()).isoformat()
    return [dict(f, result_label=RESULTS.get(f.get("result"), "?"),
                 due=bool(f.get("check_on")) and f.get("result") == "pending" and f["check_on"] <= today)
            for f in sorted(load_fixes(), key=lambda f: f["id"], reverse=True)]


# ── 5. 합성 재현 사례 초안 (2026-11-23, 3-D ⑥ — 설계 §4·§5) ─────────────────────
# '오류 확인'한 후보 → 역할 넷(고친 사례·정상 사례·반례·여러 턴) 빈 자리를 만들고, 사람이 합성 문장·기대 검색어를 적는다.
# 손님 문장과 같은 문장은 받지 않는다(소금 친 후보 번호로 견줌 — 원문을 저장하지 않고도 확인), 개인정보 모양도 받지 않는다.
# '준비됨' 초안은 tests/services/chat/synthetic_cases.jsonl 형식으로 내보낸다 → Claude PR 로 시험에 등록 (사람 병합).
CASE_ROLES = {"fixed": "고친 사례", "normal": "정상 사례", "counter": "반례", "multiturn": "여러 턴"}
CASE_STATUS = {"draft": "초안", "ready": "준비됨", "dropped": "버림"}


def load_cases() -> list[dict]:
    return _read_json(improve_dir() / "case_drafts.json", [])


def preview(turns: list[str]) -> list[str]:
    """지금 코드가 각 문장을 무슨 검색어로 찾는지 (외부 호출 없음 — 규칙만)."""
    from app.services.chat.service import shopping_terms

    return [shopping_terms(t)[0] for t in turns]


def _check_turns(turns: list[str], review_id: str | None, kind: str | None) -> None:
    from app.services.privacy import pii

    salt = _salt()
    for t in turns:
        if pii.mask(t)[1] or re.search(r"\d{6,}", t):
            raise ValueError("개인정보처럼 보이는 내용이 있어요 — 합성 문장에는 넣지 않아요")
        if review_id and kind and candidate_id(kind, t, salt) == review_id:
            raise ValueError("손님 문장과 같아요 — 유형·조건만 남기고 다시 써 주세요")


def start_cases(review_id: str) -> list[dict]:
    """'오류 확인' 후보 하나 → 역할 넷 빈 자리 (이미 있으면 그대로)."""
    rv = load_reviews().get(review_id)
    if not rv or rv.get("verdict") != "confirmed":
        raise KeyError(review_id)
    with _LOCK:
        cases = load_cases()
        if not any(c["review_id"] == review_id for c in cases):
            n = max([c["n"] for c in cases] or [0])
            group = f"{rv.get('kind')}-{(rv.get('first') or '').replace('-', '')[2:]}-{review_id[:4]}"
            for i, role in enumerate(CASE_ROLES, 1):
                cases.append({"n": n + i, "review_id": review_id, "group": group, "role": role, "turns": [],
                              "expect": {}, "fix": "", "status": "draft",
                              "signal": {"kind": rv.get("kind"), "date": rv.get("first")},
                              "at": datetime.now(KST).isoformat(timespec="minutes")})
            _write_json(improve_dir() / "case_drafts.json", cases)
    return [c for c in load_cases() if c["review_id"] == review_id]


def save_case(n: int, body: dict) -> dict:
    turns = [str(t).strip()[:80] for t in (body.get("turns") or []) if str(t).strip()][:6]
    expect = {}
    if body.get("search"):
        expect["search"] = str(body["search"]).strip()[:60]
    for k in ("search_has", "search_not"):
        words = [str(w).strip()[:30] for w in (body.get(k) or []) if str(w).strip()][:6]
        if words:
            expect[k] = words
    if body.get("searches"):
        expect = {"searches": [str(w).strip()[:60] for w in body["searches"]][:6]}
    status = body.get("status") if body.get("status") in CASE_STATUS else "draft"
    with _LOCK:
        cases = load_cases()
        c = next((x for x in cases if x["n"] == n), None)
        if c is None:
            raise KeyError(n)
        _check_turns(turns, c["review_id"], (c.get("signal") or {}).get("kind"))
        if status == "ready" and (not turns or not expect):
            raise ValueError("문장과 기대 검색어를 적어야 '준비됨'으로 바꿀 수 있어요")
        if status == "ready" and c["role"] == "multiturn" and len(turns) < 2:
            raise ValueError("여러 턴은 문장이 둘 이상이에요")
        c.update(turns=turns, expect=expect, fix=str(body.get("fix") or "").strip()[:20], status=status,
                 updated=datetime.now(KST).isoformat(timespec="minutes"))
        _write_json(improve_dir() / "case_drafts.json", cases)
    return c


def cases_view() -> list[dict]:
    return [dict(c, role_label=CASE_ROLES.get(c["role"], c["role"]), status_label=CASE_STATUS.get(c["status"], "?"),
                 now=preview(c["turns"]) if c["turns"] else [])
            for c in sorted(load_cases(), key=lambda c: c["n"])]


def export_cases() -> str:
    """'준비됨' 초안 → synthetic_cases.jsonl 줄들. var/improve/synthetic_cases_ready.jsonl 에도 남김 (Claude 가 맥에서 읽어 PR)."""
    lines = []
    for c in sorted(load_cases(), key=lambda c: c["n"]):
        if c["status"] != "ready":
            continue
        lines.append(json.dumps({"id": f"{c['group']}-{c['n']:02d}", "group": c["group"], "origin": "synthetic",
                                 "signal": {k: v for k, v in (c.get("signal") or {}).items() if k in ("kind", "date") and v},
                                 "fix": c.get("fix") or "", "role": c["role"], "turns": c["turns"], "expect": c["expect"]},
                                ensure_ascii=False))
    text = "\n".join(lines) + ("\n" if lines else "")
    p = improve_dir() / "synthetic_cases_ready.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return text
