# MA-2026-034 Phase 4 I4 Exact Scope Decision

## 1. Decision Identity

- Architecture: `MA-2026-034 Persistence Architecture`
- Phase: `Phase 4 — Controlled Consumer Migration`
- Wave: `I4 — Collector and Pipeline Constructor Migration`
- Routing predecessor:
  `ma-2026-034-phase4-post-i3-next-wave-routing-decision-established-v1.0`

## 2. Read-Only Evidence

The I4 exact-scope preflight established two registered constructor seams:

- `CMS-006` — `app/services/market/collector.py`
- `CMS-007` — `app/services/recommendation_pipeline.py`

Both modules currently:

- resolve database configuration at module import;
- call `create_engine(...)` at module import;
- expose module-level `DB_URL`;
- expose module-level `engine`.

Their runtime persistence behavior is not equivalent.

### CMS-006 — Market Collector

`market/collector.py` actively uses its module-level engine.

`fetch_naver_products_from_db()` performs:

- one `engine.connect()` acquisition;
- one SQL read;
- no `engine.begin()` transaction;
- no DDL in the target module.

The broader collector function also invokes external marketplace acquisition, so the
database read boundary and external acquisition boundary must remain distinguishable.

### CMS-007 — Recommendation Pipeline

`recommendation_pipeline.py` constructs a module-level engine but the preflight found:

- no `engine.connect()`;
- no `engine.begin()`;
- no SQL execution through that engine;
- no DDL in the target module.

The current constructor therefore has no observed runtime persistence use inside the
module.

The module is an embedded application dependency through `app.main` and
`generator_service.py`.

No concrete standalone runner or worker entrypoint was established by the preflight.

## 3. Governing Compatibility Requirements

`CMS-006` requires:

- embedded host injection or standalone worker lifecycle;
- mode-explicit runner evidence;
- preserved collection and transaction semantics;
- no import constructor at completion.

`CMS-007` requires:

- embedded host or standalone lifecycle dependency supply;
- pipeline mode evidence;
- preserved ranking, scoring, normalization, and response behavior;
- no raw config/factory/global engine at completion.

The current preflight does not provide enough evidence to authorize production
migration for either seam.

## 4. I4 Structure

I4 shall proceed:

`I4-A -> I4-B`

### I4-A

I4-A is characterization only.

Exact scope:

- exactly one new test file:
  `tests/test_persistence_collector_pipeline_constructor_characterization.py`

No production file may be modified.

The characterization shall establish at minimum:

1. both target modules currently own import-time constructor authority;
2. both expose the same accepted DB URL fallback chain;
3. market collector actively owns one bounded read acquisition through
   `fetch_naver_products_from_db()`;
4. recommendation pipeline's local engine has no observed connect/begin/execute use;
5. import and constructor ownership are distinct from actual network execution under
   the repository denial guard;
6. current embedded caller topology for both modules;
7. absence of a concrete standalone runner/worker entrypoint in current repository
   evidence;
8. absence of DDL in the two target modules;
9. market collector external acquisition remains outside the database-read function;
10. existing marketplace/recommendation behavior tests remain regression anchors.

### I4-B

I4-B is the eventual production migration wave.

Its exact production/test scope is deliberately not determined yet.

I4-B scope shall be decided only after I4-A completion evidence establishes whether:

- CMS-006 and CMS-007 can migrate together;
- CMS-007's unused constructor can be removed without replacement;
- CMS-006 requires embedded-provider injection, a standalone lifecycle binding, or a
  separately governed mode adapter;
- any caller/composition file must enter scope.

## 5. Why I4 Is Not Split by Target Yet

The two targets have different runtime persistence use, but both are constructor-owner
seams governed by the same Phase 4 routing wave.

Splitting immediately into separate implementation subwaves would prematurely choose
migration mechanisms before characterization.

One shared characterization artifact is sufficient to establish the contrast while
keeping all production files frozen.

## 6. Transaction-Wave Boundary

The Phase 3 transaction register also contains an `I4` label for API/UI read/write
boundaries.

That transaction-wave label is a separate Phase 3 migration-seam sequencing label and
does not redefine this Phase 4 constructor-migration routing decision.

No Phase 3 transaction-boundary implementation is authorized here.

## 7. I1-C2 Compatibility Bridge

I1-C2 remains deferred.

No compatibility bridge is required before I4-A because I4-A is test-only
characterization.

No bridge may be inferred for I4-B until concrete migration evidence requires it.

## 8. Non-Authorization

This decision does not authorize:

- I4-A test implementation until separate test-write authority is issued;
- I4-B production implementation;
- production writes;
- database mutation;
- database network execution;
- consumer migration;
- standalone worker lifecycle implementation;
- compatibility bridge implementation;
- Phase 4 completion.

## 9. Decision Result

Upon establishment:

- `phase_4_status=OPEN`
- `i1_status=COMPLETE`
- `i2_status=COMPLETE`
- `i3_status=COMPLETE`
- `i4_scope=I4A_THEN_I4B`
- `i4a_scope=EXACT_ONE_NEW_TEST_FILE`
- `i4a_test_file=tests/test_persistence_collector_pipeline_constructor_characterization.py`
- `i4a_production_write_required=NO`
- `i4a_implementation_authority=NOT_ISSUED`
- `i4b_scope_status=NOT_YET_DETERMINED`
- `i4b_implementation_authority=NOT_ISSUED`
- `i1c2_compatibility_bridge_status=DEFERRED_UNTIL_FURTHER_EVIDENCE`
- `production_write_authority=NONE`
- `test_write_authority=NONE`
- `database_mutation_authority=NONE`
- `database_network_execution_authority=NONE`
- `consumer_migration_authority=NONE`
- `phase_4_completion_authority=NONE`
- `next_action=AUTHOR_EXACT_I4A_TEST_WRITE_AUTHORITY`

No further authority is implied.
