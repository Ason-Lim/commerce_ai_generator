# CB-EA3B-1 External Evidence Provider Evaluation Dossier

## Document identity

| Field | Value |
|---|---|
| Document ID | CB-EA3B-1 |
| Status | RESEARCH EVIDENCE — INITIAL |
| Retrieved date | 2026-08-25 |
| Repository baseline | `4eaf78ffa619b32578dbae064f26a499980461d9` |
| Storage authority | Research documentation only |
| Runtime authority | None |
| Provider selection authority | None |

## Purpose

This dossier records bounded observations from external-evidence
provider candidate sources for later provider-neutral evaluation.

It does not establish a provider registry, adapter, client, credential,
network acquisition path, runtime authority, score, weight, rank,
comparison result, recommendation, or provider selection.

## Contract alignment

Each future evidence record must remain expressible through:

- `ExternalEvidenceProviderEvaluationSubject`
- `ExternalEvidenceProviderEvaluationDimension`
- `ExternalEvidenceProviderEvaluationSourceRelationship`
- `CrossBorderEvidence`
- `EvidenceProvenance`

The evaluation subject and the evidence source remain distinct.

An official page supplied by an evaluation subject is recorded as
`subject_supplied`. That relationship does not establish verification,
correctness, independence, trust, or authority.

A documented claim observed on such a page is normally `observed`, not
`verified`.

When a claim cannot be supported by the inspected source, its evidence
state is `unknown` and its observation value is `None`. Unknown evidence
must not manufacture a replacement value.

Values such as `0`, `False`, and the empty string remain valid observed
values when evidence exists.

## Canonical evaluation dimensions

- `evidence_kind_coverage`
- `geographic_coverage`
- `provenance_traceability`
- `temporal_evidence`
- `estimate_status_disclosure`
- `canonical_projection_compatibility`
- `operational_constraints`
- `access_security_requirements`
- `commercial_constraints`

## Official source register

The identifiers below are opaque evaluation correlation references.
They do not create canonical provider identities or registry entries.

### Currency evidence

| subject_ref | Evidence source | Source relationship | Official source reference |
|---|---|---|---|
| `candidate:currency:ecb-data-api` | ECB Data Portal API documentation | `subject_supplied` | https://data.ecb.europa.eu/help/api/data |
| `candidate:currency:ecb-data-api` | ECB Exchange Rates dataflow structure | `subject_supplied` | https://data.ecb.europa.eu/data/datasets/EXR/structure |
| `candidate:currency:ecb-data-api` | ECB Data Portal API data examples | `subject_supplied` | https://data.ecb.europa.eu/help/api/data-examples |
| `candidate:currency:ecb-data-api` | ECB Data Portal API content negotiation | `subject_supplied` | https://data.ecb.europa.eu/help/api/content-negotiation |
| `candidate:currency:ecb-data-api` | ECB Data Portal API overview | `subject_supplied` | https://data.ecb.europa.eu/help/api/overview |
| `candidate:currency:frankfurter-v2` | Frankfurter v2 documentation | `subject_supplied` | https://frankfurter.dev/ |
| `candidate:currency:frankfurter-v2` | Frankfurter v2 OpenAPI specification | `subject_supplied` | https://api.frankfurter.dev/v2/openapi.json |

### Shipping-route evidence

| subject_ref | Evidence source | Source relationship | Official source reference |
|---|---|---|---|
| `candidate:shipping:shippo-api` | Shippo API documentation | `subject_supplied` | https://docs.goshippo.com/api-reference/overview |
| `candidate:shipping:easypost-api` | EasyPost API documentation | `subject_supplied` | https://www.easypost.com/guides/getting-started |
| `candidate:shipping-landed-cost:mydhl-api` | DHL Express MyDHL API documentation | `subject_supplied` | https://developer.dhl.com/api-reference/dhl-express-mydhl-api |

### Regulatory evidence

| subject_ref | Evidence source | Source relationship | Official source reference |
|---|---|---|---|
| `candidate:regulatory:govuk-trade-tariff-api` | UK Trade Tariff API service | `subject_supplied` | https://api.trade-tariff.service.gov.uk/ |
| `candidate:regulatory:eu-access2markets` | European Commission Access2Markets | `subject_supplied` | https://trade.ec.europa.eu/access-to-markets/en/home |
| `candidate:regulatory:korea-customs-unipass` | Korea Customs Service UNI-PASS | `subject_supplied` | https://unipass.customs.go.kr/ |
| `candidate:regulatory:usitc-hts` | USITC Harmonized Tariff Schedule | `subject_supplied` | https://hts.usitc.gov/ |

