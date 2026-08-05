from __future__ import annotations

import ast
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]

TEA_DOMAIN_DIR = PROJECT_ROOT / "app/services/food/knowledge/tea"
TEA_DATA_DIR = PROJECT_ROOT / "app/services/food/registry_data/tea"
TEA_TEST_DIRS = (
    PROJECT_ROOT / "tests/services/food/knowledge/tea",
    TEA_DOMAIN_DIR / "tests",
)

SHARED_CATEGORY_REGISTRY = (
    PROJECT_ROOT / "app/services/food/category_registry.py"
)

EXPECTED_REGISTRY_TERMS = (
    "type",
    "origin",
    "variety",
    "processing",
    "oxidation",
    "flavor",
    "aroma",
    "caffeine",
    "grade",
    "registry",
)

FORBIDDEN_CALL_NAMES = {
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "httpx.get",
    "httpx.post",
    "urllib.request.urlopen",
    "socket.socket",
}

SCORING_TERMS = {
    "score",
    "scoring",
    "total_score",
    "quality_score",
    "trust_score",
    "final_score",
}

PROCESS_TERMS = {
    "commit",
    "rollback",
    "session.add",
    "session.execute",
    "db.add",
    "db.commit",
}


@dataclass
class Check:
    check_id: str
    title: str
    status: str
    evidence: list[str]
    violations: list[str]


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def list_files(directory: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes
    )


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr

    return None


def inspect_python_file(path: Path) -> dict[str, list[str]]:
    result = {
        "network_calls": [],
        "scoring_logic": [],
        "db_processes": [],
        "mutable_global_data": [],
        "syntax_errors": [],
    }

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        result["syntax_errors"].append(f"{relative(path)}: {exc}")
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name in FORBIDDEN_CALL_NAMES:
                result["network_calls"].append(
                    f"{relative(path)}:{getattr(node, 'lineno', '?')} {name}"
                )

            if name:
                lowered = name.lower()

                if any(term in lowered for term in PROCESS_TERMS):
                    result["db_processes"].append(
                        f"{relative(path)}:{getattr(node, 'lineno', '?')} {name}"
                    )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lowered_name = node.name.lower()
            if any(term in lowered_name for term in SCORING_TERMS):
                result["scoring_logic"].append(
                    f"{relative(path)}:{node.lineno} function={node.name}"
                )

        if isinstance(node, ast.Assign) and isinstance(
            getattr(node, "parent", None), ast.Module
        ):
            if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                result["mutable_global_data"].append(
                    f"{relative(path)}:{node.lineno}"
                )

    return result


def attach_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "parent", parent)


def inspect_python_file_with_parents(path: Path) -> dict[str, list[str]]:
    result = {
        "network_calls": [],
        "scoring_logic": [],
        "db_processes": [],
        "mutable_global_data": [],
        "syntax_errors": [],
    }

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        attach_parents(tree)
    except (OSError, UnicodeError, SyntaxError) as exc:
        result["syntax_errors"].append(f"{relative(path)}: {exc}")
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name in FORBIDDEN_CALL_NAMES:
                result["network_calls"].append(
                    f"{relative(path)}:{getattr(node, 'lineno', '?')} {name}"
                )

            if name:
                lowered = name.lower()
                if any(term in lowered for term in PROCESS_TERMS):
                    result["db_processes"].append(
                        f"{relative(path)}:{getattr(node, 'lineno', '?')} {name}"
                    )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lowered_name = node.name.lower()
            if any(term in lowered_name for term in SCORING_TERMS):
                result["scoring_logic"].append(
                    f"{relative(path)}:{node.lineno} function={node.name}"
                )

        if (
            isinstance(node, ast.Assign)
            and isinstance(getattr(node, "parent", None), ast.Module)
            and isinstance(node.value, (ast.List, ast.Dict, ast.Set))
        ):
            result["mutable_global_data"].append(
                f"{relative(path)}:{node.lineno}"
            )

    return result


def run_git(args: list[str]) -> tuple[int, str]:
    process = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    # Porcelain output begins with two status characters and one separator.
    # Do not strip leading whitespace because " M path" is meaningful.
    output = process.stdout.rstrip("\n")
    stderr = process.stderr.rstrip("\n")
    if stderr:
        output = f"{output}\n{stderr}" if output else stderr

    return process.returncode, output


