"""Clean City of Edmonton building permit data.

The raw dataset column names can change over time. This script:
- normalizes column names to snake_case
- tries to infer important standard columns
- creates dashboard/SQL-friendly fields
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/building_permits_raw.csv")
CLEAN_OUT = Path("data/processed/building_permits_clean.csv")
DICTIONARY_OUT = Path("docs/cleaned_data_dictionary.csv")


def snake_case(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def first_existing(columns: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def clean_currency_or_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.extract(r"([-+]?\d*\.?\d+)", expand=False),
        errors="coerce",
    )


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_PATH} not found. Run src/01_extract_permits.py first."
        )

    CLEAN_OUT.parent.mkdir(parents=True, exist_ok=True)
    DICTIONARY_OUT.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_PATH, low_memory=False)
    df.columns = [snake_case(c) for c in df.columns]
    cols = df.columns.tolist()

    date_col = first_existing(
        cols,
        [
            "issue_date",
            "issued_date",
            "permit_date",
            "date_issued",
            "created_date",
            "application_date",
        ],
    )

    permit_type_col = first_existing(
        cols,
        [
            "permit_type",
            "type",
            "permit_class",
            "work_type",
            "building_type",
        ],
    )

    neighbourhood_col = first_existing(
        cols,
        [
            "neighbourhood",
            "neighborhood",
            "neighbourhood_name",
            "neighborhood_name",
        ],
    )

    zoning_col = first_existing(
        cols,
        [
            "zoning",
            "zone",
            "land_use_zone",
        ],
    )

    units_col = first_existing(
        cols,
        [
            "units_added",
            "dwelling_units_added",
            "units",
            "new_units",
            "number_of_units",
        ],
    )

    value_col = first_existing(
        cols,
        [
            "construction_value",
            "job_value",
            "project_value",
            "estimated_value",
            "value",
        ],
    )

    description_col = first_existing(
        cols,
        [
            "description",
            "work_description",
            "scope_of_work",
            "permit_description",
        ],
    )

    lat_col = first_existing(cols, ["latitude", "lat", "y"])
    lon_col = first_existing(cols, ["longitude", "lon", "long", "x"])

    clean = df.copy()

    clean["permit_date"] = (
        pd.to_datetime(clean[date_col], errors="coerce") if date_col else pd.NaT
    )
    clean["year"] = clean["permit_date"].dt.year
    clean["month"] = clean["permit_date"].dt.month
    clean["year_month"] = clean["permit_date"].dt.to_period("M").astype(str)

    clean["permit_type_std"] = (
        clean[permit_type_col].astype(str).str.strip().str.upper()
        if permit_type_col
        else "UNKNOWN"
    )

    clean["neighbourhood_std"] = (
        clean[neighbourhood_col].astype(str).str.strip().str.upper()
        if neighbourhood_col
        else "UNKNOWN"
    )

    clean["zoning_std"] = (
        clean[zoning_col].astype(str).str.strip().str.upper()
        if zoning_col
        else "UNKNOWN"
    )

    clean["work_description_std"] = (
        clean[description_col].astype(str).str.strip()
        if description_col
        else ""
    )

    clean["units_added_num"] = (
        clean_currency_or_number(clean[units_col])
        if units_col
        else pd.Series([pd.NA] * len(clean))
    )

    clean["construction_value_num"] = (
        clean_currency_or_number(clean[value_col])
        if value_col
        else pd.Series([pd.NA] * len(clean))
    )

    clean["latitude_num"] = (
        pd.to_numeric(clean[lat_col], errors="coerce") if lat_col else pd.NA
    )

    clean["longitude_num"] = (
        pd.to_numeric(clean[lon_col], errors="coerce") if lon_col else pd.NA
    )

    clean.to_csv(CLEAN_OUT, index=False)

    dictionary = pd.DataFrame(
        [
            {
                "standard_column": "permit_date",
                "source_column": date_col,
                "description": "Standardized permit/application/issue date",
            },
            {
                "standard_column": "permit_type_std",
                "source_column": permit_type_col,
                "description": "Standardized permit/building/work type",
            },
            {
                "standard_column": "neighbourhood_std",
                "source_column": neighbourhood_col,
                "description": "Standardized neighbourhood name",
            },
            {
                "standard_column": "zoning_std",
                "source_column": zoning_col,
                "description": "Standardized zoning field",
            },
            {
                "standard_column": "units_added_num",
                "source_column": units_col,
                "description": "Numeric units added",
            },
            {
                "standard_column": "construction_value_num",
                "source_column": value_col,
                "description": "Numeric estimated construction/project value",
            },
            {
                "standard_column": "work_description_std",
                "source_column": description_col,
                "description": "Standardized work description",
            },
            {
                "standard_column": "latitude_num",
                "source_column": lat_col,
                "description": "Numeric latitude",
            },
            {
                "standard_column": "longitude_num",
                "source_column": lon_col,
                "description": "Numeric longitude",
            },
        ]
    )

    dictionary.to_csv(DICTIONARY_OUT, index=False)

    print(f"Saved cleaned data to {CLEAN_OUT}")
    print(f"Saved cleaned data dictionary to {DICTIONARY_OUT}")

    print("\nStandardized column mapping:")
    print(dictionary.to_string(index=False))

    print("\nCleaned shape:", clean.shape)


if __name__ == "__main__":
    main()
