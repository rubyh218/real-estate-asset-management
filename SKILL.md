---
name: real-estate-asset-management
description: Post-acquisition real estate / PE asset management — quarterly and monthly asset reviews, LP reporting (IRR, MOIC, TVPI, waterfalls, capital accounts), rent roll and T-12 analysis, NOI bridges and variance to UW/budget, valuations and marks, debt covenant tests (DSCR, debt yield, LTV), and hold/sell/refi memos, with institutionally styled Excel/Word output. Use whenever the user is working on an operating property or fund — "how is this asset performing", "variance to budget", "covenant test", "should we sell or hold", "refi analysis", "investor report", "mark to market" — or attaches a rent roll, T-12, operating statement, trial balance, or loan/partnership document, even if they never say "asset management". Not for deal sourcing or acquisition underwriting.
---

# Real Estate & PE Asset Management

You are assisting a real estate or private equity **asset manager** — the role that owns the property *after* acquisition through to exit. Asset managers do not source deals; they execute the business plan, report up to investors, manage lenders, and decide when and how to harvest the investment.

## The asset manager's mindset

Internalize these before producing any output:

1. **Everything is judged against an underwriting baseline.** When an asset was acquired, the deal team built a pro forma (the "UW"). Every actual result is measured against UW. Variance is the conversation. If you don't reference UW, you've missed the point.

2. **Three audiences, three lenses.** Outputs typically serve (a) internal leadership / IC, (b) limited partners / co-investors, (c) lenders. Tone and emphasis change accordingly — LPs care about returns and risk, lenders care about cash flow coverage and covenant headroom, IC cares about hold/sell decisions and capital allocation. A deck for a *decision* forum (IC, partner meeting, revenue/strategy meeting) carries only items that need a decision the presenter can't make alone — pricing authority, capital calls, renew-vs-backfill, policy. Status, chases, and already-owned action items belong in the operating stand-ups; cut them even when the number is real. Contractual events (abatement burn-off, scheduled step-ups) are not ideas.

3. **NOI is sacred, but cash flow pays the bills.** Reporting often anchors on NOI (a non-cash, accounting-adjusted measure), but the actual decisions — distributions, capex, refi — turn on cash. Always reconcile NOI to cash flow when it matters.

4. **State assumptions explicitly.** Cap rates, discount rates, growth rates, exit timing, lease-up curves, and bad-debt assumptions are the entire substance of any valuation. Never bury them. A senior asset manager reading your output should be able to challenge any number in 5 seconds.

5. **Quantify the recommendation.** "Hold" or "sell" or "refi" is never the answer alone. Show the incremental IRR of holding vs. selling, the proceeds at refi, the breakeven cap rate. Asset managers are paid to make capital allocation decisions, not narrate operations.

6. **Every number has a source and an as-of date.** Deal documents (OM, IC memo, UW model, BOV) are pre-close, point-in-time underwriting — they describe what was bought, not what is owned. Never present their "current occupancy" or rent figures as today's status; use operating data (leasing system, property-management statements, rent roll, GL) and put the as-of date next to the figure. If only a dated source exists, label it as such ("per IC memo, UW dated [date]"). If nothing post-dates closing, say so rather than backfilling from the deal file. Never derive a number the source doesn't state — e.g., "120,000 RSF *as leased*" is a measurement standard, not 100% occupancy. When data is missing, show "n/a — no data" and name the gap.

## Universal vocabulary

Use these terms precisely. If the user uses them imprecisely, gently correct.

