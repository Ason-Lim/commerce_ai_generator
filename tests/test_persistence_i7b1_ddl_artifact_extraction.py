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

BEGIN_SEAM = re.compile(r"^-- BEGIN (DDL-\d{2}) \| (\S+) \| ([A-Za-z_]\w*)$", re.M)

def test_artifact_identity_maps_exact_runtime_history():
    artifact = ARTIFACT.read_text(encoding="utf-8")
    mapped = BEGIN_SEAM.findall(artifact)
    assert mapped == [(e[0], e[1], e[2]) for e in ENTRIES]
    assert "STATIC ARTIFACT ONLY" in artifact
    assert "NO DATABASE OR DDL EXECUTION AUTHORITY" in artifact
    assert "STATEMENT COUNT: 124" in artifact

def test_artifact_contains_exact_statement_cardinality_per_seam():
    artifact = ARTIFACT.read_text(encoding="utf-8")
    starts = list(re.finditer(r"^-- BEGIN (DDL-\d{2}) \|", artifact, re.M))
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(artifact)
        section = artifact[match.start():end]
        expected = ENTRIES[index]
        assert match.group(1) == expected[0]
        assert len(re.findall(r"^-- BEGIN STATEMENT \d{3}$", section, re.M)) == expected[4]

def test_extracted_artifact_is_static_and_runtime_is_detached():
    artifact = ARTIFACT.read_text(encoding="utf-8")
    assert "engine.begin()" not in artifact
    assert "get_engine()" not in artifact
    assert "sqlalchemy" not in artifact.lower()
    assert "psycopg" not in artifact.lower()
    assert "http://" not in artifact.lower()
    assert "https://" not in artifact.lower()
    for seam, path, ddl_name, _caller, _count, _retain in ENTRIES:
        module = tree(path)
        assert ddl_name not in functions(module), seam
        assert not [n for n in ast.walk(module) if isinstance(n, ast.Call) and call_name(n) == ddl_name], seam

def test_existing_ddl06_artifact_remains_distinct():
    existing = "\n".join(line for line in DDL06_ARTIFACT.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("--"))
    assert len(DDL_PATTERN.findall(existing)) == 19
