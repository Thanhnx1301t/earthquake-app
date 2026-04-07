import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.ui_components import (page_header, kpi, section_hdr, insight,
                                   sidebar_brand, sidebar_section,
                                   apply_theme, divider)
from utils.data_loader import load_data, filter_df, REGIONS_VI

st.set_page_config(page_title="Dư chấn & Tương quan", page_icon="🔗", layout="wide")
sidebar_brand()

df_all = load_data()
if df_all.empty:
    st.stop()

# Đảm bảo có time
if "time" not in df_all.columns:
    st.warning("Thiếu cột thời gian để phân tích dư chấn.")
    st.stop()

# Sidebar
sidebar_section("BỘ LỌC")
selected_region = st.sidebar.selectbox("Chọn vùng", options=REGIONS_VI)

years = df_all["year"].dropna().unique()
if len(years) > 0:
    min_year, max_year = int(years.min()), int(years.max())
else:
    min_year, max_year = 2005, 2025
selected_years = st.sidebar.slider("Khoảng năm", min_year, max_year, (min_year, max_year))

# Lọc M >= 5 để cho hiển thị top 30
df_region = df_all[(df_all["region_vi"] == selected_region) & (df_all["year"].between(*selected_years))]
mainshocks = df_region[df_region["mag"] >= 5.0].sort_values("mag", ascending=False).head(30)

if not mainshocks.empty:
    options = mainshocks.apply(lambda row: f"{row['time'].strftime('%Y-%m-%d')} | M={row['mag']} | {row.get('place', '')}", axis=1).tolist()
    ms_choice = st.sidebar.selectbox("Chọn Mainshock (M≥5)", options)
    idx = options.index(ms_choice)
    ms = mainshocks.iloc[idx]
else:
    ms_choice = None
    ms = None
    st.sidebar.info("Không có mainshock (M≥5) trong khoảng thời gian này.")

page_header("Dư chấn & Tương quan", "Phân tích Omori Law, foreshock/aftershock và sự tương quan", "🔗")

tabs = st.tabs(["⚡ Foreshock", "🌊 Aftershock & Omori", "🔢 Depth × Mag", "🧮 Correlation"])

with tabs[0]:
    section_hdr("Foreshock (30 ngày trước)")
    if ms is not None:
        ms_time = ms["time"]
        df_region["days_diff"] = (df_region["time"] - ms_time).dt.total_seconds() / (24 * 3600)
        
        # Spatial filter thô: 100km radius (~1 độ)
        lat, lon = ms["latitude"], ms["longitude"]
        nearby = df_region[np.sqrt((df_region["latitude"] - lat)**2 + (df_region["longitude"] - lon)**2) <= 1.0]
        
        fs = nearby[(nearby["days_diff"] >= -30) & (nearby["days_diff"] < 0)]
        fs_counts = fs.groupby(fs["days_diff"].astype(int)).size().reset_index(name="count")
        
        all_fs_days = pd.DataFrame({"days_diff": range(-30, 0)})
        fs_counts = all_fs_days.merge(fs_counts, on="days_diff", how="left").fillna(0)
        
        baseline = fs_counts["count"].mean() if not fs_counts.empty else 0
        
        fig_fs = px.bar(fs_counts, x="days_diff", y="count", color_discrete_sequence=["#f87171"])
        fig_fs.add_hline(y=baseline, line_dash="dot", line_color="#94a3b8", annotation_text="Baseline")
        fig_fs = apply_theme(fig_fs)
        st.plotly_chart(fig_fs, use_container_width=True)
        
        insight(f"Phát hiện tổng cộng <strong>{int(fs_counts['count'].sum())}</strong> tiền chấn trong tháng trước mainshock (Baseline: {baseline:.1f} trận/ngày).")
    else:
        st.info("Vui lòng chọn 1 mainshock.")

