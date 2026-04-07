import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import zscore, linregress
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.ui_components import (page_header, kpi, section_hdr, insight,
                                   sidebar_brand, sidebar_section,
                                   apply_theme, divider)
from utils.data_loader import load_data, filter_df, REGIONS_VI

st.set_page_config(page_title="Bất thường & Xác suất", page_icon="⚠️", layout="wide")
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

page_header("Bất thường & Xác suất", "Phát hiện anomaly, Gutenberg-Richter và xác suất Poisson", "⚠️")

df = filter_df(df_all, regions=selected_regions, year_range=selected_years)
if df.empty:
    st.warning("Không có dữ liệu.")
    st.stop()

tabs = st.tabs(["📈 Z-score & IForest", "📐 Gutenberg-Richter", "🎲 Poisson", "📊 Mann-Kendall"])

with tabs[0]:
    section_hdr("Phát hiện bất thường với Z-Score")
    if "year" in df.columns and "month" in df.columns:
        monthly = df.groupby(["year", "month"]).size().reset_index(name="count")
        monthly["date"] = pd.to_datetime(monthly[["year", "month"]].assign(DAY=1))
        
        monthly["z_score"] = zscore(monthly["count"])
        monthly["is_anomaly"] = np.abs(monthly["z_score"]) > 2
        monthly["color"] = monthly["is_anomaly"].map({True: "#ef4444", False: "#7B2FBE"})
        
        fig_z = px.bar(monthly, x="date", y="count", color="color", color_discrete_map="identity")
        fig_z.add_hline(y=monthly["count"].mean() + 2*monthly["count"].std(), line_dash="dash", line_color="#ef4444")
        fig_z = apply_theme(fig_z)
        st.plotly_chart(fig_z, use_container_width=True)
        
        n_anom = monthly["is_anomaly"].sum()
        insight(f"Có <strong>{n_anom}</strong> tháng vượt ngưỡng 2σ, được xem là bất thường.")

    section_hdr("Isolation Forest (Mag & Depth)")
    if "mag" in df.columns and "depth_km" in df.columns:
        try:
            from sklearn.ensemble import IsolationForest
            df_iso = df.dropna(subset=["mag", "depth_km"]).copy()
            if len(df_iso) > 15000:
                df_iso = df_iso.sample(15000, random_state=42)
                
            clf = IsolationForest(contamination=0.05, random_state=42)
            df_iso["anomaly"] = clf.fit_predict(df_iso[["mag", "depth_km"]])
            df_iso["color"] = df_iso["anomaly"].map({1: "#7B2FBE", -1: "#ef4444"})
            
            c1, c2 = st.columns(2)
            with c1:
                fig_if = px.scatter(df_iso, x="mag", y="depth_km", color="color", color_discrete_map="identity", opacity=0.6)
                fig_if.update_layout(yaxis=dict(autorange="reversed"))
                fig_if = apply_theme(fig_if)
                st.plotly_chart(fig_if, use_container_width=True)
                
            with c2:
                if set(["latitude", "longitude"]).issubset(df_iso.columns):
                    anom = df_iso[df_iso["anomaly"] == -1]
                    fig_map = px.scatter_mapbox(
                        anom, lat="latitude", lon="longitude", color="mag",
                        color_continuous_scale=[[0, "#ef4444"], [1, "#fca5a5"]],
                        mapbox_style="carto-darkmatter", zoom=2
                    )
                    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                    fig_map = apply_theme(fig_map)
                    st.plotly_chart(fig_map, use_container_width=True)
                    
            insight(f"Isolation Forest tách lọc ra nhóm 5% (% contamination) các điểm cực trị ngoài biên quần thể.")
        except Exception as e:
            st.error(f"Lỗi: {e}")

