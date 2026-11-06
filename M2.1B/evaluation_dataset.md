# M2.1B — Clean Evaluation Dataset: Security-Deposit Disputes (India)

**Purpose:** Evaluation cases for the AI Lawyer intake + legal-reasoning pipeline for the
`security_deposit_dispute` case type. Each case provides a scenario narrative, structured input facts
(aligned with `SecurityDepositDisputeFacts` in `backend/app/schemas/case.py`), the provisions that
should be retrieved/applied (IDs from `provision_inventory.md`), and an expected conclusion/label.

**How to use:**
- Feed `input_narrative` (or `input_facts`) to the intake agent; check extracted facts vs. `expected_facts`.
- For legal reasoning, check retrieved provisions vs. `expected_provisions` and conclusion vs. `expected_outcome`.
- Scoring: see § 4 (Evaluation rubric).

**Counts:** 32 cases across 6 themes.
**Research date:** 2026-11-06. All legal conclusions are research-based and must be verified against
official sources before use in production.

---

## 1. Schema reference (input/output)

Input facts follow `SecurityDepositDisputeFacts`:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "...", "city": "..." },
  "parties": { "tenant": "...", "landlord": "..." },
  "property_address": "...",
  "rental_start_date": "YYYY-MM-DD",
  "rental_end_date": "YYYY-MM-DD",
  "vacating_date": "YYYY-MM-DD",
  "security_deposit_amount": 0,
  "security_deposit_currency": "INR",
  "deposit_payment_date": "YYYY-MM-DD",
  "deposit_payment_method": "bank_transfer",
  "rental_agreement_exists": true,
  "refund_clause": "...",
  "landlord_response": "...",
  "facts": ["..."],
  "timeline": [{"date": "...", "event": "..."}],
  "evidence_available": ["..."],
  "missing_information": ["..."]
}
```

Expected outcome labels: `full_refund` | `partial_refund` | `no_refund` | `over_cap_refund`
(excess deposit above statutory cap must be refunded regardless of deductions) | `escalate` (forum/limitation/verification needed).

---

## 2. Cases

### EVAL-001 - UP: landlord refuses refund, no deductions claimed
- Theme: MTA-adopter; simple refund delay
- Jurisdiction: Uttar Pradesh, Lucknow
- Difficulty: easy
- Input narrative: Tenant vacated a 2BHK in Lucknow on 2024-03-15 after 11-month lease; paid Rs.40,000 security deposit (2 months rent at Rs.20,000/month). Agreement registered with Rent Authority. Landlord has not refunded after 45 days; says no reason, will refund later.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Uttar Pradesh", "city": "Lucknow" },
  "parties": { "tenant": "A", "landlord": "B" },
  "property_address": "Lucknow",
  "rental_start_date": "2023-04-15",
  "rental_end_date": "2024-03-14",
  "vacating_date": "2024-03-15",
  "security_deposit_amount": 40000,
  "security_deposit_currency": "INR",
  "deposit_payment_date": "2023-04-10",
  "deposit_payment_method": "bank_transfer",
  "rental_agreement_exists": true,
  "refund_clause": "refund within 15 days of vacating",
  "landlord_response": "will refund later, no reason given",
  "facts": ["tenant vacated on agreed date", "no damage claimed"],
  "timeline": [{"date": "2024-03-15", "event": "vacated"}, {"date": "2024-04-30", "event": "no refund received"}],
  "evidence_available": ["registered agreement", "bank transfer proof"],
  "missing_information": []
}
```
- Expected facts: security_deposit_amount=40000; vacating_date=2024-03-15; rental_agreement_exists=true.
- Expected provisions: MTA-11, MTA-4, MTA-29, MTA-40, CC-3.
- Expected outcome: full_refund (cap not exceeded; no lawful deduction stated).
- Notes: MTA-adopter UP; forum Rent Authority. Limitation 3 years from due date.

