from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Boundary:
    ddl: str
    reads: tuple[str, ...]
    writes: tuple[str, ...]
    orchestrator: str

TB08 = {
    "app/services/market_collector_v5.py": Boundary("ensure_columns", ("fetch_targets",), ("update_market_fields",), "run_market_collector_v5"),
    "app/services/market_collector_v51.py": Boundary("ensure_columns", ("fetch_targets",), ("update_market_fields",), "run_market_collector_v51"),
    "app/services/market_identity_cluster_v53.py": Boundary("ensure_columns", ("fetch_targets",), ("update_market_cluster",), "run_market_identity_cluster_v53"),
    "app/services/market_representative_price_v54.py": Boundary("ensure_columns", ("fetch_rows",), ("update_price_fields",), "run_market_representative_price_v54"),
    "app/services/market_signal_propagation_v52.py": Boundary("ensure_columns", ("fetch_rows",), ("update_propagated_signal",), "run_market_signal_propagation_v52"),
}
TB09 = {
    "app/services/product_attribute_engine_v8.py": Boundary("ensure_columns", ("fetch_targets",), ("update_attribute_v8",), "run_attribute_engine_v8"),
    "app/services/product_cluster_representative_v5.py": Boundary("ensure_representative_columns", ("fetch_cluster_rows",), ("reset_cluster_flags", "update_row_flags"), "run_cluster_representative_v5"),
    "app/services/product_family_variant_v6.py": Boundary("ensure_columns", ("fetch_targets",), ("update_family_variant",), "run_family_variant_v6"),
    "app/services/product_identity_cluster_v4.py": Boundary("ensure_cluster_columns", ("fetch_targets",), ("update_cluster_fields",), "run_identity_cluster_v4"),
    "app/services/product_quality_engine_v10_runner.py": Boundary("ensure_columns", ("fetch_targets",), ("update_scores",), "run_quality_v10_runner"),
    "app/services/product_quality_engine_v9.py": Boundary("ensure_columns", ("fetch_targets",), ("update_quality",), "run_quality_engine_v9"),
    "app/services/product_variety_engine_v7.py": Boundary("ensure_columns", ("fetch_targets",), ("update_variety_v7",), "run_variety_engine_v7"),
}
TB11 = {"app/services/naver_shopping_api_collector.py": Boundary("ensure_collector_v2_columns", (), ("insert_products",), "collect_naver_products")}
ALL = {**TB08, **TB09, **TB11}

def _source(path: str) -> str: return Path(path).read_text(encoding="utf-8")
def _functions(path: str):
    source = _source(path)
    tree = ast.parse(source, filename=path)
    return {node.name: ast.get_source_segment(source, node) or "" for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

def test_i6_registered_cohort_is_partitioned_five_seven_one():
    assert (len(TB08), len(TB09), len(TB11), len(ALL)) == (5, 7, 1, 13)

def test_all_members_have_detached_ddl_and_provider_runtime():
    for path, boundary in ALL.items():
        source = _source(path)
        functions = _functions(path)
        assert boundary.ddl not in functions, path
        assert {*boundary.reads, *boundary.writes, boundary.orchestrator} <= functions.keys(), path
        assert "from app.db.database import engine" not in source, path
        assert "from app.db.engine_provider import get_engine" in source, path

def test_read_write_and_orchestrator_ownership_remains_preserved():
    for path, boundary in ALL.items():
        functions = _functions(path)
        for name in boundary.reads:
            read = functions[name]
            assert "get_engine().connect()" in read and "SELECT" in read.upper() and "begin()" not in read, f"{path}:{name}"
        for name in boundary.writes:
            write = functions[name]
            assert "get_engine().begin()" in write, f"{path}:{name}"
            assert any(token in write.upper() for token in ("INSERT", "UPDATE", "DELETE")), f"{path}:{name}"
        orchestrator = functions[boundary.orchestrator]
        assert "engine.begin()" not in orchestrator and "engine.connect()" not in orchestrator and "get_engine()" not in orchestrator

def test_tb11_external_io_remains_explicit_but_unexecuted():
    functions = _functions(next(iter(TB11)))
    assert "requests.get(" in functions["call_naver_api"]
    assert "os.getenv(" in functions["get_naver_credentials"]

def test_i7_reservation_and_post_detachment_importer_count():
    register = Path("docs/architecture/registers/MA-2026-034-PHASE3-TRANSACTION-BOUNDARY-MIGRATION-SEAM-REGISTER.md").read_text(encoding="utf-8")
    assert "TB-15 and DDL-01 through DDL-14" in register
    importers = {path for path in Path("app").rglob("*.py") if "from app.db.database import engine" in path.read_text(encoding="utf-8")}
    assert len(importers) == 6
    assert {Path(path) for path in ALL}.isdisjoint(importers)
