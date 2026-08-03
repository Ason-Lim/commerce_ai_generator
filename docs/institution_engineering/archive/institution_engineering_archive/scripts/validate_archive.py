\
#!/usr/bin/env python3
"""Validate IERA archive checksums and basic JSONL integrity."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "06_machine_readable" / "archive_manifest.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def validate_jsonl(path: Path) -> list[str]:
    errors = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}: line {line_no}: {exc}")
    return errors

def main() -> int:
    if not MANIFEST.exists():
        print("Manifest missing. Run build_archive.py first.")
        return 2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = []

    for item in manifest["files"]:
        path = ROOT / item["path"]
        if not path.exists():
            errors.append(f"Missing file: {item['path']}")
            continue
        actual = sha256_file(path)
        if actual != item["sha256"]:
            errors.append(f"Checksum mismatch: {item['path']}")

    for path in ROOT.rglob("*.jsonl"):
        errors.extend(validate_jsonl(path))

    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("VALIDATION PASSED")
    print(f"Checked {len(manifest['files'])} manifested files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
