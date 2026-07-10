"""
yield_maintenance.py — Yield maintenance (YM) prepayment penalty and refi-timing analysis.

WHY THIS EXISTS
---------------
Agency loans (Fannie / Freddie / FHA) and most fixed-rate CMBS impose a
"make-whole" prepayment penalty during the bulk of the loan term. The penalty
is the present value of the spread between the contract rate and the lender's
reinvestment rate (typically the matched-maturity US Treasury), discounted at
that same Treasury rate. The intent: the lender is held indifferent between
holding the loan to maturity and being prepaid now and reinvesting in
Treasuries.

The penalty typically converts to a flat fee (commonly 1% of UPB) during an
"open period" — usually the last 3–6 months before maturity — and is waived
entirely on or near the maturity date itself.

This module surfaces:
  - YM penalty at any given prepay date
  - Open-period flat-fee penalty
  - "Savings if wait" — the dollar (and % of UPB) decline in penalty
    between today and the start of the open period
  - A decision-support summary that an AM uses to time refi or sale

CAVEATS
-------
1. YM definitions vary by loan doc. Common variations:
     - PV at Treasury yield only (the "Freddie standard" used here)
     - PV at Treasury + spread (rarer; lender-friendlier)
     - YM with a floor of 1% of UPB (common in older docs)
     - Defeasance (different mechanism — securities substitution, not a fee)
   Read the prepayment exhibit in the loan doc before quoting a number.
2. We assume monthly compounding (12 periods/yr), matched-maturity Treasury,
   and that scheduled interest is paid on the current UPB through prepay.
   For amortizing loans we simulate the remaining schedule month-by-month.
3. Treasury rate must be quoted on the SAME compounding basis as the loan
   (annualized monthly), which it is for all common quotes.

Usage:
  python yield_maintenance.py \\
      --upb 8500000 \\
      --loan-rate 0.0425 \\
      --treasury-rate 0.0410 \\
      --maturity 2026-02-10 \\
      --today 2025-08-14 \\
      --amort-yrs 30 \\
      --open-period-months 3 \\
      --open-period-fee 0.01
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

@dataclass
class YMResult:
    """One snapshot of the prepayment penalty calculus."""
    today: date
    maturity: date
    ym_expiry_date: date            # the boundary between YM and open-period
    months_to_ym_expiry: int        # 0 if already at/inside the open period
    months_to_maturity: int         # 0 if at/past maturity
    upb: float
    loan_rate: float
    treasury_rate: float
    current_ym_penalty: float       # 0 if already in open period or past maturity
    open_period_penalty: float      # the flat fee that applies in the open period
    in_open_period: bool
    savings_if_wait_to_open: float  # current YM - open_period_penalty (clamped >= 0)
    savings_pct_of_upb: float


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _months_between(d1: date, d2: date) -> int:
    """Whole-or-partial months from d1 to d2, rounded up — a 1-day remainder
    counts as a full month, so the YM clock never hits 0 before the boundary
    date. Returns 0 if d2 <= d1."""
    if d2 <= d1:
        return 0
    n = (d2.year - d1.year) * 12 + (d2.month - d1.month)
    if _add_months(d1, n) < d2:
        n += 1
    return n


def _add_months(d: date, n: int) -> date:
    """Add n calendar months to d, clamping day-of-month to length."""
    import calendar
    total = d.month - 1 + n
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _amort_balance_schedule(
    upb: float,
    loan_rate: float,
    amort_yrs: int,
    months: int,
) -> list[float]:
    """Return the EOM balance for the next `months` months on a level-pay loan
    starting from `upb`. amort_yrs=0 → interest-only (constant balance)."""
    if amort_yrs <= 0:
        return [upb] * months

    monthly_rate = loan_rate / 12
    n_total = amort_yrs * 12
    if monthly_rate > 0:
        monthly_pmt = upb * (
            monthly_rate * (1 + monthly_rate) ** n_total
        ) / ((1 + monthly_rate) ** n_total - 1)
    else:
        monthly_pmt = upb / n_total

    balances: list[float] = []
    bal = upb
    for _ in range(months):
        interest = bal * monthly_rate
        principal = min(monthly_pmt - interest, bal)
        if principal < 0:
            principal = 0.0
        bal = max(0.0, bal - principal)
        balances.append(bal)
    return balances


def compute_ym_penalty(
    upb: float,
    loan_rate: float,
    treasury_rate: float,
    remaining_months: int,
    amort_yrs: int = 0,
) -> float:
    """Compute the make-whole YM penalty.

    For each remaining month i (1..N), the foregone interest is:
        balance_{i-1} * (loan_rate - treasury_rate) / 12

    discounted to today at the Treasury rate. Sum across all remaining months.

    Returns 0 if loan_rate <= treasury_rate (no make-whole owed) or if
    remaining_months <= 0.
    """
    if remaining_months <= 0:
        return 0.0
    if loan_rate <= treasury_rate:
        return 0.0

    monthly_t = treasury_rate / 12
    monthly_spread = (loan_rate - treasury_rate) / 12

    balances = _amort_balance_schedule(upb, loan_rate, amort_yrs, remaining_months)
    # Interest in month i accrues on the BEGINNING-of-month balance,
    # i.e., the EOM balance from month i-1. Month 1's beginning balance is UPB.
    beginning_balances = [upb] + balances[:-1]

    total = 0.0
    for i, bal in enumerate(beginning_balances, start=1):
        cashflow = bal * monthly_spread
        total += cashflow / (1 + monthly_t) ** i
    return total


def analyze_prepay_timing(
    upb: float,
    loan_rate: float,
    treasury_rate: float,
    maturity: date,
    today: date,
    open_period_months: int = 3,
    open_period_fee_pct: float = 0.01,
    amort_yrs: int = 0,
) -> YMResult:
    """Compute current YM penalty + open-period flat fee + savings if wait."""
    ym_expiry = _add_months(maturity, -open_period_months)
    months_to_maturity = _months_between(today, maturity)
    months_to_ym_expiry = _months_between(today, ym_expiry)
    in_open_period = today >= ym_expiry

    open_period_penalty = upb * open_period_fee_pct

    if today >= maturity:
        # Past maturity — loan is due, no prepay penalty applies.
        current_penalty = 0.0
    elif in_open_period:
        # Already in open period — flat fee, not YM.
        current_penalty = open_period_penalty
    else:
        # YM applies. Remaining months = (today → ym_expiry).
        current_penalty = compute_ym_penalty(
            upb=upb,
            loan_rate=loan_rate,
            treasury_rate=treasury_rate,
            remaining_months=months_to_ym_expiry,
            amort_yrs=amort_yrs,
        )

    savings = max(0.0, current_penalty - open_period_penalty)
    savings_pct = savings / upb if upb > 0 else 0.0

    return YMResult(
        today=today,
        maturity=maturity,
        ym_expiry_date=ym_expiry,
        months_to_ym_expiry=months_to_ym_expiry,
        months_to_maturity=months_to_maturity,
        upb=upb,
        loan_rate=loan_rate,
        treasury_rate=treasury_rate,
        current_ym_penalty=current_penalty,
        open_period_penalty=open_period_penalty,
        in_open_period=in_open_period,
        savings_if_wait_to_open=savings,
        savings_pct_of_upb=savings_pct,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> date:
    from datetime import datetime
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--upb", type=float, required=True, help="Unpaid principal balance ($)")
    p.add_argument("--loan-rate", type=float, required=True, help="Loan note rate (decimal, e.g., 0.0425)")
    p.add_argument("--treasury-rate", type=float, required=True,
                   help="Reinvest rate — typically matched-maturity Treasury (decimal)")
    p.add_argument("--maturity", required=True, help="Loan maturity date (YYYY-MM-DD)")
    p.add_argument("--today", default=None,
                   help="Analysis date (YYYY-MM-DD); defaults to today")
    p.add_argument("--amort-yrs", type=int, default=0,
                   help="Amortization period (yrs); 0 = interest-only (default)")
    p.add_argument("--open-period-months", type=int, default=3,
                   help="Months before maturity when YM converts to flat fee (default 3)")
    p.add_argument("--open-period-fee", type=float, default=0.01,
                   help="Open-period prepay fee as fraction of UPB (default 0.01 = 1%%)")
    args = p.parse_args()

    today = _parse_date(args.today) if args.today else date.today()
    maturity = _parse_date(args.maturity)

    r = analyze_prepay_timing(
        upb=args.upb,
        loan_rate=args.loan_rate,
        treasury_rate=args.treasury_rate,
        maturity=maturity,
        today=today,
        open_period_months=args.open_period_months,
        open_period_fee_pct=args.open_period_fee,
        amort_yrs=args.amort_yrs,
    )

    bar = "-" * 68
    print(bar)
    print("PREPAYMENT PENALTY ANALYSIS")
    print(bar)
    print(f"UPB:                          ${r.upb:>16,.0f}")
    print(f"Loan rate:                    {r.loan_rate*100:>16.3f}%")
    print(f"Reinvest rate (Treasury):     {r.treasury_rate*100:>16.3f}%")
    print(f"Spread:                       {(r.loan_rate-r.treasury_rate)*100:>16.3f}%")
    print(bar)
    print(f"Today:                        {r.today!s:>16}")
    print(f"Maturity:                     {r.maturity!s:>16}")
    print(f"Open period begins:           {r.ym_expiry_date!s:>16}")
    print(f"Months to open period:        {r.months_to_ym_expiry:>16d}")
    print(f"Months to maturity:           {r.months_to_maturity:>16d}")
    print(bar)
    if r.today >= r.maturity:
        print("LOAN HAS MATURED — no prepay penalty applies.")
    elif r.in_open_period:
        print("Currently in OPEN PERIOD.")
        print(f"Penalty (1% flat fee):        ${r.open_period_penalty:>16,.0f}")
    else:
        print(f"Current YM penalty:           ${r.current_ym_penalty:>16,.0f}  "
              f"({r.current_ym_penalty/r.upb*100:.2f}% of UPB)")
        print(f"Post-YM penalty (open period):${r.open_period_penalty:>16,.0f}  "
              f"({args.open_period_fee*100:.1f}% of UPB)")
        print(f"YM savings if wait to open:   ${r.savings_if_wait_to_open:>16,.0f}  "
              f"({r.savings_pct_of_upb*100:.2f}% of UPB)")
    print(bar)


if __name__ == "__main__":
    main()
