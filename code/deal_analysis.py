"""
Transaction analysis for Taipei City and New Taipei City deals, 2023-2026.

成交資料沒有 saledays，因此不能沿用開價資料的「銷售天數低於區域中位數
50%」熱銷定義。本程式改用成交量作為熱門程度指標，分別輸出每年每區的
熱門建築類型，以及熱門建築類型 + 房數 + 坪數組合。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


INPUT_FILE = "2023-2026_成交.xlsx"
OUTPUT_DIR = Path("output_deal")
MIN_COUNT_TYPE = 30
MIN_COUNT_DETAIL = 10
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


def to_numeric_series(series: pd.Series) -> pd.Series:
    """Convert a series to numeric."""
    cleaned = series.astype("string").str.strip().str.replace(",", "", regex=False)
    return pd.to_numeric(cleaned, errors="coerce")


def normalize_district_name(series: pd.Series) -> pd.Series:
    """Normalize district names by keeping a valid 3-character district prefix."""
    cleaned = series.astype("string").str.strip()
    prefix = cleaned.str.slice(0, 3)
    return cleaned.mask(prefix.isin(VALID_DISTRICTS), prefix)


def normalize_building_type(value: object) -> str:
    """Shorten transaction building-type labels to readable categories."""
    if pd.isna(value):
        return "未知"

    text = str(value).strip()
    if "住宅大樓" in text:
        return "住宅大樓"
    if "華廈" in text:
        return "華廈"
    if "公寓" in text:
        return "公寓"
    if "透天" in text:
        return "透天厝"
    if "套房" in text:
        return "套房"
    if "店面" in text:
        return "店面"
    if "(" in text:
        return text.split("(", 1)[0]
    if "（" in text:
        return text.split("（", 1)[0]
    return text or "未知"


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


def read_deal_file(base_dir: Path = Path(".")) -> pd.DataFrame:
    """Read the transaction Excel file."""
    path = base_dir / INPUT_FILE
    if not path.exists():
        raise FileNotFoundError(f"Transaction file not found: {path}")

    df = pd.read_excel(path, sheet_name=0)
    df.columns = [str(col).strip() for col in df.columns]
    df["source_file"] = INPUT_FILE
    print(f"[DEAL] Loaded {INPUT_FILE}: {len(df):,} rows")
    return df


def clean_deal_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean transaction data and map it to analysis columns."""
    required_columns = ["交易年月", "鄉鎮市區", "建物類別名稱", "總價萬", "計算單價", "總建坪", "房", "屋齡"]
    missing_required = [col for col in required_columns if col not in raw_df.columns]
    if missing_required:
        raise KeyError(f"Deal data is missing required columns: {missing_required}")

    df = raw_df.copy()
    df["year"] = to_numeric_series(df["交易年月"]).astype("Int64") // 100
    df["dist"] = normalize_district_name(df["鄉鎮市區"])
    df["type"] = df["建物類別名稱"].apply(normalize_building_type)
    df["price"] = to_numeric_series(df["總價萬"])
    df["unit"] = to_numeric_series(df["計算單價"])
    df["size"] = to_numeric_series(df["總建坪"])
    df["room"] = to_numeric_series(df["房"])
    df["age"] = to_numeric_series(df["屋齡"])

    df = df.dropna(subset=["year", "dist", "type", "price", "unit", "size"]).copy()
    df = df[(df["dist"] != "") & (df["type"] != "")]
    df = df[df["dist"].isin(VALID_DISTRICTS)].copy()
    df = df[(df["price"] > 0) & (df["unit"] > 0) & (df["size"] > 0)].copy()
    df["year"] = df["year"].astype(int)
    df["size_group"] = df["size"].apply(create_size_group)
    df["room_group"] = df["room"].apply(create_room_group)
    return df


