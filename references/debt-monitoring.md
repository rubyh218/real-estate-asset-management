# Debt & Covenant Monitoring

This reference covers the asset manager's responsibilities around the property's debt: monitoring covenants, tracking maturity exposure, managing interest rate hedges, and evaluating refinance opportunities.

## Why debt management is non-optional

A property can perform well operationally and still be lost to the lender if covenants are tripped or the loan can't be refinanced at maturity. In rising-rate environments (2022-2024 cycle), refi risk often dwarfs operating risk. Asset managers who don't track debt closely lose assets and lose jobs.

## Core debt metrics

| Metric | Formula | Used for |
|---|---|---|
| **DSCR** | NOI ÷ Annual Debt Service | Most common cash flow covenant |
| **Debt Yield** | NOI ÷ Loan Balance | Lender's risk gauge; cap-rate-independent |
| **LTV** | Loan Balance ÷ Market Value | Most common balance covenant; subject to mark |
| **LTC** | Loan Balance ÷ Total Project Cost | Construction loans; based on basis, not value |
| **NOI Coverage** | NOI ÷ Interest expense | Subset of DSCR; ignores principal amortization |
| **Breakeven Occupancy** | (OpEx + Debt Service) ÷ GPR | What occupancy is needed to cover all costs |

### Important nuances

- **NOI for covenants ≠ NOI on financial statements.** Loan agreements define NOI specifically — usually with a management fee floor (e.g., greater of actual or 4% of EGI), a capex reserve, and specific income exclusions. Always read the loan's definition.
- **Annual Debt Service**: include principal amortization if applicable. Pure interest-only periods often hide the eventual amort burden.
- **Trailing vs. forward NOI for covenants**: most loans test on T-12 or T-3 annualized. Specify which.
- **Mark for LTV testing**: lender's appraisal, not owner's mark. Lender may require a new appraisal at re-test events.

## Covenant types

### Financial (incurrence vs. maintenance)

- **Maintenance covenants**: tested periodically (quarterly). Breach = default.
- **Incurrence covenants**: tested only on a triggering action (refi, draw, distribution). Less restrictive.

### Common maintenance covenants

- **Minimum DSCR** (e.g., 1.20x or 1.25x). Most common.
- **Minimum Debt Yield** (e.g., 7.5% or 8.0%). Common in CMBS and bridge debt.
- **Maximum LTV** (e.g., 75%). Less common as a maintenance covenant; more common at refi.
- **Cash trap / cash management trigger**: if DSCR or debt yield falls below a threshold, lender sweeps excess cash flow into a controlled account.
- **Cash sweep**: cash is held by lender rather than distributed to equity.

### Reporting covenants

Separate from financial covenants but equally important — breach can trigger default:

- Monthly / quarterly operating statements
- Annual budgets
- Annual audited financials
- Tax returns
- Occupancy reports / rent rolls
- Lease approval rights (for major leases)
- Capex approval rights

### Affirmative & negative covenants

- Affirmative: things you must do (maintain insurance, pay taxes, maintain property).
- Negative: things you can't do without consent (transfer the property, incur more debt, change management, change use).

## Covenant test exhibit

Standard format for a covenant test summary:

```
COVENANT COMPLIANCE — Q[X] [YYYY]
─────────────────────────────────────────────────────────────────────
Covenant         Required    Actual    Headroom    Status   Trend
─────────────────────────────────────────────────────────────────────
DSCR (T-12)      ≥ 1.25x     1.41x     +0.16x     PASS     ↑ from 1.38x
Debt Yield       ≥ 8.00%     8.7%      +70 bps    PASS     → flat
LTV              ≤ 70%       62%       +8 pp      PASS     ↓ from 64%
─────────────────────────────────────────────────────────────────────
Cash trap trigger: DSCR < 1.20x or DY < 7.5%       Status: not active

Reporting:  All current; next audit due [date]
```

Track headroom in absolute terms — "0.16x DSCR cushion" tells you immediately how much NOI can fall before the covenant trips.

## Maturity ladder

For any portfolio with debt, maintain a rolling maturity ladder:

```
MATURITY EXPOSURE                                          As of [Date]
─────────────────────────────────────────────────────────────────────
Year       # Loans    Balance      % of Total   Avg Rate   Avg LTV
─────────────────────────────────────────────────────────────────────
2026          2       $45M         12%          5.5%       68%
2027          3       $80M         22%          4.2%       65%
2028          5       $120M        33%          3.9%       62%
2029+         4       $120M        33%          4.5%       58%
─────────────────────────────────────────────────────────────────────
Total        14       $365M        100%
```

Flag loans maturing in the next 18 months as the active workstream. Anything maturing in 6 months without a refi plan is an emergency.

## Refi analysis

When a loan approaches maturity (or a refi-opportunistic moment arises), the asset manager builds a refi case.

### Key inputs

