"""
waterfall.py — Compute a real estate / PE distribution waterfall.

Implements an American-style, deal-level waterfall with the standard four tiers.
Supports an optional two-tier promote (Tier 4a/4b with an IRR-look-back hurdle).
Most real estate partnerships use some variant of this; bespoke modifications
(e.g., 50% catch-up, pref on contributed-not-outstanding capital) require
editing the code.

Tier structure:
  Tier 1 — Return of Capital:  100% to LP until contributions returned
  Tier 2 — Preferred Return:   100% to LP until cumulative pref earned
  Tier 3 — GP Catch-up:        100% to GP until GP has [promote] share of
                                Tiers 2+3 combined ("100% catch-up")
  Tier 4 — Carried Interest:   LP / GP split per promote_pct (e.g., 80/20)

Pref convention (READ BEFORE USING ON A REAL LPA):

  Pref accrues on OUTSTANDING (unreturned) capital — the rate compounds
  on capital between distribution events.

  Pref does NOT compound on accrued-but-unpaid pref ("pref on pref"). If
  pref is partially paid (or not paid) in a given period, the unpaid
  portion carries forward at face — it does not itself earn pref in the
  next period.

  Many real-world LPAs DO compound pref on accrued pref. If your deal
  follows that convention, this script will under-state the LP pref
  balance and over-state GP catch-up timing on long unpaid-pref periods.
  Verify against the LPA before producing LP-facing numbers.

  Day-count is Actual/365 from the prior cash flow date. LPAs that
  specify 30/360 or Actual/Actual will diverge slightly on long holds.

Other simplifications: no clawback / true-up, no European whole-fund
waterfall. Bespoke deal mechanics require editing the code.

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

from returns import xirr, moic, parse_date, parse_csv, _xnpv


def run_waterfall(
    flows: list[tuple[date, float]],
    pref_rate: float = 0.08,
    promote_pct: float = 0.20,
    second_hurdle: float | None = None,
    second_promote_pct: float | None = None,
) -> dict:
    """
    Run the waterfall and return per-distribution LP/GP splits plus summary.

    flows: chronological (date, amount) pairs; contributions negative.
    pref_rate: annual preferred return on outstanding capital. Compounded
        on the *capital* base between events (NOT on accrued-unpaid pref;
        see module docstring for the convention and its limitations).
    promote_pct: GP's share in Tier 4a (e.g., 0.20 for 80/20).

    Two-tier promote (optional — pass BOTH or NEITHER):
      second_hurdle: LP IRR threshold (e.g., 0.15 for 15%) at which the
        promote share steps up.
      second_promote_pct: GP's share in Tier 4b above the hurdle
        (e.g., 0.30 for 70/30).

    When second_hurdle is set, Tier 4 splits into:
      Tier 4a: split at promote_pct        until LP achieves second_hurdle IRR
      Tier 4b: split at second_promote_pct above the hurdle

    The boundary is computed at each distribution event by solving for the
    LP T4 distribution that drives LP IRR to exactly the hurdle, given
    LP's prior cumulative flows. The first chunk of T4 above that boundary
    splits at first promote; everything above the boundary splits at the
    higher second promote.
    """
    if (second_hurdle is None) != (second_promote_pct is None):
        raise ValueError(
            "second_hurdle and second_promote_pct must be passed together"
        )
    has_second_tier = second_hurdle is not None
    if has_second_tier and second_promote_pct < promote_pct:
        raise ValueError(
            "second_promote_pct must be >= promote_pct (the hurdle step is up, not down)"
        )

    flows = sorted(flows, key=lambda x: x[0])
    t0 = flows[0][0]
    outstanding_capital = 0.0
    accrued_pref = 0.0
    prev_date = t0
    lp_distributions = []
    gp_distributions = []
    cumulative_pref_paid = 0.0     # Tier 2 cumulative — sole base for the catch-up target
    cumulative_catchup_gp = 0.0    # Tier 3 cumulative — tracks how much catch-up GP has already received
    cumulative_t4a = 0.0           # for diagnostics
    cumulative_t4b = 0.0           # for diagnostics

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

            # Tier 4 — Carried Interest. Splits at promote_pct (single-tier)
            # or splits across two sub-tiers (4a below hurdle, 4b above) if a
            # second_hurdle is configured.
            if remaining > 0:
                if not has_second_tier:
                    t4_gp = remaining * promote_pct
                    t4_lp = remaining - t4_gp
                    lp_share += t4_lp
                    gp_share += t4_gp
                    cumulative_t4a += remaining
                    remaining = 0
                else:
                    # Solve for the LP T4 distribution that drives LP IRR to
                    # exactly second_hurdle, given prior LP flows (not including
                    # this event's T1/T2 lp_share, which we'll add below).
                    #
                    # NPV(hurdle, lp_distributions_so_far) + lp_total_this_event * df = 0
                    # => lp_total_this_event = -NPV / df
                    # => lp_t4_to_hurdle = lp_total_this_event - lp_share (so far this event)
                    npv_prior = _xnpv(second_hurdle, lp_distributions)
                    years_to_now = (current_date - t0).days / 365.0
                    df = 1.0 / (1.0 + second_hurdle) ** years_to_now
                    lp_share_at_hurdle = -npv_prior / df
                    lp_t4_to_hurdle = lp_share_at_hurdle - lp_share

                    if lp_t4_to_hurdle <= 0:
                        # LP already past hurdle — all remaining splits at 4b.
                        t4b_gp = remaining * second_promote_pct
                        t4b_lp = remaining - t4b_gp
                        lp_share += t4b_lp
                        gp_share += t4b_gp
                        cumulative_t4b += remaining
                        remaining = 0
                    else:
                        # T4a portion: the chunk of `remaining` whose LP share
                        # at the first promote equals lp_t4_to_hurdle.
                        t4a_total = lp_t4_to_hurdle / (1.0 - promote_pct)
                        if t4a_total >= remaining:
                            # All remaining stays in T4a (LP doesn't quite reach hurdle).
                            t4a_gp = remaining * promote_pct
                            t4a_lp = remaining - t4a_gp
                            lp_share += t4a_lp
                            gp_share += t4a_gp
                            cumulative_t4a += remaining
                            remaining = 0
                        else:
                            # Split into T4a (up to hurdle) and T4b (above).
                            t4a_gp = t4a_total * promote_pct
                            t4a_lp = t4a_total - t4a_gp
                            lp_share += t4a_lp
                            gp_share += t4a_gp
                            cumulative_t4a += t4a_total
                            remaining -= t4a_total

                            t4b_gp = remaining * second_promote_pct
                            t4b_lp = remaining - t4b_gp
                            lp_share += t4b_lp
                            gp_share += t4b_gp
                            cumulative_t4b += remaining
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
        "tier4a_total": cumulative_t4a,
        "tier4b_total": cumulative_t4b,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", required=True, help="CSV of date,amount (signed)")
    p.add_argument("--pref", type=float, default=0.08, help="preferred return (annual, default 0.08)")
    p.add_argument("--promote", type=float, default=0.20, help="GP promote share in Tier 4a (default 0.20)")
    p.add_argument("--second-hurdle", type=float, default=None,
                   help="LP IRR threshold for second promote tier (e.g., 0.15)")
    p.add_argument("--second-promote", type=float, default=None,
                   help="GP promote share above the second hurdle (e.g., 0.30)")
    args = p.parse_args()

    flows = parse_csv(args.csv)
    result = run_waterfall(
        flows,
        pref_rate=args.pref,
        promote_pct=args.promote,
        second_hurdle=args.second_hurdle,
        second_promote_pct=args.second_promote,
    )

    print("-" * 64)
    print("WATERFALL RESULT")
    print("-" * 64)
    print(f"Preferred return:          {args.pref * 100:.1f}% annual, compounded")
    print(f"Promote (Tier 4a):         {args.promote * 100:.1f}% to GP")
    if args.second_hurdle is not None:
        print(f"Second hurdle:             {args.second_hurdle * 100:.1f}% LP IRR")
        print(f"Promote (Tier 4b):         {args.second_promote * 100:.1f}% to GP above hurdle")
    print("-" * 64)
    print(f"LP contributed:            ${result['lp_contributed']:>15,.0f}")
    print(f"LP distributed:            ${result['lp_distributed']:>15,.0f}")
    print(f"LP IRR:                    {result['lp_irr'] * 100:>15.2f}%")
    print(f"LP MOIC:                   {result['lp_moic']:>15.2f}x")
    print("-" * 64)
    print(f"GP promote earned:         ${result['gp_total_promote']:>15,.0f}")
    if args.second_hurdle is not None:
        print(f"  Tier 4a (below hurdle):  ${result['tier4a_total']:>15,.0f}")
        print(f"  Tier 4b (above hurdle):  ${result['tier4b_total']:>15,.0f}")
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
