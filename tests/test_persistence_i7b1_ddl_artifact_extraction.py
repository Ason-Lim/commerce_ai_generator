from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "sql/ma_2026_034_phase4_i7_ddl01_through_ddl14.sql"
EXISTING_DDL06_ARTIFACT = ROOT / "sql/collector_v2_migration.sql"

ENTRIES = (
    ("DDL-01", "app/services/market_collector_v5.py", "ensure_columns", "run_market_collector_v5", 4, 0),
    ("DDL-02", "app/services/market_collector_v51.py", "ensure_columns", "run_market_collector_v51", 5, 0),
    ("DDL-03", "app/services/market_identity_cluster_v53.py", "ensure_columns", "run_market_identity_cluster_v53", 11, 0),
    ("DDL-04", "app/services/market_representative_price_v54.py", "ensure_columns", "run_market_representative_price_v54", 14, 0),
    ("DDL-05", "app/services/market_signal_propagation_v52.py", "ensure_columns", "run_market_signal_propagation_v52", 7, 0),
    ("DDL-06", "app/services/naver_shopping_api_collector.py", "ensure_collector_v2_columns", "insert_products", 18, 0),
    ("DDL-07", "app/services/product_attribute_engine_v8.py", "ensure_columns", "run_attribute_engine_v8", 4, 0),
    ("DDL-08", "app/services/product_cluster_representative_v5.py", "ensure_representative_columns", "run_cluster_representative_v5", 6, 0),
    ("DDL-09", "app/services/product_family_variant_v6.py", "ensure_columns", "run_family_variant_v6", 8, 0),
    ("DDL-10", "app/services/product_identity_cluster_v4.py", "ensure_cluster_columns", "run_identity_cluster_v4", 4, 0),
    ("DDL-11", "app/services/product_quality_engine_v9.py", "ensure_columns", "run_quality_engine_v9", 11, 0),
    ("DDL-12", "app/services/product_quality_engine_v10_runner.py", "ensure_columns", "run_quality_v10_runner", 6, 0),
    ("DDL-13", "app/services/product_variety_engine_v7.py", "ensure_columns", "run_variety_engine_v7", 11, 0),
    ("DDL-14", "app/services/recommendation_intelligence_v55.py", "ensure_columns", "run_recommendation_intelligence_v55", 15, 2),
)

DDL_PATTERN = re.compile(r"\b(?:CREATE|ALTER|DROP)\s+(?:TABLE|INDEX)\b", re.IGNORECASE)
BEGIN_SEAM = re.compile(r"^-- BEGIN (DDL-\d{2}) \| (\S+) \| ([A-Za-z_]\w*)$")
BEGIN_STATEMENT = re.compile(r"^-- BEGIN STATEMENT (\d{3})$")
END_STATEMENT = re.compile(r"^-- END STATEMENT (\d{3})$")


def _canonical_sql(value: str) -> str:
    return " ".join(textwrap.dedent(value).strip().rstrip(";").split())


def _module_details(raw_path: str, ddl_name: str, caller_name: str):
    source = (ROOT / raw_path).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=raw_path)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    ddl = functions[ddl_name]
    caller = functions[caller_name]
    constants = sorted(
        (
            child
            for child in ast.walk(ddl)
            if isinstance(child, ast.Constant)
            and isinstance(child.value, str)
            and DDL_PATTERN.search(child.value)
        ),
        key=lambda child: (child.lineno, child.col_offset),
    )
    statements = [_canonical_sql(child.value) for child in constants]
    return source, tree, ddl, caller, statements


