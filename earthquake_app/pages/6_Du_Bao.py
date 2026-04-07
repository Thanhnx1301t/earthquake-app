import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.ui_components import (page_header, kpi, section_hdr, insight,
                                   sidebar_brand, sidebar_section,
                                   apply_theme, divider)
from utils.data_loader import load_data, REGIONS_VI

st.set_page_config(page_title="Dự báo & Giải pháp", page_icon="📈", layout="wide")
sidebar_brand()

df_all = load_data()
if df_all.empty:
    st.stop()

# Sidebar
sidebar_section("BỘ LỌC")
selected_region = st.sidebar.selectbox("Chọn vùng", options=REGIONS_VI)

page_header("Dự báo & Giải pháp", "Mô hình dự báo tần suất theo chuỗi thời gian & Giải pháp rủi ro", "📈")

df = df_all[df_all["region_vi"] == selected_region].copy()
if df.empty:
    st.warning("Không có dữ liệu.")
    st.stop()

tabs = st.tabs(["📈 Dự báo ARIMA", "🗺️ Risk Score", "📋 Giải pháp"])

with tabs[0]:
    section_hdr("Dự báo ARIMA / SARIMAX (24 tháng)")
    if "year" in df.columns and "month" in df.columns:
        monthly = df.groupby(["year", "month"]).size().reset_index(name="count")
        monthly["date"] = pd.to_datetime(monthly[["year", "month"]].assign(DAY=1))
        monthly = monthly.sort_values("date")
        
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            
            ts = monthly.set_index("date")["count"]
            # Train model
            with st.spinner("Đang chạy SARIMAX..."):
                model = SARIMAX(ts, order=(1,1,1), seasonal_order=(1,0,1,12), enforce_stationarity=False, enforce_invertibility=False)
                res = model.fit(disp=False)
                
                fcast = res.get_forecast(steps=24)
                fc_mean = fcast.predicted_mean
                fc_ci = fcast.conf_int(alpha=0.2) # 80% CI
            
            c1, c2, c3 = st.columns(3)
            with c1: kpi("TB Thực tế (hàng tháng)", f"{ts.mean():.1f}", icon="📅")
            with c2: kpi("TB Dự báo (24T)", f"{fc_mean.mean():.1f}", icon="🔮")
            with c3:
                trend = "Tăng" if fc_mean.iloc[-1] > fc_mean.iloc[0] else "Giảm"
                kpi("Xu hướng", trend, icon="📈" if trend=="Tăng" else "📉")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ts.index, y=ts.values, mode="lines", name="Thực tế", line=dict(color="#7B2FBE")))
            fig.add_trace(go.Scatter(x=fc_mean.index, y=fc_mean.values, mode="lines", name="Dự báo ARIMA", line=dict(color="#c084fc", dash="dash")))
            fig.add_trace(go.Scatter(
                x=pd.concat([pd.Series(fc_mean.index), pd.Series(fc_mean.index[::-1])]),
                y=pd.concat([fc_ci.iloc[:,1], fc_ci.iloc[:,0][::-1]]),
                fill="toself",
                fillcolor="rgba(123,47,190,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="Khoảng tin cậy 80%"
            ))
            fig = apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
            
            insight("Trục thời gian bao hàm 2 năm dự báo. Biến động seasonal (12 tháng) đã được tích hợp qua SARIMAX.")
            
        except ImportError:
            st.warning("Chưa có models. Đang dùng Moving Average fallback.")
            ma = monthly.copy()
            ma["rolling"] = ma["count"].rolling(12, min_periods=1).mean()
            fig = px.line(ma, x="date", y=["count", "rolling"], color_discrete_sequence=["#7B2FBE", "#c084fc"])
            fig = apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
            insight("Sử dụng Sliding Window trung bình thay vì SARIMAX due to model failure.")
        except Exception as e:
            st.error(f"Lỗi: {e}")

