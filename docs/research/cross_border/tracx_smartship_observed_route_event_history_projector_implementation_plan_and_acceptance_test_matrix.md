# TracX SmartShip observed route event history projector implementation plan and acceptance-test matrix

## Document status

- Gate: `CB-EA5E-11`
- Candidate: `candidate:shipping-aggregator:tracx-smartship`
- Product surface: polling `SmartShipService.Tracking`
- Source collection: polling `tracking_history`
- Canonical target: `observed_route_event_history`
- Status: `READ-ONLY IMPLEMENTATION PLAN DEFINED`
- Authorized plan artifact count: `ONE`
- Projector implementation performed: `NO`
- Test implementation performed: `NO`
- Projector implementation authority: `NOT YET AUTHORIZED`
- Package, registry, network, persistence, and runtime authority: `DENIED`

## Purpose

This plan converts the sealed TracX SmartShip polling compatibility observation
and projector-planning authorization boundary into an exact prospective
implementation contract and acceptance-test matrix.

This document creates no executable or test code. A later, separately authorized
implementation gate must decide whether the two prospective implementation
artifacts may be created.

Delivery WebHook and `MultiTracking` remain excluded observation surfaces.

## Governing sealed inputs

This plan is governed by:

1. `tracx_smartship_observed_route_event_history_projection_compatibility_worksheet.md`;
2. `tracx_smartship_observed_route_event_history_projection_compatibility_decision.md`;
3. `tracx_smartship_observed_route_event_history_projector_authorization_boundary_decision.md`;
4. `observed_route_event_history_implementation_ownership_and_reuse_decision.md`;
5. the existing canonical `observed_route_event_history.py` owner;
6. the existing immutable `EvidenceProvenance` contract;
7. the ShipStation V2 and MyDHL API implementation-plan precedents; and
8. the implemented ShipStation V2 and MyDHL API projector/test precedents.

Precedent structure may be reused. Provider-specific semantics may not be copied
without direct TracX evidence.

## Prospective later artifacts

Only a later explicit implementation gate may authorize exactly these two files:

1. `app/services/cross_border/tracx_smartship_observed_route_event_history_projector.py`;
2. `tests/services/cross_border/test_tracx_smartship_observed_route_event_history_projector.py`.

No existing file may be modified by that implementation gate.

This plan does not itself authorize creation of either file.

## Exact module ownership

The prospective projector module owns only deterministic transformation of one
already-acquired polling `SmartShipService.Tracking` response into the existing
canonical `ObservedRouteEventHistory`.

It must not own:

- HTTP acquisition;
- URL or credential configuration;
- authentication;
- retries or rate limiting;
- webhook ingestion;
- `MultiTracking` assembly;
- cross-response or cross-page assembly;
- persistence or caching;
- package export;
- registry or factory dispatch;
- serialization;
- deployment or runtime activation.

## Exact imports and public surface

The prospective module may import only:

- `Mapping` from `collections.abc`;
- existing canonical observed-route-event-history classes and enums; and
- existing `EvidenceProvenance`.

The module exposes exactly one public function:

