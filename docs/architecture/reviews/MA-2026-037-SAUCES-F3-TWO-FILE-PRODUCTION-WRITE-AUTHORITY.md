# MA-2026-037 Sauces F3 Two-File Production Write Authority

## Status

`ESTABLISHED_ONE_USE_BOUNDED`

## Sealed prerequisite

The F3 parser behavior test contract is sealed as exactly one test file,
16 test functions, and 58 collected expected-fail cases. Its failure is caused
by the absence of the F3 parser production contract.

## Authorized production scope

This authority permits exactly two production-file changes:

1. add `app/services/food/knowledge/sauce/parser.py`;
2. modify `app/services/food/knowledge/sauce/__init__.py` only to export the F3 parser contract.

The implementation must satisfy the exact 58-case F3 test contract and consume
the established F1 parser-result model, F2 five-axis taxonomy, and canonical
specification v1.1 Japanese-condiment routing matrix.

## Required preservation

- `tests/services/food/knowledge/sauce/test_sauce_parser.py` remains unchanged.
- `app/services/food/knowledge/sauce/parser_models.py` remains unchanged.
- `app/services/food/knowledge/sauce/attributes.py` remains unchanged.
- Japanese product identity, form, and use evidence controls inclusion.
- Unknown and conflicting signals remain explicit.

## Exclusions

No test write, resource write, registry change, integration change, F2 reopening,
F4 rules/scoring/provider implementation, Compound Seasonings reopening,
Herb & Spice reopening, Origin Processing work, or full-suite execution is authorized.

## Consumption

This authority is consumed only by implementing the exact two production-file
scope, running the exact 58-case F3 contract, committing once, creating one
annotated tag, and atomically pushing the commit and tag.
