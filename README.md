# Real Estate & PE Asset Management — Claude Plugin

[![tests](https://github.com/rubyh218/real-estate-asset-management/actions/workflows/tests.yml/badge.svg)](https://github.com/rubyh218/real-estate-asset-management/actions/workflows/tests.yml)

A Claude plugin for real estate and private equity **asset management** workflows — the work that happens after acquisition through to exit.

Covers:
- Quarterly asset reviews and IC memos
- Investor/LP reporting (IRR, MOIC, TVPI, DPI, waterfall, capital accounts)
- Property performance analysis (rent rolls, T-12 variance, NOI bridges)
- Valuation updates (DCF, direct cap, comparable sales)
- Debt and covenant monitoring (DSCR, debt yield, LTV, maturity ladders, SOFR caps)
- Hold/sell/refi disposition analysis

All Excel, Word, and slide outputs are styled to institutional investor conventions — FAST / Wall Street Prep modeling color coding, ILPA reporting aesthetics, McKinsey-style action titles.

Asset-class coverage: multifamily, office, industrial, retail, hospitality, infrastructure.

## What this plugin runs

This plugin is instructions plus a set of local Python helper scripts. Here is everything it does outside of the conversation:

- **Runs Python scripts locally.** The scripts in `skills/real-estate-asset-management/scripts/` do the math (IRR, waterfalls, DSCR, rent roll and variance analysis) and format Excel and Word files. They read only the files you give Claude and write output files to your working folder.
- **Installs two Python packages if missing.** Before the first script run, Claude checks for `openpyxl` and `python-docx` and, if they are not installed, downloads them from PyPI with `pip`. This is the only network access.
- **Sends no data anywhere.** The scripts make no network calls and do not contact any external service, API, or server. The plugin includes no MCP connectors, hooks, or telemetry.
- **Stores nothing.** The plugin keeps no data between sessions. Any files it creates are saved where you choose and are yours to keep or delete.
- **Not intended for people under 18.**

Your property, fund, and investor data stays in your conversation with Claude and the files you create.

## Install

This repo is a Claude plugin and its own plugin marketplace. Pick the option that matches how you use Claude.

### Claude.ai, Claude Desktop, or Cowork

1. Open **Customize > Plugins**.
2. Choose **Add > Add marketplace** and enter `rubyh218/real-estate-asset-management`.
3. Find **real-estate-asset-management** in the list and select **Add**.

The plugin is saved to your account, so it also syncs to Cowork and Claude Code when you sign in with the same account.

To install without a marketplace, download this repo as a `.zip` and use **Add > Upload plugin**.

### Claude Code

```bash
claude plugin marketplace add rubyh218/real-estate-asset-management
claude plugin install real-estate-asset-management@rubyh218-plugins
```

Or inside a session: `/plugin marketplace add rubyh218/real-estate-asset-management`, then `/plugin install real-estate-asset-management@rubyh218-plugins`.

The skill loads automatically when the task matches. To call it directly, type `/real-estate-asset-management:real-estate-asset-management`.

### Python dependencies

The helper scripts need `openpyxl` and `python-docx`. Claude installs them on first use if they are missing. To install them yourself:

```bash
pip install -r requirements.txt
```

### Upgrading from the old install

Earlier versions were installed by cloning into `~/.claude/skills/real-estate-asset-management`. That path no longer works because `SKILL.md` moved into `skills/`. Remove the old clone and install the plugin instead:

```bash
rm -rf ~/.claude/skills/real-estate-asset-management
```

## Update

Claude.ai and Desktop: open the plugin in **Customize > Plugins** and select **Check for updates**, or turn on **Sync automatically** for the marketplace.

Claude Code:

```bash
claude plugin marketplace update rubyh218-plugins
```

## What's included

| Component | Works in | Purpose |
|---|---|---|
| Skill: `real-estate-asset-management` | Chat, Cowork, Claude Code | Workflow router, references, templates, and scripts |
| Agent: `real-estate-asset-management` | Cowork, Claude Code | Subagent Claude can delegate asset management work to |

## Structure

```
.claude-plugin/
  plugin.json                  # Plugin manifest
  marketplace.json             # Marketplace catalog (this repo lists itself)
skills/
  real-estate-asset-management/
    SKILL.md                   # Entry point: workflow router and core principles
    references/
      quarterly-asset-review.md    # QAR / IC memo workflow
      monthly-operating-review.md  # Multi-baseline variance, exception flags, debt + YM clock
      investor-reporting.md        # LP reporting, waterfall, IRR/MOIC/TVPI
      performance-analysis.md      # Rent rolls, T-12, NOI bridges
      valuation.md                 # DCF, direct cap, comps, mark-to-market
      debt-monitoring.md           # DSCR, debt yield, LTV, refi
      disposition-analysis.md      # Hold/sell/refi decisions
      design-standards.md          # Institutional formatting conventions
      asset-classes/               # Multifamily, office, industrial, retail, hospitality, infrastructure
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
agents/
  real-estate-asset-management.md  # Subagent definition
examples/
  sample-multifamily/          # Synthetic 24-unit property: rent roll, T-12, UW baseline
tests/                         # Unit tests for the analysis scripts
```

## Develop locally

```bash
claude plugin validate .
claude --plugin-dir .
```

When you release changes, bump `version` in `.claude-plugin/plugin.json` so installed copies pick up the update.

## Try it

See [`examples/`](examples/) for a fully synthetic sample (rent roll + T-12 + UW baseline) with suggested prompts that exercise the main workflows.

The styling scripts also have demo flags that write sample outputs:

```bash
python skills/real-estate-asset-management/scripts/excel_style.py --demo sample.xlsx   # writes a styled sample workbook
python skills/real-estate-asset-management/scripts/docx_style.py --demo sample.docx    # writes a styled sample memo
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Triggers

The skill activates when Claude detects asset-management context — operating properties, fund-level returns, LP capital accounts, rent rolls, T-12s, operating statements, lender covenants, business plans, capital calls/distributions — even when "asset management" isn't said explicitly. Phrases like "review this property," "should we sell or hold," "covenant test," "variance to budget," "mark to market," or file attachments named `rent_roll.xlsx`, `T12.xlsx`, etc., also trigger it.

## License

MIT — see [LICENSE](LICENSE).
