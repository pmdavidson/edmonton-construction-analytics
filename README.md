# Edmonton Construction & Housing Activity Intelligence

A reproducible analytics project using City of Edmonton building permit open data to analyze construction activity, housing growth, neighbourhood trends, and permit patterns over time.

## Goal

Answer:

> Where is Edmonton's construction and housing activity growing, and what types of development are driving it?

## Why this project matters

This project is designed for data analyst / data science internship applications. It demonstrates:

- Python data ingestion and cleaning
- SQL analysis with time-series and ranking queries
- A reproducible pipeline
- Dashboard-ready export tables
- Civic/open-data analysis
- Construction and housing domain relevance

## Data source

City of Edmonton Open Data: General Building Permits  
Dataset ID: `24uj-dj8v`

The starter code pulls from the Socrata API endpoint:

```text
https://data.edmonton.ca/resource/24uj-dj8v.json
```

## Project structure

```text
edmonton_construction_analytics_starter/
  data/
    raw/               # raw downloaded data
    processed/         # cleaned files and SQLite database
    exports/           # dashboard-ready summary tables
  docs/                # data dictionary, notes, findings
  notebooks/           # exploratory notebooks
  sql/                 # SQL analysis queries
  src/                 # reusable Python scripts
  dashboard/           # Power BI/Tableau files or screenshots
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt

python src/01_extract_permits.py
python src/02_inspect_raw.py
python src/03_clean_permits.py
python src/04_load_sqlite.py
python src/05_export_dashboard_tables.py
```

## Recommended workflow

1. Run extraction.
2. Inspect raw columns.
3. Run cleaning.
4. Load SQLite database.
5. Run SQL queries in `sql/01_core_analysis.sql`.
6. Build a dashboard from the exported CSVs in `data/exports/`.
7. Write final findings in this README.

## Initial analysis questions

- How has Edmonton building permit volume changed since 2009?
- Which neighbourhoods have the highest recent construction activity?
- Which neighbourhoods are adding the most units?
- What permit types are growing or declining?
- Is construction activity seasonal?
- Which areas show accelerating construction growth?
- What are the limitations of using issued permits as a proxy for real construction activity?

## Planned dashboard pages

1. **Overview**
   - Total permits
   - Total units added
   - Year-over-year permit change
   - Top permit type

2. **Neighbourhood Growth**
   - Top neighbourhoods by permits
   - Top neighbourhoods by units added
   - Map, if coordinates are available

3. **Time Trends**
   - Monthly permit volume
   - Rolling 12-month average
   - Seasonal patterns

4. **Permit Type / Zoning**
   - Permit category breakdown
   - Zoning/category filters

## Limitations to mention later

- Dataset contains issued building permits, not necessarily completed construction.
- Some fields may be missing or inconsistent over time.
- Permit descriptions may require text cleaning.
- Applicant information is not included for privacy.
- Neighbourhood boundaries/demographics may require a separate join.

## Final deliverables

- Clean GitHub repository
- Reproducible pipeline
- SQL analysis file
- Dashboard screenshots or public dashboard link
- README with findings and limitations