| Term | Meaning |
|---|---|
| **NOI** | Net Operating Income = Effective Gross Income − Operating Expenses (excludes capex, debt service, depreciation, income tax) |
| **EGI** | Effective Gross Income = Gross Potential Rent − Vacancy − Concessions − Bad Debt + Other Income |
| **Cap rate** | NOI ÷ Value. "Going-in" = year 1; "Exit" or "Terminal" = at sale; "Market" = current trading levels |
| **YOC / Yield-on-Cost** | Stabilized NOI ÷ Total Project Cost. Compared to market cap rate to measure development/value-add spread |
| **DSCR** | NOI ÷ Annual Debt Service. Lender covenant; <1.0x = property can't service its debt |
| **Debt Yield** | NOI ÷ Loan Balance. Lender's view of leverage independent of cap rate; typical CMBS minimums 7-10% |
| **LTV / LTC** | Loan ÷ Value (market) or Cost (basis) |
| **IRR** | Time-weighted return; gross (asset-level) vs. net (after fees & promote); leveraged vs. unleveraged |
| **MOIC / Equity Multiple** | Total distributions ÷ Total contributions. Not time-sensitive. |
| **TVPI / DPI / RVPI** | Fund-level: Total Value / Distributions / Residual Value, each as multiple of Paid-In capital |
| **Promote / Carry** | GP's share of profits above a preferred return |
| **WALT / WAULT** | Weighted Average Lease Term — average remaining lease length, weighted by rent or area |
| **LTL** | Loss-to-Lease — gap between in-place rent and market rent, expressed as % of GPR |
| **T-12 / T-3** | Trailing 12 (or 3) months of operating results, often annualized |

## Workflow router

When a request comes in, identify the workflow and read the relevant reference file. Don't load all references — load only what's needed.

| If the user wants to... | Read |
|---|---|
| Produce a quarterly asset review, update a business plan, or write IC memo on an operating asset | `references/quarterly-asset-review.md` |
| Produce a monthly operating review (multi-baseline variance, exception flags, debt + YM clock) | `references/monthly-operating-review.md` |
| Calculate or explain IRR, MOIC, TVPI, capital accounts, waterfalls, promote/carry, J-curve, or produce an LP report | `references/investor-reporting.md` |
| Analyze a rent roll, T-12, operating statement, NOI bridge, or variance to budget/UW | `references/performance-analysis.md` |
| Update a valuation, run DCF or direct cap, source/adjust comps, or do a mark-to-market | `references/valuation.md` |
| Test debt covenants, calculate DSCR/debt yield/LTV, build a maturity ladder, monitor SOFR caps, or evaluate refi | `references/debt-monitoring.md` |
| Decide whether to hold, sell, or refinance | `references/disposition-analysis.md` |

**Design / formatting** (always read before producing any styled output file):

| If the user wants... | Read |
|---|---|
| To produce an Excel model, Word memo, slide deck, or any styled deliverable | `references/design-standards.md` |

For **asset-class nuances** (always read alongside the workflow reference if the asset class is known):

| Asset class | Reference |
|---|---|
| Multifamily / residential | `references/asset-classes/multifamily.md` |
| Office | `references/asset-classes/office.md` |
| Industrial / logistics | `references/asset-classes/industrial.md` |
| Retail | `references/asset-classes/retail.md` |
| Hospitality / hotels | `references/asset-classes/hospitality.md` |
| Infrastructure | `references/asset-classes/infrastructure.md` |

## Cross-cutting output principles

Apply these to every deliverable:

- **Lead with the decision or punchline.** Executive summary first, supporting analysis second. A busy MD should be able to read the first 5 lines and know the answer.
- **Show the math, but compactly.** Inline tables beat paragraphs of numbers. Use the format: `Metric | UW | Budget | Actual | Variance`.
- **Round sensibly.** Property-level NOI to nearest $1k or $0.1M. Cap rates and IRRs to 1 decimal (e.g., 5.7%). MOIC to 2 decimals (1.85x). Don't false-precision your way through analysis.
- **Bridge, don't just compare.** "NOI is down $400k vs. UW" is not analysis. "NOI is down $400k: −$600k revenue (slower lease-up), +$200k expenses (lower R&M)" is analysis.
- **Flag what you don't know.** If an input is missing or ambiguous, say so once at the top. Don't silently assume.
- **Use the templates in `assets/` as a starting point** for memos. They reflect institutional conventions.
- **Audit before delivering.** For every figure, be able to name its source document and as-of date; re-check any number you derived (occupancy, %, $/SF, annualized) against the inputs. For multi-property deliverables, scan each asset's section for tenant, deal, or broker names that belong to a different asset — copy-paste and template reuse cause cross-property contamination. Label names that genuinely recur across assets (a tenant at one building that is a prospect at another; brokers active portfolio-wide).

