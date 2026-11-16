# Data Model: Contract Settlement Reporter

## 1. Core Domain Entities (Ingested from CSV)

### `Contract`
Represents an overarching framework agreement with a contractor.
- **`contract_id`**: `str` — Unique identifier (e.g., `'D-1'`, `'D-2'`). Primary Key.
- **`contractor`**: `str` — Contractor name (e.g., `'Студия «Свет»'`).
- **`amount`**: `Decimal` — Total agreed contract ceiling/value in RUB (e.g., `Decimal('600000.00')`).
- **`signed_at`**: `datetime.date` — Effective signature date (e.g., `date(2026, 8, 25)`).

**Invariants**:
- `amount >= Decimal('0.00')`.
- `contract_id` must be non-empty.

---

### `Work`
Represents an individual deliverable or project milestone under a contract.
- **`work_id`**: `str` — Unique identifier (e.g., `'W-11'`). Primary Key.
- **`contract_id`**: `str` — Associated contract identifier. Foreign Key -> `Contract.contract_id`.
- **`title`**: `str` — Work description/title.
- **`price`**: `Decimal` — Agreed price for the work in RUB (e.g., `Decimal('100000.00')`).
- **`raw_status`**: `str` — Exported status string: `'planned'`, `'done'`, or `'cancelled'`.
- **`completed_at`**: `Optional[datetime.date]` — Date when work was accepted (present if `raw_status == 'done'`).
- **`cancelled_at`**: `Optional[datetime.date]` — Date when work was cancelled (present if `raw_status == 'cancelled'`).

**Invariants**:
- `price >= Decimal('0.00')`.
- If `raw_status == 'done'`, `completed_at` should typically be non-null.
- If `raw_status == 'cancelled'`, `cancelled_at` should typically be non-null.

---

### `Payment`
Represents a cash transfer or payment record.
- **`payment_id`**: `str` — Unique identifier (e.g., `'P-1'`). Primary Key.
- **`contract_id`**: `str` — Associated contract identifier. Foreign Key -> `Contract.contract_id`.
- **`work_id`**: `Optional[str]` — Associated work identifier (None or empty string for general contract advance).
- **`purpose`**: `str` — Free-text comment / payment purpose recorded by accountant.
- **`amount`**: `Decimal` — Transaction sum in RUB (e.g., `Decimal('300000.00')`).
- **`raw_status`**: `str` — Exported status string: `'paid'`, `'queued'`, or `'refunded'`.
- **`created_at`**: `datetime.date` — Date payment was recorded in accounting system.
- **`paid_at`**: `Optional[datetime.date]` — Date funds were transferred out.
- **`refunded_at`**: `Optional[datetime.date]` — Date contractor returned funds.

**Invariants**:
- `amount > Decimal('0.00')`.
- If `raw_status == 'paid'`, `paid_at` is non-null.
- If `raw_status == 'refunded'`, both `paid_at` and `refunded_at` are non-null.

---

## 2. Derived Settlement Entities (Point-in-Time as of `cutoff_date`)

### `EffectiveWorkStatus` (Enum/String)
Represents the actual state of a work on the cutoff date:
- `'done'`: Accepted on or before `cutoff_date` (`completed_at <= cutoff_date`).
- `'cancelled'`: Cancelled on or before `cutoff_date` (`cancelled_at <= cutoff_date`).
- `'planned'`: Pending, or completed/cancelled only after `cutoff_date`.

---

### `WorkSettlement`
Calculated financial state of an individual work as of `cutoff_date`.
- **`work_id`**: `str`
- **`contract_id`**: `str`
- **`title`**: `str`
- **`price`**: `Decimal` — Agreed price.
- **`effective_status`**: `str` — `'done'`, `'planned'`, or `'cancelled'`.
- **`direct_paid`**: `Decimal` — Payments specifically tagged with this `work_id`.
- **`advance_allocated`**: `Decimal` — Contract-level advances allocated to this work.
- **`total_paid`**: `Decimal` — `direct_paid + advance_allocated`.
- **`remaining_payable`**: `Decimal`:
  - If `effective_status == 'cancelled'`: `Decimal('0.00')`.
  - Else: `max(Decimal('0.00'), price - total_paid)`.

---

### `ContractSettlement`
Aggregated financial balance for a contract as of `cutoff_date`.
- **`contract_id`**: `str`
- **`contractor`**: `str`
- **`signed_at`**: `datetime.date`
- **`signed_amount`**: `Decimal` — Ceiling amount in contract agreement.
- **`active_works_total`**: `Decimal` — Sum of prices of non-cancelled works as of cutoff date.
- **`all_works_total`**: `Decimal` — Sum of prices of all works.
- **`total_paid`**: `Decimal` — Total net cash disbursed under contract on or before cutoff date.
- **`allocated_to_works`**: `Decimal` — Sum of `total_paid` across works in this contract.
- **`unallocated_advance`**: `Decimal` — `max(Decimal('0.00'), total_paid - allocated_to_works)`.
- **`remaining_payable`**: `Decimal` — `max(Decimal('0.00'), signed_amount - total_paid)`.
- **`works`**: `List[WorkSettlement]` — Detailed lines for works belonging to this contract.

---

### `ReportResult`
Top-level container for an entire audit execution.
- **`cutoff_date`**: `datetime.date`
- **`contracts`**: `List[ContractSettlement]`
- **`grand_total_signed`**: `Decimal`
- **`grand_total_paid`**: `Decimal`
- **`grand_total_remaining`**: `Decimal`
- **`grand_total_unallocated`**: `Decimal`
- **`warnings`**: `List[str]` — Discrepancies (e.g. `amount != works_total`) or unusual data conditions.
