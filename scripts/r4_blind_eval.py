"""R4 블라인드 평가 — 같은 후보를 정렬 규칙만 바꿔 보여 주고, 사람·GPT·Gemini 가 어느 1위가 나은지 고른다.

점수 연구의 첫 실험. 질문: "지금 순위(품질+가격)가 '가격만' 정렬보다 실제로 나은가?"
  (R1 에서 주 경로 순위가 가격 순위와 0.93~1.00 상관 → 품질 점수의 기여를 사람 판정으로 확인)

  capture <이름> [--path auto|db] [--gap 3]
      고정 질의마다 근거 화면(build_report)을 돌려 후보(picks+others)를 모으고,
      정렬 3가지(현행 / 100g당 / 상품가)의 상위 3개를 '목록 가·나·다'로 섞어 평가지를 만든다.
      상위 3개가 같은 정렬은 한 목록으로 합친다(어느 정렬이 같은지는 정답표에만).
      → var/r4/sheet_<이름>.md (평가자에게 그대로 붙여 넣기)  · var/r4/key_<이름>.json (정답표 — 평가 끝날 때까지 열지 않음)
        · var/r4/jev_<이름>.json (Jev 판정 모델용 질의별 state + questions — 답을 answers 에 evaluator=Jev 로 옮김)
  jev <이름> [--model jev-latest] [--threshold 0.5] [--gap 1]
      jev_<이름>.json 으로 TypeSafe API(POST /v1/systemone)를 질의마다 한 번 부르고 답을 answers 에 붙인다.
      불일치는 '예' 확률이 threshold 이상인 상품. 이미 Jev 답이 있는 질의는 건너뜀. 키: .env TYPESAFE_API_KEY
  import <이름> <평가자> <파일|->
      평가지 끝의 '답안' 표를 채운 파일(또는 GPT·Gemini 가 돌려준 표)을 answers 에 붙인다. '-' 면 붙여 넣기
  human <이름> [--limit 6]
      사람용 짧은 평가지 — AI 평가자끼리 답이 갈린 질의만 (사람 평가자는 2~3명, 자주 묻지 않음)
  score <이름>
      var/r4/answers_<이름>.csv  (열: evaluator,query,best,mismatch,reason)
        best     : 가 / 나 / 다 / 같음
        mismatch : 요청과 안 맞는 상품 번호, 세미콜론 구분 (예: 가2;다1), 없으면 비움
      → docs/claude/r4_result_<이름>.md (평가자별 정렬 승수, 평가자 간 일치, 정렬별 품목 불일치)

외부 호출: --path auto 는 고객과 같은 경로라 쿠팡 파트너스 API 를 질의마다 부른다(간격 --gap 초).
DB 는 읽기 전용 연결. 점수·순위 코드는 바꾸지 않는다.

사용 (Mac):  uv run python scripts/r4_blind_eval.py capture e1
             (평가 → var/r4/answers_e1.csv 작성)
             uv run python scripts/r4_blind_eval.py score e1
"""
from __future__ import annotations

import csv
import io
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "var" / "r4"

# 고정 질의 세트 — 과일(제철)·축수산·가공·문장형(예산·선물·용도)·레시피 재료
QUERIES = [
    "사과", "배", "샤인머스캣", "감귤", "딸기",
    "고등어", "한우 등심", "우유", "계란",
    "3만원 이하 샤인머스캣", "부모님 선물 사과", "가성비 귤 5kg",
    "굴국밥 재료 굴", "감바스용 새우", "자취생 간편식 닭가슴살",
]
ORDERINGS = ("current", "per100g", "price")
ORDER_LABEL = {"current": "현행(품질+가격 점수)", "per100g": "100g당(액체 100ml당) 가격", "price": "상품가"}
LIST_NAMES = ("가", "나", "다")
TOP = 3


def _setup():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from sqlalchemy import create_engine

    import app.main as m
    from app.core.config import resolve_database_url

    engine = create_engine(resolve_database_url(), pool_pre_ping=True,
                           connect_args={"options": "-c default_transaction_read_only=on"})
    m.engine_lifecycle._engine = engine
    m.bind_engine(engine)
    return m


def _shopping(path: str):
    from app.admin.ops import evidence

    if path == "db":
        return evidence.forced_db_shopping(), None
    from app.api.chat_routes import get_chat_service

    svc = get_chat_service()
    return svc.shopping, svc.keyword_extractor


