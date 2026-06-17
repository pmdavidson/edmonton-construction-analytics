"""
Download City of Edmonton General Building Permits data.

Dataset:
https://data.edmonton.ca/resource/24uj-dj8v.json

This script uses Socrata pagination and saves the raw data to CSV.
"""

from __future__ import annotations
import time
from pathlib import Path
import pandas as pd
import requests

DATASET_URL = "https://data.edmonton.ca/resource/24uj-dj8v.json"
RAW_OUT = Path("data/raw/building_permits_raw.csv")
METADATA_OUT = Path("docs/raw_columns.txt")
LIMIT = 50000


def fetch_all_rows() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    offset = 0

    while True:
        params = {"$limit": LIMIT, "$offset": offset}
        print(f"Fetching rows {offset:,} to {offset + LIMIT:,}...")

        response = requests.get(DATASET_URL, params=params, timeout=60)
        response.raise_for_status()

        rows = response.json()

        if not rows:
            break

        frames.append(pd.DataFrame(rows))

        if len(rows) < LIMIT:
            break

        offset += LIMIT
        time.sleep(0.2)

    if not frames:
        raise RuntimeError("No rows returned from the API.")

    return pd.concat(frames, ignore_index=True)


def main() -> None:
    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    METADATA_OUT.parent.mkdir(parents=True, exist_ok=True)

    df = fetch_all_rows()

    df.to_csv(RAW_OUT, index=False)
    METADATA_OUT.write_text("\n".join(df.columns), encoding="utf-8")

    print(f"Saved {len(df):,} rows to {RAW_OUT}")
    print(f"Saved raw column list to {METADATA_OUT}")

    print("\nColumns:")
    for col in df.columns:
        print(f"- {col}")


if __name__ == "__main__":
    main()