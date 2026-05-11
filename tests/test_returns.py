import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from returns import xirr, moic, hold_period, parse_date, _xnpv


class TestXIRR(unittest.TestCase):

    def test_simple_one_year_10pct(self):
        # Use a non-leap year span (365 days exactly) so years = 1.0.
        flows = [(date(2021, 1, 1), -1000.0), (date(2022, 1, 1), 1100.0)]
        self.assertAlmostEqual(xirr(flows), 0.10, places=4)

    def test_two_year_50pct_total_return(self):
        # -1000 at t0, +1500 at t0 + 2yrs → IRR = 1500/1000 ^ (1/2) - 1 ≈ 22.474%
        # Use 2021-2023 to avoid leap-day distortion (2x 365-day years).
        flows = [(date(2021, 1, 1), -1000.0), (date(2023, 1, 1), 1500.0)]
        self.assertAlmostEqual(xirr(flows), 0.22474, places=3)

    def test_multi_flow_zero_npv_at_solution(self):
        flows = [
            (date(2020, 1, 15), -1_000_000.0),
            (date(2022, 6, 30), 200_000.0),
            (date(2025, 12, 15), 1_400_000.0),
        ]
        rate = xirr(flows)
        self.assertLess(abs(_xnpv(rate, flows)), 1.0)  # NPV at IRR ≈ 0

    def test_requires_both_signs(self):
        with self.assertRaises(ValueError):
            xirr([(date(2020, 1, 1), -100.0), (date(2021, 1, 1), -200.0)])
        with self.assertRaises(ValueError):
            xirr([(date(2020, 1, 1), 100.0), (date(2021, 1, 1), 200.0)])


class TestMOIC(unittest.TestCase):

    def test_basic_2x(self):
        flows = [(date(2020, 1, 1), -1000.0), (date(2025, 1, 1), 2000.0)]
        m, contrib, dist = moic(flows)
        self.assertEqual(m, 2.0)
        self.assertEqual(contrib, 1000.0)
        self.assertEqual(dist, 2000.0)

    def test_no_contributions_returns_inf(self):
        flows = [(date(2025, 1, 1), 1000.0)]
        m, contrib, dist = moic(flows)
        self.assertEqual(m, float("inf"))
        self.assertEqual(contrib, 0.0)
        self.assertEqual(dist, 1000.0)

    def test_partial_distribution(self):
        flows = [
            (date(2020, 1, 1), -1000.0),
            (date(2022, 1, 1), 500.0),
            (date(2024, 1, 1), 800.0),
        ]
        m, _, _ = moic(flows)
        self.assertAlmostEqual(m, 1.3, places=10)


class TestHoldPeriod(unittest.TestCase):

    def test_exactly_one_year(self):
        # 2021-01-01 → 2022-01-01 is exactly 365 days (no leap).
        flows = [(date(2021, 1, 1), -100.0), (date(2022, 1, 1), 100.0)]
        self.assertAlmostEqual(hold_period(flows), 1.0, places=5)


class TestParseDate(unittest.TestCase):

    def test_iso(self):
        self.assertEqual(parse_date("2025-12-15"), date(2025, 12, 15))

    def test_us_slash(self):
        self.assertEqual(parse_date("12/15/2025"), date(2025, 12, 15))

    def test_bad_format_raises(self):
        with self.assertRaises(ValueError):
            parse_date("not-a-date")


if __name__ == "__main__":
    unittest.main()
