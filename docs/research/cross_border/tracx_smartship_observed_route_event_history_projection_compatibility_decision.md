# TracX SmartShip Observed Route Event History Projection Compatibility Decision

## Document status

- Gate: `CB-EA5E-4`
- Status: `research decision`
- Candidate: `candidate:shipping-aggregator:tracx-smartship`
- Product surface: TracX SmartShip polling API
- Operation: `SmartShipService.Tracking`
- Evaluated collection: `tracking_history`
- Canonical target: `observed_route_event_history`
- Worksheet SHA-256:
  `cea2d6bd6895eabbc7263f0e3e2dc0dc144f747ab712f02d7bcb3d484809ab2b`
- Decision: `ACCEPTED AS BOUNDED PARTIAL PROJECTION OBSERVATION`
- Dossier mutation: `not authorized`
- Projector implementation: `not authorized`

## Decision question

Does the validated TracX SmartShip worksheet support a research-level
observation that the directly registered polling
`SmartShipService.Tracking` response and its `tracking_history` collection can
be conservatively projected into the sealed
`observed_route_event_history` contract without prohibited inference?

## Inputs reviewed

This decision reviews:

1. `observed_route_event_history_canonical_contract_definition.md`;
2. `observed_route_event_history_next_wave_candidate_boundary_decision.md`;
3. the sealed TracX SmartShip candidate-admission evidence recorded in
   `external_evidence_provider_evaluation_dossier.md`;
4. `tracx_smartship_observed_route_event_history_projection_compatibility_worksheet.md`;
5. the current TracX dossier compatibility record
   `cb-ea4r6-tracx-smartship-006`.

The worksheet was validated at 462 lines with SHA-256
`cea2d6bd6895eabbc7263f0e3e2dc0dc144f747ab712f02d7bcb3d484809ab2b`.

The validation established:

- worksheet identity: `PASS`;
- polling-surface boundary: `PASS`;
- canonical mapping: `PASS`;
- prohibited inference: `NONE`;
- dossier mutation: `NONE`;
- production mutation: `NONE`.

## Source identity finding

The evaluated reporting-source identity is fixed to:

`candidate:shipping-aggregator:tracx-smartship`

The accepted evidence surface is limited to the polling
`SmartShipService.Tracking` response.

TracX Logis is the observed API publisher and reporting-source candidate. It
does not automatically become:

- the physical carrier;
- the event actor;
- the delivery company for each polling event;
- the location owner;
- the custodian of the shipment at every reported state.

The polling source is not aliased to an adjacent provider or carrier.

Finding: `SOURCE IDENTITY SEPARATION = PASS`.

## Polling-surface boundary finding

The decision accepts only:

- the polling `SmartShipService.Tracking` operation;
- the polling `tracking_history` collection;
- polling response correlations including `shipping_no`, `ref_no`, and
  `qs_no`;
- polling event evidence categories directly registered in the dossier.

The decision excludes:

- `MultiTracking` collection assembly;
- Delivery WebHook projection;
- webhook-only `PackingNo`;
- webhook-only `TrackingNo`;
- webhook-only `RefOrderNo`;
- webhook-only `DeliveryCompanyCode`;
- webhook-only `DeliveryCompanyName`;
- webhook authentication, delivery, retry, timing, or ordering semantics;
- Korea Post EMS;
- planned-route topology;
- live API acquisition.

Polling and webhook evidence remain separate acquisitions.

Finding: `POLLING SURFACE BOUNDARY = PASS`.

## Sufficiency and compatibility distinction

The registered polling schema evidence is sufficient to support a bounded
research compatibility observation because it establishes:

- an event-history collection boundary through `tracking_history`;
- provider-native status and status-code evidence;
- polling `date` evidence;
- raw location evidence;
- details and reason evidence;
- tracking-specific codes;
- proof-of-delivery references;
- source-local shipment correlations.

This sufficiency does not establish:

- complete canonical coverage;
- stable event identity;
- stable event sequence;
- chronological ordering;
- history completeness;
- pagination or truncation behavior;
- duplicate, correction, or revision semantics;
- event occurrence versus provider-recorded-time meaning;
- timezone or UTC offset;
- event-level physical-carrier identity;
- event actor identity;
- proof-of-delivery identity or delivery correctness;
- production readiness.

