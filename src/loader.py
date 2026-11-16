"""CSV data ingestion and validation."""

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Union

from src.models import Contract, Work, Payment


def parse_date(raw: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD date string. Returns None if empty or None."""
    if not raw:
        return None
    val = raw.strip()
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date format '{val}', expected YYYY-MM-DD: {e}") from e


def parse_decimal(raw: str, field_name: str = "amount") -> Decimal:
    """Parse monetary string to Decimal."""
    val = raw.strip() if raw else ""
    if not val:
        raise ValueError(f"Missing required monetary field '{field_name}'")
    try:
        return Decimal(val)
    except InvalidOperation as e:
        raise ValueError(f"Invalid monetary value '{val}' for {field_name}: {e}") from e


def load_contracts(file_path: Union[Path, str]) -> list[Contract]:
    """Load contracts from CSV file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Contracts file not found: {path}")

    contracts: list[Contract] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                signed_at = parse_date(row.get("signed_at"))
                if signed_at is None:
                    raise ValueError(f"Row {row_num}: signed_at date is required")
                contracts.append(
                    Contract(
                        contract_id=row["contract_id"].strip(),
                        contractor=row["contractor"].strip(),
                        amount=parse_decimal(row["amount"], "amount"),
                        signed_at=signed_at,
                    )
                )
            except KeyError as e:
                raise ValueError(f"Missing required column in {path}: {e}") from e
    return contracts


def load_works(file_path: Union[Path, str]) -> list[Work]:
    """Load works from CSV file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Works file not found: {path}")

    works: list[Work] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                works.append(
                    Work(
                        work_id=row["work_id"].strip(),
                        contract_id=row["contract_id"].strip(),
                        title=row["title"].strip(),
                        price=parse_decimal(row["price"], "price"),
                        raw_status=row["status"].strip(),
                        completed_at=parse_date(row.get("completed_at")),
                        cancelled_at=parse_date(row.get("cancelled_at")),
                    )
                )
            except KeyError as e:
                raise ValueError(f"Missing required column in {path}: {e}") from e
    return works


def load_payments(file_path: Union[Path, str]) -> list[Payment]:
    """Load payments from CSV file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Payments file not found: {path}")

    payments: list[Payment] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                created_at = parse_date(row.get("created_at"))
                if created_at is None:
                    raise ValueError(f"Row {row_num}: created_at date is required")
                payments.append(
                    Payment(
                        payment_id=row["payment_id"].strip(),
                        contract_id=row["contract_id"].strip(),
                        work_id=row.get("work_id"),
                        purpose=row.get("purpose", "").strip(),
                        amount=parse_decimal(row["amount"], "amount"),
                        raw_status=row["status"].strip(),
                        created_at=created_at,
                        paid_at=parse_date(row.get("paid_at")),
                        refunded_at=parse_date(row.get("refunded_at")),
                    )
                )
            except KeyError as e:
                raise ValueError(f"Missing required column in {path}: {e}") from e
    return payments


def load_all_data(data_dir: Union[Path, str]) -> tuple[list[Contract], list[Work], list[Payment]]:
    """Load contracts, works, and payments from a directory."""
    folder = Path(data_dir)
    if not folder.is_dir():
        raise FileNotFoundError(f"Data directory not found: {folder}")
    contracts = load_contracts(folder / "contracts.csv")
    works = load_works(folder / "works.csv")
    payments = load_payments(folder / "payments.csv")
    return contracts, works, payments
