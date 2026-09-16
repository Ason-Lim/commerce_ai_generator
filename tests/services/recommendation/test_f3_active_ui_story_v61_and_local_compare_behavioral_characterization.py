import ast
import copy
from pathlib import Path

from app.services.recommendation_story_engine_v61 import build_recommendation_story_v61


ROOT = Path(__file__).resolve().parents[3]
STREAMLIT = ROOT / "app/ui/streamlit_app.py"
RENDERER = ROOT / "app/ui/hero_renderer_v3.py"

STORY_FIELDS = {"story_title", "story_summary", "story_bullets", "caution_story"}
COMPARE_FIELDS = {"compare_summary", "compare_bullets"}


def _bound_names(node):
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
    return names


def _loaded_names(node):
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
    }


def _imported_names(node):
    if isinstance(node, ast.Import):
        return {alias.asname or alias.name.split(".")[0] for alias in node.names}
    if isinstance(node, ast.ImportFrom):
        return {alias.asname or alias.name for alias in node.names if alias.name != "*"}
    return set()


def _load_local_compare():
    tree = ast.parse(STREAMLIT.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assignments = {
        name: node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for name in _bound_names(node)
    }
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]

    selected_functions = {"build_user_friendly_hero_compare"}
    selected_assignments = set()
    required_names = set()

    changed = True
    while changed:
        changed = False
        for name in tuple(selected_functions):
            required_names.update(_loaded_names(functions[name]))
        for name in tuple(selected_assignments):
            required_names.update(_loaded_names(assignments[name]))
        for name in required_names:
            if name in functions and name not in selected_functions:
                selected_functions.add(name)
                changed = True
            if name in assignments and name not in selected_assignments:
                selected_assignments.add(name)
                changed = True

    selected_imports = [node for node in imports if _imported_names(node) & required_names]
    selected_nodes = [copy.deepcopy(node) for node in selected_imports]
    selected_nodes.extend(copy.deepcopy(assignments[name]) for name in sorted(selected_assignments))
    for name in sorted(selected_functions):
        node = copy.deepcopy(functions[name])
        node.decorator_list = []
        selected_nodes.append(node)

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"__builtins__": __builtins__}
    exec(compile(module, str(STREAMLIT), "exec"), namespace)
    return namespace["build_user_friendly_hero_compare"]


def _item(name="대표 상품", price=12000, score=0.91):
    return {
        "name": name,
        "title": name,
        "product_name": name,
        "price": price,
        "sale_price": price,
        "score": score,
        "final_score": score,
        "platform": "test-platform",
        "mall_name": "test-platform",
        "reason": "characterization reason",
    }


def _display(name="대표 상품", price=12000):
    return {
        "name": name,
        "title": name,
        "price": price,
        "price_text": f"{price:,}원",
        "platform": "test-platform",
    }


def test_story_v61_representative_output_capture():
    result = build_recommendation_story_v61(_item(), display=_display())
    assert isinstance(result, dict)
    assert STORY_FIELDS <= set(result)
    assert isinstance(result["story_bullets"], list)


def test_story_v61_sparse_input_output_capture():
    result = build_recommendation_story_v61({}, display={})
    assert isinstance(result, dict)
    assert STORY_FIELDS <= set(result)
    assert isinstance(result["story_bullets"], list)


def test_local_compare_representative_output_capture():
    build_compare = _load_local_compare()
    result = build_compare(_item(), [_item("비교 상품", 15000, 0.82)], _display(), {2: _display("비교 상품", 15000)})
    assert isinstance(result, dict)
    assert COMPARE_FIELDS <= set(result)
    assert isinstance(result["compare_bullets"], list)


def test_local_compare_empty_comparison_output_capture():
    build_compare = _load_local_compare()
    result = build_compare(_item(), [], _display(), [])
    assert isinstance(result, dict)
    assert COMPARE_FIELDS <= set(result)
    assert isinstance(result["compare_bullets"], list)


def test_active_builders_match_renderer_consumed_fields():
    source = RENDERER.read_text(encoding="utf-8")
    assert all(f'"{field}"' in source for field in STORY_FIELDS)
    assert all(f'"{field}"' in source for field in COMPARE_FIELDS)


def test_active_builders_preserve_distinct_owner_and_non_equivalence_boundary():
    build_compare = _load_local_compare()
    assert build_recommendation_story_v61.__module__ == "app.services.recommendation_story_engine_v61"
    assert build_compare.__name__ == "build_user_friendly_hero_compare"
    assert STORY_FIELDS.isdisjoint(COMPARE_FIELDS)
