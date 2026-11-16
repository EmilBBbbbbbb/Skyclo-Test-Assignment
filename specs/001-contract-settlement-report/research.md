# Phase 0 Research: Contract Settlement Reporter

## 1. Runtime & Technology Stack Selection

### Decision
Python 3.11+ using exclusively the Python Standard Library (`csv`, `decimal`, `datetime`, `argparse`, `pathlib`, `unittest`).

### Rationale
- **Zero Installation Overhead**: Requires no `pip install`, `virtualenv`, `node_modules`, or compiler tools. Any reviewer with Python 3.11+ installed can immediately run the tool and test suite with standard commands.
- **Native Financial Precision**: Python's `decimal` module implements the General Decimal Arithmetic Specification (IEEE 754-2008 compatible) natively, avoiding all floating-point roundoff errors without third-party libraries.
- **Robust Built-in CLI & Parsing**: `argparse`, `csv`, and `pathlib` provide all necessary command-line argument validation, structured file handling, and cross-platform path resolution.
- **Built-in Test Runner**: `unittest` provides comprehensive unit testing and test discovery (`python -m unittest discover tests`) out of the box.

### Alternatives Considered
- **TypeScript / Node.js**: While TS with integer cents or BigInt supports exact math, running TS requires Node.js, `npm install`, TypeScript transpilation (`tsc`), or runners (`tsx`, `ts-node`), creating environment friction for reviewers.
- **Python with Third-Party Libraries (pandas, rich, tabulate)**: Adds external dependency weight and installation failure risk for a simple CSV transformation task. Prohibited by project constitution.

---

## 2. Monetary Precision & Rounding Policy

### Decision
All monetary figures are parsed directly as `decimal.Decimal` objects from raw CSV strings (e.g., `Decimal(row['amount'])`), strictly normalized to 2 decimal places (`Decimal('0.01')`) representing exact kopecks.

### Rationale
- Standard binary `float` representations inevitably introduce binary rounding inaccuracies (e.g. `0.1 + 0.2 = 0.30000000000000004`).
- Financial audits require exact conservation: `Total Obligations == Total Paid + Remaining Payable - Unallocated Advance`.
- Decimal ensures 100% exact penny arithmetic and clean formatting with `.quantize(Decimal('0.01'))`.

### Alternatives Considered
- **Integer Cents (`int` * 100)**: Clean, but requires constant conversion when parsing strings and formatting outputs (divmod / 100). `Decimal` is idiomatic in Python and handles fixed-point operations cleanly.
- **Float**: Strictly prohibited by Principle I of the Project Constitution.

---

## 3. Contract-Level Advance Allocation Strategy (Unlinked Payments)

### Decision
Hybrid Direct-First + FIFO (First-In-First-Out) on Accepted Works by Completion Date (`completed_at`):
1. **Direct Work Allocation**: Payments with a specified `work_id` are credited exclusively to that work up to its price.
2. **General Advance Pool**: All payments without `work_id` (where `status == 'paid'` and not refunded as of cutoff date) are aggregated into a contract advance pool.
3. **Sequential Waterfall**: General advances are allocated chronologically to works with effective status `done` as of the cutoff date, ordered by `completed_at` (ascending), then by `work_id`.
4. **Cap at Price**: An accepted work cannot consume more advance than its remaining unpaid price (`price - direct_paid`).
5. **Surplus Advance**: Any advance remaining after all accepted works are fully paid is designated as "Unallocated Advance" (`Нераспределённый аванс`) at the contract summary level.
6. **Planned Works**: Planned works remain with `paid = 0` and full remaining payable until they are completed and accepted.

### Rationale
- Directly resolves the accountant's core problem: "платежи по договору ни к какой работе не привязаны, а мне надо понимать, за что мы уже рассчитались."
- In commercial contracts, advances legally cover work as deliverables are completed and accepted by act (Акт приёмки-передачи). Uncompleted planned works cannot claim advance realization until accepted.
- Prevents arbitrary proportional splitting that leaves all works partially unpaid.

### Alternatives Considered
- **Proportional Allocation**: Spreading advances proportionally across all planned and done works. Rejected because it produces messy fractional payments and fails to tell the accountant which specific jobs are settled.
- **Order by Contract Order (work_id)**: Allocating by list order regardless of completion. Rejected because completing a work later does not give it priority over an earlier accepted work.
- **Unallocated Only**: Leaving all unlinked payments at the contract level and reporting zero paid on individual works. Rejected because it fails to answer "за что мы уже рассчитались".

---

## 4. Point-in-Time Historical Cutoff Architecture

### Decision
Strict Point-in-Time Filtering based on the user-provided `--date` (default: `2026-11-10`):
- **Contracts**: Included if `signed_at <= cutoff_date`. If `signed_at > cutoff_date`, the contract is ignored for the report.
- **Works**:
  - If `status == 'done'` and `completed_at <= cutoff_date` -> Effective status: `done`.
  - If `status == 'done'` and `completed_at > cutoff_date` -> Effective status: `planned` (work was not yet completed on cutoff date).
  - If `status == 'cancelled'` and `cancelled_at <= cutoff_date` -> Effective status: `cancelled` (obligation = 0).
  - If `status == 'cancelled'` and `cancelled_at > cutoff_date` -> Effective status: `planned` (work had not yet been cancelled on cutoff date).
  - If `status == 'planned'` -> Effective status: `planned`.
- **Payments**:
  - `status == 'queued'`: Excluded from paid totals (funds never left account).
  - `status == 'paid'`: Included if `paid_at <= cutoff_date`. Excluded if `paid_at > cutoff_date`.
  - `status == 'refunded'`:
    - If `refunded_at <= cutoff_date`: Net paid amount = 0 (refund completed).
    - If `paid_at <= cutoff_date < refunded_at`: Counted as paid on the cutoff date (funds were with contractor on that date).
    - If `paid_at > cutoff_date`: Excluded completely.

### Rationale
- Enables retrospective point-in-time auditing: running the report for any historical date yields the exact financial truth as it was at that moment in time.
- Correctly models real data in the repository: `W-23` was completed on `2026-11-11` and `P-8` was paid on `2026-11-12`, both after the verification date `2026-11-10`.

### Alternatives Considered
- **Static Status Snapshot**: Relying on the CSV `status` column regardless of dates. Rejected because it leaks future completions (`W-23`) and future payments (`P-8`) into a historical report.

---

## 5. Discrepancy & Overpayment Handling (Double Balance)

### Decision
The report calculates and presents both figures:
1. `amount` from `contracts.csv` (signed legal commitment).
2. `works_total` (sum of prices of active works).
- If `amount != works_total`, the report flags the delta in a warning note.
- Contract remaining payable is computed as `max(Decimal(0), amount - total_paid)`.
- If cumulative payments exceed obligations, remaining payable is `0.00`, and the excess is explicitly categorized as "Unallocated Advance / Overpayment" (`Нераспределённый аванс / переплата`).
- Work remaining payable is `max(Decimal(0), price - paid_for_work)` for active works, and `0.00` for cancelled works.

### Rationale
- Prevents negative remaining liabilities on works and contracts.
- Gives the accountant immediate visibility into whether the contract budget matches the actual scope of work orders.
