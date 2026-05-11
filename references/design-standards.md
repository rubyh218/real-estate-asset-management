# Institutional Design Standards

Institutional LP, IC, and lender audiences read deliverables every day. A deliverable that looks "designed" raises eyebrows; a deliverable that looks like an audit workpaper or a McKinsey deck reads as credible. This reference codifies the conventions actually used at institutional buyside firms, sell-side banks, and the standard-setters (FAST, ILPA, NCREIF/PREA).

Apply these standards to every output unless the user explicitly overrides. **Do not use default Microsoft Office formatting, do not use Claude's default colors or fonts, and do not invent decorative palettes.**

## The mindset

Institutional design is **subtractive**, not additive. The defaults you'd reach for in a marketing context — gradients, drop shadows, saturated colors, custom fonts, dense emoji, banded tables — are exactly what marks a deliverable as amateur. Restraint signals seriousness. White space is a feature.

## 1. Color palette

### The institutional palette (always in-bounds)

| Role | Hex | Notes |
|---|---|---|
| Ink (primary text) | `#222222` or `#000000` | Body, headers |
| Navy (primary accent / section headers) | `#1F3864` | The institutional default; safe everywhere |
| Deep navy (alternative) | `#002060` | Slightly stronger; common in McKinsey-style decks |
| Charcoal | `#333333` | Subtitles, captions |
| Mid grey | `#7F7F7F` | Axis labels, source lines |
| Soft grey (table band, subheaders) | `#D9D9D9` | Subheader fill |
| Paper grey (alt rows, light fills) | `#F2F2F2` | Subtle alternation only |
| Highlight yellow (input cells) | `#FFF2CC` | Soft, audit-workpaper convention |
| Flag red (error / fix-me) | `#FF0000` | Only on cells flagged for correction |
| Link green (cross-sheet references) | `#00B050` | Modeling convention only; do not use elsewhere |
| External link purple | `#800080` | Modeling convention only |

### Brand-aligned accent (one only)

Use **one** accent color, drawn from these well-known institutional palettes if the user hasn't specified a firm palette:

| Reference | Accent | Hex | Use |
|---|---|---|---|
| McKinsey-style | Vivid blue | `#005EB8` | Default highlight / one-of-many bar |
| Brookfield-style | Flush orange | `#FF8200` | Strong but used sparingly (logo lockup color) |
| KKR-style | Deep purple | `#49004B` | Sophisticated alternative |
| Burgundy / oxblood | Wine | `#7B1F2B` | Conservative non-blue option |
| Muted gold | Amber | `#C7A436` | Accent under-laid in dark deck themes |

**Never** use bright red, lime green, magenta, electric cyan, gradients, or anything implying retail/marketing aesthetics.

### Out-of-bounds (do not use)

- Saturated primaries (`#FF0000` except as a flag, `#00FF00`, `#0000FF` except as the modeling input color)
- Gradients (single-color flat fills only)
- Drop shadows, glows, beveled edges
- More than 1 accent color per chart or 3 accent colors per slide
- Office default theme colors ("Office 2007 Blue," "Aspect," etc.)
- Background images behind text
- Decorative or script fonts (Comic Sans, Brush Script, etc.)

## 2. Typography

### Body and headers

| Context | Body | Headers | Notes |
|---|---|---|---|
| Excel models | Calibri 11pt or Arial 10pt | Same, bold | One font, one size across workbook |
| Word memos (modern) | Calibri 11pt | Calibri Bold 12-14pt | Microsoft default Office aesthetic |
| Word memos (traditional) | Times New Roman 11pt or Garamond 11pt | Same, bold; or sans-serif headings on serif body | Law firms, legal memos, fund formation docs |
| PowerPoint | Arial 10-12pt body | Arial Bold 24-28pt action title (Georgia 28-32pt acceptable for serif headlines) | Sans-serif body universal |
| LP letters | Garamond 11pt or Times New Roman 11pt | Same | Traditional, serif-heavy |
| Slide source line | Arial 8-9pt italic, grey | — | Always italic |

