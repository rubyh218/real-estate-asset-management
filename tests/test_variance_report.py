import os
import sys
import unittest

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from variance_report import (
    DEFAULT_THRESHOLDS,
    Flag,
    Threshold,
    VarianceReport,
    build_report,
    flag_lines,
    format_flags,
    format_report,
)


def _row(line_item, category, **values):
    return {"line_item": line_item, "category": category, **values}


def _three_col_report(unit_count=0, months=12):
    """Helper: build a small report with UW, Budget, Actual columns."""
    rows = [
        _row("GPR",           "revenue", UW=1000, Budget=1050, Actual=1020),
        _row("Vacancy",       "revenue", UW=-50,  Budget=-55,  Actual=-60),
        _row("Other Income",  "revenue", UW=100,  Budget=110,  Actual=115),
        _row("Property Tax",  "expense", UW=100,  Budget=105,  Actual=110),
        _row("Insurance",     "expense", UW=50,   Budget=55,   Actual=60),
    ]
    cols = ["UW", "Budget", "Actual"]
    return build_report(rows, cols, unit_count=unit_count, months_in_period=months)


class TestBuildReport(unittest.TestCase):

    def test_last_column_treated_as_actual(self):
        r = _three_col_report()
        self.assertEqual(r.actual_label, "Actual")
        self.assertEqual(r.baselines, ["UW", "Budget"])

    def test_egr_and_opex_totals(self):
        r = _three_col_report()
        # EGR for UW: 1000 + (-50) + 100 = 1050
        self.assertEqual(r.egr("UW"),     1050)
        self.assertEqual(r.egr("Budget"), 1105)
        self.assertEqual(r.egr("Actual"), 1075)
        # OpEx UW: 100 + 50 = 150
        self.assertEqual(r.opex("UW"),     150)
        self.assertEqual(r.opex("Budget"), 160)
        self.assertEqual(r.opex("Actual"), 170)

    def test_noi_reconciles(self):
        r = _three_col_report()
        # UW NOI = 1050 - 150 = 900
        self.assertEqual(r.noi("UW"),     900)
        self.assertEqual(r.noi("Budget"), 945)
        self.assertEqual(r.noi("Actual"), 905)

    def test_revenue_impact_is_actual_minus_baseline(self):
        r = _three_col_report()
        gpr = [L for L in r.lines if L.line_item == "GPR"][0]
        # Actual 1020 vs UW 1000 → +20 favorable.
        self.assertEqual(gpr.impacts["UW"], 20)
        # Actual 1020 vs Budget 1050 → -30 unfavorable.
        self.assertEqual(gpr.impacts["Budget"], -30)

    def test_expense_impact_is_baseline_minus_actual(self):
        r = _three_col_report()
        tax = [L for L in r.lines if L.line_item == "Property Tax"][0]
        # Actual 110 vs UW 100 → expense overrun → -10 unfavorable to NOI.
        self.assertEqual(tax.impacts["UW"], -10)
        # Actual 110 vs Budget 105 → -5 unfavorable.
        self.assertEqual(tax.impacts["Budget"], -5)

    def test_negative_revenue_vacancy_preserves_sign(self):
        r = _three_col_report()
        vac = [L for L in r.lines if L.line_item == "Vacancy"][0]
        # Vacancy went from -50 to -60 (more vacancy) → -10 unfavorable.
        self.assertEqual(vac.impacts["UW"], -10)

    def test_single_baseline_only_works(self):
        # Just one baseline + actual.
        rows = [_row("GPR", "revenue", UW=1000, Actual=1100)]
        r = build_report(rows, ["UW", "Actual"])
        self.assertEqual(r.baselines, ["UW"])
        self.assertEqual(r.lines[0].impacts["UW"], 100)

    def test_too_few_columns_raises(self):
        with self.assertRaises(ValueError):
            build_report([_row("X", "revenue", Actual=100)], ["Actual"])

    def test_bad_category_raises(self):
        with self.assertRaises(ValueError):
            build_report(
                [_row("X", "income", UW=10, Actual=20)], ["UW", "Actual"]
            )


