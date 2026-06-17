"""Export dashboard-ready tables from the SQLite database."""

from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data/processed/edmonton_construction.db")
EXPORT_DIR = Path("data/exports")


def export_query(conn: sqlite3.Connection, query: str, filename: str) -> None:
    df = pd.read_sql_query(query, conn)
    out_path = EXPORT_DIR / filename
    df.to_csv(out_path, index=False)
    print(f"Exported {len(df):,} rows -> {out_path}")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"{DB_PATH} not found. Run src/04_load_sqlite.py first."
        )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        # 1. Main detail table for dashboard filters and maps
        export_query(
            conn,
            """
            SELECT
                permit_date,
                CAST(year AS INTEGER) AS year,
                CAST(month AS INTEGER) AS month,
                year_month,
                permit_type_std,
                neighbourhood_std,
                zoning_std,
                units_added_num,
                construction_value_num,
                latitude_num,
                longitude_num
            FROM building_permits
            WHERE permit_date IS NOT NULL
            """,
            "dashboard_permits_detail.csv",
        )

        # 2. Completed yearly trend
        export_query(
            conn,
            """
            WITH bounds AS (
                SELECT CAST(strftime('%Y', MAX(permit_date)) AS INTEGER) AS partial_year
                FROM building_permits
            )
            SELECT
                CAST(year AS INTEGER) AS year,
                COUNT(*) AS permit_count,
                COALESCE(SUM(units_added_num), 0) AS total_units_added,
                COALESCE(SUM(construction_value_num), 0) AS total_construction_value
            FROM building_permits
            WHERE year IS NOT NULL
              AND CAST(year AS INTEGER) < (SELECT partial_year FROM bounds)
            GROUP BY CAST(year AS INTEGER)
            ORDER BY year
            """,
            "yearly_trends_completed.csv",
        )

        # 3. Completed monthly trend with rolling average
        export_query(
            conn,
            """
            WITH bounds AS (
                SELECT MAX(year_month) AS partial_month
                FROM building_permits
                WHERE year_month IS NOT NULL
                  AND year_month != 'NaT'
            ),
            monthly AS (
                SELECT
                    year_month,
                    COUNT(*) AS permit_count,
                    COALESCE(SUM(units_added_num), 0) AS total_units_added,
                    COALESCE(SUM(construction_value_num), 0) AS total_construction_value
                FROM building_permits
                WHERE year_month IS NOT NULL
                  AND year_month != 'NaT'
                  AND year_month < (SELECT partial_month FROM bounds)
                GROUP BY year_month
            )
            SELECT
                year_month,
                permit_count,
                total_units_added,
                total_construction_value,
                LAG(permit_count) OVER (ORDER BY year_month) AS previous_month_count,
                permit_count - LAG(permit_count) OVER (ORDER BY year_month) AS month_over_month_change,
                ROUND(
                    AVG(permit_count) OVER (
                        ORDER BY year_month
                        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
                    ),
                    2
                ) AS rolling_12_month_avg
            FROM monthly
            ORDER BY year_month
            """,
            "monthly_trends_completed.csv",
        )

        # 4. Neighbourhood summary
        export_query(
            conn,
            """
            SELECT
                neighbourhood_std,
                COUNT(*) AS permit_count,
                COALESCE(SUM(units_added_num), 0) AS total_units_added,
                COALESCE(SUM(construction_value_num), 0) AS total_construction_value
            FROM building_permits
            WHERE neighbourhood_std IS NOT NULL
              AND neighbourhood_std NOT IN ('UNKNOWN', 'NAN', '')
            GROUP BY neighbourhood_std
            ORDER BY permit_count DESC
            """,
            "neighbourhood_summary.csv",
        )

        # 5. Permit type summary
        export_query(
            conn,
            """
            SELECT
                permit_type_std,
                COUNT(*) AS permit_count,
                MIN(permit_date) AS earliest_permit_date,
                MAX(permit_date) AS latest_permit_date,
                COALESCE(SUM(units_added_num), 0) AS total_units_added,
                COALESCE(SUM(construction_value_num), 0) AS total_construction_value
            FROM building_permits
            WHERE permit_type_std IS NOT NULL
              AND permit_type_std NOT IN ('UNKNOWN', 'NAN', '')
            GROUP BY permit_type_std
            ORDER BY permit_count DESC
            """,
            "permit_type_summary.csv",
        )

        # 6. Zoning summary
        export_query(
            conn,
            """
            SELECT
                zoning_std,
                COUNT(*) AS permit_count,
                COALESCE(SUM(units_added_num), 0) AS total_units_added,
                COALESCE(SUM(construction_value_num), 0) AS total_construction_value
            FROM building_permits
            WHERE zoning_std IS NOT NULL
              AND zoning_std NOT IN ('UNKNOWN', 'NAN', '')
            GROUP BY zoning_std
            ORDER BY permit_count DESC
            """,
            "zoning_summary.csv",
        )

        # 7. Completed-year neighbourhood YoY growth
        export_query(
            conn,
            """
            WITH bounds AS (
                SELECT CAST(strftime('%Y', MAX(permit_date)) AS INTEGER) AS partial_year
                FROM building_permits
            ),
            complete_years AS (
                SELECT *
                FROM building_permits
                WHERE year IS NOT NULL
                  AND CAST(year AS INTEGER) < (SELECT partial_year FROM bounds)
                  AND neighbourhood_std IS NOT NULL
                  AND neighbourhood_std NOT IN ('UNKNOWN', 'NAN', '')
            ),
            latest_complete_year AS (
                SELECT MAX(CAST(year AS INTEGER)) AS latest_year
                FROM complete_years
            ),
            yearly AS (
                SELECT
                    neighbourhood_std,
                    CAST(year AS INTEGER) AS yr,
                    COUNT(*) AS permit_count
                FROM complete_years
                GROUP BY neighbourhood_std, CAST(year AS INTEGER)
            ),
            growth AS (
                SELECT
                    y.neighbourhood_std,
                    ly.latest_year AS latest_complete_year,
                    ly.latest_year - 1 AS previous_year,
                    SUM(CASE WHEN y.yr = ly.latest_year THEN y.permit_count ELSE 0 END) AS latest_year_permits,
                    SUM(CASE WHEN y.yr = ly.latest_year - 1 THEN y.permit_count ELSE 0 END) AS previous_year_permits
                FROM yearly y
                CROSS JOIN latest_complete_year ly
                GROUP BY y.neighbourhood_std, ly.latest_year
            )
            SELECT
                neighbourhood_std,
                latest_complete_year,
                latest_year_permits,
                previous_year,
                previous_year_permits,
                latest_year_permits - previous_year_permits AS permit_change,
                CASE
                    WHEN previous_year_permits = 0 THEN NULL
                    ELSE ROUND(
                        100.0 * (latest_year_permits - previous_year_permits) / previous_year_permits,
                        2
                    )
                END AS percent_change
            FROM growth
            ORDER BY permit_change DESC
            """,
            "neighbourhood_yoy_growth_completed.csv",
        )

        # 8. Seasonality summary
        export_query(
            conn,
            """
            WITH bounds AS (
                SELECT CAST(strftime('%Y', MAX(permit_date)) AS INTEGER) AS partial_year
                FROM building_permits
            )
            SELECT
                CAST(month AS INTEGER) AS month,
                COUNT(*) AS permit_count,
                ROUND(AVG(units_added_num), 2) AS avg_units_added,
                COALESCE(SUM(units_added_num), 0) AS total_units_added
            FROM building_permits
            WHERE month IS NOT NULL
              AND year IS NOT NULL
              AND CAST(year AS INTEGER) < (SELECT partial_year FROM bounds)
            GROUP BY CAST(month AS INTEGER)
            ORDER BY month
            """,
            "seasonality_completed_years.csv",
        )


if __name__ == "__main__":
    main()
