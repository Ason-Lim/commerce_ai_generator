from __future__ import annotations

from pathlib import Path

import pytest

from tools.verification.boundary import (
    ArchitectureBoundaryVerifier,
    is_subsequence,
    scan_python_file,
)
from tools.verification.boundary.cli import (
    main,
)
from tools.verification.core import (
    VerificationRequest,
    VerificationRunner,
    VerificationStatus,
)


def _write_domain(
    root: Path,
    *,
    parser_source: str | None = None,
    attributes_source: str | None = None,
    scoring_source: str | None = None,
    rules_source: str | None = None,
    provider_source: str | None = None,
) -> Path:
    domain = root / "domain"
    domain.mkdir()

    files = {
        "parser_models.py": (
            "class ParseResult:\n"
            "    pass\n"
        ),
        "parser.py": (
            parser_source
            or "def parse_product():\n"
            "    return None\n"
        ),
        "attributes.py": (
            attributes_source
            or "def build_attributes():\n"
            "    return {}\n"
        ),
        "scoring.py": (
            scoring_source
            or "def calculate_scores():\n"
            "    return {}\n"
        ),
        "rules.py": (
            rules_source
            or "def apply_rules():\n"
            "    return [], []\n"
        ),
        "provider.py": (
            provider_source
            or (
                "class FoodKnowledgeProvider:\n"
                "    pass\n"
                "\n"
                "class Provider("
                "FoodKnowledgeProvider):\n"
                "    def analyze(self):\n"
                "        parsed = "
                "parse_product()\n"
                "        attrs = "
                "build_cheese_attributes()\n"
                "        scores = "
                "calculate_cheese_scores()\n"
                "        reasons = "
                "apply_cheese_rules()\n"
                "        final = "
                "calculate_cheese_final_score("
                "scores)\n"
                "        return "
                "FoodKnowledgeResult()\n"
            )
        ),
    }

    for filename, source in files.items():
        (domain / filename).write_text(
            source,
            encoding="utf-8",
        )

    return domain


def test_ast_scanner_ignores_docstring_text(
    tmp_path: Path,
) -> None:
    path = tmp_path / "attributes.py"
    path.write_text(
        '"""FoodKnowledgeResult.attributes '
        'documentation."""\n'
        "\n"
        "def build_attributes():\n"
        "    return {}\n",
        encoding="utf-8",
    )

    result = scan_python_file(path)

    assert result.successful is True
    assert result.imports == ()
    assert all(
        call.leaf_name
        != "FoodKnowledgeResult"
        for call in result.calls
    )


