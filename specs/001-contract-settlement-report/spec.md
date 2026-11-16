# Feature Specification: Contract Settlement Report

**Feature Branch**: `001-contract-settlement-report`

**Created**: 2026-11-16

**Status**: Ready for Planning

**Input**: User description: "Необходимо разработать консольную утилиту для финансового учёта расчётов с подрядчиками на заданную отчётную дату (по умолчанию и для проверки: 10.11.2026). Входные данные находятся в папке data/: contracts.csv, works.csv, payments.csv. Требуемый функционал: 1. Загрузка данных из CSV и фильтрация состояния договоров, работ и платежей строго на указанную дату отчёта. 2. Расчёт по каждой работе: стоимость (цена), сумма уже выплаченных средств, остаток к оплате. 3. Расчёт итогов по каждому договору: общая сумма договора, сумма всех работ, всего выплачено по договору (включая нераспределённые авансы), остаток к оплате по договору и нераспределённый остаток авансов (если есть). 4. Вывод читаемого отчёта в консоль (и/или сохранение в файл), где бухгалтер видит прозрачную картину расчётов на дату. 5. Автоматическая фиксация всех спорных моментов и допущений бизнес-логики в файл DECISIONS.md и формирование короткой памятки бухгалтеру в NOTE_FOR_ACCOUNTANT.md."

## Clarifications

### Session 2026-11-16
- Q: Как распределять платежи по договору с пустым work_id (авансы) между работами? → A: FIFO по хронологии сдачи (completed_at): сначала учитываются прямые платежи с work_id, затем общий аванс закрывает принятые работы в порядке даты их сдачи up to price, а неиспользованный излишек выводится как нераспределённый аванс договора.
- Q: Как учитывать платежи в статусах queued и refunded относительно даты отчёта? → A: Исторический срез на дату (point-in-time): queued исключаются из выплат (деньги не списаны); refunded исключаются из выплат, если refunded_at <= дата отчёта, но считаются выплаченными на дату отчёта, если paid_at <= дата отчёта < refunded_at.
- Q: Как учитывать отменённые работы (cancelled) относительно даты отчёта и при наличии оплат? → A: Исторический статус: если cancelled_at <= дата отчёта, статус фиксируется как 'cancelled' и остаток к оплате = 0 (а произведённые прямые выплаты по ней образуют переплату/аванс к возврату); если cancelled_at > дата отчёта, на дату отчёта работа считается ещё активной со статусом 'planned'.
- Q: Как фильтровать договоры с signed_at > даты отчёта и работы с completed_at > даты отчёта? → A: Строгий point-in-time: договоры с signed_at > даты отчёта исключаются из отчёта на эту дату; работы с completed_at > даты отчёта на дату отчёта имеют эффективный статус 'planned'; платежи с paid_at > даты отчёта не учитываются.
- Q: Как обрабатывать расхождение суммы договора с суммой работ и возможные переплаты? → A: Двойной баланс: в отчёте отображаются и сумма договора (amount), и сумма работ (works_total) с индикацией дельты при расхождении. Остаток к оплате по конкретной работе или договору не может быть отрицательным (при переплате остаток = 0, а сумма переплаты выводится как аванс / переплата).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Financial Settlement Report on Target Date (Priority: P1)

As an accountant, I want to view a settlement report for all contracts and works as of a specific cutoff date (defaulting to 2026-11-10), so that I know exactly how much has been paid and what remains to be paid without manual spreadsheet calculations.

**Why this priority**: Resolves the core business problem stated in the accountant's request. Delivering accurate line-item and contract balances as of a target date provides immediate stand-alone value.

**Independent Test**: Execute the reporting tool against the provided data for target date `2026-11-10`. Verify that contract totals (signed amount, paid to date, remaining payable) and individual work balances match expected accounting calculations on that date.

**Acceptance Scenarios**:

1. **Given** valid contract and work records, **When** a user requests a report as of `2026-11-10`, **Then** all works and payments completed or paid on or before that date are included in the settlement balances.
2. **Given** a work completed after the target date (e.g., `W-23` completed on `2026-11-11`) or a payment made after the target date (e.g., `P-8` paid on `2026-11-12`), **When** the report is generated for `2026-11-10`, **Then** these future events are excluded from the settlement balances as of that date.
3. **Given** no target date is explicitly passed via CLI, **When** the tool is executed, **Then** it defaults to `2026-11-10` and produces the settlement report.

---

### User Story 2 - Transparent Allocation of Contract-Level Advances (Priority: P2)

