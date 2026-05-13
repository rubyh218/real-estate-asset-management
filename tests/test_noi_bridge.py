import os
import sys
import unittest

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from noi_bridge import build_bridge, format_bridge, BridgeLine, BridgeResult


def _row(line_item, category, baseline, actual):
    return {"line_item": line_item, "category": category, "baseline": baseline, "actual": actual}


class TestBuildBridge(unittest.TestCase):

    def test_basic_revenue_only(self):
        rows = [
            _row("GPR", "revenue", 1000, 950),
            _row("Other Income", "revenue", 100, 120),
        ]
        r = build_bridge(rows)
        self.assertEqual(r.baseline_noi, 1100)
        self.assertEqual(r.actual_noi, 1070)
        self.assertEqual(r.total_variance, -30)
        # Revenue line impact = actual - baseline
        impacts = {L.line_item: L.impact_on_noi for L in r.lines}
        self.assertEqual(impacts["GPR"], -50)
        self.assertEqual(impacts["Other Income"], 20)

    def test_expense_sign_flip(self):
        rows = [
            _row("Revenue", "revenue", 1000, 1000),
            _row("OpEx Overrun", "expense", 100, 150),  # expense up 50 → impact -50
            _row("OpEx Savings", "expense", 200, 180),  # expense down 20 → impact +20
        ]
        r = build_bridge(rows)
        self.assertEqual(r.baseline_noi, 1000 - 100 - 200)  # = 700
        self.assertEqual(r.actual_noi,   1000 - 150 - 180)  # = 670
        self.assertEqual(r.total_variance, -30)
        impacts = {L.line_item: L.impact_on_noi for L in r.lines}
        self.assertEqual(impacts["OpEx Overrun"], -50)
        self.assertEqual(impacts["OpEx Savings"], +20)

    def test_reconciliation_invariant(self):
        # The defining property: sum of impact_on_noi == NOI delta.
        rows = [
            _row("GPR",     "revenue",  5800, 5790),
            _row("Vacancy", "revenue",  -290, -325),
            _row("OI",      "revenue",   220,  245),
            _row("Tax",     "expense",   400,  450),
            _row("Ins",     "expense",   100,  140),
            _row("R&M",     "expense",   300,  280),
            _row("Payroll", "expense",   500,  540),
        ]
        r = build_bridge(rows)
        self.assertAlmostEqual(
            sum(L.impact_on_noi for L in r.lines),
            r.total_variance,
            places=6,
        )
        # And the manual sum above gives -130.
        self.assertEqual(r.total_variance, -130)

    def test_revenue_negative_amount_preserves_sign(self):
        # Vacancy is signed-negative revenue: vac going from -290 to -325 is
        # MORE vacancy => unfavorable to NOI by 35.
        rows = [_row("Vacancy", "revenue", -290, -325)]
        r = build_bridge(rows)
        self.assertEqual(r.lines[0].impact_on_noi, -35)
        # And NOI itself drops by 35 (baseline NOI = -290, actual NOI = -325).
        self.assertEqual(r.total_variance, -35)

    def test_zero_baseline_pct_handles_safely(self):
        rows = [_row("Surprise Recovery", "revenue", 0, 50)]
        r = build_bridge(rows)
        self.assertEqual(r.lines[0].pct_variance, float("inf"))

    def test_bad_category_raises(self):
        with self.assertRaises(ValueError):
            build_bridge([_row("Mystery", "income", 100, 110)])


class TestFormatBridge(unittest.TestCase):

    def test_sorted_by_absolute_impact(self):
        rows = [
            _row("Small", "revenue", 100, 105),     # +5
            _row("Big",   "expense", 100, 200),     # -100
            _row("Mid",   "revenue", 100,  80),     # -20
        ]
        r = build_bridge(rows)
        out = format_bridge(r, sort_by_impact=True)
        # Big should appear before Mid which should appear before Small.
        i_big = out.index("Big")
        i_mid = out.index("Mid")
        i_small = out.index("Small")
        self.assertLess(i_big, i_mid)
        self.assertLess(i_mid, i_small)

    def test_unsorted_preserves_input_order(self):
        rows = [
            _row("Small", "revenue", 100, 105),
            _row("Big",   "expense", 100, 200),
            _row("Mid",   "revenue", 100,  80),
        ]
        r = build_bridge(rows)
        out = format_bridge(r, sort_by_impact=False)
        self.assertLess(out.index("Small"), out.index("Big"))
        self.assertLess(out.index("Big"), out.index("Mid"))

    def test_zero_impact_lines_omitted(self):
        rows = [
            _row("Driver", "revenue", 100, 150),
            _row("Flat",   "revenue", 100, 100),
        ]
        r = build_bridge(rows)
        out = format_bridge(r)
        self.assertIn("Driver", out)
        self.assertNotIn("Flat", out)

    def test_includes_baseline_and_actual_labels(self):
        rows = [_row("X", "revenue", 100, 110)]
        r = build_bridge(rows)
        out = format_bridge(r, baseline_label="UW", actual_label="T-12")
        self.assertIn("UW NOI", out)
        self.assertIn("T-12 NOI", out)


if __name__ == "__main__":
    unittest.main()