### EVAL-002 - UP: deposit exceeds statutory cap (over_cap_refund)
- Theme: MTA-adopter; excessive deposit
- Jurisdiction: Uttar Pradesh, Noida
- Difficulty: easy
- Input narrative: Tenant paid Rs.1,20,000 deposit on rent of Rs.20,000/month (6 months) in UP. Landlord refuses to refund excess over cap.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Uttar Pradesh", "city": "Noida" },
  "parties": { "tenant": "C", "landlord": "D" },
  "property_address": "Noida",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 120000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.20,000", "deposit Rs.1,20,000 (6 months)"],
  "evidence_available": ["agreement", "rent receipts"],
  "missing_information": []
}
```
- Expected facts: security_deposit_amount=120000; monthly rent implied 20000.
- Expected provisions: MTA-11 (cap 2 months residential = Rs.40,000), MTA-4, MTA-40.
- Expected outcome: over_cap_refund (excess Rs.80,000 above cap refundable; lawful deductions only from capped amount).
- Notes: Cap breach independent of deductions.

### EVAL-003 - UP: overstay deduction (enhanced rent)
- Theme: MTA-adopter; overstay
- Jurisdiction: Uttar Pradesh, Kanpur
- Difficulty: medium
- Input narrative: Tenant stayed 1 month beyond lease end without vacating; landlord deducts 2x rent for overstay from deposit.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Uttar Pradesh", "city": "Kanpur" },
  "parties": { "tenant": "E", "landlord": "F" },
  "property_address": "Kanpur",
  "rental_start_date": "2023-01-01",
  "rental_end_date": "2023-12-31",
  "vacating_date": "2024-01-31",
  "security_deposit_amount": 40000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["tenant overstay 1 month", "rent Rs.20,000/month"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: MTA-11, MTA-23 (2x rent first 2 months), MTA-5, MTA-29.
- Expected outcome: partial_refund (deposit 40,000 - 40,000 overstay = 0; if overstay 2 months then 4x).
- Notes: Enhanced rent applies only if tenancy not renewed.

### EVAL-004 - Assam: no written agreement, oral tenancy (TPA fallback)
- Theme: MTA-adopter state but informal tenancy
- Jurisdiction: Assam, Guwahati
- Difficulty: medium
- Input narrative: Oral month-to-month tenancy in Guwahati; no registered agreement. Landlord withholds full deposit citing damages.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Assam", "city": "Guwahati" },
  "parties": { "tenant": "G", "landlord": "H" },
  "property_address": "Guwahati",
  "rental_start_date": "2022-06-01",
  "vacating_date": "2023-06-01",
  "security_deposit_amount": 30000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": false,
  "facts": ["oral tenancy", "month-to-month", "no written agreement submitted to Rent Authority"],
  "evidence_available": ["bank transfer proof", "witnesses"],
  "missing_information": ["exact terms of deposit refund"]
}
```
- Expected provisions: TPA-106, TPA-107, TPA-108, TPA-116, MTA-4 (not applicable absent written agreement), CC-3.
- Expected outcome: escalate (MTA cap may not apply; deposit terms unprovable; civil suit under TPA).
- Notes: MTA § 4 requires written agreement; absent it, TPA governs.

### EVAL-005 - J&K: recently enacted act (temporal)
- Theme: temporal metadata; new act
- Jurisdiction: Jammu & Kashmir, Srinagar
- Difficulty: hard
- Input narrative: Tenancy started 2024-06-01 in Srinagar; Act assented 1 Nov 2025. Is MTA-style cap applicable retroactively?
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Jammu and Kashmir", "city": "Srinagar" },
  "parties": { "tenant": "I", "landlord": "J" },
  "property_address": "Srinagar",
  "rental_start_date": "2024-06-01",
  "vacating_date": "2025-05-31",
  "security_deposit_amount": 60000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["tenancy started before Act assent", "deposit 3 months rent"],
  "evidence_available": ["agreement"],
  "missing_information": ["state notification date"]
}
```
- Expected provisions: MTA-1 (commencement state-notified), temporal_metadata § 3.
- Expected outcome: escalate (regime depends on state notification date and whether Act applies to pre-existing tenancies; unverified).
- Notes: Tests temporal reasoning; do not assert cap without verification.

### EVAL-006 - Chandigarh: contested extension
- Theme: contested regime
- Jurisdiction: Chandigarh
- Difficulty: hard
- Input narrative: Tenant in Chandigarh claims 2-month cap under extended Assam Tenancy Act; landlord disputes validity.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Chandigarh", "city": "Chandigarh" },
  "parties": { "tenant": "K", "landlord": "L" },
  "property_address": "Chandigarh",
  "rental_start_date": "2026-06-01",
  "vacating_date": "2026-08-31",
  "security_deposit_amount": 50000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["deposit 2.5 months rent", "tenant invokes MTA-style cap"],
  "evidence_available": ["agreement", "S.O. 2265(E) copy"],
  "missing_information": []
}
```
- Expected provisions: ST-CH (contested), CC-3.
- Expected outcome: escalate (regime contested; advise civil court; do not assert cap).
- Notes: Must not state cap as settled law.