As an accountant, I want general contract advance payments (which have no specific work ID) to be systematically and transparently allocated against works, so that I can see which works are already settled and whether an unallocated advance balance remains on the contract.

**Why this priority**: Directly resolves the accountant's confusion where payments are made at the contract level without explicit linkage to specific deliverables.

**Independent Test**: Load a contract with multiple works and a general advance payment. Verify that direct work-specific payments are credited first, remaining balances of completed works are covered in chronological order (FIFO) up to their price, and any excess advance is reported at the contract summary level.

**Acceptance Scenarios**:

1. **Given** an advance payment linked to a contract without a `work_id` (e.g., `P-1` on `D-1`), **When** calculating work balances, **Then** funds are allocated to accepted works in chronological order of completion (`completed_at`) up to each work's price.
2. **Given** a work has direct targeted payments (e.g., `P-3` with `work_id=W-14`), **When** calculating its balance, **Then** the direct payment is credited to that work first before any general contract advance is applied.
3. **Given** cumulative payments on a contract exceed the sum of completed work prices as of the report date, **When** the report is rendered, **Then** the surplus is explicitly displayed as "Unallocated Advance" (`Нераспределённый аванс`) at the contract level.

---

### User Story 3 - Accounting for Non-Standard Transaction Lifecycles (Priority: P3)

As an accountant, I want cancelled works, queued payments, and refunded payments to be properly reflected in the balances according to accounting standards, so that liabilities and cash outflows are neither overstated nor understated.

**Why this priority**: Financial reconciliations must correctly handle cancellations and cash reversals to maintain balance sheet accuracy.

**Independent Test**: Ingest records containing a queued payment (`P-4`), a refunded payment (`P-2`), and a cancelled work (`W-13`). Verify that queued payments are omitted from paid totals, refunded payments net to zero once refunded, and cancelled works show zero remaining obligation.

**Acceptance Scenarios**:

1. **Given** a payment with status `queued` (e.g., `P-4`), **When** generating the report, **Then** it is excluded from the settled "paid to date" total because funds have not left the account.
2. **Given** a payment that was paid and subsequently refunded before or on the report date (e.g., `P-2`), **When** generating the report, **Then** its net contribution to "paid to date" is zero.
3. **Given** a work marked as `cancelled` before or on the report date (e.g., `W-13`), **When** generating the report, **Then** its remaining payable is zero.

---

### User Story 4 - Audit Log & Accountant Briefing Artifacts (Priority: P4)

As a returning accountant or auditor, I want all business logic assumptions logged in `DECISIONS.md` and a concise summary note in `NOTE_FOR_ACCOUNTANT.md`, so that stakeholders immediately understand the derivation logic and verification points.

**Why this priority**: Required for organizational transparency, knowledge transfer, and compliance with project delivery standards.

**Independent Test**: Verify that `DECISIONS.md` contains the mandatory 4-part structure for every assumption and that `NOTE_FOR_ACCOUNTANT.md` provides a concise plain-language summary between 5 and 10 lines.

**Acceptance Scenarios**:

1. **Given** domain assumptions (advance allocation ordering, refund cutoffs, cancelled work handling), **When** delivery artifacts are generated, **Then** `DECISIONS.md` logs each decision in the format: Decision -> Options -> Chosen & Why -> Impact of Alternative.
2. **Given** `NOTE_FOR_ACCOUNTANT.md`, **When** reviewed, **Then** it consists of 5 to 10 lines of clear, non-technical Russian text explaining how to read the figures and what to confirm.

---

### Edge Cases

