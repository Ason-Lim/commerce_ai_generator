from __future__ import annotations

import ast
from pathlib import Path


MARKET_FILE = Path("app/services/market/collector.py")
PIPELINE_FILE = Path("app/services/recommendation_pipeline.py")


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _module_assignment_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _create_engine_assignments(tree: ast.Module) -> list[ast.Assign]:
    found: list[ast.Assign] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "create_engine"
        ):
            continue
        found.append(node)
    return found


def _function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")


def _attribute_call_lines(node: ast.AST, attr: str) -> list[int]:
    lines: list[int] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            if child.func.attr == attr:
                lines.append(child.lineno)
    return lines


def _engine_attribute_call_lines(node: ast.AST, attr: str) -> list[int]:
    lines: list[int] = []
    for child in ast.walk(node):
        if not (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == attr
        ):
            continue
        if isinstance(child.func.value, ast.Name) and child.func.value.id == "engine":
            lines.append(child.lineno)
    return lines


def _imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_market_retains_constructor_while_pipeline_constructor_is_removed() -> None:
    market_tree = _tree(MARKET_FILE)
    pipeline_tree = _tree(PIPELINE_FILE)

    market_names = _module_assignment_names(market_tree)
    pipeline_names = _module_assignment_names(pipeline_tree)

    market_constructors = _create_engine_assignments(market_tree)
    pipeline_constructors = _create_engine_assignments(pipeline_tree)

    assert "DB_URL" in market_names
    assert "engine" in market_names
    assert len(market_constructors) == 1

    assert "DB_URL" not in pipeline_names
    assert "engine" not in pipeline_names
    assert pipeline_constructors == []




def test_market_retains_database_url_fallback_chain_after_pipeline_removal() -> None:
    market_text = MARKET_FILE.read_text(encoding="utf-8")
    pipeline_text = PIPELINE_FILE.read_text(encoding="utf-8")

    required_tokens = (
        "COMMERCE_DB_URL",
        "FRUIT_DB_URL",
        "postgresql+psycopg2://mom@localhost:5432/dashboard_db",
    )

    for token in required_tokens:
        assert token in market_text
        assert token not in pipeline_text




def test_market_collector_owns_one_read_acquisition_without_local_transaction() -> None:
    tree = _tree(MARKET_FILE)
    fn = _function(tree, "fetch_naver_products_from_db")

    assert len(_engine_attribute_call_lines(fn, "connect")) == 1
    assert _engine_attribute_call_lines(fn, "begin") == []
    assert len(_attribute_call_lines(fn, "execute")) >= 1


def test_recommendation_pipeline_local_engine_has_no_observed_runtime_use() -> None:
    tree = _tree(PIPELINE_FILE)

    assert _engine_attribute_call_lines(tree, "connect") == []
    assert _engine_attribute_call_lines(tree, "begin") == []
    assert _engine_attribute_call_lines(tree, "execute") == []


def test_import_time_constructor_distinction_remains_for_market_only() -> None:
    market_tree = _tree(MARKET_FILE)
    pipeline_tree = _tree(PIPELINE_FILE)

    market_constructors = _create_engine_assignments(market_tree)
    pipeline_constructors = _create_engine_assignments(pipeline_tree)

    assert len(market_constructors) == 1
    assert pipeline_constructors == []

    constructor_line = market_constructors[0].lineno
    connect_lines = _engine_attribute_call_lines(market_tree, "connect")
    begin_lines = _engine_attribute_call_lines(market_tree, "begin")

    assert constructor_line > 0
    assert all(line != constructor_line for line in connect_lines + begin_lines)




def test_current_embedded_caller_topology_is_repository_visible() -> None:
    app_main = Path("app/main.py").read_text(encoding="utf-8")
    generator_service = Path("app/services/generator_service.py").read_text(encoding="utf-8")

    pipeline_markers = (
        "recommendation_pipeline",
        "RecommendationPipeline",
    )
    market_markers = (
        "market.collector",
        "fetch_naver_products_from_db",
        "collect_market",
    )

    assert any(marker in app_main or marker in generator_service for marker in pipeline_markers)

    repository_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for root in (Path("app"), Path("tests"))
        for path in root.rglob("*.py")
    )
    assert any(marker in repository_text for marker in market_markers)


def test_no_concrete_standalone_runner_or_worker_entrypoint_is_declared_in_targets() -> None:
    for path in (MARKET_FILE, PIPELINE_FILE):
        tree = _tree(path)

        main_guards = []
        for node in tree.body:
            if not isinstance(node, ast.If):
                continue
            try:
                expression = ast.unparse(node.test)
            except Exception:
                expression = ""
            if "__name__" in expression and "__main__" in expression:
                main_guards.append(node.lineno)

        assert main_guards == []


def test_no_ddl_is_owned_by_target_modules() -> None:
    ddl_tokens = (
        "CREATE TABLE",
        "ALTER TABLE",
        "DROP TABLE",
        "CREATE INDEX",
        "metadata.create_all",
    )

    for path in (MARKET_FILE, PIPELINE_FILE):
        text = path.read_text(encoding="utf-8").upper()
        for token in ddl_tokens:
            assert token.upper() not in text


def test_market_external_acquisition_is_outside_database_read_helper() -> None:
    tree = _tree(MARKET_FILE)
    fn = _function(tree, "fetch_naver_products_from_db")

    imported = _imported_modules(tree)
    external_import_markers = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "playwright",
        "selenium",
    )

    fn_text = ast.unparse(fn)
    assert not any(marker in fn_text for marker in external_import_markers)

    # The module may contain marketplace/network acquisition elsewhere; this test
    # only fixes the DB-read helper boundary.
    assert isinstance(imported, set)


def test_existing_marketplace_and_recommendation_tests_remain_regression_anchors() -> None:
    candidates = [
        path
        for path in Path("tests").rglob("test_*.py")
        if path != Path(__file__)
    ]

    marketplace = [
        path
        for path in candidates
        if any(
            token in path.as_posix().lower()
            for token in ("market", "collector", "marketplace")
        )
    ]
    recommendation = [
        path
        for path in candidates
        if "recommend" in path.as_posix().lower()
    ]

    assert marketplace, "expected existing marketplace/collector regression tests"
    assert recommendation, "expected existing recommendation regression tests"
