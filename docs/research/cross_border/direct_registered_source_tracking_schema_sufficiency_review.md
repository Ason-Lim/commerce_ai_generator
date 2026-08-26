# Direct Registered-Source Tracking Schema Sufficiency Review

## Document status

- Status: `research observation review`
- Review ID: `CB-EA4R-3`
- Review date: `2026-08-26`
- Scope: direct registered-source tracking schema sufficiency
- Authority: `research-only`
- Production model mutation: `not authorized`
- Canonical contract mutation: `not authorized`
- Dossier mutation: `none`
- New subject admission: `not authorized`
- Provider decision mutation: `none`

## Review question

Do the directly registered tracking surfaces of:

1. ShipStation V2 `get_tracking_log`; and
2. MyDHL API Tracking

provide sufficient source-local schema evidence to support preparation of a
future Commerce AI `observed_route_event_history` contract?

## Registered-source boundary

This review is strictly limited to:

| Evaluation subject | Direct registered source |
|---|---|
| `candidate:shipping:shipstation-api` | ShipStation V2 `get_tracking_log` |
| `candidate:shipping-landed-cost:mydhl-api` | MyDHL API Tracking response schema |

The following adjacent sources are outside the evidence boundary:

- ShipStation API formerly ShipEngine v1;
- DHL Shipment Tracking – Unified;
- any other ShipStation, ShipEngine, DHL, carrier, aggregator, or third-party
  tracking schema.

A shared company, brand, carrier network, product lineage, documentation
navigation surface, or overlapping carrier coverage does not establish source
identity, alias identity, or automatic evidence attribution.

No field or semantic rule from an adjacent source is attributed to either
registered source in this review.

## Canonical boundary

The current production canonical contract is `ShippingRouteEvidence`.

Its semantic focus is prospective `planned_route_topology`. It does not contain
an authorized canonical event-history contract or canonical fields for:

- tracking event identity;
- event sequence;
- provider event code;
- event status;
- occurrence timestamp;
- recorded or received timestamp;
- event timezone or UTC offset;
- event location or facility;
- partial-history state;
- duplicate, correction, or revision state.

`observed_route_event_history` remains a future canonical-contract candidate
only.

This review does not create a target family, enum, dataclass, field, adapter,
projector, provider mapping, registry entry, scoring rule, selection rule, or
runtime behavior.

## Observation-state meanings

- `observed`: directly documented by the registered source.
- `partially observed`: part of the required structure is directly documented,
  but the complete bounded meaning is not established.
- `not observed`: the inspected registered source does not directly establish
  the required field or semantic rule.
- `inaccessible`: the required official schema surface could not be directly
  inspected because of access or publication restrictions.

`not observed` does not mean that a provider never possesses or returns the
information. It means that this review does not have sufficient direct
registered-source evidence to assert it.

## ShipStation V2 source identity

- Evaluation subject: `candidate:shipping:shipstation-api`
- Product surface: ShipStation V2 API
- Subject base URL: `https://api.shipstation.com/v2`
- Operation: `get_tracking_log`
- Official reference:
  `https://docs.shipstation.com/apis/openapi/tracking/get_tracking_log`

The documentation version selector identifies ShipStation V2 separately from
ShipStation API formerly ShipEngine and ShipStation V1.

The ShipEngine surface is not used as a substitute source.

## ShipStation V2 direct observation matrix

