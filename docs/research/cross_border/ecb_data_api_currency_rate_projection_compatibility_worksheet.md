# ECB Data API Currency-Rate Projection Compatibility Worksheet

## Worksheet identity

- Step: `CB-EA4C-3`
- Protocol: `CB-EA4A-2`
- Evaluation subject: `candidate:currency:ecb-data-api`
- Canonical target family: `currency_rate_evidence`
- Source relationship: `subject_supplied`
- Status: `bounded observation worksheet`
- Runtime authority: `None`
- Acquisition authority: `None`
- Adapter authority: `None`
- Projector authority: `None`
- Verification authority: `None`
- Provider-selection authority: `None`

## Scope

This worksheet applies the sealed internal observation protocol to one
evaluation subject and one canonical target family.

It does not compare the ECB Data API with another evaluation subject.

It does not authorize network acquisition, credentials, raw payload storage,
an adapter, a projector, canonical evidence construction, provider
registration, scoring, ranking, recommendation, selection, runtime use, or
transaction execution.

## Registered inspected sources

| source_id | source relationship | source type | source reference |
|---|---|---|---|
| `ecb-data-portal-api-data` | `subject_supplied` | `official_documentation` | https://data.ecb.europa.eu/help/api/data |
| `ecb-exr-dataflow-structure` | `subject_supplied` | `official_documentation` | https://data.ecb.europa.eu/data/datasets/EXR/structure |
| `ecb-data-portal-api-data-examples` | `subject_supplied` | `official_documentation` | https://data.ecb.europa.eu/help/api/data-examples |
| `ecb-data-portal-api-content-negotiation` | `subject_supplied` | `official_documentation` | https://data.ecb.europa.eu/help/api/content-negotiation |
| `ecb-data-portal-api-overview` | `subject_supplied` | `official_documentation` | https://data.ecb.europa.eu/help/api/overview |

The source identifiers above are worksheet-local correlation references. They
do not create provider identities, canonical registry entries, or runtime
authority.

All inspected sources are supplied by the evaluation subject. Their
inspection does not establish verification, correctness, independence,
trust, availability, commercial entitlement, or authority.

## Documented output locator

The inspected documentation identifies the `EXR` exchange-rate dataflow and
SDMX REST data queries that combine a dataflow reference with an ordered
series key.

The documented example key:

`D.USD.EUR.SP00.A`

contains these ordered series dimensions:

1. `FREQ`;
2. `CURRENCY`;
3. `CURRENCY_DENOM`;
4. `EXR_TYPE`;
5. `EXR_SUFFIX`.

The EXR structure identifies:

- `CURRENCY` as the currency whose value is measured;
- `CURRENCY_DENOM` as the denominator or base currency;
- `TIME_PERIOD` as the observation period;
- `OBS_VALUE` as the observation value;
- `OBS_STATUS` as a statistical observation-status attribute.

The API supports multiple representations through content negotiation.
Representation-specific layouts must not change the semantic direction
defined by the EXR data structure.

## Layer A — documented subject output shape

| Documented field or dimension | Documented meaning | Canonical relevance | Observation |
|---|---|---|---|
| `CURRENCY_DENOM` | Denominator or base currency | `CurrencyPair.base_currency` | Documented |
| `CURRENCY` | Currency measured against the denominator | `CurrencyPair.quote_currency` | Documented |
| `OBS_VALUE` | Exchange-rate observation value | `CurrencyRateEvidence.rate` | Field documented; positive finite constraint not established |
| `TIME_PERIOD` | Observation period | Temporal provenance input | Documented |
| `OBS_STATUS` | Statistical status of the observation | Estimate or observation-status context only | Documented but not a Commerce AI evidence state |
| `EXR` dataflow plus ordered series key | Dataset and series identity | Prospective provenance input | Documented |
| Requested representation | SDMX or CSV response representation | Parsing context | Documented and representation-dependent |

The prospective Commerce AI direction is:

`1 CURRENCY_DENOM = OBS_VALUE CURRENCY`

Therefore the documented key `D.USD.EUR.SP00.A` prospectively corresponds to:

`1 EUR = OBS_VALUE USD`

The ordered key must not be copied positionally into
`CurrencyPair(base_currency, quote_currency)`. The subject-specific mapping
must assign `CURRENCY_DENOM` to `base_currency` and `CURRENCY` to
`quote_currency`.

No inverse-rate calculation is authorized or required for that documented
direction.

## Layer B — Commerce AI internal envelope authority

The subject does not supply Commerce AI canonical objects.

Commerce AI retains exclusive authority for:

- constructing `CurrencyPair`;
- constructing `CrossBorderEvidence`;
- assigning `EvidenceState`;
- constructing `EvidenceProvenance`;
- supplying `CrossBorderEvaluationContext`;
- evaluating `EvidenceFreshness`;
- constructing `CurrencyRateEvidence`;
- deciding whether any future adapter is authorized.

`OBS_STATUS` is an ECB statistical attribute. It must not be copied directly
into Commerce AI `EvidenceState`.

The presence of a documented `OBS_VALUE` does not authorize Commerce AI to
construct evidence when the value fails the canonical positive finite rate
invariant.

## Field-by-field canonical mapping

