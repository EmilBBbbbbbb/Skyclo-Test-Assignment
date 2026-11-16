# Implementation Plan: Contract Settlement Reporter

**Branch**: `001-contract-settlement-report` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-contract-settlement-report/spec.md`

## Summary

The project provides an automated command-line financial settlement reporter for contracts, deliverables, and payments as of a designated cutoff date (defaulting to `2026-11-10`). The technical approach uses Python 3.11+ exclusively with standard library modules (`csv`, `decimal`, `datetime`, `argparse`, `pathlib`, `unittest`), guaranteeing 100% dependency-free execution for reviewers without `pip install`. Monetary math is computed in exact integer kopecks via `decimal.Decimal`, completely barring floating-point drift. Unlinked advance payments are allocated via direct-payment priority followed by FIFO allocation across completed works by `completed_at`, and all accounting decisions are documented in `DECISIONS.md` alongside a concise memo in `NOTE_FOR_ACCOUNTANT.md`.

## Technical Context

**Language/Version**: Python 3.11+ (Standard Library only)

**Primary Dependencies**: None (Standard modules only: `csv`, `decimal`, `datetime`, `argparse`, `pathlib`, `unittest`)

**Storage**: File-based CSV ingestion (`data/contracts.csv`, `data/works.csv`, `data/payments.csv`)

**Testing**: Standard Python `unittest` (`python -m unittest discover tests`)

**Target Platform**: Cross-platform (Windows, Linux, macOS)

**Project Type**: Standalone CLI Application

**Performance Goals**: Complete execution and terminal output generation in under 0.2 seconds (far exceeding the < 2.0s specification threshold)

**Constraints**: Strict monetary math via `decimal.Decimal` (exact kopecks, no `float`), zero third-party dependencies (`pip install` prohibited), no database, no Docker, no HTTP/web servers

**Scale/Scope**: Clean modular architecture (~500 LOC Python), comprehensive edge-case test suite, 4 mandatory delivery artifacts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Compliance Status | Justification / Implementation Evidence |
|---|---|---|
| **I. Strict Monetary Precision (No Float)** | **PASS** | All currency attributes in `models.py`, `calculator.py`, and `formatter.py` use `decimal.Decimal` quantized to `Decimal('0.01')`. Binary `float` and floating `Number` are strictly prohibited. |
| **II. Minimalist Zero-Dependency Architecture** | **PASS** | Only Python 3.11+ built-in modules are used. No external libraries, no database, no Docker containers, no web frameworks. |
| **III. CLI Interface & Single-Command Usability** | **PASS** | Primary entry point is `report.py` accepting `--data-dir`, `--date`, `--format`. Single-command execution: `python report.py`. |
| **IV. Mandatory Delivery Artifacts** | **PASS** | Plan incorporates all 4 required root artifacts: executable `report.py`, `README.md` with 1-command instructions, `DECISIONS.md` (4-part format), and `NOTE_FOR_ACCOUNTANT.md` (5–10 lines). |
| **V. Rigorous Edge-Case Unit Testing** | **PASS** | Test suite in `tests/test_calculator.py` explicitly tests unlinked advances, date cutoffs, refunded payments, queued payments, cancelled works, and contract-work discrepancies. |

## Project Structure

### Documentation (this feature)

```text
specs/001-contract-settlement-report/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0 research & technology decisions
├── data-model.md        # Phase 1 data entities and settlement schema
├── quickstart.md        # Phase 1 quickstart & verification guide
├── contracts/           # Phase 1 interface contracts
│   └── cli-contract.md  # CLI command parameters and I/O contract
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code (repository root)

```text
.
├── report.py            # Executable CLI entry point (argparse, loader, calculator, formatter)
├── src/
│   ├── __init__.py
│   ├── models.py        # Data classes: Contract, Work, Payment, WorkSettlement, ContractSettlement
│   ├── loader.py        # Robust CSV parsing, date conversion, Decimal validation
│   ├── calculator.py    # Point-in-time filtering, direct payments, FIFO advance allocation
│   └── formatter.py     # Clean table and CSV formatting for console output
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py # Unit tests for financial reconciliation and edge cases
│   └── test_loader.py     # Unit tests for CSV ingestion and validation
├── data/                # Ingested datasets
│   ├── contracts.csv
│   ├── works.csv
│   ├── payments.csv
│   └── FORMAT.md
├── DECISIONS.md         # Mandatory decision log (Problem -> Options -> Choice -> Impact)
├── NOTE_FOR_ACCOUNTANT.md # Mandatory 5-10 line note for accountant
└── README.md            # Mandatory project overview and single-command run instructions
```

**Structure Decision**: A clean single-package modular architecture. The root `report.py` acts as the immediate entry point, delegating parsing to `src/loader.py`, financial reconciliation and advance allocation to `src/calculator.py`, and rendering to `src/formatter.py`. Models in `src/models.py` use native `dataclasses` with `Decimal` fields.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. The design adheres strictly to all constitutional principles and technical boundaries.*