- **Future Transactions (Date Cutoff)**: Payments executed after the report date must not be counted in paid totals; works completed after the report date must be treated as planned/pending on that date.
- **Refund Timing Boundary**: A payment made before the report date but refunded after the report date must be shown as paid as of that historical date. A payment refunded on or before the report date has net zero cash impact.
- **Overpayment on Contract**: If payments exceed total obligations, remaining payable must be zero (not negative), and the excess must be reflected as unallocated advance.
- **Contract with No Payments or No Works**: Must render gracefully without division-by-zero or missing property errors.
- **Cancelled Work with Prepayment**: If direct prepayments were made for a work that is subsequently cancelled, the paid amount must be displayed and flagged as an unearned advance requiring credit note or contractor refund.
- **Free-Text Payment Purpose**: The system must not rely on unstructured heuristic NLP parsing of `purpose`; linkage is strictly governed by `work_id`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest CSV files from `data/contracts.csv`, `data/works.csv`, and `data/payments.csv` and validate data integrity (required columns, date formats, non-negative amounts).
- **FR-002**: System MUST accept an optional report cutoff date parameter via CLI (format `YYYY-MM-DD`), defaulting to `2026-11-10`.
- **FR-003**: System MUST filter all contracts, works, and payments based on the cutoff date, reflecting only transactions and status transitions that took place on or before the cutoff date.
- **FR-004**: System MUST perform all financial calculations with exact kopeck precision (avoiding floating-point arithmetic) to prevent rounding inaccuracies.
- **FR-005**: For each work, the system MUST compute and display: work identifier, contract identifier, title, price, status as of cutoff date, allocated paid amount, and remaining payable amount.
- **FR-006**: For each contract, the system MUST compute and display: contract identifier, contractor name, signed amount, total price of works, delta indicator (if signed amount != works total), total cash paid to date, remaining payable amount to contractor (zero if overpaid), and unallocated advance / overpayment amount.
- **FR-007**: System MUST allocate direct payments (with specified `work_id`) directly to the designated work up to its price.
- **FR-008**: System MUST allocate general contract-level advance payments (empty `work_id`) to completed/accepted works in chronological completion order (FIFO) up to their outstanding balance.
- **FR-009**: System MUST ignore `queued` payments from "paid" totals as of the cutoff date.
- **FR-010**: System MUST exclude refunded amounts from "paid" totals if `refunded_at` is on or before the cutoff date.
- **FR-011**: System MUST set remaining payable to zero for `cancelled` works.
- **FR-012**: System MUST generate human-readable tabular output in the console and provide an option to export or format output cleanly.
- **FR-013**: System MUST maintain and update `DECISIONS.md` documenting every business logic assumption in the mandatory 4-point format.
- **FR-014**: System MUST maintain `NOTE_FOR_ACCOUNTANT.md` containing a 5 to 10 line plain-Russian memo for the returning accountant.

### Key Entities *(include if feature involves data)*

- **Contract**: An overarching agreement with a contractor. Attributes: `contract_id`, `contractor`, `amount` (kopecks), `signed_at`.
- **Work**: A discrete deliverable or task under a contract. Attributes: `work_id`, `contract_id`, `title`, `price` (kopecks), `status` (`planned`, `done`, `cancelled`), `completed_at`, `cancelled_at`.
- **Payment**: A financial cash movement. Attributes: `payment_id`, `contract_id`, `work_id` (optional), `purpose`, `amount` (kopecks), `status` (`paid`, `queued`, `refunded`), `created_at`, `paid_at`, `refunded_at`.
- **Work Settlement Line**: Derived report entity representing the financial status of a work on the cutoff date. Attributes: `work_id`, `title`, `price`, `paid_amount`, `remaining_amount`, `effective_status`.
- **Contract Settlement Summary**: Derived report entity representing total contract financial health. Attributes: `contract_id`, `contractor`, `signed_amount`, `works_total`, `total_paid`, `remaining_payable`, `unallocated_advance`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running the reporting tool produces the complete financial reconciliation on `2026-11-10` in under 2 seconds.
- **SC-002**: 100% of monetary calculations across contracts and works balance to the exact kopeck with zero rounding discrepancy (i.e., `Total Paid + Remaining Payable = Total Obligations`, accounting for unallocated advance).
- **SC-003**: The accountant can determine the remaining payment obligation for any contract or work at a glance without performing manual additions or cross-referencing multiple files.
- **SC-004**: The generated `NOTE_FOR_ACCOUNTANT.md` adheres strictly to the 5–10 line length limit and avoids developer jargon, enabling immediate comprehension by non-technical accounting personnel.
- **SC-005**: All domain assumptions are fully cataloged in `DECISIONS.md` with 100% adherence to the 4-part decision template.

## Assumptions

- **Data Availability**: Input files `contracts.csv`, `works.csv`, and `payments.csv` are accessible in the relative `data/` directory.
- **Advance Allocation Logic**: Unlinked contract advances are allocated chronologically (FIFO) to works that are completed (`done`) as of the cutoff date. Planned works do not consume advance payments unless explicitly tagged or until completed.
- **Direct vs. Advance Priority**: Direct payments explicitly linked to a `work_id` are applied to that work before general contract advances are drawn.
- **Payment Purpose Free-Text**: Free-text in `purpose` is not parsed with fragile heuristic NLP regexes; formal linkage relies strictly on `work_id`.
- **Refund Effect**: A payment refunded on or before the cutoff date has net cash outflow 0. If refunded after the cutoff date, it was cash-out on the cutoff date.
- **Queued Payments**: Payments in status `queued` represent intent to pay but not cleared cash outflow; hence they are omitted from settled payments.