### EVAL-007 - TN: 3-month cap, agreement overrides
- Theme: TN/AP-model; cap overridable
- Jurisdiction: Tamil Nadu, Chennai
- Difficulty: medium
- Input narrative: Lease in Chennai with deposit Rs.1,50,000 on rent Rs.30,000/month (5 months) but agreement explicitly states 5-month deposit. Landlord refunds only 3 months' worth.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Tamil Nadu", "city": "Chennai" },
  "parties": { "tenant": "M", "landlord": "N" },
  "property_address": "Chennai",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 150000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "refund_clause": "deposit 5 months rent",
  "facts": ["monthly rent Rs.30,000", "deposit Rs.1,50,000 (5 months)", "agreement states 5-month deposit"],
  "evidence_available": ["registered agreement"],
  "missing_information": []
}
```
- Expected provisions: ST-TN (3-month cap, "save agreement to the contrary"), ICA-74 (penalty/reasonable compensation).
- Expected outcome: no_refund of excess? Actually because agreement can override the 3-month default, the 5-month deposit stands if expressly agreed; landlord may retain per agreement terms unless unconscionable. Label: partial_refund only for lawful deductions; excess above agreed not refundable solely due to cap.
- Notes: TN cap is a default, not mandatory; agreement to the contrary permitted.

### EVAL-008 - AP: 3-month cap default (no override clause)
- Theme: TN/AP-model; default cap
- Jurisdiction: Andhra Pradesh, Vijayawada
- Difficulty: easy
- Input narrative: Deposit 6 months' rent in Vijayawada; agreement silent on deposit amount beyond "security deposit". Tenant claims excess over 3 months.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Andhra Pradesh", "city": "Vijayawada" },
  "parties": { "tenant": "O", "landlord": "P" },
  "property_address": "Vijayawada",
  "rental_start_date": "2023-02-01",
  "vacating_date": "2024-01-31",
  "security_deposit_amount": 180000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "refund_clause": "security deposit refundable",
  "facts": ["monthly rent Rs.30,000", "deposit Rs.1,80,000 (6 months)", "agreement silent on cap"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: ST-AP (3-month cap default), ICA-74.
- Expected outcome: over_cap_refund (excess above 3 months = Rs.90,000 refundable).
- Notes: Default cap applies where agreement does not override.

### EVAL-009 - Maharashtra: contractual deposit, MRCA registration
- Theme: rent-control no cap; registration
- Jurisdiction: Maharashtra, Mumbai
- Difficulty: medium
- Input narrative: Leave-and-licence in Mumbai; unregistered agreement; landlord withholds deposit; tenant seeks refund.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Maharashtra", "city": "Mumbai" },
  "parties": { "tenant": "Q", "landlord": "R" },
  "property_address": "Mumbai",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 100000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["leave and licence", "agreement not registered", "deposit 5 months"],
  "evidence_available": ["unregistered agreement copy", "bank transfer"],
  "missing_information": []
}
```
- Expected provisions: MRCA § 55 (compulsory registration; penalty), RA-17, RA-49, TPA-107, CC-3.
- Expected outcome: escalate (unregistered agreement inadmissible as primary evidence; deposit terms unprovable; civil suit).
- Notes: MRCA § 55 penalty up to 3 months / Rs.5,000 for non-registration.

