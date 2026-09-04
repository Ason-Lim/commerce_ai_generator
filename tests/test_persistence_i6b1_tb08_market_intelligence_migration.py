from __future__ import annotations

import ast
from pathlib import Path

SPECS = {
    "app/services/market_collector_v5.py": ("ensure_columns", "fetch_targets", "update_market_fields", "run_market_collector_v5"),
    "app/services/market_collector_v51.py": ("ensure_columns", "fetch_targets", "update_market_fields", "run_market_collector_v51"),
    "app/services/market_identity_cluster_v53.py": ("ensure_columns", "fetch_targets", "update_market_cluster", "run_market_identity_cluster_v53"),
    "app/services/market_representative_price_v54.py": ("ensure_columns", "fetch_rows", "update_price_fields", "run_market_representative_price_v54"),
    "app/services/market_signal_propagation_v52.py": ("ensure_columns", "fetch_rows", "update_propagated_signal", "run_market_signal_propagation_v52"),
}
def _source(path): return Path(path).read_text(encoding="utf-8")
def _functions(path):
    source = _source(path); tree = ast.parse(source, filename=path)
    return {node.name: ast.get_source_segment(source, node) or "" for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

def test_each_tb08_module_has_detached_ddl_and_provider_runtime_import():
    for path in SPECS:
        source = _source(path)
        assert source.count("from app.db.database import engine") == 0, path
        assert source.count("from app.db.engine_provider import get_engine") == 1, path
        assert source.count("with engine.begin() as conn:") == 0, path
        assert source.count("with get_engine().connect() as conn:") == 1, path
        assert source.count("with get_engine().begin() as conn:") == 1, path

def test_ddl_functions_are_detached():
    for path, (ddl_name, _read, _write, _run) in SPECS.items(): assert ddl_name not in _functions(path), path

def test_reads_use_provider_connect_and_writes_use_provider_begin():
    for path, (_ddl, read_name, write_name, _run) in SPECS.items():
        functions = _functions(path); read = functions[read_name]; write = functions[write_name]
        assert "get_engine().connect()" in read and "engine.begin()" not in read and "SELECT" in read.upper(), path
        assert "get_engine().begin()" in write and "UPDATE" in write.upper(), path

def test_orchestrators_keep_direct_engine_nonownership():
    for path, (_ddl, _read, _write, run_name) in SPECS.items():
        run = _functions(path)[run_name]
        assert "engine.begin()" not in run and "engine.connect()" not in run and "get_engine()" not in run, path

def test_global_legacy_importer_count_is_six():
    importers = [path for path in Path("app").rglob("*.py") if "from app.db.database import engine" in path.read_text(encoding="utf-8")]
    assert len(importers) == 6
