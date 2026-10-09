# Investor & LP Reporting

This reference covers fund- and deal-level reporting to limited partners: capital accounts, returns metrics, waterfalls, and the cash mechanics of capital calls and distributions.

## Returns metrics — definitions and when to use each

| Metric | Formula | Use when |
|---|---|---|
| **IRR** | Discount rate where NPV of cash flows = 0 | Reporting time-weighted return on an investment with multiple cash flows |
| **MOIC / Equity Multiple** | Total distributions ÷ Total contributions | Reporting total profit on capital; time-insensitive |
| **TVPI** | (Distributions + Residual NAV) ÷ Paid-in Capital | Fund-level; total value created per dollar in |
| **DPI** | Distributions ÷ Paid-in Capital | Fund-level; cash actually returned ("how much have I gotten back") |
| **RVPI** | Residual NAV ÷ Paid-in Capital | Fund-level; what's still in the ground (TVPI − DPI = RVPI) |
| **PIC** | Paid-in Capital ÷ Committed Capital | How much of an LP's commitment has been called |
| **Net IRR** | IRR after all GP fees and carry | What the LP actually realizes |
| **Gross IRR** | IRR before fees and carry, at the asset level | Track record reporting; benchmarks GP investment skill |

### Reporting conventions

- **Gross vs. net**: always specify. "8% IRR" without context is meaningless.
- **Realized vs. unrealized**: separate realized cash flows from mark-to-market NAV. LPs trust DPI more than TVPI because DPI is cash in hand.
- **Vintage year**: fund-level returns are compared against peer vintage benchmarks (Preqin, Cambridge, MSCI). A 12% IRR is great in a 2018 vintage and mediocre in a 2010 vintage.
- **J-curve**: in early years, fees and capex depress returns before distributions begin. A negative-to-low IRR in years 1-3 is normal. Don't apologize for it; explain it.

## Capital accounts

An LP's capital account tracks their share of contributions, distributions, allocated income/loss, and ending NAV. Standard rollforward:

```
Beginning capital account                 $XXX,XXX
  + Contributions during period             $XX,XXX
  − Distributions during period             $XX,XXX
  + Allocated net income (or − loss)        $XX,XXX
  +/− Mark-to-market on assets              $XX,XXX
  − Management fees                         $X,XXX
  − Allocated carry accrual (if any)        $X,XXX
Ending capital account                    $XXX,XXX
```

Issue separately to each LP — pro-rata to their commitment is typical, but side letters or different fee classes can alter this.

## Waterfalls — the mechanics

The waterfall is the cash-distribution rulebook in the partnership agreement (PSA / LPA). Two big questions define the structure:

### European vs. American

- **European (whole-fund)**: GP receives no carry until LPs have received all contributions back across the entire fund, plus their preferred return. Common in PE funds.
- **American (deal-by-deal)**: GP earns carry on each deal as it's realized, subject to a clawback if later deals underperform. Common in real estate.

### Tier structure (most common 4-tier RE waterfall)

```
Tier 1 — Return of Capital
  100% to LP until LP has received back all contributed capital.

Tier 2 — Preferred Return
  100% to LP until LP has received [8% per annum] cumulative compounded
  return on contributed capital.

Tier 3 — GP Catch-up
  [50/50 or 80/20 or 100% to GP] until GP has received [20%] of all
  profits distributed in Tiers 2 + 3. Brings GP to its promote share
  of total profits "as if there had been no preferred return."

Tier 4 — Carried Interest (Promote)
  [80% LP / 20% GP] of remaining cash flow.
```

Often a second promote tier kicks in at a higher hurdle:

```
Tier 4a — to a [15%] IRR:   80/20
Tier 4b — above [15%] IRR:  70/30 or 60/40
```

Read the actual PSA. Variations matter:

- **Pref accrual basis**: compounded annually, monthly, or simple? Compounded matters in long holds.
- **Pref on contributed vs. invested capital**: does the pref accrue on capital that's been returned, or only what's still outstanding?
- **Catch-up percentage**: 50%, 80%, or 100% are all common. 100% catch-up means GP is "made whole" fastest.
- **Lookback / clawback**: if early distributions overpaid the GP, must GP return cash at fund end?

## Capital call mechanics

When the GP needs cash (closing, capex, fees), it issues a capital call notice:

- **Notice period**: typically 10 business days
- **Amount**: stated in dollars and as % of unfunded commitment
- **Use of proceeds**: usually specified at a high level
- **Default consequence**: usually punitive — interest, forced sale of interest, dilution

Track called capital cumulatively to compute PIC and unfunded commitment.

## Distribution mechanics

When the GP returns cash to LPs:

- **Source identified**: operating cash flow, refinancing proceeds, partial sale, full sale
- **Tax character**: ordinary income, return of capital, capital gain (the partnership's K-1 ultimately governs)
- **Waterfall tier**: which tier(s) the distribution flowed through

A clean distribution notice tells the LP: total amount, their share, basis-vs-gain breakdown, waterfall trace, and resulting capital account impact.

## Common pitfalls

- **Mixing realized and unrealized.** Don't blend cash IRR with NAV-marked IRR without labeling.
- **Wrong pref base.** Pref usually accrues on *outstanding* (unreturned) capital, not contributed. Getting this wrong overstates the GP's promote.
- **Forgetting fees in net returns.** Net IRR must reflect management fees, fund expenses, and accrued carry. LPs check this.
- **Ignoring the catch-up.** During the catch-up tier, the GP's share can be 100% — this is correct and not a typo.

## Computing returns from a cash flow stream

Use `scripts/returns.py` to compute IRR and MOIC from a list of dated cash flows. For a waterfall computation, use `scripts/waterfall.py`. Both expect cash flows as `(date, amount)` pairs where contributions are negative and distributions are positive (LP perspective).
