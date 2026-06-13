"""Inspect raw building permit data before cleaning."""

from __future__ import annotations
from pathlib import Path
import pandas as pd

RAW_PATH = Path("data/raw/building_permits_raw.csv")
OUT_DIR = Path("docs")


def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"{RAW_PATH} not found. Run src/01_extract_permits.py first.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW_PATH, low_memory=False)
    print("Shape:", df.shape)
    print("
Columns:")
    print(df.columns.tolist())
    print("
First 5 rows:")
    print(df.head())
    profile = []
    for col in df.columns:
        profile.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "missing_pct": round(float(df[col].isna().mean() * 100), 2),
            "n_unique": int(df[col].nunique(dropna=True)),
            "sample_values": ", ".join(map(str, df[col].dropna().astype(str).unique()[:5])),
        })
    pd.DataFrame(profile).to_csv(OUT_DIR / "raw_column_profile.csv", index=False)
    print(f"
Saved column profile to {OUT_DIR / 'raw_column_profile.csv'}")


if __name__ == "__main__":
    main()
