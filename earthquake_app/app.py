import streamlit as st

st.set_page_config(
    page_title="Earthquake Analytics · Châu Âu",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.ui_components import inject_css, sidebar_brand
inject_css()
sidebar_brand()

# Landing page với stats cards
st.markdown("""
<div style="text-align:center;padding:5rem 2rem 3rem">
  <div style="font-size:3.5rem;margin-bottom:1.2rem">🌍</div>
  <h1 style="font-size:2.4rem;font-weight:800;color:#f8fafc;margin-bottom:.6rem">
    Earthquake Analytics
  </h1>
  <p style="color:#94a3b8;font-size:1rem;max-width:52ch;margin:0 auto 2.5rem;line-height:1.7">
    Khai thác dữ liệu địa chấn <strong style="color:#c084fc">Châu Âu 2005–2025</strong>
    — phân tích thực trạng, xu hướng và rủi ro theo từng vùng địa lý.
  </p>
  <!-- 4 stat cards -->
  <div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-bottom:2.5rem">
    <div style="background:#1e1e3a;border:1px solid rgba(123,47,190,.3);border-radius:10px;padding:14px 22px;min-width:130px">
      <p style="margin:0;font-size:.65rem;color:#64748b;text-transform:uppercase">Modules</p>
      <p style="margin:4px 0 0;font-size:1.3rem;font-weight:700;color:#c084fc">6 Trang</p>
    </div>
    <div style="background:#1e1e3a;border:1px solid rgba(123,47,190,.3);border-radius:10px;padding:14px 22px;min-width:130px">
      <p style="margin:0;font-size:.65rem;color:#64748b;text-transform:uppercase">Nguồn</p>
      <p style="margin:4px 0 0;font-size:1.3rem;font-weight:700;color:#c084fc">EMSC/USGS</p>
    </div>
    <div style="background:#1e1e3a;border:1px solid rgba(123,47,190,.3);border-radius:10px;padding:14px 22px;min-width:130px">
      <p style="margin:0;font-size:.65rem;color:#64748b;text-transform:uppercase">Giai đoạn</p>
      <p style="margin:4px 0 0;font-size:1.3rem;font-weight:700;color:#c084fc">2005–2025</p>
    </div>
    <div style="background:#1e1e3a;border:1px solid rgba(123,47,190,.3);border-radius:10px;padding:14px 22px;min-width:130px">
      <p style="margin:0;font-size:.65rem;color:#64748b;text-transform:uppercase">Khu vực</p>
      <p style="margin:4px 0 0;font-size:1.3rem;font-weight:700;color:#c084fc">5 Vùng</p>
    </div>
  </div>
  <p style="color:#475569;font-size:.88rem">← Chọn trang phân tích từ thanh sidebar</p>
</div>
""", unsafe_allow_html=True)
