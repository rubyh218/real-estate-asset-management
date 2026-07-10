import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from yield_maintenance import (
    analyze_prepay_timing,
    compute_ym_penalty,
    _add_months,
    _months_between,
)


class TestComputeYMPenalty(unittest.TestCase):

    def test_zero_when_loan_rate_at_or_below_treasury(self):
        # No make-whole owed if reinvest rate >= loan rate.
        self.assertEqual(
            compute_ym_penalty(upb=10_000_000, loan_rate=0.04, treasury_rate=0.04,
                               remaining_months=12, amort_yrs=0),
            0.0,
        )
        self.assertEqual(
            compute_ym_penalty(upb=10_000_000, loan_rate=0.04, treasury_rate=0.05,
                               remaining_months=12, amort_yrs=0),
            0.0,
        )

    def test_zero_when_no_remaining_months(self):
        self.assertEqual(
            compute_ym_penalty(upb=10_000_000, loan_rate=0.05, treasury_rate=0.03,
                               remaining_months=0, amort_yrs=0),
            0.0,
        )

    def test_io_one_month_hand_calc(self):
        # IO loan, 1 month remaining, 5% loan, 3% Treasury.
        # Foregone interest = 10M * (0.05 - 0.03) / 12 = $16,666.67
        # Discount at Treasury monthly: / (1 + 0.03/12) = $16,625.13
        result = compute_ym_penalty(
            upb=10_000_000, loan_rate=0.05, treasury_rate=0.03,
            remaining_months=1, amort_yrs=0,
        )
        expected = 10_000_000 * (0.05 - 0.03) / 12 / (1 + 0.03/12)
        self.assertAlmostEqual(result, expected, places=2)

    def test_io_scales_linearly_with_upb(self):
        # YM is linear in UPB for IO loans.
        r1 = compute_ym_penalty(10_000_000, 0.05, 0.03, 24, 0)
        r2 = compute_ym_penalty(20_000_000, 0.05, 0.03, 24, 0)
        self.assertAlmostEqual(r2, 2 * r1, places=2)

    def test_amortizing_lower_than_io_for_same_term(self):
        # Amortizing loan has declining balance → less foregone interest
        # than IO, so YM penalty should be lower.
        ym_io = compute_ym_penalty(10_000_000, 0.05, 0.03, 60, amort_yrs=0)
        ym_amort = compute_ym_penalty(10_000_000, 0.05, 0.03, 60, amort_yrs=30)
        self.assertLess(ym_amort, ym_io)
        # But not by a huge margin (early years dominate).
        self.assertGreater(ym_amort, ym_io * 0.90)

    def test_zero_spread_zero_penalty(self):
        self.assertEqual(
            compute_ym_penalty(10_000_000, 0.04, 0.04, 60, 0), 0.0
        )

    def test_longer_remaining_term_larger_penalty(self):
        # More months of foregone interest → larger penalty.
        short = compute_ym_penalty(10_000_000, 0.05, 0.03, 12, 0)
        long = compute_ym_penalty(10_000_000, 0.05, 0.03, 60, 0)
        self.assertGreater(long, short)


class TestAnalyzePrepayTiming(unittest.TestCase):

    def test_past_maturity_no_penalty(self):
        r = analyze_prepay_timing(
            upb=10_000_000, loan_rate=0.05, treasury_rate=0.03,
            maturity=date(2025, 1, 1), today=date(2026, 6, 1),
            amort_yrs=0,
        )
        self.assertEqual(r.current_ym_penalty, 0.0)
        self.assertEqual(r.savings_if_wait_to_open, 0.0)

    def test_in_open_period_flat_fee(self):
        # 1 month before maturity → in 3-month open period.
        r = analyze_prepay_timing(
            upb=10_000_000, loan_rate=0.05, treasury_rate=0.03,
            maturity=date(2026, 7, 1), today=date(2026, 6, 1),
            open_period_months=3, open_period_fee_pct=0.01, amort_yrs=0,
        )
        self.assertTrue(r.in_open_period)
        self.assertEqual(r.current_ym_penalty, 100_000.0)   # 1% of $10M
        self.assertEqual(r.open_period_penalty, 100_000.0)
        self.assertEqual(r.savings_if_wait_to_open, 0.0)

    def test_in_ym_period_with_spread_savings_positive(self):
        # Wide spread, 2 years until open period → significant savings.
        r = analyze_prepay_timing(
            upb=50_000_000, loan_rate=0.045, treasury_rate=0.025,
            maturity=date(2028, 6, 30), today=date(2026, 5, 14),
            amort_yrs=30,
        )
        self.assertFalse(r.in_open_period)
        self.assertGreater(r.current_ym_penalty, r.open_period_penalty)
        self.assertGreater(r.savings_if_wait_to_open, 0)

    def test_tight_spread_no_savings_clamped_to_zero(self):
        # Tiny spread → YM penalty less than 1% fee → savings clamped to 0.
        r = analyze_prepay_timing(
            upb=8_500_000, loan_rate=0.0425, treasury_rate=0.0410,
            maturity=date(2026, 2, 10), today=date(2025, 8, 14),
            amort_yrs=30, open_period_months=3, open_period_fee_pct=0.01,
        )
        # YM penalty is tiny (15 bps spread for 3 months); open fee is 1%.
        self.assertLess(r.current_ym_penalty, r.open_period_penalty)
        self.assertEqual(r.savings_if_wait_to_open, 0.0)

    def test_ym_expiry_date_calculated_correctly(self):
        r = analyze_prepay_timing(
            upb=10_000_000, loan_rate=0.05, treasury_rate=0.03,
            maturity=date(2028, 6, 30), today=date(2026, 5, 14),
            open_period_months=3, amort_yrs=0,
        )
        self.assertEqual(r.ym_expiry_date, date(2028, 3, 30))

    def test_savings_pct_of_upb_matches_dollar_savings(self):
        r = analyze_prepay_timing(
            upb=20_000_000, loan_rate=0.06, treasury_rate=0.03,
            maturity=date(2030, 1, 1), today=date(2026, 5, 1),
            amort_yrs=30,
        )
        self.assertAlmostEqual(
            r.savings_pct_of_upb,
            r.savings_if_wait_to_open / r.upb,
            places=6,
        )

    def test_zero_open_period_fee_means_wait_for_free(self):
        # If open-period fee is 0%, savings = full YM penalty.
        r = analyze_prepay_timing(
            upb=10_000_000, loan_rate=0.05, treasury_rate=0.03,
            maturity=date(2030, 1, 1), today=date(2026, 5, 1),
            open_period_months=3, open_period_fee_pct=0.0, amort_yrs=0,
        )
        self.assertEqual(r.open_period_penalty, 0.0)
        self.assertEqual(r.savings_if_wait_to_open, r.current_ym_penalty)