- **Current market loan terms**: rate, term, IO period, amort, max LTV, max LTC, min DSCR, min debt yield
- **Property NOI**: T-12 and NTM
- **Current value** (will drive max loan via LTV)
- **Existing loan balance** to retire
- **Prepayment cost** on existing loan (defeasance, yield maintenance, or step-down — read the loan doc)
- **Closing costs** (title, lender legal, financing fee, etc.) — typically 1-2% of new loan

### Yield maintenance + refi-timing analysis

Most agency (Fannie/Freddie/FHA) and fixed-rate CMBS loans carry a **yield maintenance** prepay penalty for the bulk of the term, converting to a flat fee (commonly 1% of UPB) during an **open period** in the last 3-6 months. The make-whole math is:

> YM = PV at Treasury yield of the spread between the contract rate and the matched-maturity Treasury, applied to the remaining scheduled balance.

The AM's recurring question is: **how much do I save by waiting until the open period vs. paying off / refinancing today?** Use `scripts/yield_maintenance.py`:

```bash
python scripts/yield_maintenance.py \
    --upb 50000000 --loan-rate 0.045 --treasury-rate 0.025 \
    --maturity 2028-06-30 --today 2026-05-14 \
    --amort-yrs 30 --open-period-months 3 --open-period-fee 0.01
```

Returns: current YM penalty, open-period flat fee, dollar/% savings if you wait, months until the open period begins. When the spread is tight (e.g., loan rate at 4.25% vs. Treasury at 4.10%), YM can be *less* than the 1% open-period fee — the script correctly reports zero savings rather than a negative number.

**Caveat:** YM definitions vary by loan doc. Common variations:
- PV at Treasury yield only (the "Freddie standard," what this script computes)
- PV at Treasury + a spread (rarer, lender-friendly)
- YM with a 1%-of-UPB floor (common in older docs)
- Defeasance (a different mechanism — securities substitution, not a fee)

Read the prepayment exhibit in the loan doc before quoting a number to IC.

### Standard refi exhibit

```
REFINANCE ANALYSIS
─────────────────────────────────────────────────────────────────────
Property NOI (NTM):                            $4,500,000
Current value (5.25% cap):                     $85,714,000

New loan sizing:
  Max via LTV (65%):                           $55,714,000
  Max via DSCR (1.30x at 6.50% I/O):           $53,300,000   ← binding
  Max via Debt Yield (9.0%):                   $50,000,000   ← binding
                                                 ─────────────
  Loan amount (binding constraint):            $50,000,000

Sources / Uses:
  New loan                                     $50,000,000
  Equity contribution / (distribution)          ($1,500,000)
                                                 ─────────────
  Total sources                                $48,500,000

  Existing loan payoff                         $44,000,000
  Prepayment cost (defeasance)                  $1,200,000
  Closing costs (1.5% × new loan)                 $750,000
  Net to equity / (capital call)                $2,550,000   ← cash to LPs
                                                 ─────────────
  Total uses                                   $48,500,000

Resulting Metrics:
  New DSCR:                                    1.30x
  New Debt Yield:                              9.0%
  New LTV:                                     58%
  Cash on cash to equity:                      X.X%
```

The binding constraint matters — if debt yield is binding, more NOI directly unlocks more proceeds. If LTV is binding, value matters more than NOI.

## Interest rate hedges

Most floating-rate loans (bridge, construction, some CMBS) require an interest rate cap. The asset manager monitors:

- **Cap strike**: the rate above which the cap pays
- **Cap term**: usually 2-3 years initially; replacement cap purchases at extension are a significant cost (and were a major hit to 2022-2024 bridge deals)
- **Cap counterparty rating**: most loans require A-rated counterparties; if downgraded, replacement may be required
- **Replacement cap reserve**: many loans require ongoing reserve deposits to fund the next cap purchase

Track time-to-expiry on every cap. Caps are expensive to replace when rates have moved — budget proactively.

## Workout / restructuring scenarios

When covenants are tripped or maturity passes without a refi:

- **Modification**: lender extends term, modifies rate, or relaxes covenants in exchange for paydown, fee, or cash equity.
- **Maturity extension**: short-term extension (6-12 months) to allow a refi or sale.
- **Cash equity infusion**: fresh capital from LPs to pay down loan and restore covenants.
- **Discounted Payoff (DPO)**: lender accepts less than face to be repaid. Common when collateral value is below loan.
- **Deed-in-lieu**: borrower hands the property to the lender, often with non-recourse carve-out releases. Last resort.
- **Foreclosure**: lender takes the property. Worst outcome.

When advising on these, model the equity recovery in each scenario. Sometimes the right answer is to hand it back; pride is expensive.

## Common pitfalls

- **Using management's NOI for covenant tests.** Loan defines NOI; use the loan definition.
- **Forgetting reporting covenants.** Most defaults at smaller GPs come from missed reporting, not financial covenants.
- **Ignoring cap replacement.** Floating-rate borrowers without a cap replacement plan have been blown up by this exact issue in the 2022-2024 cycle.
- **Optimistic NOI in refi sizing.** Lenders underwrite conservatively. Use a haircut to your own NOI projection.
