# UPS API Landed-Cost-Component Projection Compatibility Worksheet

## Document status

- Status: bounded internal observation worksheet
- Subject: `candidate:landed-cost:ups-api`
- External evidence kind: `landed_cost`
- Canonical target family: `landed_cost_component_evidence`
- Observation stage: documentation-only
- Evidence relationship: `subject_supplied`
- Observation date: `2026-08-26`
- Proposed compatibility state: `observed`
- Proposed compatibility value: subject-specific prospective component mapping
- Dossier mutation: proposed only after separate exact-scope authorization

## Purpose and authority boundary

This worksheet applies the internal canonical projection compatibility
observation protocol to the prospective landed-cost-component surface of the
UPS Landed Cost Quote API.

It asks whether the documented response shape supports a bounded prospective
mapping into `LandedCostComponentEvidence`.

It does not authorize API acquisition, credentials, payload capture,
implementation, provider registration, provider selection, provider
verification, provider ranking, production use, customs determination,
purchase recommendation, order creation, or transaction execution.

## Registered subject boundary

The evaluation dossier registers:

- subject: `candidate:landed-cost:ups-api`;
- evidence relationship: `subject_supplied`;
- current `canonical_projection_compatibility`: `unknown`;
- current value: `None`;
- target record: `cb-ea3b1-ups-006`.

The dossier already records that the UPS Landed Cost Quote API estimates
international shipment costs that may include duties, VAT, taxes, brokerage
fees, transportation cost, and other fees.

The dossier also records that UPS quote material must not be treated as a
binding customs decision or universally final charge.

## Inspected official source

### UPS developer reference

- Source owner: UPS
- Source type: official developer documentation
- Reference:
  <https://developer.ups.com/api/reference?tag=Landed-Cost>

### UPS official OpenAPI repository

- Repository: <https://github.com/UPS-API/api-documentation>
- Document: `LandedCost.yaml`
- Inspected commit: `c267acc767a1fb61ad0e3e61fff68b28f1d3a23e`
- Immutable reference:
  <https://github.com/UPS-API/api-documentation/blob/c267acc767a1fb61ad0e3e61fff68b28f1d3a23e/LandedCost.yaml>
- Inspected file SHA-256: `c30df09189c424829dd75da114e2607b3ddeb5c55199c8d2820645062eaeefb9`
- OpenAPI version: `3.0.3`
- API title: `Landed Cost Quote API`
- Operation: `LandedCost`
- Response schema: `LandedCostResponse`

The commit and file digest identify the inspected documentation artifact. They
do not establish runtime availability, account entitlement, commercial terms,
or production behavior.

## Documented response surface

The inspected response schema documents a shipment-level currency code that is
applicable to duty, tax, VAT, and fee values at shipment and commodity levels.

Documented shipment-level monetary fields include:

- `totalDuties`;
- `totalVAT`;
- `totalBrokerageFees`;
- `totalCommodityLevelTaxesAndFees`;
- `totalShipmentLevelTaxesAndFees`;
- `totalDutyAndTax`;
- `grandTotal`.

Documented brokerage detail includes:

- `brokerageFeeItems[].chargeName`;
- `brokerageFeeItems[].chargeAmount`.

Documented commodity-level fields include:

- `commodityDuty`;
- `commodityVAT`;
- `totalCommodityTaxAndFee`;
- `totalCommodityDutyAndTax`;
- `commodityCurrencyCode`;
- `isCalculable`.

The sample response also demonstrates shipment and commodity identifiers,
currency, duty, VAT, brokerage charges, combined tax-and-fee totals, and
calculability flags.

## Canonical target requirements

`LandedCostComponentEvidence` requires:

- a non-empty component identity;
- `LandedCostComponentState`;
- non-negative amount and currency for evidence-bearing states;
- no amount or currency for evidence-absent states;
- provenance when claimed;
- evaluation context when claimed;
- an estimate reason when applicable.