class TestDateHelpers(unittest.TestCase):

    def test_add_months_within_year(self):
        self.assertEqual(_add_months(date(2026, 3, 15), 5), date(2026, 8, 15))

    def test_add_months_crosses_year(self):
        self.assertEqual(_add_months(date(2026, 11, 1), 4), date(2027, 3, 1))

    def test_add_months_negative(self):
        self.assertEqual(_add_months(date(2026, 6, 30), -3), date(2026, 3, 30))

    def test_add_months_clamps_day_to_short_month(self):
        # Jan 31 minus 1 month → end of Dec (31), or Feb 28/29.
        # Going from May 31 to Feb 28 (non-leap).
        self.assertEqual(_add_months(date(2025, 5, 31), -3), date(2025, 2, 28))

    def test_months_between_is_zero_if_d2_before_d1(self):
        self.assertEqual(_months_between(date(2026, 6, 1), date(2026, 3, 1)), 0)

    def test_months_between_simple(self):
        self.assertEqual(_months_between(date(2026, 3, 1), date(2026, 9, 1)), 6)

    def test_months_between_crosses_year(self):
        self.assertEqual(_months_between(date(2026, 10, 1), date(2027, 4, 1)), 6)


class TestMonthsBetweenDayAccuracy(unittest.TestCase):

    def test_partial_month_rounds_up(self):
        # Day-of-month matters: 1 day shy of the target date is still a
        # (partial) month on the YM clock, not zero.
        self.assertEqual(_months_between(date(2025, 11, 9), date(2025, 11, 10)), 1)
        self.assertEqual(_months_between(date(2025, 8, 9), date(2025, 11, 10)), 4)
        # Aligned or later day-of-month: unchanged whole-month counts.
        self.assertEqual(_months_between(date(2025, 8, 10), date(2025, 11, 10)), 3)
        self.assertEqual(_months_between(date(2025, 8, 14), date(2025, 11, 10)), 3)

    def test_zero_when_dates_equal(self):
        self.assertEqual(_months_between(date(2025, 11, 10), date(2025, 11, 10)), 0)


class TestPenaltyJustBeforeOpenPeriod(unittest.TestCase):

    def test_day_before_open_period_is_not_free(self):
        # 2025-11-09 is one day before the open period starts (2025-11-10).
        # The old calendar-month arithmetic reported a $0 YM penalty here —
        # an actionable wrong answer in a refi-timing tool.
        r = analyze_prepay_timing(
            upb=1_000_000, loan_rate=0.06, treasury_rate=0.04,
            maturity=date(2026, 2, 10), today=date(2025, 11, 9),
            open_period_months=3, open_period_fee_pct=0.01, amort_yrs=0,
        )
        self.assertFalse(r.in_open_period)
        self.assertGreater(r.current_ym_penalty, 0.0)
        # ≈ one month of 2% spread on $1M, discounted one month at Treasury.
        expected = 1_000_000 * 0.02 / 12 / (1 + 0.04 / 12)
        self.assertAlmostEqual(r.current_ym_penalty, expected, places=2)


if __name__ == "__main__":
    unittest.main()
