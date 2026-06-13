-- Core SQL analysis for Edmonton Construction & Housing Activity Intelligence
-- Run these against data/processed/edmonton_construction.db
-- Table: building_permits

SELECT COUNT(*) AS total_rows
FROM building_permits;

SELECT
    year,
    COUNT(*) AS permit_count,
    SUM(units_added_num) AS total_units_added,
    SUM(construction_value_num) AS total_construction_value
FROM building_permits
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;

SELECT
    year_month,
    COUNT(*) AS permit_count,
    SUM(units_added_num) AS total_units_added,
    SUM(construction_value_num) AS total_construction_value
FROM building_permits
WHERE year_month IS NOT NULL
GROUP BY year_month
ORDER BY year_month;

SELECT
    neighbourhood_std,
    COUNT(*) AS permit_count,
    SUM(units_added_num) AS total_units_added,
    SUM(construction_value_num) AS total_construction_value
FROM building_permits
WHERE neighbourhood_std IS NOT NULL
  AND neighbourhood_std != 'UNKNOWN'
GROUP BY neighbourhood_std
ORDER BY permit_count DESC
LIMIT 20;

SELECT
    neighbourhood_std,
    COUNT(*) AS permit_count,
    SUM(units_added_num) AS total_units_added
FROM building_permits
WHERE neighbourhood_std IS NOT NULL
  AND neighbourhood_std != 'UNKNOWN'
GROUP BY neighbourhood_std
ORDER BY total_units_added DESC
LIMIT 20;

SELECT
    permit_type_std,
    COUNT(*) AS permit_count,
    SUM(units_added_num) AS total_units_added,
    SUM(construction_value_num) AS total_construction_value
FROM building_permits
WHERE permit_type_std IS NOT NULL
  AND permit_type_std != 'UNKNOWN'
GROUP BY permit_type_std
ORDER BY permit_count DESC;

WITH yearly AS (
    SELECT
        neighbourhood_std,
        year,
        COUNT(*) AS permit_count,
        SUM(units_added_num) AS total_units_added
    FROM building_permits
    WHERE year IS NOT NULL
      AND neighbourhood_std IS NOT NULL
      AND neighbourhood_std != 'UNKNOWN'
    GROUP BY neighbourhood_std, year
),
latest_year AS (
    SELECT MAX(year) AS max_year FROM yearly
)
SELECT
    y.neighbourhood_std,
    SUM(CASE WHEN y.year = ly.max_year THEN y.permit_count ELSE 0 END) AS latest_year_permits,
    SUM(CASE WHEN y.year = ly.max_year - 1 THEN y.permit_count ELSE 0 END) AS previous_year_permits,
    SUM(CASE WHEN y.year = ly.max_year THEN y.permit_count ELSE 0 END)
      - SUM(CASE WHEN y.year = ly.max_year - 1 THEN y.permit_count ELSE 0 END) AS permit_change
FROM yearly y
CROSS JOIN latest_year ly
GROUP BY y.neighbourhood_std
ORDER BY permit_change DESC
LIMIT 20;

WITH monthly AS (
    SELECT
        year_month,
        COUNT(*) AS permit_count
    FROM building_permits
    WHERE year_month IS NOT NULL
    GROUP BY year_month
)
SELECT
    year_month,
    permit_count,
    LAG(permit_count) OVER (ORDER BY year_month) AS previous_month_count,
    permit_count - LAG(permit_count) OVER (ORDER BY year_month) AS month_over_month_change
FROM monthly
ORDER BY year_month;

WITH monthly AS (
    SELECT
        year_month,
        COUNT(*) AS permit_count
    FROM building_permits
    WHERE year_month IS NOT NULL
    GROUP BY year_month
)
SELECT
    year_month,
    permit_count,
    AVG(permit_count) OVER (
        ORDER BY year_month
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    ) AS rolling_12_month_avg
FROM monthly
ORDER BY year_month;

SELECT
    month,
    COUNT(*) AS permit_count,
    AVG(units_added_num) AS avg_units_added
FROM building_permits
WHERE month IS NOT NULL
GROUP BY month
ORDER BY month;
