"""실수 신호 모으기 (2026-11-16) — 손님이 알려 주지 않아도 '잘못 알아들었을 수 있는' 대화를 모은다.

일주일에 한 번 `uv run python scripts/miss_report.py` 로 모아 보고, 고칠 문장은 테스트 문장으로 옮긴 뒤 규칙·프롬프트를 고친다.
(실수 발견 → 테스트 문장 추가 → 고침 → 전체 테스트)

신호 종류
- weak_match   상품을 보여 줬는데 고른 상품명이 검색어 낱말과 거의 안 겹침 ('최강록 쉐프 라면' → '쉐프의 치킨스톡')
- zero         상품·레시피를 찾았는데 하나도 못 보여 줌
- requery      상품을 보여 준 뒤 3분 안에 손님이 비슷한 말로 다시 찾거나 '다른 거'를 요청
- review_left  레시피 카드에 고쳐 쓴 뒤에도 '검토 AI 의견'이 남음
- intent_rejected  문장 뜻 읽기(LLM) 답이 검사에서 버려져 규칙으로 넘어감
- source_failed    쿠팡(주 경로)을 불러오지 못함 — 2026-11-16 R3 ④ 로 DB 예비 경로가 없어져 그대로 안내만 나감

저장: var/signals/YYYY-MM-DD.jsonl (한 줄에 신호 하나). 데이터베이스를 바꾸지 않고, 실패해도 대화는 그대로 진행된다.
개인정보: 손님 문장은 앞 200자만, 세션 id 는 앞 8자만 남긴다. 베타 전에 개인정보 처리방침에 '서비스 개선을 위한 대화 기록'을 적는다.
끄기: MISS_SIGNALS=off
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)
KST = timezone(timedelta(hours=9))
_LOCK = threading.Lock()
_LAST: dict[str, dict] = {}            # 세션 → 직전에 상품을 보여 준 턴 (이 서버 프로세스 안에서만)
REQUERY_SECONDS = 180

# 검색어에서 뺄 말 — 요청·꾸밈 말은 상품명에 없어도 정상
_STOP = re.compile(r"^(?:추천|추천해|상품|제품|보여|보여줘|보여주세요|찾아|찾아줘|사고|사고싶어|살래|사줘|주문|레시피|만드는|만들기|방법|"
                   r"알려|알려줘|알려주세요|좀|요즘|최신|유행|인기|맛있는|맛있게|저렴한|싼|가성비|좋은|괜찮은|있어|있나요|어디|뭐|"
                   r"비교|비교해|싸게|빠른|배송|로켓|구매|구입|어떤|어떤게|주세요|해줘|해주세요|해요|할래)$")
_PARTICLE = re.compile(r"(?:을|를|이|가|은|는|도|로|으로|에|에서|의|와|과|랑|이랑|하고)$")
_OTHER_RE = re.compile(r"다른\s*(?:거|것|상품|제품)|말고|별로|이거\s*아니|아니(?:고|라)|엉뚱")
_SPELL = (("쉐프", "셰프"), ("스테이크", "스테익"))


def enabled() -> bool:
    return os.getenv("MISS_SIGNALS", "on").lower() not in ("off", "0", "false", "no")


def _dir() -> Path:
    return Path(os.getenv("MISS_SIGNALS_DIR", "var/signals"))


def record(kind: str, *, text: str | None, sid: str | None = None, stage: str | None = None, **detail) -> None:
    """신호 하나를 오늘 파일에 한 줄로. 어떤 오류도 대화를 막지 않는다."""
    if not enabled():
        return
    try:
        now = datetime.now(KST)
        row = {"at": now.isoformat(timespec="seconds"), "kind": kind, "text": (text or "")[:200],
               "sid": (sid or "")[:8], "stage": stage, **detail}
        path = _dir() / f"{now:%Y-%m-%d}.jsonl"
        with _LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        log.warning("miss signal not saved", exc_info=True)


def words(text: str) -> list[str]:
    """검색어의 뜻 있는 낱말 ('최강록 쉐프 라면 추천해 줘' → ['최강록', '셰프', '라면'])."""
    out = []
    for tok in re.split(r"[\s,.?!~/]+", text or ""):
        tok = _PARTICLE.sub("", tok) if len(tok) > 2 else tok
        for a, b in _SPELL:
            tok = tok.replace(a, b)
        if len(tok) >= 2 and not _STOP.match(tok) and not re.fullmatch(r"\d+\S*", tok) and tok not in out:
            out.append(tok)
    return out


def _norm(title: str) -> str:
    t = re.sub(r"\s+", "", title or "")
    for a, b in _SPELL:
        t = t.replace(a, b)
    return t


def _shown(blocks: list[dict]) -> list[str]:
    """화면에 펼쳐 보인 상품 이름 (접힌 '더 보기'·'다른 후보'는 빼고)."""
    names = []
    for b in blocks or []:
        data = b.get("data") or {}
        if b.get("type") != "product_list" or data.get("collapsed"):
            continue
        for it in data.get("items") or []:
            name = it.get("title") or it.get("name") or it.get("product_name")
            if name:
                names.append(str(name))
    return names


def observe(sid: str, text: str | None, response: dict) -> None:
    """한 턴이 끝난 뒤 신호를 찾는다 (대화 결과는 바꾸지 않는다)."""
    if not enabled() or not text:
        return
    try:
        _observe(sid, text, response)
    except Exception:  # noqa: BLE001
        log.warning("miss signal check failed", exc_info=True)


def _observe(sid: str, text: str, response: dict) -> None:
    stage = response.get("stage") or ""
    blocks = response.get("blocks") or []
    dumped = json.dumps(blocks, ensure_ascii=False)
    shown = _shown(blocks)
    asked = words(text)
    now = time.time()

    # 다시 찾기: 직전에 상품을 보여 줬고 3분 안에 '다른 거' 또는 같은 낱말로 다시 찾음
    last = _LAST.get(sid)
    if last and now - last["at"] <= REQUERY_SECONDS:
        same = set(asked) & set(last["words"])
        if _OTHER_RE.search(text) or (same and shown and text.strip() != last["text"].strip()):
            record("requery", text=text, sid=sid, stage=stage, before=last["text"][:200], before_items=last["items"][:4])

    if shown:
        # 낱말이 둘 이상인데 상품명이 그중 절반도 못 담으면 '약한 일치'
        if len(asked) >= 2:
            weak = [n for n in shown[:4] if sum(w in _norm(n) for w in asked) * 2 < len(asked)]
            if weak:
                record("weak_match", text=text, sid=sid, stage=stage, words=asked, items=weak[:4], shown=len(shown))
        _LAST[sid] = {"at": now, "text": text, "words": asked, "items": shown[:4]}
        if len(_LAST) > 5000:                       # 오래된 세션 정리
            for k in sorted(_LAST, key=lambda k: _LAST[k]["at"])[:1000]:
                _LAST.pop(k, None)
    elif ("product" in stage or "shop" in stage) and "불러오지 못했" in dumped:
        record("source_failed", text=text, sid=sid, stage=stage, what="상품")
    elif ("product" in stage or "shop" in stage) and "찾지 못했" in dumped:
        record("zero", text=text, sid=sid, stage=stage, what="상품")
    if "recipe_other" in stage and "찾지 못했" in dumped:
        record("zero", text=text, sid=sid, stage=stage, what="레시피 글")
    if any(b.get("type") == "recipe_card" and ((b.get("data") or {}).get("review") or (b.get("data") or {}).get("review_notes"))
           for b in blocks) or "검토 AI 의견" in dumped:
        record("review_left", text=text, sid=sid, stage=stage)
