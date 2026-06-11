"""
Hot sale analysis for Taipei City and New Taipei City listings, 2023-2026.

本程式以 saledays 作為熱銷判斷依據。由於不同年度與行政區的房市流動速度不同，
因此先計算每個 year + dist 的 saledays 中位數，並將 saledays 小於該中位數
50% 的物件定義為熱銷物件。接著分別從「建築類型」與「建築類型 + 房數 +
坪數區間」兩個層級計算熱銷率，最後選出每個年度、每個行政區中熱銷率最高且
樣本數足夠的物件組合。
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd


RAW_FILES = [
    "2023_開價.xlsx",
    "2024_開價.xlsx",
    "2025_開價.xlsx",
    "202603_開價.xlsx",
]

MEDIAN_FILES = [
    "開價2023_median.xlsx - Sheet1.csv",
    "開價2024_median.xlsx - Sheet1.csv",
    "開價2025_median.xlsx - Sheet1.csv",
    "開價202603_median.xlsx - Sheet1.csv",
]

NUMERIC_COLUMNS = ["saledays", "price", "unit", "size", "room", "age"]
MIN_COUNT_TYPE = 30
MIN_COUNT_DETAIL = 10
OUTPUT_DIR = Path("output")
VALID_DISTRICTS = {
    "中正區",
    "大同區",
    "中山區",
    "松山區",
    "大安區",
    "萬華區",
    "信義區",
    "士林區",
    "北投區",
    "內湖區",
    "南港區",
    "文山區",
    "板橋區",
    "三重區",
    "中和區",
    "永和區",
    "新莊區",
    "新店區",
    "土城區",
    "蘆洲區",
    "汐止區",
    "樹林區",
    "淡水區",
    "三峽區",
    "林口區",
    "五股區",
    "泰山區",
    "瑞芳區",
    "八里區",
    "深坑區",
    "三芝區",
    "金山區",
    "萬里區",
    "烏來區",
    "石碇區",
    "坪林區",
    "平溪區",
    "雙溪區",
    "貢寮區",
    "石門區",
    "鶯歌區",
}


def extract_year_from_filename(filename: str) -> int | None:
    """Extract the first 4-digit year from a filename."""
    match = re.search(r"(20\d{2})", filename)
    if not match:
        return None
    return int(match.group(1))


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing spaces from column names."""
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def read_csv_safely(path: Path) -> pd.DataFrame:
    """Read CSV with common encodings."""
    encodings = ["utf-8-sig", "utf-8", "big5", "cp950"]
    last_error: Exception | None = None

    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise RuntimeError(f"Unable to read {path} with supported encodings") from last_error


def read_input_file(path: Path) -> pd.DataFrame:
    """Read a CSV or Excel input file."""
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=0)
    return read_csv_safely(path)


def read_raw_files(base_dir: Path = Path(".")) -> pd.DataFrame:
    """Read and combine all raw listing CSV files."""
    frames = []

    for filename in RAW_FILES:
        path = base_dir / filename
        if not path.exists():
            warnings.warn(f"Raw file not found, skipped: {filename}")
            continue

        year = extract_year_from_filename(filename)
        df = read_input_file(path)
        df = clean_column_names(df)
        df["source_file"] = filename
        df["year"] = year
        frames.append(df)
        print(f"[RAW] Loaded {filename}: {len(df):,} rows, year={year}")

    if not frames:
        raise FileNotFoundError("No raw CSV files were loaded. Please check filenames.")

    raw_df = pd.concat(frames, ignore_index=True, sort=False)
    return raw_df