The `candidate:regulatory:usitc-hts` reference intentionally does not
use `us-cbp-hts`. The inspected HTS publication source is USITC.
No CBP identity, relationship, verification, or acquisition authority
is inferred from that source.

### Landed-cost-component evidence

| subject_ref | Evidence source | Source relationship | Official source reference |
|---|---|---|---|
| `candidate:landed-cost:zonos-api` | Zonos Landed Cost documentation | `subject_supplied` | https://zonos.com/docs/supply-chain/landed-cost/get-started |
| `candidate:landed-cost:ups-api` | UPS Landed Cost API documentation | `subject_supplied` | https://developer.ups.com/api/reference?tag=Landed-Cost |

## Initial unresolved boundaries

The following remain unresolved until supported by specific evidence
records:

- actual provider availability for a Commerce AI deployment;
- contractual permission for storage, reuse, display, or comparison;
- production credentials and authorization;
- commercial pricing and negotiated terms;
- service-level guarantees;
- exact geographic availability for a prospective account;
- canonical projection compatibility;
- runtime integration feasibility;
- correctness of subject-supplied claims;
- provider suitability or selection.

Each unresolved item remains `unknown` with value `None`. Absence of
evidence is not evidence of absence.

## Currency candidate evidence records

### Record conventions

For the records below:

- `source_relationship` is `subject_supplied`.
- `retrieved_at` is `2026-08-25`.
- `observed` records reproduce bounded claims found in the cited source.
- `unknown` records carry the literal value `None`.
- No record has `verified` state.
- Canonical projection compatibility remains unknown until a separate
  internal observation is authorized and performed.

### `candidate:currency:ecb-data-api`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-ecb-001` | `evidence_kind_coverage` | `observed` | ECB Data Portal exposes exchange-rate datasets through its data API. | `ecb-data-portal` | `official_documentation` | https://data.ecb.europa.eu/help/api/data |
| `cb-ea3b1-ecb-002` | `geographic_coverage` | `unknown` | `None` | `ecb-data-portal` | `official_documentation` | https://data.ecb.europa.eu/help/api/data |
| `cb-ea3b1-ecb-003` | `provenance_traceability` | `observed` | API requests identify a dataflow and series key; metadata references may accompany data. | `ecb-data-portal` | `official_documentation` | https://data.ecb.europa.eu/help/api/data |
| `cb-ea3b1-ecb-004` | `temporal_evidence` | `observed` | The API supports dated time-series observations and period-constrained data requests. | `ecb-data-portal` | `official_documentation` | https://data.ecb.europa.eu/help/api/data |
| `cb-ea3b1-ecb-005` | `estimate_status_disclosure` | `observed` | ECB describes its euro reference rates as reference information and discourages using them for transaction purposes. | `ecb-euro-reference-rates` | `official_documentation` | https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html |
| `cb-ea3b1-ecb-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-ecb-007` | `operational_constraints` | `observed` | Use requires an SDMX REST data query identifying the dataflow, key, and requested representation. | `ecb-data-portal` | `official_documentation` | https://data.ecb.europa.eu/help/api/data |
| `cb-ea3b1-ecb-008` | `access_security_requirements` | `unknown` | `None` | `ecb-data-portal` | `official_documentation` | https://data.ecb.europa.eu/help/api/overview |
| `cb-ea3b1-ecb-009` | `commercial_constraints` | `unknown` | `None` | `ecb-data-portal` | `official_documentation` | https://data.ecb.europa.eu/help/api/overview |

The geographic record remains unknown because the inspected API page
does not establish a single unconditional geographic or currency
coverage set for every exchange-rate query.

The access-security record remains unknown because observing a public
documentation or data endpoint does not establish the complete
production access, security, availability, or acceptable-use contract.

