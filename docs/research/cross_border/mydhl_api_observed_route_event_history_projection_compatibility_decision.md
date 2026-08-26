# MyDHL API Observed Route Event History Projection Compatibility Decision

## Document status

- Gate: `CB-EA5B-8V-4`
- Status: `research decision`
- Candidate: `candidate:shipping-landed-cost:mydhl-api`
- Product surface: DHL Express MyDHL API
- Inspected version: `3.3.1`
- Canonical target: `observed_route_event_history`
- Worksheet SHA-256:
  `f8449e31119c15027c7bda43e684c43dc2987958d7928926f5af54e059602b1f`
- Decision: `ACCEPTED AS BOUNDED STRONG-PARTIAL PROJECTION OBSERVATION`
- Dossier mutation: `not authorized`
- Production implementation: `not authorized`

## Decision question

Does the validated MyDHL API worksheet support a research-level observation that
the directly documented Tracking structures can be conservatively projected into
the sealed `observed_route_event_history` contract without prohibited inference?

## Inputs reviewed

The decision reviews:

1. `observed_route_event_history_canonical_contract_definition.md`;
2. `observed_route_event_history_first_wave_projection_compatibility_review_authorization_decision.md`;
3. `direct_registered_source_tracking_schema_sufficiency_review.md`;
4. `mydhl_api_observed_route_event_history_projection_compatibility_worksheet.md`;
5. `external_evidence_provider_evaluation_dossier.md`.

The worksheet was validated at 340 lines with SHA-256
`f8449e31119c15027c7bda43e684c43dc2987958d7928926f5af54e059602b1f`.

## Source identity finding

The evaluated subject is limited to:

- `candidate:shipping-landed-cost:mydhl-api`;
- DHL Express MyDHL API;
- inspected version `3.3.1`;
- base URL `https://express.api.dhl.com/mydhlapi`;
- `GET /shipments/{shipmentTrackingNumber}/tracking`; and
- `GET /tracking`.

DHL Shipment Tracking - Unified remains a separate API product. ShipStation V2
also remains a separate candidate. Neither source supplies evidence to resolve a
MyDHL gap.

Finding: `PASS`.

## Sufficiency and compatibility distinction

The direct-source review found MyDHL insufficient to establish the complete
canonical contract. The worksheet does not reverse that finding.

It evaluates whether directly documented values fit within the established
canonical representation of partial or unknown evidence, conditional temporal
normalization, source-local correlation, optional actors and relationships, and
explicit non-inference.

Finding: complete-contract insufficiency and bounded strong-partial compatibility
are consistent and may coexist.

## Accepted bounded projection

The decision accepts these research mappings:

- one response from one evaluated Tracking operation forms one immutable evidence
  snapshot;
- shipment-level and piece-level `events[]` remain distinct source scopes;
- a shipment or piece tracking number supplies source-local correlation;
- `typeCode` may remain `provider_event_code`;
- `description` may remain `raw_status_description`;
- remarks may remain source-local metadata;
- `serviceArea[].description` may remain raw location description;
- service-area codes may remain location metadata without facility inference;
- shipment-owned events may use `scope=SHIPMENT` with the supported reference;
- piece-owned events may use `scope=PIECE` with the supported reference; and
- mandatory history provenance must be supplied by the Commerce AI acquisition
  boundary in a future separately authorized implementation.

## Accepted temporal composition

A timezone-aware `occurred_at` may be composed only when event `date`, event
`time`, and event `GMTOffset` are all present, parseable under documented formats,
and semantically describe the same occurrence instant.

If any required component is absent, malformed, or unresolved:

- `occurred_at` remains `None`;
- directly supplied components may be preserved in `occurred_at_raw`;
- no timezone or UTC offset is inferred from location, account, carrier, request,
  or adjacent documentation; and
- the event must satisfy minimum content through another supported field.

`shipmentTimestamp`, request time, retrieval time, and evaluation time do not
become event occurrence or recorded time.

Finding: `CONDITIONAL TIMEZONE-AWARE COMPOSITION WITH RAW FALLBACK = ACCEPTED`.

## Accepted unknown and absent values

- completeness: `UNKNOWN`;
- ordering: `SOURCE_ORDER` only when returned order is preserved, otherwise
  `UNKNOWN`;
- chronological ordering: not established;
- stable provider event identity: `None`;
- provider-recorded time: `None`;
- event actor: absent;
- ambiguous event scope: `UNKNOWN`;
- source sequence: `None`;
- relationships: empty;
- pagination fields: `None`; and
- freshness: `None`.

Timestamp availability does not establish chronological response order or complete
history.

## Location, actor, and scope finding

`serviceArea` is accepted as bounded location evidence, but it does not by itself
establish:

- a physical facility;
- an event actor;
- a customs authority;
- jurisdiction or legal clearance;
- custody or title transfer; or
- a verified physical event site.

DHL Express product identity at history level does not automatically populate an
event actor. Shipment and piece scopes are used only when collection ownership and
the matching tracking reference are directly supported. Piece and package are not
aliases.

Finding: `PASS WITH NON-INFERENCE BOUNDARIES`.

## Non-inference finding

The accepted projection does not require:

- manufactured event identity;
- timezone inference;
- chronological sorting;
- completeness inference;
- normalized delivery-state assignment;
- actor, facility, custody, or customs inference;
- destructive deduplication, correction, or replacement;
- cross-response, polling, webhook, or page assembly;
- cross-provider identity resolution; or
- evidence attribution from DHL Shipment Tracking - Unified or ShipStation.

Finding: `PROHIBITED INFERENCE REQUIRED = NO`.

## Compatibility decision

The worksheet proposal is accepted at the research level:

- `canonical_projection_compatibility`: `observed`;
- observation strength: `strong partial`;
- source: MyDHL API version `3.3.1` Tracking operations only;
- complete canonical coverage: not established;
- production readiness: not established.

Accepted observation value:

> MyDHL API Tracking in inspected version `3.3.1` prospectively supports a
> bounded `observed_route_event_history` projection through shipment- and
> piece-level `events[]`, provider-native `typeCode` and description, conditional
> composition of event `date`, `time`, and `GMTOffset` into a timezone-aware
> occurrence instant with raw fallback, service-area location evidence, and
> shipment or piece tracking correlation within Commerce AI-owned history
> provenance. Completeness remains `UNKNOWN`; response order is not chronological
> by default; stable event identity, recorded time, event actor, duplicate,
> revision, pagination, assembly, and freshness semantics remain absent or
> unresolved and are not inferred.

## Authority boundary

This decision does not authorize:

- changing dossier record `cb-ea3b1-mydhl-006`;
- candidate admission, selection, ranking, preference, or verification;
- live API calls, credentials, or historical backfill;
- production models, adapters, projectors, serializers, registries, or endpoints;
- deployment or runtime activation; or
- adjacent-source attribution.

The current dossier value therefore remains `unknown / None`.

## Gate result

- worksheet integrity: `PASS`;
- source-identity separation: `PASS`;
- temporal composition boundary: `PASS`;
- service-area and scope non-inference: `PASS`;
- canonical invariant review: `PASS FOR BOUNDED STRONG-PARTIAL PROJECTION`;
- prohibited inference required: `NO`;
- research observation: `ACCEPTED`;
- accepted compatibility: `observed`;
- dossier mutation: `NOT AUTHORIZED`;
- existing dossier `unknown / None`: `UNCHANGED`;
- production implementation: `NOT AUTHORIZED`.

## Required next gate

The worksheet and this decision must be jointly validated and sealed before any
dossier-mutation request is considered. This decision does not reopen or modify
the separately sealed ShipStation observation.
