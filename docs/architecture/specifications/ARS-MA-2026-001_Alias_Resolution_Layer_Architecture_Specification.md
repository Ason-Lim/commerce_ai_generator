# 00_1 Master Architecture

# Architecture Specification

## ARS-MA-2026-001-ALIAS-RESOLUTION

**Title**

Alias Resolution Layer Architecture Specification

---

# Document Identity

| Item | Value |
| --- | --- |
| Document ID | ARS-MA-2026-001-ALIAS-RESOLUTION |
| Authority | 00_1 Master Architecture |
| Project | Commerce AI Generator |
| Lifecycle | Sprint 4 |
| Governing Authorization | ADA-MA-2026-022-SPRINT4 |
| Sprint 4 Authorization Commit | a8029a4 |
| Preceding Sprint Handoff | DHN-MA-2026-020-SPRINT3 |
| Sprint 3 Handoff Commit | f4edea3 |
| Governing Sprint 3 Runtime Baseline | 6abc8fb |
| Architecture Scope | Shared Food Knowledge Alias Resolution |
| Status | ARCHITECTURE SPECIFICATION |
| Date | 2026-08-14 |

---

# 1. Purpose

This document defines the Sprint 4 architecture for a shared Alias Resolution Layer within the Commerce AI Generator Food Knowledge architecture.

The purpose of the Alias Resolution Layer is to provide a reusable mechanism for resolving non-canonical product, category, and provider terminology into stable canonical identities without expanding the responsibilities of existing registries beyond their approved architecture boundaries.

This specification is issued before substantial implementation begins.

Implementation shall conform to this specification unless a subsequent architecture decision explicitly modifies the approved design.

---

# 2. Governing Architecture

The governing Sprint 4 authorization is:

```text
ADA-MA-2026-022-SPRINT4
````

Authorization commit:

```text
a8029a4
```

The preceding Sprint 3 architecture handoff is:

```text
DHN-MA-2026-020-SPRINT3
```

Handoff commit:

```text
f4edea3
```

The historical Sprint 3 runtime verification baseline remains:

```text
6abc8fb
```

Sprint 4 does not rewrite the historical meaning of that baseline.

---

# 3. Architecture Context

Sprint 3 established a multi-provider Food Knowledge architecture with:

```text
Category Registry

Food Knowledge Provider Registry

Domain Providers

Provider Selection

Runtime Routing

Shared Result Contract
```

The integrated runtime portfolio contained fifteen providers.

Sprint 3 also identified the following Architecture Observation:

```text
Historical Provider Membership Expectation Drift
```

Final Sprint 3 disposition:

```text
CONFIRMED
NON-BLOCKING
CARRIED FORWARD
```

Sprint 4 shall improve resolution architecture without retroactively redefining the Sprint 3 completion decision.

---

# 4. Problem Statement

Alias resolution currently exists implicitly or locally across multiple architecture concerns.

Examples include:

```text
Localized names

Alternative category names

Product terminology variants

Common abbreviations

Singular / plural variants

Spacing variants

Provider-specific aliases

Domain-specific terminology
```

Without a shared resolution boundary, alias logic may become duplicated across:

```text
Category Registry

Provider Registry

Individual Providers

Parsers

Routing Logic

Tests
```

This creates risks including:

```text
Responsibility duplication

Inconsistent normalization

Divergent routing behavior

Hidden precedence rules

Difficult regression maintenance

Cross-domain alias collisions
```

Sprint 4 therefore introduces an explicit Alias Resolution Layer.

---

# 5. Architecture Objective

The primary objective is:

```text
RAW INPUT
        ↓
NORMALIZATION
        ↓
ALIAS RESOLUTION
        ↓
CANONICAL IDENTITY
        ↓
EXISTING CATEGORY / PROVIDER RESOLUTION
```

The Alias Resolution Layer shall resolve terminology.

It shall not replace domain parsing, provider routing, scoring, recommendation, or semantic reasoning.

---

# 6. Architecture Responsibilities

The Alias Resolution Layer is responsible for:

```text
Alias normalization

