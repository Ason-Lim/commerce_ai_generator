# Frankfurter v2 Currency-Rate Projection Compatibility Worksheet

## Worksheet identity

- Step: `CB-EA4B-3`
- Protocol: `CB-EA4A-2`
- Evaluation subject: `candidate:currency:frankfurter-v2`
- Canonical target family: `currency_rate_evidence`
- Source relationship: `subject_supplied`
- Status: `pilot observation worksheet`
- Runtime authority: `None`
- Acquisition authority: `None`
- Adapter authority: `None`
- Projector authority: `None`
- Verification authority: `None`
- Provider-selection authority: `None`

## Scope

This worksheet applies the sealed internal observation protocol to one
evaluation subject and one canonical target family.

It does not compare Frankfurter v2 with another evaluation subject.

It does not authorize network acquisition, credentials, raw payload storage,
an adapter, a projector, canonical evidence construction, provider
registration, scoring, ranking, recommendation, selection, runtime use, or
transaction execution.

## Registered inspected sources

| source_id | source relationship | source type | source reference |
|---|---|---|---|
| `frankfurter-v2-docs` | `subject_supplied` | `official_documentation` | https://frankfurter.dev/ |
| `frankfurter-v2-openapi` | `subject_supplied` | `official_documentation` | https://api.frankfurter.dev/v2/openapi.json |

Both sources are supplied by the evaluation subject. Their inspection does
not establish verification, correctness, independence, trust, availability,
commercial entitlement, or authority.

## Documented output locator

The inspected documentation identifies:

- `GET /v2/rate/{base}/{quote}` for one currency pair;
- `GET /v2/rates` for rate collections;
- the OpenAPI `Rate` schema for documented successful rate output.

The `Rate` schema requires:

- `date`;
- `base`;
- `quote`;
- `rate`.

The OpenAPI schema describes `rate` as a number with an exclusive minimum of
zero.

The general documentation states that a rate is fetched and that monetary
conversion is performed separately by the consumer. The subject therefore
does not supply a Commerce AI conversion authority.

## Layer A — documented subject output shape

| Documented field | Documented meaning | Canonical relevance | Observation |
|---|---|---|---|
| `base` | Base currency code | `CurrencyPair.base_currency` | Documented |
| `quote` | Quote currency code | `CurrencyPair.quote_currency` | Documented |
| `rate` | Exchange-rate value greater than zero | `CurrencyRateEvidence.rate` | Documented |
| `date` | Date of the rate | Temporal provenance input | Documented |
| `providers`, when expanded | Contributing provider observations | Additional provenance input | Optional and conditional |

The documented single-pair route makes the rate direction explicit through
the ordered `base` and `quote` path parameters and the returned fields.

For prospective Commerce AI interpretation, the direction remains:

`1 base_currency = rate quote_currency`

No inverse-rate assumption is required for the documented single-pair
shape.

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

A documented successful `Rate` shape may support a future internal
`observed` evidence state, but this worksheet does not construct that
evidence or assign runtime state.

## Field-by-field canonical mapping

| Canonical requirement | Documented or internal source | Required bounded treatment | Gap status |
|---|---|---|---|
| Base currency | Documented `base` | Commerce AI `CurrencyPair` normalization | No blocking shape gap observed |
| Quote currency | Documented `quote` | Commerce AI `CurrencyPair` normalization | No blocking shape gap observed |
| Positive finite rate | Documented positive numeric `rate` | Parse through Commerce AI decimal normalization | No blocking shape gap observed |
| Evidence state | Commerce AI internal authority | Must not be copied from a provider field | No subject field required |
| Provenance identity | Registered source plus request/record reference | Construct only under separate authorization | No blocking shape gap for prospective construction |
| Evaluation context | Commerce AI evaluation input | Must not be manufactured from the rate response | No subject field required |
| Temporal input | Documented `date` | Preserve as date evidence; do not invent time or timezone | Freshness remains unresolved |
| Freshness | Commerce AI internal authority | Leave absent or unknown unless timezone-aware evidence and policy exist | Non-blocking because freshness is optional |

## Required transformations

A future separately authorized subject-specific adapter would require these
bounded transformations:

1. normalize `base` and `quote` through `CurrencyPair`;
2. parse `rate` through Commerce AI decimal normalization;
3. preserve the documented rate direction;
4. construct Commerce AI evidence, provenance, and context envelopes from
   their own authorized inputs;
5. preserve `date` without inventing a time or timezone;
6. leave freshness absent or unknown unless sufficient temporal evidence and
   a separately authorized freshness policy are available.

These transformations are described only. They are not implemented or
executed by this worksheet.

## Unresolved gaps and limitations

- The documented `date` is not a timezone-aware timestamp.
- Freshness therefore cannot be determined from the date alone by the
  existing Commerce AI freshness evaluator.
- Provider attribution is conditional when blended rates are used.
- A provider filter or expanded provider attribution does not independently
  verify the underlying rate.
- Public API availability does not establish production SLA, entitlement,
  legal reuse for every underlying dataset, or operational readiness.
- No live response has been acquired or inspected under this protocol.
- No adapter behavior or error-handling behavior has been validated.

These limitations block freshness claims, verification, runtime readiness,
and adoption claims. They do not block the narrower documented output-shape
observation because freshness is optional in `CurrencyRateEvidence`.

## Protocol conclusion

### Proposed dossier state

`observed`

### Proposed dossier observation value

Frankfurter v2 documents a `Rate` output with required `date`, `base`,
`quote`, and positive `rate` fields, supporting prospective subject-specific
interpretation into `currency_rate_evidence` through `CurrencyPair`
normalization, decimal rate parsing, and Commerce AI-owned evidence,
provenance, and evaluation-context envelopes; freshness remains absent or
unknown unless separately sufficient timezone-aware temporal evidence and
policy are available.

## Meaning of the proposed conclusion

The proposed `observed` state is a subject-local documentation-shape
observation only.

It is not:

- `verified`;
- a compatibility score or grade;
- a provider comparison;
- an adoption recommendation;
- provider selection;
- adapter authorization;
- projector authorization;
- acquisition authority;
- runtime authority;
- evidence of quote accuracy;
- evidence of transaction suitability.

## Dossier mutation boundary

This worksheet does not modify the existing dossier evidence record.

The Frankfurter v2 `canonical_projection_compatibility` record must remain
`unknown` with literal `None` until this worksheet is separately reviewed,
committed, and sealed, and a later exact-scope dossier mutation is
authorized.
