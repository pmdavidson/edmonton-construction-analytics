.headers on
.mode column

-- ============================================================
-- Core SQL analysis for Edmonton Construction & Housing Activity Intelligence
-- Database: data/processed/edmonton_construction.db
-- Table: building_permits
-- ============================================================


-- 1. Dataset size
SELECT
    COUNT(*) AS total_rows
FROM building_permits;


-- 2. Date coverage
SELECT
    MIN(permit_date) AS earliest_permit_date,
    MAX(permit_date) AS latest_permit_date,
    strftime('%Y', MAX(permit_date)) AS latest_year_in_data,
    strftime('%Y-%m', MAX(permit_date)) AS latest_month_in_data
FROM building_permits;


-- 3. Yearly trend, including partial current year
-- Use this for data coverage, but not for final YoY conclusions.
SELECT
    CAST(year AS INTEGER) AS year,
    COUNT(*) AS permit_count,
    COALESCE(SUM(units_added_num), 0) AS total_units_added,
    COALESCE(SUM(construction_value_num), 0) AS total_construction_value
FROM building_permits
WHERE year IS NOT NULL
GROUP BY CAST(year AS INTEGER)
ORDER BY year;


-- 4. Yearly trend, completed years only
-- This excludes the latest year in the dataset because it may be incomplete.
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
ORDER BY year;


-- 5. Monthly trend, excluding latest partial month
WITH bounds AS (
    SELECT MAX(year_month) AS partial_month
    FROM building_permits
    WHERE year_month IS NOT NULL
      AND year_month != 'NaT'
)
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
ORDER BY year_month;


-- 6. Top 20 neighbourhoods by permit count
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
LIMIT 20;


-- 7. Top 20 neighbourhoods by units added
SELECT
    neighbourhood_std,
    COUNT(*) AS permit_count,
    COALESCE(SUM(units_added_num), 0) AS total_units_added,
    COALESCE(SUM(construction_value_num), 0) AS total_construction_value
FROM building_permits
WHERE neighbourhood_std IS NOT NULL
  AND neighbourhood_std NOT IN ('UNKNOWN', 'NAN', '')
GROUP BY neighbourhood_std
ORDER BY total_units_added DESC
LIMIT 20;


-- 8. Permit type breakdown
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
ORDER BY permit_count DESC;


-- 9. Neighbourhood YoY growth using completed years only
-- If the dataset includes partial 2026, this compares 2025 vs 2024.
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
LIMIT 20;


-- 10. Month-over-month permit change, excluding latest partial month
WITH bounds AS (
    SELECT MAX(year_month) AS partial_month
    FROM building_permits
    WHERE year_month IS NOT NULL
      AND year_month != 'NaT'
),
monthly AS (
    SELECT
        year_month,
        COUNT(*) AS permit_count
    FROM building_permits
    WHERE year_month IS NOT NULL
      AND year_month != 'NaT'
      AND year_month < (SELECT partial_month FROM bounds)
    GROUP BY year_month
)
SELECT
    year_month,
    permit_count,
    LAG(permit_count) OVER (ORDER BY year_month) AS previous_month_count,
    permit_count - LAG(permit_count) OVER (ORDER BY year_month) AS month_over_month_change
FROM monthly
ORDER BY year_month;


-- 11. Rolling 12-month permit average, excluding latest partial month
WITH bounds AS (
    SELECT MAX(year_month) AS partial_month
    FROM building_permits
    WHERE year_month IS NOT NULL
      AND year_month != 'NaT'
),
monthly AS (
    SELECT
        year_month,
        COUNT(*) AS permit_count
    FROM building_permits
    WHERE year_month IS NOT NULL
      AND year_month != 'NaT'
      AND year_month < (SELECT partial_month FROM bounds)
    GROUP BY year_month
)
SELECT
    year_month,
    permit_count,
    ROUND(
        AVG(permit_count) OVER (
            ORDER BY year_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_12_month_avg
FROM monthly
ORDER BY year_month;


-- 12. Seasonality by calendar month, completed years only
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
ORDER BY month;
