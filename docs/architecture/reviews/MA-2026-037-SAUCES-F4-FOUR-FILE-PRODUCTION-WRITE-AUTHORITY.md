# MA-2026-037 Sauces F4 Four-File Production Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Sealed prerequisite

The F4 rules, scoring, and provider contract is sealed as exactly three test
files, 24 test functions, and 64 collected expected-fail cases. Its failure is
caused only by the absence of the F4 production contracts.

## Authorized production scope

This authority permits exactly four production-file changes:

1. add `app/services/food/knowledge/sauce/rules.py`;
2. add `app/services/food/knowledge/sauce/scoring.py`;
3. add `app/services/food/knowledge/sauce/provider.py`;
4. modify `app/services/food/knowledge/sauce/__init__.py` only to export F4 contracts.

The implementation must satisfy the exact 64-case F4 test contract. Scoring
uses fixed weights 0.30/0.15/0.15/0.25/0.15 without renormalization and rules
consume the canonical specification v1.1 Japanese-condiment routing matrix.

## Required preservation

- All three F4 test files remain unchanged.
- `app/services/food/knowledge/sauce/parser.py` remains unchanged.
- `app/services/food/knowledge/sauce/parser_models.py` remains unchanged.
- `app/services/food/knowledge/sauce/attributes.py` remains unchanged.
- Japanese product identity, form, and use evidence controls inclusion.
- Unknown and conflicting signals remain explicit.

## Exclusions

No test write, resource write, registry change, integration change, F1-F3 reopening,
Compound Seasonings reopening,
Herb & Spice reopening, Origin Processing work, or full-suite execution is authorized.

## Consumption

This authority is consumed only by implementing the exact four production-file
scope, running the exact 64-case F4 contract, committing once, creating one
annotated tag, and atomically pushing the commit and tag.
