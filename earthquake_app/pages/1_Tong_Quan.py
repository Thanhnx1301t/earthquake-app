import streamlit as st
import numpy as np
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.ui_components import (page_header, kpi, section_hdr, insight,
                                   sidebar_brand, sidebar_section,
                                   apply_theme, divider)
from utils.data_loader import load_data, filter_df, REGIONS_VI

st.set_page_config(page_title="Tổng Quan", page_icon="📊", layout="wide")

sidebar_brand()

df_all = load_data()
if df_all.empty:
    st.stop()

# Sidebar filters
sidebar_section("BỘ LỌC")
selected_regions = st.sidebar.multiselect("Vùng địa lý", options=REGIONS_VI, default=REGIONS_VI)

years = df_all["year"].dropna().unique()
if len(years) > 0:
    min_year, max_year = int(years.min()), int(years.max())
else:
    min_year, max_year = 2005, 2025
selected_years = st.sidebar.slider("Khoảng năm", min_year, max_year, (min_year, max_year))

selected_mag = st.sidebar.slider("Magnitude", 0.0, 10.0, (0.0, 10.0), step=0.1)

page_header("Tổng Quan", "Bức tranh toàn cảnh hoạt động địa chấn Châu Âu 2005–2025", "📊")

df = filter_df(df_all, regions=selected_regions, year_range=selected_years, mag_range=selected_mag)
if df.empty:
    st.warning("Không có dữ liệu.")
    st.stop()

tabs = st.tabs(["📈 Theo năm", "🗺️ Bản đồ", "🔥 Heatmap", "🏆 Theo vùng"])

with tabs[0]:
    section_hdr("Hoạt động theo năm")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi("Tổng sự kiện", f"{len(df):,}", icon="🔢")
    with col2:
        val = df["mag"].mean() if "mag" in df.columns else 0
        kpi("Magnitude TB", f"{val:.2f}", icon="📏")
    with col3:
        val = df["depth_km"].mean() if "depth_km" in df.columns else 0
        kpi("Depth TB", f"{val:.1f} km", icon="⬇️")
    with col4:
        if "depth_km" in df.columns:
            pct = (df["depth_km"] < 70).mean() * 100
        else:
            pct = 0
        kpi("% Shallow <70km", f"{pct:.1f}%", icon="🔴")
        
    divider()
    
    if "year" in df.columns:
        yearly_counts = df.groupby("year").size().reset_index(name="count")
        if not yearly_counts.empty:
            fig = px.bar(yearly_counts, x="year", y="count", color_discrete_sequence=["#7B2FBE"])
            
            # Trendline
            z = np.polyfit(yearly_counts["year"], yearly_counts["count"], 1)
            p = np.poly1d(z)
            fig.add_scatter(x=yearly_counts["year"], y=p(yearly_counts["year"]), mode="lines", 
                            line=dict(color="#c084fc", dash="dot"), name="Trend")
            
            # Annotation đỉnh
            peak = yearly_counts.loc[yearly_counts["count"].idxmax()]
            fig.add_annotation(x=peak["year"], y=peak["count"], text=f"Đỉnh: {peak['year']}", showarrow=True, arrowhead=1)
            
            fig = apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
            
            trend_dir = "tăng" if z[0] > 0 else "giảm"
            insight(f"Năm <strong>{peak['year']}</strong> có nhiều trận nhất ({peak['count']:,} trận). Xu hướng chung trong giai đoạn đang <strong>{trend_dir}</strong>.")

with tabs[1]:
    section_hdr("Phân bố vị trí", "Bản đồ")
    if set(["latitude", "longitude", "mag", "depth_km", "region_vi"]).issubset(df.columns):
        plot_df = df.dropna(subset=["latitude", "longitude", "mag", "depth_km"])
        if len(plot_df) > 15000:
            plot_df = plot_df.sample(15000, random_state=42)
            
        fig_map = px.scatter_mapbox(
            plot_df, lat="latitude", lon="longitude", color="mag", size="mag", size_max=15,
            hover_data=["place", "mag", "depth_km", "region_vi"],
            color_continuous_scale=[[0, "#1e1e3a"], [0.5, "#7B2FBE"], [1, "#c084fc"]],
            mapbox_style="carto-darkmatter", zoom=2.5, center={"lat": 48.0, "lon": 10.0}
        )
        fig_map = apply_theme(fig_map)
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        insight(f"Bản đồ đang hiển thị <strong>{len(plot_df):,}</strong> sự kiện. Tần suất tập trung dọc theo các ranh giới mảng.")
    else:
        st.info("Thiếu dữ liệu tọa độ hoặc magnitude.")

with tabs[2]:
    section_hdr("Mật độ xuất hiện", "Heatmap")
    if set(["year", "month"]).issubset(df.columns):
        heatmap_data = df.groupby(["year", "month"]).size().unstack(fill_value=0)
        fig_heat = px.imshow(heatmap_data, color_continuous_scale=[[0,"#13131f"],[0.4,"#7B2FBE"],[1,"#c084fc"]], aspect="auto")
        fig_heat = apply_theme(fig_heat)
        st.plotly_chart(fig_heat, use_container_width=True)
        
        counts = df.groupby(["year", "month"]).size()
        if not counts.empty:
            peak_ym = counts.idxmax()
            insight(f"Dữ liệu dày đặc nhất vào <strong>Tháng {peak_ym[1]} năm {peak_ym[0]}</strong> với {counts.max()} sự kiện.")
    else:
        st.info("Thiếu dữ liệu tháng/năm.")

with tabs[3]:
    section_hdr("Hoạt động theo khu vực")
    if "region_vi" in df.columns:
        region_stats = df.groupby("region_vi").agg(
            count=("id", "count"),
            mag_mean=("mag", "mean")
        ).reset_index()
        
        region_stats = region_stats.sort_values("count", ascending=True)
        fig_bar = px.bar(region_stats, x="count", y="region_vi", orientation='h', color="mag_mean",
                         color_continuous_scale=[[0, "#1e1e3a"], [1, "#c084fc"]])
        fig_bar = apply_theme(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        top_region = region_stats.iloc[-1]["region_vi"]
        insight(f"Vùng <strong>{top_region}</strong> đứng đầu về số lượng sự kiện.")
