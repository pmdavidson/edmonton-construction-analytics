"""Generate EDA charts for the Edmonton construction analytics project."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

EXPORT_DIR = Path("data/exports")
FIGURE_DIR = Path("docs/figures")


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run src/05_export_dashboard_tables.py first."
        )


def save_current_figure(filename: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURE_DIR / filename
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved {out_path}")


def plot_yearly_permit_count() -> None:
    path = EXPORT_DIR / "yearly_trends_completed.csv"
    require_file(path)

    df = pd.read_csv(path)

    plt.figure(figsize=(10, 6))
    plt.bar(df["year"], df["permit_count"])
    plt.title("Edmonton Building Permit Count by Year")
    plt.xlabel("Year")
    plt.ylabel("Permit Count")
    plt.xticks(df["year"], rotation=45)
    save_current_figure("yearly_permit_count.png")


def plot_yearly_units_added() -> None:
    path = EXPORT_DIR / "yearly_trends_completed.csv"
    require_file(path)

    df = pd.read_csv(path)

    plt.figure(figsize=(10, 6))
    plt.bar(df["year"], df["total_units_added"])
    plt.title("Total Housing Units Added by Year")
    plt.xlabel("Year")
    plt.ylabel("Total Units Added")
    plt.xticks(df["year"], rotation=45)
    save_current_figure("yearly_units_added.png")


def plot_monthly_permit_trend() -> None:
    path = EXPORT_DIR / "monthly_trends_completed.csv"
    require_file(path)

    df = pd.read_csv(path)
    df["year_month"] = pd.to_datetime(df["year_month"])

    plt.figure(figsize=(12, 6))
    plt.plot(df["year_month"], df["permit_count"], label="Monthly Permit Count")
    plt.plot(df["year_month"], df["rolling_12_month_avg"], label="12-Month Rolling Average")
    plt.title("Monthly Building Permit Trend")
    plt.xlabel("Month")
    plt.ylabel("Permit Count")
    plt.legend()
    save_current_figure("monthly_permit_trend.png")


def plot_top_neighbourhoods_by_units() -> None:
    path = EXPORT_DIR / "neighbourhood_summary.csv"
    require_file(path)

    df = pd.read_csv(path)
    top = df.sort_values("total_units_added", ascending=False).head(15)
    top = top.sort_values("total_units_added", ascending=True)

    plt.figure(figsize=(10, 7))
    plt.barh(top["neighbourhood_std"], top["total_units_added"])
    plt.title("Top Neighbourhoods by Total Units Added")
    plt.xlabel("Total Units Added")
    plt.ylabel("Neighbourhood")
    save_current_figure("top_neighbourhoods_by_units.png")


def plot_top_permit_types() -> None:
    path = EXPORT_DIR / "permit_type_summary.csv"
    require_file(path)

    df = pd.read_csv(path)
    top = df.sort_values("permit_count", ascending=False).head(10)
    top = top.sort_values("permit_count", ascending=True)

    plt.figure(figsize=(10, 7))
    plt.barh(top["permit_type_std"], top["permit_count"])
    plt.title("Top Permit Types by Permit Count")
    plt.xlabel("Permit Count")
    plt.ylabel("Permit Type")
    save_current_figure("top_permit_types.png")


def plot_seasonality() -> None:
    path = EXPORT_DIR / "seasonality_completed_years.csv"
    require_file(path)

    df = pd.read_csv(path)

    plt.figure(figsize=(10, 6))
    plt.bar(df["month"], df["permit_count"])
    plt.title("Permit Seasonality by Calendar Month")
    plt.xlabel("Month")
    plt.ylabel("Permit Count")
    plt.xticks(df["month"])
    save_current_figure("permit_seasonality.png")


def main() -> None:
    plot_yearly_permit_count()
    plot_yearly_units_added()
    plot_monthly_permit_trend()
    plot_top_neighbourhoods_by_units()
    plot_top_permit_types()
    plot_seasonality()

    print("\nEDA chart generation complete.")


if __name__ == "__main__":
    main()
