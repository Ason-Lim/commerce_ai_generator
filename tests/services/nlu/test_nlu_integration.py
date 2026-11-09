"""NLU moved into commerce: LLMClient behaviour, dictionary prompt, validation,
and proof that no external food-nlu folder is loaded."""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.nlu import FoodNLU, LLMClient, LLMConfigError, NLUResources, validate
from app.services.nlu import food_nlu as food_nlu_module

ROOT = Path(__file__).resolve().parents[3]
DEEPSEEK_ENV = {"LLM_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "sk-test", "DEEPSEEK_MODEL": "deepseek-chat",
                "DEEPSEEK_BASE_URL": "https://api.deepseek.com"}


class FakeOpenAI:
    def __init__(self, content):
        self.content = content
        self.init_kwargs = None
        self.create_kwargs = None

    def __call__(self, **kwargs):
        self.init_kwargs = kwargs
        return self

    @property
    def chat(self):
        return SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.create_kwargs = kwargs
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))])


def test_deepseek_call_contract_is_preserved():
    fake = FakeOpenAI('```json\n{"operation":"set","ingredient":"생크림","amount":"100","unit":"mL"}\n```')
    client = LLMClient("SYSTEM", env=DEEPSEEK_ENV, openai_factory=fake)
    out = client.chat_json("생크림 100mL 있어요")
    assert out == {"operation": "set", "ingredient": "생크림", "amount": "100", "unit": "mL"}
    assert fake.init_kwargs == {"api_key": "sk-test", "base_url": "https://api.deepseek.com",
                                "timeout": 30.0, "max_retries": 0}
    assert fake.create_kwargs == {
        "model": "deepseek-chat", "temperature": 0.0, "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": "SYSTEM"}, {"role": "user", "content": "생크림 100mL 있어요"}]}


@pytest.mark.parametrize("env,message", [
    ({**DEEPSEEK_ENV, "DEEPSEEK_API_KEY": ""}, "DEEPSEEK_API_KEY 미설정"),
    ({**DEEPSEEK_ENV, "DEEPSEEK_MODEL": ""}, "DEEPSEEK_MODEL 미설정"),
    ({**DEEPSEEK_ENV, "DEEPSEEK_BASE_URL": "https://evil.example.com"}, "공식 API 주소"),
])
def test_deepseek_settings_are_checked_before_any_call(env, message):
    fake = FakeOpenAI("{}")
    with pytest.raises(LLMConfigError, match=message):
        LLMClient("S", env=env, openai_factory=fake).chat_json("x")
    assert fake.init_kwargs is None


def test_empty_base_url_defaults_to_official_host():
    fake = FakeOpenAI('{"a": 1}')
    LLMClient("S", env={**DEEPSEEK_ENV, "DEEPSEEK_BASE_URL": ""}, openai_factory=fake).chat_json("x")
    assert fake.init_kwargs["base_url"] == "https://api.deepseek.com"


def test_provider_default_and_unknown_provider():
    assert LLMClient("S", env={}).provider == "ollama"
    with pytest.raises(LLMConfigError):
        LLMClient("S", env={"LLM_PROVIDER": "nope"}).chat_json("x")


def test_safe_json_rejects_non_json():
    with pytest.raises(ValueError):
        LLMClient._safe_json("설명만 있어요")


RES = NLUResources(
    actions=[{"code": "recipe", "name": "레시피", "desc": "조리법", "required": [], "optional": ["ingredient"]},
             {"code": "recommend_food", "name": "추천", "desc": "식품 추천", "required": [], "optional": []}],
    contexts=[{"code": "taste_refreshing", "category": "TASTE", "name": "시원", "desc": "상큼"}],
    slots=[{"name": "ingredient", "type": "text", "enum": [], "desc": "재료"}],
    entities={"ingredient": ["두부", "애호박"]},
)


def test_validate_rules_match_food_nlu():
    out = validate({"action_intent": "recipe", "context_intent": "bogus", "slots": {"ingredient": "두부", "x": 1},
                    "confidence": 0.9}, RES)
    assert out == {"action_intent": "recipe", "context_intent": None, "slots": {"ingredient": "두부"},
                   "confidence": pytest.approx(0.6), "_penalty": 0.3}
    out = validate({"action_intent": "unknown", "confidence": 0.3}, RES)
    assert out["confidence"] == 0.0 and out["_penalty"] == 0.4


def test_system_prompt_contains_dictionary():
    prompt = RES.build_system_prompt()
    assert "- recipe (레시피): 조리법  required=[] optional=['ingredient']" in prompt
    assert "- ingredient: 두부, 애호박" in prompt
    assert prompt.startswith("너는 한국 식품 쇼핑 도메인 NLU 엔진이다.")


def test_food_nlu_parse_and_failure_fallback():
    fake = FakeOpenAI('{"action_intent":"recipe","context_intent":null,"slots":{},"confidence":0.8}')
    nlu = FoodNLU(RES, LLMClient("S", env=DEEPSEEK_ENV, openai_factory=fake))
    assert nlu.parse("두부로 만들 수 있는 요리")["action_intent"] == "recipe"
    broken = FoodNLU(RES, LLMClient("S", env={**DEEPSEEK_ENV, "DEEPSEEK_API_KEY": ""}))
    out = broken.parse("x")
    assert out["action_intent"] is None and "_error" in out