with tabs[1]:
    section_hdr("Risk Score (Toàn Châu Âu)")
    
    # Tính b-value cho 5 vùng
    risk_data = []
    n_years = max(1, df_all["year"].max() - df_all["year"].min() + 1)
    
    for r in REGIONS_VI:
        r_df = df_all[df_all["region_vi"] == r]
        freq = len(r_df) / n_years
        mag = r_df["mag"].mean() if not r_df["mag"].empty else 0
        
        # calc b value
        mags = r_df["mag"].dropna().values
        mags = mags[mags >= 3.0]
        b_val = 1.0 # default
        if len(mags) >= 10:
            m_vals = np.arange(3.0, mags.max() + 0.5, 0.5)
            log_n = [np.log10(np.sum(mags >= m)) for m in m_vals]
            valid = [(m, ln) for m, ln in zip(m_vals, log_n) if ln > 0]
            if len(valid) >= 3:
                x = np.array([v[0] for v in valid])
                y = np.array([v[1] for v in valid])
                slope, _, _, _, _ = linregress(x, y)
                b_val = -slope
                
        risk_data.append({"Vùng": r, "Freq": freq, "Mag": mag, "b": b_val})
        
    df_risk = pd.DataFrame(risk_data)
    
    def norm(s):
        if s.max() == s.min(): return np.zeros(len(s))
        return (s - s.min()) / (s.max() - s.min())
        
    df_risk["Risk Score"] = 0.35 * norm(df_risk["Freq"]) + 0.40 * norm(df_risk["Mag"]) + 0.25 * (1 - norm(df_risk["b"]))
    df_risk = df_risk.sort_values("Risk Score", ascending=False).reset_index(drop=True)
    
    df_risk["Mức độ"] = np.where(df_risk["Risk Score"] > 0.65, "🔴 Cao", 
                                 np.where(df_risk["Risk Score"] > 0.35, "🟡 Trung bình", "🟢 Thấp"))
    
    # Bar chart
    fig_r = px.bar(df_risk, x="Risk Score", y="Vùng", orientation="h", color="Risk Score",
                   color_continuous_scale=[[0, "#22c55e"], [0.5, "#eab308"], [1, "#ef4444"]])
    fig_r = apply_theme(fig_r)
    fig_r.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_r, use_container_width=True)
    
    st.dataframe(df_risk[["Vùng", "Freq", "Mag", "b", "Risk Score", "Mức độ"]].style.format({"Freq": "{:.1f}", "Mag": "{:.2f}", "b": "{:.2f}", "Risk Score": "{:.1%}"}), use_container_width=True)

with tabs[2]:
    section_hdr("Giải pháp đề xuất")
    for _, row in df_risk.iterrows():
        rt = row["Vùng"]
        rs = row["Risk Score"]
        level = row["Mức độ"]
        
        expand_state = rs > 0.5
        with st.expander(f"{rt} — {level} (Risk: {rs*100:.1f}%)", expanded=expand_state):
            if rs > 0.65:
                st.markdown("> **Nguy cơ rất cao:** Yêu cầu nâng cấp toàn bộ tiêu chuẩn kháng chấn đối với các toà nhà cao tầng. Vận hành hệ thống cảnh báo sớm (EEW Early Earthquake Warning) ở các thành phố lớn. Lập bản đồ đứt gãy vi mô ngay lập tức.")
            elif rs > 0.35:
                st.markdown("> **Nguy cơ trung bình:** Tăng cường mật độ trạm đo địa chấn khu vực. Thường xuyên kiểm định công trình công cộng cũ.")
            else:
                st.markdown("> **Nguy cơ thấp:** Duy trì trạng thái quan trắc hiện tại. Yêu cầu cập nhật đánh giá định kỳ sau mỗi 5 năm hoặc khi có xung chấn cục bộ.")
            
            insight(f"Đề xuất cho {rt} dựa trên điểm Risk Score tích hợp.", kind="info" if rs <= 0.35 else "warning" if rs <= 0.65 else "error")