Compatibility is accepted only at the strength directly supported by the
bounded mapping and explicit unknowns.

## Accepted bounded polling projection

The research-level observation accepts a prospective projection with these
boundaries:

- reporting source fixed to the TracX SmartShip candidate identity;
- mandatory Commerce AI-owned history provenance;
- immutable preservation of supported `tracking_history` entries;
- provider-native status preservation;
- provider-native status-code preservation without unrelated code merging;
- directly descriptive status text only when source semantics support it;
- raw-only polling temporal preservation;
- raw-only location preservation;
- explicitly owned source-local history correlation;
- no manufactured event identity;
- no deduplication or destructive merging;
- no actor or carrier inference;
- fail-closed minimum-content validation.

An event containing no supported canonical minimum content is invalid.
Metadata-only reason, auxiliary-code, or proof-of-delivery content cannot
manufacture an otherwise empty event.

If an evaluated entry cannot satisfy the canonical minimum-content invariant,
a future projector would have to fail closed for the collection rather than
return an incomplete successful result.

Finding: `BOUNDED POLLING PROJECTION = SUPPORTED WITH EXPLICIT GAPS`.

## Accepted temporal treatment

The polling `date` value is accepted only as unresolved raw temporal evidence.

The decision accepts:

- a non-empty polling `date` as prospective `occurred_at_raw`;
- `occurred_at=None`;
- `recorded_at=None`;
- `recorded_at_raw=None`;
- no chronological sorting.

The decision does not accept:

- timezone inference;
- UTC-offset inference;
- occurrence-time inference from the phrase history-change date;
- provider-recorded-time inference;
- response-observation-time inference;
- reuse of the webhook `Date` format for polling;
- chronology inferred from array position.

The polling `date` evidence therefore supports preservation, not temporal
normalization.

Finding: `TEMPORAL NON-INFERENCE = PASS`.

## Accepted unknown and absent values

The bounded observation accepts these conservative values:

| Canonical property | Accepted value |
|---|---|
| `provider_event_id` | `None` |
| `occurred_at` | `None` |
| `recorded_at` | `None` |
| `recorded_at_raw` | `None` |
| `actor` | `None` |
| `scope` | `UNKNOWN` |
| `scope_reference` | `None` |
| `source_sequence` | `None` |
| `relationships` | empty |
| `carrier_reference` | `None` |
| `completeness` | `UNKNOWN` |
| `ordering` | `SOURCE_ORDER` only when response order is preserved; otherwise `UNKNOWN` |
| `has_more` | `None` |
| `next_page_token` | `None` |
| `freshness` | `None` |

These values are not deficiencies to be silently filled. They are required
representations of unresolved or absent source evidence.

## Correlation finding

The polling response correlations `shipping_no`, `ref_no`, and `qs_no` are
accepted as provider-local correlation candidates.

This decision does not establish:

- canonical precedence among those fields;
- global shipment identity;
- global uniqueness;
- provider-independent equivalence;
- automatic promotion to event scope references.

A future acquisition contract must explicitly identify which correlation it
owns for the requested history.

Finding: `CORRELATION PRESERVATION = PASS WITH EXPLICIT OWNERSHIP`.

## Location and proof-of-delivery finding

A directly supported non-empty polling location value may be preserved only as
canonical `raw_description`.

The decision does not infer:

- country;
- subdivision;
- locality;
- postal code;
- facility identity;
- custody;
- jurisdiction;
- customs clearance;
- carrier identity.

Polling proof-of-delivery references may be retained only as source-local
metadata when their exact role and value are directly available.

Their presence does not establish:

- successful delivery;
- delivery correctness;
- recipient identity;
- signature identity;
- legal proof;
- event identity.

Finding: `LOCATION AND POD NON-INFERENCE = PASS`.

## Completeness, ordering, and collection finding

The accepted history-level values are:

- completeness: `UNKNOWN`;
- ordering: `SOURCE_ORDER` only as preservation of returned array position;
- chronological ordering: not established;
- `has_more`: `None`;
- `next_page_token`: `None`;
- retention boundary: unknown;
- truncation boundary: unknown;
- duplicate and revision policy: unknown.

Response position does not establish chronology. Absence of pagination
evidence does not establish complete history.

No sorting, deduplication, correction, supersession, overwriting, or
cross-acquisition merge is accepted.

