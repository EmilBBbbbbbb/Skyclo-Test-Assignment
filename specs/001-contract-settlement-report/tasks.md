# Tasks: Contract Settlement Reporter

**Input**: Design documents from `specs/001-contract-settlement-report/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/cli-contract.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/cli-contract.md`

**Tests**: Unit tests are REQUIRED per Constitution Principle V and user requirements, covering all edge cases (unlinked advances, refunds, cancelled works, and date cutoffs).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [X] [TaskID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [X] T001 Create project directory structure (`src/`, `tests/`) per implementation plan
- [X] T002 Initialize Python package markers in `src/__init__.py` and `tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and CSV ingestion infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Implement core domain models in `src/models.py`: `Contract` (`contract_id: str`, `contractor: str`, `amount: Decimal >= 0.00`, `signed_at: date`), `Work` (`work_id: str`, `contract_id: str`, `title: str`, `price: Decimal >= 0.00`, `raw_status: str in ('planned','done','cancelled')`, `completed_at: Optional[date]`, `cancelled_at: Optional[date]`), and `Payment` (`payment_id: str`, `contract_id: str`, `work_id: Optional[str]`, `purpose: str`, `amount: Decimal > 0.00`, `raw_status: str in ('paid','queued','refunded')`, `created_at: date`, `paid_at: Optional[date]`, `refunded_at: Optional[date]`) using standard library `dataclasses` and `decimal.Decimal`
- [X] T004 [P] Implement unit tests for CSV ingestion in `tests/test_loader.py` validating parsing of `contracts.csv`, `works.csv`, and `payments.csv`, date conversions, Decimal parsing, and error handling for missing files
- [X] T005 Implement CSV loader module in `src/loader.py` to parse CSV files into domain models with validation of date format `YYYY-MM-DD`, non-negative amounts, and error handling for corrupt data

**Checkpoint**: Foundation ready — domain models and loader verified with tests. User story implementation can now begin.

---

## Phase 3: User Story 1 - Financial Settlement Report on Target Date (Priority: P1) 🎯 MVP

**Goal**: Ingest CSV data, filter records by cutoff date (`signed_at <= cutoff_date`, `paid_at <= cutoff_date`, works `completed_at <= cutoff_date`), compute baseline work and contract balances, and output a readable report.

**Independent Test**: Execute `python report.py --date 2026-11-10` and verify that future events (`W-23` completed on 11.11, `P-8` paid on 12.11) are excluded and contract totals match expected accounting calculations on that date.

### Tests for User Story 1 ⚠️

- [X] T006 [P] [US1] Create unit tests in `tests/test_calculator.py` for point-in-time date filtering verifying that contracts with `signed_at > cutoff_date` and payments with `paid_at > cutoff_date` are excluded, and works with `completed_at > cutoff_date` have effective status `'planned'`

### Implementation for User Story 1

- [X] T007 [US1] Implement settlement data structures `WorkSettlement`, `ContractSettlement`, and `ReportResult` in `src/models.py` with monetary fields quantized to `Decimal('0.01')`
- [X] T008 [US1] Implement point-in-time filtering and basic reconciliation engine in `src/calculator.py` (`filter_and_calculate_settlements`) for target cutoff dates
- [X] T009 [P] [US1] Implement ASCII table formatter and CSV formatter in `src/formatter.py` (`format_table_report`, `format_csv_report`) per `specs/001-contract-settlement-report/contracts/cli-contract.md`
- [X] T010 [US1] Implement CLI entry point in `report.py` with `argparse` supporting `--data-dir` (default: `data`), `--date` (default: `2026-11-10`), `--format` (`table`/`csv`), and standard error handling to `sys.stderr`

**Checkpoint**: User Story 1 (MVP) is fully functional and testable independently.

---

## Phase 4: User Story 2 - Transparent Allocation of Contract-Level Advances (Priority: P2)

**Goal**: Systematically allocate general contract advances (empty `work_id`) to completed works using direct-payment priority and chronological FIFO order by `completed_at`, tracking unallocated advances at the contract level.

**Independent Test**: Test contracts with general advance payments (e.g., `D-1` with 300k advance, `D-2` with 75k advances) and verify that direct payments are credited first, completed works are covered in order of completion date up to price, and excess advance is reported as `unallocated_advance`.

### Tests for User Story 2 ⚠️

- [X] T011 [P] [US2] Add unit tests in `tests/test_calculator.py` for FIFO advance allocation verifying direct payment priority on `W-14`, sequential advance coverage of `W-11` and `W-12`, and calculation of unallocated advances for `D-1` (15,000.00 руб.) and `D-2` (25,000.00 руб.)

### Implementation for User Story 2

- [X] T012 [US2] Implement direct payment prioritization and FIFO advance allocation algorithm in `src/calculator.py` (`_allocate_advances`)
- [X] T013 [US2] Update `src/formatter.py` to display the "Нераспределённый аванс" line in contract summaries and grand totals in both table and CSV formats

**Checkpoint**: User Stories 1 AND 2 are functional and verified.

---

## Phase 5: User Story 3 - Accounting for Non-Standard Transaction Lifecycles (Priority: P3)

**Goal**: Correctly handle `queued` payments (exclude from cash paid), `refunded` payments (net 0 if `refunded_at <= cutoff_date`, but paid if `paid_at <= cutoff_date < refunded_at`), and `cancelled` works (remaining obligation = 0, prior payments treated as advance subject to recovery/refund).

**Independent Test**: Ingest test records with `P-2` (refunded), `P-4` (queued), and `W-13` (cancelled) and verify that `queued` payments are omitted, refunds net to zero after refund date, cancelled works have remaining = 0, and overpayments do not produce negative balances.

### Tests for User Story 3 ⚠️

- [X] T014 [P] [US3] Add unit tests in `tests/test_calculator.py` for non-standard lifecycles: queued payment exclusion (`P-4`), historical point-in-time refund tracking (`P-2` on 2026-09-05 vs 2026-09-15), cancelled work handling (`W-13`), and overpayment ceiling (`remaining >= 0.00`)

### Implementation for User Story 3

- [X] T015 [US3] Implement refund lifecycle logic, queued payment filtering, cancelled work obligation zeroing, and non-negative payable clamping in `src/calculator.py`
- [X] T016 [US3] Add double-balance comparison (signed contract amount vs sum of active works) with discrepancy warning generation in `src/calculator.py` and `src/formatter.py`

**Checkpoint**: User Stories 1, 2, and 3 are functional and verified.

---

## Phase 6: User Story 4 - Audit Log & Accountant Briefing Artifacts (Priority: P4)

**Goal**: Document all data decisions in `DECISIONS.md` according to the required 4-part structure, write a concise plain-language summary in `NOTE_FOR_ACCOUNTANT.md` (5–10 lines), and write `README.md` with a single-command quickstart guide.

**Independent Test**: Audit `DECISIONS.md` for the 4-part format on all decisions, count lines (5-10) and verify plain Russian in `NOTE_FOR_ACCOUNTANT.md`, and test the single-command instruction in `README.md`.

### Implementation for User Story 4

- [X] T017 [P] [US4] Create `DECISIONS.md` in repository root logging all 5 domain decisions (FIFO allocation, point-in-time refunds, cancelled works, date cutoffs, double balance) using the required format: Problem -> Options -> Chosen & Rationale -> Impact of Alternative
- [X] T018 [P] [US4] Create `NOTE_FOR_ACCOUNTANT.md` in repository root containing a concise 5 to 10 line note in plain Russian explaining how to interpret paid/remaining balances and what to verify upon return from vacation
- [X] T019 [US4] Update `README.md` in repository root with single-command run instructions (`python report.py`), test suite instructions (`python -m unittest discover tests -v`), and project architecture overview

**Checkpoint**: All 4 user stories and mandatory delivery artifacts are in place.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end verification and quality gate validation.

- [X] T020 [P] Run end-to-end quickstart validation per `specs/001-contract-settlement-report/quickstart.md` across both table and CSV output modes
- [X] T021 Run full automated test suite with `python -m unittest discover tests -v` and confirm 100% pass rate with zero external dependencies

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately.
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Delivers working MVP.
- **User Story 2 (Phase 4)**: Extends US1 calculation with FIFO advance distribution.
- **User Story 3 (Phase 5)**: Extends US1/US2 with lifecycle rules (refunds, queues, cancellations).
- **User Story 4 (Phase 6)**: Builds delivery artifacts based on finalized logic.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### Parallel Opportunities

- Within Phase 2: `T003` (models) and `T004` (loader tests) can be written in parallel.
- Within Phase 3: `T006` (tests) and `T009` (formatter) can run in parallel.
- Within Phase 6: `T017` (`DECISIONS.md`) and `T018` (`NOTE_FOR_ACCOUNTANT.md`) can be drafted in parallel.
- Within Phase 7: `T020` (validation) and `T021` (unit tests) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1): point-in-time filtering, basic calculations, table/csv formatting, CLI script.
3. Validate MVP with `python report.py --date 2026-11-10`.

### Incremental Delivery
1. Foundation (Phase 1 + 2) -> Models and CSV loader working.
2. Increment 1 (Phase 3, US1) -> CLI reporting on target date (MVP).
3. Increment 2 (Phase 4, US2) -> Transparent advance distribution and unallocated advance tracking.
4. Increment 3 (Phase 5, US3) -> Edge-case accounting (refunds, queues, cancellations).
5. Increment 4 (Phase 6, US4) -> Delivery documentation (`DECISIONS.md`, `NOTE_FOR_ACCOUNTANT.md`, `README.md`).
6. Polish (Phase 7) -> Final end-to-end validation.