Alias registration

Alias lookup

Canonical identity mapping

Alias collision detection

Resolution precedence

Resolution traceability

No-match behavior
```

It may support:

```text
Category aliases

Provider aliases

Product terminology aliases

Localized terminology aliases
```

provided ownership remains explicit.

---

# 7. Explicit Non-Responsibilities

The Alias Resolution Layer shall not be responsible for:

```text
Product scoring

Product recommendation

Market intelligence

User personalization

LLM reasoning

Semantic ranking

Domain attribute extraction

Provider business logic

Result contract construction

Category registration ownership

Provider registration ownership
```

These responsibilities remain outside this layer.

---

# 8. Core Architecture Model

The proposed architecture is:

```text
Input
        ↓
AliasNormalizer
        ↓
AliasResolver
        ↓
AliasResolution
        ↓
Canonical Identity
        ↓
Category Registry / Food Knowledge Registry
        ↓
Provider Selection
        ↓
Domain Runtime
```

The architecture shall remain composable and deterministic.

---

# 9. AliasNormalizer Responsibility

`AliasNormalizer` is responsible only for deterministic input normalization.

Authorized normalization may include:

```text
Leading / trailing whitespace removal

Case normalization

Repeated whitespace normalization

Unicode normalization where explicitly required

Approved punctuation normalization

Approved separator normalization
```

Normalization shall not perform semantic inference.

For example:

```text
"  Olive   Oil "
```

may normalize to:

```text
"olive oil"
```

But:

```text
"healthy cooking oil"
```

shall not automatically become:

```text
"olive_oil"
```

without an explicitly registered alias or separately authorized semantic classification mechanism.

---

# 10. Alias Record Model

The architecture should support an explicit alias record concept.

Conceptual model:

```text
AliasRecord
────────────────────────
alias
normalized_alias
canonical_id
alias_type
owner
priority
metadata
```

Minimum required fields:

```text
alias

canonical_id

alias_type
```

Recommended fields:

```text
owner

priority

source

locale

metadata
```

Implementation details may vary provided the architectural semantics remain equivalent.

---

# 11. Canonical Identity

Alias resolution shall return a canonical identity rather than directly performing domain analysis.

Examples:

```text
"올리브오일"
        ↓
canonical_id = "olive_oil"
```

```text
"herbs and spices"
        ↓
canonical_id = "herb_spice"
```

The canonical identity shall correspond to an identity already recognized by the appropriate owning registry or provider architecture.

Alias resolution shall not create hidden canonical identities.

---

# 12. Alias Types

The initial architecture may support the following alias types:

```text
CATEGORY

PROVIDER

PRODUCT_TERM

LOCALIZED_TERM
```

The minimum Sprint 4 implementation need not support all types immediately.

However, alias type shall be explicit enough that different ownership contexts are not silently mixed.

---

# 13. Provider.aliases Compatibility

Existing:

```text
Provider.aliases
```

shall remain a supported provider contract unless separately changed by architecture authorization.

Sprint 4 shall prefer:

```text
Provider.aliases
        ↓
Alias Resolution Layer ingestion
        ↓
Shared resolution index
```

rather than duplicating provider alias matching logic throughout the runtime.

The shared layer may consume provider aliases.

It shall not silently redefine provider ownership.

---

# 14. Category Registry Boundary

The Category Registry remains responsible for:

```text
Canonical category identity

Category registration

Category metadata

Category existence
```

The Category Registry shall not become responsible for unrestricted alias intelligence.

Preferred relationship:

```text
Alias Resolution Layer
        ↓
canonical category_id
        ↓
Category Registry
```

rather than:

```text
Category Registry
        ↓
General semantic interpretation
```

---

# 15. Food Knowledge Registry Boundary

The Food Knowledge Registry remains responsible for:

```text
Provider registration

Provider identity

Provider order

Provider lookup

Provider resolution
```

Alias resolution may provide canonical inputs to the Registry.

Preferred relationship:

```text
Raw category / provider term
        ↓
Alias Resolution Layer
        ↓
