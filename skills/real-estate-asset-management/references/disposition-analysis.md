# Disposition Analysis (Hold / Sell / Refi)

The disposition decision is one of the most consequential calls the asset manager makes. The right framework: **the LP's capital has alternative uses.** Holding an asset that earns 8% incremental when the same capital could earn 15% elsewhere destroys value, even if the asset is performing well.

## The decision framework

Compare three scenarios on a like-for-like basis:

1. **Sell now**: realize current value, return proceeds to LPs.
2. **Hold to projected exit**: continue executing the business plan to the original exit date.
3. **Refinance and hold**: pull capital out via refi, redeploy or distribute, hold residual equity.

The output is an **incremental IRR** for each "extend" decision (hold vs. sell, refi-and-hold vs. sell). If the incremental IRR exceeds the LP's cost of capital (or the GP's expected return on alternative deployments), hold. Otherwise, sell.

## Incremental ("stub") IRR

The key insight: returns already earned are sunk. The decision turns on the *go-forward* return on capital that would otherwise be returned today.

```
Stub IRR = IRR of cash flows from TODAY forward only, treating today's
           equity value as the Time-0 outflow

         t=0:     ($X)  ← current equity value (what LPs would get if sold today)
         t=1..n:  +CF   ← projected operating distributions through hold
         t=n:     +$Y   ← projected sale proceeds at extended exit
```

Compute the IRR of this stream. That's the incremental return for holding. Compare it to:

- LP cost of capital (typically 10-15% for value-add equity)
- Alternative deployment opportunities (GP's pipeline)
- Risk-adjusted hurdle (apply premium for execution risk on the remaining business plan)

### Example: Sell now or hold 18 more months

```
SELL NOW:
  Current value:                        $75.0M
  Less: debt payoff                    ($45.0M)
  Less: closing costs (2%)              ($1.5M)
  Net proceeds to equity:                $28.5M

HOLD 18 MONTHS (stub IRR):
  Time 0 (forgo sale):                 ($28.5M)
  Operating distributions (Q1-Q6):       $1.2M / quarter ≈ $7.2M total
  Sale at month 18:
    Projected value (NOI growth):       $83.0M
    Less: debt payoff:                 ($43.5M)
    Less: closing costs (2%):           ($1.7M)
    Net at sale:                        $37.8M
  ─────────────────────────────────────────────
  Stub IRR over 18 months:               ~28%
  Required hurdle:                       18%
  ─────────────────────────────────────────────
  RECOMMENDATION: HOLD (clears hurdle by ~10 pp)
```

## When to sell

Strong signals that sale beats hold:

- **Stub IRR < cost of capital** — incremental return doesn't justify the risk
- **Pricing is anomalously strong** — market is paying for growth that isn't in the asset's pro forma; you're being offered NPV of your future business plan today
- **Business plan complete** — value-add execution finished; remaining returns are largely market-driven and not differentiated by your operating skill
- **Concentrated tail risk** — single-tenant rolls, refi exposure, capex cliff — selling derisks the position
- **GP pipeline competing** — better risk-adjusted opportunities to redeploy

## When to hold

Signals that holding beats sale:

- **Material business plan execution still ahead** — lease-up, mark-to-market, repositioning, development completion
- **Disrupted markets** — selling into a bid-light environment destroys value; "be a marginal seller in good markets"
- **Tax considerations** — bonus depreciation recapture, 1031 limitations, partnership-level tax events; sometimes hold for tax timing
- **LP composition** — if LPs are long-duration capital (pension, sovereign) and the asset is performing, the hurdle to sell may be higher

## When to refinance

Refi is a partial liquidity event without a sale:

- Return capital to LPs (improves DPI, reduces equity at risk)
- Retain upside in the asset
- Reset debt terms (better rate, longer term, more IO)
- Avoid sale costs (transfer tax, closing costs ~3-5% of value)

Costs of refi: prepayment penalty on existing loan, new closing costs, possible loss of low-rate debt (in a higher-rate environment, refi can be NPV-negative even if it returns capital).

Run the **refi vs. sale vs. hold** triple comparison when value-add is mostly complete but the GP wants to retain optionality.

## BOV / Marketing

When proceeding to sale, the asset manager initiates a Broker's Opinion of Value (BOV) and broker selection:

1. **Solicit BOVs** from 3-5 brokers covering the submarket and product type. Compare ranges and underwriting assumptions.
2. **Select broker** based on relevant comps, buyer relationships, and proposed marketing strategy.
3. **Execute listing agreement** (negotiate fee, exclusivity, term).
4. **Marketing process**: OM (Offering Memorandum), data room, buyer tours, call for offers, best-and-final, LOI, PSA.

The asset manager owns the underwriting in the OM and the answers to buyer diligence questions. Bad underwriting = retrade.

## Sale memo to IC

When recommending sale, the memo typically covers:

```
1. Recommendation & Pricing
   - Recommended sale ($XX.XM, X.X% cap, $XXX/unit)
   - Net proceeds to fund, gross/net deal IRR & MOIC
   - Timing: list date, expected close

2. Rationale
   - Stub IRR vs. hold
   - Market conditions
   - Business plan status
   - Tax / fund considerations

3. Process
   - Broker recommendation
   - Marketing strategy
   - Expected buyer universe
   - Process timeline

4. Pricing detail
   - BOV ranges, key comps
   - Cap rate sensitivity
   - Bid expectations

5. Risks & Mitigants
   - Diligence risks
   - Market risks
   - Retrade exposure
```

## Common pitfalls

- **Anchoring on cost basis.** "We can't sell below basis" is a sunk-cost trap. The right question is forward returns.
- **Holding for the LP report.** Marking an asset doesn't realize the gain — selling does. DPI matters more than TVPI long-term.
- **Optimistic hold underwriting.** When comparing hold to sell, the hold case is often built by the same people who want to keep managing the asset. Stress-test rent growth, exit cap, capex.
- **Ignoring tax friction.** Sale triggers depreciation recapture and capital gains; this is borne by LPs, not the fund. A pure pre-tax IRR comparison misses this.
- **Underestimating execution time.** A sale process is typically 4-6 months from BOV to close, sometimes longer. Don't promise IRR-by-date without sale process time.
