"""Compatibility forwarder for canonical comparison snapshot services."""

from app.services.comparison.compare_snapshot_engine import (
    build_compare_snapshot,
)

__all__ = [
    "build_compare_snapshot",
]