| Requirement | State | Direct observation |
|---|---|---|
| Tracking history or event collection | `observed` | The response documents `events[]` as events occurring during the lifetime of the tracking number. |
| Event identity or event code | `partially observed` | `events[].status_code`, `carrier_status_code`, and `carrier_detail_code` are documented, but no independent stable event identity is established. |
| Raw status and status description | `observed` | Provider or carrier status-code fields and `carrier_status_description` are documented. |
| Event occurrence timestamp | `not observed` | An event-level occurrence-time field and its precise semantics were not directly established in the inspected source. |
| Timezone or UTC offset | `not observed` | No event-level timezone or UTC-offset contract was directly established. |
| Recorded or received timestamp | `not observed` | No provider-recorded, received, ingested, or observation timestamp was directly established. |
| Event location and structure | `partially observed` | Event location components including `country_code` and `company_name` are documented, but a complete canonical location structure is not established. |
| Carrier identity and tracking number | `observed` | The operation is correlated through documented `carrier_code` and `tracking_number` inputs. |
| Source record or request correlation identifier | `partially observed` | The tracking number supplies request correlation, but no separate stable source-record or request identifier was established. |
| Chronological ordering guarantee | `not observed` | No ordering guarantee was directly established. |
| Completeness or partial-history indication | `not observed` | No complete-history or partial-history indicator was directly established. |
| Duplicate semantics | `not observed` | No duplicate-event contract was directly established. |
| Correction or revision semantics | `not observed` | No correction, replacement, or revision contract was directly established. |
| Estimated event versus occurred event | `partially observed` | Actual-delivery information is documented separately, but a complete event-level estimated-versus-occurred classification is not established. |
| Freshness or retrieval timestamp | `not observed` | No retrieval-time or evidence-freshness field was directly established. |

## ShipStation V2 sufficiency finding

The registered source directly establishes an event collection and useful
provider-native status, description, location, carrier, and tracking
references.

It does not directly establish the temporal, ordering, completeness,
deduplication, correction, revision, or freshness semantics required for a
bounded canonical event-history contract.

Result:

- structural reuse potential: `partial`;
- canonical contract sufficiency: `insufficient`;
- canonical projection compatibility: `unknown`;
- canonical projection value: `None`.

## MyDHL API source identity

- Evaluation subject: `candidate:shipping-landed-cost:mydhl-api`
- Product surface: DHL Express MyDHL API
- Inspected version: `3.3.1`
- Production base URL: `https://express.api.dhl.com/mydhlapi`
- Tracking operations:
  - `GET /shipments/{shipmentTrackingNumber}/tracking`;
  - `GET /tracking`.
- Official product reference:
  `https://developer.dhl.com/api-reference/dhl-express-mydhl-api`
- Official OpenAPI:
  `https://developer.dhl.com/sites/default/files/2026-07/dpdhl-express-api-3.3.1.yaml`

DHL Shipment Tracking – Unified is not used as a substitute source.

## MyDHL API direct observation matrix

| Requirement | State | Direct observation |
|---|---|---|
| Tracking history or event collection | `observed` | The Tracking response contains shipment-level and piece-level `events[]`. |
| Event identity or event code | `partially observed` | Each event may contain `typeCode`, but no independent stable event identifier is documented. |
| Raw status and status description | `observed` | Events contain provider-native `typeCode` and `description`; remarks may also be returned. |
| Event occurrence timestamp | `observed` | Events contain separate `date` and `time` fields. |
| Timezone or UTC offset | `observed` | Events may contain `GMTOffset`; the documentation identifies a request option for returning the offset per event or checkpoint. |
| Recorded or received timestamp | `not observed` | `shipmentTimestamp` exists, but its documentation does not establish provider-recorded, received, or ingestion-time semantics. |
| Event location and structure | `observed` | Event `serviceArea[]` contains structured `code` and `description` fields. |
| Carrier identity and tracking number | `partially observed` | Shipment and piece tracking identifiers are documented; DHL Express is the source product, but no event-level carrier-identity field is established. |
| Source record or request correlation identifier | `partially observed` | `shipmentTrackingNumber` and piece `trackingNumber` supply shipment correlation, but no separate request-correlation identifier is established. |
| Chronological ordering guarantee | `not observed` | The example is sequentially presented, but no ordering guarantee is documented. |
| Completeness or partial-history indication | `not observed` | No complete-history or partial-history indicator is documented. |
| Duplicate semantics | `not observed` | No duplicate-event contract is documented. |
| Correction or revision semantics | `not observed` | No correction, replacement, or revision contract is documented. |
| Estimated event versus occurred event | `observed` | Occurred `events[]` are structurally separate from `estimatedDeliveryDate`. |
| Freshness or retrieval timestamp | `not observed` | No response-retrieval or observation timestamp is documented as evidence freshness. |

