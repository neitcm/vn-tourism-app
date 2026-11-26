"""ui.py - giao diện chung: CSS, màu house style, hàm định dạng, style Plotly."""
from __future__ import annotations

import html
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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

/* plotly modebar & external scrollbars */
.js-plotly-plot .plotly .modebar {{
  top: 4px !important;
  right: 6px !important;
  opacity: 1 !important;
  visibility: visible !important;
  background: rgba(255,255,255,0.92) !important;
  border: 1px solid {SAND_DARK} !important;
  border-radius: 10px !important;
  padding: 2px 4px !important;
  box-shadow: 0 2px 8px rgba(43,43,35,0.08) !important;
}}
.js-plotly-plot .plotly .modebar-group {{
  display: inline-flex !important;
  align-items: center !important;
  gap: 2px !important;
  background: transparent !important;
  padding: 0 !important;
}}
.js-plotly-plot .plotly .modebar-btn {{
  width: 26px !important;
  height: 26px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 6px !important;
  padding: 3px !important;
}}
.js-plotly-plot .plotly .modebar-btn:hover {{
  background: {SAND_DARK} !important;
}}
.js-plotly-plot .plotly .modebar-btn svg {{
  width: 16px !important;
  height: 16px !important;
}}
.vt-chart-shell {{
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
}}
.vt-chart-row {{
  display: flex;
  flex-direction: row;
  align-items: stretch;
  width: 100%;
}}
.vt-chart-main {{
  flex: 1 1 auto;
  min-width: 0;
}}
.vt-vscroll {{
  display: none;
  flex-direction: column;
  align-items: center;
  width: 18px;
  margin-left: 6px;
  padding: 2px 0;
  user-select: none;
}}
.vt-hscroll {{
  display: none;
  flex-direction: row;
  align-items: center;
  height: 18px;
  margin-top: 4px;
  margin-right: 24px;
  padding: 0 2px;
  user-select: none;
}}
.vt-arrow {{
  background: transparent;
  border: none;
  color: {MUTED};
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 3px;
  border-radius: 4px;
  flex: 0 0 auto;
}}
.vt-arrow:hover {{
  background: {SAND_DARK};
  color: {INK};
}}
.vt-htrack {{
  position: relative;
  flex: 1 1 auto;
  height: 8px;
  background: #E8E5DC;
  border-radius: 999px;
  margin: 0 4px;
  cursor: pointer;
}}
.vt-hthumb {{
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 30%;
  background: #5E718A;
  border-radius: 999px;
  cursor: grab;
}}
.vt-hthumb:active {{ cursor: grabbing; background: #47586E; }}
.vt-vtrack {{
  position: relative;
  flex: 1 1 auto;
  width: 8px;
  background: #E8E5DC;
  border-radius: 999px;
  margin: 4px 0;
  cursor: pointer;
}}
.vt-vthumb {{
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  height: 30%;
  background: #5E718A;
  border-radius: 999px;
  cursor: grab;
}}
.vt-vthumb:active {{ cursor: grabbing; background: #47586E; }}
</style>
"""

WAVE = ("<svg viewBox='0 0 1440 80' preserveAspectRatio='none'><path fill='%s' d='M0,40 C240,90 480,0 720,30 "
        "C960,60 1200,90 1440,40 L1440,80 L0,80 Z'/></svg>" % SAND)


_ENHANCE_HTML = """
<script>
(function() {
  const doc = window.parent.document;
  const win = window.parent;

  const RESET_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>';

  const TOOLTIPS = {
    zoomIn: "Phóng to",
    zoomOut: "Thu nhỏ",
    pan: "Di chuyển biểu đồ",
    boxZoom: "Khoanh vùng phóng to",
    reset: "Khôi phục ban đầu",
    autoscale: "Xem toàn bộ biểu đồ",
    download: "Lưu ảnh biểu đồ"
  };

  function classifyBtn(btn) {
    const attr = btn.getAttribute("data-attr") || "";
    const val = btn.getAttribute("data-val") || "";
    const title = btn.getAttribute("data-title") || "";
    if (attr === "zoom" && val === "in") return "zoomIn";
    if (attr === "zoom" && val === "out") return "zoomOut";
    if (attr === "geo" && val === "zoomin") return "zoomIn";
    if (attr === "geo" && val === "zoomout") return "zoomOut";
    if (attr === "dragmode" && val === "zoom") return "boxZoom";
    if (attr === "dragmode" && val === "pan") return "pan";
    if ((attr === "zoom" && val === "reset") || (attr === "geo" && val === "reset")) return "reset";
    if (attr === "zoom" && val === "auto") return "autoscale";
    if ((!attr && !val && /png|image|download/i.test(title)) || attr === "toImage") return "download";
    return null;
  }

  function styleModebar(gd) {
    const mb = gd.querySelector(".modebar");
    if (!mb) return;
    const data = gd._fullData || gd.data || [];
    const isTreemap = data.some(t => t.type === "treemap");
    const isGeo = data.some(t => t.type === "scattergeo");
    const order = isTreemap
      ? ["download"]
      : (isGeo
          ? ["zoomIn", "zoomOut", "pan", "reset", "download"]
          : ["zoomIn", "zoomOut", "pan", "reset", "autoscale", "download"]);

    const btns = Array.from(mb.querySelectorAll("a.modebar-btn"));
    const byKey = {};
    btns.forEach(b => {
      const k = classifyBtn(b);
      if (k && !byKey[k]) byKey[k] = b;
    });

    let grp = mb.querySelector(".modebar-group.vt-ordered");
    if (!grp) {
      mb.innerHTML = "";
      grp = doc.createElement("div");
      grp.className = "modebar-group vt-ordered";
      mb.appendChild(grp);
    } else {
      grp.innerHTML = "";
    }

    order.forEach(k => {
      const b = byKey[k];
      if (!b) return;
      if (TOOLTIPS[k]) {
        b.setAttribute("data-title", TOOLTIPS[k]);
        b.setAttribute("aria-label", TOOLTIPS[k]);
      }
      if (k === "reset") {
        b.innerHTML = RESET_SVG;
      }
      grp.appendChild(b);
    });
  }

  function toNum(ax, v) {
    if (v === undefined || v === null) return NaN;
    if (ax && ax.type === "date") {
      const t = new Date(v).getTime();
      return isNaN(t) ? Number(v) : t;
    }
    return Number(v);
  }

  function fromNum(ax, n) {
    if (ax && ax.type === "date") {
      const d = new Date(n);
      const pad = x => String(x).padStart(2, "0");
      return d.getUTCFullYear() + "-" + pad(d.getUTCMonth() + 1) + "-" + pad(d.getUTCDate()) + " " +
             pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes()) + ":" + pad(d.getUTCSeconds());
    }
    return n;
  }

  function attachScrollbars(gd) {
    const data = gd._fullData || gd.data || [];
    const isTreemap = data.some(t => t.type === "treemap");
    const isGeo = data.some(t => t.type === "scattergeo");
    if (isTreemap || isGeo) return;
    const fl = gd._fullLayout;
    if (!fl || !fl.xaxis || !fl.yaxis) return;

    const host = gd.closest('[data-testid="stPlotlyChart"]') || gd.parentElement;
    if (!host) return;

    if (!host.dataset.vtScrollInit) {
      host.dataset.vtScrollInit = "1";
      const shell = doc.createElement("div");
      shell.className = "vt-chart-shell";
      const row = doc.createElement("div");
      row.className = "vt-chart-row";
      const main = doc.createElement("div");
      main.className = "vt-chart-main";

      while (host.firstChild) main.appendChild(host.firstChild);

      const vBar = doc.createElement("div");
      vBar.className = "vt-vscroll";
      vBar.innerHTML = '<button type="button" class="vt-arrow vt-up" title="Cuộn lên">▲</button><div class="vt-vtrack"><div class="vt-vthumb"></div></div><button type="button" class="vt-arrow vt-down" title="Cuộn xuống">▼</button>';

      const hBar = doc.createElement("div");
      hBar.className = "vt-hscroll";
      hBar.innerHTML = '<button type="button" class="vt-arrow vt-left" title="Cuộn sang trái">◀</button><div class="vt-htrack"><div class="vt-hthumb"></div></div><button type="button" class="vt-arrow vt-right" title="Cuộn sang phải">▶</button>';

      row.appendChild(main);
      row.appendChild(vBar);
      shell.appendChild(row);
      shell.appendChild(hBar);
      host.appendChild(shell);
      host._vtBars = { hBar, vBar };
    }

    const bars = host._vtBars;
    if (!bars) return;
    const { hBar, vBar } = bars;

    function captureFull() {
      const xa = gd._fullLayout && gd._fullLayout.xaxis;
      const ya = gd._fullLayout && gd._fullLayout.yaxis;
      if (!xa || !ya || !xa.range || !ya.range) return;
      const x0 = toNum(xa, xa.range[0]), x1 = toNum(xa, xa.range[1]);
      const y0 = toNum(ya, ya.range[0]), y1 = toNum(ya, ya.range[1]);
      if (!gd.__vtFull || gd.__vtFull.len !== data.length) {
        gd.__vtFull = {
          len: data.length,
          xMin: Math.min(x0, x1), xMax: Math.max(x0, x1),
          yMin: Math.min(y0, y1), yMax: Math.max(y0, y1),
          yRev: y0 > y1
        };
      } else {
        gd.__vtFull.xMin = Math.min(gd.__vtFull.xMin, x0, x1);
        gd.__vtFull.xMax = Math.max(gd.__vtFull.xMax, x0, x1);
        gd.__vtFull.yMin = Math.min(gd.__vtFull.yMin, y0, y1);
        gd.__vtFull.yMax = Math.max(gd.__vtFull.yMax, y0, y1);
      }
    }

    function sync() {
      const xa = gd._fullLayout && gd._fullLayout.xaxis;
      const ya = gd._fullLayout && gd._fullLayout.yaxis;
      if (!xa || !ya || !xa.range || !ya.range || !gd.__vtFull) return;
      const f = gd.__vtFull;

      const cx0 = toNum(xa, xa.range[0]), cx1 = toNum(xa, xa.range[1]);
      const curMinX = Math.min(cx0, cx1), curMaxX = Math.max(cx0, cx1);
      const curSpanX = curMaxX - curMinX, fullSpanX = f.xMax - f.xMin;

      if (fullSpanX > 0 && curSpanX > 0 && curSpanX < fullSpanX * 0.992) {
        hBar.style.display = "flex";
        const ratio = Math.max(0.08, Math.min(1, curSpanX / fullSpanX));
        const denom = fullSpanX - curSpanX;
        const pos = denom > 0 ? Math.max(0, Math.min(1, (curMinX - f.xMin) / denom)) : 0;
        const thumb = hBar.querySelector(".vt-hthumb");
        thumb.style.width = (ratio * 100) + "%";
        thumb.style.left = (pos * (1 - ratio) * 100) + "%";
      } else {
        hBar.style.display = "none";
      }

      const cy0 = toNum(ya, ya.range[0]), cy1 = toNum(ya, ya.range[1]);
      const curMinY = Math.min(cy0, cy1), curMaxY = Math.max(cy0, cy1);
      const curSpanY = curMaxY - curMinY, fullSpanY = f.yMax - f.yMin;

      if (fullSpanY > 0 && curSpanY > 0 && curSpanY < fullSpanY * 0.992) {
        vBar.style.display = "flex";
        const ratio = Math.max(0.08, Math.min(1, curSpanY / fullSpanY));
        const denom = fullSpanY - curSpanY;
        const pos = denom > 0
          ? (f.yRev
              ? Math.max(0, Math.min(1, (curMinY - f.yMin) / denom))
              : Math.max(0, Math.min(1, (f.yMax - curMaxY) / denom)))
          : 0;
        const thumb = vBar.querySelector(".vt-vthumb");
        thumb.style.height = (ratio * 100) + "%";
        thumb.style.top = (pos * (1 - ratio) * 100) + "%";
      } else {
        vBar.style.display = "none";
      }
    }

    function applyX(newMin) {
      const xa = gd._fullLayout.xaxis, f = gd.__vtFull;
      const cx0 = toNum(xa, xa.range[0]), cx1 = toNum(xa, xa.range[1]);
      const span = Math.abs(cx1 - cx0);
      const clamped = Math.max(f.xMin, Math.min(f.xMax - span, newMin));
      const r = cx0 <= cx1 ? [fromNum(xa, clamped), fromNum(xa, clamped + span)] : [fromNum(xa, clamped + span), fromNum(xa, clamped)];
      win.Plotly.relayout(gd, { "xaxis.range": r, "xaxis.autorange": false });
    }

    function applyY(topPosFrac) {
      const ya = gd._fullLayout.yaxis, f = gd.__vtFull;
      const cy0 = toNum(ya, ya.range[0]), cy1 = toNum(ya, ya.range[1]);
      const span = Math.abs(cy1 - cy0);
      const frac = Math.max(0, Math.min(1, topPosFrac));
      const denom = Math.max(0, (f.yMax - f.yMin) - span);
      let minVal, maxVal;
      if (f.yRev) {
        minVal = f.yMin + frac * denom;
        maxVal = minVal + span;
        win.Plotly.relayout(gd, { "yaxis.range": [fromNum(ya, maxVal), fromNum(ya, minVal)], "yaxis.autorange": false });
      } else {
        maxVal = f.yMax - frac * denom;
        minVal = maxVal - span;
        win.Plotly.relayout(gd, { "yaxis.range": [fromNum(ya, minVal), fromNum(ya, maxVal)], "yaxis.autorange": false });
      }
    }

    if (!gd.dataset.vtEventsBound) {
      gd.dataset.vtEventsBound = "1";
      captureFull();
      sync();

      gd.on("plotly_relayout", () => { styleModebar(gd); sync(); });
      gd.on("plotly_afterplot", () => { styleModebar(gd); captureFull(); sync(); });

      const hTrack = hBar.querySelector(".vt-htrack"), hThumb = hBar.querySelector(".vt-hthumb");
      const vTrack = vBar.querySelector(".vt-vtrack"), vThumb = vBar.querySelector(".vt-vthumb");

      hBar.querySelector(".vt-left").onclick = () => {
        const xa = gd._fullLayout.xaxis, c0 = toNum(xa, xa.range[0]), c1 = toNum(xa, xa.range[1]);
        applyX(Math.min(c0, c1) - Math.abs(c1 - c0) * 0.2);
      };
      hBar.querySelector(".vt-right").onclick = () => {
        const xa = gd._fullLayout.xaxis, c0 = toNum(xa, xa.range[0]), c1 = toNum(xa, xa.range[1]);
        applyX(Math.min(c0, c1) + Math.abs(c1 - c0) * 0.2);
      };
      vBar.querySelector(".vt-up").onclick = () => {
        const ya = gd._fullLayout.yaxis, f = gd.__vtFull;
        const c0 = toNum(ya, ya.range[0]), c1 = toNum(ya, ya.range[1]);
        const span = Math.abs(c1 - c0), denom = Math.max(1e-9, (f.yMax - f.yMin) - span);
        const curFrac = f.yRev ? (Math.min(c0, c1) - f.yMin) / denom : (f.yMax - Math.max(c0, c1)) / denom;
        applyY(curFrac - 0.2);
      };
      vBar.querySelector(".vt-down").onclick = () => {
        const ya = gd._fullLayout.yaxis, f = gd.__vtFull;
        const c0 = toNum(ya, ya.range[0]), c1 = toNum(ya, ya.range[1]);
        const span = Math.abs(c1 - c0), denom = Math.max(1e-9, (f.yMax - f.yMin) - span);
        const curFrac = f.yRev ? (Math.min(c0, c1) - f.yMin) / denom : (f.yMax - Math.max(c0, c1)) / denom;
        applyY(curFrac + 0.2);
      };

      hThumb.onpointerdown = (e) => {
        e.preventDefault(); e.stopPropagation();
        const startX = e.clientX, startLeft = hThumb.offsetLeft;
        const maxLeft = Math.max(1, hTrack.clientWidth - hThumb.offsetWidth);
        const move = (ev) => {
          const frac = Math.max(0, Math.min(1, (startLeft + ev.clientX - startX) / maxLeft));
          const f = gd.__vtFull, xa = gd._fullLayout.xaxis;
          const span = Math.abs(toNum(xa, xa.range[1]) - toNum(xa, xa.range[0]));
          applyX(f.xMin + frac * Math.max(0, (f.xMax - f.xMin) - span));
        };
        const up = () => { doc.removeEventListener("pointermove", move); doc.removeEventListener("pointerup", up); };
        doc.addEventListener("pointermove", move); doc.addEventListener("pointerup", up);
      };

      vThumb.onpointerdown = (e) => {
        e.preventDefault(); e.stopPropagation();
        const startY = e.clientY, startTop = vThumb.offsetTop;
        const maxTop = Math.max(1, vTrack.clientHeight - vThumb.offsetHeight);
        const move = (ev) => {
          const frac = Math.max(0, Math.min(1, (startTop + ev.clientY - startY) / maxTop));
          applyY(frac);
        };
        const up = () => { doc.removeEventListener("pointermove", move); doc.removeEventListener("pointerup", up); };
        doc.addEventListener("pointermove", move); doc.addEventListener("pointerup", up);
      };
    } else {
      sync();
    }
  }

  function scanCharts() {
    if (!win.Plotly) return;
    doc.querySelectorAll(".js-plotly-plot").forEach(gd => {
      styleModebar(gd);
      attachScrollbars(gd);
    });
  }

  win.__vtScanCharts = scanCharts;
  if (!win.__vtObserverInstalled) {
    win.__vtObserverInstalled = true;
    const obs = new MutationObserver(() => {
      clearTimeout(win.__vtTimer);
      win.__vtTimer = setTimeout(scanCharts, 80);
    });
    obs.observe(doc.body, { childList: true, subtree: true });
  }
  setTimeout(scanCharts, 100);
  setTimeout(scanCharts, 450);
})();
</script>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
    components.html(_ENHANCE_HTML, height=0, width=0)


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


PLOT_CFG = {
    "displaylogo": False,
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "hoverClosestCartesian", "hoverCompareCartesian", "toggleSpikelines"],
    "modeBarButtonsToAdd": ["zoomIn2d", "zoomOut2d", "pan2d", "autoScale2d", "resetScale2d"],
}


def show(fig, key=None):
    st.plotly_chart(fig, key=key, config=PLOT_CFG, **_stretch())


def table(df, key=None, **kw):
    st.dataframe(df, hide_index=True, **_stretch(), **kw)
