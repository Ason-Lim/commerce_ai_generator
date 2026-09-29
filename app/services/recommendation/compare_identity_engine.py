"""Compatibility forwarder for canonical comparison identity services."""

from app.services.comparison.compare_identity_engine import (
    build_compare_widget_key,
    get_compare_identity,
)

__all__ = [
    "build_compare_widget_key",
    "get_compare_identity",
]
