"""관련성 보조 판정 (Jev, TypeSafe AI) — 2026-11-12, 점수 연구 S6. **보조용**: 기본 규칙이 먼저, Jev 는 덧붙이기만.

기본 구조
  - 추천은 언제나 기존 규칙(service.relevant)만으로 돌아간다. 이 모듈이 실패·지연·꺼짐이면 카드는 **그대로**.
  - 판정 대상은 규칙을 이미 통과한 카드뿐. Jev 가 규칙이 뺀 상품을 되살리는 일은 없다.
  - 순위·점수·가격 판단에는 쓰지 않는다. 묻는 것은 하나: "이 상품이 요청 품목과 다른 상품인가" (예 확률).

모드 (.env RELEVANCE_ASSIST)
  off     (기본) Jev 를 부르지 않는다
  shadow  Jev 를 백그라운드로 부르고 판정만 기록한다 (var/relevance_assist/shadow.jsonl). 화면·지연 영향 없음
  assist  '다른 상품' 확률이 RELEVANCE_ASSIST_THRESHOLD(기본 0.85) 이상인 카드를 비교 후보에서 뺀다.
          단, 전부 빠지게 되면 아무것도 빼지 않는다. 순위가 바뀌므로 켜기 전에 새 기준점 비교·승인 필요

안전장치
  - 키(TYPESAFE_API_KEY) 없으면 off 와 같다
  - 시간 제한 RELEVANCE_ASSIST_TIMEOUT 초(기본 1.5). 넘으면 카드 그대로
  - 연속 실패 3번이면 5분 동안 부르지 않는다 (차단기)
  - 보내는 것은 검색어(추출된 품목 낱말)와 상품명뿐 — 고객이 쓴 문장 원문은 보내지 않는다
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

URL = "https://api.typesafe.ai/v1/systemone"
SHADOW_LOG = Path(__file__).resolve().parents[3] / "var" / "relevance_assist" / "shadow.jsonl"
MAX_CARDS = 20
FAIL_LIMIT = 3
COOLDOWN_S = 300

_lock = threading.Lock()
_fails = 0
_open_until = 0.0


def _mode() -> str:
    m = (os.getenv("RELEVANCE_ASSIST") or "off").strip().lower()
    return m if m in ("off", "shadow", "assist") else "off"


def _default_post(payload: dict, timeout: float) -> dict:
    import requests

    r = requests.post(URL, json=payload, timeout=timeout,
                      headers={"Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
                               "Content-Type": "application/json"})
    r.raise_for_status()
    return r.json()


def build_request(query: str, titles: list[str], model: str) -> dict:
    state = "\n".join([f"고객 검색어: {query}", "검색 결과 상품명:"]
                      + [f"{i}. {t}" for i, t in enumerate(titles, 1)])
    questions = {f"other_{i}": {
        "type": "noul",
        "instructions": f"{i}번 상품이 고객 검색어의 품목과 다른 상품인가요? "
                        "(다른 품목·다른 부위·가공식품·요리 완제품이면 예. 같은 품목의 다른 등급·크기·포장은 아니오)"}
        for i in range(1, len(titles) + 1)}
    return {"model": model, "state": state, "questions": questions}


def judge(query: str, titles: list[str], *, post: Callable[[dict, float], dict] | None = None) -> dict | None:
    """{'probs': [상품별 '다른 상품' 확률], 'model', 'ms'} — 실패·꺼짐·차단기 열림이면 None."""
    global _fails, _open_until
    if not titles or (post is None and not os.getenv("TYPESAFE_API_KEY")):
        return None
    with _lock:
        if time.monotonic() < _open_until:
            return None
    timeout = float(os.getenv("RELEVANCE_ASSIST_TIMEOUT") or 1.5)
    payload = build_request(query, titles, os.getenv("RELEVANCE_ASSIST_MODEL") or "jev-latest")
    t0 = time.monotonic()
    try:
        body = (post or _default_post)(payload, timeout)
        ans = body.get("answers") or {}
        probs = [float((ans.get(f"other_{i}") or {})["noul"]) for i in range(1, len(titles) + 1)]
    except Exception as exc:  # noqa: BLE001 — 어떤 실패든 추천은 규칙만으로 계속
        with _lock:
            _fails += 1
            if _fails >= FAIL_LIMIT:
                _open_until, _fails = time.monotonic() + COOLDOWN_S, 0
        log.warning("relevance assist skipped: %s", type(exc).__name__)
        return None
    with _lock:
        _fails = 0
    return {"probs": probs, "model": body.get("model"), "ms": round((time.monotonic() - t0) * 1000)}


def _record(query: str, titles: list[str], res: dict | None):
    try:
        SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with SHADOW_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "query": query,
                                "titles": titles, "result": res}, ensure_ascii=False) + "\n")
    except OSError:
        log.warning("relevance assist shadow log failed")


def apply(query: str, cards: list[dict], *, post: Callable[[dict, float], dict] | None = None,
          background: bool = True) -> list[dict]:
    """규칙을 통과한 cards 를 받아 돌려준다. off·실패면 그대로, shadow 면 기록만, assist 면 확신 높은 '다른 상품'만 뺀다."""
    mode = _mode()
    if mode == "off" or not cards or (post is None and not os.getenv("TYPESAFE_API_KEY")):
        return cards
    titles = [str(c.get("title") or "")[:120] for c in cards[:MAX_CARDS]]
    if mode == "shadow":
        def _run():
            _record(query, titles, judge(query, titles, post=post))
        if background:
            threading.Thread(target=_run, daemon=True).start()
        else:
            _run()
        return cards
    res = judge(query, titles, post=post)
    if res is None:
        return cards
    threshold = float(os.getenv("RELEVANCE_ASSIST_THRESHOLD") or 0.85)
    drop = {i for i, p in enumerate(res["probs"]) if p >= threshold}
    if not drop or len(drop) >= len(cards):
        return cards
    kept = [c for i, c in enumerate(cards) if i not in drop]
    log.info("relevance assist removed %d/%d (%s)", len(drop), len(cards), res.get("model"))
    return kept


def _reset_for_tests():
    global _fails, _open_until
    with _lock:
        _fails, _open_until = 0, 0.0
