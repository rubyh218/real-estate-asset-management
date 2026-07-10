"""
debt_metrics.py — Compute standard debt service metrics for a property.

Calculates: DSCR, Debt Yield, LTV/LTC, breakeven occupancy, and a max-loan
sizing analysis (binding constraint of LTV / DSCR / debt yield).

Usage:
  python debt_metrics.py \
      --noi 4500000 \
      --loan-balance 50000000 \
      --rate 0.065 --term-yrs 10 --amort-yrs 30 \
      --value 85000000 \
      --gpr 5800000 --opex 2300000

  # Or for max-loan sizing:
  python debt_metrics.py \
      --noi 4500000 --value 85000000 \
      --rate 0.065 --term-yrs 10 --amort-yrs 30 \
      --max-ltv 0.65 --min-dscr 1.30 --min-debt-yield 0.09 \
      --size

Notes:
  - Pass --io-period 0 (default 0) for fully-amortizing debt.
  - --amort-yrs is the amortization period; pass equal to --term-yrs for I/O at
    sale balloon, or a separate longer period for partial amort.
  - --amort-yrs 0 = interest-only for the full term.
"""

import argparse


def _annual_debt_service(loan: float, rate: float, amort_yrs: int) -> float:
    """Annual debt service (interest + principal) on a level-payment amortizing loan."""
    if amort_yrs <= 0:
        return loan * rate  # interest-only
    monthly_rate = rate / 12
    n = amort_yrs * 12
    if monthly_rate == 0:
        monthly_pmt = loan / n
    else:
        monthly_pmt = loan * (monthly_rate * (1 + monthly_rate) ** n) / ((1 + monthly_rate) ** n - 1)
    return monthly_pmt * 12


def dscr(noi: float, debt_service: float) -> float:
    if debt_service == 0:
        return float("inf")
    return noi / debt_service


def debt_yield(noi: float, loan_balance: float) -> float:
    if loan_balance == 0:
        return float("inf")
    return noi / loan_balance


def ltv(loan: float, value: float) -> float:
    return loan / value if value else 0.0


def breakeven_occupancy(opex: float, debt_service: float, gpr: float) -> float:
    if gpr == 0:
        return float("inf")
    return (opex + debt_service) / gpr


