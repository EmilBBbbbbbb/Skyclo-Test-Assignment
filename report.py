#!/usr/bin/env python3
"""CLI Entry point for the Contract Advance & Settlement Reporter."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.loader import load_all_data
from src.calculator import calculate_settlements
from src.formatter import format_table_report, format_csv_report


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Формирование отчёта по расчётам и авансам по договорам на заданную дату."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Путь к папке с файлами contracts.csv, works.csv, payments.csv (по умолчанию: data)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2026-11-10",
        help="Отчётная дата среза в формате ГГГГ-ММ-ДД (по умолчанию: 2026-11-10)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv"],
        default="table",
        help="Формат вывода: table (читаемая таблица) или csv (по умолчанию: table)",
    )
    return parser.parse_args()


def main() -> int:
    """Main execution function."""
    args = parse_arguments()

    # Validate cutoff date
    try:
        cutoff_date = datetime.strptime(args.date.strip(), "%Y-%m-%d").date()
    except ValueError:
        sys.stderr.write(
            f"Ошибка: Неверный формат даты '{args.date}'. Ожидается формат ГГГГ-ММ-ДД (например: 2026-11-10).\n"
        )
        return 1

    # Load data from directory
    data_path = Path(args.data_dir)
    try:
        contracts, works, payments = load_all_data(data_path)
    except FileNotFoundError as e:
        sys.stderr.write(f"Ошибка загрузки данных: {e}\n")
        return 1
    except ValueError as e:
        sys.stderr.write(f"Ошибка валидации данных в {data_path}: {e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Непредвиденная ошибка при чтении данных: {e}\n")
        return 1

    # Calculate financial settlements
    try:
        report_result = calculate_settlements(contracts, works, payments, cutoff_date)
    except Exception as e:
        sys.stderr.write(f"Ошибка расчёта взаиморасчётов: {e}\n")
        return 1

    # Output formatted report
    if args.format == "csv":
        sys.stdout.write(format_csv_report(report_result))
    else:
        sys.stdout.write(format_table_report(report_result) + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
