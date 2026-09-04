from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "sql/ma_2026_034_phase4_i7_ddl01_through_ddl14.sql"
DDL06_ARTIFACT = ROOT / "sql/collector_v2_migration.sql"
ENTRIES = (
    ("DDL-01", "app/services/market_collector_v5.py", "ensure_columns", "run_market_collector_v5", 4, False),
    ("DDL-02", "app/services/market_collector_v51.py", "ensure_columns", "run_market_collector_v51", 5, False),
    ("DDL-03", "app/services/market_identity_cluster_v53.py", "ensure_columns", "run_market_identity_cluster_v53", 11, False),
    ("DDL-04", "app/services/market_representative_price_v54.py", "ensure_columns", "run_market_representative_price_v54", 14, False),
    ("DDL-05", "app/services/market_signal_propagation_v52.py", "ensure_columns", "run_market_signal_propagation_v52", 7, False),
    ("DDL-06", "app/services/naver_shopping_api_collector.py", "ensure_collector_v2_columns", "insert_products", 18, False),
    ("DDL-07", "app/services/product_attribute_engine_v8.py", "ensure_columns", "run_attribute_engine_v8", 4, False),
    ("DDL-08", "app/services/product_cluster_representative_v5.py", "ensure_representative_columns", "run_cluster_representative_v5", 6, False),
    ("DDL-09", "app/services/product_family_variant_v6.py", "ensure_columns", "run_family_variant_v6", 8, False),
    ("DDL-10", "app/services/product_identity_cluster_v4.py", "ensure_cluster_columns", "run_identity_cluster_v4", 4, False),
    ("DDL-11", "app/services/product_quality_engine_v9.py", "ensure_columns", "run_quality_engine_v9", 11, False),
    ("DDL-12", "app/services/product_quality_engine_v10_runner.py", "ensure_columns", "run_quality_v10_runner", 6, False),
    ("DDL-13", "app/services/product_variety_engine_v7.py", "ensure_columns", "run_variety_engine_v7", 11, False),
    ("DDL-14", "app/services/recommendation_intelligence_v55.py", "ensure_columns", "run_recommendation_intelligence_v55", 15, True),
)
DDL_PATTERN = re.compile(r"\b(?:CREATE|ALTER|DROP)\s+(?:TABLE|INDEX)\b", re.I)
LEGACY_IMPORT = re.compile(r"^from app\.db\.database import engine(?:\s|$)", re.M)

def source(path): return (ROOT / path).read_text(encoding="utf-8")
def tree(path): return ast.parse(source(path), filename=path)
def functions(module): return {n.name: n for n in module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
def call_name(node):
    if isinstance(node.func, ast.Name): return node.func.id
    if isinstance(node.func, ast.Attribute): return node.func.attr
    return None

EXPECTED_RETAINED_IMPORTERS = {
    "app/services/kurly_nmart_collector.py",
    "app/services/kurly_nmart_collector_v3.py",
    "app/services/kurly_review_playwright_collector.py",
    "app/services/price_detail_enricher.py",
    "app/services/recommendation_intelligence_v55.py",
    "app/ui/admin_dashboard.py",
}

def test_exact_fourteen_function_and_call_detachments():
    detached_functions = detached_calls = 0
    for seam, path, ddl_name, caller_name, _count, _retain in ENTRIES:
        module = tree(path)
        funcs = functions(module)
        assert ddl_name not in funcs, seam
        detached_functions += 1
        assert caller_name in funcs, seam
        assert sum(1 for n in ast.walk(module) if isinstance(n, ast.Call) and call_name(n) == ddl_name) == 0, seam
        detached_calls += 1
    assert (detached_functions, detached_calls) == (14, 14)

def test_thirteen_import_removals_and_one_i7_retention():
    for seam, path, _ddl, _caller, _count, retain in ENTRIES:
        assert bool(LEGACY_IMPORT.search(source(path))) is retain, seam
    importers = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "app").rglob("*.py")
        if LEGACY_IMPORT.search(path.read_text(encoding="utf-8"))
    }
    assert importers == EXPECTED_RETAINED_IMPORTERS
    assert len(importers) == 6

def test_no_runtime_ddl_remains_in_exact_cohort():
    assert all(not DDL_PATTERN.search(source(entry[1])) for entry in ENTRIES)

def test_sql_artifacts_remain_static_and_separate():
    artifact = ARTIFACT.read_text(encoding="utf-8")
    assert len(re.findall(r"^-- BEGIN STATEMENT \d{3}$", artifact, re.M)) == 124
    existing = "\n".join(line for line in DDL06_ARTIFACT.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("--"))
    assert len(DDL_PATTERN.findall(existing)) == 19

def test_detachment_contract_uses_no_runtime_dependencies():
    this_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
    roots = {alias.name.split(".", 1)[0] for n in ast.walk(this_tree) if isinstance(n, ast.Import) for alias in n.names}
    roots |= {(n.module or "").split(".", 1)[0] for n in ast.walk(this_tree) if isinstance(n, ast.ImportFrom)}
    assert roots.isdisjoint({"app", "sqlalchemy", "requests", "httpx", "psycopg2"})