### `candidate:currency:frankfurter-v2`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-frankfurter-001` | `evidence_kind_coverage` | `observed` | Frankfurter v2 exposes current and historical currency exchange-rate data. | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |
| `cb-ea3b1-frankfurter-002` | `geographic_coverage` | `observed` | The subject states that v2 tracks rates from 84 central banks and covers 201 currencies. | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |
| `cb-ea3b1-frankfurter-003` | `provenance_traceability` | `observed` | The API exposes provider identities and permits requests to be constrained to a named provider. | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |
| `cb-ea3b1-frankfurter-004` | `temporal_evidence` | `observed` | The subject states that daily and historical exchange-rate data extends back to 1948. | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |
| `cb-ea3b1-frankfurter-005` | `estimate_status_disclosure` | `unknown` | `None` | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |
| `cb-ea3b1-frankfurter-006` | `canonical_projection_compatibility` | `observed` | Frankfurter v2 documents a `Rate` output with required `date`, `base`, `quote`, and positive `rate` fields, supporting prospective subject-specific interpretation into `currency_rate_evidence` through `CurrencyPair` normalization, decimal rate parsing, and Commerce AI-owned evidence, provenance, and evaluation-context envelopes; freshness remains absent or unknown unless separately sufficient timezone-aware temporal evidence and policy are available. | `commerce-ai-evaluation` | `internal_research_boundary` | [CB-EA4B-3 worksheet](frankfurter_v2_currency_rate_projection_compatibility_worksheet.md) |
| `cb-ea3b1-frankfurter-007` | `operational_constraints` | `observed` | The public v2 service uses an HTTPS API and the project may also be self-hosted. | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |
| `cb-ea3b1-frankfurter-008` | `access_security_requirements` | `observed` | The subject states that the public API requires no API key or account. | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |
| `cb-ea3b1-frankfurter-009` | `commercial_constraints` | `observed` | The public API is described as free and the project as open source; quotas, SLA, and deployment-specific terms remain unresolved. | `frankfurter-v2-docs` | `official_documentation` | https://frankfurter.dev/ |

The numeric coverage and historical-depth statements remain
subject-supplied observations. They are not independently verified by
this dossier.

## Shipping candidate evidence records

### Record conventions

For the records below:

- `source_relationship` is `subject_supplied`.
- `retrieved_at` is `2026-08-25`.
- `observed` records reproduce bounded claims found in the cited source.
- `unknown` records carry the literal value `None`.
- No record has `verified` state.
- Canonical projection compatibility remains unknown until a separate
  internal observation is authorized and performed.
- Carrier, route, account, service, and price availability is not
  generalized beyond the cited documentation.

