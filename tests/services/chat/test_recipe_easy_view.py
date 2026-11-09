"""Step 2 (2026-10-29): 쉽게 보기 (AI-edited, validated against the source) + general tips."""
from __future__ import annotations

import copy
import json
import sqlite3
import threading
from pathlib import Path

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat import easy_view
from app.services.recipe_chat.catalog import RecipeResolver
from app.services.recipe_chat.catalog_store import RecipeCatalog, StaticCatalog, load_json
from app.services.recipe_chat.easy_view import EasyViews, EasyViewStore, validate
from app.services.recipe_chat.recipes import packaged_467
from app.services.recipe_chat.service import RecipeChat

FIXTURE = Path(__file__).with_name("fixtures") / "recipe_catalog_sample.json"
EASY_DDL = """CREATE TABLE recipe_easy_view (
    recipe_id TEXT NOT NULL, content_hash TEXT NOT NULL, prompt_version TEXT NOT NULL,
    view_json TEXT NOT NULL, model TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipe_id, content_hash, prompt_version));"""

GOOD_467 = {
    "overview": {"feature": "베이컨과 양파를 볶아 생크림·우유 소스에 버무린 크림파스타예요.",
                 "flow": "베이컨과 양파를 볶아 크림소스를 끓이고, 삶은 면을 넣어 버무려요."},
    "steps": [
        {"title": "재료 손질", "text": "양파는 채 썰고, 베이컨은 먹기 좋은 크기로 썰어 주세요.", "from": [1],
         "done": None, "notes": []},
        {"title": "베이컨 볶기", "text": "냄비에 버터를 두르고 양파와 다진 마늘을 볶다가 베이컨을 넣어 함께 볶아 주세요.", "from": [2],
         "done": {"text": "양파가 투명해지면 다음으로 넘어가요.", "quote": "양파가 투명해질 정도로 볶아지면"},
         "notes": [{"kind": "caution", "text": "마늘은 타기 쉬우니 불을 너무 세게 하지 마세요."}]},
        {"title": "크림소스 만들기", "text": "볶은 양파에 우유, 생크림, 바질을 넣고 끓여 주세요. 끓어오르면 불을 약하게 줄이고 "
                                       "2분 정도 더 끓인 뒤 소금, 후춧가루로 간해 주세요.", "from": [3],
         "done": {"text": "끓어오른 뒤 약불에서 2분 정도 더 끓였으면 간을 해요.", "quote": "2분 정도 더 끓여"},
         "notes": [{"kind": "fix", "text": "소스가 분리되면 불을 끄고 저어 주세요."}]},
        {"title": "면 삶기", "text": "끓는 물에 소금과 식용유를 약간 넣고 파스타를 기호에 맞게 삶아 물기를 빼 주세요.", "from": [4],
         "done": {"text": "면을 하나 건져 씹어 보고 마음에 들면 건져요.", "quote": None}, "notes": []},
        {"title": "버무리기", "text": "프라이팬에 버터를 두르고 삶은 파스타를 볶다가 끓여 둔 소스를 넣어 버무린 뒤 접시에 담아 주세요.",
         "from": [5], "done": None, "notes": []},
    ],
    "tips": [{"title": "분리 막기", "text": "소스가 끓어오르면 바로 약불로 줄여야 분리되지 않아요."},
             {"title": "더 진하게", "text": "우유를 줄이고 생크림을 늘리면 더 진해져요."}],
}


class FakeLLM:
    def __init__(self, *drafts, gate: threading.Event | None = None):
        self.drafts = list(drafts)
        self.calls: list[str] = []
        self.gate = gate

    def __call__(self, text):
        self.calls.append(text)
        if self.gate is not None:
            assert self.gate.wait(5)
        draft = self.drafts[min(len(self.calls), len(self.drafts)) - 1]
        if isinstance(draft, Exception):
            raise draft
        return copy.deepcopy(draft)


@pytest.fixture
def easy_db(sqlite_db):
    raw = sqlite3.connect(sqlite_db.path)
    raw.executescript(EASY_DDL)
    raw.close()
    return sqlite_db


