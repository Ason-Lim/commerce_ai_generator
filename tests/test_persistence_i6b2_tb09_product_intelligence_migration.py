from __future__ import annotations

import ast
from pathlib import Path

SPECS = {
    "app/services/product_attribute_engine_v8.py": ("ensure_columns", ("fetch_targets",), ("update_attribute_v8",), "run_attribute_engine_v8"),
    "app/services/product_cluster_representative_v5.py": ("ensure_representative_columns", ("fetch_cluster_rows",), ("reset_cluster_flags", "update_row_flags"), "run_cluster_representative_v5"),
    "app/services/product_family_variant_v6.py": ("ensure_columns", ("fetch_targets",), ("update_family_variant",), "run_family_variant_v6"),
    "app/services/product_identity_cluster_v4.py": ("ensure_cluster_columns", ("fetch_targets",), ("update_cluster_fields",), "run_identity_cluster_v4"),
    "app/services/product_quality_engine_v10_runner.py": ("ensure_columns", ("fetch_targets",), ("update_scores",), "run_quality_v10_runner"),
    "app/services/product_quality_engine_v9.py": ("ensure_columns", ("fetch_targets",), ("update_quality",), "run_quality_engine_v9"),
    "app/services/product_variety_engine_v7.py": ("ensure_columns", ("fetch_targets",), ("update_variety_v7",), "run_variety_engine_v7"),
}
def _source(path): return Path(path).read_text(encoding="utf-8")
def _functions(path):
    source = _source(path); tree = ast.parse(source, filename=path)
    return {node.name: ast.get_source_segment(source, node) or "" for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

def test_each_tb09_module_has_detached_ddl_and_provider_runtime_import():
    for path in SPECS:
        source = _source(path)
        assert source.count("from app.db.database import engine") == 0, path
        assert source.count("from app.db.engine_provider import get_engine") == 1, path

def test_ddl_functions_are_detached():
    for path, (ddl_name, _reads, _writes, _run) in SPECS.items(): assert ddl_name not in _functions(path), path

def test_reads_use_provider_connect_and_writes_use_provider_begin():
    for path, (_ddl, reads, writes, _run) in SPECS.items():
        functions = _functions(path)
        for name in reads:
            read = functions[name]; assert "get_engine().connect()" in read and "begin()" not in read and "SELECT" in read.upper(), f"{path}:{name}"
        for name in writes:
            write = functions[name]; assert "get_engine().begin()" in write and any(t in write.upper() for t in ("INSERT", "UPDATE", "DELETE")), f"{path}:{name}"

def test_orchestrators_keep_direct_engine_nonownership():
    for path, (_ddl, _reads, _writes, run_name) in SPECS.items():
        run = _functions(path)[run_name]
        assert "engine.begin()" not in run and "engine.connect()" not in run and "get_engine()" not in run, path

def test_global_legacy_importer_count_is_six():
    importers = [path for path in Path("app").rglob("*.py") if "from app.db.database import engine" in path.read_text(encoding="utf-8")]
    assert len(importers) == 6
