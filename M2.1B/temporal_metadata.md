# M2.1B — Temporal Metadata Recommendations

**Scope:** How to capture, version, and query time-dependent legal facts for the M2.1B knowledge base
(effective dates, amendments, MTA state notifications, rent thresholds, limitation periods) so that
the AI Lawyer can apply the *law in force on the relevant date*.

**Companion files:** `provision_inventory.md`, `state_applicability_table.md`, `source_register.md`.

---

## 1. Why temporal metadata matters for this domain

Security-deposit disputes are highly date-sensitive:

- The **applicable tenancy act** may have changed mid-tenancy (e.g., a state adopting the MTA in 2023
  vs. a tenancy started in 2019 under the old rent-control act).
- The **MTA itself is not self-executing** — it commences on the date notified by the State Government
  (MTA § 1), not the date of the Union Cabinet approval (2021).
- **Rent thresholds** in rent-control acts (Delhi ₹3,500; Karnataka ₹3,500/₹2,000) are revised by
  amendment; exemption status depends on the rent *at the relevant time*.
- **Limitation periods** (Limitation Act, 1963 — Art. 22 / Art. 113, typically 3 years for deposit
  recovery) run from the date the deposit became due (vacating date / demand).
- **Deposit caps** (TN/AP 3-month "save agreement to the contrary") interact with agreement dates.
- **Forum rules** change with amendments (e.g., Karnataka Rent (Amendment) Bill, 2025).

Without temporal metadata, the system will apply the *current* law to *past* tenancies and produce
wrong answers.

---

## 2. Recommended metadata schema (per provision / per regime)

Store each legal fact as a versioned record with the following fields. Proposed as YAML/JSON objects.

```yaml
provision_record:
  id: "MTA-11"                      # stable ID from provision_inventory.md
  law: "Model Tenancy Act, 2021 (as adopted by State)"
  jurisdiction:
    country: "IN"
    state: "UP"                      # ISO/state code; "ALL" for central statutes
    level: "state"                   # central | state | ut
  section: "§ 11"
  topic: "Security deposit"
  text_summary: "Cap 2 months (residential), 6 months (non-residential); refund on handing over vacant possession after deducting tenant liability."
  status: "current"                  # current | amended | repealed | model | uncertain
  effective_from: "2021-07-??"       # ISO date or null if unknown
  effective_to: null                 # null = still in force
  commenced_by: "State Government notification under MTA § 1 (state-notified date)"
  applies_to_tenancies_from: "2021-07-??"   # tenancy start date threshold
  applies_to_tenancies_to: null
  amended_by:
    - source_id: "SRC-xx"
      amendment: "..."
      effective: "YYYY-MM-DD"
  supersedes: ["OLD-ACT-... "]        # prior regime IDs
  superseded_by: null
  source_ids: ["SRC-01", "SRC-02"]
  verified_on: "2026-11-06"
  verified_by: "M2.1B research"
  confidence: "high"                 # high | medium | low
  notes: "Urban areas only (UP)."
```

### 2.1 Minimum required fields (must not be null)

- `id`, `law`, `jurisdiction.state`, `section`, `topic`, `status`, `source_ids`, `verified_on`.
- `effective_from` may be null only if genuinely unknown — must be flagged `confidence: low` and listed in the verification backlog.

### 2.2 State-regime record (for the applicability table)

```yaml
regime_record:
  state: "UP"
  regime: "MTA-adopter"
  act: "U.P. Regulation of Urban Premises Tenancy Act, 2021 (Act No. 16 of 2021)"
  deposit_cap_residential_months: 2
  deposit_cap_non_residential_months: 6
  cap_overridable: false              # true for TN/AP ("save agreement to the contrary")
  forum: "Rent Authority (Deputy Collector) → Rent Tribunal (District Judge)"
  mta_commencement_notified: "YYYY-MM-DD"   # state-notified date; null if unknown
  applies_to_tenancies_from: "YYYY-MM-DD"
  rent_thresholds:                    # for rent-control exemptions
    - { name: "exemption_rent_monthly", value: null, currency: "INR", effective_from: null }
  last_verified: "2026-11-06"
  verification_status: "enacted"      # enacted | contested | unverified | uncertain
```

