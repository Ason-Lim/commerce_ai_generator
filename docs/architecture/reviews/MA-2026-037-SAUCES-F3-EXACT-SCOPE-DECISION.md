# MA-2026-037 Sauces F3 Exact-Scope Decision

## Status

`ESTABLISHED`

## Lifecycle and stage

- Lifecycle: `MA-2026-037`
- Subject: `SAUCES`
- Stage: `F3_PARSER_BEHAVIOR_CONTRACT`
- Canonical specification: `v1.1`
- Delivery order: `TEST_FIRST`

## Exact F3 test-first scope

F3 selects exactly one new test file:

`tests/services/food/knowledge/sauce/test_sauce_parser.py`

The contract shall contain exactly 16 test functions and 58 collected cases.
The cases shall cover:

1. public export and parse-result shape;
2. empty, whitespace-only, and noise-only inputs;
3. all nine Sauce family values;
4. supported texture evidence;
5. supported heat-level evidence;
6. supported intended-use evidence;
7. whitespace, case, punctuation, and lexical alias normalization;
8. formulated Japanese sauce inclusion;
9. raw, prepared-condiment, paste, powder, and dry-spice distinctions;
10. shio-kombu versus formulated shio-kombu sauce;
11. ponzu, tsuyu, and tare product-identity distinctions;
12. rayu, ume-paste, and nori-tsukudani boundaries;
13. standalone salt, vinegar, herb, and spice exclusions;
14. conflicting and unresolved evidence preservation;
15. explicit-text, normalized-alias, derived-rule, and unresolved provenance;
16. deterministic, side-effect-free results.

## Prospective production scope

After the expected-fail test contract is separately sealed, a later authority
may permit exactly two production changes:

- add `app/services/food/knowledge/sauce/parser.py`;
- modify `app/services/food/knowledge/sauce/__init__.py` only to export the F3 parser contract.

The established `attributes.py` and `parser_models.py` contracts shall be
consumed without modification.

## Required behavioral boundary

The parser must consume the canonical specification v1.1 Japanese-condiment
routing matrix. Cross-language aliases cannot override product identity, form,
or use evidence. Raw wasabi, mustard, horseradish, dry shichimi, shio kombu,
yuzu-kosho paste or powder, generic tare, broth identity, ume paste, and nori
tsukudani must not be silently promoted to Sauce. Distinct formulated sauce
identity may qualify when supported by input evidence.

Unknown and conflicting signals remain explicit. No classification may be
invented from a generic `paste`, `condiment`, ingredient, or preparation term.

## Exclusions

- F2 taxonomy reopening;
- rules, scoring, evaluation, and provider implementation (deferred to F4);
- resource files;
- shared or category registry changes;
- Alias Resolution Layer reopening;
- Compound Seasonings or Herb & Spice modification;
- Origin Processing;
- full-suite execution.

## Authority boundary

This decision does not authorize tests, test writes, production writes,
resource writes, implementation, integration, registry mutation, or full-suite
execution. The next step requires a separate one-use bounded test-contract
write authority.