def build_checks() -> list[Check]:
    checks: list[Check] = []

    tea_python_files = list_files(TEA_DOMAIN_DIR, (".py",))
    tea_data_files = list_files(
        TEA_DATA_DIR,
        (".yaml", ".yml", ".json", ".toml", ".csv"),
    )

    # 1. Registry file composition
    registry_python_files = [
        path
        for path in tea_python_files
        if any(term in path.stem.lower() for term in EXPECTED_REGISTRY_TERMS)
    ]

    evidence_1 = [
        f"Tea domain directory exists: {TEA_DOMAIN_DIR.exists()}",
        f"Tea Python files: {len(tea_python_files)}",
        *[relative(path) for path in tea_python_files],
        f"Registry-related Python files: {len(registry_python_files)}",
        *[relative(path) for path in registry_python_files],
    ]

    violations_1: list[str] = []
    if not TEA_DOMAIN_DIR.exists():
        violations_1.append(
            f"Tea domain directory is missing: {relative(TEA_DOMAIN_DIR)}"
        )

    checks.append(
        Check(
            check_id="RIV-1",
            title="Registry file composition",
            status=(
                "PASS"
                if TEA_DOMAIN_DIR.exists() and registry_python_files
                else "FAIL"
            ),
            evidence=evidence_1,
            violations=violations_1,
        )
    )

    # 2. Registry declarative data composition
    evidence_2 = [
        f"Tea registry data directory exists: {TEA_DATA_DIR.exists()}",
        f"Declarative data files: {len(tea_data_files)}",
        *[relative(path) for path in tea_data_files],
    ]

    violations_2: list[str] = []
    if not tea_data_files:
        violations_2.append(
            "No Tea YAML/JSON/TOML/CSV Registry data files were found."
        )

    checks.append(
        Check(
            check_id="RIV-2",
            title="Registry declarative data composition",
            status="PASS" if tea_data_files else "FAIL",
            evidence=evidence_2,
            violations=violations_2,
        )
    )

    # 3. Registry support layer
    support_files = [
        path
        for path in tea_python_files
        if (
            "support" in path.stem.lower()
            or "registry" in path.stem.lower()
            or "loader" in path.stem.lower()
        )
    ]

    evidence_3 = [
        f"Registry support files: {len(support_files)}",
        *[relative(path) for path in support_files],
    ]

    checks.append(
        Check(
            check_id="RIV-3",
            title="Registry support layer",
            status="PASS" if support_files else "FAIL",
            evidence=evidence_3,
            violations=(
                []
                if support_files
                else ["No identifiable Registry support or loader file found."]
            ),
        )
    )

    # 4. Registry contract compliance
    inspection_targets = sorted(set(registry_python_files + support_files))
    contract_evidence: list[str] = []
    contract_violations: list[str] = []

    for path in inspection_targets:
        result = inspect_python_file_with_parents(path)
        contract_evidence.append(f"AST inspected: {relative(path)}")

        for category, items in result.items():
            if items:
                contract_violations.extend(
                    f"{category}: {item}" for item in items
                )

    if not inspection_targets:
        status_4 = "PENDING"
        contract_violations.append(
            "No Registry implementation was available for AST inspection."
        )
    elif contract_violations:
        status_4 = "FAIL"
    else:
        status_4 = "PASS"

    checks.append(
        Check(
            check_id="RIV-4",
            title="Registry contract compliance",
            status=status_4,
            evidence=contract_evidence,
            violations=contract_violations,
        )
    )

    # 5. Change scope compliance
    git_code, git_output = run_git(
        ["status", "--short", "--untracked-files=all"]
    )

    scope_evidence = [
        f"git status exit code: {git_code}",
        git_output or "(working tree clean)",
    ]
    scope_violations: list[str] = []

    allowed_prefixes = (
        "app/services/food/knowledge/tea/",
        "app/services/food/registry_data/tea/",
        "tests/services/food/knowledge/tea/",
        "docs/verification/tea/",
        "docs/domains/tea",
    )

    if git_code == 0 and git_output:
        for line in git_output.splitlines():
            # Git porcelain v1 format: XY<space>PATH.
            if len(line) < 4:
                scope_violations.append(
                    f"Unrecognized git status entry: {line!r}"
                )
                continue

            changed_path = line[3:]

            if " -> " in changed_path:
                changed_path = changed_path.split(" -> ", maxsplit=1)[1]

            changed_path = changed_path.strip('"')

            if not changed_path.startswith(allowed_prefixes):
                scope_violations.append(
                    f"Outside Tea authorized scope: {changed_path}"
                )

            if changed_path == relative(SHARED_CATEGORY_REGISTRY):
                scope_violations.append(
                    "Shared Category Registry changed; review explicit "
                    "authorization and approved routing-only scope."
                )

    if git_code != 0:
        status_5 = "PENDING"
        scope_violations.append("Unable to obtain Git working-tree evidence.")
    elif scope_violations:
        status_5 = "FAIL"
    else:
        status_5 = "PASS"

    checks.append(
        Check(
            check_id="RIV-5",
            title="Registry implementation scope compliance",
            status=status_5,
            evidence=scope_evidence,
            violations=scope_violations,
        )
    )

    return checks


def main() -> int:
    if not PROJECT_ROOT.exists():
        print(f"Project root not found: {PROJECT_ROOT}", file=sys.stderr)
        return 2

    checks = build_checks()

    overall = "PASS"
    if any(check.status == "FAIL" for check in checks):
        overall = "FAIL"
    elif any(check.status == "PENDING" for check in checks):
        overall = "PENDING"

    payload: dict[str, Any] = {
        "document_id": "RIV-2026-013-TEA",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "overall_status": overall,
        "checks": [asdict(check) for check in checks],
    }

    output_dir = PROJECT_ROOT / "docs/verification/tea"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "tea_registry_evidence.json"
    text_path = output_dir / "tea_registry_evidence.txt"

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "RIV-2026-013-TEA",
        "Tea Registry Inventory Verification Evidence",
        f"Overall Status: {overall}",
        "",
    ]

    for check in checks:
        lines.extend(
            [
                f"[{check.check_id}] {check.title}",
                f"STATUS: {check.status}",
                "EVIDENCE:",
                *[f"  - {item}" for item in check.evidence],
                "VIOLATIONS:",
                *(
                    [f"  - {item}" for item in check.violations]
                    if check.violations
                    else ["  - None detected"]
                ),
                "",
            ]
        )

    text_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"JSON evidence: {relative(json_path)}")
    print(f"Text evidence: {relative(text_path)}")

    return 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