### EVAL-010 - Karnataka: high-rent exemption (TPA fallback)
- Theme: rent-control no cap; exemption
- Jurisdiction: Karnataka, Bengaluru
- Difficulty: medium
- Input narrative: Rent Rs.25,000/month in Bengaluru (> Rs.3,500 threshold) so Karnataka Rent Act exempt; TPA governs. Landlord cuts essential services to force vacating, withholds deposit.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Karnataka", "city": "Bengaluru" },
  "parties": { "tenant": "S", "landlord": "T" },
  "property_address": "Bengaluru",
  "rental_start_date": "2023-03-01",
  "vacating_date": "2024-02-29",
  "security_deposit_amount": 75000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.25,000", "landlord cut water/electricity", "deposit 3 months"],
  "evidence_available": ["agreement", "complaint to police"],
  "missing_information": []
}
```
- Expected provisions: Karnataka § 2 (exemption), TPA-108 (quiet enjoyment), SRA-38, CC-2 (criminal breach of trust), CC-3.
- Expected outcome: partial_refund/full_refund of deposit plus injunction; essential-services coercion unlawful.
- Notes: No statutory cap; deposit contractual but landlord cannot coerce.

### EVAL-011 - Delhi: rent above threshold (civil court)
- Theme: rent-control no cap; exemption
- Jurisdiction: Delhi (NCT), New Delhi
- Difficulty: easy
- Input narrative: Rent Rs.15,000/month in Delhi (> Rs.3,500) so DRCA does not apply; civil court jurisdiction. Landlord delays refund 6 months.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Delhi", "city": "New Delhi" },
  "parties": { "tenant": "U", "landlord": "V" },
  "property_address": "New Delhi",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 45000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.15,000", "deposit 3 months", "no refund for 6 months"],
  "evidence_available": ["agreement", "demand notice"],
  "missing_information": []
}
```
- Expected provisions: Delhi § 3(c) (exemption), TPA-106, TPA-108, CC-3 (limitation 3 years).
- Expected outcome: full_refund (no lawful deduction stated).
- Notes: Forum Civil Court (> Rs.3,500).

### EVAL-012 - Telangana: unverified deposit clause
- Theme: unverified regime
- Jurisdiction: Telangana, Hyderabad
- Difficulty: hard
- Input narrative: Tenant in Hyderabad claims statutory deposit cap; landlord says none exists.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Telangana", "city": "Hyderabad" },
  "parties": { "tenant": "W", "landlord": "X" },
  "property_address": "Hyderabad",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 90000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.30,000", "deposit 3 months"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: Telangana Act (deposit clause unverified), TPA-106, TPA-108, CC-3.
- Expected outcome: escalate (deposit clause of Telangana rent statute not confirmed by official text; treat as contractual/TPA).
- Notes: Must not assert a statutory cap.

### EVAL-013 - Kerala: contractual deposit, rent-control act applies
- Theme: rent-control no cap
- Jurisdiction: Kerala, Kochi
- Difficulty: easy
- Input narrative: Deposit refund delayed in Kochi; no deductions; market deposit 2 months.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Kerala", "city": "Kochi" },
  "parties": { "tenant": "Y", "landlord": "Z" },
  "property_address": "Kochi",
  "rental_start_date": "2023-04-01",
  "vacating_date": "2024-03-31",
  "security_deposit_amount": 40000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.20,000", "deposit 2 months", "no damage"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: Kerala Act + TPA, TPA-106, TPA-108, CC-3.
- Expected outcome: full_refund.
- Notes: No statutory cap; contractual.