Canonical category_id
        ↓
Food Knowledge Registry
```

The Registry remains authoritative for provider existence.

---

# 16. Resolution Interface

A conceptual shared interface may take the form:

```text
resolve_alias(
    value,
    *,
    alias_type=None,
    locale=None,
)
```

and return:

```text
AliasResolution
```

or:

```text
None
```

The exact Python API is not mandated by this specification.

However, the API shall preserve deterministic behavior and explicit failure handling.

---

# 17. AliasResolution Result

A successful resolution should make the following information available:

```text
input_value

normalized_value

canonical_id

alias_type

matched_alias

owner
```

Optional diagnostic information may include:

```text
priority

source

locale

metadata
```

This supports Evidence First verification and debugging.

---

# 18. No-Match Behavior

No-match behavior shall be explicit.

Preferred behavior:

```text
Alias Resolver
        ↓
NO MATCH
        ↓
Return None / explicit unresolved result
        ↓
Existing resolution path continues
```

The Alias Resolution Layer shall not fabricate a canonical identity.

No-match shall not automatically be treated as an exception unless the calling contract explicitly requires resolution.

---

# 19. Failure Behavior

Possible resolver outcomes shall remain distinguishable:

```text
MATCH

NO MATCH

AMBIGUOUS MATCH

INVALID INPUT
```

Where implementation complexity requires staged delivery, Sprint 4 may initially support:

```text
MATCH

NO MATCH
```

provided ambiguous alias registration is prevented during construction or registration.

---

# 20. Alias Collision Policy

Two aliases that normalize to the same value but resolve to different canonical identities create an alias collision.

Example:

```text
normalized alias
"apple"

→ fruit

and

→ another canonical owner
```

This shall not be silently resolved by arbitrary registration order.

The architecture shall either:

```text
reject the collision
```

or:

```text
require an explicit precedence / ownership rule
```

Collision behavior must be deterministic and testable.

---

# 21. Resolution Precedence

Default resolution precedence shall be explicit.

Recommended order:

```text
1. Direct canonical identity
2. Exact normalized alias
3. Scoped alias match
4. Existing provider supports() fallback
```

A future semantic or fuzzy layer may be added only through separate authorization.

Sprint 4 Alias Resolution shall not silently introduce fuzzy or probabilistic routing.

---

# 22. Direct Canonical Identity First

If an input already represents a valid canonical identity, direct identity resolution shall take precedence over aliases.

Example:

```text
olive_oil
```

shall remain:

```text
olive_oil
```

without requiring alias translation.

This protects stable contracts and reduces unnecessary indirection.

---

# 23. Scoped Alias Resolution

Where identical alias text is valid in different contexts, the architecture may support scoped resolution.

Possible scopes:

```text
alias_type

domain

provider

locale

owner
```

Scoped resolution shall be explicit.

Global aliases shall not silently override scoped aliases without an approved precedence rule.

---

# 24. Determinism Requirement

For a fixed:

```text
Alias Registry State

Input

Resolution Scope
```

the result must be deterministic.

Required property:

```text
Same Input
+
Same Resolver State
=
Same Resolution
```

Repeated resolution shall not depend on unordered collection behavior.

---

# 25. Ordering Requirement

Alias registration order shall not unintentionally become an architecture contract.

If priority matters, priority shall be explicit.

Preferred architecture:

```text
explicit priority
```

over:

```text
implicit insertion-order conflict resolution
```

This principle directly reduces the risk of repeating historical provider-order expectation drift in a new subsystem.

---

# 26. Alias Registry

The architecture may introduce a dedicated registry concept:

```text
AliasRegistry
```

Responsibilities:

```text
Register alias records

Normalize alias keys

Detect collisions

Lookup aliases

Expose deterministic resolution data
```

It shall not manage provider registration or category registration.

---

# 27. Proposed Module Boundary

A recommended implementation location is:

```text
app/services/food/knowledge/alias_resolution/
```

Potential modules:

```text
__init__.py

models.py

normalizer.py

registry.py

