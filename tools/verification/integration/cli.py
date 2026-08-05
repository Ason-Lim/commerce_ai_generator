from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tools.verification.core import (
    VerificationRequest,
    VerificationRunner,
    VerificationStatus,
)
from tools.verification.integration.integration_verifier import (
    SUPPORTED_PHASES,
    IntegrationVerificationTool,
)
from tools.verification.integration.profiles import (
    PROFILES,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run project-level integration "
            "verification."
        )
    )

    parser.add_argument(
        "profile",
        choices=sorted(PROFILES),
    )
    parser.add_argument(
        "--phase",
        choices=sorted(SUPPORTED_PHASES),
        default="all",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
    )
    parser.add_argument(
        "--output",
        default=None,
    )

    return parser


def format_text_result(result) -> str:
    lines = [
        "Project Integration Verification",
        "",
        f"Status: {result.status.value}",
        f"Summary: {result.summary}",
        f"Profile: "
        f"{result.metadata['profile_id']}",
        f"Phase: {result.metadata['phase']}",
        "",
        "Checks:",
    ]

    for check in result.checks:
        lines.append(
            f"- [{check.status.value}] "
            f"{check.title}: "
            f"{check.summary}"
        )

        for detail in check.details:
            lines.append(
                f"    {detail}"
            )

    return "\n".join(lines)


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = build_parser().parse_args(argv)

    verifier = (
        IntegrationVerificationTool
        .from_profile_id(
            args.profile,
            phase=args.phase,
        )
    )

    request = VerificationRequest(
        target=(
            "app/services/food/knowledge/"
            f"{args.profile}"
        ),
        domain_id=verifier.profile.domain_id,
        architecture_id=(
            verifier.profile.architecture_id
        ),
    )

    result = VerificationRunner().run(
        verifier,
        request,
    )

    output = (
        json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
        if args.json_output
        else format_text_result(result)
    )

    print(output)

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(
            output + "\n",
            encoding="utf-8",
        )

    return (
        0
        if result.status
        in {
            VerificationStatus.PASS,
            VerificationStatus.WARNING,
        }
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "build_parser",
    "format_text_result",
    "main",
]
