from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DDLBoundary:
    seam: str
    path: str
    ddl_function: str
    caller: str
    statement_count: int
    cohort: str
    reachability: str


DDL_BOUNDARIES = (
    DDLBoundary("DDL-01", "app/services/market_collector_v5.py", "ensure_columns", "run_market_collector_v5", 4, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-02", "app/services/market_collector_v51.py", "ensure_columns", "run_market_collector_v51", 5, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-03", "app/services/market_identity_cluster_v53.py", "ensure_columns", "run_market_identity_cluster_v53", 11, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-04", "app/services/market_representative_price_v54.py", "ensure_columns", "run_market_representative_price_v54", 14, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-05", "app/services/market_signal_propagation_v52.py", "ensure_columns", "run_market_signal_propagation_v52", 7, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-06", "app/services/naver_shopping_api_collector.py", "ensure_collector_v2_columns", "insert_products", 18, "I6_DDL_RETAINED", "NESTED_WRITE"),
    DDLBoundary("DDL-07", "app/services/product_attribute_engine_v8.py", "ensure_columns", "run_attribute_engine_v8", 4, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-08", "app/services/product_cluster_representative_v5.py", "ensure_representative_columns", "run_cluster_representative_v5", 6, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-09", "app/services/product_family_variant_v6.py", "ensure_columns", "run_family_variant_v6", 8, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-10", "app/services/product_identity_cluster_v4.py", "ensure_cluster_columns", "run_identity_cluster_v4", 4, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-11", "app/services/product_quality_engine_v9.py", "ensure_columns", "run_quality_engine_v9", 11, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-12", "app/services/product_quality_engine_v10_runner.py", "ensure_columns", "run_quality_v10_runner", 6, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-13", "app/services/product_variety_engine_v7.py", "ensure_columns", "run_variety_engine_v7", 11, "I6_DDL_RETAINED", "DIRECT_ORCHESTRATOR"),
    DDLBoundary("DDL-14", "app/services/recommendation_intelligence_v55.py", "ensure_columns", "run_recommendation_intelligence_v55", 15, "NON_I6_DDL", "DIRECT_ORCHESTRATOR"),
)

REGISTER_FAMILIES = {
    "DDL-01": "market collector v5",
    "DDL-02": "market collector v51",
    "DDL-03": "market identity cluster v53",
    "DDL-04": "market representative price v54",
    "DDL-05": "market signal propagation v52",
    "DDL-06": "Naver shopping collector",
    "DDL-07": "product attribute v8",
    "DDL-08": "product cluster representative v5",
    "DDL-09": "product family variant v6",
    "DDL-10": "product identity cluster v4",
    "DDL-11": "product quality v9",
    "DDL-12": "product quality v10 runner",
    "DDL-13": "product variety v7",
    "DDL-14": "recommendation intelligence v55",
}

NON_DDL_LEGACY_IMPORTERS = {
    Path("app/services/kurly_nmart_collector.py"),
    Path("app/services/kurly_nmart_collector_v3.py"),
    Path("app/services/kurly_review_playwright_collector.py"),
    Path("app/services/price_detail_enricher.py"),
    Path("app/ui/admin_dashboard.py"),
}

DDL_PATTERN = re.compile(r"\b(?:CREATE|ALTER|DROP)\s+(?:TABLE|INDEX)\b", re.IGNORECASE)
LEGACY_IMPORT_PATTERN = re.compile(
    r"^from app\.db\.database import engine(?:\s|$)", re.MULTILINE
)


def _source(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _tree(path: str | Path) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _functions(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    assert segment is not None
    return segment


def _ddl_statements(node: ast.AST) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant)
        and isinstance(child.value, str)
        and DDL_PATTERN.search(child.value)
    ]


def _normalize_sql(value: str) -> str:
    return " ".join(value.strip().rstrip(";").split()).upper()


def test_ddl01_through_ddl14_mapping_and_124_statement_inventory() -> None:
    register = _source(
        "docs/architecture/registers/MA-2026-034-PHASE3-TRANSACTION-BOUNDARY-MIGRATION-SEAM-REGISTER.md"
    )
    assert len(DDL_BOUNDARIES) == 14
    assert [boundary.seam for boundary in DDL_BOUNDARIES] == [
        f"DDL-{number:02d}" for number in range(1, 15)
    ]
    assert sum(boundary.statement_count for boundary in DDL_BOUNDARIES) == 124

    for boundary in DDL_BOUNDARIES:
        expected_register_row = (
            f"| {boundary.seam} | {REGISTER_FAMILIES[boundary.seam]} | "
            "runtime `begin` | migration artifact |"
        )
        assert expected_register_row in register, boundary.seam

        tree = _tree(boundary.path)
        functions = _functions(tree)
        assert boundary.ddl_function in functions, boundary.path
        assert boundary.caller in functions, boundary.path
        assert len(_ddl_statements(functions[boundary.ddl_function])) == boundary.statement_count


def test_zero_argument_legacy_ddl_acquisition_and_runtime_reachability() -> None:
    direct_count = 0
    nested_count = 0

    for boundary in DDL_BOUNDARIES:
        source = _source(boundary.path)
        tree = _tree(boundary.path)
        functions = _functions(tree)
        ddl = functions[boundary.ddl_function]

        assert not ddl.args.posonlyargs, boundary.path
        assert not ddl.args.args, boundary.path
        assert not ddl.args.kwonlyargs, boundary.path
        assert ddl.args.vararg is None, boundary.path
        assert ddl.args.kwarg is None, boundary.path

        ddl_source = _segment(source, ddl)
        assert ddl_source.count("engine.begin()") == 1, boundary.path
        assert "get_engine()" not in ddl_source, boundary.path

        callers = [
            name
            for name, function in functions.items()
            if name != boundary.ddl_function
            and any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == boundary.ddl_function
                for child in ast.walk(function)
            )
        ]
        assert callers == [boundary.caller], boundary.path

        if boundary.reachability == "DIRECT_ORCHESTRATOR":
            direct_count += 1
        else:
            assert boundary.reachability == "NESTED_WRITE"
            assert boundary.seam == "DDL-06"
            assert boundary.caller == "insert_products"
            nested_count += 1

    assert direct_count == 13
    assert nested_count == 1