def size_max_loan(
    noi: float,
    value: float,
    rate: float,
    amort_yrs: int,
    max_ltv: float,
    min_dscr: float,
    min_debt_yield: float,
) -> dict:
    """Find the binding loan constraint and the max loan it permits."""
    by_ltv = max_ltv * value

    # DSCR constraint: solve for loan such that NOI / DS = min_dscr
    # DS depends on loan, so we work backward: max DS = NOI / min_dscr.
    # Then back-solve loan from DS using the amortizing payment formula.
    max_ds = noi / min_dscr
    if amort_yrs <= 0:
        by_dscr = max_ds / rate if rate > 0 else float("inf")
    else:
        mr = rate / 12
        n = amort_yrs * 12
        max_monthly_pmt = max_ds / 12
        if mr == 0:
            by_dscr = max_monthly_pmt * n
        else:
            by_dscr = max_monthly_pmt * ((1 + mr) ** n - 1) / (mr * (1 + mr) ** n)

    by_debt_yield = noi / min_debt_yield

    constraints = {
        "LTV":         by_ltv,
        "DSCR":        by_dscr,
        "Debt Yield":  by_debt_yield,
    }
    binding = min(constraints, key=constraints.get)
    max_loan = constraints[binding]
    return {
        "constraints": constraints,
        "binding": binding,
        "max_loan": max_loan,
        "implied_dscr": dscr(noi, _annual_debt_service(max_loan, rate, amort_yrs)),
        "implied_debt_yield": debt_yield(noi, max_loan),
        "implied_ltv": ltv(max_loan, value),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--noi", type=float, required=True, help="Annual NOI ($)")
    p.add_argument("--value", type=float, help="Property value ($)")
    p.add_argument("--loan-balance", type=float, help="Current loan balance ($)")
    p.add_argument("--rate", type=float, required=True, help="Loan rate (decimal, e.g., 0.065)")
    p.add_argument("--term-yrs", type=int, default=10, help="Loan term (years, default 10)")
    p.add_argument("--amort-yrs", type=int, default=30, help="Amortization (years, default 30; 0 = IO)")
    p.add_argument("--gpr", type=float, help="Gross Potential Rent ($) for breakeven occupancy")
    p.add_argument("--opex", type=float, help="Operating expenses ($) for breakeven occupancy")
    p.add_argument("--size", action="store_true", help="Run max-loan sizing analysis")
    p.add_argument("--max-ltv", type=float, default=0.65, help="Max LTV constraint (default 0.65)")
    p.add_argument("--min-dscr", type=float, default=1.25, help="Min DSCR constraint (default 1.25)")
    p.add_argument("--min-debt-yield", type=float, default=0.08, help="Min debt yield (default 0.08)")
    args = p.parse_args()

    print("-" * 64)
    print(f"NOI:                       ${args.noi:>15,.0f}")
    if args.value:
        print(f"Property value:            ${args.value:>15,.0f}")
        print(f"Implied cap rate (NOI/V):  {args.noi / args.value * 100:>15.2f}%")
    print(f"Loan rate:                 {args.rate * 100:>15.2f}%")
    print(f"Term / Amort (yrs):        {args.term_yrs:>15d} / {args.amort_yrs}")
    print("-" * 64)

    if args.size:
        if not args.value:
            raise SystemExit("--value is required for --size analysis")
        result = size_max_loan(
            noi=args.noi,
            value=args.value,
            rate=args.rate,
            amort_yrs=args.amort_yrs,
            max_ltv=args.max_ltv,
            min_dscr=args.min_dscr,
            min_debt_yield=args.min_debt_yield,
        )
        print("MAX LOAN SIZING")
        print(f"  Max via LTV ({args.max_ltv * 100:.0f}%):              ${result['constraints']['LTV']:>15,.0f}")
        print(f"  Max via DSCR ({args.min_dscr:.2f}x):            ${result['constraints']['DSCR']:>15,.0f}")
        print(f"  Max via Debt Yield ({args.min_debt_yield * 100:.1f}%):    ${result['constraints']['Debt Yield']:>15,.0f}")
        print("-" * 64)
        print(f"  Binding constraint:      {result['binding']:>15s}")
        print(f"  Max loan:                ${result['max_loan']:>15,.0f}")
        print(f"  At this loan:")
        print(f"    DSCR:                  {result['implied_dscr']:>15.2f}x")
        print(f"    Debt Yield:            {result['implied_debt_yield'] * 100:>15.2f}%")
        print(f"    LTV:                   {result['implied_ltv'] * 100:>15.2f}%")
        return

    if not args.loan_balance:
        raise SystemExit("--loan-balance required (or use --size for max-loan analysis)")

    ds = _annual_debt_service(args.loan_balance, args.rate, args.amort_yrs)
    print(f"Loan balance:              ${args.loan_balance:>15,.0f}")
    print(f"Annual debt service:       ${ds:>15,.0f}")
    print("-" * 64)
    print(f"DSCR:                      {dscr(args.noi, ds):>15.2f}x")
    print(f"Debt Yield:                {debt_yield(args.noi, args.loan_balance) * 100:>15.2f}%")
    if args.value:
        print(f"LTV:                       {ltv(args.loan_balance, args.value) * 100:>15.2f}%")
    if args.gpr and args.opex is not None:
        beo = breakeven_occupancy(args.opex, ds, args.gpr)
        print(f"Breakeven occupancy:       {beo * 100:>15.2f}%")
    print("-" * 64)


if __name__ == "__main__":
    main()
