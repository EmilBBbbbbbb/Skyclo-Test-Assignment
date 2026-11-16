"""Unit tests for CSV loader."""

import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
import tempfile

from src.loader import load_contracts, load_works, load_payments, load_all_data


class TestCSVLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.data_dir = Path("data")

    def test_load_real_contracts(self) -> None:
        contracts = load_contracts(self.data_dir / "contracts.csv")
        self.assertEqual(len(contracts), 2)
        d1 = next(c for c in contracts if c.contract_id == "D-1")
        self.assertEqual(d1.contractor, "Студия «Свет»")
        self.assertEqual(d1.amount, Decimal("600000.00"))
        self.assertEqual(d1.signed_at, date(2026, 8, 25))

        d2 = next(c for c in contracts if c.contract_id == "D-2")
        self.assertEqual(d2.contractor, "Иван Петров, дизайнер")
        self.assertEqual(d2.amount, Decimal("90000.00"))
        self.assertEqual(d2.signed_at, date(2026, 9, 20))

    def test_load_real_works(self) -> None:
        works = load_works(self.data_dir / "works.csv")
        self.assertEqual(len(works), 9)

        w11 = next(w for w in works if w.work_id == "W-11")
        self.assertEqual(w11.contract_id, "D-1")
        self.assertEqual(w11.price, Decimal("100000.00"))
        self.assertEqual(w11.raw_status, "done")
        self.assertEqual(w11.completed_at, date(2026, 9, 20))
        self.assertIsNone(w11.cancelled_at)

        w13 = next(w for w in works if w.work_id == "W-13")
        self.assertEqual(w13.raw_status, "cancelled")
        self.assertEqual(w13.cancelled_at, date(2026, 10, 12))
        self.assertIsNone(w13.completed_at)

        w15 = next(w for w in works if w.work_id == "W-15")
        self.assertEqual(w15.raw_status, "planned")
        self.assertIsNone(w15.completed_at)
        self.assertIsNone(w15.cancelled_at)

    def test_load_real_payments(self) -> None:
        payments = load_payments(self.data_dir / "payments.csv")
        self.assertEqual(len(payments), 8)

        p1 = next(p for p in payments if p.payment_id == "P-1")
        self.assertEqual(p1.contract_id, "D-1")
        self.assertIsNone(p1.work_id)
        self.assertEqual(p1.amount, Decimal("300000.00"))
        self.assertEqual(p1.raw_status, "paid")
        self.assertEqual(p1.paid_at, date(2026, 9, 1))

        p2 = next(p for p in payments if p.payment_id == "P-2")
        self.assertEqual(p2.raw_status, "refunded")
        self.assertEqual(p2.paid_at, date(2026, 9, 2))
        self.assertEqual(p2.refunded_at, date(2026, 9, 10))

        p3 = next(p for p in payments if p.payment_id == "P-3")
        self.assertEqual(p3.work_id, "W-14")

        p4 = next(p for p in payments if p.payment_id == "P-4")
        self.assertEqual(p4.raw_status, "queued")
        self.assertIsNone(p4.paid_at)

    def test_load_all_data(self) -> None:
        contracts, works, payments = load_all_data(self.data_dir)
        self.assertEqual(len(contracts), 2)
        self.assertEqual(len(works), 9)
        self.assertEqual(len(payments), 8)

    def test_missing_file_raises_filenotfound(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_contracts(Path("non_existent_folder/contracts.csv"))

    def test_invalid_date_format_raises_value_error(self) -> None:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as tf:
            tf.write("contract_id,contractor,amount,signed_at\n")
            tf.write("D-99,Test,1000.00,25-08-2026\n")
            temp_path = Path(tf.name)

        try:
            with self.assertRaises(ValueError):
                load_contracts(temp_path)
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
