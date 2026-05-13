import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from rent_roll import Unit, analyze, parse_csv, _add_months


def _unit(unit_id, status="Occupied", in_place=1000.0, market=1100.0,
          sqft=800.0, unit_type="1BR", lease_end=None):
    return Unit(
        unit=unit_id,
        unit_type=unit_type,
        sqft=sqft,
        status=status,
        tenant=f"Tenant {unit_id}" if status != "Vacant" else "",
        in_place_rent=in_place if status != "Vacant" else 0.0,
        market_rent=market,
        lease_start=None,
        lease_end=lease_end,
    )


class TestOccupancy(unittest.TestCase):

    def test_basic_physical_occupancy(self):
        # 3 occupied, 1 vacant — 75% physical.
        units = [
            _unit("1", "Occupied"),
            _unit("2", "Occupied"),
            _unit("3", "Vacant"),
            _unit("4", "Occupied"),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertAlmostEqual(a.physical_occ_units, 0.75)
        self.assertEqual(a.total_units, 4)

    def test_notice_counts_as_paying(self):
        # 2 occupied + 1 notice (still paying) + 1 vacant = 75% physical.
        units = [
            _unit("1", "Occupied"),
            _unit("2", "Notice"),
            _unit("3", "Occupied"),
            _unit("4", "Vacant"),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertAlmostEqual(a.physical_occ_units, 0.75)

    def test_sno_counts_as_leased_not_physical(self):
        # 2 occupied + 1 SNO + 1 vacant
        #   Physical = 2/4 = 50%; Leased = 3/4 = 75%
        units = [
            _unit("1", "Occupied"),
            _unit("2", "Occupied"),
            _unit("3", "SNO"),
            _unit("4", "Vacant"),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertAlmostEqual(a.physical_occ_units, 0.50)
        self.assertAlmostEqual(a.leased_occ_units, 0.75)


class TestGPRAndLTL(unittest.TestCase):

    def test_gpr_is_market_rent_times_12(self):
        units = [
            _unit("1", "Occupied", market=1000),
            _unit("2", "Occupied", market=1200),
            _unit("3", "Vacant",   market=1000),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        # 1000 + 1200 + 1000 = 3200 * 12 = 38400
        self.assertEqual(a.gpr_annual, 38_400)

    def test_in_place_excludes_vacant(self):
        units = [
            _unit("1", "Occupied", in_place=900,  market=1000),
            _unit("2", "Vacant",                   market=1000),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertEqual(a.in_place_annual, 900 * 12)

    def test_ltl_is_gap_between_market_and_in_place(self):
        # 1 unit at $100 below market → annualized LTL = $1,200.
        units = [_unit("1", "Occupied", in_place=900, market=1000)]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertEqual(a.ltl_dollars_annual, 1_200)
        self.assertAlmostEqual(a.ltl_pct_of_gpr, 1_200 / 12_000)

    def test_ltl_excludes_over_market_in_place(self):
        # If in-place exceeds market (e.g., long-stay tenant on old higher rate),
        # LTL should count this as 0, not negative.
        units = [_unit("1", "Occupied", in_place=1100, market=1000)]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertEqual(a.ltl_dollars_annual, 0)


class TestWALT(unittest.TestCase):

    def test_walt_rent_weighted(self):
        # Tenant A: $1000 rent, 2 yrs remaining.
        # Tenant B: $2000 rent, 1 yr remaining.
        # WALT = (2 * 1000 + 1 * 2000) / (1000 + 2000) = 4000 / 3000 = 1.333...
        units = [
            _unit("A", "Occupied", in_place=1000, lease_end=date(2024, 1, 1)),
            _unit("B", "Occupied", in_place=2000, lease_end=date(2023, 1, 1)),
        ]
        a = analyze(units, as_of=date(2022, 1, 1))
        self.assertAlmostEqual(a.walt_years, 4 / 3, places=3)

    def test_expired_leases_become_mtm(self):
        # lease_end before as_of → tenant reclassified MTM by parse_csv,
        # but if we pass Unit objects directly, analyze() sees the original status.
        # In practice the CSV parser auto-promotes; analyze excludes from WALT either way.
        units = [
            _unit("A", "Occupied", in_place=1000, lease_end=date(2023, 1, 1)),
            _unit("B", "Occupied", in_place=1000, lease_end=date(2028, 1, 1)),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        # WALT should only consider tenant B (future expiration).
        self.assertAlmostEqual(a.walt_years, 2.0, places=1)
        self.assertEqual(a.walt_population_count, 1)


class TestEconomicOccupancy(unittest.TestCase):

    def test_basic(self):
        # 2 units, 1 occupied at $900, 1 vacant; market $1000 each.
        # GPR = $24,000; in-place = $10,800; econ occ = 45%.
        units = [
            _unit("1", "Occupied", in_place=900, market=1000),
            _unit("2", "Vacant",                  market=1000),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertAlmostEqual(a.economic_occupancy, 10_800 / 24_000)


class TestByUnitType(unittest.TestCase):

    def test_breakdown(self):
        units = [
            _unit("101", "Occupied", in_place=1000, market=1100, unit_type="1BR"),
            _unit("102", "Vacant",                  market=1100, unit_type="1BR"),
            _unit("201", "Occupied", in_place=1800, market=1900, unit_type="2BR"),
            _unit("202", "Occupied", in_place=1850, market=1900, unit_type="2BR"),
        ]
        a = analyze(units, as_of=date(2026, 1, 1))
        self.assertIn("1BR", a.by_unit_type)
        self.assertIn("2BR", a.by_unit_type)
        # 1BR: 2 units, 1 occupied → 50%.
        self.assertAlmostEqual(a.by_unit_type["1BR"]["occupancy"], 0.50)
        # 2BR: 2 units, 2 occupied → 100%.
        self.assertAlmostEqual(a.by_unit_type["2BR"]["occupancy"], 1.00)


class TestSampleData(unittest.TestCase):
    """Integration test against the bundled sample-multifamily rent roll."""

    def test_sample_metrics_match_hand_calc(self):
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "examples", "sample-multifamily", "rent_roll.csv"
        ))
        as_of = date(2026, 3, 31)
        units = parse_csv(path, as_of=as_of)
        a = analyze(units, as_of=as_of)

        self.assertEqual(a.total_units, 24)
        # 22 paying (Occ + Notice), 2 vacant.
        self.assertAlmostEqual(a.physical_occ_units, 22 / 24)
        # GPR: 12 * 1975 + 12 * 2600 = $54,900/mo * 12 = $658,800.
        self.assertEqual(a.gpr_annual, 658_800)
        # In-place: hand-summed = $577,500 annual.
        self.assertEqual(a.in_place_annual, 577_500)
        # LTL: $26,400 annual → 4.01% of GPR.
        self.assertEqual(a.ltl_dollars_annual, 26_400)
        # All 22 paying tenants are MTM as of 2026-03-31 (their lease_ends are
        # all 2024-2025). This is itself a known data-quality issue in the
        # sample — the parser surfaces it correctly.
        self.assertEqual(a.mtm_count, 22)
        self.assertEqual(a.walt_population_count, 0)


class TestAddMonths(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(_add_months(date(2026, 1, 15), 3), date(2026, 4, 15))

    def test_crosses_year(self):
        self.assertEqual(_add_months(date(2026, 11, 1), 3), date(2027, 2, 1))

    def test_clamps_day_to_short_month(self):
        # Jan 31 + 1 month → Feb 28 (or Feb 29 in leap year).
        self.assertEqual(_add_months(date(2026, 1, 31), 1), date(2026, 2, 28))


if __name__ == "__main__":
    unittest.main()