with tabs[1]:
    section_hdr("Định luật Gutenberg-Richter")
    if "mag" in df.columns and "region_vi" in df.columns:
        try:
            gr_data = []
            fig_gr = go.Figure()
            for r in REGIONS_VI:
                mags = df[df["region_vi"] == r]["mag"].dropna().values
                mags = mags[mags >= 3.0]
                if len(mags) >= 10:
                    m_vals = np.arange(3.0, mags.max() + 0.5, 0.5)
                    log_n = [np.log10(np.sum(mags >= m)) for m in m_vals]
                    
                    valid = [(m, ln) for m, ln in zip(m_vals, log_n) if ln > 0]
                    if len(valid) >= 3:
                        x = np.array([v[0] for v in valid])
                        y = np.array([v[1] for v in valid])
                        slope, intercept, r_val, _, _ = linregress(x, y)
                        
                        b_val = -slope
                        a_val = intercept
                        
                        eval_star = "🟢 Tốt" if b_val > 1.2 else "🔴 Nguy hiểm" if b_val < 0.8 else "🟡 Cảnh báo"
                        gr_data.append({"Vùng": r, "a-value": a_val, "b-value": b_val, "Đánh giá": eval_star})
                        
                        # Plot
                        fig_gr.add_trace(go.Scatter(x=x, y=y, mode="markers", name=r))
                        fig_gr.add_trace(go.Scatter(x=x, y=intercept - b_val * x, mode="lines", line=dict(dash="dash"), name=f"Fit {r}"))

            if gr_data:
                fig_gr.update_layout(xaxis_title="Magnitude (M)", yaxis_title="Log10(N)")
                fig_gr = apply_theme(fig_gr)
                st.plotly_chart(fig_gr, use_container_width=True)
                
                df_b = pd.DataFrame(gr_data)
                st.dataframe(df_b.style.format({"a-value": "{:.2f}", "b-value": "{:.3f}"}), use_container_width=True)
                
                min_b = df_b.loc[df_b["b-value"].idxmin()]
                insight(f"Vùng <strong>{min_b['Vùng']}</strong> có b-value thấp nhất ({min_b['b-value']:.2f}), cho thấy nguy cơ xảy ra động đất cường độ lớn cao nhất.", kind="warning")
            else:
                st.info("Không đủ dữ liệu M>=3.0 để tính toán G-R.")
        except Exception as e:
            st.error(f"Lỗi: {e}")

with tabs[2]:
    section_hdr("Xác suất Poisson P(≥1)")
    if "year" in df.columns and "mag" in df.columns:
        n_years = max(1, df["year"].max() - df["year"].min() + 1)
        
        for m_th in [4.0, 5.0, 6.0]:
            st.markdown(f"<p style='color:#c084fc;font-weight:600;margin-top:1rem'>Ngưỡng Magnitude ≥ {m_th}</p>", unsafe_allow_html=True)
            poisson_data = []
            for r in REGIONS_VI:
                count = len(df[(df["region_vi"] == r) & (df["mag"] >= m_th)])
                lam = count / n_years
                
                row = {"Vùng": r}
                for T in [1, 5, 10]:
                    prob = (1 - np.exp(-lam * T)) * 100
                    row[f"Trong {T} năm"] = f"{prob:.1f}%"
                poisson_data.append(row)
                
            st.dataframe(pd.DataFrame(poisson_data), use_container_width=True)
            
        insight("Xác suất Poisson giả định các diễn biến M lớn là độc lập thống kê.")

with tabs[3]:
    section_hdr("Mann-Kendall Trend Test")
    if "year" in df.columns and "month" in df.columns:
        try:
            import pymannkendall as mk
            
            mk_data = []
            for r in REGIONS_VI:
                df_r = df[df["region_vi"] == r].groupby(["year", "month"]).size()
                if len(df_r) > 12:
                    res = mk.original_test(df_r.values)
                    mk_data.append({"Vùng": r, "τ": res.Tau, "p-value": res.p, "Xu hướng": res.trend})
            
            if mk_data:
                df_mk = pd.DataFrame(mk_data)
                st.dataframe(df_mk, use_container_width=True)
            
        except ImportError:
            st.warning("Chưa cài đặt `pymannkendall`. Sử dụng Rolling average 12 tháng làm phương án dự phòng.")
            
        # Line chart rolling avg 12 month
        df_rolling = df.groupby(["region_vi", "year", "month"]).size().reset_index(name="count")
        df_rolling["date"] = pd.to_datetime(df_rolling[["year", "month"]].assign(DAY=1))
        df_rolling = df_rolling.sort_values(["region_vi", "date"])
        
        df_rolling["rolling"] = df_rolling.groupby("region_vi")["count"].transform(lambda x: x.rolling(12, min_periods=1).mean())
        
        fig_r = px.line(df_rolling, x="date", y="rolling", color="region_vi",
                        color_discrete_sequence=["#7B2FBE","#c084fc","#38bdf8","#34d399","#f59e0b"])
        fig_r = apply_theme(fig_r)
        st.plotly_chart(fig_r, use_container_width=True)
        
        insight("Mann-Kendall / Rolling average giúp xác nhận chuỗi sự kiện có tính định hướng tăng cường theo thời gian hay không.")