resolver.py
```

This location is recommended, not mandated.

Equivalent structure is acceptable if responsibility boundaries remain clear.

---

# 28. Dependency Direction

Preferred dependencies:

```text
Alias Models
        ↑
Alias Normalizer
        ↑
Alias Registry
        ↑
Alias Resolver
        ↑
Food Knowledge Registry integration
```

Domain providers may expose alias metadata.

The shared resolver shall not depend on domain scoring/rules internals.

---

# 29. Domain Provider Integration

Domain providers may supply alias metadata such as:

```text
aliases = (
    ...
)
```

The integration layer may collect these aliases into the shared Alias Registry.

Providers remain responsible for declaring aliases they own.

The shared layer is responsible for normalization and resolution mechanics.

---

# 30. Provider Ownership

An alias originating from a provider shall preserve ownership metadata where practical.

Example:

```text
Alias:
"olive oil"

Canonical ID:
olive_oil

Owner:
OliveOilKnowledgeProvider
```

This enables collision analysis and verification traceability.

---

# 31. Category Alias Ownership

Category aliases shall map to canonical category identities.

Ownership of the canonical category remains with the Category Registry architecture.

The Alias Resolution Layer only maps terminology to that identity.

---

# 32. Product-Term Aliases

Product-term aliases may be supported when they represent stable terminology mappings.

They shall not become a replacement for domain parsers.

Example:

```text
"extra virgin olive oil"
```

may help identify:

```text
olive_oil
```

but the Alias Resolver shall not be responsible for extracting:

```text
grade

origin

acidity

packaging

quality score
```

Those remain domain concerns.

---

# 33. Locale Support

Locale metadata may be supported.

Conceptual examples:

```text
ko-KR

en-US
```

Locale behavior shall remain optional unless an alias is genuinely ambiguous without locale context.

Sprint 4 shall avoid introducing unnecessary locale complexity into aliases that are globally unambiguous.

---

# 34. Backward Compatibility

Sprint 4 shall preserve existing approved runtime behavior.

Minimum compatibility expectations:

```text
Existing category_id lookup continues to work

Existing provider registration continues to work

Existing provider IDs remain unchanged

Existing FoodKnowledgeResult contract remains unchanged

Existing deterministic routing remains operational

Provider.aliases remains available
```

Alias resolution shall be additive unless separately authorized.

---

# 35. Integration Strategy

Preferred staged integration:

```text
Phase 1
Introduce isolated Alias Resolution Layer

Phase 2
Load provider alias metadata

Phase 3
Integrate canonical alias resolution before provider fallback

Phase 4
Add architecture boundary verification

Phase 5
Perform cross-domain regression
```

Each phase should remain independently testable.

---

# 36. Historical Membership Drift Separation

The Sprint 3 observation:

```text
Historical Provider Membership Expectation Drift
```

concerns provider portfolio expectation evolution.

Alias resolution work shall not conflate this with alias matching.

However, Sprint 4 Verification Contract Evolution may separately normalize provider portfolio tests.

The two workstreams shall remain distinguishable:

```text
Alias Resolution Architecture

and

Verification Contract Modernization
```

---

# 37. Provider Portfolio Verification Contract

Sprint 4 verification should distinguish:

```text
Required Provider Presence

Provider ID Uniqueness

Relative Ordering

Exact Membership
```

Exact membership shall be asserted only where it is an intentional architecture contract.

Expansion-safe tests should prefer:

```text
required providers are present
```

over:

```text
registry equals one historical fixed list
```

unless exact membership is architecturally required.

---

# 38. Relative Ordering Contract

Where provider ordering affects routing, relative ordering may be a legitimate architecture contract.

Example conceptual invariant:

```text
fruit precedes a general fallback provider
```

is different from:

```text
the registry must contain exactly N providers
```

Sprint 4 tests shall distinguish these semantics.

---

# 39. Verification Contract Modernization

Sprint 4 is authorized to modernize historical tests only after their architectural intent is identified.

For each affected historical test:

```text
Identify intended invariant

Determine whether invariant remains valid

Replace accidental exact-membership assumptions

