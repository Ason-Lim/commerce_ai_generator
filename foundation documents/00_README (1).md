# IERA-2026-001 — Institution Engineering Research Archive

## Purpose

This archive preserves the discussion, discoveries, hypotheses, decisions,
terminology evolution, and official-document provenance of the Institution
Engineering research process.

## Record Layers

1. **Raw Record**
   - Verbatim or source-faithful discussion records.
   - Must not be silently rewritten.
2. **Interpreted Research Record**
   - Structured discoveries, hypotheses, questions, decisions, and terminology.
   - May contain editorial normalization, but must link back to source records.
3. **Official Institutional Record**
   - Reviewed and approved documents.
   - Must be changed only through the applicable governance process.

## Important Limitation of This Initial Snapshot

This package was generated from the discussion context currently available
during archive creation. It does **not** claim to contain a complete verbatim
export of every earlier chat turn.

Accordingly:

- `full_conversation_partial.md` is a partial, source-faithful reconstruction
  limited to currently available messages and summaries.
- `discoveries.jsonl` contains normalized discovery records AD-175 through AD-260.
- Records derived from summaries are marked with `source_fidelity: "summary_derived"`.
- Records derived from directly available messages are marked with
  `source_fidelity: "direct_context"`.

A later official chat export can be ingested without overwriting this snapshot.

## Recommended Workflow

```text
Discussion
  -> Raw Snapshot
  -> Normalization
  -> Traceability Mapping
  -> Governance Review
  -> Official Documents
  -> Archive Validation
```

## Core Commands

```bash
python scripts/build_archive.py
python scripts/validate_archive.py
```

## Integrity

`06_machine_readable/archive_manifest.json` contains SHA-256 hashes for archive files.
Run the validation script after any intentional update.

## Archive ID

- Archive: IERA-2026-001
- Snapshot: SNAPSHOT-0001
- Scope: Architecture Discovery 175–260 and associated foundational discussion
