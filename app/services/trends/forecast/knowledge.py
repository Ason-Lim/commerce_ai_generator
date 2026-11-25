"""예보 지식 묶음 · 학습용 데이터셋 · AI에게 묻기 (2026-11-25)
=========================================================

사용자 요청(11-25 10:40): 예보·백테스트·트렌드 변화 결과를 Claude·Ollama 가 '학습'하고 계속 업데이트되게.

**'학습'을 두 가지로 나눈다** (사실대로):
  1. 지식 묶음(바로 씀) — 매주 최신 결과를 한 묶음(`var/forecast/knowledge/YYYY-MM-DD.json`)으로 만들어 질문할 때마다
     Claude·Ollama 에 함께 준다. 모델 자체는 바뀌지 않지만 **답은 늘 최신 결과를 근거로** 한다. Claude(API)는 우리가
     모델을 고쳐 학습시킬 수 없으므로 이 방식만 가능하다.
  2. 데이터셋(나중에 Ollama 미세조정용) — 같은 결과를 대화형 JSONL(`system/user/assistant`)로 쌓는다(`var/forecast/dataset/`).
     관리자가 '좋은 답'으로 표시한 질문·답도 들어간다. 미세조정(LoRA 등)은 **지금 하지 않는다** — 숫자가 매주 바뀌어
     학습하면 옛 숫자를 외우게 되고, 자료가 아직 적다. 실제 예보 12주 뒤 다시 판단.
* 고객 문장은 넣지 않는다(11-22 결정 '고객 문장으로 학습하지 않음' 유지). 넣는 것은 공개 순위 집계 결과·규칙 정의뿐.
* 관측 결과는 원인 확정이 아니다(GPT 11-25) — 지식 묶음·답에도 그대로 적는다.
* 관리자 전용 — 고객 화면·추천 순위에는 쓰지 않는다.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path


VERSION = "2026-11-25"
NAMES = {"recent": "최근 유지", "last_year": "전년 같은 주", "last_year_lunar": "전년 기준(비교 기준)",
         "event_rel": "행사 상대일", "explorer": "탐색기", "explorer_repeat": "탐색기(반복만)"}  # fmt: skip

RULES = [
    "주 지표: 28일 · 제출 상위 20 · 선행 적중률 = 첫 100위 진입이 기준일 7~28일 뒤인 적중 ÷ 제출 수(분모 = 제출 전체).",
    "비교 기준 = 전년 기준: 평소 전년 같은 주(364일), 설·추석 D-35~D+7 은 전년 같은 명절 날짜에 맞춤.",
    "목표: 두 해 백테스트 모두 비교 기준 이상. 수치 목표는 실제 예보 12주가 채점되면 다시 정함.",
    "보조 지표 1 — 제출 결과 4분류(분모 = 제출, 합 100%): 선행 적중(7~28일) · 선행 부족 적중(1~6일) · 시점 어긋남(앞뒤 14일 안 진입) · 관측창 내 미진입.",
    "보조 지표 2 — 실제 주요 상승(50위 안) 중 '과거 400일 Top500 관측 이력 없음' 비율(분모 = 실제 주요 상승). 과거 순위 파일 90% 미만이면 판정 안 함.",
    "관측창 내 미진입은 관측 결과이지 원인 확정이 아니다 — 트렌드 변화는 검토 가설(더 큰 시점 차이·작년 일회성일 수도).",
    "백테스트(2024~2026)는 규칙을 만들 때 본 자료라 참고값. 진짜 성적은 매주 먼저 적어 두는 예보 장부(28+14일 뒤 채점).",
    "예보·트렌드 결과는 관리자 참고용 — 고객 화면·추천 순위에 쓰지 않는다.",
]

SYSTEM = (
    "너는 trendguide 의 식품 키워드 예보 분석 도우미다. 아래 '지식 묶음'에 있는 숫자·규칙만 근거로 한국어로 답한다. "
    "묶음에 없는 숫자는 만들지 말고 '자료에 없음'이라고 말한다. 관측 결과를 원인으로 단정하지 않는다(가설이면 가설이라고). "
    "백테스트는 참고값, 예보 장부가 진짜 성적이라는 점을 지킨다. 답은 짧게, 근거로 쓴 항목(기준일·방법·표)을 밝힌다."
)


def root() -> Path:
    env = os.environ.get("FORECAST_KNOWLEDGE_DIR")
    return Path(env) if env else Path(__file__).resolve().parents[4] / "var" / "forecast"


def _latest_backtests(forecast_dir: Path, skipped: list | None = None) -> list[dict]:
    """var/forecast/backtest_*.json 중 **지금 형식**(짝 비교 `paired` 있음 = 11-25 백필 뒤 코드) 결과만 요약(28일만).
    옛 형식(백필 전 실행·짝 비교 없음)은 숫자가 낡았을 수 있어 묶음에 넣지 않고 skipped 에 이름을 남긴다(11-25 운영 확인)."""
    out = []
    for p in sorted(forecast_dir.glob("backtest_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(d, dict) or "metrics" not in d:
            continue
        if p.stem.endswith("_exp"):  # 순서 실험(2026-11-25) — 기본 방법 결과가 아님
            continue
        if "paired" not in d or not d.get("question"):
            if skipped is not None:
                skipped.append(
                    {"file": p.name, "why": "옛 형식(짝 비교 없음) — 지금 코드로 다시 실행해야 묶음에 들어감"}
                )
            continue
        rows = {}
        for m, byh in d["metrics"].items():
            x = byh.get("28") or byh.get(28) or {}
            rows[NAMES.get(m, m)] = {"선행적중률": x.get("top20_lead7"), "4분류": x.get("miss_breakdown")}
        paired = {NAMES.get(m, m): (v.get("28") or v.get(28)) for m, v in (d.get("paired") or {}).items()}
        u = (d.get("union") or {}).get("28") or (d.get("union") or {}).get(28) or {}
        run_at = dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")
        out.append({"file": p.name, "run_at": run_at, "question": d.get("question"), "range": d.get("range"), "dates": d.get("dates"),
                    "min_share": (d.get("rules") or {}).get("future_min_share"), "methods": rows, "paired_vs_baseline": paired,
                    "major_missed_all": u.get("major_missed_all"), "no_history_share": u.get("first_seen_share")})  # fmt: skip
    return out


def build(rank_dir, *, today: dt.date | None = None, save: bool = True, ledger_root: Path | None = None) -> dict:
    """지식 묶음 만들기 — 규칙 · 백테스트 요약 · 예보 장부 성적 · 트렌드 변화(최근) · 다음 4주 후보(상위)."""
    from app.services.trends.forecast import ledger
    from app.services.trends.forecast import next_weeks as nw
    from app.services.trends.forecast import trend_shift as ts

    today = today or dt.date.today()
    snap: dict = {"version": VERSION, "built_at": dt.datetime.now().isoformat(timespec="seconds"), "rules": RULES}
    skipped: list = []
    snap["backtests"] = _latest_backtests(root(), skipped)
    snap["backtests_skipped"] = skipped
    try:
        ev = ledger.evaluate(rank_dir, root=ledger_root)
        snap["ledger"] = {k: ev[k] for k in ("graded_weeks", "pending", "summary", "first_seen", "target", "metric")}
    except Exception as e:  # noqa: BLE001
        snap["ledger"] = {"error": str(e)}
    d0 = ts.default_as_of(rank_dir)
    if d0:
        r = ts.report(rank_dir, d0, limit=15)
        snap["trend_shift"] = {k: r.get(k) for k in ("as_of", "window", "status", "missing_days", "history_ok", "last_year_major",
                                                    "came_back", "timing_off", "not_entered", "not_entered_share",
                                                    "major_rise", "no_history", "no_history_share",
                                                    "not_entered_items", "no_history_items")}  # fmt: skip
        snap["trend_shift_weekly"] = ts.weekly(rank_dir, d0, weeks=8)
    as_of = today - dt.timedelta(days=1)
    try:
        f = nw.next_weeks(rank_dir, as_of, top_n=10)
        snap["next4w"] = {"as_of": f["as_of"], "status": f["status"],
                          "weeks": [{"start": w["start"], "end": w["end"], "events": [e["event"] for e in w["events"]],
                                     "top": [{"keyword": i["keyword"], "last_year_best": i["last_year_best"],
                                              "sources": i["sources"][:2],
                                              "explorer_repeat": bool(i.get("explorer_repeat"))} for i in w["items"]]}
                                    for w in f.get("weeks", [])]}  # fmt: skip
    except Exception as e:  # noqa: BLE001
        snap["next4w"] = {"error": str(e)}
    if save:
        p = root() / "knowledge" / f"{today.isoformat()}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
        snap["path"] = str(p)
    return snap


def latest() -> dict | None:
    files = sorted((root() / "knowledge").glob("????-??-??.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def context_text(snap: dict, max_chars: int = 24000) -> str:
    """모델에 줄 글 — JSON 을 그대로(숫자 왜곡 없이), 길면 목록부터 줄인다."""
    s = dict(snap)
    s.pop("path", None)
    txt = json.dumps(s, ensure_ascii=False, separators=(",", ":"))
    if len(txt) > max_chars and isinstance(s.get("trend_shift"), dict):
        s["trend_shift"] = {k: v for k, v in s["trend_shift"].items() if not k.endswith("_items")}
        txt = json.dumps(s, ensure_ascii=False, separators=(",", ":"))
    return txt[:max_chars]


# ── 데이터셋 (대화형 JSONL — Ollama 미세조정·평가용, 지금은 쌓기만) ──
def _pct(v) -> str:
    return "자료 없음" if v is None else f"{v * 100:.1f}%"


def qa_pairs(snap: dict) -> list[dict]:
    """지식 묶음에서 사실 그대로의 질문·답을 만든다(템플릿 — 모델이 만든 문장 아님)."""
    out: list[dict] = []

    def add(q: str, a: str, kind: str):
        out.append({"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q},
                                 {"role": "assistant", "content": a}],
                    "meta": {"kind": kind, "built_at": snap.get("built_at"), "version": snap.get("version"), "source": "template"}})  # fmt: skip

    for r in snap.get("rules", []):
        if r.startswith("주 지표"):
            add("예보 주 지표가 뭐야?", r, "rule")
        elif r.startswith("비교 기준"):
            add("비교 기준은 어떻게 정해?", r, "rule")
        elif r.startswith("관측창 내 미진입"):
            add("관측창 내 미진입은 트렌드 변화야?", r, "rule")
    for b in snap.get("backtests", []):
        if b.get("question") != "q1" or b.get("min_share") not in (0.6, None):
            continue
        rng = "~".join(b.get("range") or [])
        base = (b["methods"].get("전년 기준(비교 기준)") or {}).get("선행적중률")
        lines = [f"{m}: {_pct(x.get('선행적중률'))}" for m, x in b["methods"].items()]
        add(f"{rng} 백테스트에서 방법별 28일 선행 적중률은?",
            f"평가일 {b.get('dates')}개, 28일·상위 20 선행 적중률 — " + " · ".join(lines)
            + f". 비교 기준(전년 기준) {_pct(base)}. 백테스트는 규칙을 만들 때 본 자료라 참고값이에요.", "backtest")  # fmt: skip
        for m, p in (b.get("paired_vs_baseline") or {}).items():
            if p and p.get("dates"):
                add(f"{rng}에 {m}은 비교 기준보다 꾸준히 나았어?",
                    f"같은 평가일 {p['dates']}일 중 나음 {p['better']} · 같음 {p['same']} · 못함 {p['worse']}, 평균 차이 "
                    f"{p['mean_diff_pp']:+.1f}%p. " + ("날짜별로 갈려 일관된 개선이라 보기 어려워요." if p["better"] - p["worse"] < p["dates"] / 4 else "대체로 나았어요."),
                    "paired")  # fmt: skip
    t = snap.get("trend_shift") or {}
    if t.get("status") == "ok":
        ne = ", ".join(x["keyword"] for x in (t.get("not_entered_items") or [])[:10]) or "없음"
        add(f"기준일 {t['as_of']} 이후 28일 동안 작년엔 50위 안이었는데 올해 안 들어온 키워드는?",
            f"작년 이 기간 50위 안 {t['last_year_major']}개 중 다시 진입 {t['came_back']} · 시점 어긋남 {t['timing_off']} · "
            f"관측창 내 미진입 {t['not_entered']}({_pct(t.get('not_entered_share'))}). 예: {ne}. 관측 결과이고, 수요 변화인지는 "
            "검토할 가설이에요(더 큰 시점 차이나 작년 일회성일 수도).", "trend_shift")  # fmt: skip
        if t.get("no_history") is not None:
            nh = ", ".join(x["keyword"] for x in (t.get("no_history_items") or [])[:10]) or "없음"
            add(f"기준일 {t['as_of']} 이후 28일에 과거 이력 없이 새로 50위 안에 든 키워드는?",
                f"주요 상승 {t['major_rise']}개 중 과거 400일 Top500 관측 이력 없음 {t['no_history']}개"
                f"({_pct(t.get('no_history_share'))}). 예: {nh}.", "trend_shift")  # fmt: skip
    lg = snap.get("ledger") or {}
    if "graded_weeks" in lg:
        add("예보 장부 성적은 지금 어때?",
            f"채점된 실제 예보 {lg['graded_weeks']}주, 대기 {lg['pending']}주. 목표 재설정까지 {lg['target']['weeks_left']}주. "
            + ("아직 채점된 주가 없어 실제 성적은 없어요." if not lg["graded_weeks"] else
               " · ".join(f"{x['name']} {_pct(x['lead7_rate'])}" for x in lg["summary"].values())), "ledger")  # fmt: skip
    return out


def append_dataset(rows: list[dict], name: str) -> Path:
    p = root() / "dataset" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def export_week(snap: dict) -> dict:
    """이번 묶음의 템플릿 질문·답을 주별 파일로 (덮어씀 — 같은 주 재실행 안전)."""
    day = (snap.get("built_at") or dt.date.today().isoformat())[:10]
    p = root() / "dataset" / f"forecast_qa_{day}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = qa_pairs(snap)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return {"path": str(p), "rows": len(rows)}


# ── AI에게 묻기 ──
PROVIDERS = ("anthropic", "ollama")


class _HttpClaude:
    """Claude 를 SDK 없이 httpx 로 (운영 맥엔 anthropic SDK 가 선택 설치라 없음 — 11-25 운영 확인).
    nlu.llm_client._anthropic 과 같은 방식. Claude 5.5 는 temperature 를 받지 않고 생각까지 포함해 출력 상한을 넉넉히."""

    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str, post=None):
        self.model = model
        self.post = post

    @property
    def s(self):  # ask() 기록용 — getattr(client.s, "anthropic_model")
        return type("S", (), {"anthropic_model": self.model})

    def chat(self, system: str, user: str, *, max_tokens: int = 8000, **_) -> str:
        key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY 미설정")
        post = self.post
        if post is None:
            import httpx

            post = httpx.post
        body = {"model": self.model, "max_tokens": max(max_tokens, 8000), "system": system,
                "messages": [{"role": "user", "content": user}]}  # fmt: skip
        r = post(self.URL, json=body, timeout=180,
                 headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})  # fmt: skip
        if r.status_code >= 400:
            raise RuntimeError(f"Claude API {r.status_code}: {r.text[:200]}")
        data = r.json()
        u = data.get("usage") or {}
        try:
            from app.services.ai import usage

            usage.record("admin_llm", f"anthropic:{data.get('model') or self.model}", u.get("input_tokens") or 0,
                         u.get("output_tokens") or 0)  # fmt: skip
        except Exception:  # noqa: BLE001 — 비용 기록 실패는 답을 막지 않음
            pass
        text = "".join(b.get("text", "") for b in data.get("content") or [] if b.get("type") == "text")
        if not text:
            raise RuntimeError(f"Claude 빈 응답 ({data.get('stop_reason')})")
        return text


def ask(question: str, provider: str, *, snap: dict | None = None, client=None) -> dict:
    """최신 지식 묶음을 함께 주고 묻는다. provider = anthropic(Claude) | ollama. 기록은 ask_log.jsonl(관리자 질문만)."""
    from app.admin.shared.config import get_settings
    from app.admin.shared.llm import LLMClient

    if provider not in PROVIDERS:
        raise ValueError("provider 는 anthropic 또는 ollama")
    snap = snap or latest()
    if snap is None:
        raise LookupError("지식 묶음이 아직 없어요 — '지식 묶음 새로 만들기'를 먼저 눌러 주세요")
    if client is None:
        if provider == "anthropic":
            client = _HttpClaude(get_settings().anthropic_model)
        else:
            from dataclasses import replace

            client = LLMClient(replace(get_settings(), llm_provider=provider))
    user = f"[지식 묶음 — {snap.get('built_at')}]\n{context_text(snap)}\n\n[질문]\n{question.strip()}"
    answer = client.chat(SYSTEM, user, max_tokens=1500, temperature=0.2)
    rec = {"at": dt.datetime.now().isoformat(timespec="seconds"), "provider": provider,
           "model": getattr(getattr(client, "s", None), f"{provider}_model", None),
           "knowledge_built_at": snap.get("built_at"), "question": question.strip(), "answer": answer, "rating": None}  # fmt: skip
    p = root() / "ask_log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def ask_log(limit: int = 30) -> list[dict]:
    p = root() / "ask_log.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return rows[-limit:]


def rate(at: str, rating: str, corrected: str | None = None) -> dict:
    """관리자 평가: good(그대로 데이터셋) · fix(고친 답으로) · bad(버림). good/fix 는 dataset/forecast_ask_gold.jsonl 에 추가."""
    if rating not in ("good", "fix", "bad"):
        raise ValueError("rating 은 good · fix · bad")
    p = root() / "ask_log.jsonl"
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
    hit = next((r for r in rows if r["at"] == at), None)
    if hit is None:
        raise LookupError("그 질문 기록이 없어요")
    already = hit.get("rating") in ("good", "fix")
    hit["rating"] = rating
    if corrected:
        hit["corrected"] = corrected
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    if rating in ("good", "fix") and not already:
        ans = corrected if rating == "fix" and corrected else hit["answer"]
        append_dataset([{"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": hit["question"]},
                                      {"role": "assistant", "content": ans}],
                         "meta": {"kind": "ask", "rating": rating, "provider": hit["provider"],
                                  "knowledge_built_at": hit["knowledge_built_at"], "source": "admin_rated"}}],
                       "forecast_ask_gold.jsonl")  # fmt: skip
    return hit


__all__ = [
    "build",
    "latest",
    "context_text",
    "qa_pairs",
    "export_week",
    "ask",
    "ask_log",
    "rate",
    "SYSTEM",
    "PROVIDERS",
]
