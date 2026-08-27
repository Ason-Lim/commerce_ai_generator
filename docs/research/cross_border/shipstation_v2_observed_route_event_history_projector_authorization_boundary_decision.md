# ShipStation V2 Observed Route Event History Projector Authorization Boundary Decision

## Document status

- Gate: `CB-EA5C-1C-B`
- Decision type: provider-projector implementation-authorization boundary
- Candidate: `candidate:shipping:shipstation-api`
- Product surface: ShipStation V2 `get_tracking_log`
- Canonical target: `observed_route_event_history`
- Decision: `BOUNDED PROJECTOR PLANNING AUTHORIZED`
- Production implementation performed: `NO`
- Ingress or projection registry mutation: `NOT AUTHORIZED`
- Network acquisition or runtime activation: `NOT AUTHORIZED`

## Purpose

This decision defines the maximum implementation boundary for a first
provider-specific projector from a ShipStation V2 tracking-log response into the
sealed provider-neutral `ObservedRouteEventHistory` model.

It does not implement the projector. It authorizes a later implementation plan
to specify one isolated deterministic mapping module and its focused tests.

## Selection basis

ShipStation V2 was selected for the first projector authorization review under
the rule `MINIMUM AUTHORIZED SEMANTIC BRANCHING`.

The selection does not rank providers or establish production preference.
MyDHL API retains its bounded strong-partial compatibility observation and
remains the second review candidate. Korea Post EMS retains its research-candidate
status and requires a dedicated direct-source worksheet and compatibility
decision before projector review.

## Inspected implementation architecture

The current Cross-Border implementation contains no executable provider
projector and no ShipStation-specific runtime module.

`external_evidence_projection.py` owns only provider-neutral kind-to-target
eligibility. It explicitly does not construct canonical evidence or interpret
provider fields.

`ExternalEvidenceIngress` explicitly excludes raw provider payloads,
provider-field mappings, credentials, HTTP state, and executable projection.

Therefore the ShipStation projector must not be added to either existing
contract and must not change their registries in this phase.

## Authorized module ownership

A later implementation gate may create exactly one independent production
module:

`app/services/cross_border/shipstation_v2_observed_route_event_history_projector.py`

That module may own only:

- ShipStation V2 tracking-log response shape validation;
- conservative source-field extraction;
- deterministic construction of the sealed canonical value objects; and
- provider-specific projection errors expressed through deterministic existing
  Python `TypeError` or `ValueError` behavior.

It must not own HTTP acquisition, authentication, credentials, retries, polling,
webhooks, persistence, serialization, provider selection, ranking, or registry
lookup.

## Authorized focused-test ownership

A later implementation gate may create exactly one focused test module:

`tests/services/cross_border/test_shipstation_v2_observed_route_event_history_projector.py`

No existing test file may be modified by the bounded projector implementation.

## Package-export boundary

The provider-specific projector must not be exported from the provider-neutral
`app.services.cross_border` package `__all__` surface in this phase.

Consumers authorized in a later phase must import it from its explicit
provider-specific module. This prevents provider-specific execution from being
presented as a general canonical Cross-Border contract.

## Input boundary

The later plan may define a provider-specific immutable projection-input value
object in the same module or a single explicitly named projection function whose
arguments carry:

- an already-acquired ShipStation V2 tracking-log response mapping;
- the request tracking number;
- the optional request carrier code; and
- an existing `EvidenceProvenance` instance for the exact acquisition.

The input boundary must not perform network access and must not accept
credentials, URLs, sessions, clients, retry configuration, or mutable runtime
registries.

The reporting source identity is fixed to
`candidate:shipping:shipstation-api`. It must not be caller-overridable and must
not be aliased to ShipEngine v1 or another ShipStation product surface.

## Output boundary

The only successful output is an `ObservedRouteEventHistory` instance.

The output must use:

- mandatory supplied acquisition provenance;
- the direct request tracking number as source-local correlation;
- the direct request carrier code as optional carrier correlation;
- an immutable event tuple preserving response order;
- `ObservedRouteEventHistoryCompleteness.UNKNOWN`;
- `ObservedRouteEventHistoryOrdering.SOURCE_ORDER` when response order is
  preserved;
- `has_more=None`;
- `next_page_token=None`; and
- `freshness=None`.

Construction must not evaluate freshness or infer completeness or chronology.

## Event mapping boundary

Each source event may map only the directly supported fields:

