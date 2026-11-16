"""Domain and settlement data models."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


ZERO = Decimal("0.01")


def to_cents(val: Decimal) -> Decimal:
    """Normalize decimal to two decimal places (exact kopecks)."""
    return val.quantize(ZERO)


@dataclass
class Contract:
    """Contract with a contractor."""

    contract_id: str
    contractor: str
    amount: Decimal
    signed_at: date

    def __post_init__(self) -> None:
        if self.amount < Decimal("0.00"):
            raise ValueError(f"Contract amount cannot be negative: {self.amount}")
        self.amount = to_cents(self.amount)


@dataclass
class Work:
    """Work deliverable under a contract."""

    work_id: str
    contract_id: str
    title: str
    price: Decimal
    raw_status: str
    completed_at: Optional[date] = None
    cancelled_at: Optional[date] = None

    def __post_init__(self) -> None:
        if self.price < Decimal("0.00"):
            raise ValueError(f"Work price cannot be negative: {self.price}")
        self.price = to_cents(self.price)
        if self.raw_status not in ("planned", "done", "cancelled"):
            raise ValueError(f"Unknown work raw_status: {self.raw_status}")


@dataclass
class Payment:
    """Cash transaction record."""

    payment_id: str
    contract_id: str
    work_id: Optional[str]
    purpose: str
    amount: Decimal
    raw_status: str
    created_at: date
    paid_at: Optional[date] = None
    refunded_at: Optional[date] = None

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0.00"):
            raise ValueError(f"Payment amount must be positive: {self.amount}")
        self.amount = to_cents(self.amount)
        if self.raw_status not in ("paid", "queued", "refunded"):
            raise ValueError(f"Unknown payment raw_status: {self.raw_status}")
        if self.work_id is not None:
            cleaned = self.work_id.strip()
            self.work_id = cleaned if cleaned else None


@dataclass
class WorkSettlement:
    """Financial settlement state of a single work deliverable on cutoff date."""

    work_id: str
    contract_id: str
    title: str
    price: Decimal
    effective_status: str
    direct_paid: Decimal = field(default_factory=lambda: Decimal("0.00"))
    advance_allocated: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_paid: Decimal = field(default_factory=lambda: Decimal("0.00"))
    remaining_payable: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def __post_init__(self) -> None:
        self.price = to_cents(self.price)
        self.direct_paid = to_cents(self.direct_paid)
        self.advance_allocated = to_cents(self.advance_allocated)
        self.total_paid = to_cents(self.total_paid)
        self.remaining_payable = to_cents(self.remaining_payable)


@dataclass
class ContractSettlement:
    """Financial settlement summary of an entire contract on cutoff date."""

    contract_id: str
    contractor: str
    signed_at: date
    signed_amount: Decimal
    active_works_total: Decimal
    all_works_total: Decimal
    total_paid: Decimal
    allocated_to_works: Decimal
    unallocated_advance: Decimal
    remaining_payable: Decimal
    works: list[WorkSettlement] = field(default_factory=list)
    warning: Optional[str] = None

    def __post_init__(self) -> None:
        self.signed_amount = to_cents(self.signed_amount)
        self.active_works_total = to_cents(self.active_works_total)
        self.all_works_total = to_cents(self.all_works_total)
        self.total_paid = to_cents(self.total_paid)
        self.allocated_to_works = to_cents(self.allocated_to_works)
        self.unallocated_advance = to_cents(self.unallocated_advance)
        self.remaining_payable = to_cents(self.remaining_payable)


@dataclass
class ReportResult:
    """Aggregated financial report for all contracts on cutoff date."""

    cutoff_date: date
    contracts: list[ContractSettlement]
    grand_total_signed: Decimal
    grand_total_paid: Decimal
    grand_total_remaining: Decimal
    grand_total_unallocated: Decimal
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.grand_total_signed = to_cents(self.grand_total_signed)
        self.grand_total_paid = to_cents(self.grand_total_paid)
        self.grand_total_remaining = to_cents(self.grand_total_remaining)
        self.grand_total_unallocated = to_cents(self.grand_total_unallocated)