def _artifact_sections():
    sections: dict[str, dict[str, object]] = {}
    current_seam: str | None = None
    current_number: str | None = None
    buffer: list[str] = []

    for line in ARTIFACT.read_text(encoding="utf-8").splitlines():
        seam_match = BEGIN_SEAM.fullmatch(line)
        if seam_match:
            current_seam = seam_match.group(1)
            sections[current_seam] = {
                "path": seam_match.group(2),
                "function": seam_match.group(3),
                "statements": [],
            }
            continue
        statement_match = BEGIN_STATEMENT.fullmatch(line)
        if statement_match:
            assert current_seam is not None
            assert current_number is None
            current_number = statement_match.group(1)
            buffer = []
            continue
        end_match = END_STATEMENT.fullmatch(line)
        if end_match:
            assert current_seam is not None
            assert current_number == end_match.group(1)
            statements = sections[current_seam]["statements"]
            assert isinstance(statements, list)
            statements.append(_canonical_sql("\n".join(buffer)))
            current_number = None
            buffer = []
            continue
        if current_number is not None:
            buffer.append(line)

    assert current_number is None
    return sections


def test_canonical_artifact_maps_all_fourteen_seams() -> None:
    sections = _artifact_sections()
    assert tuple(sections) == tuple(entry[0] for entry in ENTRIES)
    for seam, raw_path, ddl_name, _caller_name, expected_count, _outside in ENTRIES:
        section = sections[seam]
        assert section["path"] == raw_path
        assert section["function"] == ddl_name
        assert len(section["statements"]) == expected_count


def test_canonical_artifact_preserves_exact_124_statement_inventory() -> None:
    sections = _artifact_sections()
    total = 0
    for seam, raw_path, ddl_name, caller_name, expected_count, _outside in ENTRIES:
        _source, _tree, _ddl, _caller, source_statements = _module_details(
            raw_path, ddl_name, caller_name
        )
        artifact_statements = sections[seam]["statements"]
        assert artifact_statements == source_statements
        assert len(source_statements) == expected_count
        total += len(source_statements)
    assert total == 124


def test_runtime_ddl_boundaries_remain_attached_and_unchanged() -> None:
    direct = 0
    nested = 0
    for seam, raw_path, ddl_name, caller_name, _count, expected_outside in ENTRIES:
        source, tree, ddl, caller, _statements = _module_details(raw_path, ddl_name, caller_name)
        assert not ddl.args.posonlyargs
        assert not ddl.args.args
        assert not ddl.args.kwonlyargs
        assert ddl.args.vararg is None
        assert ddl.args.kwarg is None
        ddl_source = ast.get_source_segment(source, ddl) or ""
        assert ddl_source.count("engine.begin()") == 1
        assert "get_engine()" not in ddl_source
        call_count = sum(
            1
            for child in ast.walk(caller)
            if isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == ddl_name
        )
        assert call_count == 1
        outside_refs = sum(
            1
            for node in tree.body
            if node is not ddl
            for child in ast.walk(node)
            if isinstance(child, ast.Name) and child.id == "engine"
        )
        assert outside_refs == expected_outside
        if seam == "DDL-06":
            nested += 1
        else:
            direct += 1
    assert (direct, nested) == (13, 1)


def test_importer_consequence_remains_unconsumed() -> None:
    importers = []
    for path in sorted((ROOT / "app").rglob("*.py")):
        if re.search(
            r"^from app\.db\.database import engine(?:\s|$)",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            importers.append(path.relative_to(ROOT).as_posix())
    assert len(importers) == 19
    assert sum(1 for entry in ENTRIES if entry[5] == 0) == 13
    assert sum(1 for entry in ENTRIES if entry[5] != 0) == 1


def test_artifact_is_static_and_existing_ddl06_artifact_remains_separate() -> None:
    artifact_text = ARTIFACT.read_text(encoding="utf-8")
    assert "STATIC ARTIFACT ONLY" in artifact_text
    assert "NO DATABASE OR DDL EXECUTION AUTHORITY" in artifact_text
    assert "STATEMENT COUNT: 124" in artifact_text
    assert "engine.begin()" not in artifact_text
    assert "get_engine()" not in artifact_text
    assert "sqlalchemy" not in artifact_text.lower()
    assert "psycopg" not in artifact_text.lower()
    assert "http://" not in artifact_text.lower()
    assert "https://" not in artifact_text.lower()
    existing = "\n".join(
        line
        for line in EXISTING_DDL06_ARTIFACT.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    )
    assert len(re.findall(r"\b(?:CREATE|ALTER|DROP)\s+(?:TABLE|INDEX)\b", existing, re.I)) == 19