with tabs[1]:
    section_hdr("Aftershock & Định luật Omori (90 ngày sau)")
    if ms is not None:
        ast = nearby[(nearby["days_diff"] > 0) & (nearby["days_diff"] <= 90)]
        ast_counts = ast.groupby(ast["days_diff"].astype(int)).size().reset_index(name="count")
        
        all_as_days = pd.DataFrame({"days_diff": range(1, 91)})
        ast_counts = all_as_days.merge(ast_counts, on="days_diff", how="left").fillna(0)
        
        days_arr = ast_counts["days_diff"].values
        counts_arr = ast_counts["count"].values
        
        def omori(t, K, c, p): return K / (t + c)**p
        
        try:
            params, _ = curve_fit(omori, days_arr, counts_arr, p0=[max(counts_arr), 1.0, 1.0], bounds=([0, 0.01, 0.1], [1e5, 10, 3]))
            fitted = omori(days_arr, *params)
            ss_res = np.sum((counts_arr - fitted)**2)
            ss_tot = np.sum((counts_arr - counts_arr.mean())**2)
            r2 = 1 - (ss_res/ss_tot) if ss_tot > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            with c1: kpi("Tham số K", f"{params[0]:.1f}", icon="📈")
            with c2: kpi("Tham số p", f"{params[2]:.2f}", icon="📉")
            with c3: kpi("Mức độ Fit (R²)", f"{r2:.2f}", icon="🎯")
            
            fig_as = px.bar(ast_counts, x="days_diff", y="count", color_discrete_sequence=["#38bdf8"])
            fig_as.add_scatter(x=days_arr, y=fitted, mode="lines", line=dict(color="#c084fc", dash="dot"), name="Omori Fit")
            fig_as = apply_theme(fig_as)
            st.plotly_chart(fig_as, use_container_width=True)
            
            insight(f"Định luật Omori (n(t) = K/(t+c)ᵖ) fit dữ liệu với <strong>R² = {r2:.3f}</strong>. Hệ số suy giảm p = {params[2]:.2f}.")
            
        except Exception:
            fig_as = px.bar(ast_counts, x="days_diff", y="count", color_discrete_sequence=["#38bdf8"])
            fig_as = apply_theme(fig_as)
            st.plotly_chart(fig_as, use_container_width=True)
            insight("Không đủ dữ liệu hoặc chuỗi hội tụ để fit Omori Law.")
    else:
        st.info("Vui lòng chọn 1 mainshock.")

with tabs[2]:
    section_hdr("Tương quan: Depth × Magnitude")
    if set(["depth_km", "mag", "region_vi"]).issubset(df_all.columns):
        plot_df = df_all.dropna(subset=["depth_km", "mag"])
        if len(plot_df) > 10000:
            plot_df = plot_df.sample(10000, random_state=42)
            
        fig_scatter = px.scatter(
            plot_df, x="mag", y="depth_km", color="region_vi", opacity=0.6,
            color_discrete_sequence=["#7B2FBE","#c084fc","#38bdf8","#34d399","#f59e0b"]
        )
        fig_scatter.update_layout(yaxis=dict(autorange="reversed"))
        fig_scatter = apply_theme(fig_scatter)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        try:
            r, p = pearsonr(plot_df["mag"], plot_df["depth_km"])
            insight(f"Tương quan Pearson: <strong>r = {r:.3f}</strong> (p-value = {p:.3f}). Động đất càng sâu thì magnitude thường không lớn rõ rệt.")
        except Exception:
            pass

with tabs[3]:
    section_hdr("Ma trận tương quan đặc trưng")
    cols = ["mag", "depth_km", "felt", "cdi", "sig", "gap", "rms", "nst"]
    avail_cols = [c for c in cols if c in df_all.columns]
    
    if len(avail_cols) > 1:
        corr_df = df_all[avail_cols].dropna()
        if len(corr_df) > 20000:
            corr_df = corr_df.sample(20000, random_state=42)
            
        corr_mat = corr_df.corr().round(2)
        
        fig_corr = go.Figure(data=go.Heatmap(
            z=corr_mat.values,
            x=corr_mat.columns,
            y=corr_mat.index,
            colorscale="Purples",
            text=corr_mat.values,
            texttemplate="%{text}"
        ))
        fig_corr = apply_theme(fig_corr)
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Tìm cặp |r| > 0.3 (loại trừ đường chéo)
        pairs = []
        for i in range(len(corr_mat.columns)):
            for j in range(i+1, len(corr_mat.columns)):
                val = corr_mat.iloc[i, j]
                if abs(val) > 0.3:
                    pairs.append(f"{corr_mat.columns[i]}—{corr_mat.columns[j]} ({val})")
        
        pair_str = ", ".join(pairs) if pairs else "Không có tương quan tuyến tính nào đáng kể."
        insight(f"Các cặp có độ tương quan đáng kể (|r| > 0.3): <strong>{pair_str}</strong>.")
