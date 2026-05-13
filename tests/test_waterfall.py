import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from waterfall import run_waterfall


class TestWaterfall(unittest.TestCase):

    def test_single_sale_after_capital_and_pref(self):
        # Contribute $1M, sell after 1 year for $1.2M.
        # Pref: 8% on $1M for 1yr = $80,000.
        # After cap return ($1M) and pref ($80k), profit-above-pref = $120,000.
        # 100% catch-up: target_gp = 80,000 * 0.20 / 0.80 = $20,000.
        #   GP gets $20k catch-up (now cumulative_promote = $100k total, GP has 20%).
        # Remaining: $120k - $20k = $100k, split 80/20:
        #   LP gets $80k, GP gets $20k.
        # Totals: LP = $1M + $80k + $80k = $1,160,000; GP = $40,000.
        flows = [
            (date(2020, 1, 1), -1_000_000.0),
            (date(2021, 1, 1), 1_200_000.0),
        ]
        r = run_waterfall(flows, pref_rate=0.08, promote_pct=0.20)
        self.assertAlmostEqual(r["gp_total_promote"], 40_000.0, places=0)
        self.assertAlmostEqual(r["lp_distributed"], 1_160_000.0, places=0)

    def test_tier3_catchup_fires_on_every_event(self):
        """Regression: Tier 3 catch-up must fire each time new pref is paid.

        Setup: $1M contribution; first profit event ($700k yr 1) is consumed
        entirely by Tier 1 (cap return) — no pref paid yet. Second profit
        event ($700k yr 2) pays both years of accrued pref, the catch-up on
        that pref, and a Tier 4 split.

        Hand calc (verified):
          Event 1 (yr 1, $700k):  T1 returns $700k cap. Outstanding cap left
                                  = $300k. accrued_pref = $80k (yr 1 on $1M).
          Event 2 (yr 2, $700k):  +$24k pref accrual on remaining $300k.
                                  T1: $300k cap return.    remaining $400k
                                  T2: $104k pref → LP.     remaining $296k
                                  T3: $26k catch-up → GP.  remaining $270k
                                       (target = $104k * 0.2 / 0.8)
                                  T4: 80/20 split — LP $216k, GP $54k.

          GP total = $26k + $54k = $80k.
          LP total = $700k + $300k + $104k + $216k = $1,320k.

        Invariant: at full catch-up + T4 completion, GP holds promote_pct of
        total-above-cap. Here: $80k / $400k above cap = 20% ✓.
        """
        flows = [
            (date(2020, 1, 1), -1_000_000.0),
            (date(2021, 1, 1), 700_000.0),    # all goes to Tier 1 cap return
            (date(2022, 1, 1), 700_000.0),    # cap + pref + catch-up + carry
        ]
        r = run_waterfall(flows, pref_rate=0.08, promote_pct=0.20)

        # Sanity: LP + GP totals reconcile to distributed cash.
        total_distributed = 700_000.0 + 700_000.0
        self.assertAlmostEqual(r["lp_distributed"] + r["gp_total_promote"],
                               total_distributed, places=0)

        # Exact GP / LP per hand calc above.
        self.assertAlmostEqual(r["gp_total_promote"], 80_000.0, places=0)
        self.assertAlmostEqual(r["lp_distributed"], 1_320_000.0, places=0)

        # Equilibrium check: at full catch-up + T4 completion, GP share of
        # total-above-cap == promote_pct.
        above_cap = total_distributed - 1_000_000.0  # $400k
        self.assertAlmostEqual(r["gp_total_promote"] / above_cap, 0.20, places=4)

    def test_post_tier4_event_does_not_double_charge_catchup(self):
        """Regression: catch-up base must be Tier 2 only, not Tier 2 + Tier 4.

        If event 1 fully processes all four tiers, the GP is already at promote_pct
        of total-above-cap. A later event with no new pref must split 80/20 — the
        Tier 3 catch-up must NOT fire again on prior Tier 4 amounts.

        Before the fix, cumulative_promote_total folded Tier 4 into the catch-up
        base, so a second event re-triggered the catch-up and over-promoted the GP.

        Setup: $1M contribution, $1.3M at yr 1 (Tier 1+2+3+4 all run; pref = $80k),
        then $100k at yr 2 (outstanding=0, no new pref → pure 80/20 carry).

        Expected GP total: $20k (yr 1 catch-up) + 20% * $300k (carry on profits
        above pref+catchup) = $20k + $60k = $80k.
        """
        flows = [
            (date(2020, 1, 1), -1_000_000.0),
            (date(2021, 1, 1),  1_300_000.0),
            (date(2022, 1, 1),    100_000.0),
        ]
        r = run_waterfall(flows, pref_rate=0.08, promote_pct=0.20)

        self.assertAlmostEqual(r["gp_total_promote"], 80_000.0, places=0)
        self.assertAlmostEqual(r["lp_distributed"], 1_320_000.0, places=0)

        # Invariant: GP share of total-above-cap == promote_pct after equilibrium
        # is reached and pref-on-pref is fully consumed.
        above_cap = 400_000.0  # ($1.3M + $100k) - $1M contributed
        pref_paid = 80_000.0
        catchup = pref_paid * 0.20 / 0.80  # $20k
        # GP / (above_cap - pref_paid) should equal promote_pct (since catchup
        # has its own ratio that resolves to the same equilibrium).
        gp_share_of_above_pref = r["gp_total_promote"] / (above_cap - pref_paid)
        # 80k / 320k = 25% — combination of the $20k catch-up and the 20% T4 split.
        self.assertAlmostEqual(gp_share_of_above_pref, 0.25, places=4)
        # And the algebra: catch-up + 20% of (above_pref - catch-up)
        self.assertAlmostEqual(
            r["gp_total_promote"],
            catchup + 0.20 * (above_cap - pref_paid - catchup),
            places=0,
        )

    def test_early_distribution_below_pref_pays_no_gp(self):
        # Year 1 distribution below pref → all to LP via Tier 1 (cap return).
        # GP gets nothing.
        flows = [
            (date(2020, 1, 1), -1_000_000.0),
            (date(2021, 1, 1), 50_000.0),
        ]
        r = run_waterfall(flows, pref_rate=0.08, promote_pct=0.20)
        self.assertEqual(r["gp_total_promote"], 0.0)
        self.assertAlmostEqual(r["uncalled_capital"], 950_000.0, places=0)


