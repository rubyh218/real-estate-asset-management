# Valuation

This reference covers the three standard valuation approaches used in real estate asset management: direct capitalization, discounted cash flow, and sales comparison. Most institutional asset managers use a triangulation of all three.

## Choosing the basis of NOI

Before you cap anything, decide what NOI you're capping. The asset manager's choices, in order of conservatism:

| NOI basis | What it captures | When to use |
|---|---|---|
| **T-12 actual** | What the property earned | Conservative; stable, fully leased assets |
| **NTM forecast** | Next 12 months expected | Most common for institutional mark; rolls forward from T-12 with known changes |
| **Stabilized** | NOI at full lease-up / completed business plan | Value-add / development; for "stabilized value" exhibits |
| **Forward / "look-through"** | Year 2 or Year 3 projected | Aggressive; use only when business plan execution is highly visible |

State the basis explicitly: "$12.5M ÷ 5.5% cap on Year 1 NTM NOI of $688k."

## Direct capitalization

```
Value = NOI ÷ Cap rate
```

Simple but the entire exercise is choosing the right cap rate. Sources, in order of reliability:

1. **Recent transactions for comparable assets in the submarket** (last 6-12 months). Strongest evidence.
2. **Broker BOVs** (Brokers' Opinions of Value). Useful but inherently sale-pitch biased; discount slightly.
3. **Capital markets surveys** (CBRE, JLL, RCA/MSCI cap rate reports). Good for benchmarking direction and spreads, weaker for absolute pricing.
4. **Spread to risk-free**: historical cap rate spread over 10Y Treasury for the asset class can sanity-check an absolute level.

### Adjusting comps

No comp is a perfect match. Standard adjustments:

- **Quality / vintage**: newer & higher-quality assets trade tighter
- **Location**: trophy submarket vs. tertiary
- **Lease term / WALT**: longer WALT = lower cap (more bond-like)
- **Tenant credit**: investment-grade tenants compress the cap
- **Size**: large assets often trade tighter (institutional liquidity); very large can be illiquidity-discounted

Document each adjustment in basis points: "Subject is older vintage than Comp 1, +25 bps; smaller deal size, +10 bps; weaker submarket, +15 bps. Adjusted cap: Comp 1 5.25% → 5.75%."

## Discounted Cash Flow (DCF)

Standard institutional DCF for real estate:

- **Hold period**: 10 years is the convention. Sometimes 5-7 for value-add.
- **Cash flow each year**: NOI − capex − leasing costs (TIs, LCs, free rent)
- **Reversion / Terminal value**: Year-11 NOI ÷ Exit cap rate, less selling costs (typically 1-2%)
- **Discount rate**: levered or unlevered IRR target; for institutional core RE, often 6.5-9% unlevered, 10-13% levered. Depends entirely on asset class, risk profile, and capital cost.

### Standard DCF exhibit structure

```
                Year 1   Year 2   Year 3   ...   Year 10   Year 11 (terminal)
─────────────────────────────────────────────────────────────────────────────
NOI            $XXX,XXX  $XXX     $XXX     ...    $XXX      $XXX
− Capex        ($XX)
− TI/LC        ($XX)
+ Reversion                                                  $X,XXX
Cash flow      $XXX     $XXX     $XXX     ...    $XXX      $X,XXX
Discount       0.93    0.86     0.79     ...    0.49       0.46
PV             $XXX     $XXX     $XXX     ...    $XXX      $X,XXX

Sum of PV cash flows = Value
```

### Setting the exit cap

The exit cap is usually set 25-100 bps wider than the going-in cap to reflect the property being older at exit. Set it based on:

- Going-in cap + age premium (25-50 bps for a 10-yr hold of a stable asset)
- Comparable terminal caps in current market surveys
- Sensitivity: report value at exit cap −25/+25/+50 bps; this is the single biggest swing factor

### Common DCF mistakes

- **Exit cap too tight.** Aggressive exit caps fabricate value. Sensitivity-test.
- **Forgetting leasing costs.** In office and retail, TIs and LCs can be 5-15% of revenue. UWs that omit these overstate cash NOI.
- **Confusing levered and unlevered discount rates.** Match the cash flow stream (post-debt or pre-debt) to the corresponding discount rate. Mixing is a common error.
- **Inflation assumptions on rent vs. expenses.** Expenses often inflate faster than rent (especially when leases are fixed-step). Don't blanket-inflate both at 3%.

## Sales comparison

Per-unit or per-SF prices from comparable sales, adjusted. Useful as a cross-check on cap-rate-based value, and required by most appraisal standards.

```
COMP TABLE
─────────────────────────────────────────────────────────────────────────────
Comp        Date     Submkt   Size      $/Unit  Cap Rate  Adjustments    Adj $/Unit
Comp 1      Q2-25    [Sub]    280 unit  $315k   5.25%     −5% (older)    $299k
Comp 2      Q4-25    [Sub]    180 unit  $340k   5.10%     −10% (smaller)  $306k
Comp 3      Q1-26    [Adj]    320 unit  $295k   5.40%     +5% (better sub) $310k
─────────────────────────────────────────────────────────────────────────────
Average adjusted $/unit:                                                  $305k
Subject: 250 units → indicated value: $76.3M
```

## Triangulation

Most institutional marks combine the approaches:

```
APPROACH                  INDICATED VALUE      WEIGHT     WEIGHTED
─────────────────────────────────────────────────────────────────
Direct Cap (NTM)          $77.5M               40%        $31.0M
DCF                       $74.8M               40%        $29.9M
Sales Comparison          $76.3M               20%        $15.3M
─────────────────────────────────────────────────────────────────
Concluded value                                           $76.2M
```

Weighting reflects confidence — give less weight to approaches with thin data (e.g., low-comp submarkets).

## What asset managers actually need

In practice, a quarterly mark is usually:

1. Direct cap on NTM NOI as the primary
2. A DCF for assets being held longer or with capex cycles in flight
3. Comp set for cross-check

Don't run a full 10-year DCF every quarter unless the asset's value-add story makes it material. Build it once at acquisition, update key assumptions quarterly, and re-run at sale.

## Reporting the value

State, at minimum:

- Value ($M and $/unit or $/SF)
- Implied cap rate on T-12 and NTM NOI
- vs. acquisition basis
- vs. prior mark
- vs. UW value at this point in time
- Key assumptions (cap rate / discount rate / exit cap / growth)
- Confidence level (low / moderate / high) — and why