### EVAL-014 - Gujarat: unverified deposit clause
- Theme: unverified regime
- Jurisdiction: Gujarat, Ahmedabad
- Difficulty: hard
- Input narrative: Tenant in Ahmedabad claims rent-control protection; landlord says Act does not apply.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Gujarat", "city": "Ahmedabad" },
  "parties": { "tenant": "AA", "landlord": "AB" },
  "property_address": "Ahmedabad",
  "rental_start_date": "2022-01-01",
  "vacating_date": "2023-01-01",
  "security_deposit_amount": 60000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": false,
  "facts": ["oral tenancy", "deposit 3 months"],
  "evidence_available": ["bank transfer"],
  "missing_information": ["written agreement"]
}
```
- Expected provisions: Gujarat Act (deposit clause unverified), TPA-106, TPA-107, TPA-108, CC-3.
- Expected outcome: escalate.
- Notes: Unregistered/unwritten; TPA fallback.

### EVAL-015 - West Bengal: unverified deposit clause
- Theme: unverified regime
- Jurisdiction: West Bengal, Kolkata
- Difficulty: hard
- Input narrative: Tenant in Kolkata; deposit clause of WB rent statute unconfirmed.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "West Bengal", "city": "Kolkata" },
  "parties": { "tenant": "AC", "landlord": "AD" },
  "property_address": "Kolkata",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 80000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.20,000", "deposit 4 months"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: WB Act (deposit clause unverified), TPA-106, TPA-108, CC-3.
- Expected outcome: escalate (do not assert statutory cap).
- Notes: Treat as contractual/TPA.


### EVAL-016 - Nagaland: TPA-only, no statute
- Theme: TPA-only
- Jurisdiction: Nagaland, Kohima
- Difficulty: easy
- Input narrative: No tenancy statute confirmed; deposit dispute in Kohima.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Nagaland", "city": "Kohima" },
  "parties": { "tenant": "AE", "landlord": "AF" },
  "property_address": "Kohima",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 36000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.12,000", "deposit 3 months"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: TPA-105, TPA-106, TPA-108, CC-3.
- Expected outcome: full_refund (no lawful deduction stated).
- Notes: TPA governs; Civil Court.

### EVAL-017 - Manipur: TPA-only
- Theme: TPA-only
- Jurisdiction: Manipur, Imphal
- Difficulty: easy
- Input narrative: Deposit dispute in Imphal.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Manipur", "city": "Imphal" },
  "parties": { "tenant": "AG", "landlord": "AH" },
  "property_address": "Imphal",
  "rental_start_date": "2023-02-01",
  "vacating_date": "2024-01-31",
  "security_deposit_amount": 24000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.8,000", "deposit 3 months"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: TPA-105, TPA-106, TPA-108, CC-3.
- Expected outcome: full_refund.
- Notes: TPA governs.

### EVAL-018 - Mizoram: TPA-only
- Theme: TPA-only
- Jurisdiction: Mizoram, Aizawl
- Difficulty: easy
- Input narrative: Deposit dispute in Aizawl.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Mizoram", "city": "Aizawl" },
  "parties": { "tenant": "AI", "landlord": "AJ" },
  "property_address": "Aizawl",
  "rental_start_date": "2023-03-01",
  "vacating_date": "2024-02-29",
  "security_deposit_amount": 30000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.10,000", "deposit 3 months"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: TPA-105, TPA-106, TPA-108, CC-3.
- Expected outcome: full_refund.

### EVAL-019 - Meghalaya: TPA-only
- Theme: TPA-only
- Jurisdiction: Meghalaya, Shillong
- Difficulty: easy
- Input narrative: Deposit dispute in Shillong.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Meghalaya", "city": "Shillong" },
  "parties": { "tenant": "AK", "landlord": "AL" },
  "property_address": "Shillong",
  "rental_start_date": "2023-04-01",
  "vacating_date": "2024-03-31",
  "security_deposit_amount": 45000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.15,000", "deposit 3 months"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: TPA-105, TPA-106, TPA-108, CC-3.
- Expected outcome: full_refund.

### EVAL-020 - Ladakh: TPA-only
- Theme: TPA-only
- Jurisdiction: Ladakh, Leh
- Difficulty: easy
- Input narrative: Deposit dispute in Leh.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Ladakh", "city": "Leh" },
  "parties": { "tenant": "AM", "landlord": "AN" },
  "property_address": "Leh",
  "rental_start_date": "2023-05-01",
  "vacating_date": "2024-04-30",
  "security_deposit_amount": 60000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["monthly rent Rs.20,000", "deposit 3 months"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: TPA-105, TPA-106, TPA-108, CC-3.
- Expected outcome: full_refund.

### EVAL-021 - Cross-cutting: limitation period (3 years)
- Theme: cross-cutting; limitation
- Jurisdiction: Maharashtra, Mumbai
- Difficulty: medium
- Input narrative: Tenant vacated 4 years ago; now claims deposit; landlord pleads limitation.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Maharashtra", "city": "Mumbai" },
  "parties": { "tenant": "AO", "landlord": "AP" },
  "property_address": "Mumbai",
  "rental_start_date": "2019-01-01",
  "vacating_date": "2020-01-01",
  "security_deposit_amount": 50000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["vacated 2020-01-01", "no refund", "deposit 2 months"],
  "evidence_available": ["agreement"],
  "missing_information": ["date of demand"]
}
```
- Expected provisions: CC-3 (Limitation Act Art. 22/113, 3 years), TPA-108.
- Expected outcome: escalate (limitation may bar; depends on date of demand/acknowledgement).
- Notes: Compute limitation_expiry_date from deposit-due date.

