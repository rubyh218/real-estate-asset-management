import os
import sys
import unittest

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from debt_metrics import (
    dscr, debt_yield, ltv, breakeven_occupancy,
    _annual_debt_service, size_max_loan,
)


class TestSimpleRatios(unittest.TestCase):

    def test_dscr(self):
        self.assertEqual(dscr(noi=1_250_000, debt_service=1_000_000), 1.25)

    def test_dscr_zero_debt_service(self):
        self.assertEqual(dscr(noi=100, debt_service=0), float("inf"))

    def test_debt_yield(self):
        self.assertAlmostEqual(debt_yield(noi=80_000, loan_balance=1_000_000), 0.08)

    def test_ltv(self):
        self.assertEqual(ltv(loan=65, value=100), 0.65)

    def test_ltv_zero_value(self):
        self.assertEqual(ltv(loan=100, value=0), 0.0)

    def test_breakeven_occupancy(self):
        self.assertEqual(breakeven_occupancy(opex=10, debt_service=20, gpr=100), 0.30)


class TestDebtService(unittest.TestCase):

    def test_interest_only(self):
        # $1M at 6%, IO → $60k annual
        self.assertAlmostEqual(_annual_debt_service(1_000_000, 0.06, 0), 60_000)

    def test_amortizing_30yr_6pct(self):
        # $1M at 6%, 30yr amort → monthly payment ≈ $5,995.50; annual ≈ $71,946
        ds = _annual_debt_service(1_000_000, 0.06, 30)
        self.assertGreater(ds, 71_000)
        self.assertLess(ds, 73_000)

    def test_zero_rate(self):
        # $1.2M at 0% over 10yr amort → $120k annual
        ds = _annual_debt_service(1_200_000, 0.0, 10)
        self.assertAlmostEqual(ds, 120_000)


class TestSizeMaxLoan(unittest.TestCase):

    def test_ltv_binding(self):
        # High NOI relative to value → LTV is binding constraint.
        r = size_max_loan(
            noi=10_000_000, value=50_000_000, rate=0.06, amort_yrs=30,
            max_ltv=0.65, min_dscr=1.25, min_debt_yield=0.08,
        )
        self.assertEqual(r["binding"], "LTV")
        self.assertEqual(r["max_loan"], 32_500_000)  # 0.65 * 50M

    def test_debt_yield_binding(self):
        # With a low rate, the DSCR-implied loan is large, so debt yield binds.
        r = size_max_loan(
            noi=4_000_000, value=100_000_000, rate=0.04, amort_yrs=30,
            max_ltv=0.65, min_dscr=1.25, min_debt_yield=0.10,
        )
        self.assertEqual(r["binding"], "Debt Yield")
        self.assertAlmostEqual(r["max_loan"], 40_000_000, places=0)

    def test_implied_ratios_satisfy_constraints(self):
        r = size_max_loan(
            noi=5_000_000, value=80_000_000, rate=0.07, amort_yrs=30,
            max_ltv=0.65, min_dscr=1.25, min_debt_yield=0.08,
        )
        self.assertGreaterEqual(r["implied_dscr"], 1.25 - 1e-6)
        self.assertGreaterEqual(r["implied_debt_yield"], 0.08 - 1e-6)
        self.assertLessEqual(r["implied_ltv"], 0.65 + 1e-6)


class TestSizeMaxLoanZeroRateIO(unittest.TestCase):

    def test_zero_rate_interest_only_is_not_dscr_bound(self):
        # 0% interest-only debt has no debt service, so DSCR cannot bind.
        # Used to raise ZeroDivisionError.
        r = size_max_loan(
            noi=1_000_000, value=20_000_000, rate=0.0, amort_yrs=0,
            max_ltv=0.65, min_dscr=1.25, min_debt_yield=0.08,
        )
        self.assertEqual(r["constraints"]["DSCR"], float("inf"))
        self.assertNotEqual(r["binding"], "DSCR")


if __name__ == "__main__":
    unittest.main()