def _f(v):
    """근거 값은 문자열('1000')로 올 수 있다 — 숫자로, 못 바꾸면 None."""
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _cand(r: dict) -> dict:
    per = r["per100g"]
    w = per.get("weight") or {}
    return {
        "url": r["url"], "title": (r["title"] or "")[:60], "mall": r["mall"],
        "price": _f(r["price"].get("price")), "price_status": r["price"].get("status"),
        "price_label": r["price"].get("label"),
        "per100g": _f(per["value"]) if per["comparable"] else None,
        "weight_g": _f(w.get("value")) if per["comparable"] else None,
        "per100g_label": per["label"],
        "volume_ml": _f(r.get("volume_ml")), "per100ml": _f(r.get("per100ml")),   # 2026-11-12: 액체
        "current_rank": r["display_rank"],
    }


def _order(cands: list[dict], how: str) -> list[dict]:
    big = float("inf")
    if how == "current":
        return sorted(cands, key=lambda c: c["current_rank"])
    if how == "per100g":   # 비교 가능한 100g당(액체는 100ml당) 먼저, 나머지는 상품가 순으로 뒤에
        unit = lambda c: c["per100g"] if c["per100g"] else c.get("per100ml")
        return sorted(cands, key=lambda c: (unit(c) is None, unit(c) or big, c["price"] or big, c["url"]))
    return sorted(cands, key=lambda c: (c["price"] is None, c["price"] or big, c["url"]))


def _item_line(i: int, c: dict) -> str:
    price = f"{c['price']:,.0f}원" if isinstance(c["price"], (int, float)) else "가격 없음"
    if c["per100g"]:
        per = (f"{c['weight_g']:,.0f}g · " if c["weight_g"] else "") + f"100g당 {c['per100g']:,.0f}원"
    elif c.get("per100ml"):
        per = (f"{c['volume_ml']:,.0f}ml · " if c.get("volume_ml") else "") + f"100ml당 {c['per100ml']:,.0f}원"
    else:
        per = "100g당 비교 불가"
    note = "" if c["price_status"] == "live" else f" · {c['price_label'] or '가격 확인 시각 없음'}"
    return f"   {i}. {c['title']} — {c['mall'] or '판매처 미상'} · {price} · {per}{note}"


def _jev_request(q: str, entry: dict, by_url: dict) -> dict:
    """Jev(TypeSafe AI 판정 모델) 입력 — state 는 질의와 목록, questions 는 정해진 답만 고르는 질문.
    playground 에 그대로 붙이거나, 키가 생기면 API(state + questions)로 보낸다. 답은 확률과 함께 돌아온다."""
    names = list(entry["lists"])
    state = [f"고객 요청: {q}", "같은 검색 결과를 서로 다른 기준으로 정렬한 상위 3개 목록입니다."]
    criteria = {n: f"목록 {n}의 1위 상품이 가장 살 만하다" for n in names}
    criteria["같음"] = "목록들의 1위 사이에 의미 있는 차이가 없다"
    questions: dict[str, dict] = {
        "best": {"type": "choice", "criteria": criteria,
                 "instructions": "1위 상품이 고객 요청에 가장 '살 만한' 목록을 고르세요. "
                                 "상품명·판매처·가격·중량만 보고 판단합니다."},
    }
    for name in names:
        state.append(f"목록 {name}")
        for i, u in enumerate(entry["lists"][name]["urls"], start=1):
            state.append(_item_line(i, by_url[u]).strip())
            questions[f"mismatch_{name}{i}"] = {
                "type": "noul",                       # TypeSafe 의 예/아니오 유형 (답은 '예' 확률)
                "instructions": f"목록 {name}의 {i}번 상품이 고객 요청 품목과 다른 상품인가요? "
                                "(다른 품목·가공품·용도 불일치면 true)"}
    return {"query": q, "state": "\n".join(state), "questions": questions}


