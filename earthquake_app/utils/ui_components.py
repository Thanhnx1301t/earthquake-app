import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }

.stApp { background: #0f0f1a !important; }

section[data-testid="stSidebar"] {
    background: #13131f !important;
    border-right: 1px solid rgba(123,47,190,0.25) !important;
}
.main .block-container {
    padding-top: 1.8rem !important;
    max-width: 1280px !important;
}
h1,h2,h3 { color: #f8fafc !important; }

/* Sidebar nav - HIDE NATIVE NAVIGATION, ONLY KEEP FILTERS */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Metric */
[data-testid="stMetric"] {
    background: #1e1e3a !important;
    border: 1px solid rgba(123,47,190,0.3) !important;
    border-radius: 12px !important; padding: 1rem 1.2rem !important;
}
[data-testid="stMetricValue"] {
    color: #c084fc !important; font-size: 1.9rem !important; font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important; font-size: 0.78rem !important;
    text-transform: uppercase; letter-spacing: 0.06em;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg,#7B2FBE,#9b59d0) !important;
    color: #fff !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 18px rgba(123,47,190,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(123,47,190,0.4) !important;
    color: #c084fc !important;
}

/* Select */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: #1e1e3a !important;
    border: 1px solid rgba(123,47,190,0.3) !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
}
.stSelectbox label, .stMultiSelect label,
.stSlider label, .stNumberInput label {
    color: #94a3b8 !important; font-size: 0.78rem !important;
    text-transform: uppercase; letter-spacing: 0.05em;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #1e1e3a !important; border-radius: 10px !important;
    padding: 4px !important; gap: 4px;
    border-bottom: 1px solid rgba(123,47,190,0.25) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #64748b !important;
    border-radius: 6px !important; font-weight: 500 !important;
    font-size: 0.87rem !important; transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#7B2FBE,#9b59d0) !important;
    color: #fff !important; box-shadow: 0 2px 10px rgba(123,47,190,0.4) !important;
}

/* Expander */
.streamlit-expander {
    background: #1e1e3a !important;
    border: 1px solid rgba(123,47,190,0.25) !important;
    border-radius: 10px !important;
}
.streamlit-expander header { color: #e2e8f0 !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(123,47,190,0.25) !important;
    border-radius: 10px !important; overflow: hidden !important;
}

hr { border-color: rgba(123,47,190,0.2) !important; margin: 1.2rem 0 !important; }
</style>
"""


# ── BLOCK NAVIGATION MESSAGES ─────────────────────────────────────────────────
# Streamlit KHÔNG được gửi message điều hướng ra HTML bên ngoài.
# Luồng 1 chiều tuyệt đối: HTML sidebar → showPage() → Streamlit hiển thị.
_BLOCK_NAV_JS = """
<script>
(function() {
  // Override parent.postMessage để chặn SYNC_SIDEBAR và navigate messages
  try {
    var _orig = window.parent.postMessage.bind(window.parent);
    window.parent.postMessage = function(msg, origin) {
      if (msg && typeof msg === 'object' &&
          (msg.type === 'SYNC_SIDEBAR' || msg.type === 'navigate' ||
           msg.type === 'page_change' || msg.type === 'streamlit:navigation')) {
        return; // Chặn hoàn toàn
      }
      _orig(msg, origin);
    };
  } catch(e) {}

  try {
    var _origTop = window.top.postMessage.bind(window.top);
    window.top.postMessage = function(msg, origin) {
      if (msg && typeof msg === 'object' &&
          (msg.type === 'SYNC_SIDEBAR' || msg.type === 'navigate' ||
           msg.type === 'page_change')) {
        return;
      }
      _origTop(msg, origin);
    };
  } catch(e) {}
})();
</script>
"""

def inject_css():
    """Inject CSS + JS chặn navigation. Gọi đầu tiên trong mỗi Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
    # Chặn Streamlit gửi message điều hướng ra HTML bên ngoài (chống loop)
    st.markdown(_BLOCK_NAV_JS, unsafe_allow_html=True)

PLY = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(family="Inter,sans-serif", color="#cbd5e1", size=12),
    title=dict(font=dict(color="#fff", size=14), x=0.01, xanchor="left"),
    xaxis=dict(
        gridcolor="rgba(123,47,190,0.15)", linecolor="rgba(123,47,190,0.3)",
        tickcolor="#94a3b8", tickfont=dict(color="#94a3b8"), zeroline=False
    ),
    yaxis=dict(
        gridcolor="rgba(123,47,190,0.15)", linecolor="rgba(123,47,190,0.3)",
        tickcolor="#94a3b8", tickfont=dict(color="#94a3b8"), zeroline=False
    ),
    legend=dict(
        bgcolor="rgba(19,19,31,0.85)", bordercolor="rgba(123,47,190,0.3)",
        borderwidth=1, font=dict(color="#cbd5e1")
    ),
    hoverlabel=dict(
        bgcolor="#1e1e3a", bordercolor="rgba(123,47,190,0.6)",
        font=dict(color="#fff", family="Inter")
    ),
    colorway=["#7B2FBE","#c084fc","#38bdf8","#34d399","#f59e0b","#f87171","#a78bfa","#fb923c"],
    margin=dict(l=40, r=20, t=50, b=40),
)

MAP_STYLE = "carto-darkmatter"

def apply_theme(fig):
    """Áp dụng dark theme cho mọi Plotly chart"""
    fig.update_layout(**PLY)
    return fig