### EVAL-022 - Cross-cutting: essential services cut (coercion)
- Theme: cross-cutting; essential services
- Jurisdiction: Uttar Pradesh, Lucknow
- Difficulty: medium
- Input narrative: MTA-adopter state; landlord cuts water/electricity to force vacating; tenant claims deposit + compensation.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Uttar Pradesh", "city": "Lucknow" },
  "parties": { "tenant": "AQ", "landlord": "AR" },
  "property_address": "Lucknow",
  "rental_start_date": "2023-06-01",
  "vacating_date": "2024-05-31",
  "security_deposit_amount": 40000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["landlord cut water and electricity for 2 weeks", "tenant vacated under duress"],
  "evidence_available": ["complaint", "photos"],
  "missing_information": []
}
```
- Expected provisions: MTA-20 (compensation up to 2 months' rent), MTA-11, MTA-40, SRA-38, CC-2.
- Expected outcome: partial_refund (deposit refunded + compensation up to 2 months rent).
- Notes: Essential services coercion unlawful; compensation remedy.

### EVAL-023 - Cross-cutting: property sold during tenancy
- Theme: cross-cutting; transferee
- Jurisdiction: Delhi, New Delhi
- Difficulty: medium
- Input narrative: Property sold during tenancy; new owner refuses to refund deposit paid to old owner.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Delhi", "city": "New Delhi" },
  "parties": { "tenant": "AS", "landlord": "AT" },
  "property_address": "New Delhi",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2024-01-01",
  "security_deposit_amount": 60000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["property sold mid-tenancy", "deposit paid to original landlord", "new owner refuses refund"],
  "evidence_available": ["agreement", "sale deed"],
  "missing_information": ["whether deposit transferred to buyer"]
}
```
- Expected provisions: TPA-109 (transferee rights), TPA-108, CC-3.
- Expected outcome: escalate (deposit obligation may pass to transferee; depends on sale terms).
- Notes: TPA § 109 governs transferee of lessor's interest.

### EVAL-024 - Cross-cutting: illegal eviction (dispossession)
- Theme: cross-cutting; possession
- Jurisdiction: Maharashtra, Mumbai
- Difficulty: medium
- Input narrative: Landlord changes locks and removes tenant's belongings; tenant seeks possession + deposit.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Maharashtra", "city": "Mumbai" },
  "parties": { "tenant": "AU", "landlord": "AV" },
  "property_address": "Mumbai",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 80000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["landlord changed locks", "removed belongings", "deposit withheld"],
  "evidence_available": ["photos", "police complaint"],
  "missing_information": []
}
```
- Expected provisions: SRA-6 (dispossessed without due process, 6 months), SRA-5, TPA-108, CC-2.
- Expected outcome: escalate (possession recovery first; deposit claim follows).
- Notes: SRA § 6 suit within 6 months of dispossession.

### EVAL-025 - Cross-cutting: consumer forum attempt
- Theme: cross-cutting; forum shopping
- Jurisdiction: Uttar Pradesh, Lucknow
- Difficulty: medium
- Input narrative: Tenant files consumer complaint for deposit refund in MTA-adopter state; landlord invokes § 40 bar.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Uttar Pradesh", "city": "Lucknow" },
  "parties": { "tenant": "AW", "landlord": "AX" },
  "property_address": "Lucknow",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 40000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["tenant filed consumer complaint", "landlord invokes MTA s.40 bar"],
  "evidence_available": ["complaint copy"],
  "missing_information": []
}
```
- Expected provisions: MTA-40 (bar of civil court jurisdiction), CC-1 (Consumer Protection Act).
- Expected outcome: escalate (forum exclusivity; MTA matters must go to Rent Authority/Court/Tribunal).
- Notes: Consumer forum may be barred where MTA applies.

