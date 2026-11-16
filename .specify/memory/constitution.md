<!--
Sync Impact Report:
- Version change: Uninitialized scaffold -> 1.0.0
- List of modified principles:
  - Principle 1 (scaffold) -> I. Strict Monetary Precision (No Floating Point)
  - Principle 2 (scaffold) -> II. Minimalist Architecture & Zero Heavy Dependencies
  - Principle 3 (scaffold) -> III. CLI Interface & Single-Command Usability
  - Principle 4 (scaffold) -> IV. Mandatory Delivery Artifacts
  - Principle 5 (scaffold) -> V. Rigorous Edge-Case Unit Testing
- Added sections:
  - Technical Stack & Constraints
  - Development Workflow & Quality Gates
- Removed sections:
  - None
- Follow-up TODOs:
  - None
-->

# Contract Advance Settlement Reporter Constitution

## Core Principles

### I. Strict Monetary Precision (No Floating Point)
Financial calculations MUST NEVER use standard floating-point types (`float` in Python or floating `Number` in TypeScript). All monetary inputs, balances, allocations, and remainders MUST be represented and calculated with exact kopeck precision using either `decimal.Decimal` (Python) or integer kopecks via `BigInt` / integer arithmetic (TypeScript). Rounding errors or precision loss in financial totals are strictly unacceptable.

### II. Minimalist Architecture & Zero Heavy Dependencies
The application MUST operate as a self-contained, lightweight tool. External databases (SQL/NoSQL), Docker containers, web servers, and heavy third-party application frameworks are strictly prohibited. The implementation MUST rely on standard libraries (e.g., Python `csv`, `decimal`, `datetime`, `argparse`, `pathlib`) or minimal Node.js built-ins.

### III. CLI Interface & Single-Command Usability
The primary execution interface MUST be a standalone command-line interface (CLI) script. It must accept target reporting dates (e.g., `--date 2026-11-10`), ingest raw CSV files from `data/`, output clear human-readable settlement reports to stdout, and direct errors to stderr. The application MUST be runnable via a single documented command without complex environment setup.

### IV. Mandatory Delivery Artifacts
The root repository MUST contain four standardized deliverables alongside the source code:
1. Executable CLI script for settlement reporting.
2. `README.md` containing single-command run and test execution instructions.
3. `DECISIONS.md` documenting every business logic and data assumption using the standard 4-part structure: Decision Topic -> Options Considered -> Chosen Option & Rationale -> Impact if Alternative Chosen.
4. `NOTE_FOR_ACCOUNTANT.md` providing a clear, jargon-free summary (strictly 5 to 10 lines) explaining how to read the report and which points require verification.

### V. Rigorous Edge-Case Unit Testing
The financial calculation engine MUST be thoroughly tested with automated unit tests before reporting is finalized. Tests MUST cover critical real-world edge cases, including unlinked advance payments, overpayments, refunds and payment reversals, cancelled or modified works, and strict as-of-date filtering (ensuring future payments and works do not pollute historical report balances).

## Technical Stack & Constraints

- **Language Options**: Python 3.11+ using only standard library modules (`csv`, `decimal`, `datetime`, `argparse`, `pathlib`) OR TypeScript on Node.js without heavy frameworks.
- **Monetary Representation**: Integer kopecks or `Decimal` with fixed 2 decimal places.
- **Data Source**: Read-only ingestion of `data/contracts.csv`, `data/works.csv`, and `data/payments.csv`.
- **Prohibited Technologies**: No SQL/NoSQL databases, no Docker/Podman containers, no HTTP servers/REST APIs, no web frontends.

## Development Workflow & Quality Gates

- **Verification Gate**: 100% automated test pass rate for all unit and edge-case suites using the platform's standard test runner.
- **Assumption Logging Gate**: Every ambiguous data relationship (e.g., matching unlinked contract-level advances to works) MUST be logged in `DECISIONS.md` prior to completion.
- **Accountant Review Gate**: `NOTE_FOR_ACCOUNTANT.md` must be audited for brevity (5–10 lines) and plain language accessibility for non-technical stakeholders.

## Governance

This constitution defines the mandatory architectural, technical, and quality requirements for the project and supersedes any conflicting informal instructions. All future specifications, architectural plans, and code implementations MUST comply with these principles.

Amendments to this constitution require:
1. A documented business or technical justification.
2. A Semantic Version bump (`MAJOR` for principle removals or breaking governance changes, `MINOR` for new principles or constraints, `PATCH` for non-semantic refinements).
3. A Sync Impact Report documenting all changes.

**Version**: 1.0.0 | **Ratified**: 2026-11-16 | **Last Amended**: 2026-11-16
