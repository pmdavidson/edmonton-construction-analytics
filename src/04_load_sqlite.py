"""Load cleaned Edmonton building permit data into SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

CLEAN_PATH = Path("data/processed/building_permits_clean.csv")
DB_PATH = Path("data/processed/edmonton_construction.db")
TABLE_NAME = "building_permits"


def main() -> None:
    if not CLEAN_PATH.exists():
        raise FileNotFoundError(
            f"{CLEAN_PATH} not found. Run src/03_clean_permits.py first."
        )

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(CLEAN_PATH, low_memory=False)

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

        row_count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
        column_count = len(df.columns)

    print(f"Loaded {row_count:,} rows into {DB_PATH}")
    print(f"Table name: {TABLE_NAME}")
    print(f"Columns loaded: {column_count}")


if __name__ == "__main__":
    main()
