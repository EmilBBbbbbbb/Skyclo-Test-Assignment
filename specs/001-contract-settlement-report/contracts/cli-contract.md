# CLI Interface Contract: `report.py`

## Synopsis

```bash
python report.py [--data-dir PATH] [--date YYYY-MM-DD] [--format {table,csv}]
```

## Arguments & Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--data-dir` | Path (`str`) | `data` | Path to directory containing `contracts.csv`, `works.csv`, `payments.csv`. |
| `--date` | Date (`YYYY-MM-DD`) | `2026-11-10` | Cutoff date for point-in-time financial reconciliation. |
| `--format` | Choice: `table`, `csv` | `table` | Output format: formatted ASCII/Unicode table to stdout, or CSV stream. |
| `-h`, `--help` | Flag | N/A | Show help message and exit. |

## Exit Codes

| Code | Meaning | Condition |
|---|---|---|
| `0` | Success | Report successfully generated and written to stdout. |
| `1` | Data / Parameter Error | Missing input files, invalid CSV syntax, bad date format, or corrupted numbers. Details written to stderr. |

## Standard Streams

- **`stdout`**:
  - If `--format table`: Clean human-readable tabular settlement report and contract summary cards.
  - If `--format csv`: Header and comma-separated records suitable for piping or redirecting into a `.csv` file.
- **`stderr`**:
  - Informational errors, validation failure messages, missing file notices, or data integrity warnings.

## Output Specification

### 1. Table Format (`--format table`, default)

```text
================================================================================
ФИНАНСОВЫЙ ОТЧЁТ ПО ДОГОВОРАМ И РАБОТАМ (на дату: 10.11.2026)
================================================================================

ДОГОВОР: D-1 | Подрядчик: Студия «Свет» | Подписан: 2026-08-25
Сумма по договору: 600 000.00 руб. | Сумма работ: 600 000.00 руб.
Всего выплачено:   315 000.00 руб. | Остаток к оплате: 285 000.00 руб.
Нераспределённый аванс: 15 000.00 руб.
--------------------------------------------------------------------------------
Код    | Название                 | Статус    |      Цена | Выплачено |   Остаток
--------------------------------------------------------------------------------
W-11   | Съёмка: весенняя колл... | done      | 100000.00 | 100000.00 |      0.00
W-12   | Съёмка: лето             | done      | 100000.00 | 100000.00 |      0.00
W-13   | Съёмка: аксессуары       | cancelled | 100000.00 |      0.00 |      0.00
W-14   | Съёмка: осень            | done      | 100000.00 | 100000.00 |      0.00
W-15   | Съёмка: зима             | planned   | 100000.00 |      0.00 | 100000.00
W-16   | Съёмка: новогодняя       | planned   | 100000.00 |      0.00 | 100000.00
--------------------------------------------------------------------------------

...

================================================================================
ИТОГО ПО ВСЕМ ДОГОВОРАМ:
Сумма договоров:         690 000.00 руб.
Всего выплачено:         390 000.00 руб.
Остаток к оплате:        300 000.00 руб.
Нераспределённый аванс:   40 000.00 руб.
================================================================================
```

### 2. CSV Format (`--format csv`)

Comma-separated format containing:
`contract_id,contractor,work_id,work_title,status,price,paid,remaining,unallocated_contract_advance`