### `candidate:shipping:shippo-api`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-shippo-001` | `evidence_kind_coverage` | `observed` | Shippo documents API resources for shipments, rates, transactions, refunds, customs items, and customs declarations. | `shippo-api-overview` | `official_documentation` | [https://docs.goshippo.com/api-reference/overview](https://docs.goshippo.com/api-reference/overview) |
| `cb-ea3b1-shippo-002` | `geographic_coverage` | `unknown` | `None` | `shippo-api-overview` | `official_documentation` | [https://docs.goshippo.com/api-reference/overview](https://docs.goshippo.com/api-reference/overview) |
| `cb-ea3b1-shippo-003` | `provenance_traceability` | `observed` | Shippo rate records represent distinct shipping costs and service levels, and carrier-account configuration participates in test and live operation. | `shippo-rate-and-testing-docs` | `official_documentation` | [https://docs.goshippo.com/api-concepts/glossary](https://docs.goshippo.com/api-concepts/glossary); [https://docs.goshippo.com/guides/testing](https://docs.goshippo.com/guides/testing) |
| `cb-ea3b1-shippo-004` | `temporal_evidence` | `unknown` | `None` | `shippo-rating-docs` | `official_documentation` | [https://docs.goshippo.com/ratings/rating](https://docs.goshippo.com/ratings/rating) |
| `cb-ea3b1-shippo-005` | `estimate_status_disclosure` | `unknown` | `None` | `shippo-rating-docs` | `official_documentation` | [https://docs.goshippo.com/ratings/rating](https://docs.goshippo.com/ratings/rating) |
| `cb-ea3b1-shippo-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-shippo-007` | `operational_constraints` | `observed` | The API uses REST-style operations and JSON request and response bodies; most created shipping objects are immutable and must be recreated when values change. | `shippo-api-overview` | `official_documentation` | [https://docs.goshippo.com/api-reference/overview](https://docs.goshippo.com/api-reference/overview) |
| `cb-ea3b1-shippo-008` | `access_security_requirements` | `observed` | Requests require Shippo token authentication using a live or test token and TLS 1.2 or higher. | `shippo-api-overview` | `official_documentation` | [https://docs.goshippo.com/api-reference/overview](https://docs.goshippo.com/api-reference/overview) |
| `cb-ea3b1-shippo-009` | `commercial_constraints` | `unknown` | `None` | `shippo-api-overview` | `official_documentation` | [https://docs.goshippo.com/api-reference/overview](https://docs.goshippo.com/api-reference/overview) |

The inspected Shippo documentation does not establish one unconditional
geographic coverage set, commercial contract, or universal temporal and
estimate-status contract across every carrier, account, service, and
route. Those dimensions therefore remain unknown.

### `candidate:shipping:easypost-api`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-easypost-001` | `evidence_kind_coverage` | `observed` | EasyPost documents shipment rate records containing service, carrier, carrier-account, price, currency, and delivery fields. | `easypost-rate-docs` | `official_documentation` | [https://docs.easypost.com/docs/shipments/rates](https://docs.easypost.com/docs/shipments/rates) |
| `cb-ea3b1-easypost-002` | `geographic_coverage` | `unknown` | `None` | `easypost-getting-started` | `official_documentation` | [https://www.easypost.com/guides/getting-started](https://www.easypost.com/guides/getting-started) |
| `cb-ea3b1-easypost-003` | `provenance_traceability` | `observed` | A rate record identifies its carrier, carrier account, shipment, service, rate value, and currency. | `easypost-rate-docs` | `official_documentation` | [https://docs.easypost.com/docs/shipments/rates](https://docs.easypost.com/docs/shipments/rates) |
| `cb-ea3b1-easypost-004` | `temporal_evidence` | `observed` | Rate records may expose delivery days, a delivery date, and whether the delivery window is guaranteed. | `easypost-rate-docs` | `official_documentation` | [https://docs.easypost.com/docs/shipments/rates](https://docs.easypost.com/docs/shipments/rates) |
| `cb-ea3b1-easypost-005` | `estimate_status_disclosure` | `observed` | The rate schema distinguishes the quoted rate, retail rate, list rate, and whether a documented delivery window is guaranteed. | `easypost-rate-docs` | `official_documentation` | [https://docs.easypost.com/docs/shipments/rates](https://docs.easypost.com/docs/shipments/rates) |
| `cb-ea3b1-easypost-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-easypost-007` | `operational_constraints` | `observed` | Parcel weight is required, some services require dimensions, carrier-specific requirements apply, and individual carriers may fail to return rates. | `easypost-parcel-and-message-docs` | `official_documentation` | [https://docs.easypost.com/docs/parcels](https://docs.easypost.com/docs/parcels); [https://docs.easypost.com/docs/shipments/messages](https://docs.easypost.com/docs/shipments/messages) |
| `cb-ea3b1-easypost-008` | `access_security_requirements` | `observed` | EasyPost provides separate test and production API keys; production keys are used for live operations. | `easypost-authentication-docs` | `official_documentation` | [https://docs.easypost.com/docs/authentication](https://docs.easypost.com/docs/authentication) |
| `cb-ea3b1-easypost-009` | `commercial_constraints` | `observed` | Negotiated carrier rates are documented as production-only for inspected carrier integrations, and carrier-account availability and requirements remain carrier-specific. | `easypost-carrier-docs` | `official_documentation` | [https://www.easypost.com/carriers/usps-guide](https://www.easypost.com/carriers/usps-guide); [https://docs.easypost.com/docs/carrier-accounts](https://docs.easypost.com/docs/carrier-accounts) |

The EasyPost records do not establish unconditional geographic,
carrier, service, or negotiated-price availability. Those properties
remain dependent on the applicable carrier integration, account,
credentials, shipment data, and production mode.

### `candidate:shipping-landed-cost:mydhl-api`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-mydhl-001` | `evidence_kind_coverage` | `observed` | MyDHL documents rating, product, landed-cost, shipment, pickup, tracking, and address-capability services. | `mydhl-api-docs` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |
| `cb-ea3b1-mydhl-002` | `geographic_coverage` | `observed` | DHL describes MyDHL as globally available for time-definite international DHL Express shipping use. | `mydhl-api-docs` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |
| `cb-ea3b1-mydhl-003` | `provenance_traceability` | `observed` | Rating results are tied to DHL Express products and the requesting customer's DHL Express account rates. | `mydhl-api-docs` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |
| `cb-ea3b1-mydhl-004` | `temporal_evidence` | `observed` | Rating may return estimated delivery time, while DHL states that transit-time and delivery-date information is indicative and not guaranteed. | `mydhl-api-terms` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |
| `cb-ea3b1-mydhl-005` | `estimate_status_disclosure` | `observed` | The landed-cost service returns estimated landed cost including duties and taxes, and rating and transit information is described as indicative rather than guaranteed. | `mydhl-api-terms` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |
| `cb-ea3b1-mydhl-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-mydhl-007` | `operational_constraints` | `observed` | Landed-cost use requires item and customs information including HS codes; the documented test environment is limited to 500 service calls per day for an access key. | `mydhl-api-docs` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |
| `cb-ea3b1-mydhl-008` | `access_security_requirements` | `observed` | Productive access requires an active DHL Express customer account and successful credential validation; requests use provided access credentials and Basic Authentication. | `mydhl-api-docs` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |
| `cb-ea3b1-mydhl-009` | `commercial_constraints` | `observed` | MyDHL legal terms restrict use of Product and Rating Data, including third-party disclosure, storage, modification, and competitive analysis without prior written consent, and additional landed-cost terms may apply. | `mydhl-api-terms` | `official_documentation` | [https://developer.dhl.com/api-reference/dhl-express-mydhl-api](https://developer.dhl.com/api-reference/dhl-express-mydhl-api) |

The MyDHL observations describe DHL's documented service and legal
boundaries only. They do not establish actual route availability,
quote accuracy, entitlement, canonical compatibility, or suitability
for Commerce AI acquisition.

## Regulatory candidate evidence records

### Record conventions

For the records below:

- `source_relationship` is `subject_supplied`.
- `retrieved_at` is `2026-08-25`.
- `observed` records reproduce bounded claims found in the cited source.
- `unknown` records carry the literal value `None`.
- No record has `verified` state.
- Canonical projection compatibility remains unknown until a separate
  internal observation is authorized and performed.
- A public portal, search interface, download function, or documented
  service does not by itself establish automated acquisition authority.
- Published tariff or regulatory information does not by itself
  establish classification correctness, binding treatment, customs
  clearance, or final landed cost for a specific shipment.

### `candidate:regulatory:govuk-trade-tariff-api`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-govuk-001` | `evidence_kind_coverage` | `observed` | The official service endpoint identifies a UK Trade Tariff API and redirects users to its documentation service. | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |
| `cb-ea3b1-govuk-002` | `geographic_coverage` | `unknown` | `None` | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |
| `cb-ea3b1-govuk-003` | `provenance_traceability` | `observed` | The evidence endpoint is hosted under the official UK government Trade Tariff service domain. | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |
| `cb-ea3b1-govuk-004` | `temporal_evidence` | `unknown` | `None` | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |
| `cb-ea3b1-govuk-005` | `estimate_status_disclosure` | `unknown` | `None` | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |
| `cb-ea3b1-govuk-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-govuk-007` | `operational_constraints` | `unknown` | `None` | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |
| `cb-ea3b1-govuk-008` | `access_security_requirements` | `unknown` | `None` | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |
| `cb-ea3b1-govuk-009` | `commercial_constraints` | `unknown` | `None` | `govuk-trade-tariff-api` | `official_documentation` | [https://api.trade-tariff.service.gov.uk/](https://api.trade-tariff.service.gov.uk/) |

The inspected endpoint establishes an official UK Trade Tariff service
identity but does not, by itself, establish complete dataset scope,
revision behavior, production access terms, reuse permission, service
levels, or suitability for automated Commerce AI acquisition.

### `candidate:regulatory:eu-access2markets`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-access2markets-001` | `evidence_kind_coverage` | `observed` | Access2Markets provides trade-condition information including tariffs, taxes, rules of origin, product requirements, procedures, trade agreements, and statistics. | `eu-access2markets` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/home](https://trade.ec.europa.eu/access-to-markets/en/home); [https://trade.ec.europa.eu/access-to-markets/en/sitemap](https://trade.ec.europa.eu/access-to-markets/en/sitemap) |
| `cb-ea3b1-access2markets-002` | `geographic_coverage` | `observed` | My Trade Assistant accepts a product and countries of export and import to present conditions for trade with the EU under the applicable market and agreement context. | `eu-access2markets-rules-origin` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/content/rules-origin-access2markets](https://trade.ec.europa.eu/access-to-markets/en/content/rules-origin-access2markets) |
| `cb-ea3b1-access2markets-003` | `provenance_traceability` | `observed` | The portal is managed by the European Commission Directorate-General for Trade and Economic Security, and its rules-of-origin tools provide links to applicable legal texts. | `eu-access2markets` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/home](https://trade.ec.europa.eu/access-to-markets/en/home); [https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa](https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa) |
| `cb-ea3b1-access2markets-004` | `temporal_evidence` | `unknown` | `None` | `eu-access2markets` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/home](https://trade.ec.europa.eu/access-to-markets/en/home) |
| `cb-ea3b1-access2markets-005` | `estimate_status_disclosure` | `observed` | ROSA is described as a self-assessment tool; separate Binding Origin Information is required when a trader seeks a written decision providing legal certainty. | `eu-access2markets-origin-docs` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa](https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa); [https://trade.ec.europa.eu/access-to-markets/en/content/binding-origin-information-2](https://trade.ec.europa.eu/access-to-markets/en/content/binding-origin-information-2) |
| `cb-ea3b1-access2markets-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-access2markets-007` | `operational_constraints` | `observed` | Product-specific assistance depends on the product code, export country, import country, applicable trade agreement, and the user's supplied origin facts. | `eu-access2markets-origin-docs` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/content/rules-origin-access2markets](https://trade.ec.europa.eu/access-to-markets/en/content/rules-origin-access2markets); [https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa](https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa) |
| `cb-ea3b1-access2markets-008` | `access_security_requirements` | `unknown` | `None` | `eu-access2markets` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/home](https://trade.ec.europa.eu/access-to-markets/en/home) |
| `cb-ea3b1-access2markets-009` | `commercial_constraints` | `observed` | The European Commission describes the ROSA rules-of-origin self-assessment tool as free to use; broader automated reuse, quota, and service-level terms remain unresolved. | `eu-access2markets-rosa` | `official_documentation` | [https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa](https://trade.ec.europa.eu/access-to-markets/en/content/how-use-rules-origin-self-assessment-tool-rosa) |

The Access2Markets observations concern public portal functionality.
They do not establish a supported machine API, scraping permission,
production credential model, binding tariff classification, or final
customs treatment for an individual shipment.

### `candidate:regulatory:korea-customs-unipass`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-unipass-001` | `evidence_kind_coverage` | `observed` | UNI-PASS exposes Korean customs-administration workflows for export and import declarations, tariff treatment, customs valuation, cargo, special clearance, tariff classification, refunds, and FTA origin procedures. | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |
| `cb-ea3b1-unipass-002` | `geographic_coverage` | `observed` | The portal represents Korea Customs Service procedures for goods entering, leaving, or moving through the Korean customs system. | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |
| `cb-ea3b1-unipass-003` | `provenance_traceability` | `observed` | The observed source is the official Korea Customs Service UNI-PASS system and organizes information by named customs-administration workflow and document type. | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |
| `cb-ea3b1-unipass-004` | `temporal_evidence` | `unknown` | `None` | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |
| `cb-ea3b1-unipass-005` | `estimate_status_disclosure` | `unknown` | `None` | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |
| `cb-ea3b1-unipass-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-unipass-007` | `operational_constraints` | `observed` | UNI-PASS separates customs work into specific declarations, applications, approvals, corrections, certificates, and status workflows rather than exposing one unconditional regulatory result. | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |
| `cb-ea3b1-unipass-008` | `access_security_requirements` | `unknown` | `None` | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |
| `cb-ea3b1-unipass-009` | `commercial_constraints` | `unknown` | `None` | `korea-customs-unipass` | `official_documentation` | [https://unipass.customs.go.kr/](https://unipass.customs.go.kr/) |

The inspected UNI-PASS portal does not establish a general machine API
contract, credential entitlement, automated reuse permission, service
level, or canonical projection. Portal availability and electronic
customs workflows are not acquisition-runtime authorization.

### `candidate:regulatory:usitc-hts`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-usitc-001` | `evidence_kind_coverage` | `observed` | The USITC HTS publishes United States tariff rates and statistical categories and provides search, download, and export functions. | `usitc-hts` | `official_documentation` | [https://hts.usitc.gov/](https://hts.usitc.gov/); [https://hts.usitc.gov/download](https://hts.usitc.gov/download); [https://hts.usitc.gov/export](https://hts.usitc.gov/export) |
| `cb-ea3b1-usitc-002` | `geographic_coverage` | `observed` | The schedule covers the Harmonized Tariff Schedule of the United States. | `usitc-hts` | `official_documentation` | [https://hts.usitc.gov/](https://hts.usitc.gov/) |
| `cb-ea3b1-usitc-003` | `provenance_traceability` | `observed` | The HTS source identifies USITC as the publication authority and labels the currently presented schedule by year and revision. | `usitc-hts` | `official_documentation` | [https://hts.usitc.gov/](https://hts.usitc.gov/); [https://hts.usitc.gov/download](https://hts.usitc.gov/download) |
| `cb-ea3b1-usitc-004` | `temporal_evidence` | `observed` | USITC publishes revision-identified current schedules and provides an HTS archive for earlier editions and revisions. | `usitc-hts-revisions` | `official_documentation` | [https://hts.usitc.gov/download](https://hts.usitc.gov/download); [https://www.usitc.gov/harmonized_tariff_information/hts/archive/list](https://www.usitc.gov/harmonized_tariff_information/hts/archive/list) |
| `cb-ea3b1-usitc-005` | `estimate_status_disclosure` | `observed` | The HTS is presented as official tariff information rather than a shipment-specific landed-cost estimate; it does not by itself determine classification or final customs treatment for a shipment. | `usitc-hts` | `official_documentation` | [https://hts.usitc.gov/](https://hts.usitc.gov/); [https://www.usitc.gov/applications/dataweb/faqs](https://www.usitc.gov/applications/dataweb/faqs) |
| `cb-ea3b1-usitc-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-usitc-007` | `operational_constraints` | `observed` | Users must identify the applicable HTS revision and tariff line; the current schedule can be searched, downloaded, or exported in CSV, Excel, and JSON formats. | `usitc-hts-export` | `official_documentation` | [https://hts.usitc.gov/search](https://hts.usitc.gov/search); [https://hts.usitc.gov/download](https://hts.usitc.gov/download); [https://hts.usitc.gov/export](https://hts.usitc.gov/export) |
| `cb-ea3b1-usitc-008` | `access_security_requirements` | `unknown` | `None` | `usitc-hts` | `official_documentation` | [https://hts.usitc.gov/](https://hts.usitc.gov/) |
| `cb-ea3b1-usitc-009` | `commercial_constraints` | `unknown` | `None` | `usitc-hts` | `official_documentation` | [https://hts.usitc.gov/](https://hts.usitc.gov/) |

The evaluation subject is the USITC HTS publication source. No CBP
subject identity, source relationship, verification, classification
decision, acquisition authority, or customs-clearance capability is
created by these records.

## Landed-cost candidate evidence records

### Record conventions

For the records below:

- `source_relationship` is `subject_supplied`.
- `retrieved_at` is `2026-08-25`.
- `observed` records reproduce bounded claims found in the cited source.
- `unknown` records carry the literal value `None`.
- No record has `verified` state.
- Canonical projection compatibility remains unknown until a separate
  internal observation is authorized and performed.
- A quoted, approximate, estimated, or conditionally guaranteed landed
  cost is not treated as a customs determination or universal final
  charge.
- Geographic coverage claims do not establish route, account, product,
  guarantee, or production entitlement for Commerce AI.

### `candidate:landed-cost:zonos-api`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-zonos-001` | `evidence_kind_coverage` | `observed` | Zonos Landed Cost calculates and breaks down duties, taxes, and import-related fees for international shipments. | `zonos-landed-cost-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/get-started](https://zonos.com/docs/supply-chain/landed-cost/get-started) |
| `cb-ea3b1-zonos-002` | `geographic_coverage` | `observed` | Zonos states support for landed-cost calculations across 217 countries and territories. | `zonos-landed-cost-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/get-started](https://zonos.com/docs/supply-chain/landed-cost/get-started) |
| `cb-ea3b1-zonos-003` | `provenance_traceability` | `observed` | Landed-cost results provide item-level duty descriptions and identify the source used for an HS-code calculation, including catalog, request, platform, classification, or account-default sources. | `zonos-duty-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/calculate-landed-cost---graphql/duties](https://zonos.com/docs/supply-chain/landed-cost/calculate-landed-cost---graphql/duties) |
| `cb-ea3b1-zonos-004` | `temporal_evidence` | `unknown` | `None` | `zonos-landed-cost-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/get-started](https://zonos.com/docs/supply-chain/landed-cost/get-started) |
| `cb-ea3b1-zonos-005` | `estimate_status_disclosure` | `observed` | Zonos states that a request without an HS code may return an approximate estimate, while guarantee availability depends on the selected workflow and required inputs. | `zonos-landed-cost-calculation-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/create-a-landed-cost](https://zonos.com/docs/supply-chain/landed-cost/create-a-landed-cost); [https://zonos.com/docs/supply-chain/landed-cost/calculate-landed-cost---graphql](https://zonos.com/docs/supply-chain/landed-cost/calculate-landed-cost---graphql) |
| `cb-ea3b1-zonos-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-zonos-007` | `operational_constraints` | `observed` | Requests require parties or locations, item and monetary data, destination information, and landed-cost configuration; shipping cost must be supplied or obtained through a separate rating workflow, and an HS code may become required above applicable thresholds. | `zonos-landed-cost-request-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/create-a-landed-cost](https://zonos.com/docs/supply-chain/landed-cost/create-a-landed-cost); [https://zonos.com/docs/supply-chain/landed-cost/calculate-landed-cost---graphql](https://zonos.com/docs/supply-chain/landed-cost/calculate-landed-cost---graphql) |
| `cb-ea3b1-zonos-008` | `access_security_requirements` | `observed` | REST use requires a Zonos account, an API key, and the documented version header; Dashboard configuration is account-restricted. | `zonos-landed-cost-access-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/create-a-landed-cost](https://zonos.com/docs/supply-chain/landed-cost/create-a-landed-cost); [https://zonos.com/docs/global-ecommerce/landed-cost/configuration](https://zonos.com/docs/global-ecommerce/landed-cost/configuration) |
| `cb-ea3b1-zonos-009` | `commercial_constraints` | `unknown` | `None` | `zonos-landed-cost-docs` | `official_documentation` | [https://zonos.com/docs/supply-chain/landed-cost/get-started](https://zonos.com/docs/supply-chain/landed-cost/get-started) |

The Zonos documentation distinguishes approximate and conditionally
guaranteed calculations. It does not establish Commerce AI pricing,
contractual entitlement, storage and display permission, supported
production volume, or applicability of a guarantee to a prospective
Commerce AI request.

### `candidate:landed-cost:ups-api`

| record_id | dimension | state | observation value | source_id | source_type | source_reference |
|---|---|---|---|---|---|---|
| `cb-ea3b1-ups-001` | `evidence_kind_coverage` | `observed` | The UPS Landed Cost Quote API is documented as estimating international shipment cost including applicable duties, VAT, taxes, brokerage fees, and transportation cost. | `ups-landed-cost-api` | `official_documentation` | [https://developer.ups.com/api/reference?tag=Landed-Cost](https://developer.ups.com/api/reference?tag=Landed-Cost) |
| `cb-ea3b1-ups-002` | `geographic_coverage` | `unknown` | `None` | `ups-landed-cost-api` | `official_documentation` | [https://developer.ups.com/api/reference?tag=Landed-Cost](https://developer.ups.com/api/reference?tag=Landed-Cost) |
| `cb-ea3b1-ups-003` | `provenance_traceability` | `unknown` | `None` | `ups-landed-cost-api` | `official_documentation` | [https://developer.ups.com/api/reference?tag=Landed-Cost](https://developer.ups.com/api/reference?tag=Landed-Cost) |
| `cb-ea3b1-ups-004` | `temporal_evidence` | `unknown` | `None` | `ups-landed-cost-api` | `official_documentation` | [https://developer.ups.com/api/reference?tag=Landed-Cost](https://developer.ups.com/api/reference?tag=Landed-Cost) |
| `cb-ea3b1-ups-005` | `estimate_status_disclosure` | `observed` | UPS describes the Landed Cost Quote API and TradeAbility landed-cost service as estimates, and states that TradeAbility accuracy is not guaranteed and applicable laws may change. | `ups-landed-cost-and-tradeability` | `official_documentation` | [https://developer.ups.com/api/reference?tag=Landed-Cost](https://developer.ups.com/api/reference?tag=Landed-Cost); [https://wwwapps.ups.com/tradeability/](https://wwwapps.ups.com/tradeability/) |
| `cb-ea3b1-ups-006` | `canonical_projection_compatibility` | `unknown` | `None` | `commerce-ai-evaluation` | `internal_research_boundary` | `CB-EA3B-1` |
| `cb-ea3b1-ups-007` | `operational_constraints` | `observed` | UPS states that international cost depends on shipment value, manufacture country, origin, destination, shipment purpose, and product tariff information; complete shipment and customs details remain necessary for accurate assessment. | `ups-international-cost-docs` | `official_documentation` | [https://www.ups.com/us/en/shipping/international-shipping/international-shipping-costs](https://www.ups.com/us/en/shipping/international-shipping/international-shipping-costs) |
| `cb-ea3b1-ups-008` | `access_security_requirements` | `unknown` | `None` | `ups-landed-cost-api` | `official_documentation` | [https://developer.ups.com/api/reference?tag=Landed-Cost](https://developer.ups.com/api/reference?tag=Landed-Cost) |
| `cb-ea3b1-ups-009` | `commercial_constraints` | `unknown` | `None` | `ups-landed-cost-api` | `official_documentation` | [https://developer.ups.com/api/reference?tag=Landed-Cost](https://developer.ups.com/api/reference?tag=Landed-Cost) |

The inspected UPS sources do not establish unconditional geographic
availability, production credentials, quote-field provenance,
commercial API terms, storage and display permission, service levels,
or account entitlement for Commerce AI. No UPS quote is treated as a
binding customs decision or universally final charge.

## Deferred work

Later exact-scope steps may add bounded evidence observations for the
registered subjects. Those observations must preserve source URLs,
retrieval time, evidence state, source relationship, and the applicable
evaluation dimension.

No network client, credential, raw response, HTML capture, provider
adapter, registry entry, score, rank, recommendation, or selection
decision is authorized by this dossier.
