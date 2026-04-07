import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.data_loader import load_data, filter_df, REGIONS_VI
from utils.ui_components import (page_header, kpi, section_hdr, insight, 
                                   divider, apply_theme, sidebar_brand, sidebar_section)

st.set_page_config(page_title="Xu Hướng & Rủi Ro", page_icon="📈", layout="wide")
sidebar_brand()

df_all = load_data()
if df_all.empty:
    st.stop()

# ── Sidebars ──────────────────────────────────────────────────────────────────
sidebar_section("BỘ LỌC")
selected_regions = st.sidebar.multiselect("Vùng địa lý", options=REGIONS_VI, default=REGIONS_VI)

years = df_all["year"].dropna().unique()
if len(years) > 0:
    min_year, max_year = int(years.min()), int(years.max())
else:
    min_year, max_year = 2005, 2025
selected_years = st.sidebar.slider("Khoảng năm", min_year, max_year, (min_year, max_year))

# Apply Filter
df = filter_df(df_all, regions=selected_regions, year_range=selected_years)

page_header("Xu Hướng & Rủi Ro", "Phân tích xu hướng theo thời gian và đánh giá rủi ro tích hợp", "📈")

if df.empty:
    st.warning("Không có dữ liệu cho bộ lọc hiện tại.")
    st.stop()

# ── KPI ────────────────────────────────────────────────────────────────────────
cols = st.columns(4)
regions = df["region_vi"].unique() if "region_vi" in df.columns else []
risk_scores = {}

# Tính toán Risk Score đơn giản cho UI
df_all_yrs = df_all["year"].nunique()
for region in regions:
    sub = df[df["region_vi"] == region]
    freq  = len(sub) / max(1, df["year"].nunique())
    mag   = sub["mag"].mean() if "mag" in sub.columns else 0
    # Risk Score giả định (Normalize Magnitude 0-10 và Frequency)
    risk  = round(0.4 * (freq / 500) + 0.6 * (mag / 8), 3) 
    risk_scores[region] = min(risk, 1.0)

with cols[0]:
    top_region = max(risk_scores, key=risk_scores.get) if risk_scores else "N/A"
    kpi("Vùng rủi ro cao nhất", top_region, icon="⚠️")
with cols[1]:
    kpi("Số vùng phân tích", str(len(regions)), icon="🗺️")
with cols[2]:
    avg_risk = round(sum(risk_scores.values()) / len(risk_scores), 3) if risk_scores else 0
    kpi("Điểm rủi ro TB", str(avg_risk), icon="📊")
with cols[3]:
    high_risk_count = sum(1 for v in risk_scores.values() if v > 0.6)
    kpi("Vùng cần theo dõi sát", str(high_risk_count), icon="🔴")

divider()

# ── BIỂU ĐỒ 1: Xu hướng số lượng theo năm mỗi vùng ──────────────────────────
section_hdr("Số trận động đất mỗi năm theo vùng")

if "year" in df.columns and "region_vi" in df.columns:
    yearly = df.groupby(["year", "region_vi"]).size().reset_index(name="count")
    fig1 = px.line(yearly, x="year", y="count", color="region_vi",
                   title="Số trận động đất ghi nhận mỗi năm — phân theo vùng")
    fig1.update_traces(line_width=2)
    fig1 = apply_theme(fig1)
    st.plotly_chart(fig1, use_container_width=True)

divider()

# ── BIỂU ĐỒ 2: Điểm rủi ro tổng hợp theo vùng ───────────────────────────────
section_hdr("Điểm rủi ro tổng hợp (Dựa trên Tần suất & Cường độ)")

if risk_scores:
    risk_df = pd.DataFrame(list(risk_scores.items()), columns=["Vùng", "Điểm rủi ro"])
    risk_df = risk_df.sort_values("Điểm rủi ro", ascending=True)
    fig2 = px.bar(risk_df, x="Điểm rủi ro", y="Vùng", orientation="h",
                  title="Xếp hạng rủi ro (0 = thấp, 1 = cao nhất)",
                  color="Điểm rủi ro", color_continuous_scale=[[0, "#22c55e"], [0.5, "#eab308"], [1, "#ef4444"]])
    fig2 = apply_theme(fig2)
    st.plotly_chart(fig2, use_container_width=True)

divider()

# ── BIỂU ĐỒ 3: Xu hướng cường độ trung bình theo năm ────────────────────────
section_hdr("Biến động cường độ trung bình theo năm")

if "year" in df.columns and "mag" in df.columns:
    mag_trend = df.groupby("year")["mag"].mean().reset_index()
    fig3 = px.scatter(mag_trend, x="year", y="mag", trendline="lowess",
                      title="Cường độ trung bình mỗi năm (đường xu hướng LOWESS)")
    fig3.update_traces(marker_color="#7B2FBE", selector=dict(mode="markers"))
    fig3 = apply_theme(fig3)
    st.plotly_chart(fig3, use_container_width=True)

divider()

# ── INSIGHTS ──────────────────────────────────────────────────────────────────
section_hdr("Kết luận quan trọng")

insight(
    "Nam Âu liên tục dẫn đầu về cả số lượng lẫn điểm rủi ro "
    "— điều này phản ánh đúng thực tế kiến tạo mảng tại Địa Trung Hải.",
    kind="warning"
)
insight(
    "Điểm rủi ro được tính toán dựa trên sự kết hợp giữa tần suất xuất hiện và cường độ trung bình "
    "trong khoảng thời gian lọc đã chọn.",
    kind="info"
)
insight(
    "Sự gia tăng số lượng bản ghi trong giai đoạn gần đây thường đi kèm với việc giảm nhẹ "
    "cường độ trung bình, một dấu hiệu cho thấy mạng lưới trạm đo đang phát hiện tốt các trận nhỏ.",
    kind="success"
)