## MyDHL API sufficiency finding

The registered source directly establishes:

- shipment-level and piece-level event collections;
- provider-native event codes and descriptions;
- occurrence date and time;
- optional GMT offset;
- structured service-area location;
- shipment and piece tracking references;
- structural separation between occurred events and estimated delivery.

It does not directly establish:

- provider-recorded or received time;
- stable event identity;
- chronological-ordering guarantees;
- complete or partial-history state;
- duplicate, correction, or revision semantics;
- retrieval-time freshness.

Result:

- structural reuse potential: `strong partial`;
- canonical contract sufficiency: `insufficient`;
- canonical projection compatibility: `unknown`;
- canonical projection value: `None`.

## Cross-source comparison

| Contract concern | ShipStation V2 | MyDHL API |
|---|---|---|
| Event collection | Observed | Observed |
| Provider event code | Partially observed | Partially observed |
| Status description | Observed | Observed |
| Occurrence date and time | Not observed | Observed |
| Timezone or UTC offset | Not observed | Observed |
| Structured event location | Partially observed | Observed |
| Shipment correlation | Observed | Observed |
| Stable event identity | Not observed | Not observed |
| Recorded or received time | Not observed | Not observed |
| Ordering guarantee | Not observed | Not observed |
| Complete or partial history | Not observed | Not observed |
| Duplicate semantics | Not observed | Not observed |
| Correction or revision semantics | Not observed | Not observed |
| Estimated versus occurred distinction | Partially observed | Observed |
| Retrieval freshness | Not observed | Not observed |

## Reuse decision

The two registered sources may be reused as bounded research precedents for:

- an event collection;
- preservation of provider-native event codes and descriptions;
- shipment and tracking correlation;
- occurrence date, time, and offset where directly supplied;
- structured event location where directly supplied;
- separation of estimated delivery from occurred events where directly
  supplied.

They are not sufficient to establish canonical rules for:

- stable event identity;
- canonical event ordering;
- out-of-order handling;
- complete and partial history;
- deduplication;
- correction and revision;
- occurrence time versus recorded time;
- evidence freshness;
- event-level provenance across carriers or network participants.

Provider fields must not be copied directly into future canonical fields without
a separately authorized normalization and semantic contract.

## Review decision

ShipStation V2 `get_tracking_log` and the MyDHL API Tracking response provide
direct evidence of tracking-event collections and portions of the field
structure relevant to a future `observed_route_event_history` contract.

MyDHL provides the stronger temporal and location structure.

Neither registered source provides sufficient direct evidence for the complete
canonical contract.

Therefore:

- direct registered-source review: `complete`;
- source-identity separation: `pass`;
- adjacent-source attribution: `denied`;
- structural reuse potential: `partial`;
- canonical contract sufficiency: `insufficient`;
- canonical projection compatibility: `unknown`;
- canonical projection value: `None`;
- new subject admission: `not authorized`;
- production model mutation: `none`;
- canonical contract mutation: `none`;
- dossier mutation: `none`.

## Required future integration gate

The next research gate may integrate this sealed review with:

- the internal precedent findings from `CB-EA4Q-2`;
- Korea Post EMS;
- TracX SmartShip;
- Fassto FMS;
- Delivered Korea.

That integration must evaluate contract readiness without:

- merging planned-route and observed-event evidence;
- attributing destination-carrier events to another provider without direct
  provenance;
- treating a tracking identifier as globally unique canonical identity;
- converting provider status codes directly into canonical event status;
- treating example ordering as an ordering guarantee;
- treating an event collection as complete history;
- creating or modifying a production canonical contract.

## Non-authorizations

This review does not authorize:

- source acquisition;
- credentials or live API calls;
- raw payload retention;
- a canonical target family;
- production fields or enums;
- adapters or projectors;
- provider selection;
- scoring or ranking;
- recommendation;
- transaction execution;
- dossier mutation.