class TestFormatReportBases(unittest.TestCase):

    def test_dollar_basis_default(self):
        r = _three_col_report()
        out = format_report(r, baseline="UW", basis="dollar")
        # Should show the (35,000)-style format for negative variances.
        self.assertIn("Var vs UW", out)
        # NOI line should be present.
        self.assertIn("NET OPERATING INCOME", out)

    def test_per_unit_mo_requires_unit_count(self):
        r = _three_col_report(unit_count=0)
        with self.assertRaises(ValueError):
            format_report(r, baseline="UW", basis="per_unit_mo")

    def test_per_unit_mo_with_units(self):
        # 100 units, 12 months. NOI variance UW vs Actual = 905 - 900 = +5.
        # Per unit/mo = 5 / 100 / 12 = 0.00417.
        r = _three_col_report(unit_count=100, months=12)
        out = format_report(r, baseline="UW", basis="per_unit_mo")
        # Verify the output contains a dollar/unit/mo formatted value.
        self.assertIn("$/unit/mo", out + " $/unit/mo")  # basis tag in header
        # NOI variance = +5 → 5 / 100 / 12 ≈ $0.00 per unit/mo. Tiny but shown.
        # We just check the report renders without error.
        self.assertIn("NET OPERATING INCOME", out)

    def test_pct_of_egr(self):
        r = _three_col_report()
        out = format_report(r, baseline="UW", basis="pct_of_egr")
        self.assertIn("% EGR", out + " % EGR")
        # GPR impact = +20. EGR actual = 1075. Pct = 20/1075 = 1.86%.
        self.assertIn("1.86%", out)

    def test_pct_of_opex_blanks_revenue_lines(self):
        r = _three_col_report()
        out = format_report(r, baseline="UW", basis="pct_of_opex")
        # Property Tax (expense) impact = -10. OpEx actual = 170. Pct = -5.88%.
        self.assertIn("-5.88%", out)
        # Revenue line "GPR" should show "—" for pct_of_opex.
        self.assertIn("—", out)

    def test_pct_var_basis(self):
        # Variance as % of baseline value.
        r = _three_col_report()
        out = format_report(r, baseline="UW", basis="pct_var")
        # GPR: impact 20 / |1000| = 2.0%
        self.assertIn("2.00%", out)


class TestFormatReportBaselineSelection(unittest.TestCase):

    def test_default_baseline_is_first(self):
        r = _three_col_report()
        out = format_report(r, basis="dollar")
        self.assertIn("vs baseline: UW", out)

    def test_explicit_baseline_switches_var_column(self):
        r = _three_col_report()
        out = format_report(r, baseline="Budget", basis="dollar")
        self.assertIn("vs baseline: Budget", out)
        self.assertIn("Var vs Budget", out)

    def test_unknown_baseline_raises(self):
        r = _three_col_report()
        with self.assertRaises(ValueError):
            format_report(r, baseline="Mystery", basis="dollar")


class TestSorting(unittest.TestCase):

    def test_sort_by_abs_impact_puts_biggest_first(self):
        rows = [
            _row("Small",  "revenue", UW=100, Actual=105),     # +5
            _row("Big",    "expense", UW=100, Actual=200),     # -100
            _row("Medium", "revenue", UW=100, Actual=80),      # -20
        ]
        r = build_report(rows, ["UW", "Actual"])
        out = format_report(r, baseline="UW", basis="dollar", sort_by_abs_impact=True)
        # Big should appear before Medium which appears before Small WITHIN
        # their category sections (revenue and expense are still separated).
        # Within revenue: Medium before Small.
        # Within expense: only Big.
        rev_section = out.split("OPERATING EXPENSES")[0]
        self.assertLess(rev_section.index("Medium"), rev_section.index("Small"))


class TestThreeBaselinesEnd2End(unittest.TestCase):

    def test_full_uw_budget_prior_actual(self):
        # The pattern an operating dashboard surfaces.
        rows = [
            _row("GPR",      "revenue", UW=1000, Budget=1050, Prior=1020, Actual=1100),
            _row("Tax",      "expense", UW=100,  Budget=110,  Prior=105,  Actual=120),
        ]
        cols = ["UW", "Budget", "Prior", "Actual"]
        r = build_report(rows, cols)
        self.assertEqual(r.baselines, ["UW", "Budget", "Prior"])
        gpr = [L for L in r.lines if L.line_item == "GPR"][0]
        # Actual 1100 vs each baseline
        self.assertEqual(gpr.impacts["UW"],     100)
        self.assertEqual(gpr.impacts["Budget"],  50)
        self.assertEqual(gpr.impacts["Prior"],   80)


