# Quarterly Asset Review (QAR)

The QAR is the asset manager's primary recurring deliverable. It documents how the asset is performing against the business plan, what's changed, what's at risk, and what action is recommended.

## Standard QAR structure

Follow this structure unless the user has a firm-specific template (in which case adopt theirs). The order matters — decisions go at the top, supporting analysis below.

```
1. Executive summary           (5-10 lines, decision-ready)
2. Recommendation & action items
3. Financial performance       (NOI vs. UW/budget, with bridge)
4. Operations                  (leasing, occupancy, capex, asset condition)
5. Market update               (submarket trends affecting this asset)
6. Valuation update            (current value, vs. basis, vs. UW exit)
7. Debt status                 (covenants, maturity, hedge if any)
8. Risks & issues
9. Appendix                    (rent roll summary, comp set, financials)
```

## Executive summary template

```
PROPERTY: [Name], [City, State]
ASSET CLASS: [Multifamily / Office / etc.]
ACQUISITION: [Date] | BASIS: $[XX]M ($[XXX]/unit or $[XX]/SF)
CURRENT VALUE (Q[X] [YYYY]): $[XX]M ([X.X]% cap on T-12 NOI)
UNREALIZED RETURN: [X.X]x MOIC, [XX]% IRR

PERFORMANCE vs. UW:        [On track / Outperforming / Underperforming]
NOI Q[X] YTD:              $[X.XX]M (UW: $[X.XX]M, variance: [+/-X.X]%)
Occupancy:                 [XX.X]% (UW: [XX.X]%)

RECOMMENDATION: [Hold / Sell / Refi / Recapitalize / Reforecast]
RATIONALE: [One sentence.]
```

## NOI bridge — the core analytical exhibit

A bridge explains *why* NOI moved between two points (UW vs. actual, or prior period vs. current). Present in this format:

```
NOI Bridge: UW → Actual T-12

UW NOI                                          $X,XXX,XXX
  + / − Rental revenue variance                   $XXX,XXX    (in-place vs. UW; mark-to-market gap)
  + / − Occupancy variance                        $XXX,XXX    (actual vs. UW occupancy × in-place rent)
  + / − Other income (parking, fees, etc.)        $XXX,XXX
  + / − Bad debt / concessions                    $XXX,XXX
  + / − Property tax                              $XXX,XXX    (reassessment, appeals)
  + / − Insurance                                 $XXX,XXX    (renewal, hard market)
  + / − R&M / Utilities / Mgmt fee                $XXX,XXX
  + / − Other opex                                $XXX,XXX
Actual T-12 NOI                                 $X,XXX,XXX
```

Each line should be at most one root cause. If a single line has multiple drivers, break it out. The goal is that a reader can ask "why is NOI off?" and the bridge answers it line by line.

## Operations section

Cover these topics, briefly:

- **Leasing activity**: new leases signed, renewals, retention rate, average new lease rate vs. expiring rate (spreads), free rent / TI given
- **Occupancy**: physical, leased, economic (the three are different — economic occupancy = collected rent / GPR, captures concessions and bad debt)
- **Capex**: spent YTD vs. budget, what's been completed vs. in flight
- **Asset condition**: any deferred maintenance, capital events, casualty losses
- **Property management**: who runs it, any changes, KPIs

## Valuation update

State the methodology used and the key inputs:

- **Direct cap**: Cap rate applied (cite source — recent comps, broker BOV, internal mark) × NOI basis (T-12, NTM, stabilized)
- **DCF**: Discount rate, hold period, exit cap, growth assumptions
- **Mark to comps**: List 3-5 recent comps with $/unit or $/SF, date, cap rate, size, quality adjustment

Show value vs. (a) UW projected value at this point in time, (b) acquisition basis, (c) prior quarter's mark.

## Recommendation framing

The recommendation should be one of:

- **Hold per business plan** — execution is on track
- **Hold but reforecast** — assumptions need updating; flag what changed
- **Sell now** — incremental IRR of holding doesn't justify the marginal capital
- **Refinance** — return capital to LPs while retaining upside
- **Recapitalize** — bring in fresh equity (often at a discount); usually defensive
- **Inject capital / capex** — value-add opportunity that wasn't in UW
- **Workout / restructure** — distressed; lender or LP conversation needed

For sell/hold/refi specifically, see `disposition-analysis.md`.

## Common QAR pitfalls

- **Telling the story of operations instead of returns.** Operations matter, but LPs invested in returns. Translate operating events into return impact.
- **Burying bad news.** Asset managers who hide problems lose credibility faster than asset managers who underperform. Surface issues in the executive summary.
- **Comparing to last quarter instead of UW.** Trend matters, but the contract with LPs is the UW. Always anchor there.
- **No quantified recommendation.** "We should consider selling" is not a recommendation. "Sell at $XXM ([X.X]% cap) generates an incremental 8% IRR vs. holding 18 more months" is.