def capture(label: str, path: str, gap: float):
    _setup()
    from app.admin.ops import evidence

    shopping, extractor = _shopping(path)
    rng = random.Random(f"r4-{label}")
    run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    key = {"label": label, "run_at": run_at, "path": path, "queries": {}}
    sheet = [f"# 추천 목록 블라인드 평가 ({label})", "",
             "같은 검색 결과를 서로 다른 기준으로 정렬한 상위 3개 목록입니다. 어떤 기준인지는 알려 드리지 않습니다.",
             "상품명·판매처·가격·중량만 보고 판단해 주세요(페이지를 열어 볼 필요 없음).", "",
             "질의마다 답해 주세요:",
             "1. **best**: 1위 상품이 가장 '살 만한' 목록 (가 / 나 / 다 / 같음)",
             "2. **mismatch**: 요청과 맞지 않는 상품 번호 (예: 가2, 다1 — 없으면 '없음')",
             "3. **reason**: 이유 한 줄", "",
             "답은 표로: `질의 | best | mismatch | reason`", ""]
    n_calls = 0
    jev: list[dict] = []
    for q in QUERIES:
        if path == "auto" and n_calls:
            time.sleep(gap)
        n_calls += 1
        try:
            with redirect_stdout(io.StringIO()):
                rep = evidence.build_report(q, shopping=shopping, keyword_extractor=extractor)
            err = rep["error"]
        except Exception as exc:  # noqa: BLE001
            rep, err = {"rows": [], "path": None}, f"{type(exc).__name__}: {str(exc)[:160]}"
        cands = [_cand(r) for r in rep["rows"] if r["section"] in ("picks", "others")]
        entry = {"path": rep.get("path"), "error": err, "candidates": cands, "lists": {}}
        if len(cands) < 2:
            key["queries"][q] = entry
            sheet += [f"## {q}", "", f"- 후보 부족({len(cands)}개) — 평가 제외" + (f" ({err})" if err else ""), ""]
            continue
        # e1 교훈: 대안 정렬이 예산을 무시하면 비교가 불공정 — 예산 밖 후보는 모든 정렬에서 뒤로 (현행은 원래 그렇게 함)
        from app.services.chat.budget import fits, parse_budget

        budget = parse_budget(q)
        if budget and not budget.get("none"):
            for c in cands:
                c["over_budget"] = not fits(c["price"] or 0, budget)
        tops = {how: [c["url"] for c in sorted(_order(cands, how), key=lambda c: bool(c.get("over_budget")))[:TOP]]
                for how in ORDERINGS}
        groups: dict[tuple, list[str]] = {}
        for how in ORDERINGS:
            groups.setdefault(tuple(tops[how]), []).append(how)
        group_list = list(groups.items())
        rng.shuffle(group_list)
        by_url = {c["url"]: c for c in cands}
        sheet += [f"## {q}", ""]
        for name, (urls, hows) in zip(LIST_NAMES, group_list):
            entry["lists"][name] = {"orderings": hows, "urls": list(urls)}
            sheet.append(f"**목록 {name}**")
            sheet += [_item_line(i, by_url[u]) for i, u in enumerate(urls, start=1)]
            sheet.append("")
        if len(group_list) == 1:
            sheet += ["- (세 기준의 상위 3개가 모두 같음 — best 는 '같음'으로)", ""]
        key["queries"][q] = entry
        if len(group_list) > 1:
            jev.append(_jev_request(q, entry, by_url))
    rated = [q for q, v in key["queries"].items() if v["lists"]]
    sheet += ["---", "", "## 답안 — 이 표를 채워 주세요", "",
              "mismatch 는 요청과 맞지 않는 상품 번호(예: `가2;다1`), 없으면 `없음`. "
              "목록이 하나뿐인 질의는 best 가 `같음`으로 미리 채워져 있습니다(mismatch 만 보면 됨).", "",
              "| 질의 | best | mismatch | reason |", "|---|---|---|---|"]
    sheet += [f"| {q} | {'같음' if len(key['queries'][q]['lists']) == 1 else ''} |  |  |" for q in rated]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"key_{label}.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / f"sheet_{label}.md").write_text("\n".join(sheet) + "\n", encoding="utf-8")
    (OUT / f"jev_{label}.json").write_text(json.dumps(jev, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / f"answers_{label}.csv").exists() or (OUT / f"answers_{label}.csv").write_text(
        "evaluator,query,best,mismatch,reason\n", encoding="utf-8")
    usable = sum(1 for v in key["queries"].values() if v["lists"])
    merged = sum(1 for v in key["queries"].values() if 0 < len(v["lists"]) < len(ORDERINGS))
    print(f"저장: {OUT / f'sheet_{label}.md'}  (질의 {len(QUERIES)}, 평가 가능 {usable}, "
          f"정렬끼리 상위 3개가 겹친 질의 {merged}, 경로 {Counter(v['path'] for v in key['queries'].values())})")


JEV_URL = "https://api.typesafe.ai/v1/systemone"


def run_jev(label: str, model: str, threshold: float, gap: float):
    """jev_<이름>.json 의 질의마다 Jev 를 한 번 부르고, 답을 answers_<이름>.csv 에 evaluator=Jev 로 붙인다.
    원 응답(확률 포함)은 var/r4/jev_raw_<이름>.json. 키: .env 의 TYPESAFE_API_KEY (값은 출력하지 않음)."""
    import os

    import requests
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    api_key = os.getenv("TYPESAFE_API_KEY")
    if not api_key:
        sys.exit("TYPESAFE_API_KEY 가 .env 에 없습니다")
    reqs = json.loads((OUT / f"jev_{label}.json").read_text(encoding="utf-8"))
    answers_path = OUT / f"answers_{label}.csv"
    done = {r["query"] for r in csv.DictReader(answers_path.open(encoding="utf-8")) if r["evaluator"] == "Jev"}
    raw_path = OUT / f"jev_raw_{label}.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
    new_rows, usage = [], Counter()
    for n, rq in enumerate(r for r in reqs if r["query"] not in done):
        if n:
            time.sleep(gap)
        resp = requests.post(JEV_URL, timeout=30, headers={"Authorization": f"Bearer {api_key}",
                                                          "Content-Type": "application/json"},
                             json={"model": model, "state": rq["state"], "questions": rq["questions"]})
        if resp.status_code != 200:
            print(f"{rq['query']}: HTTP {resp.status_code} {resp.text[:300]}")
            continue
        body = resp.json()
        raw[rq["query"]] = {"request_id": resp.headers.get("x-typesafe-request-id"), **body}
        ans = body.get("answers") or {}
        best = (ans.get("best") or {}).get("choice", "")
        mism = [k.removeprefix("mismatch_") for k, v in ans.items()
                if k.startswith("mismatch_") and (v.get("noul") or 0) >= threshold]
        conf = (ans.get("best") or {}).get("confidence")
        new_rows.append({"evaluator": "Jev", "query": rq["query"], "best": best, "mismatch": ";".join(mism),
                         "reason": f"jev {body.get('model')} best_conf={conf} threshold={threshold}"})
        for k, v in (body.get("usage") or {}).items():
            usage[k] += v
        print(f"{rq['query']}: best={best} (확신 {conf}) · 불일치 {mism or '없음'}")
    raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    with answers_path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["evaluator", "query", "best", "mismatch", "reason"])
        w.writerows(new_rows)
    print(f"Jev 답 {len(new_rows)}개 추가 → {answers_path}  · 사용량 {dict(usage)}")