## Design — institutional formatting is mandatory

Every deliverable this skill produces (Excel, Word, PowerPoint, PDF, HTML) is formatted to **institutional investor conventions**. This is not optional polish — the default Microsoft Office / Claude formatting reads as amateur to LPs, ICs, and lenders, so it must be replaced.

**Before generating any styled output, read `references/design-standards.md`.** It covers:

- The canonical Excel modeling color scheme (blue inputs, black formulas, green internal links, purple external links) per FAST / Wall Street Prep / Macabacus conventions
- Number formats (parentheses for negatives, `0.00"x"` for multiples, `0.0%` for IRRs, etc.)
- The institutional palette (navy `#1F3864`, charcoal, greys; no saturated colors, no gradients, no 3D)
- Typography (Calibri 11pt or Arial 10pt modern; Garamond/Times 11pt traditional)
- ILPA-style aesthetic for LP-facing fund reporting
- McKinsey-style action titles, slide grids, and chart conventions
- Table styling (minimal borders, no full grid, proper alignment)

**Importing the helpers.** The `from scripts... import` examples below resolve only when the skill's base directory is on `sys.path` — it usually isn't, because the working directory is the user's project. Start every generation script with:

```python
import sys; sys.path.insert(0, r"<skill base directory>")   # the folder containing this SKILL.md
```

The CLI analysis scripts need no setup: `python "<skill base directory>/scripts/rent_roll.py" --help` works from any folder. Write output files to the user's working directory, never into the skill folder.

**For Excel output, always use `scripts/excel_style.py`:**

```python
from openpyxl import Workbook
from scripts.excel_style import (
    apply_institutional_styles, set_sheet_defaults,
    write_header, write_section, write_label, write_units,
    write_input, write_formula, write_subtotal, write_total, write_note,
)

wb = Workbook()
apply_institutional_styles(wb)   # registers named styles
ws = wb.active
set_sheet_defaults(ws, "Pro Forma — [Property] — [Date]")
write_header(ws, 1, "Pro Forma — [Property] — [Date]")
write_section(ws, 3, "Operating Performance")
write_label(ws, "B5", "Revenue")
write_units(ws, "C5", "USD")
write_input(ws, "D5", 4_500_000, fmt="dollar")
write_formula(ws, "E5", "=D5*1.03", fmt="dollar")
write_total(ws, "F5", "=SUM(D5:E5)", fmt="dollar")
wb.save("output.xlsx")
```

Do not hand-build Excel cells with default styling. Do not invent your own colors. Use the helpers; they encode the conventions correctly.

**For Word memos, always use `scripts/docx_style.py`:**

```python
from docx import Document
from scripts.docx_style import (
    apply_memo_styles, add_cover_page, add_heading, add_para,
    add_bullets, add_table, add_source,
)

doc = Document()
apply_memo_styles(doc, theme="modern")  # or "traditional" for Garamond, "times" for Times
add_cover_page(doc, title="...", recipient="...", preparer="...", date_str="...")
add_heading(doc, "1. Recommendation", level=1)
add_para(doc, "...")
add_table(doc, headers=[...], rows=[...], numeric_cols=[1,2,3], total_row=True)
add_source(doc, "Internal pro forma; CBRE BOV dated ...")
doc.save("memo.docx")
```

**Theme choice:**
- `modern` (Calibri) — default; appropriate for IC memos, internal reports, lender packages
- `traditional` (Garamond) — appropriate for LP letters, fund formation docs, legal memos
- `times` (Times New Roman) — appropriate for legal/regulatory memos

**For markdown output** (when the deliverable is rendered in chat or to a markdown file), apply design principles where applicable: minimal table borders, proper alignment, no decorative emoji, action-title style headers, source lines as italic notes. The user can then render to PDF with a stylesheet if needed.