### Hierarchy rules

- One font family per deliverable (occasional second family for headers vs. body acceptable but not required).
- Bold reserved for headers, subtotals, totals, and emphasis on a single key figure. Bolding everything = bolding nothing.
- Italics reserved for units of measure ("USD millions"), source lines, and footnotes — not for emphasis in body text.
- ALL CAPS reserved for top-level section banners or one-word "STATUS" labels (e.g., PASS / FAIL). Never set body text in all caps.

### Numbered hierarchy

Institutional memos use numbered section headers — `1.` `1.1` `1.1.1` — for cross-referenceability. Use this convention in memos. Decks use action titles only; no numbering.

## 3. Excel modeling conventions (the canonical scheme)

### Color coding by cell content

This convention — variously called the "Wall Street Prep scheme," the "Macabacus AutoColor scheme," and "banking colors" — is universal across US sell-side and PE/RE buy-side. Apply it whenever building or updating a model.

| Cell content | Font color | Hex | Fill (optional) |
|---|---|---|---|
| Hard-coded input (a number typed by the modeler) | Blue | `#0000FF` | `#FFF2CC` light yellow for editable inputs |
| Formula referencing the same sheet | Black | `#000000` | — |
| Formula linking to another sheet in the same workbook | Green | `#00B050` | — |
| Formula linking to a different workbook (external) | Purple | `#800080` | — |
| Hardcode that should be a formula ("fix me") | Bold red | `#FF0000` | `#FFFF00` yellow |
| Partial input (mixed formula + hardcode, e.g., `=B5*1.03`) | Blue | `#0000FF` | — |

This is the single most important Excel convention. A reviewer looking at any cell should know at a glance whether it's an assumption (blue, editable) or a calculation (black, derived).

### Number formats (Excel format strings)

Use these format strings exactly. Negatives are **always parentheses, never minus signs**.

| Use case | Format string |
|---|---|
| Dollar value | `#,##0;(#,##0);"-"` |
| Dollar value, scaled to thousands | `#,##0,;(#,##0,);"-"` |
| Dollar value, scaled to millions, 1 dp | `#,##0.0,,;(#,##0.0,,);"-"` |
| Currency with $ symbol | `_($* #,##0_);_($* (#,##0);_($* "-"??_);_(@_)` |
| Percentage, 1 decimal (most metrics) | `0.0%;(0.0%);"-"` |
| Percentage, 2 decimals (cap rates, yields, IRRs sometimes) | `0.00%;(0.00%);"-"` |
| Basis points | `0" bps";(0" bps");"-"` |
| Multiple (MOIC, TVPI, DPI, equity multiple, DSCR) | `0.00"x";(0.00"x");"-"` |
| Years | `0.0" yrs"` |
| Date | `mmm-yy` or `mmm-yyyy` (never `m/d/yyyy` — US-ambiguous) |
| Squared feet | `#,##0" SF"` |
| Per-unit / per-SF | `$#,##0.00"/SF"` or `$#,##0"/unit"` |
| Suppress zero in totals row | `#,##0;(#,##0);"-"` (the `"-"` after the second `;`) |

### Sheet structure (FAST-derived)

- **Column A**: blank gutter, width 2
- **Column B**: row label, width 35-45
- **Column C**: units (`USD m`, `%`, `x`, `years`), width 8-10, italic grey
- **Column D**: constants/anchor values, width 12
- **Columns E onward**: time series, uniform width 11-13

Time flows **left-to-right**. Same column structure across every sheet so any row can be summed or charted across sheets without breakage.

### Named styles to define

Configure these as `NamedStyle` objects at workbook initialization (see `scripts/excel_style.py`):

