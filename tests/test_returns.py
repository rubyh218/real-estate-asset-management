import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from returns import xirr, moic, hold_period, parse_date, _xnpv, count_sign_changes, xirr_all_roots, xmirr


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


class TestCountSignChanges(unittest.TestCase):

    def test_conventional_flows_one_sign_change(self):
        flows = [(date(2020, 1, 1), -1000.0), (date(2025, 1, 1), 1500.0)]
        self.assertEqual(count_sign_changes(flows), 1)

    def test_multiple_distributions_still_one_sign_change(self):
        flows = [
            (date(2020, 1, 1), -1000.0),
            (date(2021, 1, 1), 200.0),
            (date(2022, 1, 1), 300.0),
            (date(2025, 1, 1), 800.0),
        ]
        self.assertEqual(count_sign_changes(flows), 1)

    def test_recap_pattern_three_sign_changes(self):
        # Cap call, distribution, recap call, distribution
        flows = [
            (date(2020, 1, 1), -1000.0),
            (date(2021, 1, 1),   800.0),
            (date(2022, 1, 1),  -500.0),  # recap call
            (date(2025, 1, 1),  1200.0),
        ]
        self.assertEqual(count_sign_changes(flows), 3)

    def test_zero_amounts_ignored(self):
        flows = [
            (date(2020, 1, 1), -1000.0),
            (date(2021, 1, 1),     0.0),
            (date(2022, 1, 1),  1500.0),
        ]
        self.assertEqual(count_sign_changes(flows), 1)

    def test_single_or_zero_flows(self):
        self.assertEqual(count_sign_changes([]), 0)
        self.assertEqual(count_sign_changes([(date(2020, 1, 1), -1000.0)]), 0)


class TestXIRRAllRoots(unittest.TestCase):

    def test_conventional_flows_return_single_root(self):
        flows = [(date(2021, 1, 1), -1000.0), (date(2022, 1, 1), 1100.0)]
        roots = xirr_all_roots(flows)
        self.assertEqual(len(roots), 1)
        self.assertAlmostEqual(roots[0], 0.10, places=4)

    def test_classic_two_irr_textbook_case(self):
        # 1320*v^2 - 2300*v + 1000 = 0 has roots v = 0.9091 and v = 0.8333,
        # giving IRRs of 10% and 20%. xirr() returns just one (the root
        # closest to zero); we expect xirr_all_roots to find BOTH.
        flows = [
            (date(2021, 1, 1), -1000.0),
            (date(2022, 1, 1),  2300.0),
            (date(2023, 1, 1), -1320.0),
        ]
        roots = xirr_all_roots(flows)
        self.assertEqual(len(roots), 2)
        self.assertAlmostEqual(roots[0], 0.10, places=3)
        self.assertAlmostEqual(roots[1], 0.20, places=3)

    def test_npv_is_zero_at_every_returned_root(self):
        flows = [
            (date(2021, 1, 1), -1000.0),
            (date(2022, 1, 1),  2300.0),
            (date(2023, 1, 1), -1320.0),
        ]
        for r in xirr_all_roots(flows):
            self.assertLess(abs(_xnpv(r, flows)), 1e-3)

    def test_requires_both_signs(self):
        with self.assertRaises(ValueError):
            xirr_all_roots([(date(2020, 1, 1), -100.0), (date(2021, 1, 1), -200.0)])


class TestXMIRR(unittest.TestCase):

    def test_zero_rates_reduces_to_geometric_return(self):
        # With both rates = 0, MIRR = (FV_pos / PV_neg)^(1/yrs) - 1
        # = (1500/1000)^(1/1) - 1 = 0.50 over 1 year
        flows = [(date(2021, 1, 1), -1000.0), (date(2022, 1, 1), 1500.0)]
        self.assertAlmostEqual(xmirr(flows, 0.0, 0.0), 0.50, places=4)

    def test_known_value_with_reinvest(self):
        # -1000 at t0, +600 at t1, +600 at t2 (3 non-leap years).
        # PV_neg at t0 = 1000.
        # FV_pos at t2 = 600 * 1.10^1 + 600 * 1.10^0 = 660 + 600 = 1260.
        # MIRR = (1260/1000)^(1/2) - 1 = sqrt(1.26) - 1 ≈ 0.12250
        flows = [
            (date(2021, 1, 1), -1000.0),
            (date(2022, 1, 1),   600.0),
            (date(2023, 1, 1),   600.0),
        ]
        self.assertAlmostEqual(xmirr(flows, finance_rate=0.10, reinvest_rate=0.10), 0.12250, places=4)

    def test_always_unique_on_multi_sign_change_case(self):
        # The classic two-IRR case: xirr() gives one (often wrong) answer;
        # MIRR gives exactly one, defined.
        flows = [
            (date(2021, 1, 1), -1000.0),
            (date(2022, 1, 1),  2300.0),
            (date(2023, 1, 1), -1320.0),
        ]
        m = xmirr(flows, finance_rate=0.08, reinvest_rate=0.08)
        # The exact value depends on the rates; here we just assert it's
        # finite, real, and in a sensible band (well above -1, well below 1).
        self.assertGreater(m, -0.5)
        self.assertLess(m, 0.5)
        # And it must be deterministic.
        self.assertEqual(m, xmirr(flows, 0.08, 0.08))

    def test_requires_both_signs(self):
        with self.assertRaises(ValueError):
            xmirr([(date(2020, 1, 1), -100.0), (date(2021, 1, 1), -200.0)])

    def test_requires_nonzero_horizon(self):
        # Same date for both flows — undefined.
        with self.assertRaises(ValueError):
            xmirr([(date(2020, 1, 1), -100.0), (date(2020, 1, 1), 200.0)])


class TestParseDate(unittest.TestCase):

    def test_iso(self):
        self.assertEqual(parse_date("2025-12-15"), date(2025, 12, 15))

    def test_us_slash(self):
        self.assertEqual(parse_date("12/15/2025"), date(2025, 12, 15))

    def test_bad_format_raises(self):
        with self.assertRaises(ValueError):
            parse_date("not-a-date")


class TestXIRRBracketRobustness(unittest.TestCase):

    def test_irr_above_1000pct_expands_bracket(self):
        # True IRR = 4,900% — beyond the original +1000% upper bound. The old
        # bisection silently returned the bracket endpoint (10.0) as if it
        # were the answer.
        flows = [(date(2021, 1, 1), -100.0), (date(2022, 1, 1), 5000.0)]
        r = xirr(flows)
        self.assertAlmostEqual(r, 49.0, places=2)
        self.assertLess(abs(_xnpv(r, flows)), 0.01)

    def test_two_root_stream_returns_an_actual_root(self):
        # NPV has two real roots (10% and 20%). The old bracket geometry
        # collapsed to -100%, which is not a root at all. Now: a genuine
        # root, deterministically the one closest to zero.
        flows = [
            (date(2021, 1, 1), -1000.0),
            (date(2022, 1, 1),  2300.0),
            (date(2023, 1, 1), -1320.0),
        ]
        r = xirr(flows)
        self.assertAlmostEqual(r, 0.10, places=4)
        self.assertLess(abs(_xnpv(r, flows)), 1e-3)


if __name__ == "__main__":
    unittest.main()
