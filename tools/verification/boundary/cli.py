from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from tools.verification.boundary.architecture_boundary_verifier import (
    ArchitectureBoundaryVerifier,
)
from tools.verification.core import (
    VerificationRequest,
    VerificationRunner,
    VerificationStatus,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify architecture boundaries "
            "for a domain source directory."
        )
    )

    parser.add_argument(
        "target",
        help="Domain source directory",
    )
    parser.add_argument(
        "--domain-id",
        default=None,
    )
    parser.add_argument(
        "--architecture-id",
        default=None,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional report output path",
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = build_parser().parse_args(
        argv
    )

    request = VerificationRequest(
        target=args.target,
        domain_id=args.domain_id,
        architecture_id=(
            args.architecture_id
        ),
    )

    result = VerificationRunner().run(
        ArchitectureBoundaryVerifier(),
        request,
    )

    if args.json_output:
        output = json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
    else:
        output = format_text_result(
            result
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

    if result.status in {
        VerificationStatus.PASS,
        VerificationStatus.WARNING,
    }:
        return 0

    return 1


def format_text_result(
    result,
) -> str:
    lines = [
        "Architecture Boundary Verification",
        "",
        f"Target: {result.target}",
        f"Status: {result.status.value}",
        f"Summary: {result.summary}",
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


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "build_parser",
    "format_text_result",
    "main",
]
