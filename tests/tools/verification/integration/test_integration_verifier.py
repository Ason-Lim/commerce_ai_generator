from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.verification.core import (
    VerificationRequest,
    VerificationRunner,
    VerificationStatus,
)
from tools.verification.integration import (
    CHEESE_PROFILE,
    IntegrationVerificationTool,
    get_integration_profile,
)
from tools.verification.integration.cli import (
    main,
)


def _run_phase(phase: str):
    verifier = IntegrationVerificationTool(
        profile=CHEESE_PROFILE,
        phase=phase,
    )

    return VerificationRunner().run(
        verifier,
        VerificationRequest(
            target=(
                "app/services/food/"
                "knowledge/cheese"
            ),
            domain_id="10_Cheese",
            architecture_id=(
                "MA-2026-012"
            ),
        ),
    )


def test_profile_lookup() -> None:
    profile = get_integration_profile(
        "cheese"
    )

    assert profile.category_id == "cheese"
    assert profile.provider_class_name == (
        "CheeseKnowledgeProvider"
    )


def test_unknown_profile_fails() -> None:
    with pytest.raises(
        KeyError,
        match="Unknown integration profile",
    ):
        get_integration_profile("unknown")


def test_registration_passes_without_fixed_order() -> None:
    result = _run_phase("registration")

    assert result.status is (
        VerificationStatus.PASS
    )

    registration_evidence = (
        result.evidence[0]
    )

    order = registration_evidence.metadata[
        "registry_order_snapshot"
    ]

    assert "cheese" in order
    assert len(order) == len(set(order))


def test_selection_passes() -> None:
    result = _run_phase("selection")

    assert result.status is (
        VerificationStatus.PASS
    )


def test_contract_passes() -> None:
    result = _run_phase("contract")

    assert result.status is (
        VerificationStatus.PASS
    )


def test_routing_passes() -> None:
    result = _run_phase("routing")

    assert result.status is (
        VerificationStatus.PASS
    )


def test_all_without_regression_checks() -> None:
    verifier = IntegrationVerificationTool(
        profile=CHEESE_PROFILE,
        phase="all",
    )

    assert verifier.phase == "all"


def test_cli_registration(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "cheese",
            "--phase",
            "registration",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Status: PASS" in output


def test_cli_json_output(
    tmp_path: Path,
) -> None:
    output = tmp_path / "registration.json"

    exit_code = main(
        [
            "cheese",
            "--phase",
            "registration",
            "--json",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0

    payload = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert payload["status"] == "PASS"
    assert payload["metadata"][
        "phase"
    ] == "registration"