def read_median_files(base_dir: Path = Path(".")) -> pd.DataFrame:
    """Read median CSV files for auxiliary checks. This never stops main analysis."""
    frames = []

    for filename in MEDIAN_FILES:
        path = base_dir / filename
        if not path.exists():
            warnings.warn(f"Median file not found, skipped: {filename}")
            continue

        try:
            year = extract_year_from_filename(filename)
            df = read_csv_safely(path)
            df = clean_column_names(df)
            df["source_file"] = filename
            df["year"] = year
            frames.append(df)
            print(f"[MEDIAN] Loaded {filename}: {len(df):,} rows, year={year}")
        except Exception as exc:  # Median files are optional.
            warnings.warn(f"Failed to read median file {filename}: {exc}")

    if not frames:
        warnings.warn("No median CSV files were loaded. Median report will use raw data only.")
        return pd.DataFrame()

    median_df = pd.concat(frames, ignore_index=True, sort=False)

    print("\n[MEDIAN] Basic information")
    print(f"Rows: {len(median_df):,}")
    print(f"Columns: {list(median_df.columns)}")
    print("Head:")
    print(median_df.head().to_string(index=False))
    print()

    return median_df


def to_numeric_series(series: pd.Series) -> pd.Series:
    """Convert a series to numeric, tolerating commas and non-numeric values."""
    cleaned = (
        series.astype("string")
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("坪", "", regex=False)
        .str.replace("萬", "", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def normalize_district_name(series: pd.Series) -> pd.Series:
    """Normalize dirty district names by keeping a valid 3-character district prefix."""
    cleaned = series.astype("string").str.strip()
    prefix = cleaned.str.slice(0, 3)
    return cleaned.mask(prefix.isin(VALID_DISTRICTS), prefix)


def create_size_group(size: object) -> str:
    """Create size interval labels."""
    if pd.isna(size):
        return "未知"
    if size < 20:
        return "20坪以下"
    if size < 30:
        return "20-30坪"
    if size < 40:
        return "30-40坪"
    if size < 60:
        return "40-60坪"
    return "60坪以上"


def create_room_group(room: object) -> str:
    """Create room-count labels."""
    if pd.isna(room):
        return "未知"
    if room == 0:
        return "0房"
    if room == 1:
        return "1房"
    if room == 2:
        return "2房"
    if room == 3:
        return "3房"
    if room == 4:
        return "4房"
    if room >= 5:
        return "5房以上"
    return "未知"


def build_data_quality_report(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> pd.DataFrame:
    """Build yearly data-quality statistics."""
    report_rows = []

    for year in sorted(raw_df["year"].dropna().unique()):
        raw_year = raw_df[raw_df["year"] == year].copy()
        clean_year = clean_df[clean_df["year"] == year]

        saledays_numeric = (
            to_numeric_series(raw_year["saledays"])
            if "saledays" in raw_year.columns
            else pd.Series([pd.NA] * len(raw_year), index=raw_year.index)
        )

        report_rows.append(
            {
                "year": int(year),
                "raw_count": len(raw_year),
                "cleaned_count": len(clean_year),
                "removed_count": len(raw_year) - len(clean_year),
                "missing_dist_count": raw_year["dist"].isna().sum()
                if "dist" in raw_year.columns
                else len(raw_year),
                "missing_type_count": raw_year["type"].isna().sum()
                if "type" in raw_year.columns
                else len(raw_year),
                "missing_saledays_count": saledays_numeric.isna().sum(),
                "invalid_saledays_le_zero_count": (saledays_numeric <= 0).sum(),
                "missing_size_count": raw_year["size"].isna().sum()
                if "size" in raw_year.columns
                else len(raw_year),
                "missing_room_count": raw_year["room"].isna().sum()
                if "room" in raw_year.columns
                else len(raw_year),
            }
        )

    return pd.DataFrame(report_rows)


def clean_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw data and create size/room groups."""
    required_columns = ["dist", "type", "saledays"]
    missing_required = [col for col in required_columns if col not in raw_df.columns]
    if missing_required:
        raise KeyError(f"Raw data is missing required columns: {missing_required}")

    df = raw_df.copy()

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = to_numeric_series(df[col])
        else:
            warnings.warn(f"Column not found, filled with NA: {col}")
            df[col] = pd.NA

    df["dist"] = normalize_district_name(df["dist"])
    df["type"] = df["type"].astype("string").str.strip()

    df = df.dropna(subset=["dist", "type", "saledays"])
    df = df[(df["dist"] != "") & (df["type"] != "")]
    df = df[df["saledays"] > 0].copy()

    if df["year"].isna().any() and "ym" in df.columns:
        ym_year = df["ym"].astype("string").str.extract(r"^(20\d{2})")[0]
        df["year"] = df["year"].fillna(pd.to_numeric(ym_year, errors="coerce"))

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)

    df["size_group"] = df["size"].apply(create_size_group)
    df["room_group"] = df["room"].apply(create_room_group)

    return df


def define_hot_items(df: pd.DataFrame) -> pd.DataFrame:
    """Define hot sale items by year + district median saledays."""
    df = df.copy()
    district_median = (
        df.groupby(["year", "dist"], dropna=False)["saledays"]
        .median()
        .reset_index(name="district_year_median_saledays")
    )

    df = df.merge(district_median, on=["year", "dist"], how="left")
    df["hot_threshold"] = df["district_year_median_saledays"] * 0.5
    df["is_hot"] = df["saledays"] < df["hot_threshold"]
    return df


def calculate_hot_summary_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate hot-sale metrics by year, district, and building type."""
    summary = (
        df.groupby(["year", "dist", "type"], dropna=False)
        .agg(
            total_count=("saledays", "size"),
            hot_count=("is_hot", "sum"),
            median_saledays=("saledays", "median"),
            avg_saledays=("saledays", "mean"),
            avg_price=("price", "mean"),
            avg_unit_price=("unit", "mean"),
            avg_size=("size", "mean"),
            avg_room=("room", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
    )
    summary["hot_rate"] = summary["hot_count"] / summary["total_count"]
    summary["hot_rate_pct"] = summary["hot_rate"] * 100
    return reorder_metric_columns(summary, ["year", "dist", "type"])


def calculate_hot_summary_detail(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate hot-sale metrics by year, district, type, room group, and size group."""
    summary = (
        df.groupby(["year", "dist", "type", "room_group", "size_group"], dropna=False)
        .agg(
            total_count=("saledays", "size"),
            hot_count=("is_hot", "sum"),
            median_saledays=("saledays", "median"),
            avg_saledays=("saledays", "mean"),
            avg_price=("price", "mean"),
            avg_unit_price=("unit", "mean"),
            avg_size=("size", "mean"),
            avg_room=("room", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
    )
    summary["hot_rate"] = summary["hot_count"] / summary["total_count"]
    summary["hot_rate_pct"] = summary["hot_rate"] * 100
    return reorder_metric_columns(summary, ["year", "dist", "type", "room_group", "size_group"])


def reorder_metric_columns(summary: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Put frequently used metric columns in a readable order."""
    metric_cols = [
        "total_count",
        "hot_count",
        "hot_rate",
        "hot_rate_pct",
        "median_saledays",
        "avg_saledays",
        "avg_price",
        "avg_unit_price",
        "avg_size",
        "avg_room",
        "avg_age",
    ]
    return summary[group_cols + metric_cols]


def select_top_hot_type(hot_summary_by_type: pd.DataFrame) -> pd.DataFrame:
    """Select the hottest building type for each year + district."""
    eligible = hot_summary_by_type[hot_summary_by_type["total_count"] >= MIN_COUNT_TYPE].copy()
    eligible = eligible.sort_values(
        by=["year", "dist", "hot_rate", "hot_count", "median_saledays", "total_count"],
        ascending=[True, True, False, False, True, False],
    )
    return eligible.groupby(["year", "dist"], as_index=False).head(1).reset_index(drop=True)


def select_top_hot_detail(hot_summary_detail: pd.DataFrame) -> pd.DataFrame:
    """Select the hottest type + room + size combination for each year + district."""
    eligible = hot_summary_detail[hot_summary_detail["total_count"] >= MIN_COUNT_DETAIL].copy()
    eligible = eligible.sort_values(
        by=["year", "dist", "hot_rate", "hot_count", "median_saledays", "total_count"],
        ascending=[True, True, False, False, True, False],
    )
    return eligible.groupby(["year", "dist"], as_index=False).head(1).reset_index(drop=True)


def build_median_check_report(clean_df: pd.DataFrame, median_df: pd.DataFrame) -> pd.DataFrame:
    """Compare raw-data median saledays with optional median files when possible."""
    raw_median = (
        clean_df.groupby(["year", "dist"], dropna=False)["saledays"]
        .median()
        .reset_index(name="raw_calculated_median_saledays")
    )

    if median_df.empty:
        raw_median["median_file_median_saledays"] = pd.NA
        raw_median["median_diff_raw_minus_file"] = pd.NA
        raw_median["median_file_available"] = False
        return raw_median

    needed = {"year", "dist", "saledays"}
    if not needed.issubset(set(median_df.columns)):
        warnings.warn(
            "Median files cannot be compared because required columns "
            f"are missing. Required={sorted(needed)}, actual={list(median_df.columns)}"
        )
        raw_median["median_file_median_saledays"] = pd.NA
        raw_median["median_diff_raw_minus_file"] = pd.NA
        raw_median["median_file_available"] = False
        return raw_median

    median_clean = median_df.copy()
    median_clean["dist"] = normalize_district_name(median_clean["dist"])
    median_clean["saledays"] = to_numeric_series(median_clean["saledays"])
    median_clean["year"] = pd.to_numeric(median_clean["year"], errors="coerce")
    median_clean = median_clean.dropna(subset=["year", "dist", "saledays"])
    median_clean["year"] = median_clean["year"].astype(int)

    median_by_file = (
        median_clean.groupby(["year", "dist"], dropna=False)["saledays"]
        .median()
        .reset_index(name="median_file_median_saledays")
    )

    report = raw_median.merge(median_by_file, on=["year", "dist"], how="left")
    report["median_diff_raw_minus_file"] = (
        report["raw_calculated_median_saledays"] - report["median_file_median_saledays"]
    )
    report["median_file_available"] = report["median_file_median_saledays"].notna()
    return report


def round_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Round float columns for cleaner CSV output."""
    rounded = df.copy()
    float_cols = rounded.select_dtypes(include=["float"]).columns
    rounded[float_cols] = rounded[float_cols].round(4)
    return rounded


def format_top_hot_type_output(df: pd.DataFrame) -> pd.DataFrame:
    """Apply requested rounding rules for top hot type output."""
    formatted = round_numeric_columns(df)
    format_rules = {
        "hot_rate_pct": "{:.2f}",
        "avg_saledays": "{:.1f}",
        "avg_price": "{:.2f}",
        "avg_unit_price": "{:.2f}",
        "avg_size": "{:.2f}",
        "avg_age": "{:.1f}",
    }

    for col, format_rule in format_rules.items():
        if col in formatted.columns:
            formatted[col] = formatted[col].apply(
                lambda value, rule=format_rule: "" if pd.isna(value) else rule.format(value)
            )

    if "avg_room" in formatted.columns:
        formatted["avg_room"] = formatted["avg_room"].round(0).astype("Int64")

    return formatted


def export_outputs(
    hot_summary_by_type: pd.DataFrame,
    top_hot_type_by_district_year: pd.DataFrame,
    hot_summary_detail: pd.DataFrame,
    top_hot_detail_by_district_year: pd.DataFrame,
    data_quality_report: pd.DataFrame,
    median_check_report: pd.DataFrame,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Export all required CSV outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "hot_summary_by_type.csv": hot_summary_by_type,
        "top_hot_type_by_district_year.csv": format_top_hot_type_output(top_hot_type_by_district_year),
        "hot_summary_detail.csv": hot_summary_detail,
        "top_hot_detail_by_district_year.csv": top_hot_detail_by_district_year,
        "data_quality_report.csv": data_quality_report,
        "median_check_report.csv": median_check_report,
    }

    for filename, df in outputs.items():
        path = output_dir / filename
        round_numeric_columns(df).to_csv(path, index=False, encoding="utf-8-sig")
        print(f"[OUTPUT] {path} ({len(df):,} rows)")


def print_readable_results(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    hot_summary_by_type: pd.DataFrame,
    hot_summary_detail: pd.DataFrame,
    top_hot_type_by_district_year: pd.DataFrame,
    top_hot_detail_by_district_year: pd.DataFrame,
) -> None:
    """Print terminal summary requested by the project."""
    hot_count = int(clean_df["is_hot"].sum())
    non_hot_count = int((~clean_df["is_hot"]).sum())
    eligible_type_count = int((hot_summary_by_type["total_count"] >= MIN_COUNT_TYPE).sum())
    eligible_detail_count = int((hot_summary_detail["total_count"] >= MIN_COUNT_DETAIL).sum())

    print("\n========== Analysis Summary ==========")
    print(f"Total raw rows: {len(raw_df):,}")
    print(f"Cleaned rows: {len(clean_df):,}")
    print(f"Hot items: {hot_count:,}")
    print(f"Non-hot items: {non_hot_count:,}")
    print(f"Type groups with total_count >= {MIN_COUNT_TYPE}: {eligible_type_count:,}")
    print(f"Detail groups with total_count >= {MIN_COUNT_DETAIL}: {eligible_detail_count:,}")

    print("\n========== Top Hot Type by Year + District: first 20 ==========")
    cols_type = [
        "year",
        "dist",
        "type",
        "total_count",
        "hot_count",
        "hot_rate_pct",
        "median_saledays",
        "avg_unit_price",
        "avg_size",
    ]
    print(round_numeric_columns(top_hot_type_by_district_year[cols_type].head(20)).to_string(index=False))

    print("\n========== Top Hot Detail by Year + District: first 20 ==========")
    cols_detail = [
        "year",
        "dist",
        "type",
        "room_group",
        "size_group",
        "total_count",
        "hot_count",
        "hot_rate_pct",
        "median_saledays",
        "avg_unit_price",
        "avg_size",
    ]
    print(round_numeric_columns(top_hot_detail_by_district_year[cols_detail].head(20)).to_string(index=False))


def main() -> None:
    """Run full analysis workflow."""
    base_dir = Path(".")

    raw_df = read_raw_files(base_dir)
    median_df = read_median_files(base_dir)

    clean_df = clean_data(raw_df)
    data_quality_report = build_data_quality_report(raw_df, clean_df)
    clean_df = define_hot_items(clean_df)

    hot_summary_by_type = calculate_hot_summary_by_type(clean_df)
    hot_summary_detail = calculate_hot_summary_detail(clean_df)

    top_hot_type_by_district_year = select_top_hot_type(hot_summary_by_type)
    top_hot_detail_by_district_year = select_top_hot_detail(hot_summary_detail)

    median_check_report = build_median_check_report(clean_df, median_df)

    export_outputs(
        hot_summary_by_type=hot_summary_by_type,
        top_hot_type_by_district_year=top_hot_type_by_district_year,
        hot_summary_detail=hot_summary_detail,
        top_hot_detail_by_district_year=top_hot_detail_by_district_year,
        data_quality_report=data_quality_report,
        median_check_report=median_check_report,
    )

    print_readable_results(
        raw_df=raw_df,
        clean_df=clean_df,
        hot_summary_by_type=hot_summary_by_type,
        hot_summary_detail=hot_summary_detail,
        top_hot_type_by_district_year=top_hot_type_by_district_year,
        top_hot_detail_by_district_year=top_hot_detail_by_district_year,
    )


if __name__ == "__main__":
    main()