def make_svc(db, shopping, views, catalog=None):
    provider = StaticCatalog(catalog) if catalog is not None else None
    return ChatService(db, shopping=shopping,
                       recipe_chat=RecipeChat(statement_factory=str, catalog_provider=provider, easy_views=views))


def card_of(res):
    return next(b for b in res["blocks"] if b["type"] == "recipe_card")["data"]


# ── validation ─────────────────────────────────────────────────

def test_good_draft_passes_and_keeps_source_step_refs():
    view, problems = validate(copy.deepcopy(GOOD_467), packaged_467())
    assert problems == []
    assert [s["from"] for s in view["steps"]] == [[1], [2], [3], [4], [5]]
    assert view["prompt_version"] == easy_view.PROMPT_VERSION == "easy-v4" and len(view["tips"]) == 2
    assert view["overview"]["flow"].startswith("베이컨과 양파를 볶아")
    assert view["summary"] == view["overview"]["feature"]


def test_done_signals_are_marked_source_only_when_quoted_from_the_source():
    view, _ = validate(copy.deepcopy(GOOD_467), packaged_467())
    done = [s["done"] for s in view["steps"]]
    # the cue for step 2 is written at the start of source step 3 → still a source signal
    # a source signal is shown as the source words, not the model's paraphrase
    assert done[1] == {"text": "양파가 투명해질 정도로 볶아지면", "basis": "source", "quote": "양파가 투명해질 정도로 볶아지면"}
    assert done[2] == {"text": "2분 정도 더 끓여", "basis": "source", "quote": "2분 정도 더 끓여"}
    assert done[3] == {"text": "면을 하나 건져 씹어 보고 마음에 들면 건져요.", "basis": "general", "quote": None}
    assert done[0] is None and done[4] is None


@pytest.mark.parametrize("done,expected", [
    # a quote that is not in the source → downgraded to a general suggestion
    ({"text": "면이 부드러워지면 건져요.", "quote": "면이 부드러워지면"}, {"text": "면이 부드러워지면 건져요.", "basis": "general", "quote": None}),
    # general signals may not carry numbers (no invented times) → dropped
    ({"text": "면을 8분 삶으면 건져요.", "quote": None}, None),
    ({"text": "면을 2분 더 삶으면 건져요.", "quote": None}, None),
    # nor ingredients the source lacks
    ({"text": "파마산 치즈가 녹으면 건져요.", "quote": None}, None),
    # a signal is a state, not a new instruction (adding, seasoning, heat)
    ({"text": "물이 끓으면 면을 넣고 간을 맞춰요.", "quote": None}, None),
    # real DeepSeek draft (2026-10-29, deepseek-v4-flash): a 5-letter quote with a paraphrase that
    # dropped "2분 정도 더 끓여" → no longer a source signal; as a general one it is an instruction → dropped
    ({"text": "소스가 보글보글 끓어 오르면 불을 줄이고 간을 맞추면 돼요.", "quote": "끓어 오르면"}, None),
])
def test_bad_done_signals_are_downgraded_or_dropped_without_rejecting_the_view(done, expected):
    draft = copy.deepcopy(GOOD_467)
    draft["steps"][3]["done"] = done
    view, problems = validate(draft, packaged_467())
    assert problems == [] and view["steps"][3]["done"] == expected


def test_a_start_cue_is_moved_to_the_step_it_ends():
    # real DeepSeek draft (2026-10-29, easy-v3 run): "양파가 투명해질 정도로 볶아지면" opens source step 3,
    # so under step 3 it would tell the cook to move on before the sauce is made
    draft = copy.deepcopy(GOOD_467)
    draft["steps"][1]["done"] = {"text": "양파가 숨이 죽으면 다음으로 넘어가요.", "quote": None}
    draft["steps"][2]["done"] = {"text": "양파가 투명해지면", "quote": "양파가 투명해질 정도로 볶아지면"}
    view, problems = validate(draft, packaged_467())
    assert problems == []
    assert view["steps"][1]["done"] == {"text": "양파가 투명해질 정도로 볶아지면", "basis": "source",
                                        "quote": "양파가 투명해질 정도로 볶아지면"}
    assert view["steps"][2]["done"] is None