def test_exact_legacy_importer_and_post_extraction_consequence() -> None:
    importers = {
        path
        for path in Path("app").rglob("*.py")
        if LEGACY_IMPORT_PATTERN.search(_source(path))
    }
    ddl_importers = {Path(boundary.path) for boundary in DDL_BOUNDARIES}
    assert len(importers) == 19
    assert len(ddl_importers) == 14
    assert ddl_importers <= importers
    assert importers - ddl_importers == NON_DDL_LEGACY_IMPORTERS

    removal_candidates: set[Path] = set()
    retained_ddl_importers: set[Path] = set()
    for boundary in DDL_BOUNDARIES:
        path = Path(boundary.path)
        tree = _tree(path)
        ddl = _functions(tree)[boundary.ddl_function]
        outside_engine_refs = sum(
            1
            for node in tree.body
            if node is not ddl
            for child in ast.walk(node)
            if isinstance(child, ast.Name) and child.id == "engine"
        )
        if boundary.cohort == "I6_DDL_RETAINED":
            assert outside_engine_refs == 0, boundary.path
            removal_candidates.add(path)
        else:
            assert boundary.seam == "DDL-14"
            assert outside_engine_refs == 2, boundary.path
            retained_ddl_importers.add(path)

    assert len(removal_candidates) == 13
    assert retained_ddl_importers == {
        Path("app/services/recommendation_intelligence_v55.py")
    }
    assert len(importers - removal_candidates) == 6


def test_existing_ddl06_artifact_covers_runtime_with_one_extra_index() -> None:
    source_path = Path("app/services/naver_shopping_api_collector.py")
    artifact_path = Path("sql/collector_v2_migration.sql")
    tree = _tree(source_path)
    ddl = _functions(tree)["ensure_collector_v2_columns"]
    runtime = {_normalize_sql(statement) for statement in _ddl_statements(ddl)}

    artifact_text = "\n".join(
        line
        for line in _source(artifact_path).splitlines()
        if not line.lstrip().startswith("--")
    )
    artifact = {
        _normalize_sql(statement)
        for statement in artifact_text.split(";")
        if DDL_PATTERN.search(statement)
    }
    covered = runtime & artifact
    missing = runtime - artifact
    extra = artifact - runtime

    assert len(runtime) == 18
    assert len(artifact) == 19
    assert len(covered) == 18
    assert not missing
    assert len(extra) == 1
    assert next(iter(extra)).startswith("CREATE INDEX ")


def test_characterization_is_static_and_migration_framework_is_absent() -> None:
    assert not Path("alembic.ini").exists()
    assert not Path("alembic").exists()
    assert not Path("migrations").exists()
    assert not Path("app/db/migrations").exists()

    this_source = _source(__file__)
    tree = ast.parse(this_source, filename=__file__)
    forbidden_import_roots = {"app", "sqlalchemy", "requests", "httpx"}
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported_roots.isdisjoint(forbidden_import_roots)