class TestSecondTierHurdle(unittest.TestCase):
    """Two-tier promote: 80/20 below an IRR hurdle, 70/30 above."""

    def test_validation_requires_both_args(self):
        flows = [(date(2021, 1, 1), -1_000_000.0), (date(2022, 1, 1), 1_200_000.0)]
        with self.assertRaises(ValueError):
            run_waterfall(flows, second_hurdle=0.15)
        with self.assertRaises(ValueError):
            run_waterfall(flows, second_promote_pct=0.30)

    def test_validation_second_promote_not_below_first(self):
        flows = [(date(2021, 1, 1), -1_000_000.0), (date(2022, 1, 1), 1_200_000.0)]
        with self.assertRaises(ValueError):
            run_waterfall(flows, second_hurdle=0.15, second_promote_pct=0.10)

    def test_no_second_tier_unchanged(self):
        # Without second-tier args, behavior should match single-tier exactly.
        flows = [(date(2021, 1, 1), -1_000_000.0), (date(2022, 1, 1), 1_200_000.0)]
        r1 = run_waterfall(flows, pref_rate=0.08, promote_pct=0.20)
        # Sanity: LP \$1.16M, GP \$40k (same as test_single_sale_after_capital_and_pref)
        self.assertAlmostEqual(r1["gp_total_promote"], 40_000.0, places=0)
        self.assertAlmostEqual(r1["lp_distributed"], 1_160_000.0, places=0)
        self.assertEqual(r1["tier4b_total"], 0.0)

    def test_split_at_hurdle_boundary(self):
        """Hand calc:
          -\$1M at t0, +\$1.2M at t1 (yr 1, no leap). 8% pref, 15% hurdle, 20-then-30 promote.
          T1=\$1M, T2=\$80k (pref), T3=\$20k catch-up. Remaining = \$100k.
          To hit 15% IRR: LP needs \$1.15M at t1.
          LP after T1+T2 = \$1.08M, so lp_t4_to_hurdle = \$70k.
          T4a = \$70k / 0.8 = \$87.5k total (\$70k LP + \$17.5k GP).
          T4b = \$12.5k @ 70/30 (\$8.75k LP + \$3.75k GP).

          LP = \$1M + \$80k + \$70k + \$8.75k = \$1,158,750.
          GP = \$20k catch-up + \$17.5k + \$3.75k = \$41,250.
          LP IRR ends at 15.875% (above hurdle, since T4b portion exists).
        """
        flows = [(date(2021, 1, 1), -1_000_000.0), (date(2022, 1, 1), 1_200_000.0)]
        r = run_waterfall(
            flows, pref_rate=0.08, promote_pct=0.20,
            second_hurdle=0.15, second_promote_pct=0.30,
        )
        self.assertAlmostEqual(r["lp_distributed"], 1_158_750.0, places=0)
        self.assertAlmostEqual(r["gp_total_promote"], 41_250.0, places=0)
        self.assertAlmostEqual(r["tier4a_total"], 87_500.0, places=0)
        self.assertAlmostEqual(r["tier4b_total"], 12_500.0, places=0)
        # LP IRR exceeds hurdle (because T4b fired on amounts beyond the boundary).
        self.assertGreater(r["lp_irr"], 0.15)

    def test_below_hurdle_no_tier4b(self):
        # LP doesn't quite reach 15% — Tier 4b should not fire.
        # -\$1M, +\$1.15M at yr 1. T1=\$1M, T2=\$80k, T3=\$20k (full catch-up),
        # remaining=\$50k for T4.
        # LP after T1+T2 = \$1.08M; needed for 15% = \$1.15M; gap = \$70k LP.
        # T4a total to close gap = \$70k / 0.8 = \$87.5k — more than \$50k available.
        # → All \$50k stays in T4a (LP doesn't reach hurdle).
        # T4a: GP gets \$10k, LP gets \$40k.
        # LP total = \$1M + \$80k + \$40k = \$1.12M; LP IRR = 12% < 15% ✓.
        # GP total = \$20k (catch-up) + \$10k = \$30k.
        flows = [(date(2021, 1, 1), -1_000_000.0), (date(2022, 1, 1), 1_150_000.0)]
        r = run_waterfall(
            flows, pref_rate=0.08, promote_pct=0.20,
            second_hurdle=0.15, second_promote_pct=0.30,
        )
        self.assertAlmostEqual(r["tier4b_total"], 0.0, places=0)
        self.assertAlmostEqual(r["tier4a_total"], 50_000.0, places=0)
        self.assertLess(r["lp_irr"], 0.15)
        self.assertAlmostEqual(r["gp_total_promote"], 30_000.0, places=0)
        self.assertAlmostEqual(r["lp_distributed"], 1_120_000.0, places=0)

    def test_subsequent_event_all_tier4b_when_already_past_hurdle(self):
        """Multi-event: if LP cleared the hurdle in event 1, event 2's T4
        should split entirely at the second promote (no T4a).
        """
        # Event 1: -\$1M at t0, +\$1.3M at yr 1 — pushes LP past 15% hurdle.
        # Event 2: +\$500k at yr 2 — no outstanding cap, no new pref → T4 only.
        flows = [
            (date(2021, 1, 1), -1_000_000.0),
            (date(2022, 1, 1),  1_300_000.0),
            (date(2023, 1, 1),    500_000.0),
        ]
        r = run_waterfall(
            flows, pref_rate=0.08, promote_pct=0.20,
            second_hurdle=0.15, second_promote_pct=0.30,
        )
        # Event 2 (\$500k) should be ALL T4b, splitting 70/30 → LP \$350k, GP \$150k.
        # Event 1 split LP/GP per the boundary math.
        # The yr-2 contribution to t4b_total alone should be \$500k.
        # Total t4b = event 1 T4b portion + \$500k (all of event 2).
        # We verify the *increment* from event 2 by isolating event 1 separately:
        r1 = run_waterfall(
            flows[:2], pref_rate=0.08, promote_pct=0.20,
            second_hurdle=0.15, second_promote_pct=0.30,
        )
        event2_t4b = r["tier4b_total"] - r1["tier4b_total"]
        self.assertAlmostEqual(event2_t4b, 500_000.0, places=0)
        # Event 2's GP take should be 30% of $500k = $150k.
        event2_gp = r["gp_total_promote"] - r1["gp_total_promote"]
        self.assertAlmostEqual(event2_gp, 150_000.0, places=0)
        # LP IRR clearly past hurdle.
        self.assertGreater(r["lp_irr"], 0.15)

    def test_full_reconciliation_invariant(self):
        # LP distributed + GP total = total positive cash flows, on every parameterization.
        flows = [
            (date(2021, 1, 1), -1_000_000.0),
            (date(2022, 1, 1),    400_000.0),
            (date(2023, 1, 1),  1_200_000.0),
        ]
        r = run_waterfall(
            flows, pref_rate=0.08, promote_pct=0.20,
            second_hurdle=0.15, second_promote_pct=0.30,
        )
        total_pos = 400_000.0 + 1_200_000.0
        self.assertAlmostEqual(r["lp_distributed"] + r["gp_total_promote"], total_pos, places=0)


if __name__ == "__main__":
    unittest.main()