def test_a_start_cue_is_dropped_when_the_previous_step_already_has_a_source_signal():
    draft = copy.deepcopy(GOOD_467)
    draft["steps"][2]["done"] = {"text": "양파가 투명해지면", "quote": "양파가 투명해질 정도로 볶아지면"}
    view, _ = validate(draft, packaged_467())
    assert view["steps"][1]["done"]["quote"] == "양파가 투명해질 정도로 볶아지면"   # its own, kept
    assert view["steps"][2]["done"] is None


def test_notes_are_general_suggestions_without_numbers_amounts_or_new_ingredients():
    draft = copy.deepcopy(GOOD_467)
    draft["steps"][1]["notes"] = draft["steps"][2]["notes"] = []
    draft["steps"][3]["notes"] = [{"kind": "fix", "text": "면이 퍼지면 2분 덜 삶아 주세요."},
                                  {"kind": "caution", "text": "올리브유를 넣으면 면이 덜 붙어요."}]
    draft["steps"][4]["notes"] = [{"kind": "caution", "text": "소스를 넣은 뒤에는 오래 볶지 마세요."},
                                  {"kind": "other", "text": "아무 말이나 써요."}]
    view, problems = validate(draft, packaged_467())
    assert problems == []
    assert view["steps"][3]["notes"] == []
    assert view["steps"][4]["notes"] == [{"kind": "caution", "label": "주의", "text": "소스를 넣은 뒤에는 오래 볶지 마세요."}]
    good, _ = validate(copy.deepcopy(GOOD_467), packaged_467())
    assert good["steps"][1]["notes"][0]["label"] == "주의" and good["steps"][2]["notes"][0]["label"] == "잘 안 되면"


def test_notes_are_capped_for_the_whole_recipe():
    draft = copy.deepcopy(GOOD_467)
    for st in draft["steps"]:
        st["notes"] = [{"kind": "caution", "text": "불 세기를 살피며 천천히 해 주세요."}] * 2
    view, _ = validate(draft, packaged_467())
    assert sum(len(s["notes"]) for s in view["steps"]) == easy_view.MAX_NOTES
    assert [len(s["notes"]) for s in view["steps"]] == [1, 1, 0, 0, 0]


def test_adjacent_source_steps_may_be_merged_in_order():
    draft = copy.deepcopy(GOOD_467)
    merged = {**draft["steps"][1], "from": [2, 3], "text": draft["steps"][1]["text"] + " " + draft["steps"][2]["text"]}
    draft["steps"] = [draft["steps"][0], merged, draft["steps"][3], draft["steps"][4]]
    view, problems = validate(draft, packaged_467())
    assert problems == [] and [s["from"] for s in view["steps"]] == [[1], [2, 3], [4], [5]]


@pytest.mark.parametrize("arrange,expected", [
    # 2026-10-29 step 3: the source order is kept (v1 allowed "boil the water first")
    (lambda st: [st[3], st[0], st[1], st[2], st[4]], "원문 순서를 바꿈"),
    (lambda st: [st[0], {**st[1], "from": [2, 4]}, st[2], st[4]], "원문 순서를 바꿈"),
])
def test_reordering_source_steps_is_rejected(arrange, expected):
    draft = copy.deepcopy(GOOD_467)
    draft["steps"] = arrange(draft["steps"])
    view, problems = validate(draft, packaged_467())
    assert view is None and any(expected in p for p in problems), problems


def test_an_ingredient_moved_to_another_step_is_rejected():
    draft = copy.deepcopy(GOOD_467)
    # source step 1 only cuts onion and bacon; garlic is added in step 2
    draft["steps"][0]["text"] = "양파는 채 썰고, 베이컨은 먹기 좋은 크기로 썰고 다진마늘도 준비해 주세요."
    view, problems = validate(draft, packaged_467())
    assert view is None and any("1번째 step에 원문 해당 단계에 없는 재료: 다진마늘" in p for p in problems), problems


