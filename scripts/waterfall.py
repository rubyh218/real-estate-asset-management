"""
waterfall.py — Compute real estate / PE distribution waterfalls.

Two entry points:
  run_waterfall(flows, ...)    — single deal, deal-level / American style.
                                  Supports an optional two-tier promote
                                  (Tier 4a/4b with an IRR-look-back hurdle).
  fund_waterfall(deals, ...)   — multiple deals at fund level (American or
                                  European), with optional clawback.

Tier structure (same in both):
  Tier 1 — Return of Capital:  100% to LP until contributions returned
  Tier 2 — Preferred Return:   100% to LP until cumulative pref earned
  Tier 3 — GP Catch-up:        100% to GP until GP has [promote] share of
                                Tiers 2+3 combined ("100% catch-up")
  Tier 4 — Carried Interest:   LP / GP split per promote_pct (e.g., 80/20).
                                Optionally a second tier above an LP-IRR
                                hurdle (e.g., 80/20 to 15% IRR, then 70/30).

American vs. European (fund-level):
  American: per-deal waterfalls aggregated. GP can take carry on profitable
            deals immediately, even if later deals lose money. Common in
            opportunistic / value-add RE funds.
  European: ALL deal flows pooled chronologically; one waterfall on the fund.
            GP cannot take carry until LPs are made whole across the fund.
            Standard for core-RE and closed-end fund vehicles.

Clawback (American mode only):
  At fund end, compare GP carry under American vs. what European would have
  produced. If American > European, the excess is what GP must return to LPs.
  fund_waterfall(...) computes this automatically when compute_clawback=True.

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

Usage:
  # Single-deal:
  python waterfall.py --csv flows.csv --pref 0.08 --promote 0.20

  # Fund-level (one CSV per deal in the directory):
  python waterfall.py --fund-dir ./deals/ --style american
  python waterfall.py --fund-dir ./deals/ --style european

Where each CSV has signed cash flows from the LP's perspective:
  Contributions are NEGATIVE; pre-promote operating/sale cash is POSITIVE.

The script splits the POSITIVE flows between LP and GP according to the
waterfall, then prints the LP and GP IRRs and MOICs.
"""

import argparse
import csv
from datetime import date, datetime, timedelta
from typing import Iterable

try:  # works both as a flat script (scripts/ on path) and as a package import
    from returns import xirr, moic, parse_date, parse_csv, _xnpv
except ImportError:
    from scripts.returns import xirr, moic, parse_date, parse_csv, _xnpv


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
                    npv_prior = (
                        _xnpv(second_hurdle, lp_distributions)
                        if lp_distributions else 0.0
                    )
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

    try:
        lp_irr = xirr(lp_distributions)
    except ValueError:
        lp_irr = float("nan")  # e.g., a total-loss deal with no distributions
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


