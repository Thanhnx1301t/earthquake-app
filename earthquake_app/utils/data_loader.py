import pandas as pd
import numpy as np
import streamlit as st
import os

REGION_MAP = {
    "Northern Europe": "Bắc Âu",
    "Southern Europe": "Nam Âu",
    "Central Europe":  "Trung Âu",
    "Eastern Europe":  "Đông Âu",
    "Western Europe":  "Tây Âu",
}
REGIONS_VI = ["Nam Âu", "Đông Âu", "Trung Âu", "Bắc Âu", "Tây Âu"]

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "earthquake_data.csv")

@st.cache_data(show_spinner="Đang tải dữ liệu…")
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(DATA_PATH, low_memory=False)
    except FileNotFoundError:
        st.error(f"❌ Không tìm thấy file: {DATA_PATH}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()

    # Parse datetime
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce", dayfirst=False)

    # Ép kiểu số
    for col in ["latitude","longitude","depth_km","mag","felt","cdi","mmi",
                "sig","gap","dmin","rms","nst"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # year / month
    if "year" not in df.columns and "time" in df.columns:
        df["year"]  = df["time"].dt.year
    if "month" not in df.columns and "time" in df.columns:
        df["month"] = df["time"].dt.month

    df["year"]  = pd.to_numeric(df.get("year",  pd.Series(dtype=float)), errors="coerce")
    df["month"] = pd.to_numeric(df.get("month", pd.Series(dtype=float)), errors="coerce")

    # Map sub_region → tiếng Việt
    if "sub_region" in df.columns:
        df["region_vi"] = df["sub_region"].map(REGION_MAP).fillna("Khác")
    else:
        df["region_vi"] = "Khác"

    # Phân loại độ sâu
    if "depth_km" in df.columns:
        df["depth_cat"] = pd.cut(
            df["depth_km"], bins=[-1, 70, 300, 10000],
            labels=["Nông (<70 km)", "Trung (70–300 km)", "Sâu (>300 km)"]
        )

    return df.reset_index(drop=True)


def filter_df(df, regions=None, year_range=None, mag_range=None):
    out = df.copy()
    if regions:
        out = out[out["region_vi"].isin(regions)]
    if year_range and "year" in out.columns:
        out = out[out["year"].between(*year_range)]
    if mag_range and "mag" in out.columns:
        out = out[out["mag"].between(*mag_range)]
    return out