@pytest.mark.parametrize("mutate,expected", [
    (lambda d: d["steps"].pop(), "원문 단계가 빠짐: 5"),
    (lambda d: d["steps"][2].update(text=d["steps"][2]["text"] + " 파마산 치즈를 뿌려 주세요."), "원문에 없는 재료"),
    (lambda d: d["steps"][3].update(text="끓는 물에 소금을 넣고 파스타를 8분 삶아 주세요."), "원문에 없는 숫자: 8"),
    (lambda d: d["steps"][3].update(text=d["steps"][3]["text"] + " 면 삶은 물은 반 컵 남겨 주세요."), "원문에 없는 분량 표현"),
    (lambda d: d["steps"][2].update(text="볶은 양파에 우유와 생크림 200mL를 넣고 끓인 뒤 소금, 후춧가루로 간해 주세요. 바질도 넣어 주세요."),
     "생크림 분량이 원문"),
    (lambda d: d["steps"][0].update(**{"from": [9]}), "원문 단계 번호"),
    (lambda d: [s.update(text="잘 만들어 주세요.") for s in d["steps"]], "원문 내용이 너무 많이 빠짐"),
])
def test_drafts_that_add_or_drop_source_content_are_rejected(mutate, expected):
    draft = copy.deepcopy(GOOD_467)
    mutate(draft)
    view, problems = validate(draft, packaged_467())
    assert view is None
    assert any(expected in p for p in problems), problems


def test_cups_are_not_converted_in_the_easy_view():
    draft = copy.deepcopy(GOOD_467)
    draft["steps"][2]["text"] = "볶은 양파에 우유 1/2컵, 생크림 300mL, 바질을 넣고 끓이다가 약불에서 2분 더 끓여 소금, 후춧가루로 간해 주세요."
    view, problems = validate(draft, packaged_467())
    assert view is None and any("300" in p for p in problems)


def test_bad_tips_are_dropped_without_rejecting_the_view():
    draft = copy.deepcopy(GOOD_467)
    draft["tips"] = [{"title": "더 진하게", "text": "생크림을 100mL 더 넣으면 진해져요."},
                     {"title": "간 맞추기", "text": "소금은 마지막에 조금씩 넣어 주세요."},
                     {"title": "x" * 30, "text": "제목이 너무 길어요."}]
    view, problems = validate(draft, packaged_467())
    assert problems == [] and view["tips"] == [{"title": "간 맞추기", "text": "소금은 마지막에 조금씩 넣어 주세요."}]


def test_catalogue_vocabulary_catches_ingredients_the_source_lacks():
    catalog = RecipeCatalog([{"id": "x", "name": "x", "ingredients": [{"name": "페투치네"}, {"name": "채소"}]}])
    assert "페투치네" in catalog.ingredient_vocab() and "채소" not in catalog.ingredient_vocab()
    draft = copy.deepcopy(GOOD_467)
    draft["steps"][3]["text"] = "끓는 물에 소금과 식용유를 약간 넣고 페투치네를 기호에 맞게 삶아 물기를 빼 주세요."
    _view, problems = validate(draft, packaged_467(), catalog.ingredient_vocab())
    assert any("페투치네" in p for p in problems)


# ── generation, retry, cache ───────────────────────────────────

def test_retry_once_with_problems_then_store(easy_db):
    bad = copy.deepcopy(GOOD_467)
    bad["steps"].pop()
    llm = FakeLLM(bad, GOOD_467)
    views = EasyViews(llm, statement_factory=str, background=False, model="m")
    status, view = views.ensure(packaged_467(), easy_db)
    assert status == "ready" and len(llm.calls) == 2
    assert "이전 출력의 문제" in llm.calls[1] and "원문 단계가 빠짐: 5" in llm.calls[1]
    raw = sqlite3.connect(easy_db.path)
    rows = raw.execute("SELECT recipe_id, prompt_version, model, view_json FROM recipe_easy_view").fetchall()
    raw.close()
    assert [(r[0], r[1], r[2]) for r in rows] == [("EPIS:467", easy_view.PROMPT_VERSION, "m")]
    assert json.loads(rows[0][3]) == view
    # a new process reads the stored view without calling the LLM
    fresh = FakeLLM(GOOD_467)
    assert EasyViews(fresh, statement_factory=str, background=False).ensure(packaged_467(), easy_db) == ("ready", view)
    assert fresh.calls == []


