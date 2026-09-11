import ast
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

CANDIDATES = {
    "app/services/recommendation_engine.py",
    "app/services/ai_ranking_engine_v7.py",
}

PRESERVED = {
    "app/services/recommendation/score_engine.py",
    "app/services/recommendation/compare_engine.py",
    "app/services/recommendation_pipeline.py",
    "app/services/generator_compatibility.py",
    "app/services/recommendation/recommendation_score_v8.py",
    "app/services/recommendation_intelligence_v55.py",
}

FORBIDDEN_MODULES = {
    "app.services.recommendation_engine",
    "app.services.ai_ranking_engine_v7",
}

SELF = "tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py"


def _tracked_python_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", "app/**/*.py", "tests/**/*.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _forbidden_imports(path: str) -> list[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"), filename=path)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_MODULES:
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in FORBIDDEN_MODULES:
                found.append(module)
            for alias in node.names:
                combined = f"{module}.{alias.name}" if module else alias.name
                if combined in FORBIDDEN_MODULES:
                    found.append(combined)
    return found


def test_f2a_candidate_state_is_atomic() -> None:
    assert len(CANDIDATES) == 2
    present = {path for path in CANDIDATES if (ROOT / path).is_file()}
    assert present in (CANDIDATES, set()), (
        "F2-A1 candidates must be either both present before removal or both absent "
        f"after removal; observed present={sorted(present)}"
    )


def test_f2a_preserved_surfaces_remain_present() -> None:
    missing = sorted(path for path in PRESERVED if not (ROOT / path).is_file())
    assert not missing, f"preserved F2-A1 and deferred F2-A2 surfaces missing: {missing}"


def test_f2a_has_no_external_python_imports() -> None:
    violations: dict[str, list[str]] = {}
    for path in _tracked_python_files():
        if path in CANDIDATES or path == SELF:
            continue
        found = _forbidden_imports(path)
        if found:
            violations[path] = found
    assert not violations, f"external imports of F2-A1 removal candidates found: {violations}"


def test_f2a_has_no_external_textual_module_references() -> None:
    patterns = [
        re.compile(r"\bapp\.services\.recommendation_engine\b"),
        re.compile(r"\bapp\.services\.recommendation\.(?:score_engine|compare_engine)\b"),
        re.compile(r"\bapp\.services\.ai_ranking_engine_v7\b"),
        re.compile(r"\bfrom\s+app\.services\s+import\s+recommendation_engine\b"),
        re.compile(r"\bfrom\s+app\.services\.recommendation\s+import\s+(?:score_engine|compare_engine)\b"),
        re.compile(r"\bfrom\s+app\.services\s+import\s+ai_ranking_engine_v7\b"),
    ]
    violations: list[str] = []
    for path in _tracked_python_files():
        if path in CANDIDATES or path == SELF:
            continue
        text = (ROOT / path).read_text(encoding="utf-8")
        if any(pattern.search(text) for pattern in patterns):
            violations.append(path)
    assert not violations, f"external textual references to F2-A1 removal candidates found: {violations}"