def import_answers(label: str, evaluator: str, src: str):
    """채운 답안 표(마크다운)를 answers_<이름>.csv 에 evaluator 이름으로 붙인다. src='-' 이면 붙여 넣기(입력 끝: Ctrl-D).
    같은 평가자·질의의 이전 답은 새 답으로 바꾼다."""
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    key = json.loads((OUT / f"key_{label}.json").read_text(encoding="utf-8"))
    new = {}
    for line in text.splitlines():
        cells = [c.strip().strip("*`") for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("질의", "") or set(cells[0]) <= set("-: "):
            continue
        q = cells[0]
        if q not in key["queries"]:
            print(f"건너뜀(평가지에 없는 질의): {q}")
            continue
        # 번호만 뽑는다 ('나2는 부위 불일치' → 나2). 설명이 붙은 답은 원문을 reason 앞에 남긴다
        toks = re.findall(r"[가나다]\d", cells[2])
        note = "" if re.fullmatch(r"[\s가나다\d,;·없음—\-]*", cells[2]) else f"[mismatch 원문: {cells[2]}] "
        picks_ = re.findall(r"[가나다]\d", cells[1])     # 2026-11-12: 상품 번호로 답해도 받는다 (예: 나2;다2)
        lists_ = re.findall(r"[가나다](?!\d)", re.sub(r"[가나다]\d", "", cells[1]))  # '나·다 공동' → 나;다 (공동 1위)
        best = (cells[1] if cells[1] in ("가", "나", "다", "같음") else
                ";".join(dict.fromkeys(picks_)) if picks_ else
                ";".join(dict.fromkeys(lists_)) if lists_ else ("같음" if "같음" in cells[1] else ""))
        new[q] = {"evaluator": evaluator, "query": q, "best": best, "mismatch": ";".join(dict.fromkeys(toks)),
                  "reason": note + (cells[3] if len(cells) > 3 else "")}
    path = OUT / f"answers_{label}.csv"
    old = [r for r in csv.DictReader(path.open(encoding="utf-8"))
           if not (r["evaluator"] == evaluator and r["query"] in new)]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["evaluator", "query", "best", "mismatch", "reason"])
        w.writeheader()
        w.writerows(old + list(new.values()))
    blank = [q for q, r in new.items() if not r["best"]]
    print(f"{evaluator}: {len(new)}개 질의 저장 → {path}" + (f" · best 비어 있음: {', '.join(blank)}" if blank else ""))