- `status_code` to `provider_event_code`;
- `carrier_status_code` to `raw_status`;
- `carrier_status_description` to `raw_status_description`;
- directly documented country-code evidence to location `country_code`;
- ambiguous non-empty `company_name` to location `raw_description`; and
- `carrier_detail_code` and other separately approved source-local remnants to
  immutable event metadata.

The projector must leave these values absent or conservative:

- `provider_event_id=None`;
- `occurred_at=None`;
- `occurred_at_raw=None`;
- `recorded_at=None`;
- `recorded_at_raw=None`;
- `actor=None`;
- `scope=UNKNOWN`;
- `scope_reference=None`;
- `source_sequence=None`;
- `relationships=()`; and
- event provenance `None` unless a later authorization establishes genuinely
  narrower event-level provenance.

`company_name` must not be promoted to facility ownership or actor identity.

## Collection-preservation boundary

The source `events` collection must be processed in returned order and copied to
an immutable tuple.

The projector must not sort, deduplicate, merge, correct, overwrite, supersede,
or manufacture relationships among events.

An empty source event collection may produce a valid empty canonical event tuple
when the response boundary is otherwise valid. A non-empty source event that has
no supported canonical minimum-content field must not be silently removed.

## Failure behavior

The implementation plan must define deterministic failure behavior with these
minimum rules:

- wrong top-level or nested runtime types raise `TypeError`;
- missing required request correlation raises `ValueError`;
- malformed event collection structure raises `TypeError`;
- a non-empty source event with no supported canonical minimum content raises
  `ValueError` rather than being silently dropped;
- invalid supplied provenance raises `TypeError`; and
- no error path falls back to inferred identity, time, actor, scope, location,
  relationship, completeness, or chronology.

Provider response interpretation must fail closed when safe bounded projection
is not possible.

## Constraint disclosure

The projected aggregate must preserve a stable, plan-defined tuple of constraint
identifiers representing at least:

- undocumented history completeness;
- absence of chronological-order guarantee;
- undocumented event occurrence time;
- undocumented stable event identity;
- undocumented provider-recorded time;
- undocumented event actor identity;
- undocumented pagination or truncation behavior; and
- undocumented provider freshness semantics.

The plan must use identifiers already supported by the sealed ShipStation
worksheet or explicitly document any exact spelling choice. Constraint labels do
not become canonical status or compatibility values.

## Metadata restraint

Metadata may preserve only source-local values that are not promoted into a
canonical semantic claim. It must be copied into the canonical immutable mapping.

The projector must not use metadata to create canonical event identity,
normalized status, actor identity, chronological ordering, or provider
equivalence.

## Explicitly unchanged contracts

The bounded implementation must not modify:

- `observed_route_event_history.py`;
- `external_evidence_ingress.py`;
- `external_evidence_projection.py`;
- `provenance.py`;
- `freshness.py`;
- `context.py`;
- `shipping.py`;
- the package-level `__init__.py`;
- any provider registry, dossier, endpoint, serializer, or database artifact; or
- any existing test module.

## Authority not created

This decision does not authorize:

- implementation before a separate plan and acceptance matrix is approved;
- live ShipStation API calls or credentials;
- ShipEngine v1 attribution;
- webhook, polling, page, or cross-response assembly;
- ingress-kind or canonical-target registration;
- runtime factory or automatic projector dispatch;
- dossier compatibility mutation;
- provider ranking, selection, or recommendation;
- MyDHL projector implementation;
- Korea Post EMS projector implementation;
- serialization, persistence, migration, API, UI, deployment, or activation; or
- commit, tag, or push by this decision itself.

## Decision result

- first projector review candidate: `SHIPSTATION_V2`;
- independent module ownership: `REQUIRED`;
- bounded deterministic projector planning: `AUTHORIZED`;
- projector implementation: `NOT YET AUTHORIZED`;
- provider-neutral package export: `DENIED`;
- ingress registry mutation: `DENIED`;
- projection registry mutation: `DENIED`;
- network acquisition: `DENIED`;
- runtime activation: `DENIED`;
- MyDHL compatibility consequence: `NONE`; and
- Korea Post EMS status consequence: `NONE`.

## Required next gate

The next gate must create a read-only ShipStation V2 projector implementation
plan and acceptance-test matrix. It must fix the exact public or private symbols,
input shape, constraint identifiers, field extraction rules, failure matrix,
authorized file count, and verification sequence before any production or test
file is created.
