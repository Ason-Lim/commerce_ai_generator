# US Low-Value Commercial Shipment Policy Evidence Registration Lifecycle Opening Decision

## Decision identity

- Decision gate: `CB-MAR-3_US_LOW_VALUE_POLICY_EVIDENCE_REGISTRATION_LIFECYCLE_OPENING_DECISION`
- Selected lifecycle: `US_LOW_VALUE_COMMERCIAL_SHIPMENT_POLICY_EVIDENCE_REGISTRATION`
- Previous lifecycle state: `SELECTED_NOT_OPENED`
- Decision result: `OPEN`
- Initial gate: `CB-USLV-1_OFFICIAL_SOURCE_IDENTITY_AND_SCOPE_ACQUISITION`
- Initial gate mode: `BOUNDED_READ_ONLY_EXTERNAL_EVIDENCE_ACQUISITION`

## Decision

The exactly selected
`US_LOW_VALUE_COMMERCIAL_SHIPMENT_POLICY_EVIDENCE_REGISTRATION`
lifecycle is opened.

This decision opens one bounded evidence-registration lifecycle only. It does not
perform external evidence acquisition, register a new evidence fact, admit any
fact into a canonical contract, select a provider, or authorize production,
model, implementation, test, or runtime mutation.

The first authorized lifecycle gate is
`CB-USLV-1_OFFICIAL_SOURCE_IDENTITY_AND_SCOPE_ACQUISITION`.

## Authorized evidence boundary

The initial gate is limited to read-only acquisition of source identity, scope,
and time evidence concerning United States low-value commercial shipment policy.

The permitted source class is:

`OFFICIAL_US_GOVERNMENT_PRIMARY_POLICY_SOURCES_ONLY`

The permitted subject is:

`US_LOW_VALUE_COMMERCIAL_SHIPMENT_POLICY_ONLY`

The permitted operation is:

`READ_ONLY_SOURCE_IDENTITY_SCOPE_AND_TIME_EVIDENCE_ACQUISITION`

The following capture requirements apply:

- issuing authority: required
- official source reference: required
- rule identity: required
- publication, effective, suspension, replacement, validity, or other relevant
  time identity: capture only when directly established
- shipment channel or mode scope: required
- destination jurisdiction: required
- value threshold: capture only when directly established
- duty, tax, fee, entry, or exemption treatment: capture only as directly stated

## Evidence treatment

The permitted evidence-status vocabulary is:

- `VERIFIED`
- `PARTIALLY_VERIFIED`
- `REPORTED`
- `MISSING`

Source fact, project interpretation, and canonical admission must remain
separate.

Acquisition under this lifecycle does not itself establish canonical admission.

Anything not directly established by an authorized primary source must not be
inferred and must remain appropriately marked under the authorized
evidence-status vocabulary.

## Explicitly withheld authority

This opening decision grants no authority for:

- secondary-source evidence acquisition
- provider-document evidence acquisition
- credential use
- broad crawling
- automatic canonical admission
- dossier mutation
- canonical contract mutation
- production or model mutation
- implementation
- test creation or modification
- provider selection
- runtime activation
- any other lifecycle opening

## Repository mutation boundary

The only repository write authorized by `CB-MAR-3B` is creation of this decision
file:

`docs/research/cross_border/us_low_value_commercial_shipment_policy_evidence_registration_lifecycle_opening_decision.md`

No external policy evidence is acquired or registered by writing this decision.

Staging, commit creation, tag creation, and push remain withheld pending a
separate explicit authority gate.

The reserved future lifecycle-opening tag identity is:

`cross-border-us-low-value-commercial-shipment-policy-evidence-registration-lifecycle-opened-v1.0`

This decision does not create that tag.

## Result

- selected lifecycle opening decision: `RECORDED`
- opened lifecycle:
  `US_LOW_VALUE_COMMERCIAL_SHIPMENT_POLICY_EVIDENCE_REGISTRATION`
- initial gate:
  `CB-USLV-1_OFFICIAL_SOURCE_IDENTITY_AND_SCOPE_ACQUISITION`
- external evidence acquisition: `NOT PERFORMED`
- new evidence registration: `NOT PERFORMED`
- canonical admission: `NOT AUTHORIZED`
- provider selection: `NOT AUTHORIZED`
- implementation and runtime mutation: `NOT AUTHORIZED`
- stage, commit, tag, and push: `NOT AUTHORIZED`
