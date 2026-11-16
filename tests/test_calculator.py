"""Unit tests for settlement calculator and edge cases."""

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.loader import load_all_data
from src.models import Contract, Work, Payment
from src.calculator import calculate_settlements


class TestCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.data_dir = Path("data")
        self.contracts, self.works, self.payments = load_all_data(self.data_dir)

    def test_real_data_settlement_on_2026_11_10(self) -> None:
        """Verify exact figures on the primary audit verification date 2026-11-10."""
        cutoff = date(2026, 11, 10)
        report = calculate_settlements(self.contracts, self.works, self.payments, cutoff)

        self.assertEqual(report.cutoff_date, cutoff)
        self.assertEqual(len(report.contracts), 2)

        # Contract D-1
        d1 = next(c for c in report.contracts if c.contract_id == "D-1")
        self.assertEqual(d1.contractor, "Студия «Свет»")
        self.assertEqual(d1.signed_amount, Decimal("600000.00"))
        # Total paid = P-1 (300k) + P-3 (15k) = 315,000 (P-2 refunded, P-4 queued)
        self.assertEqual(d1.total_paid, Decimal("315000.00"))
        self.assertEqual(d1.remaining_payable, Decimal("285000.00"))
        self.assertEqual(d1.unallocated_advance, Decimal("15000.00"))

        # Check D-1 works
        w11 = next(w for w in d1.works if w.work_id == "W-11")
        self.assertEqual(w11.effective_status, "done")
        self.assertEqual(w11.total_paid, Decimal("100000.00"))
        self.assertEqual(w11.remaining_payable, Decimal("0.00"))

        w12 = next(w for w in d1.works if w.work_id == "W-12")
        self.assertEqual(w12.effective_status, "done")
        self.assertEqual(w12.total_paid, Decimal("100000.00"))
        self.assertEqual(w12.remaining_payable, Decimal("0.00"))

        w13 = next(w for w in d1.works if w.work_id == "W-13")
        self.assertEqual(w13.effective_status, "cancelled")
        self.assertEqual(w13.total_paid, Decimal("0.00"))
        self.assertEqual(w13.remaining_payable, Decimal("0.00"))

        w14 = next(w for w in d1.works if w.work_id == "W-14")
        self.assertEqual(w14.effective_status, "done")
        self.assertEqual(w14.direct_paid, Decimal("15000.00"))
        self.assertEqual(w14.advance_allocated, Decimal("85000.00"))
        self.assertEqual(w14.total_paid, Decimal("100000.00"))
        self.assertEqual(w14.remaining_payable, Decimal("0.00"))

        w15 = next(w for w in d1.works if w.work_id == "W-15")
        self.assertEqual(w15.effective_status, "planned")
        self.assertEqual(w15.total_paid, Decimal("0.00"))
        self.assertEqual(w15.remaining_payable, Decimal("100000.00"))

        w16 = next(w for w in d1.works if w.work_id == "W-16")
        self.assertEqual(w16.effective_status, "planned")
        self.assertEqual(w16.total_paid, Decimal("0.00"))
        self.assertEqual(w16.remaining_payable, Decimal("100000.00"))

        # Contract D-2
        d2 = next(c for c in report.contracts if c.contract_id == "D-2")
        self.assertEqual(d2.contractor, "Иван Петров, дизайнер")
        self.assertEqual(d2.signed_amount, Decimal("90000.00"))
        # Paid = P-5 (45k) + P-6 (25k) + P-7 (5k) = 75,000 (P-8 is 12.11 -> excluded)
        self.assertEqual(d2.total_paid, Decimal("75000.00"))
        self.assertEqual(d2.remaining_payable, Decimal("15000.00"))
        # Completed works: W-21 (20k) + W-22 (30k) = 50k. Advance unallocated = 75k - 50k = 25,000
        self.assertEqual(d2.unallocated_advance, Decimal("25000.00"))

        w21 = next(w for w in d2.works if w.work_id == "W-21")
        self.assertEqual(w21.effective_status, "done")
        self.assertEqual(w21.total_paid, Decimal("20000.00"))
        self.assertEqual(w21.remaining_payable, Decimal("0.00"))

        w22 = next(w for w in d2.works if w.work_id == "W-22")
        self.assertEqual(w22.effective_status, "done")
        self.assertEqual(w22.total_paid, Decimal("30000.00"))
        self.assertEqual(w22.remaining_payable, Decimal("0.00"))

        w23 = next(w for w in d2.works if w.work_id == "W-23")
        # W-23 completed on 2026-11-11, so on 2026-11-10 it is planned!
        self.assertEqual(w23.effective_status, "planned")
        self.assertEqual(w23.total_paid, Decimal("0.00"))
        self.assertEqual(w23.remaining_payable, Decimal("40000.00"))

        # Grand Totals
        self.assertEqual(report.grand_total_signed, Decimal("690000.00"))
        self.assertEqual(report.grand_total_paid, Decimal("390000.00"))
        self.assertEqual(report.grand_total_remaining, Decimal("300000.00"))
        self.assertEqual(report.grand_total_unallocated, Decimal("40000.00"))

    def test_future_cutoff_date_includes_w23_and_p8(self) -> None:
        """On 2026-11-15, W-23 is done and P-8 (20k) is paid, resulting in 5k overpayment."""
        cutoff = date(2026, 11, 15)
        report = calculate_settlements(self.contracts, self.works, self.payments, cutoff)

        d2 = next(c for c in report.contracts if c.contract_id == "D-2")
        # 45k + 25k + 5k + 20k = 95,000 paid for a 90,000 contract (5,000 overpayment)
        self.assertEqual(d2.total_paid, Decimal("95000.00"))
        self.assertEqual(d2.remaining_payable, Decimal("0.00"))
        self.assertEqual(d2.unallocated_advance, Decimal("5000.00"))

        w23 = next(w for w in d2.works if w.work_id == "W-23")
        self.assertEqual(w23.effective_status, "done")
        self.assertEqual(w23.total_paid, Decimal("40000.00"))
        self.assertEqual(w23.remaining_payable, Decimal("0.00"))

    def test_queued_payment_never_counted(self) -> None:
        """P-4 is queued with 150k and should never be counted as cash disbursed."""
        cutoff = date(2026, 11, 20)
        report = calculate_settlements(self.contracts, self.works, self.payments, cutoff)
        d1 = next(c for c in report.contracts if c.contract_id == "D-1")
        # Still 315,000, not 465,000
        self.assertEqual(d1.total_paid, Decimal("315000.00"))

    def test_refund_point_in_time_behavior(self) -> None:
        """P-2 paid on 2026-09-02, refunded on 2026-09-10."""
        # On 2026-09-05: P-2 is paid and not yet refunded
        cutoff_pre_refund = date(2026, 9, 5)
        report_pre = calculate_settlements(self.contracts, self.works, self.payments, cutoff_pre_refund)
        d1_pre = next(c for c in report_pre.contracts if c.contract_id == "D-1")
        # P-1 (300k) + P-2 (50k) = 350k
        self.assertEqual(d1_pre.total_paid, Decimal("350000.00"))

        # On 2026-09-11: P-2 has been refunded, so net cash is 0
        cutoff_post_refund = date(2026, 9, 11)
        report_post = calculate_settlements(self.contracts, self.works, self.payments, cutoff_post_refund)
        d1_post = next(c for c in report_post.contracts if c.contract_id == "D-1")
        self.assertEqual(d1_post.total_paid, Decimal("300000.00"))

    def test_future_signed_contract_excluded(self) -> None:
        """Contracts signed after cutoff date must be omitted."""
        # D-1 signed on 2026-08-25, D-2 signed on 2026-09-20
        cutoff = date(2026, 9, 10)
        report = calculate_settlements(self.contracts, self.works, self.payments, cutoff)
        self.assertEqual(len(report.contracts), 1)
        self.assertEqual(report.contracts[0].contract_id, "D-1")

    def test_cancelled_work_with_direct_payment(self) -> None:
        """If a cancelled work had direct payment, remaining is 0, payment remains tracked."""
        contracts = [Contract("D-99", "Подрядчик", Decimal("100000.00"), date(2026, 1, 1))]
        works = [
            Work("W-991", "D-99", "Работа 1", Decimal("50000.00"), "cancelled", cancelled_at=date(2026, 2, 1))
        ]
        payments = [
            Payment("P-991", "D-99", "W-991", "Аванс", Decimal("20000.00"), "paid", date(2026, 1, 15), paid_at=date(2026, 1, 15))
        ]
        report = calculate_settlements(contracts, works, payments, date(2026, 3, 1))
        d99 = report.contracts[0]
        self.assertEqual(d99.total_paid, Decimal("20000.00"))
        # Cancelled work has remaining = 0
        self.assertEqual(d99.works[0].remaining_payable, Decimal("0.00"))
        self.assertEqual(d99.works[0].total_paid, Decimal("20000.00"))
        # Contract remaining payable: 100k - 20k = 80k
        self.assertEqual(d99.remaining_payable, Decimal("80000.00"))
        # The 20k paid on cancelled work acts as unallocated advance for remaining scope
        self.assertEqual(d99.unallocated_advance, Decimal("20000.00"))


if __name__ == "__main__":
    unittest.main()