def build_data_quality_report(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> pd.DataFrame:
    """Build yearly transaction data-quality statistics."""
    raw_year = to_numeric_series(raw_df["交易年月"]).astype("Int64") // 100
    report_rows = []

    for year in sorted(raw_year.dropna().unique()):
        raw_mask = raw_year == year
        raw_part = raw_df[raw_mask]
        clean_part = clean_df[clean_df["year"] == year]
        dist = normalize_district_name(raw_part["鄉鎮市區"])

        report_rows.append(
            {
                "year": int(year),
                "raw_count": len(raw_part),
                "cleaned_count": len(clean_part),
                "removed_count": len(raw_part) - len(clean_part),
                "invalid_dist_count": (~dist.isin(VALID_DISTRICTS)).sum(),
                "missing_type_count": raw_part["建物類別名稱"].isna().sum(),
                "missing_price_count": to_numeric_series(raw_part["總價萬"]).isna().sum(),
                "missing_unit_price_count": to_numeric_series(raw_part["計算單價"]).isna().sum(),
                "missing_size_count": to_numeric_series(raw_part["總建坪"]).isna().sum(),
                "missing_room_count": to_numeric_series(raw_part["房"]).isna().sum(),
            }
        )

    return pd.DataFrame(report_rows)


def calculate_deal_summary_by_type(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate transaction metrics by year, district, and building type."""
    summary = (
        df.groupby(["year", "dist", "type"], dropna=False)
        .agg(
            total_count=("price", "size"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            median_unit_price=("unit", "median"),
            avg_unit_price=("unit", "mean"),
            avg_size=("size", "mean"),
            avg_room=("room", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
    )
    return summary[
        [
            "year",
            "dist",
            "type",
            "total_count",
            "median_price",
            "avg_price",
            "median_unit_price",
            "avg_unit_price",
            "avg_size",
            "avg_room",
            "avg_age",
        ]
    ]


def calculate_deal_summary_detail(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate transaction metrics by year, district, type, room group, and size group."""
    summary = (
        df.groupby(["year", "dist", "type", "room_group", "size_group"], dropna=False)
        .agg(
            total_count=("price", "size"),
            median_price=("price", "median"),
            avg_price=("price", "mean"),
            median_unit_price=("unit", "median"),
            avg_unit_price=("unit", "mean"),
            avg_size=("size", "mean"),
            avg_room=("room", "mean"),
            avg_age=("age", "mean"),
        )
        .reset_index()
    )
    return summary[
        [
            "year",
            "dist",
            "type",
            "room_group",
            "size_group",
            "total_count",
            "median_price",
            "avg_price",
            "median_unit_price",
            "avg_unit_price",
            "avg_size",
            "avg_room",
            "avg_age",
        ]
    ]


def select_top_deal_type(deal_summary_by_type: pd.DataFrame) -> pd.DataFrame:
    """Select the highest-volume building type for each year + district."""
    eligible = deal_summary_by_type[deal_summary_by_type["total_count"] >= MIN_COUNT_TYPE].copy()
    eligible = eligible.sort_values(
        by=["year", "dist", "total_count", "median_unit_price", "avg_price"],
        ascending=[True, True, False, False, False],
    )
    return eligible.groupby(["year", "dist"], as_index=False).head(1).reset_index(drop=True)


def select_top_deal_detail(deal_summary_detail: pd.DataFrame) -> pd.DataFrame:
    """Select the highest-volume type + room + size combination for each year + district."""
    eligible = deal_summary_detail[deal_summary_detail["total_count"] >= MIN_COUNT_DETAIL].copy()
    eligible = eligible.sort_values(
        by=["year", "dist", "total_count", "median_unit_price", "avg_price"],
        ascending=[True, True, False, False, False],
    )
    return eligible.groupby(["year", "dist"], as_index=False).head(1).reset_index(drop=True)


def round_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Round numeric output columns."""
    rounded = df.copy()
    rounding_rules = {
        "median_price": 2,
        "avg_price": 2,
        "median_unit_price": 2,
        "avg_unit_price": 2,
        "avg_size": 2,
        "avg_room": 0,
        "avg_age": 1,
    }
    for col, decimals in rounding_rules.items():
        if col in rounded.columns:
            rounded[col] = rounded[col].round(decimals)
    if "avg_room" in rounded.columns:
        rounded["avg_room"] = rounded["avg_room"].astype("Int64")
    return rounded


def export_outputs(
    deal_summary_by_type: pd.DataFrame,
    top_deal_type_by_district_year: pd.DataFrame,
    deal_summary_detail: pd.DataFrame,
    top_deal_detail_by_district_year: pd.DataFrame,
    data_quality_report: pd.DataFrame,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Export transaction CSV outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "deal_summary_by_type.csv": deal_summary_by_type,
        "top_deal_type_by_district_year.csv": top_deal_type_by_district_year,
        "deal_summary_detail.csv": deal_summary_detail,
        "top_deal_detail_by_district_year.csv": top_deal_detail_by_district_year,
        "data_quality_report.csv": data_quality_report,
    }

    for filename, df in outputs.items():
        path = output_dir / filename
        round_numeric_columns(df).to_csv(path, index=False, encoding="utf-8-sig")
        print(f"[OUTPUT] {path} ({len(df):,} rows)")


def main() -> None:
    """Run full transaction analysis workflow."""
    raw_df = read_deal_file()
    clean_df = clean_deal_data(raw_df)
    data_quality_report = build_data_quality_report(raw_df, clean_df)
    deal_summary_by_type = calculate_deal_summary_by_type(clean_df)
    deal_summary_detail = calculate_deal_summary_detail(clean_df)
    top_deal_type_by_district_year = select_top_deal_type(deal_summary_by_type)
    top_deal_detail_by_district_year = select_top_deal_detail(deal_summary_detail)

    export_outputs(
        deal_summary_by_type=deal_summary_by_type,
        top_deal_type_by_district_year=top_deal_type_by_district_year,
        deal_summary_detail=deal_summary_detail,
        top_deal_detail_by_district_year=top_deal_detail_by_district_year,
        data_quality_report=data_quality_report,
    )

    print("\n========== Deal Analysis Summary ==========")
    print(f"Total raw rows: {len(raw_df):,}")
    print(f"Cleaned rows: {len(clean_df):,}")
    print(f"Years: {sorted(clean_df['year'].unique())}")
    print(f"Districts: {clean_df['dist'].nunique()}")


if __name__ == "__main__":
    main()