- `input_dollar`, `input_pct`, `input_multiple`, `input_date`, `input_general` — blue font, yellow fill, appropriate number format
- `formula_dollar`, `formula_pct`, `formula_multiple` — black font
- `link_internal`, `link_external` — green/purple font
- `flag_cell` — bold red font, yellow fill
- `section_header` — bold white on navy `#1F3864`, height 21
- `subheader` — bold black on grey `#D9D9D9`, height 17
- `subtotal` — bold, thin top border
- `total` — bold, thin top + double bottom border
- `units_cell` — italic grey `#595959`, right-aligned
- `date_header` — bold center, `mmm-yy` format
- `note_cell` — italic 9pt grey `#595959`

### Workbook-level settings

For every sheet:

- `sheet.sheet_view.showGridLines = False`
- `sheet.freeze_panes` at the cell below/right of the headers
- `sheet.page_setup.orientation = 'landscape'`
- `sheet.page_setup.fitToWidth = 1` ("Fit to 1 page wide")
- Margins: 0.5" L/R, 0.7" T/B
- Header/footer: file name (L), sheet name (C), page X of Y + date (R)
- Print area explicitly set
- No merged cells (banner row only, if at all)

### Header banner

Row 1 of every sheet: navy fill `#1F3864`, white text, bold, sheet title (e.g., "Pro Forma — [Property Name] — As of [Date]"). Row height 24-30. This is the only place merged cells are acceptable.

## 4. ILPA capital account / fund reporting conventions

For LP-facing fund reporting (capital call notices, distribution notices, capital account statements, performance summaries), follow ILPA template aesthetic:

- White background, black text, light grey (`#D9D9D9`) section bands, navy headers
- **No firm-brand color** — ILPA templates are intentionally plain
- Calibri 11pt or Arial 10pt
- Negatives in parentheses
- Currency unscaled with thousand separators
- Required metrics — always display, in this order: **Paid-In Capital, Unfunded Commitment, Distributions, NAV, TVPI, DPI, RVPI, Net IRR**
- TVPI = DPI + RVPI (use this identity as an embedded check row in Excel)

## 5. Charts

### Preferred chart types

| Use case | Chart | Notes |
|---|---|---|
| Time-series comparison | Column (vertical bars) | Most common in IC decks |
| Ranked categories | Bar (horizontal) | Use when labels are long |
| Trend / index | Line | Single or 2-3 series max |
| Bridge / decomposition (NOI bridge, IRR attribution, value bridge) | Waterfall | The McKinsey signature chart |
| Portfolio positioning | Scatter / bubble | Risk-return, basis-vs-cap-rate |
| Composition over time | Stacked column | Use sparingly; never stacked area |

### Avoid

- Pie charts with more than 3-4 slices (illegible)
- Donut charts (graphic-design trope)
- All 3D chart variants (universally derided)
- Stacked area (visually misleading)
- Speedometer / gauge / radar charts (dashboard aesthetic, not institutional)

### Chart styling

- **Title**: the *takeaway*, not the description ("NOI grew 14% CAGR driven by rent step-ups"), left-aligned above the chart, 10-12pt bold ink
- **Axis labels**: 9pt Arial/Calibri, grey `#595959`, units in the axis title ("USD millions")
- **Gridlines**: light grey `#D9D9D9` horizontal only; vertical gridlines off; or no gridlines with data labels on bars
- **Data labels**: on for bars/columns with few categories; same format as source cells
- **Legend**: omitted if one series; otherwise bottom or right, 9pt
- **Colors**: 1-4 max per chart. The "current" or "highlight" series gets the accent color; comparators are grey
- **No chart borders, no chart background fill** — white on white
- **Source line**: bottom-left below chart frame, 8-9pt italic grey, prefixed `Source: ` (capital S, colon, space)

## 6. Tables

### Style rules

- Minimal borders: thin top, thin bottom of table, single rule under header row only
- No vertical borders, no full grid
- Header row: bold, optional light grey `#F2F2F2` fill
- Numbers right-aligned; labels left-aligned; units centered or right-aligned
- Alternating row shading optional (`#F2F2F2`) — only on tables >8 rows where readability benefits
- Subtotals: bold + thin top border
- Totals: bold + thin top + double bottom border
- Footnote markers: superscript letter (a, b, c), not numbers (avoid confusion with figures)

