"""
returns.py — Compute IRR, NPV, MOIC, MIRR, and equity multiple from cash flow streams.

Cash flow convention (LP perspective):
  Contributions (capital calls)  = NEGATIVE
  Distributions (returns of cap) = POSITIVE

Usage:
  python returns.py --csv flows.csv
  python returns.py --inline "2020-01-15:-1000000;2021-06-30:50000;2025-12-15:1800000"

CSV format (date,amount):
  2020-01-15,-1000000
  2021-06-30,50000
  ...

Output: IRR (annualized), NPV at given discount rate, MOIC, total contributed,
total distributed, holding period. When the flow sequence has more than one
sign change (e.g., capital call → distribution → recap → distribution), the
script ALSO prints all candidate IRRs and an MIRR — see "Non-conventional
flows" below.

Non-conventional flows and why IRR can lie

  IRR solves NPV(r) = 0. For a "conventional" series — all contributions
  first, then all distributions — there is exactly one positive real root
  and IRR is well-defined.

  For series with 2+ sign changes (recaps, capex draws after early
  distributions, top-ups, etc.) the equation can have MULTIPLE positive
  real roots. Bisection silently returns one of them, and which one
  depends on bracket geometry, not economics. This produces confidently
  wrong numbers.

  This module:
    - count_sign_changes(flows)   → diagnoses the structure
    - xirr_all_roots(flows)       → returns every real root in the bracket
    - xmirr(flows, fr, rr)        → modified IRR with explicit financing
                                    and reinvestment rates; always unique

  When in doubt on multi-sign-change flows, report MIRR (with reasonable
  fund-cost-of-capital rates) instead of IRR.
"""

import argparse
import csv
from datetime import date, datetime
from typing import Iterable


