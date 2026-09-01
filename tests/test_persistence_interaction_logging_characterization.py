from __future__ import annotations

import ast
from pathlib import Path


LOGGER_FILES = {
    "analytics": Path("app/services/analytics_logger.py"),
    "context": Path("app/services/context_logger.py"),
    "impression": Path("app/services/impression_logger.py"),
}


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _engine_begin_with_nodes(fn: ast.AST) -> list[ast.With]:
    matches: list[ast.With] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            expr = item.context_expr
            if (
                isinstance(expr, ast.Call)
                and isinstance(expr.func, ast.Attribute)
                and isinstance(expr.func.value, ast.Name)
                and expr.func.value.id == "engine"
                and expr.func.attr == "begin"
            ):
                matches.append(node)
    return matches



def _provider_begin_with_nodes(node: ast.AST) -> list[ast.With]:
    found: list[ast.With] = []

    for candidate in ast.walk(node):
        if not isinstance(candidate, ast.With):
            continue

        for item in candidate.items:
            expr = item.context_expr
            if not (
                isinstance(expr, ast.Call)
                and isinstance(expr.func, ast.Attribute)
                and expr.func.attr == "begin"
            ):
                continue

            owner = expr.func.value
            if (
                isinstance(owner, ast.Call)
                and isinstance(owner.func, ast.Name)
                and owner.func.id == "get_engine"
                and not owner.args
                and not owner.keywords
            ):
                found.append(candidate)

    return found

def _calls_named(fn: ast.AST, names: set[str]) -> list[ast.Call]:
    result: list[ast.Call] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        if isinstance(callee, ast.Name) and callee.id in names:
            result.append(node)
        elif isinstance(callee, ast.Attribute) and callee.attr in names:
            result.append(node)
    return result


def _keyword_name(call: ast.Call, name: str) -> str | None:
    for kw in call.keywords:
        if kw.arg != name:
            continue
        if isinstance(kw.value, ast.Name):
            return kw.value.id
        return ast.unparse(kw.value)
    return None


def test_exact_three_logger_modules_use_bounded_provider_without_local_engine_authority() -> None:
    assert set(LOGGER_FILES) == {"analytics", "context", "impression"}

    for path in LOGGER_FILES.values():
        text = path.read_text(encoding="utf-8")
        assert "create_engine(DB_URL)" not in text
        assert "from app.db.engine_provider import get_engine" in text
        assert "DB_URL" not in text


def test_logger_transaction_boundary_counts_are_two_one_one() -> None:
    expected = {"analytics": 2, "context": 1, "impression": 1}

    for name, path in LOGGER_FILES.items():
        tree = _tree(path)
        count = 0
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                count += len(_provider_begin_with_nodes(node))
        assert count == expected[name]


def test_tb02_log_search_is_analytics_transaction_owner() -> None:
    fn = _function(_tree(LOGGER_FILES["analytics"]), "log_search")
    assert len(_provider_begin_with_nodes(fn)) == 1


def test_tb03_log_product_click_is_analytics_transaction_owner() -> None:
    fn = _function(_tree(LOGGER_FILES["analytics"]), "log_product_click")
    assert len(_provider_begin_with_nodes(fn)) == 1


def test_tb04_context_and_impression_functions_own_local_transactions() -> None:
    context_tree = _tree(LOGGER_FILES["context"])
    impression_tree = _tree(LOGGER_FILES["impression"])

    context_owners = [
        node.name
        for node in context_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and _provider_begin_with_nodes(node)
    ]
    impression_owners = [
        node.name
        for node in impression_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and _provider_begin_with_nodes(node)
    ]

    assert len(context_owners) == 1
    assert len(impression_owners) == 1


def test_tb03_forwards_same_connection_to_preference_and_session_context() -> None:
    fn = _function(_tree(LOGGER_FILES["analytics"]), "log_product_click")

    calls = _calls_named(
        fn,
        {"update_user_preference", "update_session_context"},
    )
    by_name: dict[str, ast.Call] = {}
    for call in calls:
        callee = call.func
        name = callee.id if isinstance(callee, ast.Name) else callee.attr
        by_name[name] = call

    assert set(by_name) == {"update_user_preference", "update_session_context"}
    assert _keyword_name(by_name["update_user_preference"], "conn") == "conn"
    assert _keyword_name(by_name["update_session_context"], "conn") == "conn"


def test_tb03_connection_identity_is_owned_by_single_provider_begin_block() -> None:
    fn = _function(_tree(LOGGER_FILES["analytics"]), "log_product_click")
    begin_blocks = _provider_begin_with_nodes(fn)
    assert len(begin_blocks) == 1

    block = begin_blocks[0]
    optional_vars = block.items[0].optional_vars
    assert isinstance(optional_vars, ast.Name)
    assert optional_vars.id == "conn"


def test_borrowed_consumers_do_not_own_transaction_or_lifecycle_capability() -> None:
    analytics_tree = _tree(LOGGER_FILES["analytics"])
    targets = {"update_user_preference", "update_session_context"}
    modules: dict[str, str] = {}

    for node in analytics_tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        for alias in node.names:
            if alias.name in targets:
                modules[alias.name] = node.module

    assert set(modules) == targets

    def resolve_module(module: str) -> Path:
        base = Path(*module.split("."))
        file_candidate = base.with_suffix(".py")
        package_candidate = base / "__init__.py"
        candidates = [
            candidate
            for candidate in (file_candidate, package_candidate)
            if candidate.is_file()
        ]
        assert len(candidates) == 1
        return candidates[0]

    for module in modules.values():
        module_path = resolve_module(module)
        module_text = module_path.read_text(encoding="utf-8")
        assert ".begin()" not in module_text
        assert ".commit()" not in module_text
        assert ".rollback()" not in module_text
        assert ".dispose()" not in module_text

def test_characterization_introduces_no_compatibility_bridge_requirement() -> None:
    lifecycle = Path("app/db/lifecycle.py").read_text(encoding="utf-8")
    database = Path("app/db/database.py").read_text(encoding="utf-8")

    assert "get_engine" not in lifecycle
    assert "current_engine" not in lifecycle
    assert "engine_accessor" not in lifecycle
    assert "compatibility" not in database.lower()
