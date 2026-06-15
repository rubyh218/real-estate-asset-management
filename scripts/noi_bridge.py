"""
noi_bridge.py — Build NOI variance bridges from baseline vs actual line items.

The NOI bridge is the asset manager's signature reconciliation exhibit: it
walks from one NOI figure (UW, prior period, budget) to another (actual,
forecast) by isolating each driver. Per performance-analysis.md: each line
has one root cause, lines are ordered by size of driver descending, and
the bridge totals exactly to the NOI delta.

CSV input format:

    line_item,category,baseline,actual
    Gross Potential Rent,revenue,5800000,5790000
    Vacancy,revenue,-290000,-325000
    Other Income,revenue,220000,245000
    Property Tax,expense,400000,450000
    Insurance,expense,100000,140000

Where `category` is "revenue" or "expense" — the natural P&L view:
  - revenue: positive amounts add to NOI; negative subtract
    (vacancy and concessions enter as negative revenue)
  - expense: positive amounts subtract from NOI
    (NOI = sum(revenue) - sum(expense))

For each line the impact-on-NOI variance is computed as:
  revenue: actual - baseline      (positive = favorable to NOI)
  expense: baseline - actual      (positive = expense reduction = favorable)

Usage:

    python noi_bridge.py --csv lines.csv \\
        --baseline-label "UW Yr2" --actual-label "T-12 Actual"

    # With Excel output styled to institutional conventions:
    python noi_bridge.py --csv lines.csv --xlsx bridge.xlsx
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass


@dataclass
class BridgeLine:
    line_item: str
    category: str           # "revenue" or "expense"
    baseline: float
    actual: float
    impact_on_noi: float    # signed: positive = favorable to NOI

    @property
    def raw_variance(self) -> float:
        """actual - baseline, no sign flip. Tells you whether the line itself moved up or down."""
        return self.actual - self.baseline

    @property
    def pct_variance(self) -> float:
        if self.baseline == 0:
            return float("inf") if self.actual != 0 else 0.0
        return (self.actual - self.baseline) / abs(self.baseline)


@dataclass
class BridgeResult:
    baseline_noi: float
    actual_noi: float
    lines: list[BridgeLine]

    @property
    def total_variance(self) -> float:
        return self.actual_noi - self.baseline_noi

    @property
    def pct_variance(self) -> float:
        if self.baseline_noi == 0:
            return float("inf") if self.actual_noi != 0 else 0.0
        return self.total_variance / abs(self.baseline_noi)


def build_bridge(rows: list[dict]) -> BridgeResult:
    """Build a BridgeResult from a list of row dicts.

    Each row must have keys: 'line_item', 'category' ('revenue' or 'expense'),
    'baseline', 'actual'. Amounts are floats.
    """
    lines: list[BridgeLine] = []
    rev_baseline = rev_actual = 0.0
    exp_baseline = exp_actual = 0.0
    for r in rows:
        cat = r["category"].lower().strip()
        if cat not in ("revenue", "expense"):
            raise ValueError(
                f"line {r.get('line_item')!r}: category must be 'revenue' or 'expense', "
                f"got {r['category']!r}"
            )
        b = float(r["baseline"])
        a = float(r["actual"])
        if cat == "revenue":
            impact = a - b
            rev_baseline += b
            rev_actual += a
        else:
            impact = b - a
            exp_baseline += b
            exp_actual += a
        lines.append(BridgeLine(
            line_item=r["line_item"],
            category=cat,
            baseline=b,
            actual=a,
            impact_on_noi=impact,
        ))

    baseline_noi = rev_baseline - exp_baseline
    actual_noi = rev_actual - exp_actual
    return BridgeResult(baseline_noi=baseline_noi, actual_noi=actual_noi, lines=lines)


def format_bridge(
    result: BridgeResult,
    baseline_label: str = "Baseline",
    actual_label: str = "Actual",
    sort_by_impact: bool = True,
) -> str:
    """Pretty-print the bridge as institutional plain text.

    sort_by_impact: order lines by |impact_on_noi| descending (biggest drivers first).
    """
    lines = result.lines
    if sort_by_impact:
        lines = sorted(lines, key=lambda L: -abs(L.impact_on_noi))

    out = []
    out.append("=" * 72)
    out.append(f"NOI BRIDGE: {baseline_label} -> {actual_label}")
    out.append("=" * 72)
    out.append(f"{baseline_label + ' NOI':<52} ${result.baseline_noi:>15,.0f}")
    out.append("-" * 72)
    for L in lines:
        if L.impact_on_noi == 0:
            continue
        sign_char = "+" if L.impact_on_noi > 0 else "-"
        amt_str = (
            f"({abs(L.impact_on_noi):,.0f})" if L.impact_on_noi < 0
            else f"{L.impact_on_noi:,.0f}"
        )
        out.append(f"  {sign_char} {L.line_item:<46} ${amt_str:>14}")
    out.append("-" * 72)
    out.append(f"{actual_label + ' NOI':<52} ${result.actual_noi:>15,.0f}")
    out.append("=" * 72)
    pct = result.pct_variance * 100
    sign = "+" if result.total_variance >= 0 else ""
    out.append(
        f"Variance:                                          "
        f"  ${result.total_variance:>13,.0f}  ({sign}{pct:.1f}%)"
    )
    out.append("=" * 72)

    # Reconciliation invariant — should always hold mod float noise.
    impact_sum = sum(L.impact_on_noi for L in lines)
    if abs(impact_sum - result.total_variance) > 0.5:
        out.append(
            f"WARNING: line impacts sum to ${impact_sum:,.2f} but NOI delta is "
            f"${result.total_variance:,.2f} — math drift detected"
        )

    return "\n".join(out)


def parse_csv(path: str) -> list[dict]:
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {k.strip().lower(): (v or "").strip() for k, v in raw.items()}
            if not row.get("line_item"):
                continue
            rows.append({
                "line_item": row["line_item"],
                "category": row["category"],
                "baseline": float(row["baseline"].replace(",", "").replace("$", "")),
                "actual": float(row["actual"].replace(",", "").replace("$", "")),
            })
    return rows


def to_xlsx(
    result: BridgeResult,
    path: str,
    baseline_label: str = "Baseline",
    actual_label: str = "Actual",
) -> None:
    """Write the bridge to an Excel workbook styled to institutional conventions."""
    from openpyxl import Workbook
    try:  # works both as a flat script (scripts/ on path) and as a package import
        from excel_style import (
            apply_institutional_styles, set_sheet_defaults,
            write_header, write_section, write_label,
            write_input, write_subtotal, write_total, write_note,
        )
    except ImportError:
        from scripts.excel_style import (
            apply_institutional_styles, set_sheet_defaults,
            write_header, write_section, write_label,
            write_input, write_subtotal, write_total, write_note,
        )

    wb = Workbook()
    apply_institutional_styles(wb)
    ws = wb.active
    ws.title = "NOI Bridge"
    title = f"NOI Bridge - {baseline_label} to {actual_label}"
    set_sheet_defaults(ws, title)

    write_header(ws, 1, title, span_cols=6)
    write_section(ws, 3, "Bridge from baseline to actual", span_cols=6)

    write_label(ws, "B4", "Line Item", bold=True)
    write_label(ws, "E4", "Impact on NOI", bold=True)

    write_label(ws, "B5", f"{baseline_label} NOI", bold=True)
    write_subtotal(ws, "E5", result.baseline_noi, fmt="dollar")

    row = 7
    sorted_lines = sorted(result.lines, key=lambda L: -abs(L.impact_on_noi))
    for L in sorted_lines:
        if L.impact_on_noi == 0:
            continue
        write_label(ws, f"B{row}", L.line_item)
        write_input(ws, f"E{row}", L.impact_on_noi, fmt="dollar")
        row += 1

    end_row = row + 1
    write_label(ws, f"B{end_row}", f"{actual_label} NOI", bold=True)
    write_total(ws, f"E{end_row}", result.actual_noi, fmt="dollar")

    write_note(
        ws,
        end_row + 2,
        f"Variance: ${result.total_variance:,.0f} ({result.pct_variance*100:+.1f}% vs {baseline_label})",
    )

    wb.save(path)


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--csv", required=True, help="CSV: line_item, category, baseline, actual")
    p.add_argument("--baseline-label", default="Baseline", help="Label for baseline column (default 'Baseline')")
    p.add_argument("--actual-label", default="Actual", help="Label for actual column (default 'Actual')")
    p.add_argument("--no-sort", action="store_true", help="Print in input order (default: sort by |impact| desc)")
    p.add_argument("--xlsx", default=None, help="Also write a styled Excel workbook to this path")
    args = p.parse_args()

    rows = parse_csv(args.csv)
    result = build_bridge(rows)
    print(format_bridge(
        result,
        baseline_label=args.baseline_label,
        actual_label=args.actual_label,
        sort_by_impact=not args.no_sort,
    ))

    if args.xlsx:
        to_xlsx(result, args.xlsx, baseline_label=args.baseline_label, actual_label=args.actual_label)
        print(f"\nWrote Excel bridge to {args.xlsx}")


if __name__ == "__main__":
    main()
