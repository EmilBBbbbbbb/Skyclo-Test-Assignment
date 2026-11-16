# Quickstart & Verification Guide: Contract Settlement Reporter

## Prerequisites

- **Python 3.11+** installed (`python --version`).
- No external packages required (uses only standard library).

---

## 1. Quick Verification Command (Single-Command Run)

Run the CLI utility with default parameters (reads from `data/` for date `2026-11-10`):

```bash
python report.py
```

### Expected Output Summary
- **Contract D-1 (Студия «Свет»)**:
  - Signed: `600 000.00 руб.`
  - Works: `W-11` (100k, done, paid 100k, rem 0), `W-12` (100k, done, paid 100k, rem 0), `W-13` (100k, cancelled, rem 0), `W-14` (100k, done, paid 100k via 15k direct + 85k advance, rem 0), `W-15` (100k, planned, paid 0, rem 100k), `W-16` (100k, planned, paid 0, rem 100k).
  - Total Paid: `315 000.00 руб.` (300k P-1 advance + 15k P-3 direct). P-2 refunded (net 0), P-4 queued (omitted).
  - Remaining to Pay: `285 000.00 руб.`
  - Unallocated Advance: `15 000.00 руб.` (surplus from 300k advance after covering W-11, W-12, and 85k on W-14).
- **Contract D-2 (Иван Петров, дизайнер)**:
  - Signed: `90 000.00 руб.`
  - Works on 10.11.2026: `W-21` (20k, done, paid 20k, rem 0), `W-22` (30k, done, paid 30k, rem 0), `W-23` (40k, completed on 11.11, so on 10.11 it is planned, paid 0, rem 40k).
  - Total Paid: `75 000.00 руб.` (45k P-5 + 25k P-6 + 5k P-7). P-8 paid on 12.11 (omitted).
  - Remaining to Pay: `15 000.00 руб.` (90k signed - 75k paid).
  - Unallocated Advance: `25 000.00 руб.` (75k paid - 50k completed works).
- **Grand Totals**:
  - Total Signed: `690 000.00 руб.`
  - Total Paid: `390 000.00 руб.`
  - Remaining Payable: `300 000.00 руб.`
  - Unallocated Advances: `40 000.00 руб.`

---

## 2. Test Execution Command

Run the full automated unit test suite:

```bash
python -m unittest discover tests -v
```

All unit tests must pass with 100% success rate without warnings.

---

## 3. Alternative Scenarios & Parameters

### Running for a Custom Date
```bash
python report.py --date 2026-10-15
```

### Exporting to CSV
```bash
python report.py --format csv > settlement_report_2026-11-10.csv
```

### Specifying Custom Data Folder
```bash
python report.py --data-dir ./data --date 2026-11-10
```
