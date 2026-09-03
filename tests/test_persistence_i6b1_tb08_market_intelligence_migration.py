from __future__ import annotations

import ast
import hashlib
from pathlib import Path


SPECS = {
    "app/services/market_collector_v5.py": ("ensure_columns", "fetch_targets", "update_market_fields", "run_market_collector_v5", "384bce24c9a2fab1f6ed8ccb416ccf226faa32954955ace981e91e2c60951380"),
    "app/services/market_collector_v51.py": ("ensure_columns", "fetch_targets", "update_market_fields", "run_market_collector_v51", "98642d3ad57d0d8ab7ffdf36dcdfc76e168366f9132d5f44181601e21884bc42"),
    "app/services/market_identity_cluster_v53.py": ("ensure_columns", "fetch_targets", "update_market_cluster", "run_market_identity_cluster_v53", "6c992542b852ed6f6cecc980e726d8b96e3cf6b71d5b73a56c32942750cffe9f"),
    "app/services/market_representative_price_v54.py": ("ensure_columns", "fetch_rows", "update_price_fields", "run_market_representative_price_v54", "123b171dea4e3c4ec5649dcd0c8411810678a3e9d2143f16e7ae8eca0065e051"),
    "app/services/market_signal_propagation_v52.py": ("ensure_columns", "fetch_rows", "update_propagated_signal", "run_market_signal_propagation_v52", "17b66f2e7dccc586624056f19332bb583f2092771f634bb8d6f6a328e082a856"),
}


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _functions(path: str) -> dict[str, str]:
    source = _source(path)
    tree = ast.parse(source, filename=path)
    return {
        node.name: ast.get_source_segment(source, node) or ""
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_each_tb08_module_has_mixed_legacy_ddl_and_provider_runtime_imports() -> None:
    for path in SPECS:
        source = _source(path)
        assert source.count("from app.db.database import engine") == 1, path
        assert source.count("from app.db.engine_provider import get_engine") == 1, path
        assert source.count("with engine.begin() as conn:") == 1, path
        assert source.count("with get_engine().connect() as conn:") == 1, path
        assert source.count("with get_engine().begin() as conn:") == 1, path


def test_ddl_functions_are_byte_preserved_and_provider_free() -> None:
    for path, (ddl_name, _read, _write, _run, expected_sha) in SPECS.items():
        ddl = _functions(path)[ddl_name]
        assert hashlib.sha256(ddl.encode()).hexdigest() == expected_sha, path
        assert "engine.begin()" in ddl, path
        assert "get_engine()" not in ddl, path


def test_reads_use_provider_connect_and_writes_use_provider_begin() -> None:
    for path, (_ddl, read_name, write_name, _run, _sha) in SPECS.items():
        functions = _functions(path)
        read = functions[read_name]
        write = functions[write_name]
        assert "get_engine().connect()" in read and "engine.begin()" not in read, path
        assert "SELECT" in read.upper(), path
        assert "get_engine().begin()" in write, path
        assert "UPDATE" in write.upper(), path


def test_orchestrators_keep_direct_engine_nonownership() -> None:
    for path, (_ddl, _read, _write, run_name, _sha) in SPECS.items():
        run = _functions(path)[run_name]
        assert "engine.begin()" not in run, path
        assert "engine.connect()" not in run, path
        assert "get_engine()" not in run, path


def test_global_legacy_importer_count_remains_nineteen() -> None:
    importers = [path for path in Path("app").rglob("*.py") if "from app.db.database import engine" in path.read_text(encoding="utf-8")]
    assert len(importers) == 19