| Canonical requirement | Documented or internal source | Required bounded treatment | Gap status |
|---|---|---|---|
| Base currency | Documented `CURRENCY_DENOM` | Normalize through `CurrencyPair.base_currency` | No blocking shape gap observed |
| Quote currency | Documented `CURRENCY` | Normalize through `CurrencyPair.quote_currency` | No blocking shape gap observed |
| Rate direction | EXR dimension semantics | Preserve `1 CURRENCY_DENOM = OBS_VALUE CURRENCY` | No blocking direction gap observed |
| Positive finite rate | Documented `OBS_VALUE` plus Commerce AI invariant | Decimal parsing may validate a value, but registered documentation does not establish a positive finite output constraint | Blocking documentation gap |
| Evidence state | Commerce AI internal authority | Must not be copied from `OBS_STATUS` or another subject field | No subject field required |
| Statistical status | Documented `OBS_STATUS` | Preserve separately if later authorized; do not reinterpret as `EvidenceState` | Non-blocking semantic separation required |
| Provenance identity | Registered source, `EXR` dataflow, series key, and observation reference | Construct only under separate authorization | No blocking shape gap for prospective construction |
| Evaluation context | Commerce AI evaluation input | Must not be manufactured from an ECB response | No subject field required |
| Temporal input | Documented `TIME_PERIOD` | Preserve without inventing time or timezone | Freshness remains unresolved |
| Freshness | Commerce AI internal authority | Leave absent or unknown unless timezone-aware evidence and policy exist | Non-blocking because freshness is optional |
| Representation | Registered content-negotiation documentation | Use a representation-specific parser if later authorized | No generic parser or projector authorized |

## Required transformations

A future separately authorized subject-specific adapter would require these
bounded transformations:

1. identify the `EXR` dataflow and the applicable ordered series-key structure;
2. map `CURRENCY_DENOM` to `CurrencyPair.base_currency`;
3. map `CURRENCY` to `CurrencyPair.quote_currency`;
4. parse `OBS_VALUE` through Commerce AI decimal normalization;
5. reject non-finite, zero, or negative values rather than manufacturing rate
   evidence;
6. preserve the documented rate direction without inversion;
7. preserve `TIME_PERIOD` without inventing a time or timezone;
8. keep `OBS_STATUS` distinct from Commerce AI `EvidenceState`;
9. construct Commerce AI evidence, provenance, and evaluation-context
   envelopes only from their separately authorized inputs;
10. leave freshness absent or unknown unless sufficient timezone-aware
    temporal evidence and a separately authorized freshness policy exist;
11. use a subject-specific, representation-specific parser rather than a
    generic projector.

These transformations are described only. They are not implemented or
executed by this worksheet.

## State and value semantic alignment

The canonical `CurrencyRateEvidence` contract requires:

- `UNKNOWN` evidence to carry no rate;
- every evidence-bearing state to carry a rate;
- every carried rate to be a valid, positive, finite decimal value.

The ECB `OBS_STATUS` attribute describes statistical observation status. It
does not assign Commerce AI evidence authority and does not satisfy the
canonical evidence-state requirement.

A future subject-specific parser could reject an invalid `OBS_VALUE`, but that
runtime validation capability does not establish that the subject
documentation guarantees a positive finite output value.

## Unresolved gaps and limitations

- The registered inspected documentation identifies `OBS_VALUE` but does not
  establish a positive finite constraint for all applicable documented
  outputs or representations.
- Commerce AI validation cannot be substituted for missing subject
  documentation when recording projection compatibility.
- `TIME_PERIOD` does not by itself establish a timezone-aware evidence
  timestamp.
- Freshness therefore remains absent or unknown.
- `OBS_STATUS` requires semantic separation from Commerce AI `EvidenceState`.
- Multiple representations require representation-specific parsing.
- No live response has been acquired or inspected under this protocol.
- No schema payload, raw response, adapter behavior, or error-handling
  behavior has been validated.
- Public documentation does not establish production SLA, entitlement,
  acceptable-use terms, quote accuracy, transaction suitability, or
  operational readiness.

The missing documented positive finite constraint blocks an `observed`
compatibility conclusion under the sealed protocol.

## Protocol conclusion

### Proposed dossier state

`unknown`

### Proposed dossier observation value

`None`

### Reason outside the observation value

The documented EXR dataflow supplies prospective base-currency,
quote-currency, rate-value, observation-period, and series-identity inputs,
but the registered inspected documentation does not establish that
`OBS_VALUE` satisfies the mandatory positive finite rate invariant across the
applicable documented outputs. The conclusion therefore depends on
unsupported documentation and must remain `unknown` with literal `None`.

## Meaning of the proposed conclusion

The proposed `unknown` state records a bounded unresolved documentation gap.

It does not mean that:

- ECB publishes zero, negative, or non-finite exchange rates;
- ECB data is incorrect;
- the ECB Data API is incompatible;
- a future valid response could not be parsed;
- a provider comparison has been performed;
- another evaluation subject is preferred;
- runtime use has been rejected.

It also does not establish:

- `observed` compatibility;
- `verified` compatibility;
- a compatibility score or grade;
- an adoption recommendation;
- provider selection;
- adapter authorization;
- projector authorization;
- acquisition authority;
- runtime authority;
- quote accuracy;
- transaction suitability.

## Boundary review

This worksheet contains no:

- score;
- weight;
- rank;
- provider comparison;
- recommendation;
- selection;
- network client;
- credential;
- live acquisition;
- raw payload storage;
- adapter implementation;
- projector implementation;
- runtime import;
- package-level public export.

The worksheet remains research documentation only.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The ECB Data API `canonical_projection_compatibility` record remains
`unknown` with literal `None`.

A later review, commit, or seal of this worksheet does not itself authorize a
dossier mutation. Any future change would require separately sufficient
registered documentation, a separately reviewed conclusion, and a later
exact-scope authorization.