Preserve intentional ordering behavior

Record evidence
```

Historical tests shall not be changed merely because they fail.

---

# 40. Architecture Boundary Tests

Sprint 4 shall add verification protecting responsibilities such as:

```text
Alias Resolver does not score products

Alias Registry does not register providers

Category Registry does not perform fuzzy search

Provider Registry remains authoritative for providers

Alias collisions are deterministic

Canonical IDs remain stable
```

These tests should protect architectural responsibility, not implementation trivia.

---

# 41. Unit Verification Requirements

Alias Resolution unit verification should include:

```text
Normalization

Exact alias lookup

Canonical identity passthrough

No-match

Collision detection

Duplicate alias behavior

Priority behavior if implemented

Scoped aliases if implemented
```

---

# 42. Integration Verification Requirements

Integration verification shall include:

```text
Provider alias ingestion

Category alias resolution

Provider resolution after alias translation

Existing direct category resolution

Existing product routing

Provider uniqueness

Result contract compatibility

Cross-domain determinism
```

---

# 43. Regression Requirements

Sprint 4 regression shall verify that introducing Alias Resolution does not regress completed Sprint 3 behavior.

At minimum:

```text
Food Knowledge regression

Provider registration

Provider selection

Category resolution

Cross-domain routing

Result contracts

Compilation safety
```

Any failures shall be attributed before remediation.

---

# 44. Evidence First Requirement

All Architecture Completion decisions must be based on executed evidence.

Required principle:

```text
No Architecture Completion Claim
Without Runtime and Verification Evidence
```

Failing evidence shall be preserved.

It shall not be hidden through undocumented test removal or production-code modification.

---

# 45. No Silent Remediation

During Sprint 4:

```text
NO SILENT PRODUCTION CHANGE

NO SILENT TEST NORMALIZATION

NO SILENT CONTRACT CHANGE
```

Every material architecture change shall be attributable to an approved Sprint 4 objective.

---

# 46. Migration Strategy

Existing providers shall not require simultaneous invasive migration.

Preferred migration model:

```text
Existing Provider
        ↓
Existing aliases retained
        ↓
Shared layer consumes aliases
        ↓
Existing supports() remains fallback
```

This enables incremental adoption.

---

# 47. Fallback Strategy

Existing `supports()` behavior shall remain available during the initial migration unless architecture evidence supports removal.

Preferred resolution flow:

```text
Canonical ID
        ↓
Alias Resolution
        ↓
Provider Lookup
        ↓
Existing supports() fallback
```

This minimizes behavioral regression risk.

---

# 48. Performance Boundary

Alias resolution should remain lightweight and deterministic.

The initial layer should not introduce:

```text
External network calls

LLM calls

Vector database dependency

Remote semantic search
```

into the core Food Knowledge provider selection path.

Such capabilities require separate architecture review.

---

# 49. Persistence Boundary

Sprint 4 does not require a database-backed Alias Registry.

An in-memory or configuration-backed registry is acceptable for the initial architecture.

Persistent alias management may be introduced later if supported by an explicit requirement and architecture decision.

---

# 50. Configuration Boundary

Alias definitions may originate from:

```text
Provider metadata

Static Python definitions

Configuration files

Approved registry data
```

The architecture shall not require a single storage mechanism unless necessary.

Resolution semantics shall remain independent from storage format where practical.

---

# 51. Security and Input Safety

Alias normalization shall avoid arbitrary code execution or dynamic import behavior based on untrusted input.

Alias values shall be treated as data.

Canonical IDs shall be validated before use by owning registries.

---

# 52. Observability

Resolution diagnostics should make it possible to determine:

```text
Input

Normalized Input

Matched Alias

Canonical ID

Owner

Resolution Path
```

This information may be exposed internally for verification and debugging.

User-facing exposure is not required by this specification.

---

# 53. Architecture Invariants

Sprint 4 shall preserve the following invariants:

```text
Canonical provider IDs remain stable

Provider IDs remain unique

Alias resolution remains deterministic

Alias collisions are not silently ignored

