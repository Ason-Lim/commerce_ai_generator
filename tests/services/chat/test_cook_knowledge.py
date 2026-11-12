"""요리 경험 지식 (2026-11-12) — 사용자·블라인드 평가에서 나온 지적이 검사로 잡히는지."""
from app.services.recipe_chat import ai_recipe, cook_knowledge as K


def rec(ings, steps, tips=()):
    return {"ingredients": [{"name": n, "amount": "약간"} for n in ings], "steps": [{"text": s} for s in steps],
            "tips": list(tips)}


def test_gambas_needs_drying_shrimp():
    bad = rec(["새우", "마늘", "올리브유"], ["새우 껍질을 벗기고 소금으로 밑간해 주세요.", "올리브유를 두르고 마늘을 약불에 볶다가 새우를 넣어 볶아 주세요."])
    assert any("물기" in p for p in K.problems(bad, "감바스"))
    good = rec(["새우", "마늘", "올리브유"], ["새우 껍질을 벗기고 키친타월로 물기를 닦아 주세요.", "올리브유를 두르고 마늘을 약불에 볶다가 새우를 넣어 볶아 주세요."])
    assert K.problems(good, "감바스") == []


def test_oyster_soup_cooking_point_and_sesame_oil_is_not_frying():
    light = rec(["굴", "무", "참기름"], ["무를 넣고 끓여 주세요.", "굴을 넣고 살짝 데쳐 주세요.", "참기름을 두르고 불을 꺼 주세요."])
    assert any("살짝" in p for p in K.problems(light, "굴국밥"))
    ok = rec(["굴", "무", "참기름"], ["무를 넣고 끓여 주세요.", "굴을 넣고 가장자리가 오그라들 때까지 익혀 주세요.", "참기름을 두르고 불을 꺼 주세요."])
    assert K.problems(ok, "굴국밥") == []            # 참기름을 둘러도 '해산물 튀김'이 아니다


def test_sandwich_bread_before_meat_and_patty_doneness():
    wrong = rec(["떡갈비", "식빵"], ["팬에 떡갈비를 앞뒤로 구워 육즙이 맑게 나오면 꺼내 주세요.", "같은 팬에 식빵을 노릇하게 구워 주세요."])
    assert any("빵을 먼저" in p for p in K.problems(wrong, "떡갈비 샌드위치"))
    right = rec(["떡갈비", "식빵"], ["식빵을 팬에 노릇하게 구워 주세요.", "떡갈비를 구워 가운데를 눌러 맑은 육즙이 나오면 꺼내 주세요."])
    assert K.problems(right, "떡갈비 샌드위치") == []
    raw = rec(["떡갈비", "식빵"], ["식빵을 구워 주세요.", "떡갈비를 앞뒤로 구워 주세요."])
    assert any("속까지" in p for p in K.problems(raw, "떡갈비 샌드위치"))


def test_melted_ingredient_must_be_used_later():
    bad = rec(["화이트초콜릿", "마시멜로"], ["화이트초콜릿을 전자레인지에 녹여 주세요.", "마시멜로를 녹여 반죽에 섞어 주세요."])
    assert any("화이트초콜릿" in p for p in K.problems(bad, "두바이 쫀득쿠키"))
    good = rec(["화이트초콜릿", "마시멜로"], ["화이트초콜릿을 전자레인지에 녹여 주세요.", "녹인 화이트초콜릿을 반죽에 섞어 주세요."])
    assert K.problems(good, "두바이 쫀득쿠키") == []


def test_guidance_goes_into_the_generation_request():
    g = K.guidance("감바스")
    assert any("물기" in x for x in g) and any("약불" in x for x in g) and any("취향" in x for x in g)
    assert any("빵을 먼저" in x for x in K.guidance("떡갈비 샌드위치"))


def test_recipe_versions_and_claude_provider():
    assert ai_recipe.recipe_id("두쫀쿠").endswith("-v3") and ai_recipe.version_of(ai_recipe.legacy_id("두쫀쿠") + "-v2") == "ai-recipe-v2"
    a = ai_recipe.from_env({"ANTHROPIC_API_KEY": "k", "DEEPSEEK_API_KEY": "d", "DEEPSEEK_MODEL": "deepseek-flash"})
    assert a.model == "claude-sonnet-5-5" and a.generator is not None
    b = ai_recipe.from_env({"ANTHROPIC_API_KEY": "k", "DEEPSEEK_API_KEY": "d", "DEEPSEEK_MODEL": "deepseek-flash",
                            "RECIPE_AI_PROVIDER": "deepseek"})
    assert b.model == "deepseek-flash"
    assert ai_recipe.from_env({}).generator is None


def test_llm_client_calls_claude_without_temperature():
    from app.services.nlu.llm_client import LLMClient

    sent = {}

    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return {"model": "claude-sonnet-5-5", "content": [{"type": "thinking"}, {"type": "text", "text": '{"ok": 1}'}],
                    "usage": {"input_tokens": 10, "output_tokens": 5}}

    def post(url, json, timeout, headers):
        sent.update(json)
        return R()

    c = LLMClient("s", provider="anthropic", env={"ANTHROPIC_API_KEY": "k"}, http_post=post, model="claude-sonnet-5-5")
    assert c.chat_json("x", temperature=0.3) == {"ok": 1}
    assert "temperature" not in sent and sent["model"] == "claude-sonnet-5-5"
