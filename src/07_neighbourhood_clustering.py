"""
Neighbourhood clustering analysis for Edmonton construction permits.

Groups neighbourhoods by development profile using K-means clustering on:
- permit volume (how active)
- units added (how much housing)
- construction value (how expensive)
- value per unit (what kind of development)

Outputs:
- docs/figures/cluster_profiles.png  (bar charts showing each cluster's mean features)
- docs/figures/cluster_scatter.png   (scatter plot: units added vs construction value)
- data/exports/neighbourhood_clusters.csv
"""

from __future__ import annotations
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from adjustText import adjust_text

INPUT_PATH = Path("data/exports/neighbourhood_summary.csv")
EXPORT_PATH = Path("data/exports/neighbourhood_clusters.csv")
FIGURES_DIR = Path("docs/figures")

N_CLUSTERS = 3
RANDOM_STATE = 42


def load_and_engineer(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Drop unknowns and low-activity neighbourhoods (< 50 permits — likely data noise)
    df = df[~df["neighbourhood_std"].isin(["UNKNOWN", "NAN", ""])]
    df = df[df["permit_count"] >= 50].copy()

    # Drop neighbourhoods with negligible residential activity
    df = df[df["total_units_added"] >= 10].copy()

    # Feature engineering
    df["value_per_unit"] = np.where(
        df["total_units_added"] > 0,
        df["total_construction_value"] / df["total_units_added"],
        0,
    )

    return df


def find_optimal_k(X_scaled: np.ndarray, max_k: int = 8) -> None:
    """Print silhouette scores to help validate cluster count choice."""
    print("Silhouette scores by k:")
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        print(f"  k={k}: {score:.3f}")


def label_cluster(row: pd.Series) -> str:
    """Assign a human-readable label based on cluster mean profile."""
    # Labels are assigned after inspecting cluster means — see print output
    labels = {
        0: "Emerging Suburban Areas",
        1: "Major Residential Growth Corridors",
        2: "High-Value Established Areas",
    }
    return labels.get(row["cluster"], f"Cluster {row['cluster']}")


def plot_profiles(df: pd.DataFrame, features: list[str], out_path: Path) -> None:
    cluster_means = df.groupby("cluster")[features].mean()

    fig, axes = plt.subplots(1, len(features), figsize=(14, 4))
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    feature_labels = [
        "Permit Count",
        "Units Added",
        "Construction Value ($)",
        "Value per Unit ($)",
    ]

    for ax, feat, label in zip(axes, features, feature_labels):
        ax.bar(
            [f"C{i}" for i in cluster_means.index],
            cluster_means[feat],
            color=colors[: len(cluster_means)],
        )
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Cluster")
        ax.tick_params(axis="x", labelsize=9)

    fig.suptitle("Neighbourhood Cluster Profiles — Mean Feature Values", fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved cluster profiles -> {out_path}")


def plot_scatter(df: pd.DataFrame, out_path: Path) -> None:
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    cluster_names = df.groupby("cluster")["cluster_label"].first()

    fig, ax = plt.subplots(figsize=(10, 7))

    for cluster_id, group in df.groupby("cluster"):
        ax.scatter(
            group["total_units_added"],
            group["total_construction_value"] / 1e6,
            c=colors[cluster_id],
            label=f"Cluster {cluster_id}: {cluster_names[cluster_id]}",
            alpha=0.7,
            s=60,
        )

    # Annotate top neighbourhoods
    top = df.nlargest(8, "total_units_added")
    texts = []
    for _, row in top.iterrows():
        texts.append(ax.text(
            row["total_units_added"],
            row["total_construction_value"] / 1e6,
            row["neighbourhood_std"].title(),
            fontsize=8,
        ))
    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color="gray", lw=0.5))

    ax.set_xlabel("Total Units Added", fontsize=11)
    ax.set_ylabel("Total Construction Value ($M)", fontsize=11)
    ax.set_title("Edmonton Neighbourhoods by Development Profile", fontsize=13)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved cluster scatter -> {out_path}")


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"{INPUT_PATH} not found. Run src/05_export_dashboard_tables.py first."
        )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = load_and_engineer(INPUT_PATH)
    print(f"Neighbourhoods after filtering: {len(df)}")

    features = ["permit_count", "total_units_added", "total_construction_value", "value_per_unit"]
    X = df[features].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Validate cluster count
    find_optimal_k(X_scaled)

    # Fit final model
    km = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    df["cluster"] = km.fit_predict(X_scaled)

    # Print cluster means so you can verify label assignments
    print("\nCluster means (unscaled):")
    print(df.groupby("cluster")[features].mean().round(0).to_string())

    # Print top 5 neighbourhoods per cluster
    print("\nTop neighbourhoods per cluster:")
    for cluster_id, group in df.groupby("cluster"):
        top5 = group.nlargest(5, "total_units_added")["neighbourhood_std"].tolist()
        print(f"  Cluster {cluster_id}: {', '.join(top5)}")

    df["cluster_label"] = df.apply(label_cluster, axis=1)

    # Plots
    plot_profiles(df, features, FIGURES_DIR / "cluster_profiles.png")
    plot_scatter(df, FIGURES_DIR / "cluster_scatter.png")

    # Export
    out = df[["neighbourhood_std", "permit_count", "total_units_added",
              "total_construction_value", "value_per_unit", "cluster", "cluster_label"]]
    out.to_csv(EXPORT_PATH, index=False)
    print(f"\nExported cluster assignments -> {EXPORT_PATH}")
    print(f"Total neighbourhoods clustered: {len(df)}")


if __name__ == "__main__":
    main()