The canonical vocabulary is intentionally open. Provider-specific component
identities remain permitted, but they must not be declared canonical without a
separate mapping justification.

## Prospective field mapping

| UPS response field | Prospective canonical material | Boundary |
|---|---|---|
| `shipment.currencyCode` | Currency for shipment-level duty, VAT, tax, and fee evidence | Apply only within the documented shipment response. |
| `totalDuties` | `amount` for component `duty` | Shipment-level aggregate; do not also add its commodity constituents. |
| `commodityDuty` | `amount` for component `duty` | Commodity-level evidence; retain commodity identity and evaluation unit. |
| `totalVAT` | `amount` for component `tax` | VAT is treated prospectively as tax evidence, not as a customs determination. |
| `commodityVAT` | `amount` for component `tax` | Commodity-level evidence; retain commodity identity and evaluation unit. |
| `brokerageFeeItems[].chargeName` | Provider-specific component identity | Preserve the documented charge name without declaring a canonical subtype. |
| `brokerageFeeItems[].chargeAmount` | Amount for the corresponding provider-specific brokerage component | Use the documented response currency. |
| `totalBrokerageFees` | Provider-specific aggregate component `ups_total_brokerage_fees` | Do not add both aggregate and constituent brokerage fee items. |
| `totalCommodityLevelTaxesAndFees` | Provider-specific combined component `ups_total_commodity_level_taxes_and_fees` | Do not split tax from fees without separate item semantics. |
| `totalShipmentLevelTaxesAndFees` | Provider-specific combined component `ups_total_shipment_level_taxes_and_fees` | Do not split tax from fees without separate item semantics. |
| `totalCommodityTaxAndFee` | Provider-specific combined component `ups_total_commodity_tax_and_fee` | Preserve the combined identity and commodity evaluation unit. |
| `totalDutyAndTax` | Reconciliation aggregate only | Do not project as an additional additive component. |
| `totalCommodityDutyAndTax` | Commodity reconciliation aggregate only | Do not project as an additional additive component. |
| `grandTotal` | Reconciliation aggregate only | Do not add to its documented constituent totals. |
| `isCalculable` | Calculability evidence | `false` must not manufacture a zero monetary component. |
| Shipment and commodity IDs | Correlation material | Commerce AI owns the canonical provenance envelope. |
| Request and response evaluation inputs | Evaluation-context correlation material | Commerce AI owns and validates the canonical evaluation-context envelope. |

## Component-identity decision

The following mappings are supported prospectively:

- UPS `totalDuties` and `commodityDuty` → canonical `duty`;
- UPS `totalVAT` and `commodityVAT` → canonical `tax`.

The following remain provider-specific:

- individual brokerage charge names;
- `ups_total_brokerage_fees`;
- `ups_total_commodity_level_taxes_and_fees`;
- `ups_total_shipment_level_taxes_and_fees`;
- `ups_total_commodity_tax_and_fee`.

This worksheet does not silently map a brokerage charge to `customs_fee`,
`service_fee`, `payment_fee`, or another canonical subtype.

This worksheet does not split a documented combined taxes-and-fees amount into
separate tax and fee components.

A narrower mapping requires field- or entry-level documented semantics and a
separate mapping justification.

## State decision

The default prospective component state is:

- `LandedCostComponentState.ESTIMATED`

This follows the documented quote and estimate semantics.

Neither the API title, a successful calculation, `isCalculable = true`, nor a
returned monetary amount independently authorizes `KNOWN`.

The following are prohibited:

- converting a quote directly to `KNOWN`;
- treating `isCalculable = false` as zero;
- treating a missing field as zero;
- deriving absent duty, VAT, tax, or fee amounts;
- converting a UPS quote into a customs determination.

## Aggregation-level boundary

Shipment totals and commodity-level values may describe the same economic
amounts at different aggregation levels.