def fund_waterfall(
    deals: dict[str, list[tuple[date, float]]],
    *,
    style: str = "european",
    pref_rate: float = 0.08,
    promote_pct: float = 0.20,
    compute_clawback: bool = True,
) -> dict:
    """Run a fund-level waterfall across multiple deals.

    Args:
      deals: mapping of deal_name -> chronological (date, amount) flows from
             the LP's perspective (contributions negative, distributions positive).
      style: "european" pools ALL flows chronologically and runs one waterfall —
             GP cannot take carry until LPs have been made whole across the
             entire fund. Standard for core-RE / closed-end fund vehicles.
             "american" runs the waterfall on each deal independently and
             aggregates — GP earns carry on each deal as it realizes. Standard
             for many opportunistic / value-add RE funds.
      pref_rate, promote_pct: passed through to run_waterfall.
      compute_clawback: in American mode, also runs an implicit European
             waterfall to compute the clawback:
                 clawback = max(0, GP_american - GP_european)
             That's the excess GP must return to LPs at fund end. Has no
             effect in European mode (GP cannot be over-promoted by
             construction).

    Returns a dict with:
      style, deals (per-deal results dict in American; empty in European),
      gp_total, lp_distributed, lp_contributed, lp_irr, lp_moic,
      clawback, and (in American mode) gp_total_if_european for transparency.
    """
    if style not in ("american", "european"):
        raise ValueError(f"style must be 'american' or 'european', got {style!r}")
    if not deals:
        raise ValueError("deals dict is empty")

    if style == "european":
        # Pool every deal's flows into one sorted stream.
        pooled = [f for flows in deals.values() for f in flows]
        result = run_waterfall(pooled, pref_rate=pref_rate, promote_pct=promote_pct)
        return {
            "style": "european",
            "deals": {},
            "gp_total": result["gp_total_promote"],
            "lp_distributed": result["lp_distributed"],
            "lp_contributed": result["lp_contributed"],
            "lp_irr": result["lp_irr"],
            "lp_moic": result["lp_moic"],
            "clawback": 0.0,
        }

    # American: per-deal waterfalls.
    deal_results = {}
    gp_total = 0.0
    for name, flows in deals.items():
        r = run_waterfall(flows, pref_rate=pref_rate, promote_pct=promote_pct)
        deal_results[name] = r
        gp_total += r["gp_total_promote"]

    # Aggregate LP economics by pooling LP flows across deals.
    all_lp_flows = [f for r in deal_results.values() for f in r["lp_flows"]]
    try:
        agg_lp_irr = xirr(all_lp_flows)
    except ValueError:
        agg_lp_irr = float("nan")
    contributed_sum = sum(-a for _, a in all_lp_flows if a < 0)
    distributed_sum = sum(a for _, a in all_lp_flows if a > 0)
    agg_lp_moic = (
        distributed_sum / contributed_sum if contributed_sum > 0 else float("inf")
    )

    result = {
        "style": "american",
        "deals": deal_results,
        "gp_total": gp_total,
        "lp_distributed": distributed_sum,
        "lp_contributed": contributed_sum,
        "lp_irr": agg_lp_irr,
        "lp_moic": agg_lp_moic,
    }

    if compute_clawback:
        # Run the same flows European-style and compare GP totals.
        pooled = [f for flows in deals.values() for f in flows]
        eu = run_waterfall(pooled, pref_rate=pref_rate, promote_pct=promote_pct)
        result["gp_total_if_european"] = eu["gp_total_promote"]
        result["clawback"] = max(0.0, gp_total - eu["gp_total_promote"])
    else:
        result["clawback"] = 0.0

    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="Single-deal CSV of date,amount (signed)")
    src.add_argument("--fund-dir", help="Directory of one CSV per deal (fund-level mode)")
    p.add_argument("--pref", type=float, default=0.08, help="preferred return (annual, default 0.08)")
    p.add_argument("--promote", type=float, default=0.20, help="GP promote share in Tier 4a (default 0.20)")
    p.add_argument("--second-hurdle", type=float, default=None,
                   help="LP IRR threshold for second promote tier (single-deal mode; e.g., 0.15)")
    p.add_argument("--second-promote", type=float, default=None,
                   help="GP promote share above the second hurdle (e.g., 0.30)")
    p.add_argument("--style", choices=["american", "european"], default="european",
                   help="Fund-level mode only: 'european' pools all deal flows; "
                        "'american' computes per-deal then aggregates (default 'european')")
    p.add_argument("--no-clawback", action="store_true",
                   help="Skip clawback computation in American fund-level mode")
    args = p.parse_args()

    if args.fund_dir:
        _run_fund_cli(args)
    else:
        _run_single_cli(args)


def _run_single_cli(args):
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


def _run_fund_cli(args):
    import os
    import glob

    deals = {}
    csvs = sorted(glob.glob(os.path.join(args.fund_dir, "*.csv")))
    if not csvs:
        raise SystemExit(f"No CSVs found in {args.fund_dir}")
    for path in csvs:
        name = os.path.splitext(os.path.basename(path))[0]
        deals[name] = parse_csv(path)

    result = fund_waterfall(
        deals,
        style=args.style,
        pref_rate=args.pref,
        promote_pct=args.promote,
        compute_clawback=not args.no_clawback,
    )

    bar = "=" * 72
    print(bar)
    print(f"FUND-LEVEL WATERFALL ({result['style'].upper()})")
    print(bar)
    print(f"Preferred return:          {args.pref * 100:.1f}% annual")
    print(f"Promote:                   {args.promote * 100:.1f}% to GP above pref")
    print(f"Deals:                     {len(deals)}")
    print("-" * 72)
    print(f"LP contributed:            ${result['lp_contributed']:>15,.0f}")
    print(f"LP distributed:            ${result['lp_distributed']:>15,.0f}")
    print(f"LP IRR (pooled):           {result['lp_irr'] * 100:>15.2f}%")
    print(f"LP MOIC (pooled):          {result['lp_moic']:>15.2f}x")
    print("-" * 72)
    print(f"GP total promote:          ${result['gp_total']:>15,.0f}")
    if result["style"] == "american" and "gp_total_if_european" in result:
        print(f"  (vs. European-equivalent): ${result['gp_total_if_european']:>15,.0f}")
        if result["clawback"] > 0:
            print(f"  CLAWBACK (excess to LP):  ${result['clawback']:>15,.0f}")
        else:
            print(f"  Clawback:                  ${0:>15,.0f}  (no excess)")
    print(bar)

    if result["style"] == "american" and result["deals"]:
        print()
        print("PER-DEAL DETAIL")
        print(f"{'Deal':<24} {'LP IRR':>10} {'LP MOIC':>9} {'GP Promote':>14}")
        print("-" * 72)
        for name, r in result["deals"].items():
            irr_str = f"{r['lp_irr']*100:.2f}%" if r['lp_irr'] == r['lp_irr'] else "n/a"
            print(
                f"{name:<24} {irr_str:>10} {r['lp_moic']:>8.2f}x "
                f"${r['gp_total_promote']:>13,.0f}"
            )
        print(bar)


if __name__ == "__main__":
    main()
