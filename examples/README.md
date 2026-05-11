# Examples

A fully synthetic walkthrough showing what the skill produces. All numbers, tenants, and property details are fabricated.

## `sample-multifamily/`

A 24-unit garden multifamily property, acquired April 2023, now mid-Year 2 of a 5-year hold. Performance is **soft against UW** — exactly the situation an asset manager actually has to write about.

### Files

| File | What it is |
|---|---|
| `rent_roll.csv` | Unit-level rent roll as of 31 Mar 2026 (24 units) |
| `t12.csv` | Trailing 12-month operating statement (Apr 2025 – Mar 2026) |
| `uw_baseline.md` | Original underwriting assumptions to compare actuals against |

### What to ask Claude

Open Claude Code in this folder and try any of these:

**1. Performance triage**
> "Read the rent roll and T-12. How is this asset doing vs. the UW in uw_baseline.md?"

Expected output: a 1-paragraph executive summary leading with the punchline, an NOI bridge (UW → Actual broken into revenue/expense drivers), occupancy and WALT from the rent roll, and 2-3 specific action items.

**2. Rent roll deep-dive**
> "Build a rent roll analysis — occupancy, loss-to-lease, expiration ladder, and rent-to-market gap by unit type. Output as a styled Excel file."

Expected output: an Excel workbook with FAST-style color coding (blue inputs, black formulas, navy headers, parenthetical negatives), tabs for summary / by-unit / expiration ladder, and a clear LTL number that quantifies the upside from marking units to market.

**3. NOI variance memo**
> "Write a 1-page IC memo: actual NOI vs. UW for the T-12, with a bridge, drivers, and a recommendation on what to do about it. Use the modern theme."

Expected output: a Word memo with a navy header, action-title sections, an inline variance table, and a "Recommendation" section that quantifies the ask (e.g., "approve $X in deferred capex to reset Y units, projected $Z NOI lift").

**4. Hold/sell test**
> "Run a hold-vs-sell analysis. Use a market exit cap of 5.75% (50bps wider than UW) and compare to holding 3 more years assuming 3% rent growth and stabilized expenses."

Expected output: incremental IRR of holding, breakeven cap rate, sensitivity table, recommendation with the math behind it.

**5. Covenant check**
> "Test DSCR and debt yield against the loan covenants in uw_baseline.md. Build a maturity ladder and flag refi risk."

Expected output: trailing DSCR and debt yield by quarter, covenant headroom in bps, and a refi readiness assessment.

### What you'll notice

- The skill **anchors every number to UW** — variance is the conversation, not the level
- Outputs lead with the **decision** (hold/sell/intervene), not narrate operations
- Excel and Word outputs are **styled to institutional conventions** — not Microsoft defaults
- The skill **flags missing inputs** rather than silently assuming