def test_rejected_twice_is_not_shown_stored_or_retried_immediately(easy_db):
    bad = copy.deepcopy(GOOD_467)
    bad["steps"][0]["text"] = "생크림 200mL를 준비해 주세요."
    llm = FakeLLM(bad, bad, GOOD_467)
    views = EasyViews(llm, statement_factory=str, background=False)
    assert views.ensure(packaged_467(), easy_db) == ("unavailable", None)
    assert views.ensure(packaged_467(), easy_db) == ("unavailable", None)
    assert len(llm.calls) == 2
    assert sqlite3.connect(easy_db.path).execute("SELECT COUNT(*) FROM recipe_easy_view").fetchone()[0] == 0


def test_llm_errors_fall_back_to_the_source_card(easy_db, shopping):
    llm = FakeLLM(TimeoutError("slow"), RuntimeError("down"))
    svc = make_svc(easy_db, shopping, EasyViews(llm, statement_factory=str, background=False))
    card = card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert card["easy"] is None and card["easy_status"] == "unavailable"
    assert card["general_tips"]["kind"] == "curated" and card["steps"][0]["text"].startswith("양파는 채썰고")


def test_modes_off_and_cache_never_call_the_llm(easy_db):
    llm = FakeLLM(GOOD_467)
    assert EasyViews(llm, statement_factory=str, mode="off", background=False).ensure(packaged_467(), easy_db)[0] == "unavailable"
    assert EasyViews(llm, statement_factory=str, mode="cache", background=False).ensure(packaged_467(), easy_db)[0] == "unavailable"
    assert llm.calls == []


def test_missing_table_still_shows_the_view_from_memory(sqlite_db):
    views = EasyViews(FakeLLM(GOOD_467), statement_factory=str, background=False)
    assert views.ensure(packaged_467(), sqlite_db)[0] == "ready"      # no recipe_easy_view table: not stored
    assert views.cached(packaged_467(), sqlite_db) is not None


def test_from_env_needs_a_server_side_deepseek_key():
    assert easy_view.from_env({}).generator is None
    assert easy_view.from_env({"DEEPSEEK_API_KEY": "k", "DEEPSEEK_MODEL": "deepseek-chat",
                               "RECIPE_EASY_VIEW": "off"}).generator is None
    views = easy_view.from_env({"DEEPSEEK_API_KEY": "k", "DEEPSEEK_MODEL": "deepseek-chat"})
    assert views.generator is not None and views.mode == "on" and views.model == "deepseek-chat"


# ── chat integration ───────────────────────────────────────────

def test_card_has_easy_view_and_untouched_source(easy_db, shopping):
    svc = make_svc(easy_db, shopping, EasyViews(FakeLLM(GOOD_467), statement_factory=str, background=False))
    res = svc.handle(None, message="크림파스타 만드는 법")
    card = card_of(res)
    source = packaged_467()
    assert card["easy_status"] == "ready" and card["easy"]["steps"][2]["title"] == "크림소스 만들기"
    assert card["source"]["level"] == "source"                      # the source itself stays 원문
    assert [s["text"] for s in card["steps"]] == source.step_texts()  # source steps verbatim
    assert {i["name"]: i["amount"] for i in card["ingredients"]}["생크림"] == "1과1/2컵"
    # 2026-10-29 (user decision): labels without "원문 아님"; the card shows a single source line at the bottom
    assert card["general_tips"] == {"kind": "ai", "label": "일반 조리 제안 · AI", "items": GOOD_467["tips"]}
    assert card["easy_key"] == source.content_hash()
    assert shopping.calls == []
    # stock flow is unchanged by the easy view
    sid = res["session_id"]
    assert svc.handle(sid, message="생크림 100mL 있어요")["stage"] == "recipe_stock_saved"
    res = svc.handle(sid, message="아니, 200mL예요")
    text = json.dumps(res["blocks"], ensure_ascii=False)
    assert "100mL에서 **200mL**로 바꿨어요" in text and "원문 컵 용량이 없어 정확한 비교는 어려워요" in text
    assert shopping.calls == []


