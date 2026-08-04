# IPR-MA-2026-013-WINE

## Provider Registration Verification Report

| Item | Value |
|---|---|
| Project | Commerce AI Generator |
| Domain | 12_Wine |
| Authority | 99_Integration Verification Authority |
| Status | OFFICIAL |
| Result | PASS |
| Date | 2026-08-04 |

## Evidence

```text
Branch: main
HEAD: c946996
Provider order:
fruit
cheese
coffee
wine
venison
goat
beef
lamb
chicken
duck

PROVIDER_IDS_UNIQUE=True
WINE_REGISTERED_ONCE=True
```

Verified APIs:

- `get_food_provider()`
- `require_food_provider()`
- `resolve_food_provider()`
- `list_food_providers()`

Execution evidence:

```text
Wine tests: 141 passed
Registry/provider/resolver tests: 402 passed, 590 deselected
Compilation: compile_exit_code=0
```

After Wine Category and alias corrections:

```text
Wine tests: 144 passed
Wine registry/provider/resolver tests: 81 passed, 914 deselected
Compilation: compile_exit_code=0
```

## Decision

```text
PROVIDER REGISTRATION VERIFIED
```

**Issued by:** 99_Integration Verification Authority
