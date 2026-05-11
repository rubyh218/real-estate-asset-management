"""
returns.py — Compute IRR, NPV, MOIC, and equity multiple from cash flow streams.

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
total distributed, holding period.
"""

import argparse
import csv
from datetime import date, datetime
from typing import Iterable


def _parse_date(s: str) -> date:
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


def xirr(flows: list[tuple[date, float]], guess: float = 0.10) -> float:
    """
    Solve for the rate such that xnpv(rate) == 0.
    Brent's method via bisection — robust to bad guesses, no SciPy dependency.
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


def moic(flows: Iterable[tuple[date, float]]) -> tuple[float, float, float]:
    """Return (moic, total_contributed, total_distributed)."""
    contributed = sum(-a for _, a in flows if a < 0)
    distributed = sum(a for _, a in flows if a > 0)
    if contributed == 0:
        return float("inf"), 0.0, distributed
    return distributed / contributed, contributed, distributed


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
        out.append((_parse_date(d_str), float(amt)))
    return out


def _parse_csv(path: str) -> list[tuple[date, float]]:
    out = []
    with open(path) as f:
        for row in csv.reader(f):
            if not row or row[0].lstrip().startswith("#"):
                continue
            try:
                out.append((_parse_date(row[0]), float(row[1].replace(",", ""))))
            except (ValueError, IndexError):
                continue  # skip headers
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="path to CSV of date,amount rows")
    src.add_argument("--inline", help="semicolon-separated date:amount pairs")
    p.add_argument("--discount-rate", type=float, default=0.10, help="discount rate for NPV (default 0.10)")
    args = p.parse_args()

    flows = _parse_csv(args.csv) if args.csv else _parse_inline(args.inline)
    if len(flows) < 2:
        raise SystemExit("need at least 2 cash flows")

    irr = xirr(flows)
    m, contrib, dist = moic(flows)
    npv = _xnpv(args.discount_rate, flows)
    hp = hold_period(flows)

    bar = "-" * 60
    print(bar)
    print(f"Cash flows analyzed:       {len(flows)}")
    print(f"Period:                    {flows[0][0]} -> {flows[-1][0]}  ({hp:.2f} years)")
    print(f"Total contributed:         ${contrib:>15,.0f}")
    print(f"Total distributed:         ${dist:>15,.0f}")
    print(f"Net cash flow:             ${dist - contrib:>15,.0f}")
    print(bar)
    print(f"IRR (annualized):          {irr * 100:>15.2f}%")
    print(f"MOIC (equity multiple):    {m:>15.2f}x")
    print(f"NPV @ {args.discount_rate * 100:.1f}%:                 ${npv:>15,.0f}")
    print(bar)


if __name__ == "__main__":
    main()