A later adapter must select one internally consistent projection grain for an
evaluation unit. It must not add:

- `totalDuties` and all `commodityDuty` values together;
- `totalVAT` and all `commodityVAT` values together;
- `totalBrokerageFees` and all brokerage charge amounts together;
- `totalDutyAndTax` to its duty, VAT, tax, or fee constituents;
- `grandTotal` to any of its documented constituents.

Aggregate fields may be retained as reconciliation evidence without becoming
additional additive components.

## Documentation consistency boundary

The inspected OpenAPI sample and schema contain naming variations, including
capitalization and singular/plural differences for some aggregate fields.

A later implementation must bind to the actual versioned response contract and
must not infer field equivalence solely from similar names in examples.

This worksheet records documentation-level prospective compatibility only. It
does not establish a production parser or payload contract.

## Provenance and evaluation context

Prospective canonical evidence requires Commerce AI-owned envelopes that retain:

- subject identity;
- official source identity and immutable reference;
- retrieval or observation time;
- shipment and commodity correlation identifiers;
- origin, destination, shipment purpose, transport, price, and currency inputs;
- aggregation grain;
- evaluation purpose and context;
- applicable estimate or calculability conditions.

The provider output does not independently own the canonical provenance or
evaluation-context contract.

## Prospective adapter rules

A later separately authorized adapter would need to:

1. accept only an authorized UPS response artifact;
2. preserve the response currency;
3. preserve shipment and commodity correlation identifiers;
4. reject negative evidence-bearing amounts;
5. map duty fields only to `duty`;
6. map VAT fields only to `tax`;
7. preserve brokerage charge identities as provider-specific;
8. preserve combined taxes-and-fees fields without silent decomposition;
9. assign `ESTIMATED` by default;
10. preserve zero as numeric zero only when explicitly returned;
11. preserve calculability separately from monetary state;
12. choose a single non-duplicative aggregation grain;
13. treat aggregate totals as reconciliation evidence where appropriate;
14. construct Commerce AI-owned provenance and evaluation-context envelopes;
15. manufacture no customs, classification, legal, verification, or selection result.

## Projection compatibility decision

### Target-family result

- Target family: `landed_cost_component_evidence`
- Proposed state: `observed`
- Proposed value: UPS documents shipment- and commodity-level duty and VAT
  amounts, response currency, brokerage charges, and combined taxes-and-fees
  amounts that prospectively support bounded component projection; duty fields
  map to `duty`, VAT fields map to `tax`, brokerage and combined tax-and-fee
  identities remain provider-specific, all monetary components default to
  `ESTIMATED`, and aggregation levels must not be double-counted.

### Sufficiency rationale

The documented response supplies:

- identifiable monetary component surfaces;
- numeric duty, VAT, brokerage, and combined tax-and-fee amounts;
- a response currency;
- shipment and commodity correlation identifiers;
- calculability information;
- documented estimate semantics.

These fields are sufficient for prospective construction of bounded
`LandedCostComponentEvidence`.

### Overall subject result

Because `landed_cost_component_evidence` is the only applicable canonical
target family:

- `canonical_projection_compatibility`: `observed`
- value: subject-specific prospective component mapping

The result is documentation-only and subject-specific.

It does not establish provider selection, provider verification, provider
ranking, runtime acquisition, commercial entitlement, production activation,
or customs authority.

## Residual unknowns

The following remain unknown or unauthorized:

- unconditional geographic availability;
- production credentials and account entitlement;
- commercial API terms;
- storage and display permission;
- production service levels;
- observed live-response conformance;
- production parser behavior;
- guarantee applicability;
- customs authority or final-charge status.

## Dossier boundary

This worksheet does not mutate the dossier.

The dossier record remains `unknown / None` until a separate exact-scope
mutation is authorized and performed.

The proposed later mutation is limited to `cb-ea3b1-ups-006` and must preserve
the subject identity, record count, source relationships, and every other
dossier record.
