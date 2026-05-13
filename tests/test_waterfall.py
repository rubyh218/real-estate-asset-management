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


if __name__ == "__main__":
    unittest.main()
