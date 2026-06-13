"""Load cleaned permit data into SQLite for SQL analysis."""

from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

CLEAN_PATH = Path("data/processed/building_permits_clean.csv")
DB_PATH = Path("data/processed/edmonton_construction.db")


def main() -> None:
    if not CLEAN_PATH.exists():
        raise FileNotFoundError(f"{CLEAN_PATH} not found. Run src/03_clean_permits.py first.")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("building_permits", conn, if_exists="replace", index=False)
    print(f"Loaded {len(df):,} rows into {DB_PATH}")
    print("Table: building_permits")


if __name__ == "__main__":
    main()