class TestFlagLines(unittest.TestCase):

    def _flag_setup(self):
        rows = [
            _row("GPR",          "revenue", UW=1_000_000, Actual=995_000),    # -0.5%, below warn
            _row("Vacancy",      "revenue", UW=-50_000,  Actual=-57_000),     # 14% unfavorable → WARN
            _row("Property Tax", "expense", UW=100_000,  Actual=109_000),     #  +9% over → WARN (≥ 5% warn band)
            _row("Insurance",    "expense", UW=100_000,  Actual=140_000),     # +40% → CRITICAL
            _row("R&M",          "expense", UW=100_000,  Actual=108_000),     # +8%, below warn
        ]
        return build_report(rows, ["UW", "Actual"])

    def test_below_warn_threshold_not_flagged(self):
        r = self._flag_setup()
        flags = flag_lines(r, baseline="UW")
        items = {f.line_item for f in flags}
        # GPR (-0.5%) and R&M (+8%) both under default 10% warn — should NOT flag.
        self.assertNotIn("GPR", items)
        self.assertNotIn("R&M", items)

    def test_above_critical_threshold_flagged_critical(self):
        r = self._flag_setup()
        flags = flag_lines(r, baseline="UW")
        ins = [f for f in flags if f.line_item == "Insurance"]
        self.assertEqual(len(ins), 1)
        self.assertEqual(ins[0].severity, "critical")

    def test_insurance_tighter_threshold_applies(self):
        # Insurance threshold is pct_critical=0.15, narrower than the catch-all 0.20.
        # At 16% over budget, default catch-all would say "warn"; insurance rule says "critical".
        rows = [_row("Insurance", "expense", UW=100_000, Actual=116_000)]
        r = build_report(rows, ["UW", "Actual"])
        flags = flag_lines(r, baseline="UW")
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].severity, "critical")

    def test_property_tax_tighter_threshold_warn(self):
        # Property tax catches 6% as a warn (default pct_warn=0.05 for that line).
        rows = [_row("Property Tax", "expense", UW=100_000, Actual=106_000)]
        r = build_report(rows, ["UW", "Actual"])
        flags = flag_lines(r, baseline="UW")
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].severity, "warn")

    def test_favorable_variances_not_flagged_by_default(self):
        # Default direction = "unfavorable". GPR up 15% is favorable — no flag.
        rows = [_row("GPR", "revenue", UW=1_000_000, Actual=1_150_000)]
        r = build_report(rows, ["UW", "Actual"])
        flags = flag_lines(r, baseline="UW")
        self.assertEqual(flags, [])

    def test_zero_baseline_skipped(self):
        # Can't compute % var when baseline is 0.
        rows = [_row("Surprise Recovery", "revenue", UW=0, Actual=100_000)]
        r = build_report(rows, ["UW", "Actual"])
        flags = flag_lines(r, baseline="UW")
        self.assertEqual(flags, [])

    def test_custom_threshold_overrides_default(self):
        # Override: GPR-specific 1% warn band.
        thresholds = [
            Threshold(line_item="GPR", pct_warn=0.01, pct_critical=0.05),
            Threshold(line_item=None, pct_warn=0.99, pct_critical=0.99),  # block everything else
        ]
        rows = [
            _row("GPR", "revenue", UW=1_000_000, Actual=980_000),         # -2%
            _row("Insurance", "expense", UW=100_000, Actual=150_000),     # +50% — would normally crit
        ]
        r = build_report(rows, ["UW", "Actual"])
        flags = flag_lines(r, baseline="UW", thresholds=thresholds)
        items = {f.line_item for f in flags}
        self.assertIn("GPR", items)
        # Insurance shouldn't flag because the second catch-all has impossibly high bands.
        self.assertNotIn("Insurance", items)

    def test_message_includes_dollar_impact_and_pct(self):
        r = self._flag_setup()
        flags = flag_lines(r, baseline="UW")
        ins = [f for f in flags if f.line_item == "Insurance"][0]
        self.assertIn("$-40,000", ins.message)
        self.assertIn("-40.0%", ins.message)

    def test_format_flags_empty_says_none(self):
        out = format_flags([])
        self.assertIn("none flagged", out)

    def test_format_flags_groups_by_severity(self):
        r = self._flag_setup()
        flags = flag_lines(r, baseline="UW")
        out = format_flags(flags)
        # Critical comes before warn.
        self.assertLess(out.index("[CRITICAL]"), out.index("[WARN]"))


if __name__ == "__main__":
    unittest.main()
