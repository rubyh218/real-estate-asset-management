# Property Performance Analysis

This reference covers rent roll analysis, T-12 / operating statement variance analysis, and NOI bridges. These are the building blocks of the QAR.

## Rent roll analysis

A rent roll is a snapshot of all leases at a point in time. Outputs the asset manager wants from any rent roll:

### Core metrics

- **Physical occupancy** = Occupied units (or SF) ÷ Total units (or SF)
- **Leased occupancy** = (Occupied + signed-not-yet-occupied) ÷ Total. Always ≥ physical.
- **Economic occupancy** = Actual rent collected ÷ Gross Potential Rent. Captures concessions, bad debt, vacancy.
- **In-place rent** vs. **market rent** — gap is loss-to-lease (LTL). Big LTL is upside; negative gap (over-market) is risk on renewal.
- **WALT / WAULT** (commercial) — weighted average remaining lease term, in years, weighted by rent or SF
- **Tenant concentration** (commercial) — top 5 tenants as % of NOI; flag anyone above 20%
- **Lease expiration ladder** — rolling 12-quarter expiration schedule by SF and by rent

### Standard rent roll exhibit

```
RENT ROLL SUMMARY                    As of [Date]
─────────────────────────────────────────────────────
Total units / SF:                    XXX / XXX,XXX SF
Occupied:                            XXX / XXX,XXX SF  (XX.X%)
Leased (incl. SNO):                  XXX / XXX,XXX SF  (XX.X%)
GPR (annualized):                    $X,XXX,XXX
In-place rent:                       $XX.XX /SF or $X,XXX /unit
Market rent (current):               $XX.XX /SF or $X,XXX /unit
Loss-to-lease:                       X.X%
WALT (rent-weighted):                X.X years
```

### Multifamily-specific rent roll cuts

- By floor plan / unit type — average rent, occupancy, mark-to-market by 1BR / 2BR / etc.
- Renewal pricing — recent renewal increases vs. new lease pricing
- Lease trade-out — new lease rent vs. expiring lease rent for the same unit type, expressed in $ and %

### Commercial rent roll cuts

- By tenant — name, SF, rent, $/SF, expiration, options, escalations, free rent burn-off
- By industry (office, retail) — concentration risk
- Top 10 tenants exhibit
- Sublease exposure (office) — what % of tenant space is being subleased; signals downsizing

## T-12 / Operating Statement variance analysis

A T-12 is the trailing 12 months of operating activity. Variance analysis compares it to a baseline (UW, budget, prior period, or NTM forecast).

### Variance table format

```
                            UW         Actual T-12    Variance     % Var
─────────────────────────────────────────────────────────────────────────
REVENUE
  Gross Potential Rent     $X,XXX     $X,XXX         $XXX         X.X%
  Vacancy & Concessions   ($XXX)     ($XXX)         ($XX)        X.X%
  Bad Debt                ($XX)      ($XX)          ($X)         X.X%
  Other Income             $XXX       $XXX           $XX          X.X%
  Effective Gross Income   $X,XXX     $X,XXX         $XXX         X.X%

EXPENSES
  Property Tax             $XXX       $XXX           $XX          X.X%
  Insurance                $XXX       $XXX           $XX          X.X%
  Utilities                $XXX       $XXX           $XX          X.X%
  R&M                      $XXX       $XXX           $XX          X.X%
  Payroll                  $XXX       $XXX           $XX          X.X%
  Management Fee           $XXX       $XXX           $XX          X.X%
  G&A / Other              $XXX       $XXX           $XX          X.X%
  Total OpEx              $X,XXX     $X,XXX         $XXX         X.X%
  Expense Ratio            XX.X%      XX.X%          X.X pp

NOI                        $X,XXX     $X,XXX         $XXX         X.X%
NOI Margin                 XX.X%      XX.X%          X.X pp
```

Sign convention: variance is *favorable* to NOI = positive. A revenue overage is positive variance; an expense overage is negative variance. State the convention.