def score(label: str):
    key = json.loads((OUT / f"key_{label}.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((OUT / f"answers_{label}.csv").open(encoding="utf-8")))
    wins = defaultdict(Counter)          # evaluator → ordering → 1위 승
    contested = defaultdict(int)         # evaluator → 실제로 갈린 질의 수
    mismatch = Counter()                 # ordering → 상위 3 안 품목 불일치 건수
    picks = defaultdict(dict)            # query → evaluator → best
    for r in rows:
        q, ev, best = r["query"].strip(), r["evaluator"].strip(), r["best"].strip()
        lists = key["queries"].get(q, {}).get("lists") or {}
        if not lists or not best:            # 빈 답(아직 안 채운 칸)은 세지 않는다
            continue
        picks[q][ev] = best
        picked_items = re.findall(r"[가나다]\d", best)
        if len(lists) > 1 and picked_items:
            # 상품 번호로 답한 경우: 그 상품을 1위로 둔 정렬이 '승' (여러 개면 각각)
            contested[ev] += 1
            urls = {lists[t[0]]["urls"][int(t[1]) - 1] for t in picked_items
                    if t[0] in lists and int(t[1]) <= len(lists[t[0]]["urls"])}
            for v in lists.values():
                if v["urls"] and v["urls"][0] in urls:
                    for how in v["orderings"]:
                        wins[ev][how] += 1
        elif len(lists) > 1:
            contested[ev] += 1
            names = [b for b in best.split(";") if b in lists]   # 공동 1위는 나눠서 (합이 1)
            for b in names:
                for how in lists[b]["orderings"]:
                    wins[ev][how] += 1 / len(names)
            if best == "같음":
                wins[ev]["같음"] += 1
        for tok in filter(None, (t.strip() for t in (r.get("mismatch") or "").replace(",", ";").split(";"))):
            if tok in ("없음", "-"):
                continue
            name, idx = tok[0], tok[1:]
            lst = lists.get(name)
            if lst and idx.isdigit() and 1 <= int(idx) <= len(lst["urls"]):
                url = lst["urls"][int(idx) - 1]
                for how in ORDERINGS:   # 같은 상품이 다른 정렬의 상위 3에도 있으면 그 정렬에도 센다
                    if any(url in v["urls"] and how in v["orderings"] for v in lists.values()):
                        mismatch[(r["evaluator"].strip(), how)] += 1
    evs = sorted({r["evaluator"].strip() for r in rows})
    L = [f"# R4 블라인드 평가 결과 ({label})", "",
         f"- 평가지 생성 {key['run_at']} · 경로 {key['path']} · 평가자 {', '.join(evs)}",
         "- '승'은 그 정렬의 1위 목록이 선택된 횟수. 상위 3이 겹친 정렬은 함께 승을 받는다", "",
         "| 평가자 | 갈린 질의 | " + " | ".join(ORDER_LABEL[h] for h in ORDERINGS) + " | 같음 |",
         "|---|---|" + "---|" * (len(ORDERINGS) + 1)]
    for ev in evs:
        L.append(f"| {ev} | {contested[ev]} | " + " | ".join(f"{wins[ev][h]:g}" for h in ORDERINGS)
                 + f" | {wins[ev]['같음']:g} |")
    L += ["", "## 정렬별 품목 불일치 (상위 3 안, 평가자가 표시한 수)", "",
          "| 평가자 | " + " | ".join(ORDER_LABEL[h] for h in ORDERINGS) + " |", "|---|" + "---|" * len(ORDERINGS)]
    L += [f"| {ev} | " + " | ".join(str(mismatch[(ev, h)]) for h in ORDERINGS) + " |" for ev in evs]
    agree = [q for q, d in picks.items() if len(d) >= 2 and len(set(d.values())) == 1]
    L += ["", f"## 평가자 간 일치: {len(agree)}/{sum(1 for d in picks.values() if len(d) >= 2)} 질의", ""]
    L += ["| 질의 | " + " | ".join(evs) + " | 정렬 대응 |", "|---|" + "---|" * (len(evs) + 1)]
    for q, d in picks.items():
        lists = key["queries"][q]["lists"]
        mapping = " · ".join(f"{n}={'+'.join(ORDER_LABEL[h] for h in v['orderings'])}" for n, v in lists.items())
        L.append(f"| {q} | " + " | ".join(d.get(ev, "-") for ev in evs) + f" | {mapping} |")
    out = ROOT / "docs" / "claude" / f"r4_result_{label}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"저장: {out}")


def human_sheet(label: str, limit: int = 6):
    """사람용 짧은 평가지 (2026-11-12): 사람 평가자는 2~3명, 자주 묻지 않는다.
    AI 평가자(GPT·Gemini·Jev)끼리 답이 갈린 질의만, 가장 많이 갈린 순으로 limit 개까지 뽑는다.
    다 같은 답이면 그 질의는 묻지 않는다 — 사람 판정은 AI 가 엇갈린 곳에만 쓴다.
    → var/r4/sheet_<이름>_human.md (5분 안에 끝나는 분량)."""
    key = json.loads((OUT / f"key_{label}.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((OUT / f"answers_{label}.csv").open(encoding="utf-8")))
    ai = defaultdict(dict)
    for r in rows:
        if r["evaluator"] in ("GPT", "Gemini", "Jev") and r["best"]:
            ai[r["query"]][r["evaluator"]] = (r["best"], frozenset(filter(None, r["mismatch"].split(";"))))
    split = []
    for q, d in ai.items():
        if len(d) < 2 or not key["queries"].get(q, {}).get("lists"):
            continue
        # 1위 판정은 GPT·Gemini 만 견준다 (Jev 의 1위 판정은 확신이 낮아 — e1·e2), 불일치 상품은 셋 다
        bests = Counter(b for e, (b, _) in d.items() if e != "Jev")
        mism = {frozenset(m) for _, m in d.values()}
        score_ = 2 * (len(bests) > 1) + (len(mism) > 1)
        if score_:
            split.append((score_, q))
    split.sort(key=lambda x: -x[0])
    chosen = [q for _, q in split[:limit]]
    sheet = (OUT / f"sheet_{label}.md").read_text(encoding="utf-8").split("\n## ")
    head = ["# 짧은 평가 (" + label + f") — 질의 {len(chosen)}개, 5분 정도", "",
            "같은 검색 결과를 서로 다른 기준으로 고른 목록입니다. 질의마다 두 가지만 답해 주세요:",
            "1. **살 만한 상품**: 집에서 산다면 고를 상품 번호 1~2개 (예: 나2) — 없으면 '없음'",
            "2. **안 맞는 상품**: 요청과 맞지 않는 상품 번호 (예: 가1) — 없으면 '없음'", ""]
    body = ["## " + part.split("\n---")[0].rstrip() for part in sheet[1:]
            if part.split("\n", 1)[0].strip() in chosen]
    form = ["", "## 답안", "", "| 질의 | best | mismatch | reason |", "|---|---|---|---|"]
    form += [f"| {q} |  |  |  |" for q in chosen]
    form += ["", "best 칸에는 살 만한 상품 번호를 적어 주세요(예: 나2). 목록 이름만 적어도 됩니다."]
    out = OUT / f"sheet_{label}_human.md"
    out.write_text("\n".join(head) + "\n" + "\n\n".join(body) + "\n" + "\n".join(form) + "\n", encoding="utf-8")
    print(f"저장: {out}  (AI 답이 갈린 질의 {len(split)}개 중 {len(chosen)}개)")


if __name__ == "__main__":
    a = sys.argv
    if len(a) >= 3 and a[1] == "capture":
        path = a[a.index("--path") + 1] if "--path" in a else "auto"
        gap = float(a[a.index("--gap") + 1]) if "--gap" in a else 3.0
        capture(a[2], path, gap)
    elif len(a) >= 3 and a[1] == "jev":
        run_jev(a[2], a[a.index("--model") + 1] if "--model" in a else "jev-latest",
                float(a[a.index("--threshold") + 1]) if "--threshold" in a else 0.5,
                float(a[a.index("--gap") + 1]) if "--gap" in a else 1.0)
    elif len(a) >= 5 and a[1] == "import":
        import_answers(a[2], a[3], a[4])
    elif len(a) >= 3 and a[1] == "human":
        human_sheet(a[2], int(a[a.index("--limit") + 1]) if "--limit" in a else 6)
    elif len(a) >= 3 and a[1] == "score":
        score(a[2])
    else:
        print(__doc__)
        sys.exit(1)