---

## 3. Time-handling rules for the AI Lawyer (application logic)

1. **Determine the relevant date first.** For a deposit dispute, the relevant date is the **tenancy start date**
   (which regime was in force when the tenancy began) and the **vacating date** (when the refund became due).
   Do not use "today" to pick the regime.
2. **Regime selection:** Use `applies_to_tenancies_from` / `applies_to_tenancies_to` on the regime record.
   If the tenancy started before MTA commencement, fall back to the prior regime (TPA/rent-control).
3. **Amendment handling:** If a provision was amended, apply the version in force on the relevant date.
   Keep all versions; never overwrite — append with `effective_from`/`effective_to`.
4. **MTA adoption lag:** In MTA-adopter states, require evidence that (a) the state notified commencement
   and (b) the parties submitted a written agreement to the Rent Authority (MTA §§ 1, 4). If either is
   absent, treat as TPA/contract regime.
5. **Thresholds:** Rent-control exemption thresholds (Delhi ₹3,500; Karnataka ₹3,500/₹2,000) are applied
   using the rent in force at tenancy start; if unknown, mark `uncertain` and ask the user.
6. **Limitation:** Compute the limitation expiry from the deposit-due date (vacating date + demand),
   typically 3 years (Limitation Act, 1963 Art. 22/113). Surface as `limitation_expiry_date` in output.
7. **Staleness:** Any record with `verified_on` older than 90 days (or `confidence: low`) must trigger a
   re-verification prompt before being used in a final answer.

---

## 4. Temporal fields to add to the intake schema (M1/M2)

Recommend adding to `SecurityDepositDisputeFacts` (backend/app/schemas/case.py):

- `tenancy_start_date` (already `rental_start_date`)
- `tenancy_end_date` / `vacating_date` (already present)
- `deposit_due_date` (derived: vacating date + agreement's refund window; default MTA § 11 = on handing over possession)
- `applicable_regime` (derived: MTA-adopter / TN/AP / rent-control / TPA-only)
- `applicable_regime_effective_from`
- `limitation_expiry_date`
- `regime_confidence` (high/medium/low/uncertain)

These are *derived* facts and should be stored with `source: "derived"` in fact provenance.

---

## 5. Recommended persistence / storage approach

- Store provision records and regime records as **versioned JSON/YAML files** under `M2.1B/` (this repo)
  and load into a small SQLite/JSON store at runtime for M2 (RAG over provisions).
- Never mutate a record in place; append a new version with `effective_from`.
- Keep a `verification_backlog.md` (in `research_notes/`) listing records with null/low-confidence dates.
- Add a `last_verified` field and a CI check (future) that fails if any `current` record is > 180 days stale.
- Cache official PDFs under `M2.1B/sources/` with a filename pattern:
  `SRC-XX__short-title__YYYY-MM-DD.pdf` and record SHA-256 in `source_register.md`.

---

## 6. Known temporal unknowns (backlog)

1. Exact state-notified commencement dates for all MTA-adopter states (MTA § 1) — unknown; must be
   fetched from state gazettes.
2. Whether Arunachal Pradesh's 2022 Act has been notified and commenced.
3. Chandigarh extension validity (S.O. 2265(E), 6 May 2026) — pending judicial resolution.
4. Karnataka Rent (Amendment) Bill, 2025 — enactment status unknown.
5. Madhya Pradesh 2010 Bill — enactment status unknown.
6. UP Act 16 of 2021 — whether it applies statewide or urban-only, and its commencement date.

These are tracked in `research_notes/verification_backlog.md`.

---

## 7. Source references

- SRC-01, SRC-04, SRC-14, SRC-18, SRC-24 (see `source_register.md`).
