from __future__ import annotations

import ast
import hashlib
from pathlib import Path


SPECS = {
    "app/services/product_attribute_engine_v8.py": ("ensure_columns", ("fetch_targets",), ("update_attribute_v8",), "run_attribute_engine_v8", "d6beeff6456f15cb85088a584d0c9dd55bde46e38849b5ba2ca9c164f3963634"),
    "app/services/product_cluster_representative_v5.py": ("ensure_representative_columns", ("fetch_cluster_rows",), ("reset_cluster_flags", "update_row_flags"), "run_cluster_representative_v5", "2f99ee43538bb2a63ae533bf791f845264eb6e60fd9e9376b005c2a06b81e0fb"),
    "app/services/product_family_variant_v6.py": ("ensure_columns", ("fetch_targets",), ("update_family_variant",), "run_family_variant_v6", "e4d643fcaaf14001fb952100729f271d3ae5639bff7d5c132f03d91b1bf39131"),
    "app/services/product_identity_cluster_v4.py": ("ensure_cluster_columns", ("fetch_targets",), ("update_cluster_fields",), "run_identity_cluster_v4", "ca663a90121354bdddebdb2fb4af28db2ca61e984939d627dc4ded40ccd85257"),
    "app/services/product_quality_engine_v10_runner.py": ("ensure_columns", ("fetch_targets",), ("update_scores",), "run_quality_v10_runner", "8245c92049802ad9161c7efea0ebc38054cefd1a041c409ed88ee63210fe40ea"),
    "app/services/product_quality_engine_v9.py": ("ensure_columns", ("fetch_targets",), ("update_quality",), "run_quality_engine_v9", "d1dc6a07aabce0d4dada6c749dd58feba5c0740bfd4243776d8de3afbbc34732"),
    "app/services/product_variety_engine_v7.py": ("ensure_columns", ("fetch_targets",), ("update_variety_v7",), "run_variety_engine_v7", "1b24c9352763e97b49c998f91cb4db266862134613b0106c6d0341b62b23e57a"),
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


def test_each_tb09_module_has_mixed_legacy_ddl_and_provider_runtime_imports() -> None:
    for path in SPECS:
        source = _source(path)
        assert source.count("from app.db.database import engine") == 1, path
        assert source.count("from app.db.engine_provider import get_engine") == 1, path


def test_ddl_functions_are_byte_preserved_and_provider_free() -> None:
    for path, (ddl_name, _reads, _writes, _run, expected_sha) in SPECS.items():
        ddl = _functions(path)[ddl_name]
        assert hashlib.sha256(ddl.encode()).hexdigest() == expected_sha, path
        assert "engine.begin()" in ddl, path
        assert "get_engine()" not in ddl, path


def test_reads_use_provider_connect_and_writes_use_provider_begin() -> None:
    for path, (_ddl, reads, writes, _run, _sha) in SPECS.items():
        functions = _functions(path)
        for read_name in reads:
            read = functions[read_name]
            assert "get_engine().connect()" in read, f"{path}:{read_name}"
            assert "begin()" not in read, f"{path}:{read_name}"
            assert "SELECT" in read.upper(), f"{path}:{read_name}"
        for write_name in writes:
            write = functions[write_name]
            assert "get_engine().begin()" in write, f"{path}:{write_name}"
            assert any(token in write.upper() for token in ("INSERT", "UPDATE", "DELETE")), f"{path}:{write_name}"


def test_orchestrators_keep_direct_engine_nonownership() -> None:
    for path, (_ddl, _reads, _writes, run_name, _sha) in SPECS.items():
        run = _functions(path)[run_name]
        assert "engine.begin()" not in run, path
        assert "engine.connect()" not in run, path
        assert "get_engine()" not in run, path


def test_global_legacy_importer_count_remains_nineteen() -> None:
    importers = [path for path in Path("app").rglob("*.py") if "from app.db.database import engine" in path.read_text(encoding="utf-8")]
    assert len(importers) == 19