### Reading expense lines

Things to look for and call out:

- **Property tax**: post-acquisition reassessment can hit 1-2 years after closing. Major variance source. Check appeal status.
- **Insurance**: hard market 2022-2024 saw 30-100% renewals on coastal/CAT-exposed assets. Compare $/unit or $/SF.
- **Utilities**: ratio of utility expense to gross is a quick check for over/underbilling tenants (commercial NNN).
- **R&M**: one-time vs. recurring. A bad quarter with a roof repair is not the trend.
- **Payroll**: changes in headcount or wages, or move between in-house vs. third-party.
- **Management fee**: usually 2-4% of EGI. Should track EGI proportionally — if it doesn't, ask why.

### Reading revenue lines

- **GPR vs. in-place rent × 12**: should reconcile. If they don't, there's a mid-period rent change or a unit count change.
- **Concessions**: typically capitalized over the lease term in GAAP but expensed monthly in cash. Specify which view.
- **Bad debt**: trending up is a leading indicator. Compare to prior periods, not just UW.
- **Other income**: parking, fees, RUBS (multifamily), antenna licenses, storage. Often understated in UW.

## NOI bridges — the asset manager's most important exhibit

A bridge walks from one NOI value to another by isolating each driver. Use bridges anywhere two NOI figures need to be reconciled: UW vs. actual, budget vs. forecast, prior year vs. current year.

### Bridge construction rules

1. **One driver per line.** Don't combine revenue and expense impacts on a single line.
2. **Quantify each line in dollars.** Percentages obscure size.
3. **Total bridges to zero.** If your bridge doesn't reconcile, you've missed a driver. Add a "Plug / Other" line at most a few percent of NOI — anything bigger needs investigation.
4. **Order by size of driver, descending.** Biggest impacts first.
5. **Label each driver with its root cause**, not just its line item. "Property tax: +$200k from successful 2024 appeal" beats "Property tax: +$200k."

### Example: Actual vs. UW NOI bridge

```
UW NOI                                                   $4,200,000
  − Rent ramp shortfall (occupancy below UW curve)         (380,000)
  − Concessions higher than UW (3 mo free vs. 1 mo)        (150,000)
  + Other income outperformance (parking, RUBS)              90,000
  − Property tax (post-close reassessment, no appeal yet)  (220,000)
  − Insurance renewal (CAT-exposed, +60% premium)          (140,000)
  + R&M favorable (capex deferred to next year)              80,000
  + Payroll favorable (eliminated one FTE)                   60,000
  + Other / rounding                                         20,000
Actual T-12 NOI                                          $3,560,000
Variance to UW                                          −$640,000 (−15.2%)
```

## Operating ratios — quick diagnostic checks

| Ratio | Healthy range (varies by class) | Signals if outside |
|---|---|---|
| OpEx / EGI | 35-50% (multifamily, suburban office), 25-40% (industrial) | Hidden costs or property tax surge |
| Mgmt fee / EGI | 2-4% | Negotiate or check tier breaks |
| R&M / unit (MF) | $400-$900/unit/yr | Deferred maintenance or one-time event |
| Insurance / unit (MF) | $300-$1,200/unit/yr | Hard market exposure, CAT zone |
| Property tax / value | 1-3% (varies state by state, brutal in TX/NY/IL) | Reassessment risk |

These are heuristics, not standards. Cite local comps where available.

## Common pitfalls

- **Annualizing T-3 or T-6 numbers as if they were T-12.** Seasonal businesses (hospitality, retail) make this misleading. Show both.
- **Comparing cash to accrual T-12s.** Many GLs are cash; UWs are accrual. Reconcile bad-debt and prepaid items.
- **Ignoring one-time items.** Insurance proceeds, real estate tax refunds, broken lease fees can inflate a single year. Normalize.
- **Treating leased occupancy as economic occupancy.** A 95% leased property running 12 months of free rent has near-zero economic occupancy.
