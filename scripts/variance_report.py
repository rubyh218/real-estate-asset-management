"""
variance_report.py — Multi-baseline, multi-basis operating variance report.

WHY THIS EXISTS
---------------
The institutional AM dashboard surfaces operating performance through
two rotating axes:

  1. BASELINE: actual vs. UW / Budget / Prior period / T-12 average
  2. BASIS:    $ total / $/unit/month / % of EGR / % of OpEx / % of baseline

`noi_bridge.py` handles the simple two-column case (one baseline, dollars only).
This module covers the multi-column matrix view that's standard in monthly
operating reviews and ILPA-style LP reports.

INPUT FORMAT
-----------
A CSV with `line_item`, `category` (revenue/expense), and ONE OR MORE
baseline columns followed by an Actual column. The LAST value column is
always treated as the actual; everything before it is a baseline:

    line_item,category,UW,Budget,Prior T-12,Actual T-12
    Gross Potential Rent,revenue,5800000,5850000,5790000,5790000
    Vacancy,revenue,-290000,-295000,-310000,-325000
    Other Income,revenue,220000,235000,240000,245000
    Property Tax,expense,400000,410000,430000,450000
    Insurance,expense,100000,115000,125000,140000

SIGN CONVENTION
---------------
Same as noi_bridge.py:
  - revenue rows: positive amounts add to NOI (vacancy as negative revenue)
  - expense rows: positive amounts subtract from NOI

Variance is always computed as IMPACT ON NOI:
  - revenue: actual - baseline   (positive = favorable)
  - expense: baseline - actual   (positive = favorable, i.e. lower spend)

OUTPUT
------
format_report() prints a wide table with one row per line item:
  Line | Baseline_1 | Baseline_2 | ... | Actual | Var vs <chosen baseline>

The "Var vs <baseline>" column is rendered in the chosen basis:
  - dollar:      raw $ impact on NOI
  - per_unit_mo: $/unit/month impact (requires unit_count + months_in_period)
  - pct_of_egr:  variance / actual EGR
  - pct_of_opex: variance / actual OpEx (expense rows only; revenue lines blank)
  - pct_var:     variance / baseline value (the "% var" column most P&Ls show)

Usage:
  python variance_report.py --csv lines.csv --baseline "UW" --basis dollar
  python variance_report.py --csv lines.csv --baseline Budget \\
      --basis per_unit_mo --unit-count 200 --months 12
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field


@dataclass
class VarianceLine:
    line_item: str
    category: str                          # "revenue" or "expense"
    values: dict[str, float]               # {column_label: value}
    # Computed by build_report():
    impacts: dict[str, float] = field(default_factory=dict)
    # {baseline_label: impact_on_noi_vs_that_baseline}


@dataclass
class VarianceReport:
    columns: list[str]                     # all value column labels in order
    baselines: list[str]                   # all columns except the last
    actual_label: str                      # the last column
    lines: list[VarianceLine]
    unit_count: int = 0                    # for $/unit/mo basis
    months_in_period: int = 12             # T-3=3, T-6=6, T-12=12, etc.

    def column_total(self, column: str, category: str | None = None) -> float:
        """Sum a column, optionally filtered by category."""
        return sum(
            L.values.get(column, 0.0)
            for L in self.lines
            if category is None or L.category == category
        )

    def egr(self, column: str) -> float:
        """Effective gross revenue (sum of all revenue lines) for a column."""
        return self.column_total(column, category="revenue")

    def opex(self, column: str) -> float:
        """Total OpEx (sum of all expense lines) for a column."""
        return self.column_total(column, category="expense")

    def noi(self, column: str) -> float:
        return self.egr(column) - self.opex(column)


def build_report(
    rows: list[dict],
    columns: list[str],
    unit_count: int = 0,
    months_in_period: int = 12,
) -> VarianceReport:
    """Build a VarianceReport from parsed rows.

    `columns` is the ordered list of value column labels (e.g.,
    ["UW", "Budget", "Prior T-12", "Actual T-12"]). The LAST column is
    treated as the actual; everything before is a baseline.
    """
    if len(columns) < 2:
        raise ValueError("need at least 2 columns: 1+ baselines and 1 actual")

    actual = columns[-1]
    baselines = columns[:-1]

    lines: list[VarianceLine] = []
    for r in rows:
        cat = r["category"].lower().strip()
        if cat not in ("revenue", "expense"):
            raise ValueError(
                f"line {r.get('line_item')!r}: category must be 'revenue' or "
                f"'expense', got {r['category']!r}"
            )
        values = {col: float(r[col]) for col in columns}
        actual_val = values[actual]
        # impact_on_noi for each baseline column (positive = favorable to NOI).
        impacts = {}
        for b in baselines:
            base_val = values[b]
            if cat == "revenue":
                impacts[b] = actual_val - base_val
            else:
                impacts[b] = base_val - actual_val
        lines.append(VarianceLine(
            line_item=r["line_item"],
            category=cat,
            values=values,
            impacts=impacts,
        ))

    return VarianceReport(
        columns=columns,
        baselines=baselines,
        actual_label=actual,
        lines=lines,
        unit_count=unit_count,
        months_in_period=months_in_period,
    )


# ---------------------------------------------------------------------------
# Basis transformations
# ---------------------------------------------------------------------------

def _basis_value(
    report: VarianceReport,
    line: VarianceLine,
    impact: float,
    basis: str,
) -> tuple[str, str]:
    """Return (formatted_str, basis_name) for a given line's variance under
    a basis. Used for the printed Var column.
    """
    actual = report.actual_label
    if basis == "dollar":
        return _fmt_dollar(impact), "$"
    if basis == "per_unit_mo":
        if report.unit_count <= 0 or report.months_in_period <= 0:
            raise ValueError(
                "per_unit_mo basis requires unit_count > 0 and months_in_period > 0"
            )
        v = impact / report.unit_count / report.months_in_period
        return f"${v:>10,.2f}", "$/unit/mo"
    if basis == "pct_of_egr":
        egr = report.egr(actual)
        if egr == 0:
            return "n/a", "% EGR"
        return f"{impact / egr * 100:>9.2f}%", "% EGR"
    if basis == "pct_of_opex":
        if line.category != "expense":
            return "—", "% OpEx"
        opex = report.opex(actual)
        if opex == 0:
            return "n/a", "% OpEx"
        return f"{impact / opex * 100:>9.2f}%", "% OpEx"
    if basis == "pct_var":
        # % of baseline value; tricky for vacancy etc. (negative baseline).
        # We use absolute baseline so the % reads natural.
        base_val = line.values.get(_chosen_baseline_for_pct(line, impact), 0.0)
        if base_val == 0:
            return "n/a", "% var"
        return f"{impact / abs(base_val) * 100:>9.2f}%", "% var"
    raise ValueError(f"unknown basis: {basis!r}")


def _chosen_baseline_for_pct(line: VarianceLine, impact: float) -> str:
    """Used by pct_var: pick the baseline whose impact matches the one being
    rendered. Caller should pass the baseline name through context."""
    # Simplification: assume the caller provided the right impact and we can
    # find its baseline by matching the value.
    for k, v in line.impacts.items():
        if abs(v - impact) < 1e-6:
            return k
    return next(iter(line.impacts))


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _fmt_dollar(v: float) -> str:
    if v < 0:
        return f"({abs(v):,.0f})"
    return f"{v:,.0f}"


def format_report(
    report: VarianceReport,
    baseline: str | None = None,
    basis: str = "dollar",
    sort_by_abs_impact: bool = False,
) -> str:
    """Render the variance report as institutional plain text.

    baseline: which baseline column to use for the Variance column. Defaults
              to the first baseline in `report.baselines`.
    basis: 'dollar' | 'per_unit_mo' | 'pct_of_egr' | 'pct_of_opex' | 'pct_var'
    sort_by_abs_impact: if True, sort lines by |impact vs baseline| desc.
    """
    if baseline is None:
        baseline = report.baselines[0]
    if baseline not in report.baselines:
        raise ValueError(
            f"baseline {baseline!r} not in available baselines: {report.baselines}"
        )

    lines = report.lines
    if sort_by_abs_impact:
        lines = sorted(lines, key=lambda L: -abs(L.impacts[baseline]))

    # Column widths
    line_w = max(20, max(len(L.line_item) for L in lines) + 2)
    col_w = 14   # wide enough for $ amounts with commas + parens

    out: list[str] = []
    bar = "=" * (line_w + col_w * (len(report.columns) + 1) + 4)
    out.append(bar)
    period = f"({report.months_in_period}-mo period"
    if report.unit_count:
        period += f", {report.unit_count} units"
    period += ")"
    out.append(f"OPERATING VARIANCE REPORT  {period}")
    out.append(f"Variance basis: {basis}  |  vs baseline: {baseline}")
    out.append(bar)

    # Header
    header = f"{'Line Item':<{line_w}}"
    for col in report.columns:
        header += f"{col:>{col_w}}"
    header += f"{'Var vs ' + baseline:>{col_w}}"
    out.append(header)
    out.append("-" * len(bar))

    # Body — revenue lines, then a subtotal, then expense lines, then NOI.
    def _emit(L: VarianceLine):
        row = f"  {L.line_item:<{line_w - 2}}"
        for col in report.columns:
            row += f"{_fmt_dollar(L.values[col]):>{col_w}}"
        var_str, _ = _basis_value(report, L, L.impacts[baseline], basis)
        row += f"{var_str:>{col_w}}"
        out.append(row)

    revenue_lines = [L for L in lines if L.category == "revenue"]
    expense_lines = [L for L in lines if L.category == "expense"]

    if revenue_lines:
        out.append(f"{'REVENUE':<{line_w}}")
        for L in revenue_lines:
            _emit(L)
        sub = f"  {'Effective Gross Revenue':<{line_w - 2}}"
        for col in report.columns:
            sub += f"{_fmt_dollar(report.egr(col)):>{col_w}}"
        # Variance on subtotal = sum of impacts on revenue lines for the baseline
        egr_impact = sum(L.impacts[baseline] for L in revenue_lines)
        sub_var, _ = _basis_value(
            report,
            VarianceLine("EGR Total", "revenue", {}, {baseline: egr_impact}),
            egr_impact, basis,
        )
        sub += f"{sub_var:>{col_w}}"
        out.append(sub)
        out.append("")

    if expense_lines:
        out.append(f"{'OPERATING EXPENSES':<{line_w}}")
        for L in expense_lines:
            _emit(L)
        sub = f"  {'Total OpEx':<{line_w - 2}}"
        for col in report.columns:
            sub += f"{_fmt_dollar(report.opex(col)):>{col_w}}"
        opex_impact = sum(L.impacts[baseline] for L in expense_lines)
        sub_var, _ = _basis_value(
            report,
            VarianceLine("OpEx Total", "expense", {}, {baseline: opex_impact}),
            opex_impact, basis,
        )
        sub += f"{sub_var:>{col_w}}"
        out.append(sub)
        out.append("")

    # NOI row
    noi_row = f"{'NET OPERATING INCOME':<{line_w}}"
    for col in report.columns:
        noi_row += f"{_fmt_dollar(report.noi(col)):>{col_w}}"
    noi_impact = report.noi(report.actual_label) - report.noi(baseline)
    noi_var, _ = _basis_value(
        report,
        VarianceLine("NOI", "revenue", {}, {baseline: noi_impact}),
        noi_impact, basis,
    )
    noi_row += f"{noi_var:>{col_w}}"
    out.append(noi_row)
    out.append(bar)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def parse_csv(path: str) -> tuple[list[dict], list[str]]:
    """Parse a variance CSV. Returns (rows, ordered_value_columns)."""
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        headers = [h.strip() for h in reader.fieldnames or []]
        meta_cols = {"line_item", "category"}
        value_cols = [c for c in headers if c not in meta_cols]
        if not value_cols:
            raise ValueError(
                f"{path}: no value columns found. CSV needs columns "
                "line_item, category, and one or more dollar columns "
                "(last is actual)."
            )
        for raw in reader:
            row = {k.strip(): (v or "").strip() for k, v in raw.items()}
            if not row.get("line_item"):
                continue
            parsed = {"line_item": row["line_item"], "category": row["category"]}
            for c in value_cols:
                s = row.get(c, "").replace(",", "").replace("$", "")
                parsed[c] = float(s) if s else 0.0
            rows.append(parsed)
    return rows, value_cols


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--csv", required=True, help="Variance CSV path")
    p.add_argument("--baseline", default=None,
                   help="Which baseline column to compare actual against. "
                        "Defaults to the first baseline.")
    p.add_argument("--basis", default="dollar",
                   choices=["dollar", "per_unit_mo", "pct_of_egr",
                            "pct_of_opex", "pct_var"],
                   help="Variance display basis (default: dollar)")
    p.add_argument("--unit-count", type=int, default=0,
                   help="Required for --basis per_unit_mo")
    p.add_argument("--months", type=int, default=12,
                   help="Months in period (T-3=3, T-12=12, etc.). Default 12.")
    p.add_argument("--sort", action="store_true",
                   help="Sort lines by absolute variance vs chosen baseline (desc)")
    p.add_argument("--flags", action="store_true",
                   help="Also print an operating-exceptions report using default thresholds")
    args = p.parse_args()

    rows, value_cols = parse_csv(args.csv)
    report = build_report(
        rows, columns=value_cols,
        unit_count=args.unit_count, months_in_period=args.months,
    )
    print(format_report(
        report, baseline=args.baseline, basis=args.basis,
        sort_by_abs_impact=args.sort,
    ))
    if args.flags:
        flags = flag_lines(report, baseline=args.baseline)
        print()
        print(format_flags(flags))


# ---------------------------------------------------------------------------
# Operating exceptions / flag logic
# ---------------------------------------------------------------------------
#
# Heatmap-style flagging: any line where the variance to baseline exceeds a
# threshold gets surfaced. The defaults reflect institutional review tolerance —
# insurance and property tax get tighter bands because those are the typical
# step-function risks (CAT premium spike, post-close reassessment); other lines
# get the broader 10/20 band.

@dataclass(frozen=True)
class Threshold:
    """One threshold rule. `line_item` and `category` are either both None
    (= default for any line) or one of them is set to scope the rule."""
    pct_warn: float            # |variance / baseline| > pct_warn → warn
    pct_critical: float        # |variance / baseline| > pct_critical → critical
    line_item: str | None = None
    category: str | None = None   # "revenue" or "expense"
    direction: str = "unfavorable"  # "favorable" | "unfavorable" | "either"


@dataclass(frozen=True)
class Flag:
    line_item: str
    category: str
    baseline: str
    baseline_value: float
    actual_value: float
    impact_on_noi: float
    pct_variance: float          # signed; positive = favorable
    severity: str                # "warn" | "critical"
    direction: str               # "favorable" | "unfavorable"
    message: str


# Default thresholds: tighter on tax/insurance, looser everywhere else.
# Order matters — more-specific rules first.
DEFAULT_THRESHOLDS: list[Threshold] = [
    Threshold(line_item="Property Tax", pct_warn=0.05, pct_critical=0.15),
    Threshold(line_item="Insurance",    pct_warn=0.10, pct_critical=0.15),
    # Catch-all for all other lines:
    Threshold(line_item=None, category=None, pct_warn=0.10, pct_critical=0.20),
]


def _direction_for_line(line: VarianceLine, impact: float) -> str:
    """positive impact_on_noi = favorable; negative = unfavorable."""
    if impact > 0:
        return "favorable"
    if impact < 0:
        return "unfavorable"
    return "neither"


def _applicable_threshold(
    line: VarianceLine, thresholds: list[Threshold]
) -> Threshold | None:
    """Pick the first threshold whose line_item / category scope matches."""
    for t in thresholds:
        if t.line_item is not None and t.line_item.lower() != line.line_item.lower():
            continue
        if t.category is not None and t.category != line.category:
            continue
        return t
    return None


def flag_lines(
    report: VarianceReport,
    baseline: str | None = None,
    thresholds: list[Threshold] | None = None,
) -> list[Flag]:
    """Return all lines whose variance vs the chosen baseline exceeds the
    applicable threshold's warn or critical band.

    Lines are flagged only if the direction matches the threshold's
    `direction` (defaults to 'unfavorable' so the report doesn't drown in
    favorable-side noise).
    """
    if baseline is None:
        baseline = report.baselines[0]
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    flags: list[Flag] = []
    for L in report.lines:
        t = _applicable_threshold(L, thresholds)
        if t is None:
            continue
        baseline_val = L.values[baseline]
        actual_val = L.values[report.actual_label]
        impact = L.impacts[baseline]
        if baseline_val == 0:
            continue   # can't compute % variance
        pct_var = impact / abs(baseline_val)
        direction = _direction_for_line(L, impact)

        # Filter by direction policy.
        if t.direction == "unfavorable" and direction != "unfavorable":
            continue
        if t.direction == "favorable" and direction != "favorable":
            continue

        abs_pct = abs(pct_var)
        if abs_pct < t.pct_warn:
            continue
        severity = "critical" if abs_pct >= t.pct_critical else "warn"
        sign = "+" if pct_var > 0 else ""
        message = (
            f"{L.line_item}: {sign}{pct_var * 100:.1f}% vs {baseline} "
            f"(${actual_val:,.0f} vs ${baseline_val:,.0f}) -- "
            f"{direction} impact ${impact:+,.0f}"
        )
        flags.append(Flag(
            line_item=L.line_item, category=L.category,
            baseline=baseline, baseline_value=baseline_val,
            actual_value=actual_val, impact_on_noi=impact,
            pct_variance=pct_var, severity=severity,
            direction=direction, message=message,
        ))
    return flags


def format_flags(flags: list[Flag]) -> str:
    """Pretty-print the exception list with severity grouping."""
    if not flags:
        return "OPERATING EXCEPTIONS: none flagged."
    out: list[str] = []
    bar = "=" * 72
    out.append(bar)
    out.append(f"OPERATING EXCEPTIONS  ({len(flags)} flagged)")
    out.append(bar)
    for severity in ("critical", "warn"):
        bucket = [f for f in flags if f.severity == severity]
        if not bucket:
            continue
        marker = "!!" if severity == "critical" else " !"
        out.append(f"\n  [{severity.upper()}]")
        for f in bucket:
            out.append(f"  {marker} {f.message}")
    out.append(bar)
    return "\n".join(out)


if __name__ == "__main__":
    main()
