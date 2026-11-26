"""ui.py - giao diện chung: CSS, màu house style, hàm định dạng, style Plotly."""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

import house_style as hs

P = hs.P
INK, MUTED, GRID = hs.TEXT, hs.MUTED, hs.GRID

# Màu chrome (nền, thẻ) lấy từ bảng màu nhóm + biến thể rất nhạt để nền không "ăn" màu biểu đồ
SEA_DEEP, SEA, SEA_LIGHT = P["Forest"], "#2F7D8C", P["Blue Berry"]
SAND, SAND_DARK = "#FBF8F1", "#F1EADB"
SUN = P["Florida Oranges"]

# Quy ước màu ngữ nghĩa (house style): <100 Poppy | quanh 100 Good Surf | >100 Pea Flower
STATUS_COLOR = {
    "Chưa phục hồi": hs.STATUS["below"],
    "Quanh mốc 2019": hs.STATUS["at"],
    "Vượt 2019": hs.STATUS["above"],
    "Chưa có mốc 2019": "#D9DCDD",
}
CLUSTER_COLOR = {1: P["Pea Flower"], 2: P["Florida Oranges"], 3: P["Forest"], 4: P["Dusty Berry"]}

_EXTRA = ["Blue Berry", "Dusty Berry", "Gold Velvet", "Grape Juice", "Spring Leaves", "Bubble-gum",
          "Night Forest", "Poppy", "Tea Green", "Lilacs", "Dry Earth", "Good Surf"]


def market_colors(markets: list[str]) -> dict[str, str]:
    """Màu cố định theo thị trường: 6 thị trường chính dùng đúng màu house style, còn lại lấy màu phụ ổn định."""
    colors = dict(hs.MARKET_COLORS)
    rest = [m for m in sorted(markets) if m not in colors]
    for i, m in enumerate(rest):
        colors[m] = P[_EXTRA[i % len(_EXTRA)]]
    return colors


# ---------------------------------------------------------------- định dạng (kiểu Việt Nam 1.234,5)
def n0(x) -> str:
    return "–" if pd.isna(x) else hs.fmt_int(x)


def n1(x) -> str:
    return "–" if pd.isna(x) else hs._vn(f"{x:,.1f}")


def pct(x, signed=True) -> str:
    if pd.isna(x):
        return "–"
    return hs._vn(f"{x:+,.1f}" if signed else f"{x:,.1f}") + "%"


def big(x) -> str:
    """1.234.567 -> '1,23 triệu'."""
    if pd.isna(x):
        return "–"
    if abs(x) >= 1e6:
        return hs._vn(f"{x / 1e6:,.2f}") + " triệu"
    if abs(x) >= 1e3:
        return hs._vn(f"{x / 1e3:,.0f}") + " nghìn"
    return hs.fmt_int(x)


def mlabel(d) -> str:
    d = pd.Timestamp(d)
    return f"T{d.month}/{d.year}"


