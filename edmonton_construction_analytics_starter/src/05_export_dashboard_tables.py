"""Create dashboard-ready summary CSVs from cleaned permit data."""

from __future__ import annotations
from pathlib import Path
import pandas as pd

CLEAN_PATH = Path("data/processed/building_permits_clean.csv")
EXPORT_DIR = Path("data/exports")


def main() -> None:
    if not CLEAN_PATH.exists():
        raise FileNotFoundError(f"{CLEAN_PATH} not found. Run src/03_clean_permits.py first.")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    df["permit_date"] = pd.to_datetime(df["permit_date"], errors="coerce")
    valid = df[df["permit_date"].notna()].copy()

    monthly = valid.groupby("year_month", dropna=False).agg(
        permit_count=("permit_date", "size"),
        total_units_added=("units_added_num", "sum"),
        total_construction_value=("construction_value_num", "sum"),
    ).reset_index().sort_values("year_month")
    monthly["permit_count_12mo_rolling"] = monthly["permit_count"].rolling(12, min_periods=1).mean()
    monthly.to_csv(EXPORT_DIR / "monthly_permit_trends.csv", index=False)

    neighbourhood = valid.groupby("neighbourhood_std", dropna=False).agg(
        permit_count=("permit_date", "size"),
        total_units_added=("units_added_num", "sum"),
        total_construction_value=("construction_value_num", "sum"),
    ).reset_index().sort_values(["total_units_added", "permit_count"], ascending=False)
    neighbourhood.to_csv(EXPORT_DIR / "neighbourhood_summary.csv", index=False)

    permit_type = valid.groupby("permit_type_std", dropna=False).agg(
        permit_count=("permit_date", "size"),
        total_units_added=("units_added_num", "sum"),
        total_construction_value=("construction_value_num", "sum"),
    ).reset_index().sort_values("permit_count", ascending=False)
    permit_type.to_csv(EXPORT_DIR / "permit_type_summary.csv", index=False)

    neighbourhood_monthly = valid.groupby(["year_month", "neighbourhood_std"], dropna=False).agg(
        permit_count=("permit_date", "size"),
        total_units_added=("units_added_num", "sum"),
        total_construction_value=("construction_value_num", "sum"),
    ).reset_index().sort_values(["year_month", "permit_count"], ascending=[True, False])
    neighbourhood_monthly.to_csv(EXPORT_DIR / "neighbourhood_monthly_summary.csv", index=False)

    print(f"Exported dashboard tables to {EXPORT_DIR}:")
    for file in sorted(EXPORT_DIR.glob("*.csv")):
        print(f"- {file}")


if __name__ == "__main__":
    main()