### EVAL-026 - Edge: void/unenforceable agreement (ICA-65)
- Theme: edge; restitution
- Jurisdiction: Karnataka, Bengaluru
- Difficulty: hard
- Input narrative: Agreement void for illegality; tenant seeks restitution of deposit.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Karnataka", "city": "Bengaluru" },
  "parties": { "tenant": "AY", "landlord": "AZ" },
  "property_address": "Bengaluru",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 50000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["agreement void for illegality", "deposit paid"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: ICA-65 (restitution), ICA-56, TPA-107, CC-3.
- Expected outcome: full_refund (restitution of deposit).
- Notes: Void agreement → restitution of benefit received.

### EVAL-027 - Edge: forfeiture clause excessive (ICA-74)
- Theme: edge; penalty
- Jurisdiction: Maharashtra, Mumbai
- Difficulty: medium
- Input narrative: Agreement forfeits entire deposit on any breach; tenant minor breach; landlord forfeits.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Maharashtra", "city": "Mumbai" },
  "parties": { "tenant": "BA", "landlord": "BB" },
  "property_address": "Mumbai",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 60000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "refund_clause": "entire deposit forfeited on any breach",
  "facts": ["minor breach by tenant", "landlord forfeits full deposit"],
  "evidence_available": ["agreement"],
  "missing_information": []
}
```
- Expected provisions: ICA-74 (reasonable compensation not exceeding stipulated; courts may reduce penalty), ICA-73, CC-3.
- Expected outcome: partial_refund (only reasonable compensation deductible, not full forfeiture).
- Notes: Court may reduce penalty to reasonable amount.

### EVAL-028 - Edge: holding over (TPA-116)
- Theme: edge; hold-over
- Jurisdiction: Karnataka, Bengaluru
- Difficulty: medium
- Input narrative: Tenant holds over with landlord's assent; landlord charges double rent and deducts from deposit.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Karnataka", "city": "Bengaluru" },
  "parties": { "tenant": "BC", "landlord": "BD" },
  "property_address": "Bengaluru",
  "rental_start_date": "2023-01-01",
  "rental_end_date": "2023-12-31",
  "vacating_date": "2024-01-15",
  "security_deposit_amount": 45000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["tenant held over 15 days with landlord assent", "landlord charges double rent"],
  "evidence_available": ["agreement", "messages"],
  "missing_information": []
}
```
- Expected provisions: TPA-116 (effect of holding over), TPA-106, ICA-73, CC-3.
- Expected outcome: partial_refund (rent for hold-over period deductible at agreed/TPA rate, not arbitrary double).
- Notes: Holding over with assent → tenant by sufferance; damages measured reasonably.

### EVAL-029 - Edge: unregistered long lease (RA-49)
- Theme: edge; evidence
- Jurisdiction: Tamil Nadu, Chennai
- Difficulty: medium
- Input narrative: 3-year lease unregistered; deposit terms unprovable; landlord denies deposit amount.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Tamil Nadu", "city": "Chennai" },
  "parties": { "tenant": "BE", "landlord": "BF" },
  "property_address": "Chennai",
  "rental_start_date": "2021-01-01",
  "vacating_date": "2024-01-01",
  "security_deposit_amount": 90000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["3-year lease", "unregistered", "landlord denies deposit amount"],
  "evidence_available": ["bank transfer proof", "unregistered agreement"],
  "missing_information": []
}
```
- Expected provisions: RA-17 (compulsory registration >1 year), RA-49 (effect of non-registration), TPA-107, ICA-65, CC-3.
- Expected outcome: escalate (deposit terms unprovable via unregistered lease; secondary evidence; civil suit).
- Notes: Evidentiary barrier; bank proof helps.

### EVAL-030 - Edge: arrears adjustment from deposit
- Theme: edge; arrears
- Jurisdiction: Uttar Pradesh, Lucknow
- Difficulty: easy
- Input narrative: Tenant owes 1 month rent; landlord adjusts from deposit; refunds balance.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Uttar Pradesh", "city": "Lucknow" },
  "parties": { "tenant": "BG", "landlord": "BH" },
  "property_address": "Lucknow",
  "rental_start_date": "2023-01-01",
  "vacating_date": "2023-12-31",
  "security_deposit_amount": 40000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["1 month rent arrears Rs.20,000", "landlord deducts from deposit"],
  "evidence_available": ["rent ledger"],
  "missing_information": []
}
```
- Expected provisions: MTA-11 (refund after deducting tenant liability), MTA-21 (non-payment ground), CC-3.
- Expected outcome: partial_refund (deposit 40,000 - 20,000 arrears = 20,000).
- Notes: Lawful deduction for arrears permitted.