### Number alignment

All currency, multiples, percentages, and bps right-aligned. Dates and text labels left-aligned. Header text matches column data alignment.

## 7. Slide deck conventions (IC, LP, lender pitches)

### Layout grid

- **Slide size**: 16:9, 13.33" × 7.5"
- **Action title** (top): 24-28pt sans-serif bold or 28-32pt serif. Left-aligned. Full sentence stating the takeaway. Fixed position across the deck.
- **Tracker bar** (optional): 8pt section labels, 0.3" tall, under the action title
- **Body**: chart/table on the left or center (~70% of slide); takeaway bullets on right or top (~30%)
- **Body bullets**: 3-5 max, 11-14pt, 1.2 line spacing, no paragraphs
- **Source line**: bottom-left above the footer, 8-9pt italic grey, `Source: ` prefix
- **Footer**: confidentiality marker L, deck title C, page number R; 8pt grey
- **Confidentiality**: `Confidential — for discussion purposes only` if appropriate; centered bottom or in footer

### Action titles — the most important rule

Every slide headline is a **complete sentence stating the conclusion**, not a topic label.

- Good: "Acquisition delivers 18% unlevered IRR with downside-protected basis"
- Bad: "IRR Analysis"
- Good: "Submarket vacancy of 4.2% supports 4% annual rent growth through 2028"
- Bad: "Market Overview"

A reader skimming only the action titles should be able to follow the entire argument of the deck.

### One idea per slide

If the slide needs a second action title or covers two unrelated points, split it. Density is welcome in the chart/table area; the action title and takeaway bullets must distill to one idea.

## 8. Memos (Word / PDF / markdown)

### Layout

- 1" margins all sides
- Letter-size (8.5" × 11")
- Line spacing 1.15 or 1.5
- Page numbers bottom-right
- Header: confidentiality marker, recipient if any
- Cover page: title, recipient, date (Month DD, YYYY format), preparer, version

### Hierarchy

- H1 (numbered, e.g., `1. Recommendation`): 14pt bold
- H2 (`1.1`): 12pt bold
- H3 (`1.1.1`): 11pt bold, often inline with paragraph
- Body: 11pt

### Inline content

- Footnotes for source attribution and detail; not parentheticals
- Tables: as described in §6
- Charts/figures: numbered ("Figure 1: ..."), with caption underneath in 9pt italic
- Cross-references: use section numbers ("See §3.2")

## 9. When the user provides a firm style guide

Override these defaults with the firm's specifics:

- Logo placement
- Firm-specific font (often a custom commercial typeface — substitute to the closest free equivalent if you can't access it)
- Firm primary and accent hex colors
- Firm's specific table/chart conventions
- Firm's deck cover page template

If the user mentions a firm name but doesn't provide a style guide, ask once. Don't guess.

## 10. Programmatic application

The skill ships with `scripts/excel_style.py` which applies the institutional named-style set to any openpyxl workbook. **Use it whenever generating Excel output.** Do not hand-style cells inconsistently.

Example:

```python
from openpyxl import Workbook
from scripts.excel_style import apply_institutional_styles, write_header, write_input, write_formula, write_section, write_total

wb = Workbook()
apply_institutional_styles(wb)
ws = wb.active
write_header(ws, "Pro Forma — Marina Apartments — As of 2026-Q1")
write_section(ws, "Operating Performance")
write_input(ws, "B5", 4500000, fmt="dollar")
write_formula(ws, "B6", "=B5/0.055", fmt="dollar")
write_total(ws, "B7", "=SUM(B5:B6)", fmt="dollar")
wb.save("output.xlsx")
```

For Word memos, `scripts/docx_style.py` provides equivalent helpers for python-docx (institutional fonts, hierarchy, table styling).
