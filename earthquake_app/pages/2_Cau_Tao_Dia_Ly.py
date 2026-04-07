import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.ui_components import (page_header, kpi, section_hdr, insight,
                                   sidebar_brand, sidebar_section,
                                   apply_theme, divider)
from utils.data_loader import load_data, filter_df, REGIONS_VI

st.set_page_config(page_title="Cấu tạo địa lý", page_icon="🌍", layout="wide")

sidebar_brand()

df_all = load_data()
if df_all.empty:
    st.stop()

# Sidebar filters
sidebar_section("BỘ LỌC")
selected_region = st.sidebar.selectbox("Chọn vùng", options=REGIONS_VI)

years = df_all["year"].dropna().unique()
if len(years) > 0:
    min_year, max_year = int(years.min()), int(years.max())
else:
    min_year, max_year = 2005, 2025
selected_years = st.sidebar.slider("Khoảng năm", min_year, max_year, (min_year, max_year))

page_header("Cấu tạo địa lý", "Đặc trưng địa chất và hoạt động địa chấn từng khu vực", "🌍")

df = filter_df(df_all, year_range=selected_years)
if df.empty:
    st.warning("Không có dữ liệu.")
    st.stop()

# Geo Info
GEO_INFO = {
    "Nam Âu":   "Vành đai Địa Trung Hải. Hellenic Arc, mảng Anatolia...",
    "Đông Âu":  "Đới Vrancea (Romania) — dị thường địa chấn sâu 60–200km...",
    "Trung Âu": "Dải Alps, Rhine Graben. Ít hoạt động...",
    "Bắc Âu":   "Mid-Atlantic Ridge, Iceland hotspot, GIA rebound...",
    "Tây Âu":   "Đới Azores–Gibraltar, Lisbon 1755, mảng Phi Châu–Á Âu...",
}

df_vung = df[df["region_vi"] == selected_region]

# HTML card for info
st.markdown(f"""
<div style="background:#1e1e3a;border-left:4px solid #7B2FBE;
     border-radius:8px;padding:16px 20px;margin-bottom:20px;color:#cbd5e1">
  <h3 style="margin-top:0;color:#fff">{selected_region}</h3>
  <p style="margin:0">{GEO_INFO.get(selected_region, "")}</p>
</div>
""", unsafe_allow_html=True)

# 4 KPI
col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi("Tổng trận", f"{len(df_vung):,}", icon="🔢")
with col2:
    val = df_vung["mag"].mean() if "mag" in df_vung.columns else 0
    kpi("Magnitude TB", f"{val:.2f}", icon="📏")
with col3:
    val = df_vung["depth_km"].mean() if "depth_km" in df_vung.columns else 0
    kpi("Depth TB", f"{val:.1f} km", icon="⬇️")
with col4:
    val = df_vung["sig"].mean() if "sig" in df_vung.columns else 0
    kpi("Sig TB", f"{val:.1f}", icon="🔴")

divider()

# Charts
c1, c2 = st.columns([3, 2])
with c1:
    section_hdr("Bản đồ vùng")
    if set(["latitude", "longitude", "mag", "depth_km"]).issubset(df_vung.columns):
        fig_map = px.scatter_mapbox(
            df_vung.dropna(subset=["latitude", "longitude", "mag"]).sample(min(10000, len(df_vung))),
            lat="latitude", lon="longitude", color="mag",
            color_continuous_scale=[[0, "#1e1e3a"], [0.5, "#7B2FBE"], [1, "#c084fc"]],
            mapbox_style="carto-darkmatter", zoom=3.5
        )
        fig_map = apply_theme(fig_map)
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        insight("Động đất chủ yếu bám theo đường đứt gãy kiến tạo mảng.")

with c2:
    section_hdr("Histogram Magnitude")
    if "mag" in df_vung.columns:
        fig_hist = px.histogram(df_vung, x="mag", nbins=30, color_discrete_sequence=["#7B2FBE"])
        fig_hist = apply_theme(fig_hist)
        st.plotly_chart(fig_hist, use_container_width=True)
        insight("Đa số các trận có cường độ nhỏ, bám sát đỉnh tháp chuông lệch.")

c3, c4 = st.columns([2, 3])
with c3:
    section_hdr("Phân bố Depth 5 vùng")
    if "depth_km" in df.columns and "region_vi" in df.columns:
        fig_box = px.box(df, x="region_vi", y="depth_km", color="region_vi",
                         color_discrete_sequence=["#7B2FBE","#c084fc","#38bdf8","#34d399","#f59e0b"])
        fig_box.update_layout(yaxis=dict(autorange="reversed"))
        fig_box = apply_theme(fig_box)
        st.plotly_chart(fig_box, use_container_width=True)
        insight("Đông Âu dị thường do dải Vrancea rất sâu.")

with c4:
    section_hdr("Biến động theo năm")
    if "year" in df_vung.columns:
        yearly = df_vung.groupby("year").size().reset_index(name="count")
        fig_bar_yr = px.bar(yearly, x="year", y="count", color_discrete_sequence=["#c084fc"])
        fig_bar_yr = apply_theme(fig_bar_yr)
        st.plotly_chart(fig_bar_yr, use_container_width=True)
        insight(f"Xu hướng số trận hàng năm cho vùng <strong>{selected_region}</strong>.")

divider()
section_hdr("Radar Chart 5 vùng")

if "mag" in df.columns and "depth_km" in df.columns:
    stats = df.groupby("region_vi").agg(
        Freq=("id", "count"),
        Mag=("mag", "mean"),
        Depth=("depth_km", "mean"),
        Sig=("sig", "mean"),
        Felt=("felt", "mean")
    ).fillna(0)
    
    def normalize(s):
        if s.max() == s.min(): return np.zeros(len(s))
        return (s - s.min()) / (s.max() - s.min())
        
    stats_n = stats.copy()
    for col in stats.columns:
        stats_n[col] = normalize(stats[col])
        
    categories = ['Tần suất', 'Magnitude', 'Độ sâu', 'Độ lớn (Sig)', 'Mức độ cảm nhận']
    fig_radar = go.Figure()
    
    for r in REGIONS_VI:
        if r in stats_n.index:
            values = stats_n.loc[r].tolist()
            values += values[:1]
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill='toself' if r == selected_region else 'none',
                name=r,
                fillcolor='rgba(123,47,190,0.4)' if r == selected_region else None,
                line=dict(color="#c084fc" if r == selected_region else "rgba(148,163,184,0.3)")
            ))
            
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="rgba(123,47,190,0.2)"),
            angularaxis=dict(gridcolor="rgba(123,47,190,0.2)", linecolor="rgba(123,47,190,0.4)")
        )
    )
    fig_radar = apply_theme(fig_radar)
    st.plotly_chart(fig_radar, use_container_width=True)
    insight("Mô hình đa chiều làm nổi bật điểm khác biệt của từng vùng kiến tạo.")
