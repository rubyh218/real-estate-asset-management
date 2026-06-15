# Real Estate & PE Asset Management — Claude Skill

[![tests](https://github.com/rubyh218/real-estate-asset-management/actions/workflows/tests.yml/badge.svg)](https://github.com/rubyh218/real-estate-asset-management/actions/workflows/tests.yml)

A [Claude Code](https://claude.com/claude-code) skill for real estate and private equity **asset management** workflows — the work that happens after acquisition through to exit.

Covers:
- Quarterly asset reviews and IC memos
- Investor/LP reporting (IRR, MOIC, TVPI, DPI, waterfall, capital accounts)
- Property performance analysis (rent rolls, T-12 variance, NOI bridges)
- Valuation updates (DCF, direct cap, comparable sales)
- Debt and covenant monitoring (DSCR, debt yield, LTV, maturity ladders, SOFR caps)
- Hold/sell/refi disposition analysis

All Excel, Word, and slide outputs are styled to institutional investor conventions — FAST / Wall Street Prep modeling color coding, ILPA reporting aesthetics, McKinsey-style action titles.

Asset-class coverage: multifamily, office, industrial, retail, hospitality, infrastructure.

## Install

Clone into your Claude Code skills directory:

```bash
# User-level (available across all projects)
git clone https://github.com/rubyh218/real-estate-asset-management.git \
  ~/.claude/skills/real-estate-asset-management

# Or project-level
git clone https://github.com/rubyh218/real-estate-asset-management.git \
  .claude/skills/real-estate-asset-management
```

Python dependencies for the helper scripts:

```bash
pip install -r requirements.txt
```

## Update

```bash
cd ~/.claude/skills/real-estate-asset-management
git pull
```

## Structure

```
SKILL.md                       # Entry point — workflow router and core principles
references/
  quarterly-asset-review.md    # QAR / IC memo workflow
  monthly-operating-review.md  # Multi-baseline variance, exception flags, debt + YM clock
  investor-reporting.md        # LP reporting, waterfall, IRR/MOIC/TVPI
  performance-analysis.md      # Rent rolls, T-12, NOI bridges
  valuation.md                 # DCF, direct cap, comps, mark-to-market
  debt-monitoring.md           # DSCR, debt yield, LTV, refi
  disposition-analysis.md      # Hold/sell/refi decisions
  design-standards.md          # Institutional formatting conventions
  asset-classes/
    multifamily.md
    office.md
    industrial.md
    retail.md
    hospitality.md
    infrastructure.md
assets/
  qar-template.md              # Quarterly asset review template
  disposition-memo-template.md # Hold/sell/refi memo template
scripts/
  returns.py                   # IRR, NPV, MOIC, MIRR + multi-IRR detection
  waterfall.py                 # Deal + fund waterfall (pref, catchup, two-tier promote, clawback)
  debt_metrics.py              # DSCR, debt yield, LTV/LTC, max-loan sizing
  yield_maintenance.py         # YM prepay penalty + refi-timing decision support
  noi_bridge.py                # NOI variance bridge (UW vs Actual line-item walk)
  variance_report.py           # Multi-baseline / multi-basis operating variance + exception flags
  rent_roll.py                 # Rent roll analyzer (occupancy, GPR, LTL, WALT, expiration ladder)
  excel_style.py               # Institutional Excel formatting helpers
  docx_style.py                # Institutional Word memo formatting helpers
examples/
  sample-multifamily/          # Synthetic 24-unit property — rent roll, T-12, UW baseline
```

## Try it

See [`examples/`](examples/) for a fully synthetic sample (rent roll + T-12 + UW baseline) with suggested prompts that exercise the main workflows.

The styling scripts also have demo flags that write sample outputs:

```bash
python scripts/excel_style.py --demo sample.xlsx   # writes a styled sample workbook
python scripts/docx_style.py --demo sample.docx    # writes a styled sample memo
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Triggers

The skill activates when Claude detects asset-management context — operating properties, fund-level returns, LP capital accounts, rent rolls, T-12s, operating statements, lender covenants, business plans, capital calls/distributions — even when "asset management" isn't said explicitly. Phrases like "review this property," "should we sell or hold," "covenant test," "variance to budget," "mark to market," or file attachments named `rent_roll.xlsx`, `T12.xlsx`, etc., also trigger it.

## License

MIT — see [LICENSE](LICENSE).