def test_catalogue_easy_view_reuses_source_step_photos(easy_db, shopping):
    catalog = load_json(FIXTURE)
    recipe = RecipeResolver(StaticCatalog(catalog)).get("fs-450")
    draft = {"summary": "", "tips": [],
             "steps": [{"title": "과정 정리", "text": t, "from": [n]} for n, t in enumerate(recipe.step_texts(), 1)]}
    svc = make_svc(easy_db, shopping, EasyViews(FakeLLM(draft), statement_factory=str, background=False), catalog)
    card = card_of(svc.handle(None, message="조개크림파스타 만드는 법"))
    assert card["easy"]["steps"][0]["image"] == card["steps"][0]["image"]
    assert card["general_tips"]["kind"] == "curated"                # AI gave no tips → curated tips


def test_background_generation_then_polling(easy_db, shopping):
    gate = threading.Event()
    views = EasyViews(FakeLLM(GOOD_467, gate=gate), statement_factory=str, background=True)
    svc = make_svc(easy_db, shopping, views)
    card = card_of(svc.handle(None, message="크림파스타 만드는 법"))
    assert card["easy"] is None and card["easy_status"] == "pending"
    assert svc.recipe_easy("EPIS:467", card["easy_key"])["status"] == "pending"
    gate.set()
    views._pool.shutdown(wait=True)
    polled = svc.recipe_easy("EPIS:467", card["easy_key"])
    assert polled["status"] == "ready" and polled["easy"]["steps"][0]["title"] == "재료 손질"
    assert polled["general_tips"]["kind"] == "ai"
    assert svc.recipe_easy("EPIS:467", "other-version") == {"status": "stale"}
    assert svc.recipe_easy("nope", None) == {"status": "unknown"}
    # the next card is ready at once
    assert card_of(svc.handle(None, message="크림파스타 만드는 법"))["easy_status"] == "ready"


def test_polling_endpoint_never_starts_a_job(easy_db, shopping):
    llm = FakeLLM(GOOD_467)
    svc = make_svc(easy_db, shopping, EasyViews(llm, statement_factory=str, background=False))
    # (response also carries hero_status / hero since the AI-image step)
    assert svc.recipe_easy("EPIS:467") == {"status": "unavailable", "hero_status": "unavailable", "hero": None}
    assert llm.calls == []


def test_curated_tips_without_llm_have_no_amounts(make_service):
    card = card_of(make_service().handle(None, message="크림파스타 만드는 법"))
    tips = card["general_tips"]
    assert tips["kind"] == "curated" and tips["label"] == "일반 조리 제안" and 1 <= len(tips["items"]) <= 3
    assert not any(ch.isdigit() for t in tips["items"] for ch in t["text"])
    assert card["easy"] is None and card["easy_status"] == "unavailable"


# ── alternatives ───────────────────────────────────────────────

def test_similar_recipes_rank_by_shared_ingredients():
    def rec(rid, name, ings, image=None):
        return {"id": rid, "name": name, "ingredients": [{"name": i} for i in ings], "steps": [{"text": "a"}], "image": image}
    catalog = RecipeCatalog([
        rec("b", "바나나크림파스타", ["바나나", "아보카도", "토마토", "저염베이컨", "마늘", "양파", "휘핑크림", "우유", "소금", "스파게티면"]),
        rec("d", "단호박크림파스타", ["단호박", "파스타", "소금", "다진 마늘", "버터", "베이컨", "양파", "우유"], "http://x/1.png"),
        rec("p", "표고크림파스타", ["표고버섯", "소금", "후춧가루", "스파게티", "버터", "우유", "생크림"]),
        rec("c", "조개크림파스타", ["스파게티", "소금", "버터", "양파", "마늘", "우유", "생크림", "조개"]),
    ])
    resolver = RecipeResolver(StaticCatalog(catalog))
    finding = resolver.find("크림파스타 만드는 법")
    assert finding.recipe.recipe_id == "EPIS:467"
    titles = [t for _r, t in finding.alternatives]
    assert titles[0] == "단호박크림파스타" and "바나나크림파스타" not in titles and len(titles) == 3


