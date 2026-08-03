\
#!/usr/bin/env python3
"""Build or refresh an IERA archive from JSONL source files.

This script intentionally avoids inventing missing transcript text.
Use `ingest_chat_export()` to add a real platform export later.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def iter_archive_files():
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and path.name != "archive_manifest.json":
            yield path

def build_manifest() -> dict:
    files = []
    for path in iter_archive_files():
        files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    return {
        "archive_id": "IERA-2026-001",
        "snapshot_id": "SNAPSHOT-0001",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_layers": [
            "raw_record",
            "interpreted_research_record",
            "official_institutional_record"
        ],
        "limitations": [
            "Initial snapshot is not a complete verbatim platform conversation export.",
            "Summary-derived records are explicitly labeled."
        ],
        "files": files
    }

def ingest_chat_export(export_path: Path) -> None:
    """Placeholder adapter for a future official chat export.

    Requirements:
    - preserve original text
    - assign stable turn IDs
    - retain timestamps and speaker roles
    - never overwrite existing snapshot records silently
    - record export checksum and ingestion provenance
    """
    raise NotImplementedError(
        "Implement an adapter after the official export format is known."
    )

def main() -> None:
    manifest = build_manifest()
    out = ROOT / "06_machine_readable" / "archive_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Files recorded: {len(manifest['files'])}")

if __name__ == "__main__":
    main()