# ---------------------------------------------------------------- CSS
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Be Vietnam Pro', 'Segoe UI', Roboto, Arial, sans-serif; }}
.stApp {{ background: {SAND}; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 4rem; max-width: 1280px; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* sidebar: biển sâu */
section[data-testid="stSidebar"] > div {{ background: linear-gradient(180deg, {SEA_DEEP} 0%, #1D4A55 100%); }}
section[data-testid="stSidebar"] * {{ color: #F3EFE4 !important; }}
section[data-testid="stSidebar"] .stRadio label {{ padding: .35rem .2rem; border-radius: 10px; }}
section[data-testid="stSidebar"] .stRadio label:hover {{ background: rgba(255,255,255,.08); }}
.brand {{ font-weight: 800; font-size: 1.35rem; letter-spacing: .2px; margin: .2rem 0 0; }}
.brand small {{ display:block; font-weight:500; font-size:.78rem; opacity:.8; letter-spacing:.3px; }}

/* hero */
.hero {{
  position: relative; overflow: hidden; border-radius: 26px; padding: 2.1rem 2.3rem 3.2rem; color: #fff;
  background: radial-gradient(1200px 400px at 90% -10%, rgba(239,206,123,.55), transparent 60%),
              linear-gradient(135deg, {SEA_DEEP} 0%, {SEA} 55%, {SEA_LIGHT} 100%);
  box-shadow: 0 18px 40px -18px rgba(37,83,63,.55);
}}
.hero h1 {{ font-size: 2.15rem; line-height: 1.2; margin: .35rem 0 .6rem; font-weight: 800; color:#fff; }}
.hero p  {{ font-size: 1.04rem; max-width: 760px; opacity: .95; margin: 0; }}
.hero .chip {{ display:inline-block; background: rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.35);
  padding: .22rem .75rem; border-radius: 999px; font-size: .8rem; font-weight:600; margin-right:.4rem; backdrop-filter: blur(4px); }}
.hero svg {{ position:absolute; left:0; bottom:-1px; width:100%; height:60px; }}
.hero .sun {{ position:absolute; right:38px; top:26px; font-size:3.2rem; filter: drop-shadow(0 4px 10px rgba(0,0,0,.2)); }}

/* thẻ KPI */
.kpi {{ background:#fff; border-radius:18px; padding:1rem 1.15rem; border:1px solid {SAND_DARK};
  box-shadow: 0 6px 18px -12px rgba(43,43,35,.35); height:100%; transition: transform .15s ease, box-shadow .15s ease; }}
.kpi:hover {{ transform: translateY(-2px); box-shadow: 0 14px 26px -14px rgba(43,43,35,.4); }}
.kpi .lab {{ font-size:.78rem; font-weight:600; color:{MUTED}; text-transform:uppercase; letter-spacing:.5px; }}
.kpi .val {{ font-size:1.85rem; font-weight:800; color:{INK}; line-height:1.15; margin:.15rem 0; }}
.kpi .sub {{ font-size:.85rem; color:{MUTED}; }}
.up {{ color:{P['Pea Flower']}; font-weight:700; }} .down {{ color:{P['Poppy']}; font-weight:700; }}

/* chương câu chuyện */
.chapter {{ display:flex; align-items:center; gap:.8rem; margin: 2.2rem 0 .3rem; }}
.chapter .no {{ background:{SUN}; color:#fff; width:2.3rem; height:2.3rem; border-radius:50%; display:flex;
  align-items:center; justify-content:center; font-weight:800; box-shadow:0 6px 14px -6px {SUN}; flex:none; }}
.chapter .tt {{ font-size:1.35rem; font-weight:800; color:{INK}; line-height:1.25; }}
.chapter-sub {{ color:{MUTED}; margin: 0 0 .6rem 3.1rem; font-size:.95rem; }}

.card {{ background:#fff; border-radius:18px; padding:1.1rem 1.25rem; border:1px solid {SAND_DARK};
  box-shadow: 0 6px 18px -14px rgba(43,43,35,.4); }}
.card.sun {{ background: linear-gradient(135deg, #FFF6DD, #FCE8C2); border-color:#F2D9A0; }}
.card.sea {{ background: linear-gradient(135deg, #E8F3F6, #DCEBF0); border-color:#C4DCE4; }}
.card h4 {{ margin:.1rem 0 .4rem; font-size:1.02rem; color:{INK}; }}
.card p, .card li {{ font-size:.93rem; color:#3B3F3A; }}
.tag {{ display:inline-block; padding:.12rem .6rem; border-radius:999px; font-size:.74rem; font-weight:700; margin:.1rem .25rem .1rem 0; }}
.chart-title {{ font-weight:800; font-size:1.12rem; color:{INK}; margin:.2rem 0 0; }}
.chart-sub {{ color:{MUTED}; font-size:.86rem; margin:0 0 .35rem; }}
.src {{ color:{MUTED}; font-size:.76rem; margin-top:-.4rem; }}
.guide-box {{ background:#fff; border:1px solid {SAND_DARK}; border-left:4px solid {SEA}; border-radius:12px;
  padding:.75rem 1rem; margin:.2rem 0 .85rem; font-size:.88rem; color:{INK}; }}
.guide-box .guide-title {{ font-weight:700; margin-bottom:.25rem; color:{SEA_DEEP}; }}
.scale-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:.6rem; margin-top:.45rem; }}
.scale-item {{ background:{SAND}; border:1px solid {SAND_DARK}; border-radius:10px; padding:.5rem .7rem; }}
.scale-item .num {{ font-size:1.25rem; font-weight:800; color:{INK}; line-height:1.15; }}
.scale-item .desc {{ font-size:.8rem; color:{MUTED}; margin-top:.15rem; }}
.pill-ok {{ background:#E6F1E1; color:#25533F; }} .pill-warn {{ background:#FCE8C2; color:#8A5A10; }}
.pill-bad {{ background:#FBDDD0; color:#9C3A08; }}

/* tab */
.stTabs [data-baseweb="tab-list"] {{ gap: .3rem; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 12px 12px 0 0; padding: .55rem 1rem; font-weight:600; }}
.stTabs [aria-selected="true"] {{ background:#fff; }}
div[data-testid="stMetric"] {{ background:#fff; border:1px solid {SAND_DARK}; border-radius:16px; padding:.7rem .9rem; }}
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {{ border-radius: 12px; font-weight:700; }}
</style>
"""

WAVE = ("<svg viewBox='0 0 1440 80' preserveAspectRatio='none'><path fill='%s' d='M0,40 C240,90 480,0 720,30 "
        "C960,60 1200,90 1440,40 L1440,80 L0,80 Z'/></svg>" % SAND)


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, text: str, chips: list[str], icon: str = "🏝️"):
    chips_html = "".join(f"<span class='chip'>{html.escape(c)}</span>" for c in chips)
    st.markdown(f"<div class='hero'><div class='sun'>{icon}</div>{chips_html}<h1>{title}</h1><p>{text}</p>{WAVE}</div>",
                unsafe_allow_html=True)


def kpi(col, label: str, value: str, sub: str = ""):
    col.markdown(f"<div class='kpi'><div class='lab'>{label}</div><div class='val'>{value}</div>"
                 f"<div class='sub'>{sub}</div></div>", unsafe_allow_html=True)


def chapter(no: int, title: str, sub: str = ""):
    st.markdown(f"<div class='chapter'><div class='no'>{no}</div><div class='tt'>{title}</div></div>"
                + (f"<div class='chapter-sub'>{sub}</div>" if sub else ""), unsafe_allow_html=True)


def chart_title(headline: str, sub: str = ""):
    head_html = f"<div class='chart-title'>{headline}</div>" if headline else ""
    sub_html = f"<div class='chart-sub'>{sub}</div>" if sub else ""
    if head_html or sub_html:
        st.markdown(head_html + sub_html, unsafe_allow_html=True)


def set_title(fig, title: str, top_margin: int | None = None):
    """Gắn tiêu đề đồng nhất ngay trong figure Plotly và đảm bảo đủ lề trên."""
    cur_m = fig.layout.margin.to_plotly_json() if fig.layout.margin else {}
    min_top = top_margin if top_margin is not None else 56
    if (cur_m.get("t") or 0) < min_top:
        cur_m["t"] = min_top
    fig.update_layout(
        margin=cur_m,
        title=dict(
            text=f"<b>{title}</b>",
            x=0.01,
            xanchor="left",
            y=0.97,
            yanchor="top",
            font=dict(
                family="Be Vietnam Pro, Segoe UI, Roboto, Arial, sans-serif",
                size=16,
                color=INK,
            ),
        ),
    )
    return fig


def source(text: str):
    st.markdown(f"<div class='src'>Nguồn: {text}</div>", unsafe_allow_html=True)


def card(body: str, kind: str = ""):
    st.markdown(f"<div class='card {kind}'>{body}</div>", unsafe_allow_html=True)


def page_header(icon: str, title: str, text: str, guide: str = ""):
    """Hiển thị tiêu đề trang, mô tả và hướng dẫn đọc ngắn (nếu có)."""
    st.markdown(
        f"<h2 style='margin:.2rem 0 .15rem;font-weight:800'>{icon} {title}</h2>"
        f"<p style='color:{MUTED};margin:0 0 .65rem;font-size:1rem'>{text}</p>",
        unsafe_allow_html=True,
    )
    if guide:
        st.markdown(
            f"<div class='guide-box'><div class='guide-title'>Hướng dẫn đọc nhanh</div>{guide}</div>",
            unsafe_allow_html=True,
        )


def guide_box(title: str, body_html: str):
    """Khung chú giải gọn đặt dưới bộ lọc hoặc trước biểu đồ."""
    st.markdown(
        f"<div class='guide-box'><div class='guide-title'>{title}</div>{body_html}</div>",
        unsafe_allow_html=True,
    )


def style_fig(fig, height: int = 420, legend: bool = True, margin=None):
    """Style Plotly theo house style: nền trong, lưới nhạt, font Be Vietnam Pro, số kiểu Việt Nam."""
    fig.update_layout(
        height=height, template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Be Vietnam Pro, Segoe UI, Roboto, Arial, sans-serif", size=13, color=INK),
        margin=margin or dict(l=10, r=10, t=10, b=10), separators=",.",
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor=GRID),
        showlegend=legend,
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(
        showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED, size=12),
        title_font=dict(size=13, color=INK), automargin=True, zeroline=False,
    )
    fig.update_yaxes(
        gridcolor=GRID, linecolor="rgba(0,0,0,0)", tickfont=dict(color=MUTED, size=12),
        title_font=dict(size=13, color=INK), automargin=True, zeroline=False,
    )
    return fig


# ---------------------------------------------------------------- tương thích phiên bản Streamlit
def _ver() -> tuple[int, int]:
    try:
        a, b = st.__version__.split(".")[:2]
        return int(a), int(b)
    except Exception:
        return (1, 0)


def _stretch() -> dict:
    # Từ ~1.50 `use_container_width` bị thay bằng width="stretch"
    return {"width": "stretch"} if _ver() >= (1, 50) else {"use_container_width": True}


PLOT_CFG = {"displaylogo": False, "displayModeBar": "hover",
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


def show(fig, key=None):
    st.plotly_chart(fig, key=key, config=PLOT_CFG, **_stretch())


def table(df, key=None, **kw):
    st.dataframe(df, hide_index=True, **_stretch(), **kw)