Finding: `COLLECTION NON-INFERENCE = PASS`.

## Accepted constraint disclosure

The compatibility observation requires disclosure equivalent to:

- history completeness not documented;
- chronological order not documented;
- stable event identity not documented;
- stable event sequence not documented;
- provider-recorded time not documented;
- event-level actor identity not documented;
- event-level carrier identity not documented;
- duplicate and revision semantics not documented;
- pagination and truncation semantics not documented;
- retention and update latency not documented;
- temporal format and timezone unresolved;
- proof-of-delivery identity semantics unresolved;
- polling and webhook surface separation required.

This decision does not authorize an implementation-specific constraint tuple.

## Non-inference finding

The accepted observation requires none of the following prohibited inferences:

- physical carrier from reporting-source identity;
- event actor from aggregator identity;
- webhook values on polling events;
- webhook `Date` format on polling `date`;
- event identity from content or array position;
- chronology from response position;
- completeness from silence;
- duplicate or revision relationships from similarity;
- normalized delivery state from provider-native status;
- delivery correctness from proof-of-delivery references;
- planned-route topology from observed tracking events;
- globally unique shipment identity from source-local correlations;
- evidence attribution from Korea Post EMS or adjacent providers.

Finding: `PROHIBITED INFERENCE REQUIRED = NO`.

## Compatibility decision

The validated worksheet proposal is accepted at the research level:

- `canonical_projection_compatibility`: `observed`;
- observation strength: `bounded partial`;
- source: TracX SmartShip polling `SmartShipService.Tracking` only;
- collection: polling `tracking_history` only;
- complete canonical coverage: not established;
- production readiness: not established.

Accepted observation value:

> TracX SmartShip polling `SmartShipService.Tracking` prospectively supports
> a bounded `observed_route_event_history` projection through its
> `tracking_history` collection by preserving directly supported
> provider-native status and code evidence, unresolved polling `date` as raw
> temporal evidence, raw location evidence, and an explicitly owned
> source-local tracking correlation within Commerce AI-owned history
> provenance. Completeness remains `UNKNOWN`; response position carries no
> chronological meaning; stable event identity and sequence, provider-recorded
> time, event actor, physical carrier, pagination, duplicate and revision
> semantics, freshness, and proof-of-delivery identity semantics remain
> unresolved. Delivery WebHook evidence and `MultiTracking` assembly are
> excluded.

This is a research compatibility observation. It is not a verification of
shipment state, delivery outcome, provider quality, commercial suitability, or
production readiness.

## Authority boundary

This decision accepts only the research-level compatibility observation.

It does not authorize:

- mutation of `external_evidence_provider_evaluation_dossier.md`;
- projector implementation or implementation planning;
- production models, adapters, serializers, or API surfaces;
- package exports;
- ingress or projection registry mutation;
- network acquisition;
- API-key or OAuth-key use;
- raw payload collection or retention;
- persistence or caching;
- webhook ingestion;
- `MultiTracking` assembly;
- runtime activation or deployment;
- provider selection, ranking, recommendation, or verification;
- planned-route mutation;
- Korea Post EMS compatibility consequences;
- adjacent-source attribution;
- commit, tag, or push.

The current dossier record
`cb-ea4r6-tracx-smartship-006` therefore remains `unknown / None`.

## Gate result

- worksheet identity: `PASS`;
- source-identity separation: `PASS`;
- polling-surface boundary: `PASS`;
- direct field mapping: `PASS WITH EXPLICIT GAPS`;
- temporal non-inference: `PASS`;
- location and POD non-inference: `PASS`;
- canonical invariant review: `PASS FOR BOUNDED PARTIAL PROJECTION`;
- prohibited inference required: `NO`;
- research observation: `ACCEPTED`;
- accepted compatibility: `observed`;
- dossier mutation: `NOT AUTHORIZED`;
- existing dossier `unknown / None`: `UNCHANGED`;
- projector implementation: `NOT AUTHORIZED`;
- production and runtime mutation: `NONE`.

## Required next gate

The worksheet and this decision must undergo a joint read-only validation
before either artifact is sealed.

After successful joint validation, a separate sealing gate may be considered
for exactly these two research artifacts.

No dossier-mutation or projector-authorization request may be considered from
this decision alone. Such requests require later, separately authorized
boundaries after the worksheet and decision are jointly validated and sealed.