# ── pre-build script & HTTP route ──────────────────────────────

def test_build_script_dry_run_prints_and_does_not_store():
    from scripts import build_recipe_easy_views as build

    bad = copy.deepcopy(GOOD_467)
    bad["steps"].pop()
    lines: list[str] = []
    code = build.run(["EPIS:467"], None, 5, str(FIXTURE), None, apply=False,
                     generator=FakeLLM(GOOD_467), out=lines.append)
    assert code == 0 and lines[0] == "[통과] EPIS:467 크림소스파스타"
    assert lines[-1].endswith("(dry run — --apply 로 저장)")
    lines.clear()
    code = build.run(["EPIS:467", "nope"], None, 5, str(FIXTURE), None, apply=False,
                     generator=FakeLLM(bad, bad), out=lines.append)
    assert code == 1 and "[없음] nope" in lines and "[거부] EPIS:467 크림소스파스타" in lines


def test_easy_route(easy_db, shopping):
    from fastapi.testclient import TestClient

    import app.main as main
    from app.api import chat_routes

    svc = make_svc(easy_db, shopping, EasyViews(FakeLLM(GOOD_467), statement_factory=str, background=False))
    main.app.dependency_overrides[chat_routes.get_chat_service] = lambda: svc
    try:
        client = TestClient(main.app)
        assert client.get("/api/recipe/easy", params={"recipe_id": "EPIS:467"}).json()["status"] == "unavailable"
        key = card_of(client.post("/api/chat", json={"message": "크림파스타 만드는 법"}).json())["easy_key"]
        body = client.get("/api/recipe/easy", params={"recipe_id": "EPIS:467", "key": key}).json()
        assert body["status"] == "ready" and len(body["easy"]["steps"]) == 5
        assert client.get("/api/recipe/easy", params={"recipe_id": "x" * 65}).status_code == 422
    finally:
        main.app.dependency_overrides.pop(chat_routes.get_chat_service, None)


def test_card_shows_at_most_two_notes_even_for_views_stored_by_an_older_prompt():
    # easy-v3 allowed 4 notes (2 per step); a real DeepSeek view had a caution on 4 of 5 steps
    old = copy.deepcopy(GOOD_467)
    for st in old["steps"]:
        st["notes"] = [{"kind": "caution", "label": "주의", "text": "불 세기를 살피며 천천히 해 주세요."}] * 2
        st["done"] = None
    old["steps"] = [dict(st, no=k + 1) for k, st in enumerate(old["steps"])]
    card = packaged_467().card(easy=old)
    assert [len(s["notes"]) for s in card["easy"]["steps"]] == [1, 1, 0, 0, 0]


def test_step_notes_never_replace_the_cards_own_notes():
    # regression (2026-10-30, real DeepSeek easy-v4 view): the last step had a note, and the
    # trimming loop overwrote the card's ingredient notes with it → the page failed to render
    view = copy.deepcopy(GOOD_467)
    view["steps"] = [dict(st, no=k + 1, done=None, notes=[]) for k, st in enumerate(view["steps"])]
    view["steps"][-1]["notes"] = [{"kind": "fix", "label": "잘 안 되면", "text": "소스가 굳으면 약한 불에서 데워 주세요."}]
    card = packaged_467().card(easy=view, servings_target=1)
    assert all(isinstance(n, str) for n in card["notes"]) and len(card["notes"]) == 1
    assert card["easy"]["steps"][-1]["notes"][0]["kind"] == "fix"