def page_header(title: str, subtitle: str = "", icon: str = "🌍"):
    """Header chuẩn cho mỗi page — gọi NGAY SAU inject_css()"""
    inject_css()
    
    st.markdown(f"""
    <div style="margin-bottom:1.6rem">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
        <div style="background:linear-gradient(135deg,#7B2FBE,#9b59d0);
             border-radius:10px;width:44px;height:44px;display:flex;
             align-items:center;justify-content:center;font-size:22px;
             box-shadow:0 3px 14px rgba(123,47,190,0.4);flex-shrink:0">{icon}</div>
        <div>
          <h1 style="margin:0;font-size:1.55rem;font-weight:700;
               color:#fff;line-height:1.2">{title}</h1>
          <p style="margin:2px 0 0;color:#94a3b8;font-size:.83rem">{subtitle}</p>
        </div>
      </div>
      <div style="height:1px;background:linear-gradient(90deg,
           rgba(123,47,190,0.7),rgba(123,47,190,0.15),transparent);
           margin-top:10px"></div>
    </div>""", unsafe_allow_html=True)


def kpi(label: str, value: str, delta: str = None, icon: str = "📊"):
    """Card KPI với gradient value — thay thế st.metric()"""
    delta_html = ""
    if delta:
        c = "#22c55e" if "+" in str(delta) else "#ef4444"
        delta_html = f'<p style="margin:4px 0 0;font-size:.8rem;color:{c}">{delta}</p>'
    st.markdown(f"""
    <div style="background:#1e1e3a;border:1px solid rgba(123,47,190,.3);
         border-radius:12px;padding:18px 20px;height:100%">
      <p style="margin:0 0 8px;font-size:.72rem;color:#94a3b8;
         text-transform:uppercase;letter-spacing:.07em">{icon}&nbsp;{label}</p>
      <p style="margin:0;font-size:1.85rem;font-weight:700;
         background:linear-gradient(135deg,#7B2FBE,#9b59d0);
         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
         background-clip:text;line-height:1.1">{value}</p>
      {delta_html}
    </div>""", unsafe_allow_html=True)


def section_hdr(text: str, badge: str = None):
    """Tiêu đề section với accent màu tím"""
    badge_html = ""
    if badge:
        badge_html = (f'<span style="margin-left:10px;padding:2px 10px;'
                      f'background:rgba(123,47,190,.15);border:1px solid rgba(123,47,190,.35);'
                      f'border-radius:999px;font-size:.7rem;font-weight:600;color:#c084fc">'
                      f'{badge}</span>')
    st.markdown(f"""
    <p style="font-size:1.05rem;font-weight:700;color:#f1f5f9;
       margin:1.4rem 0 .8rem;display:flex;align-items:center">
      <span style="background:linear-gradient(135deg,#7B2FBE,#9b59d0);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text">{text}</span>{badge_html}
    </p>""", unsafe_allow_html=True)


def insight(text: str, kind: str = "info"):
    """
    Box insight có màu theo loại:
    kind = "info" (tím) | "success" (xanh) | "warning" (vàng) | "error" (đỏ)
    text hỗ trợ HTML: <strong>, <em>, v.v.
    """
    cfg = {
        "info":    ("#7B2FBE", "rgba(123,47,190,.12)", "💡"),
        "success": ("#22c55e", "rgba(34,197,94,.1)",   "✅"),
        "warning": ("#eab308", "rgba(234,179,8,.08)",  "⚠️"),
        "error":   ("#ef4444", "rgba(239,68,68,.08)",  "❌"),
    }
    bc, bg, ic = cfg.get(kind, cfg["info"])
    st.markdown(f"""
    <div style="background:{bg};border-left:3px solid {bc};
         border-radius:8px;padding:12px 16px;margin:10px 0;
         color:#cbd5e1;font-size:.86rem;line-height:1.6">
      {ic}&nbsp;{text}
    </div>""", unsafe_allow_html=True)


def sidebar_brand():
    """Logo + tên app ở đầu sidebar — gọi ở đầu mỗi page"""
    st.sidebar.markdown("""
    <div style="padding:14px 10px 18px;border-bottom:1px solid rgba(123,47,190,.25);margin-bottom:6px">
      <div style="display:flex;align-items:center;gap:9px">
        <div style="background:linear-gradient(135deg,#7B2FBE,#9b59d0);
             border-radius:9px;width:34px;height:34px;display:flex;
             align-items:center;justify-content:center;font-size:17px;
             box-shadow:0 2px 12px rgba(123,47,190,.4)">🌍</div>
        <div>
          <p style="margin:0;font-size:.9rem;font-weight:700;color:#e2e8f0">Earthquake Analytics</p>
          <p style="margin:0;font-size:.65rem;color:#64748b">Châu Âu · 2005–2025</p>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)


def sidebar_section(label: str):
    """Nhãn phân nhóm filter trong sidebar"""
    st.sidebar.markdown(
        f'<p style="margin:12px 0 4px 6px;font-size:.65rem;font-weight:600;'
        f'color:#64748b;text-transform:uppercase;letter-spacing:.08em">{label}</p>',
        unsafe_allow_html=True)


def divider():
    """Đường kẻ phân cách section"""
    st.markdown('<hr style="border-color:rgba(123,47,190,.2);margin:1rem 0">',
                unsafe_allow_html=True)
