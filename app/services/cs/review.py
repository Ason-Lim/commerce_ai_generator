"""분야 판단 주간 검수 (2026-11-23 창 4 ④) — 설계 claude/stage4_design_2026-11-23.md §2 '기록'·§6.

* 손님이 직접 쓴 문장(칩·구조화 답 제외, 운영자 시험 제외)의 분야 판단을 **샘플로** 남긴다:
  식품 아닌 분야는 모두, 식품은 10개 중 1개(세션·문장으로 정해지는 고정 추출 — 다시 계산해도 같음).
* 문장은 입구에서 개인정보를 가린 뒤 것, 200자. **관리자 화면에서만**, 내보내기 없음, **90일 뒤 지움**(대화 원문 보존과 같음).
* 운영자가 맞음 / 틀림(맞는 분야) / 모름 을 누르면 분야별 오분류율 = 틀림 ÷ (맞음 + 틀림). 30 미만은 '관찰'.
* 판정은 문장 없이 남는다 (샘플이 지워져도 비율은 이어짐).
"""
from __future__ import annotations

import hashlib
import json
import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.cs import tickets

KST = timezone(timedelta(hours=9))
_LOCK = threading.Lock()
KEEP_DAYS = 90
FOOD_EVERY = 10
OBSERVE_BELOW = 30
VERDICTS = {"right": "맞음", "wrong": "틀림", "unsure": "모름"}
LABELS = {"food": "식품", "emergency": "위급", "food_safety": "식품 안전", "health": "건강·알레르기", "privacy": "개인정보",
          "dispute": "분쟁·보상", "affiliate": "제휴·주문", "stock": "품절·재고", "account": "계정", "site_help": "사이트 이용",
          "not_food": "식품 아님", "chitchat": "잡담"}


def _dir() -> Path:
    return tickets.store_dir() / "review"


def _now() -> datetime:
    return datetime.now(KST)


def sample_id(sid: str, text: str, at: str) -> str:
    return hashlib.sha1(f"{sid}|{text}|{at}".encode()).hexdigest()[:12]


def picked(domain: str, sid: str, text: str) -> bool:
    if domain != "food":
        return True
    return int(hashlib.sha1(f"{sid}|{text}".encode()).hexdigest()[:6], 16) % FOOD_EVERY == 0


def record(sid: str, text: str | None, domain: str | None, by: str | None, *, internal: bool = False,
           now: datetime | None = None) -> dict | None:
    """ChatService.handle 이 손님 문장 차례마다 부른다. 샘플이 아니면 아무것도 남기지 않는다."""
    text = " ".join((text or "").split())[:200]
    domain = domain or "food"
    if internal or not text or domain not in LABELS or not picked(domain, sid or "", text):
        return None
    now = now or _now()
    at = now.isoformat(timespec="seconds")
    row = {"id": sample_id(sid or "", text, at), "at": at, "domain": domain, "by": by or "rule", "text": text}
    p = _dir() / f"{now:%Y-%m-%d}.jsonl"
    with _LOCK:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _verdict_path() -> Path:
    return tickets.store_dir() / "review_verdicts.json"


def _verdicts() -> dict:
    try:
        data = json.loads(_verdict_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _rows(days: int, now: datetime) -> list[dict]:
    out = []
    for i in range(days):
        p = _dir() / f"{(now - timedelta(days=i)):%Y-%m-%d}.jsonl"
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def samples(days: int = 7, per_domain: int = 20, now: datetime | None = None) -> dict:
    """분야별로 최근 것부터 per_domain 개 (판정 안 한 것 먼저)."""
    now = now or _now()
    v = _verdicts()
    by_dom: dict[str, list[dict]] = defaultdict(list)
    for r in sorted(_rows(days, now), key=lambda r: r["at"], reverse=True):
        by_dom[r["domain"]].append(dict(r, verdict=v.get(r["id"])))
    out = []
    for dom in sorted(by_dom, key=lambda d: (d == "food", d)):
        rows = sorted(by_dom[dom], key=lambda r: r["verdict"] is not None)[:per_domain]
        out.append({"domain": dom, "label": LABELS.get(dom, dom), "total": len(by_dom[dom]), "items": rows})
    return {"days": days, "groups": out, "summary": summary(), "labels": LABELS, "verdicts": VERDICTS}


def judge(sid: str, verdict: str, should: str | None = None, *, domain: str | None = None, by: str = "operator") -> dict:
    """판정 저장 — 문장은 남기지 않음 (샘플 번호·분야·판정·맞는 분야·시각)."""
    if verdict not in VERDICTS:
        raise ValueError("verdict")
    if verdict == "wrong" and should not in LABELS:
        raise ValueError("should")
    if verdict != "wrong":
        should = None
    with _LOCK:
        v = _verdicts()
        rec = {"verdict": verdict, "should": should, "domain": domain or (v.get(sid) or {}).get("domain"),
               "at": _now().isoformat(timespec="seconds"), "by": by}
        v[sid] = rec
        p = _verdict_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(p)
    return rec


def summary() -> list[dict]:
    """분야별 판정 결과 — 오분류율 = 틀림 ÷ (맞음 + 틀림). 놓침(다른 분야였어야 하는데 이 분야로 간 것)은 '맞는 분야' 쪽에 셈."""
    cnt: dict[str, dict[str, int]] = defaultdict(lambda: {"right": 0, "wrong": 0, "unsure": 0, "missed": 0})
    for rec in _verdicts().values():
        dom = rec.get("domain")
        if dom not in LABELS:
            continue
        cnt[dom][rec["verdict"]] += 1
        if rec["verdict"] == "wrong" and rec.get("should") in LABELS:
            cnt[rec["should"]]["missed"] += 1
    out = []
    for dom in [d for d in LABELS if d in cnt]:
        c = cnt[dom]
        den = c["right"] + c["wrong"]
        out.append({"domain": dom, "label": LABELS[dom], **c, "judged": den + c["unsure"],
                    "error_rate": round(c["wrong"] / den, 4) if den else None, "observe": den < OBSERVE_BELOW})
    return out


def prune(now: datetime | None = None) -> int:
    """90일 지난 샘플 파일을 지운다 (판정 기록은 문장이 없어 남긴다)."""
    now = now or _now()
    cut = (now - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    n = 0
    for p in _dir().glob("????-??-??.jsonl") if _dir().is_dir() else []:
        if p.stem < cut:
            p.unlink(missing_ok=True)
            n += 1
    return n


__all__ = ["record", "samples", "judge", "summary", "prune", "picked", "LABELS", "VERDICTS"]
