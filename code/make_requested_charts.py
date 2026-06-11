from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


TARGET_DISTRICTS = ["大安區", "士林區", "中山區"]
TARGET_TYPES = ["電梯大樓", "公寓", "華廈"]
OUTPUT_DIR = Path("charts")
MEDIAN_REPORT = Path("output/median_check_report.csv")
HOT_SUMMARY_BY_TYPE = Path("output/hot_summary_by_type.csv")


def setup_plot_style() -> None:
    """Configure fonts and chart defaults for Traditional Chinese labels."""
    plt.rcParams["font.sans-serif"] = [
        "Arial Unicode MS",
        "PingFang HK",
        "Heiti TC",
        "STHeiti",
        "Hiragino Sans",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    sns.set_theme(
        style="whitegrid",
        rc={
            "font.sans-serif": plt.rcParams["font.sans-serif"],
            "axes.edgecolor": "#D0D5DD",
            "grid.color": "#EAECF0",
        },
    )


def build_listing_days_summary() -> pd.DataFrame:
    df = pd.read_csv(MEDIAN_REPORT, encoding="utf-8-sig")
    selected = df[df["dist"].isin(TARGET_DISTRICTS)].copy()
    selected["period"] = selected["year"].map(
        lambda year: "2023-25" if year in {2023, 2024, 2025} else "2026 Q1"
    )
    selected = selected[selected["period"].isin(["2023-25", "2026 Q1"])]

    summary = (
        selected.groupby(["dist", "period"], as_index=False)
        .agg(
            median_saledays=("raw_calculated_median_saledays", "median"),
            year_count=("year", "size"),
        )
        .sort_values(["dist", "period"])
    )
    summary["median_saledays"] = summary["median_saledays"].round(1)
    return summary


def plot_listing_days_bar(summary: pd.DataFrame, output_path: Path) -> None:
    period_order = ["2023-25", "2026 Q1"]
    dist_order = TARGET_DISTRICTS
    palette = {"2023-25": "#4E79A7", "2026 Q1": "#E15759"}

    fig, ax = plt.subplots(figsize=(9.6, 5.4), dpi=180)
    sns.barplot(
        data=summary,
        x="dist",
        y="median_saledays",
        hue="period",
        order=dist_order,
        hue_order=period_order,
        palette=palette,
        ax=ax,
    )

    max_y = summary["median_saledays"].max()
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f 天", padding=4, fontsize=9, color="#344054")

    for idx, dist in enumerate(dist_order):
        rows = summary[summary["dist"] == dist].set_index("period")
        if not {"2023-25", "2026 Q1"}.issubset(rows.index):
            continue
        baseline = rows.loc["2023-25", "median_saledays"]
        q1 = rows.loc["2026 Q1", "median_saledays"]
        delta = q1 - baseline
        ax.text(
            idx,
            max(baseline, q1) + max_y * 0.11,
            f"+{delta:.0f} 天",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#B42318",
        )

    ax.set_title("掛牌天數中位數：2026 Q1 較 2023-25 拉長", fontsize=16, pad=16, weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("掛牌天數中位數（天）")
    ax.set_ylim(0, max_y * 1.28)
    ax.legend(title="", loc="upper left", frameon=False, ncol=2)
    sns.despine(ax=ax, left=False, bottom=False)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def build_hot_rate_heatmap_summary() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(HOT_SUMMARY_BY_TYPE, encoding="utf-8-sig")
    summary = df[
        (df["year"] == 2026)
        & df["dist"].isin(TARGET_DISTRICTS)
        & df["type"].isin(TARGET_TYPES)
    ].copy()
    summary = summary[["dist", "type", "total_count", "hot_count", "hot_rate_pct"]]
    summary["hot_rate_pct"] = summary["hot_rate_pct"].round(1)

    complete_index = pd.MultiIndex.from_product(
        [TARGET_DISTRICTS, TARGET_TYPES], names=["dist", "type"]
    )
    summary = (
        summary.set_index(["dist", "type"])
        .reindex(complete_index)
        .reset_index()
    )
    summary["total_count"] = summary["total_count"].fillna(0).astype(int)
    summary["hot_count"] = summary["hot_count"].fillna(0).astype(int)

    heatmap_values = summary.pivot(index="dist", columns="type", values="hot_rate_pct").loc[
        TARGET_DISTRICTS, TARGET_TYPES
    ]
    annotations = heatmap_values.copy().astype(object)
    count_values = summary.pivot(index="dist", columns="type", values="total_count").loc[
        TARGET_DISTRICTS, TARGET_TYPES
    ]
    for dist in TARGET_DISTRICTS:
        for building_type in TARGET_TYPES:
            value = heatmap_values.loc[dist, building_type]
            count = count_values.loc[dist, building_type]
            annotations.loc[dist, building_type] = "" if pd.isna(value) else f"{value:.1f}%\nn={count}"

    return summary, annotations


def plot_hot_rate_heatmap(summary: pd.DataFrame, annotations: pd.DataFrame, output_path: Path) -> None:
    heatmap_values = summary.pivot(index="dist", columns="type", values="hot_rate_pct").loc[
        TARGET_DISTRICTS, TARGET_TYPES
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=180)
    sns.heatmap(
        heatmap_values,
        annot=annotations,
        fmt="",
        cmap="YlGnBu",
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": "熱銷率（%）"},
        ax=ax,
    )
    ax.set_title("2026 Q1 行政區 × 房型熱銷率", fontsize=15, pad=14, weight="bold")
    ax.set_xlabel("房型")
    ax.set_ylabel("行政區")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_plot_style()

    listing_days_summary = build_listing_days_summary()
    listing_days_summary.to_csv(
        OUTPUT_DIR / "listing_days_median_2023_25_vs_2026q1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    plot_listing_days_bar(
        listing_days_summary,
        OUTPUT_DIR / "listing_days_median_bar.png",
    )

    hot_rate_summary, heatmap_annotations = build_hot_rate_heatmap_summary()
    hot_rate_summary.to_csv(
        OUTPUT_DIR / "hot_rate_heatmap_2026q1.csv",
        index=False,
        encoding="utf-8-sig",
    )
    plot_hot_rate_heatmap(
        hot_rate_summary,
        heatmap_annotations,
        OUTPUT_DIR / "hot_rate_heatmap_2026q1.png",
    )

    print("Generated:")
    print(f"- {OUTPUT_DIR / 'listing_days_median_bar.png'}")
    print(f"- {OUTPUT_DIR / 'listing_days_median_2023_25_vs_2026q1.csv'}")
    print(f"- {OUTPUT_DIR / 'hot_rate_heatmap_2026q1.png'}")
    print(f"- {OUTPUT_DIR / 'hot_rate_heatmap_2026q1.csv'}")


if __name__ == "__main__":
    main()
