"""Inspect raw building permit data before cleaning."""

from __future__ import annotations
from pathlib import Path
import pandas as pd

RAW_PATH = Path("data/raw/building_permits_raw.csv")
OUT_DIR = Path("docs")
PROFILE_PATH = OUT_DIR / "raw_column_profile.csv"


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_PATH} not found. Run src/01_extract_permits.py first."
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_PATH, low_memory=False)

    print("Shape:", df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 rows:")
    print(df.head())

    profile = []

    for col in df.columns:
        sample_values = (
            df[col]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .head(5)
            .tolist()
        )

        profile.append(
            {
                "column": col,
                "dtype": str(df[col].dtype),
                "missing_count": int(df[col].isna().sum()),
                "missing_pct": round(float(df[col].isna().mean() * 100), 2),
                "n_unique": int(df[col].nunique(dropna=True)),
                "sample_values": ", ".join(sample_values),
            }
        )

    pd.DataFrame(profile).to_csv(PROFILE_PATH, index=False)

    print(f"\nSaved column profile to {PROFILE_PATH}")


if __name__ == "__main__":
    main()