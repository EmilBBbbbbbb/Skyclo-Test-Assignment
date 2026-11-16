"""Financial settlement and advance allocation calculation engine."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Optional

from src.models import (
    Contract,
    Work,
    Payment,
    WorkSettlement,
    ContractSettlement,
    ReportResult,
    to_cents,
)


def determine_effective_status(work: Work, cutoff_date: date) -> str:
    """Determine effective status of a work as of cutoff date."""
    if work.raw_status == "done":
        if work.completed_at is not None and work.completed_at <= cutoff_date:
            return "done"
        return "planned"
    if work.raw_status == "cancelled":
        if work.cancelled_at is not None and work.cancelled_at <= cutoff_date:
            return "cancelled"
        return "planned"
    return "planned"


def calculate_payment_net_amount(payment: Payment, cutoff_date: date) -> Decimal:
    """Calculate effective cash disbursed by payment on cutoff date."""
    if payment.raw_status == "queued":
        return Decimal("0.00")
    if payment.paid_at is None or payment.paid_at > cutoff_date:
        return Decimal("0.00")
    if payment.raw_status == "refunded":
        if payment.refunded_at is not None and payment.refunded_at <= cutoff_date:
            return Decimal("0.00")
        # Payment was made on or before cutoff, and refunded strictly after cutoff
        return payment.amount
    if payment.raw_status == "paid":
        return payment.amount
    return Decimal("0.00")


def calculate_settlements(
    contracts: list[Contract],
    works: list[Work],
    payments: list[Payment],
    cutoff_date: date,
) -> ReportResult:
    """Calculate full financial settlement report on cutoff date."""
    # 1. Filter contracts signed on or before cutoff date
    active_contracts = [c for c in contracts if c.signed_at <= cutoff_date]
    active_contracts.sort(key=lambda c: (c.signed_at, c.contract_id))

    # Group works and payments by contract_id
    works_by_contract: dict[str, list[Work]] = defaultdict(list)
    for w in works:
        works_by_contract[w.contract_id].append(w)

    payments_by_contract: dict[str, list[Payment]] = defaultdict(list)
    for p in payments:
        payments_by_contract[p.contract_id].append(p)

    contract_settlements: list[ContractSettlement] = []
    global_warnings: list[str] = []

    for contract in active_contracts:
        contract_works = works_by_contract.get(contract.contract_id, [])
        contract_payments = payments_by_contract.get(contract.contract_id, [])

        # Settle payments on cutoff date
        direct_payments_by_work: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        general_advances_pool = Decimal("0.00")

        for payment in contract_payments:
            effective_amount = calculate_payment_net_amount(payment, cutoff_date)
            if effective_amount <= Decimal("0.00"):
                continue

            if payment.work_id:
                direct_payments_by_work[payment.work_id] += effective_amount
            else:
                general_advances_pool += effective_amount

        total_contract_paid = sum(direct_payments_by_work.values(), Decimal("0.00")) + general_advances_pool

        # Prepare initial work settlements
        work_settlement_map: dict[str, WorkSettlement] = {}
        for w in contract_works:
            eff_status = determine_effective_status(w, cutoff_date)
            direct_paid = direct_payments_by_work.get(w.work_id, Decimal("0.00"))

            if eff_status == "cancelled":
                ws = WorkSettlement(
                    work_id=w.work_id,
                    contract_id=w.contract_id,
                    title=w.title,
                    price=w.price,
                    effective_status=eff_status,
                    direct_paid=direct_paid,
                    advance_allocated=Decimal("0.00"),
                    total_paid=direct_paid,
                    remaining_payable=Decimal("0.00"),
                )
            else:
                rem = max(Decimal("0.00"), w.price - direct_paid)
                ws = WorkSettlement(
                    work_id=w.work_id,
                    contract_id=w.contract_id,
                    title=w.title,
                    price=w.price,
                    effective_status=eff_status,
                    direct_paid=direct_paid,
                    advance_allocated=Decimal("0.00"),
                    total_paid=direct_paid,
                    remaining_payable=rem,
                )
            work_settlement_map[w.work_id] = ws

        # FIFO advance allocation to completed (done) works
        completed_works = [
            w for w in contract_works
            if work_settlement_map[w.work_id].effective_status == "done"
        ]
        # Order by completion date, then by work_id
        completed_works.sort(key=lambda w: (w.completed_at or date.max, w.work_id))

        remaining_advance_pool = general_advances_pool
        for w in completed_works:
            ws = work_settlement_map[w.work_id]
            unpaid_balance = max(Decimal("0.00"), ws.price - ws.direct_paid)
            if unpaid_balance > Decimal("0.00") and remaining_advance_pool > Decimal("0.00"):
                alloc = min(remaining_advance_pool, unpaid_balance)
                ws.advance_allocated = to_cents(alloc)
                ws.total_paid = to_cents(ws.direct_paid + ws.advance_allocated)
                ws.remaining_payable = to_cents(max(Decimal("0.00"), ws.price - ws.total_paid))
                remaining_advance_pool -= alloc

        # Order work settlements in original work list order
        ordered_work_settlements = [work_settlement_map[w.work_id] for w in contract_works]

        # Calculate totals
        active_works_total = sum(
            (ws.price for ws in ordered_work_settlements if ws.effective_status != "cancelled"),
            Decimal("0.00"),
        )
        all_works_total = sum((ws.price for ws in ordered_work_settlements), Decimal("0.00"))

        allocated_to_active_works = sum(
            (ws.total_paid for ws in ordered_work_settlements if ws.effective_status != "cancelled"),
            Decimal("0.00"),
        )
        unallocated_advance = max(Decimal("0.00"), total_contract_paid - allocated_to_active_works)
        remaining_payable = max(Decimal("0.00"), contract.amount - total_contract_paid)

        # Warning check
        warning_msg: Optional[str] = None
        if contract.amount != active_works_total:
            delta = contract.amount - active_works_total
            warning_msg = (
                f"Сумма договора ({contract.amount:,.2f}) расходится с суммой активных работ "
                f"({active_works_total:,.2f}) на {abs(delta):,.2f} руб."
            ).replace(",", " ")
            global_warnings.append(f"Договор {contract.contract_id}: {warning_msg}")

        contract_settlements.append(
            ContractSettlement(
                contract_id=contract.contract_id,
                contractor=contract.contractor,
                signed_at=contract.signed_at,
                signed_amount=contract.amount,
                active_works_total=active_works_total,
                all_works_total=all_works_total,
                total_paid=total_contract_paid,
                allocated_to_works=allocated_to_active_works,
                unallocated_advance=unallocated_advance,
                remaining_payable=remaining_payable,
                works=ordered_work_settlements,
                warning=warning_msg,
            )
        )

    # Calculate grand totals
    grand_total_signed = sum((cs.signed_amount for cs in contract_settlements), Decimal("0.00"))
    grand_total_paid = sum((cs.total_paid for cs in contract_settlements), Decimal("0.00"))
    grand_total_remaining = sum((cs.remaining_payable for cs in contract_settlements), Decimal("0.00"))
    grand_total_unallocated = sum((cs.unallocated_advance for cs in contract_settlements), Decimal("0.00"))

    return ReportResult(
        cutoff_date=cutoff_date,
        contracts=contract_settlements,
        grand_total_signed=grand_total_signed,
        grand_total_paid=grand_total_paid,
        grand_total_remaining=grand_total_remaining,
        grand_total_unallocated=grand_total_unallocated,
        warnings=global_warnings,
    )
