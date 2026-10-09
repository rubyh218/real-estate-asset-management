"""
rent_roll.py — Analyze a multifamily / commercial rent roll CSV.

Computes the standard metrics an asset manager extracts from any rent roll:
physical / leased / economic occupancy, GPR, in-place rent, loss-to-lease
(rent- and GPR-weighted), WALT, expiration ladder, and a per-unit-type
breakdown.

Expected CSV columns (case-insensitive; extra columns ignored):
  unit             unit number / ID                   (required)
  unit_type        floor plan label (e.g., "1BR")     (optional but useful)
  sqft             unit square footage                (optional)
  status           tenant status (see below)          (required)
  tenant           tenant name                        (optional)
  in_place_rent    current monthly rent ($)           (required for occupied)
  market_rent      current asking / market rent ($)   (required)
  lease_start      ISO date                           (optional)
  lease_end        ISO date                           (optional)
  move_in          ISO date                           (optional)

Status values (case-insensitive; alternates in parens):
  Occupied (Occ)   tenant in place, paying rent
  Notice           tenant in place but has given notice to vacate
  SNO (Signed)     lease signed, tenant not yet moved in
  Vacant (Vac)     unit vacant and available
  MTM              month-to-month (occupied, no fixed lease_end)

Conventions:
  - Physical occupancy: counts Occupied + Notice + MTM (all in-place paying units)
  - Leased occupancy:   counts Occupied + Notice + SNO + MTM
  - Economic occupancy: sum of in-place rents (Occupied + Notice + MTM) divided by GPR
  - GPR (annualized):   12 * sum of market rents across ALL units
  - LTL %:              sum of per-unit max(market - in_place, 0) across paying
                        units, / GPR. Units above market are floored at 0 —
                        gain-to-lease does not net against loss-to-lease.
  - WALT (rent-weighted): excludes MTM and expired leases (no future lease_end)
  - Expiration ladder:  rolling 12 months by quarter from as_of

Usage:
  python rent_roll.py --csv rent_roll.csv --as-of 2026-03-31
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import date, datetime


# Status normalization
_STATUS_ALIAS = {
    "occupied": "Occupied", "occ": "Occupied",
    "notice":   "Notice",
    "sno":      "SNO",      "signed": "SNO",
    "vacant":   "Vacant",   "vac": "Vacant",
    "mtm":      "MTM",      "month-to-month": "MTM",
}

# Statuses where the unit is generating in-place revenue.
_PAYING = {"Occupied", "Notice", "MTM"}
# Statuses where the unit is leased (incl. signed-not-yet-occupied).
_LEASED = {"Occupied", "Notice", "SNO", "MTM"}


@dataclass
class Unit:
    unit: str
    unit_type: str
    sqft: float
    status: str
    tenant: str
    in_place_rent: float
    market_rent: float
    lease_start: date | None
    lease_end: date | None

    @property
    def is_paying(self) -> bool:
        return self.status in _PAYING

    @property
    def is_leased(self) -> bool:
        return self.status in _LEASED

    @property
    def is_vacant(self) -> bool:
        return self.status == "Vacant"


@dataclass
class RentRollAnalysis:
    as_of: date
    total_units: int
    total_sqft: float

    physical_occ_units: float           # 0.0 - 1.0
    physical_occ_sqft: float
    leased_occ_units: float
    economic_occupancy: float

    gpr_annual: float                   # sum(market_rent) * 12 across all units
    in_place_annual: float              # sum(in_place_rent) * 12 across paying units

    ltl_dollars_annual: float           # market - in_place across paying units, annualized
    ltl_pct_of_gpr: float               # ltl_dollars / gpr

    walt_years: float                   # rent-weighted, excludes MTM/expired
    mtm_count: int                      # tenants whose lease has expired
    walt_population_count: int          # tenants with valid future lease_end included in WALT

    by_unit_type: dict                  # unit_type -> dict of metrics
    expiration_ladder: dict             # quarter_label -> {units, sqft, rent}


def _parse_date(s: str) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(s: str) -> float:
    s = (s or "").strip().replace(",", "").replace("$", "")
    return float(s) if s else 0.0


def _normalize_status(s: str) -> str:
    return _STATUS_ALIAS.get((s or "").strip().lower(), (s or "").strip().title())


def parse_csv(path: str, as_of: date) -> list[Unit]:
    """Parse a rent roll CSV into Unit objects. Tenants whose lease_end is
    before as_of and who are in Occupied/Notice status are reclassified to MTM.
    """
    units = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {k.strip().lower(): (v or "").strip() for k, v in raw.items()}
            if not row.get("unit"):
                continue
            lease_end = _parse_date(row.get("lease_end", ""))
            status = _normalize_status(row.get("status", ""))
            # Auto-promote expired Occupied / Notice tenants to MTM.
            if status in ("Occupied", "Notice") and lease_end and lease_end < as_of:
                status = "MTM"
            units.append(Unit(
                unit=row["unit"],
                unit_type=row.get("unit_type", ""),
                sqft=_parse_float(row.get("sqft", "0")),
                status=status,
                tenant=row.get("tenant", ""),
                in_place_rent=_parse_float(row.get("in_place_rent", "0")),
                market_rent=_parse_float(row.get("market_rent", "0")),
                lease_start=_parse_date(row.get("lease_start", "")),
                lease_end=lease_end,
            ))
    return units


def analyze(units: list[Unit], as_of: date) -> RentRollAnalysis:
    if not units:
        raise ValueError("rent roll is empty")

    total_units = len(units)
    total_sqft = sum(u.sqft for u in units)
    paying = [u for u in units if u.is_paying]
    leased = [u for u in units if u.is_leased]

    physical_occ_units = sum(1 for u in units if u.is_paying) / total_units
    physical_occ_sqft = (
        sum(u.sqft for u in units if u.is_paying) / total_sqft
        if total_sqft > 0 else 0.0
    )
    leased_occ_units = sum(1 for u in units if u.is_leased) / total_units

    gpr_annual = sum(u.market_rent for u in units) * 12
    in_place_annual = sum(u.in_place_rent for u in paying) * 12
    economic_occupancy = in_place_annual / gpr_annual if gpr_annual > 0 else 0.0

    ltl_monthly = sum(max(u.market_rent - u.in_place_rent, 0) for u in paying)
    ltl_dollars_annual = ltl_monthly * 12
    ltl_pct_of_gpr = ltl_dollars_annual / gpr_annual if gpr_annual > 0 else 0.0

    # WALT (rent-weighted): only on units with valid future lease_end.
    walt_population = [
        u for u in paying
        if u.status != "MTM" and u.lease_end and u.lease_end >= as_of
    ]
    mtm_count = sum(1 for u in paying if u.status == "MTM" or not u.lease_end)
    walt_population_count = len(walt_population)
    if walt_population and any(u.in_place_rent > 0 for u in walt_population):
        num = sum(
            ((u.lease_end - as_of).days / 365.0) * u.in_place_rent
            for u in walt_population
        )
        denom = sum(u.in_place_rent for u in walt_population)
        walt_years = num / denom if denom > 0 else 0.0
    else:
        walt_years = 0.0

    # By unit type
    by_type: dict[str, dict] = {}
    types = sorted({u.unit_type or "(unspecified)" for u in units})
    for t in types:
        type_units = [u for u in units if (u.unit_type or "(unspecified)") == t]
        type_paying = [u for u in type_units if u.is_paying]
        n = len(type_units)
        n_paying = len(type_paying)
        type_gpr = sum(u.market_rent for u in type_units) * 12
        type_in_place = sum(u.in_place_rent for u in type_paying) * 12
        type_ltl = sum(max(u.market_rent - u.in_place_rent, 0) for u in type_paying) * 12
        by_type[t] = {
            "count":          n,
            "occupancy":      n_paying / n if n else 0.0,
            "avg_market":     (sum(u.market_rent for u in type_units) / n) if n else 0.0,
            "avg_in_place":   (
                sum(u.in_place_rent for u in type_paying) / n_paying
                if n_paying else 0.0
            ),
            "gpr_annual":     type_gpr,
            "in_place_annual": type_in_place,
            "ltl_annual":     type_ltl,
            "ltl_pct_of_gpr": type_ltl / type_gpr if type_gpr > 0 else 0.0,
        }

    # Expiration ladder: rolling 4 quarters from as_of.
    ladder: dict[str, dict] = {}
    for q in range(4):
        q_start = _add_months(as_of, q * 3)
        q_end = _add_months(as_of, (q + 1) * 3) - _one_day()
        label = f"{q_start.strftime('%b-%y')} to {q_end.strftime('%b-%y')}"
        bucket = [
            u for u in paying
            if u.lease_end and q_start <= u.lease_end <= q_end
        ]
        ladder[label] = {
            "units": len(bucket),
            "sqft":  sum(u.sqft for u in bucket),
            "rent_annual": sum(u.in_place_rent for u in bucket) * 12,
        }

    return RentRollAnalysis(
        as_of=as_of,
        total_units=total_units,
        total_sqft=total_sqft,
        physical_occ_units=physical_occ_units,
        physical_occ_sqft=physical_occ_sqft,
        leased_occ_units=leased_occ_units,
        economic_occupancy=economic_occupancy,
        gpr_annual=gpr_annual,
        in_place_annual=in_place_annual,
        ltl_dollars_annual=ltl_dollars_annual,
        ltl_pct_of_gpr=ltl_pct_of_gpr,
        walt_years=walt_years,
        mtm_count=mtm_count,
        walt_population_count=walt_population_count,
        by_unit_type=by_type,
        expiration_ladder=ladder,
    )


def _add_months(d: date, n: int) -> date:
    """Add n months to a date, clamping day-of-month to month length."""
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    # Clamp day to last valid day of target month.
    import calendar
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _one_day():
    from datetime import timedelta
    return timedelta(days=1)


def format_analysis(a: RentRollAnalysis) -> str:
    out = []
    bar = "=" * 72
    out.append(bar)
    out.append(f"RENT ROLL SUMMARY                        As of {a.as_of}")
    out.append(bar)
    out.append(f"Total units:                                   {a.total_units:>15,d}")
    out.append(f"Total SF:                                      {a.total_sqft:>15,.0f}")
    out.append("-" * 72)
    out.append(f"Physical occupancy (by unit):                  {a.physical_occ_units*100:>14.1f}%")
    if a.total_sqft > 0:
        out.append(f"Physical occupancy (by SF):                    {a.physical_occ_sqft*100:>14.1f}%")
    out.append(f"Leased occupancy   (incl. SNO):                {a.leased_occ_units*100:>14.1f}%")
    out.append(f"Economic occupancy (in-place/GPR):             {a.economic_occupancy*100:>14.1f}%")
    out.append("-" * 72)
    out.append(f"GPR (annualized):                              ${a.gpr_annual:>14,.0f}")
    out.append(f"In-place rent (annualized):                    ${a.in_place_annual:>14,.0f}")
    out.append(f"Loss-to-lease (annualized $):                  ${a.ltl_dollars_annual:>14,.0f}")
    out.append(f"Loss-to-lease (% of GPR):                      {a.ltl_pct_of_gpr*100:>14.1f}%")
    out.append("-" * 72)
    if a.walt_population_count > 0:
        out.append(f"WALT (rent-weighted, yrs):                     {a.walt_years:>14.2f}")
        out.append(f"  Based on {a.walt_population_count} leases with future expirations")
    if a.mtm_count > 0:
        out.append(f"MTM / expired leases:                          {a.mtm_count:>15d} units")
    out.append(bar)

    if a.by_unit_type:
        out.append("BY UNIT TYPE")
        out.append("-" * 72)
        out.append(f"{'Type':<10} {'Units':>6} {'Occ':>7} {'Avg Mkt':>9} {'Avg In-Pl':>10} {'LTL %':>7}")
        for t, m in a.by_unit_type.items():
            out.append(
                f"{t:<10} {m['count']:>6d} {m['occupancy']*100:>6.1f}% "
                f"${m['avg_market']:>7,.0f} ${m['avg_in_place']:>8,.0f} "
                f"{m['ltl_pct_of_gpr']*100:>6.1f}%"
            )
        out.append(bar)

    if any(b["units"] for b in a.expiration_ladder.values()):
        out.append("EXPIRATION LADDER (next 12 months)")
        out.append("-" * 72)
        out.append(f"{'Quarter':<25} {'Units':>6} {'SF':>10} {'Rent (annual)':>16}")
        for label, b in a.expiration_ladder.items():
            out.append(
                f"{label:<25} {b['units']:>6d} {b['sqft']:>10,.0f} ${b['rent_annual']:>14,.0f}"
            )
        out.append(bar)

    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--csv", required=True, help="Path to rent roll CSV")
    p.add_argument("--as-of", required=True, help="As-of date for occupancy/WALT (YYYY-MM-DD)")
    args = p.parse_args()

    as_of = _parse_date(args.as_of)
    if as_of is None:
        raise SystemExit(f"Could not parse as-of date: {args.as_of}")

    units = parse_csv(args.csv, as_of=as_of)
    analysis = analyze(units, as_of=as_of)
    print(format_analysis(analysis))


if __name__ == "__main__":
    main()