def test_ast_scanner_collects_imports_calls_and_bases(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sample.py"
    path.write_text(
        "from package.module import Thing\n"
        "\n"
        "class Sample(BaseClass):\n"
        "    def run(self):\n"
        "        return Thing()\n",
        encoding="utf-8",
    )

    result = scan_python_file(path)

    assert result.successful is True
    assert result.imports[0].name == "Thing"
    assert result.calls[0].leaf_name == "Thing"
    assert result.classes[0].bases == (
        "BaseClass",
    )


def test_ast_scanner_reports_syntax_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "broken.py"
    path.write_text(
        "def broken(:\n",
        encoding="utf-8",
    )

    result = scan_python_file(path)

    assert result.successful is False
    assert "SyntaxError" in (
        result.syntax_error or ""
    )


def test_subsequence() -> None:
    assert is_subsequence(
        ("a", "c"),
        ("a", "b", "c"),
    )
    assert not is_subsequence(
        ("c", "a"),
        ("a", "b", "c"),
    )


def test_passing_domain(
    tmp_path: Path,
) -> None:
    domain = _write_domain(tmp_path)

    result = VerificationRunner().run(
        ArchitectureBoundaryVerifier(),
        VerificationRequest(
            target=str(domain)
        ),
    )

    assert result.status is (
        VerificationStatus.PASS
    )
    assert result.passed is True
    assert result.failed_checks == ()


def test_docstring_false_positive_is_not_reported(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        attributes_source=(
            '"""Converts data for '
            'FoodKnowledgeResult.attributes."""\n'
            "\n"
            "def build_attributes():\n"
            "    return {}\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    assert result.status is (
        VerificationStatus.PASS
    )


def test_parser_forbidden_scoring_import_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        parser_source=(
            "from package.scoring import "
            "calculate_score\n"
            "\n"
            "def parse_product():\n"
            "    return calculate_score()\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    assert result.status is (
        VerificationStatus.FAIL
    )
    assert any(
        check.status
        is VerificationStatus.FAIL
        and "imports" in check.check_id
        for check in result.checks
    )


def test_attribute_result_construction_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        attributes_source=(
            "def build_attributes():\n"
            "    return "
            "FoodKnowledgeResult()\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    assert result.status is (
        VerificationStatus.FAIL
    )
    assert any(
        "FoodKnowledgeResult"
        in detail
        for check in result.failed_checks
        for detail in check.details
    )


def test_scoring_parser_call_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        scoring_source=(
            "def calculate_scores():\n"
            "    return parser.parse_product()\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    assert result.status is (
        VerificationStatus.FAIL
    )


def test_rule_score_recalculation_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        rules_source=(
            "def apply_rules():\n"
            "    return "
            "calculate_cheese_scores()\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    assert result.status is (
        VerificationStatus.FAIL
    )


def test_external_dependency_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        parser_source=(
            "import requests\n"
            "\n"
            "def parse_product():\n"
            "    return None\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    assert result.status is (
        VerificationStatus.FAIL
    )
    assert any(
        "external_dependencies"
        in check.check_id
        and check.status
        is VerificationStatus.FAIL
        for check in result.checks
    )


def test_provider_wrong_order_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        provider_source=(
            "class FoodKnowledgeProvider:\n"
            "    pass\n"
            "\n"
            "class Provider("
            "FoodKnowledgeProvider):\n"
            "    def analyze(self):\n"
            "        scores = "
            "calculate_cheese_scores()\n"
            "        parsed = "
            "parse_product()\n"
            "        attrs = "
            "build_cheese_attributes()\n"
            "        reasons = "
            "apply_cheese_rules()\n"
            "        final = "
            "calculate_cheese_final_score("
            "scores)\n"
            "        return "
            "FoodKnowledgeResult()\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    flow = next(
        check
        for check in result.checks
        if check.check_id
        == "boundary.provider.flow"
    )

    assert flow.status is (
        VerificationStatus.FAIL
    )


def test_provider_missing_base_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(
        tmp_path,
        provider_source=(
            "class Provider:\n"
            "    def analyze(self):\n"
            "        parsed = "
            "parse_product()\n"
            "        attrs = "
            "build_cheese_attributes()\n"
            "        scores = "
            "calculate_cheese_scores()\n"
            "        reasons = "
            "apply_cheese_rules()\n"
            "        final = "
            "calculate_cheese_final_score("
            "scores)\n"
            "        return "
            "FoodKnowledgeResult()\n"
        ),
    )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    inheritance = next(
        check
        for check in result.checks
        if check.check_id
        == "boundary.provider.inheritance"
    )

    assert inheritance.status is (
        VerificationStatus.FAIL
    )


def test_missing_required_file_fails(
    tmp_path: Path,
) -> None:
    domain = _write_domain(tmp_path)
    (domain / "rules.py").unlink()

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(domain)
        )
    )

    required = next(
        check
        for check in result.checks
        if check.check_id
        == "boundary.domain.required_files"
    )

    assert required.status is (
        VerificationStatus.FAIL
    )
    assert "rules.py" in required.details


def test_missing_target_returns_error(
    tmp_path: Path,
) -> None:
    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(
                tmp_path / "missing"
            )
        )
    )

    assert result.status is (
        VerificationStatus.ERROR
    )


def test_cli_passes_for_valid_domain(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    domain = _write_domain(tmp_path)

    exit_code = main(
        [
            str(domain),
            "--domain-id",
            "test",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Status: PASS" in output


def test_real_cheese_domain_passes() -> None:
    target = Path(
        "app/services/food/knowledge/cheese"
    )

    if not target.exists():
        pytest.skip(
            "Cheese domain is not present."
        )

    result = ArchitectureBoundaryVerifier().verify(
        VerificationRequest(
            target=str(target),
            domain_id="10_Cheese",
            architecture_id=(
                "MA-2026-012"
            ),
        )
    )

    assert result.status is (
        VerificationStatus.PASS
    ), result.to_dict()