def test_resources_from_connection_with_array_columns():
    rows = {
        "ACTION": [{"intent_code": "recipe", "name": "레시피", "description": "d",
                    "required_slots": "{}", "optional_slots": ["ingredient"]}],
        "CTX": [{"intent_code": "taste_refreshing", "category_code": "TASTE", "name": "n", "description": "d"}],
        "SLOT": [{"slot_name": "ingredient", "slot_type": "text", "enum_values": None, "description": "d"}],
        "ENT": [{"entity_type": "ingredient", "canonical_name": "두부"}],
    }

    class Conn:
        def execute(self, sql):
            key = ("ACTION" if "= 'ACTION'" in sql else "CTX" if "<> 'ACTION'" in sql
                   else "SLOT" if "slot_definition" in sql else "ENT")
            return SimpleNamespace(mappings=lambda: SimpleNamespace(all=lambda: rows[key]))

    res = NLUResources.from_connection(Conn(), statement_factory=str)
    assert res.actions[0]["required"] == [] and res.actions[0]["optional"] == ["ingredient"]
    assert res.slots[0]["enum"] == [] and res.entities == {"ingredient": ["두부"]}


def test_load_food_nlu_is_off_without_llm_or_dictionary():
    food_nlu_module.reset_cache()
    assert food_nlu_module.load_food_nlu(env={"LLM_PROVIDER": "none"}) is None
    assert food_nlu_module.load_food_nlu(env={**DEEPSEEK_ENV, "CHAT_NLU_ENABLED": "0"}) is None

    def no_engine():
        raise RuntimeError("canonical engine is not bound")

    assert food_nlu_module.load_food_nlu(no_engine, env=DEEPSEEK_ENV) is None
    food_nlu_module.reset_cache()


def test_recipe_stock_interpret_uses_internal_client(monkeypatch):
    from app.services.recipe_session import direct_stock_chat
    from app.services.recipe_session.sequence_467 import materials

    for k, v in DEEPSEEK_ENV.items():
        monkeypatch.setenv(k, v)
    before = dict(os.environ)
    fake = FakeOpenAI('{"operation":"set","ingredient":"생크림","amount":"100","unit":"mL"}')

    def factory(prompt):
        assert "생크림" in prompt
        return LLMClient(prompt, provider="deepseek", env=DEEPSEEK_ENV, openai_factory=fake)

    out = direct_stock_chat.interpret("생크림 100mL 남았어요", materials(), client_factory=factory)
    assert out["ingredient_id"] == "EPIS:467:5145" and out["amount"] == "100" and out["unit"] == "mL"
    assert dict(os.environ) == before  # no environment mutation
    assert "_commerce_recipe_food_nlu" not in sys.modules


SCANNED = ["app/services/nlu", "app/services/recipe_session", "app/services/recipe_chat",
           "app/services/chat", "app/api/chat_routes.py"]


def _python_files():
    for entry in SCANNED:
        path = ROOT / entry
        yield from ([path] if path.is_file() else sorted(path.rglob("*.py")))


def test_no_external_nlu_folder_or_sys_path_loading():
    offenders = []
    for path in _python_files():
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "/Users/" in node.value or "food-nlu/" in node.value or "food_nlu/" in node.value:
                    offenders.append((str(path), node.value[:60]))
            if isinstance(node, ast.Attribute) and node.attr in {"spec_from_file_location", "insert"}:
                src = ast.get_source_segment(text, node) or ""
                if "sys.path" in src or node.attr == "spec_from_file_location":
                    offenders.append((str(path), src))
            if isinstance(node, ast.Import) and any(a.name in {"nlu", "router", "naver_api", "coupang_api"} for a in node.names):
                offenders.append((str(path), "import external module"))
    assert offenders == []


def test_import_and_run_without_food_nlu_on_path(tmp_path):
    """Fresh interpreter, empty HOME, no food-nlu on sys.path: import and run a recipe turn."""
    import subprocess

    code = (
        "import sys\n"
        "from app.services.chat.service import ChatService\n"
        "from app.services.recipe_chat.service import RecipeChat\n"
        "import app.api.chat_routes, app.services.recipe_session.direct_stock_chat\n"
        "res = ChatService(None, shopping=lambda *a: {}, recipe_chat=RecipeChat()).handle(None, message='크림파스타 만드는 법')\n"
        "assert res['stage'] == 'recipe_guide', res\n"
        "bad = [m for m in sys.modules if m == 'nlu' or 'food_nlu' in m.replace('-', '_') and not m.startswith('app.')]\n"
        "assert not bad, bad\n"
        "assert not [p for p in sys.path if 'food' in p and 'nlu' in p]\n"
        "print('ok')\n"
    )
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp_path), "PYTHONPATH": str(ROOT)}
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    assert out.stdout.strip().endswith("ok")