### EVAL-031 - Edge: damages deduction (repairs)
- Theme: edge; damages
- Jurisdiction: Tamil Nadu, Chennai
- Difficulty: medium
- Input narrative: Landlord deducts Rs.50,000 for repainting/repairs from deposit; tenant claims normal wear and tear.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Tamil Nadu", "city": "Chennai" },
  "parties": { "tenant": "BI", "landlord": "BJ" },
  "property_address": "Chennai",
  "rental_start_date": "2022-01-01",
  "vacating_date": "2024-01-01",
  "security_deposit_amount": 90000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["landlord deducts Rs.50,000 for repairs", "tenant claims normal wear and tear"],
  "evidence_available": ["photos before/after", "quotes"],
  "missing_information": ["itemised repair bills"]
}
```
- Expected provisions: TPA-108 (lessee restore possession; lessor repairs), MTA-11 (deduct tenant liability), ST-TN, ICA-73, CC-3.
- Expected outcome: partial_refund (only proven, reasonable damages deductible; normal wear and tear not deductible).
- Notes: Burden of proof on landlord for damages.

### EVAL-032 - Edge: arrears + damages combined
- Theme: edge; combined deductions
- Jurisdiction: Andhra Pradesh, Visakhapatnam
- Difficulty: hard
- Input narrative: Landlord deducts arrears + damages from 3-month deposit; tenant disputes amounts.
- Input facts:
```json
{
  "case_type": "security_deposit_dispute",
  "jurisdiction": { "state": "Andhra Pradesh", "city": "Visakhapatnam" },
  "parties": { "tenant": "BK", "landlord": "BL" },
  "property_address": "Visakhapatnam",
  "rental_start_date": "2022-06-01",
  "vacating_date": "2024-05-31",
  "security_deposit_amount": 90000,
  "security_deposit_currency": "INR",
  "rental_agreement_exists": true,
  "facts": ["2 months arrears Rs.60,000", "damages claimed Rs.40,000", "deposit Rs.90,000"],
  "evidence_available": ["ledger", "photos"],
  "missing_information": ["itemised bills"]
}
```
- Expected provisions: ST-AP (3-month cap default), MTA-11 (deduct tenant liability), TPA-108, ICA-73, CC-3.
- Expected outcome: partial_refund (lawful deductions limited to proven arrears + reasonable damages; balance refunded; if deductions exceed deposit, landlord may claim balance separately).
- Notes: Combined deduction scenario.


---

## 3. Coverage matrix

| Dimension | Cases |
|---|---|
| MTA-adopter states | EVAL-001..006 |
| TN/AP-model | EVAL-007, 008 |
| Rent-control (no cap) | EVAL-009..015 |
| TPA-only | EVAL-016..020 |
| Cross-cutting | EVAL-021..025 |
| Edge cases | EVAL-026..032 |

State coverage: UP, Assam, J&K, Chandigarh, TN, AP, Maharashtra, Karnataka, Delhi, Telangana, Kerala, Gujarat, West Bengal, Nagaland, Manipur, Mizoram, Meghalaya, Ladakh (18 states/UTs).

---

## 4. Evaluation rubric

For each case, score three sub-tasks:

1. **Intake extraction (0-1):** Are all `expected_facts` correctly extracted from the narrative into
   `SecurityDepositDisputeFacts`? Missing or hallucinated facts reduce score.
2. **Provision retrieval (0-1):** Does the retrieved set include all `expected_provisions` (recall) and
   avoid clearly inapplicable ones (precision)? Score = F1 over provision IDs.
3. **Conclusion (0/1):** Does the final answer's outcome label match `expected_outcome` and cite the
   correct reasoning (cap breach, lawful deduction, forum, limitation)?

**Aggregate:** macro-average across cases; report per-theme and per-state.

**Pass criteria (suggested):** extraction >= 0.85, retrieval F1 >= 0.80, conclusion >= 0.75.

---

## 5. Notes for maintainers

- Add new cases by appending `### EVAL-NNN` blocks; keep IDs sequential.
- When a provision ID or regime changes, update affected cases and the coverage matrix.
- Mark cases that depend on unverified facts with `Difficulty: hard` and an `escalate` outcome.
- Do not assert statutory caps for unverified states (Telangana, West Bengal, Gujarat, Arunachal Pradesh).