Category Registry remains category authority

Food Knowledge Registry remains provider authority

Provider.aliases remains compatible

Result contract remains compatible
```

---

# 54. Implementation Prohibition

Implementation shall not:

```text
Move scoring into Alias Resolver

Move parser responsibility into Alias Resolver

Make Category Registry a semantic search engine

Replace provider IDs with aliases

Use provider insertion order as alias collision resolution

Silently remove supports() fallback

Silently alter FoodKnowledgeResult
```

unless separately authorized.

---

# 55. Initial Completion Criteria

The initial Alias Resolution Layer implementation may be considered implementation-complete when:

```text
Architecture modules exist

Alias model exists

Normalization is implemented

Deterministic registry exists

Resolver exists

Collision behavior is tested

Provider alias ingestion is verified

Existing provider routing remains operational

Architecture boundaries are tested

Compilation passes
```

This does not itself constitute Sprint 4 Architecture Completion.

---

# 56. Integration Completion Criteria

Sprint 4 integration completion shall additionally require:

```text
Cross-domain alias resolution verified

Existing direct resolution verified

Provider ordering behavior verified

Result contract verified

Full regression executed

Failures attributed

Historical membership observation disposition reviewed
```

---

# 57. Architecture Completion Criteria

Final Sprint 4 Architecture Completion shall require independent 00_1 review of:

```text
Specification conformance

Boundary preservation

Runtime compatibility

Integration evidence

Regression evidence

Observation disposition

Blocking defect status

Evidence completeness
```

---

# 58. Carried Observation Disposition

The Sprint 3 observation remains at Sprint 4 start:

```text
Historical Provider Membership Expectation Drift

CONFIRMED

NON-BLOCKING

CARRIED FORWARD
```

This specification does not declare it resolved.

Resolution requires explicit evidence showing that the intended provider portfolio verification contracts have been reconciled.

---

# 59. Architecture Decision

00_1 Master Architecture determines:

```text
ARS-MA-2026-001-ALIAS-RESOLUTION

ALIAS RESOLUTION LAYER
ARCHITECTURE SPECIFICATION

APPROVED FOR IMPLEMENTATION
```

subject to:

```text
ADA-MA-2026-022-SPRINT4
```

---

# 60. Authorized Next Stage

Following approval and repository preservation of this specification, Sprint 4 may proceed to:

```text
Alias Resolution Layer
IMPLEMENTATION
```

Implementation shall conform to the approved boundaries of this document.

Material deviation requires architecture review.

---

# 61. Current Sprint 4 State

```text
Sprint 3 Food Knowledge Architecture
COMPLETE

Sprint 3 Architecture Handoff
COMPLETE

ADA-MA-2026-022-SPRINT4
AUTHORIZED

ARS-MA-2026-001-ALIAS-RESOLUTION
APPROVED FOR IMPLEMENTATION

Alias Resolution Implementation
NEXT

Sprint 4 Verification
PENDING

Sprint 4 Integration Completion
PENDING

Sprint 4 Architecture Completion
NOT YET DECLARED
```

---

# Official Architecture Specification

00_1 Master Architecture formally approves the Alias Resolution Layer architecture defined by this document for Sprint 4 implementation.

The approved design establishes:

```text
Explicit Alias Resolution Responsibility

Deterministic Normalization

Canonical Identity Resolution

Provider.aliases Compatibility

Category Registry Boundary Preservation

Food Knowledge Registry Boundary Preservation

Explicit Collision Handling

Backward-Compatible Provider Resolution

Evidence-Based Verification
```

Accordingly:

```text
ARS-MA-2026-001-ALIAS-RESOLUTION

APPROVED FOR IMPLEMENTATION
```

The carried Sprint 3 Architecture Observation:

```text
Historical Provider Membership Expectation Drift
```

remains:

```text
CONFIRMED
NON-BLOCKING
CARRIED FORWARD
```

until independently dispositioned through Sprint 4 evidence.

---

**Approved By**

**00_1 Master Architecture**

Commerce AI Generator

**Date**

2026-08-14