```python
def project_tracx_smartship_tracking_history(
    response: Mapping[str, object],
    *,
    correlation_key: str,
    correlation_value: str,
    provenance: EvidenceProvenance,
) -> ObservedRouteEventHistory:
    ...
No input dataclass, provider client, serializer, registry, factory, adapter,
dispatcher, protocol, additional public function, or __all__ export is
authorized.

The exact private symbols are:

_REPORTING_SOURCE_ID
_CORRELATION_KEYS
_CONSTRAINTS
_optional_source_string
_required_correlation_key
_normalize_correlations
_project_location
_project_event

Additional private helpers require a later plan amendment.

Fixed reporting-source identity

The module owns:

_REPORTING_SOURCE_ID = (
    "candidate:shipping-aggregator:tracx-smartship"
)

The caller cannot override this identity.

provenance must be an existing EvidenceProvenance instance whose
source_id equals _REPORTING_SOURCE_ID. A wrong runtime type raises
TypeError; a source mismatch raises ValueError.

The exact caller-supplied provenance object is reused unchanged as history
provenance. No fallback provenance is constructed.

EvidenceProvenance has no canonical-target field. This plan therefore does not
invent one. Canonical-target suitability is enforced by this exact
projector-specific return contract and canonical constructor reuse.

The plan adds no unsealed literal restriction to provenance.source_type.
Its existing non-empty invariant remains authoritative. Retrieval or effective
time is not reused as event occurrence or provider-recorded time.

Exact response contract

response must be a runtime Mapping. Any other runtime type, including
None, raises TypeError.

The response must contain the exact key tracking_history. Absence raises
ValueError.

response["tracking_history"] must be a list or tuple. None and every
other runtime type raise TypeError.

An empty list or tuple is a valid observed empty source collection and produces
an empty canonical event tuple.

Every collection element must be a runtime Mapping. One invalid element fails
the entire call with TypeError.

Projection is atomic. No partial history is returned after validation or
canonical-construction failure.

The function reads an already-acquired response snapshot and performs no I/O.

Exact correlation contract

The only recognized top-level correlation keys are:

_CORRELATION_KEYS = (
    "shipping_no",
    "ref_no",
    "qs_no",
)

correlation_key identifies the acquisition-owned correlation selected by the
caller.

Rules:

correlation_key must be a runtime string;
it must equal one of the three exact _CORRELATION_KEYS values;
surrounding whitespace or case variants do not create an alias;
correlation_value must be a runtime string;
its trimmed value must be non-empty;
the selected key must be present in response;
the selected response value must be a runtime string;
its trimmed value must be non-empty; and
it must equal the trimmed correlation_value.

Wrong runtime types raise TypeError. Unsupported keys, absent or empty
selected correlation, and mismatched selected values raise ValueError.

Every non-selected recognized correlation field, when present, must be either
None or a runtime string. A wrong type raises TypeError. Strings are
trimmed; empty results are omitted.

Multiple non-empty correlation fields are not assigned precedence and are not
merged. They retain their separate source roles in flat immutable history
metadata under their exact source keys.

The selected normalized correlation value populates canonical
tracking_number.

The history fields remain:

carrier_reference=None;
source_record_id=None;
request_correlation_id=None.

No correlation value becomes a globally unique shipment identity, event
identity, carrier reference, actor, scope reference, or request identifier.

A top-level caller or source metadata key is ignored. Metadata collision is
prevented because history metadata is constructed only from the three fixed
correlation keys.

Source-string normalization

Every supported source event value must be either None or a runtime string.

Supported strings are trimmed. Empty strings normalize to None.

Wrong runtime types raise TypeError; they are never stringified.

No source string is case-folded, translated, parsed as a datetime, geocoded,
classified, or normalized into a provider-independent delivery state.

Exact supported event keys

Phase 1 recognizes exactly these polling event keys:

status
status_code
details
location
date

This exact set is bounded by sealed evidence that names these key roles
directly.

The plan does not recognize or preserve reason, auxiliary tracking codes, or
proof-of-delivery references because their exact source-key spelling and runtime
types are not sealed strongly enough for an executable contract.

Those fields remain deferred. Unknown or deferred keys are ignored and do not
become generic metadata.

Exact event projection

For each tracking_history entry:

Source key	Canonical destination	Exact rule
status_code	provider_event_code	optional trimmed source string
status	raw_status	optional trimmed source string
details	raw_status_description	optional trimmed source string
date	occurred_at_raw	optional trimmed raw source string
location	location.raw_description	bounded rule below

Every other canonical event field remains:

Canonical field	Value
provider_event_id	None
occurred_at	None
recorded_at	None
recorded_at_raw	None
actor	None
scope	ObservedRouteEventScope.UNKNOWN
scope_reference	None
source_sequence	None
relationships	()
provenance	None
metadata	immutable empty mapping

Array position is used only for indexed error messages. It does not populate
event identity or sequence.

No source status is case-folded or mapped to a canonical delivery taxonomy.
status_code is not merged with another code. details is not concatenated
with an unresolved reason field.

Raw temporal rule

A normalized non-empty polling date maps only to occurred_at_raw.

The projector must set:

occurred_at=None;
recorded_at=None;
recorded_at_raw=None.

The projector performs no date parsing, timezone inference, UTC-offset
inference, aware-datetime construction, format validation, webhook Date
reuse, occurrence-time assertion, provider-recorded-time assertion, or
response-observation-time assertion.

Any non-empty source string is preserved after the exact trimming rule without
asserting syntactic or semantic validity.

A wrong runtime type raises TypeError.

Temporal evidence never authorizes chronological sorting.

Location rule

A normalized non-empty location source string creates
ObservedRouteEventLocation with only raw_description populated.

The following remain absent:

country_code;
subdivision;
locality;
postal_code;
facility_reference;
facility_name.

An absent, None, or empty normalized source value produces location=None.

Location text does not establish custody, jurisdiction, customs state, country,
facility ownership, carrier identity, event actor, or event scope.

A wrong runtime type raises TypeError.

Event minimum-content and atomic failure

A source entry is projectable only when at least one of these canonical values
is non-empty after cleaning:

provider_event_code;
raw_status;
raw_status_description;
occurred_at_raw; or
location.

Unknown, deferred, or metadata-only source content does not satisfy the
canonical minimum-content rule.

An empty mapping, a whitespace-only supported entry, or a non-empty entry
containing only unknown/deferred keys raises indexed ValueError.

One invalid event fails the entire projection. The projector does not filter,
silently drop, sort, deduplicate, merge, correct, overwrite, supersede, or
replace entries.

Exact history construction

The prospective projector returns:

ObservedRouteEventHistory(
    reporting_source_id=_REPORTING_SOURCE_ID,
    provenance=provenance,
    events=tuple(projected_events),
    carrier_reference=None,
    tracking_number=normalized_correlation_value,
    source_record_id=None,
    request_correlation_id=None,
    completeness=ObservedRouteEventHistoryCompleteness.UNKNOWN,
    ordering=ObservedRouteEventHistoryOrdering.SOURCE_ORDER,
    has_more=None,
    next_page_token=None,
    freshness=None,
    constraints=_CONSTRAINTS,
    metadata=normalized_correlations,
)

Source event order is preserved exactly. SOURCE_ORDER carries no
chronological meaning.

Repeated source entries remain separate.

Later mutation of the source response cannot mutate the canonical history,
event tuple, location object, constraints, or metadata.

Exact constraint tuple

The private immutable tuple is fixed in this order:

_CONSTRAINTS = (
    "history_completeness_not_documented",
    "chronological_order_not_documented",
    "stable_event_identity_not_documented",
    "stable_event_sequence_not_documented",
    "provider_recorded_time_not_documented",
    "event_level_actor_identity_not_documented",
    "event_level_carrier_identity_not_documented",
    "duplicate_and_revision_semantics_not_documented",
    "pagination_and_truncation_semantics_not_documented",
    "retention_and_update_latency_not_documented",
    "temporal_format_and_timezone_unresolved",
    "proof_of_delivery_identity_semantics_unresolved",
    "polling_webhook_surface_separation_required",
)

Tuple order is part of the planned contract.

No constraint is removed when optional values exist. No provider payload value
adds a constraint dynamically.

Deterministic failure taxonomy

Raise TypeError for:

wrong top-level response type;
wrong tracking_history collection type;
wrong event-entry type;
wrong supported event-field type;
wrong correlation-key runtime type;
wrong correlation-value runtime type;
wrong recognized response-correlation runtime type; and
wrong provenance runtime type.

Raise ValueError for:

missing tracking_history;
unsupported correlation key;
empty correlation value;
absent selected response correlation;
empty selected response correlation;
mismatch between selected response correlation and caller value;
provenance source mismatch;
an empty source event;
a non-empty event without supported canonical minimum content.

A non-empty temporal string is unresolved raw evidence and is not rejected for
format. Only its runtime type and empty normalization are validated.

Canonical constructor exceptions propagate unchanged.

No exception is converted into an empty successful history.

Acceptance-test matrix
ID	Required acceptance
AT-01	Exact public function name, argument order, keyword-only boundary, annotations, and return type.
AT-02	Reporting source is fixed to the exact TracX candidate identity.
AT-03	Wrong provenance runtime type raises TypeError.
AT-04	Adjacent or mismatched provenance source_id raises ValueError.
AT-05	Exact caller-supplied provenance object is reused without mutation.
AT-06	Mapping response is accepted and non-mapping response raises TypeError.
AT-07	Missing tracking_history raises ValueError.
AT-08	None or wrong history collection type raises TypeError.
AT-09	Empty list and empty tuple each produce a valid empty event tuple.
AT-10	Non-mapping event entry raises indexed TypeError.
AT-11	correlation_key must be an exact supported string.
AT-12	Wrong, empty, or missing correlation_value fails deterministically.
AT-13	Selected response correlation must exist and be non-empty.
AT-14	Selected response/caller correlation mismatch raises ValueError.
AT-15	Wrong runtime type in any recognized response correlation raises TypeError.
AT-16	Multiple correlations remain separate with no inferred precedence.
AT-17	Selected correlation populates only canonical tracking_number.
AT-18	Minimal non-empty status produces raw_status.
AT-19	Minimal non-empty status_code produces provider_event_code.
AT-20	Minimal non-empty details produces raw_status_description.
AT-21	Minimal non-empty location produces raw-description-only location.
AT-22	Empty location produces no location object.
AT-23	Minimal non-empty date produces only occurred_at_raw.
AT-24	Canonical occurred_at, recorded_at, and recorded_at_raw remain None.
AT-25	Wrong runtime type for every supported event key raises TypeError.
AT-26	Supported strings are trimmed and empty strings normalize to None.
AT-27	Unknown and deferred keys do not leak into fields or metadata.
AT-28	Reason, auxiliary code, or POD-only entry fails minimum content.
AT-29	Empty, whitespace-only, and unsupported-only events raise indexed ValueError.
AT-30	One invalid element makes a multi-event projection fail atomically.
AT-31	Valid entries preserve exact source order.
AT-32	Duplicate entries remain separate.
AT-33	No chronological sorting occurs for raw date strings.
AT-34	Event identity, actor, carrier, scope reference, sequence, relationships, and event provenance remain absent.
AT-35	Completeness is UNKNOWN and ordering is SOURCE_ORDER.
AT-36	Pagination and freshness fields remain None.
AT-37	Exact thirteen-item ordered constraint tuple is emitted.
AT-38	History metadata contains only normalized recognized correlations.
AT-39	History metadata and all canonical collections are immutable.
AT-40	Later source-response mutation cannot change canonical output.
AT-41	Webhook-only keys produce no attribution or canonical claims.
AT-42	MultiTracking structures are not accepted or assembled.
AT-43	Direct module import exposes exactly one public function.
AT-44	Provider-neutral package export remains absent.
AT-45	Ingress and projection registries remain unchanged.
AT-46	Network, credentials, webhook, persistence, serialization, and runtime dependencies remain absent.
AT-47	Canonical objects are reused; no parallel event-history model exists.
AT-48	Pending implementation scope contains exactly the two prospectively named implementation files.

The focused test module must contain exactly one named test function for every
AT-01 through AT-48. Parameterization may create a larger observed pytest
case count.

Every conditional planning branch has a corresponding acceptance test.

Prospective implementation sequence

Only after a later explicit implementation-authorization gate:

create the isolated projector module;
add only the authorized canonical and provenance imports;
define the fixed source, correlation-key, and constraint constants;
implement exact source-string and correlation validation;
implement bounded raw location projection;
implement indexed event projection;
implement the single public projection function;
create the focused test module covering AT-01 through AT-48;
run the complete verification sequence;
create a separate implementation-result decision; and
leave commit, annotated tag, and push to later separate gates.
Verification sequence

A later implementation gate must run, in order:

focused projector acceptance tests;
existing canonical observed-route-event-history tests;
focused plus canonical combined tests;
all Cross-Border service tests;
full repository regression;
Python compile checks for the two prospective implementation artifacts;
import and dependency audit;
package-export and registry non-mutation audit;
exact file-scope and whitespace audit; and
final clean-state or exact-pending-scope verification.

Required results:

Verification	Required result
Focused acceptance tests	all collected cases pass
Canonical history tests	all pass
Combined focused/canonical tests	all pass
Cross-Border suite	all pass
Full regression	all pass
Compile checks	pass
Import/dependency audit	pass
Package and registry audit	unchanged
Whitespace audit	pass
Runtime activation	none
Static file-scope acceptance

At this planning gate, the only pending file must be this research plan.

A later implementation gate may create only the prospective projector and test
files while preserving this plan and its boundary decision unchanged.

No package, registry, canonical model, provenance model, dossier, worksheet,
compatibility decision, API, UI, database, configuration, or runtime file may
change.

Explicit non-authorizations

This plan does not authorize:

projector or test creation;
modification of the canonical model or provenance model;
package export;
ingress or projection registry mutation;
provider factory or dispatcher creation;
HTTP acquisition, credentials, retries, or rate limiting;
webhook ingestion or authentication;
Delivery WebHook attribution;
MultiTracking assembly;
cross-response, cross-page, or historical assembly;
date parsing or aware-datetime construction;
timezone or chronological inference;
event identity, actor, carrier, relationship, scope, or custody inference;
status taxonomy or normalized delivery-state generation;
preservation of unsealed reason, auxiliary-code, or POD key spellings;
sorting, deduplication, merging, correction, supersession, or replacement;
serialization, persistence, caching, API, UI, or database integration;
provider ranking, selection, recommendation, or verification;
Korea Post EMS consequences;
mutation of sealed research artifacts;
commit, tag, push, deployment, or runtime activation.
Plan result
exact public surface: DEFINED;
fixed reporting source: DEFINED;
exact response contract: DEFINED;
exact acquisition-owned correlation contract: DEFINED;
exact recognized event keys: FIVE;
ambiguous optional source keys: DEFERRED;
raw-temporal-only mapping: DEFINED;
exact location rule: DEFINED;
event minimum-content rule: DEFINED;
atomic failure behavior: DEFINED;
exact ordered constraints: THIRTEEN;
acceptance surfaces: AT-01 through AT-48;
prospective later implementation artifact count: TWO;
projector implementation performed: NO;
test implementation performed: NO;
package and registry mutation: DENIED;
production and runtime authority: NONE.
Required next gate

The next gate is:

CB-EA5E-11-C_TRACX_PROJECTOR_PLAN_JOINT_READ_ONLY_VALIDATION

It must validate this plan against the sealed boundary, worksheet,
compatibility decision, canonical owner, provenance contract, and implemented
provider precedents.

It must perform no stage, commit, tag, push, projector creation, test creation,
package mutation, registry mutation, or runtime activation.