def parse_date(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognized date format: {s}")


def _xnpv(rate: float, flows: list[tuple[date, float]]) -> float:
    """Net present value for dated cash flows. rate is annual."""
    if rate <= -1:
        return float("inf")
    t0 = flows[0][0]
    return sum(amt / (1 + rate) ** ((d - t0).days / 365.0) for d, amt in flows)


def xirr(flows: list[tuple[date, float]]) -> float:
    """
    Solve for the rate such that xnpv(rate) == 0.
    Bisection over a wide bracket — robust, no SciPy dependency.

    Caveat: for flows with multiple sign changes, NPV(r) can have multiple
    positive real roots. Bisection returns ONE of them — which one depends
    on the bracket, not on economics. Use count_sign_changes() to detect
    this and xirr_all_roots() / xmirr() to handle it correctly.
    """
    flows = sorted(flows, key=lambda x: x[0])
    if not any(a < 0 for _, a in flows) or not any(a > 0 for _, a in flows):
        raise ValueError("IRR requires both negative and positive cash flows")

    lo, hi = -0.999999, 10.0  # -100% to +1000% annual
    for _ in range(200):
        mid = (lo + hi) / 2
        v = _xnpv(mid, flows)
        if abs(v) < 1e-6 or (hi - lo) < 1e-9:
            return mid
        if v > 0:
            lo = mid
        else:
            hi = mid
    return mid


def count_sign_changes(flows: list[tuple[date, float]]) -> int:
    """Count sign changes in the chronologically-sorted flow sequence.

    Conventional flow pattern (one capital deployment then distributions)
    has exactly 1 sign change and a unique IRR. Two or more sign changes
    (recaps, follow-on capital calls, capex draws after distributions)
    can produce multiple IRRs — see xirr_all_roots().
    """
    flows = sorted(flows, key=lambda x: x[0])
    nonzero = [a for _, a in flows if a != 0]
    if len(nonzero) < 2:
        return 0
    changes = 0
    prev_sign = 1 if nonzero[0] > 0 else -1
    for a in nonzero[1:]:
        sign = 1 if a > 0 else -1
        if sign != prev_sign:
            changes += 1
            prev_sign = sign
    return changes


def xirr_all_roots(
    flows: list[tuple[date, float]],
    bracket: tuple[float, float] = (-0.95, 10.0),
    samples: int = 2000,
) -> list[float]:
    """Find ALL IRRs in the bracket by sampling NPV and bisecting each
    sub-interval where NPV changes sign.

    For conventional flows (one sign change) returns a single-element list.
    For non-conventional flows may return 0, 1, or many roots, sorted ascending.

    Sampling near r=-1 is skipped (singularity); the default bracket starts
    at -0.95, which covers any economically meaningful negative return.
    """
    flows = sorted(flows, key=lambda x: x[0])
    if not any(a < 0 for _, a in flows) or not any(a > 0 for _, a in flows):
        raise ValueError("IRR requires both negative and positive cash flows")

    lo, hi = bracket
    if lo <= -1:
        raise ValueError("bracket lower bound must be > -1 (NPV diverges at r=-1)")

    step = (hi - lo) / samples
    roots: list[float] = []

    prev_r = lo
    prev_v = _xnpv(prev_r, flows)
    for i in range(1, samples + 1):
        r = lo + i * step
        v = _xnpv(r, flows)
        # Detect a sign change. Treat exact zero as a root directly.
        if v == 0:
            roots.append(r)
        elif prev_v != 0 and (prev_v > 0) != (v > 0):
            # Bisect within [prev_r, r] for a tight root.
            a, b = prev_r, r
            fa = prev_v
            for _ in range(80):
                mid = (a + b) / 2
                fm = _xnpv(mid, flows)
                if abs(fm) < 1e-9 or (b - a) < 1e-12:
                    break
                if (fm > 0) == (fa > 0):
                    a, fa = mid, fm
                else:
                    b = mid
            roots.append((a + b) / 2)
        prev_r = r
        prev_v = v

    return sorted(set(round(r, 9) for r in roots))


def moic(flows: Iterable[tuple[date, float]]) -> tuple[float, float, float]:
    """Return (moic, total_contributed, total_distributed)."""
    contributed = sum(-a for _, a in flows if a < 0)
    distributed = sum(a for _, a in flows if a > 0)
    if contributed == 0:
        return float("inf"), 0.0, distributed
    return distributed / contributed, contributed, distributed


def xmirr(
    flows: list[tuple[date, float]],
    finance_rate: float = 0.08,
    reinvest_rate: float = 0.08,
) -> float:
    """Modified IRR for dated cash flows.

    Negatives are financed back to the earliest date at finance_rate;
    positives are reinvested forward to the latest date at reinvest_rate.
    The modified rate that links the present value of negatives to the
    future value of positives over the total horizon is:

        MIRR = (FV_pos_at_end / PV_neg_at_start) ^ (1 / years) - 1

    Unlike IRR, MIRR is always unique. It's the right metric for any
    series with non-monotonic flows (recaps, mid-life capital calls).

    Choose finance_rate and reinvest_rate to reflect economic reality —
    fund cost-of-capital is a common default for both.
    """
    flows = sorted(flows, key=lambda x: x[0])
    if not any(a < 0 for _, a in flows) or not any(a > 0 for _, a in flows):
        raise ValueError("MIRR requires both negative and positive cash flows")
    t0 = flows[0][0]
    t_end = flows[-1][0]
    years = (t_end - t0).days / 365.0
    if years <= 0:
        raise ValueError("MIRR requires a non-zero time horizon")

    fv_pos = sum(
        a * (1 + reinvest_rate) ** ((t_end - d).days / 365.0)
        for d, a in flows if a > 0
    )
    pv_neg = sum(
        -a / (1 + finance_rate) ** ((d - t0).days / 365.0)
        for d, a in flows if a < 0
    )
    if pv_neg <= 0 or fv_pos <= 0:
        raise ValueError(
            "Cannot compute MIRR: PV of negatives or FV of positives is non-positive"
        )
    return (fv_pos / pv_neg) ** (1 / years) - 1


def hold_period(flows: list[tuple[date, float]]) -> float:
    flows = sorted(flows, key=lambda x: x[0])
    return (flows[-1][0] - flows[0][0]).days / 365.0


def _parse_inline(s: str) -> list[tuple[date, float]]:
    out = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        d_str, amt = chunk.split(":")
        out.append((parse_date(d_str), float(amt)))
    return out


def parse_csv(path: str) -> list[tuple[date, float]]:
    out = []
    with open(path) as f:
        for row in csv.reader(f):
            if not row or row[0].lstrip().startswith("#"):
                continue
            try:
                out.append((parse_date(row[0]), float(row[1].replace(",", ""))))
            except (ValueError, IndexError):
                continue  # skip headers
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="path to CSV of date,amount rows")
    src.add_argument("--inline", help="semicolon-separated date:amount pairs")
    p.add_argument("--discount-rate", type=float, default=0.10, help="discount rate for NPV (default 0.10)")
    p.add_argument("--finance-rate", type=float, default=0.08, help="MIRR financing rate for negatives (default 0.08)")
    p.add_argument("--reinvest-rate", type=float, default=0.08, help="MIRR reinvestment rate for positives (default 0.08)")
    args = p.parse_args()

    flows = parse_csv(args.csv) if args.csv else _parse_inline(args.inline)
    if len(flows) < 2:
        raise SystemExit("need at least 2 cash flows")

    irr = xirr(flows)
    m, contrib, dist = moic(flows)
    npv = _xnpv(args.discount_rate, flows)
    hp = hold_period(flows)
    sign_changes = count_sign_changes(flows)
    mirr = xmirr(flows, finance_rate=args.finance_rate, reinvest_rate=args.reinvest_rate)

    bar = "-" * 60
    print(bar)
    print(f"Cash flows analyzed:       {len(flows)}")
    print(f"Period:                    {flows[0][0]} -> {flows[-1][0]}  ({hp:.2f} years)")
    print(f"Total contributed:         ${contrib:>15,.0f}")
    print(f"Total distributed:         ${dist:>15,.0f}")
    print(f"Net cash flow:             ${dist - contrib:>15,.0f}")
    print(f"Sign changes in flows:     {sign_changes:>15d}{'  (conventional)' if sign_changes == 1 else ''}")
    print(bar)
    print(f"IRR (annualized):          {irr * 100:>15.2f}%")
    print(f"MOIC (equity multiple):    {m:>15.2f}x")
    print(f"NPV @ {args.discount_rate * 100:.1f}%:                 ${npv:>15,.0f}")
    print(f"MIRR ({args.finance_rate*100:.1f}%/{args.reinvest_rate*100:.1f}%):            {mirr * 100:>15.2f}%")
    print(bar)

    if sign_changes > 1:
        # Non-conventional flows: IRR may not be unique. Show all roots.
        roots = xirr_all_roots(flows)
        print()
        print("!" * 60)
        print(f"WARNING: {sign_changes} sign changes in flow sequence.")
        print("The IRR equation can have multiple positive real roots --")
        print("the IRR reported above is ONE of them, not necessarily the")
        print("economically meaningful one.")
        if len(roots) > 1:
            print(f"All real roots found in [-95%, 1000%]:")
            for r in roots:
                print(f"  {r * 100:>8.2f}%")
        elif len(roots) == 1:
            print(f"Only one real root found at {roots[0] * 100:.2f}% — IRR is unique despite sign changes.")
        else:
            print("No real roots found in the bracket.")
        print(f"Recommend reporting MIRR ({mirr * 100:.2f}%) instead of IRR for this stream.")
        print("!" * 60)


if __name__ == "__main__":
    main()