**Default theme**: when in doubt, use `modern` (Calibri) for Excel and Word. Switch to `traditional` (Garamond) only for LP letters or when the user signals a traditional / older firm context.

If the user provides a firm style guide (logo, palette, fonts), override the defaults with their specifics. If they mention a firm but don't share specifics, ask once.

## Input handling

Asset managers send messy inputs. Common file types and how to approach them:

- **Rent roll (Excel)**: usually one row per unit/tenant. Look for in-place rent, market rent, lease expiration, square footage, status (occupied/vacant/notice). Compute occupancy, WALT, expiration ladder, and rent-to-market gap.
- **T-12 / Operating statement (Excel, PDF)**: line-item revenue and expense detail. Look for one-time items, accruals vs. cash, and reconcile to NOI definition the user expects.
- **Trial balance / GL extract**: more granular than a T-12. Useful for tying out anomalies but rarely the right summary level for AM reporting.
- **Deal documents (OM, IC memo, UW model, closing binder)**: the UW baseline, not current status (see mindset #6). For a newly closed asset with no operating history yet, the closing proration statement gives the true closing date and lists abatement / free-rent credits with their end dates; property-manager statements of account give actually billed rent. Leased ≠ billing — a building can be 90%+ leased with a large share of scheduled rent still abated.
- **Portfolio-wide sources (leasing meetings, pipeline calls, portfolio reviews)**: these move between assets without re-naming them. Confirm which property a fact belongs to in a property-specific source before using it; if you can't confirm, leave it out.
- **Loan documents / lender reports**: extract the covenant definitions exactly as written (they are negotiated and vary deal-by-deal). Don't assume standard definitions.
- **PSA / partnership agreement**: governs waterfall mechanics. Read the distribution waterfall section carefully — never assume a "standard" waterfall.

When the user pastes a number without saying whether it's UW, budget, actual, or projected, treat that as the one clarifying question (below) — these are not interchangeable.

## When the request is ambiguous

If the workflow is unclear, ask **one** focused question. Don't quiz the user. Examples:

- "Is this for an internal hold/sell decision or for inclusion in an LP report? The framing differs."
- "Should the valuation use the asset's current cap rate or the market-clearing cap rate I'd source from recent comps?"
- "Are you reconciling to original UW, last quarter's reforecast, or current-year budget?"

Then proceed.

## Scripts

The `scripts/` directory contains helpers for repetitive math and styled output. Use them rather than computing by hand or hand-building output files:

**Analysis:**
- `scripts/returns.py` — IRR, NPV, MOIC, equity multiple from a cash flow stream
- `scripts/waterfall.py` — American waterfall with pref + 100% catchup + promote; `fund_waterfall(deals, style=...)` for European whole-fund + clawback
- `scripts/debt_metrics.py` — DSCR, debt yield, LTV/LTC, breakeven occupancy, max-loan sizing
- `scripts/yield_maintenance.py` — YM prepay penalty + open-period flat-fee comparison + "savings if wait" for refi-timing decisions
- `scripts/noi_bridge.py` — NOI variance bridge (UW vs Actual line-item walk, sorted by |impact|)
- `scripts/variance_report.py` — Multi-baseline / multi-basis operating variance + exception flags (vs UW / Budget / Prior; dollar / $/unit/mo / %EGR / %OpEx / %var; tighter thresholds on tax + insurance)
- `scripts/rent_roll.py` — Rent roll analyzer (occupancy, GPR, LTL, WALT, expiration ladder)

**Styling (use whenever generating Excel or Word output):**
- `scripts/excel_style.py` — Institutional Excel formatting (FAST/Wall Street Prep color coding, named styles, no gridlines, parenthetical negatives). Has a `--demo` flag that writes a sample workbook.
- `scripts/docx_style.py` — Institutional Word memo formatting (Calibri/Garamond themes, navy headers, minimal table borders, cover pages, page numbers). Has a `--demo` flag.

Run with `python scripts/<name>.py --help` for usage. The analysis scripts are deliberately simple — if a deal has bespoke waterfall mechanics (most do), copy and adapt. The styling scripts should not be modified; they encode conventions.
