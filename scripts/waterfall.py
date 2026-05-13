"""
waterfall.py — Compute a real estate / PE distribution waterfall.

Implements an American-style, deal-level waterfall with the standard four tiers.
Most real estate partnerships use some variant of this; bespoke modifications
(e.g., 50% catch-up, pref on contributed-not-outstanding capital, a true
IRR-lookback second hurdle) require editing the code.

Tier structure:
  Tier 1 — Return of Capital:  100% to LP until contributions returned
  Tier 2 — Preferred Return:   100% to LP until cumulative pref earned
  Tier 3 — GP Catch-up:        100% to GP until GP has [promote] share of
                                Tiers 2+3 combined ("100% catch-up")
  Tier 4 — Carried Interest:   LP / GP split per promote_pct (e.g., 80/20)

Convention: pref accrues on OUTSTANDING (unreturned) capital, compounded annually.

Usage:
  python waterfall.py --csv flows.csv --pref 0.08 --promote 0.20

Where flows.csv has signed cash flows from the LP's perspective:
  Contributions are NEGATIVE; pre-promote operating/sale cash is POSITIVE.

The script splits the POSITIVE flows between LP and GP according to the
waterfall, then prints the LP and GP IRRs and MOICs.
"""

import argparse
import csv
from datetime import date, datetime, timedelta
from typing import Iterable

from returns import xirr, moic, parse_date, parse_csv


def run_waterfall(
    flows: list[tuple[date, float]],
    pref_rate: float = 0.08,
    promote_pct: float = 0.20,
) -> dict:
    """
    Run the waterfall and return per-distribution LP/GP splits plus summary.

    flows: chronological (date, amount) pairs; contributions negative.
    pref_rate: annual preferred return on outstanding capital (compounded).
    promote_pct: GP's share of profits above pref (e.g., 0.20).
    """
    flows = sorted(flows, key=lambda x: x[0])
    outstanding_capital = 0.0
    accrued_pref = 0.0
    prev_date = flows[0][0]
    lp_distributions = []
    gp_distributions = []
    cumulative_pref_paid = 0.0     # Tier 2 cumulative — sole base for the catch-up target
    cumulative_catchup_gp = 0.0    # Tier 3 cumulative — tracks how much catch-up GP has already received

    for current_date, amount in flows:
        # Accrue pref on outstanding capital since last cash flow
        if outstanding_capital > 0:
            years = (current_date - prev_date).days / 365.0
            if years > 0:
                accrued_pref += outstanding_capital * ((1 + pref_rate) ** years - 1)

        if amount < 0:
            # Contribution
            outstanding_capital += -amount
            lp_distributions.append((current_date, amount))  # LP funded
            gp_distributions.append((current_date, 0.0))
        else:
            # Distribution to split via waterfall
            remaining = amount
            lp_share = 0.0
            gp_share = 0.0

            # Tier 1 — Return of Capital
            if outstanding_capital > 0 and remaining > 0:
                t1 = min(remaining, outstanding_capital)
                lp_share += t1
                outstanding_capital -= t1
                remaining -= t1

            # Tier 2 — Preferred Return
            if accrued_pref > 0 and remaining > 0:
                t2 = min(remaining, accrued_pref)
                lp_share += t2
                accrued_pref -= t2
                cumulative_pref_paid += t2
                remaining -= t2

            # Tier 3 — GP Catch-up (100% catch-up convention)
            # After Tier 3, GP should hold promote_pct of (Tier 2 + Tier 3 combined).
            # That requires cumulative T3 = cumulative T2 * promote / (1 - promote).
            # The base must be Tier 2 ALONE — Tier 4 amounts are already split at
            # promote_pct so they preserve the equilibrium and must not enter the
            # catch-up base. Runs every event so newly paid pref keeps catching up.
            if remaining > 0 and cumulative_pref_paid > 0:
                target_catchup = cumulative_pref_paid * promote_pct / (1 - promote_pct)
                t3 = min(remaining, max(0.0, target_catchup - cumulative_catchup_gp))
                if t3 > 0:
                    gp_share += t3
                    cumulative_catchup_gp += t3
                    remaining -= t3

            # Tier 4 — Carried Interest (promote_pct to GP)
            # Splits at promote_pct so the (GP share / total above cap) ratio is
            # preserved — no need to update Tier 2 / Tier 3 cumulatives.
            if remaining > 0:
                t4_gp = remaining * promote_pct
                t4_lp = remaining - t4_gp
                lp_share += t4_lp
                gp_share += t4_gp
                remaining = 0

            lp_distributions.append((current_date, lp_share))
            gp_distributions.append((current_date, gp_share))

        prev_date = current_date

    lp_irr = xirr(lp_distributions)
    lp_moic, lp_contrib, lp_dist = moic(lp_distributions)
    gp_total = sum(a for _, a in gp_distributions if a > 0)

    return {
        "lp_flows": lp_distributions,
        "gp_flows": gp_distributions,
        "lp_irr": lp_irr,
        "lp_moic": lp_moic,
        "lp_contributed": lp_contrib,
        "lp_distributed": lp_dist,
        "gp_total_promote": gp_total,
        "uncalled_pref": accrued_pref,
        "uncalled_capital": outstanding_capital,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", required=True, help="CSV of date,amount (signed)")
    p.add_argument("--pref", type=float, default=0.08, help="preferred return (annual, default 0.08)")
    p.add_argument("--promote", type=float, default=0.20, help="GP promote share (default 0.20)")
    args = p.parse_args()

    flows = parse_csv(args.csv)
    result = run_waterfall(flows, pref_rate=args.pref, promote_pct=args.promote)

    print("-" * 64)
    print("WATERFALL RESULT")
    print("-" * 64)
    print(f"Preferred return:          {args.pref * 100:.1f}% annual, compounded")
    print(f"Promote:                   {args.promote * 100:.1f}% to GP above pref")
    print("-" * 64)
    print(f"LP contributed:            ${result['lp_contributed']:>15,.0f}")
    print(f"LP distributed:            ${result['lp_distributed']:>15,.0f}")
    print(f"LP IRR:                    {result['lp_irr'] * 100:>15.2f}%")
    print(f"LP MOIC:                   {result['lp_moic']:>15.2f}x")
    print("-" * 64)
    print(f"GP promote earned:         ${result['gp_total_promote']:>15,.0f}")
    print("-" * 64)
    if result['uncalled_capital'] > 0:
        print(f"NOTE: ${result['uncalled_capital']:,.0f} of capital not yet returned")
    if result['uncalled_pref'] > 0:
        print(f"NOTE: ${result['uncalled_pref']:,.0f} of accrued pref unpaid")

    print()
    print("PER-FLOW DETAIL")
    print(f"{'Date':<12} {'Total':>15} {'-> LP':>15} {'-> GP':>15}")
    for (d, total), (_, gp) in zip(
        # Reconstruct original totals from LP+GP for clarity
        [(d, lp + gp) for (d, lp), (_, gp) in zip(result['lp_flows'], result['gp_flows'])],
        result['gp_flows'],
    ):
        lp = total - gp
        print(f"{d!s:<12} ${total:>14,.0f} ${lp:>14,.0f} ${gp:>14,.0f}")


if __name__ == "__main__":
    main()
