"""
app.py - "Coming Back": Khách quốc tế trở lại Việt Nam (P07)
M9 (Interaction & Story) + M10 (Evaluate & Improve) - phụ trách: Cẩm Tiên
Chạy:  streamlit run app.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data_layer as dl
import house_style as hs
import m10
import pages_m7_m8 as m78
import ui
from ui import INK, MUTED, GRID, P

st.set_page_config(page_title="Coming Back · Du lịch Việt Nam", page_icon="🏝️", layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

PLOTLY_MARKER = {"o": "circle", "s": "square", "^": "triangle-up", "D": "diamond", "v": "triangle-down", "P": "cross"}
DIV_SCALE = [[i / (len(hs.DIV_COLORS) - 1), c] for i, c in enumerate(hs.DIV_COLORS)]
CLUSTER_NAME = {1: "Thị trường xa - Mùa vụ rõ hơn", 2: "Thị trường gần - Mùa vụ nhẹ hơn"}
CLUSTER_ACTION = {1: "Kiểm tra đường bay và thời gian đặt tour.", 2: "Thử gói ngắn ngày ở các tháng còn công suất."}


# ============================================================ dữ liệu (cache)
@st.cache_data(show_spinner="Đang nạp dữ liệu…")
def get_data():
    m = dl.load_master()
    feats, excl = dl.build_features(m)
    seg, prof, evr, sil = dl.segment_markets(feats)
    return dict(
        master=m, weather=dl.load_weather(), trends=dl.load_trends(), corr=dl.load_correlations(), yoy=dl.load_yoy(),
        feats=feats, excluded=excl, seg=seg, prof=prof, evr=evr, sil=sil, season=dl.seasonal_index(m),
        colors=ui.market_colors(sorted(m["market"].unique())),
    )


def page_header(icon, title, text):
    st.markdown(f"<h2 style='margin:.2rem 0 .1rem;font-weight:800'>{icon} {title}</h2>"
                f"<p style='color:{MUTED};margin:0 0 .8rem;font-size:1rem'>{text}</p>", unsafe_allow_html=True)


def add_gap_band(fig, start="2020-04-01", end="2021-12-31", text="Nguồn không có số liệu theo thị trường"):
    mid = (pd.Timestamp(start) + (pd.Timestamp(end) - pd.Timestamp(start)) / 2).strftime("%Y-%m-%d")
    fig.add_shape(type="rect", xref="x", yref="paper", x0=start, x1=end, y0=0, y1=1,
                  fillcolor=GRID, opacity=0.55, line_width=0, layer="below")
    fig.add_annotation(x=mid, y=0.98, yref="paper", text=text, showarrow=False, font=dict(size=11, color=MUTED))


# ============================================================ TRANG 1 · CÂU CHUYỆN
def page_story(D):
    m, colors = D["master"], D["colors"]
    end = dl.latest_date(m)
    tot, ytd, snap = dl.comparable_total(m, end), dl.ytd_compare(m), dl.market_snapshot(m)
    has_base = snap.dropna(subset=["recovery_index"]).copy()
    has_base["gap"] = has_base["arrivals"] - has_base["baseline_2019"]
    above, below = has_base[has_base["status"] == "Vượt 2019"], has_base[has_base["status"] == "Chưa phục hồi"]
    worst = below.sort_values("gap").head(2)
    best = has_base.sort_values("gap", ascending=False).head(3)

    ui.hero(
        "Khách quốc tế đã trở lại Việt Nam — nhưng không phải ai cũng trở lại như nhau",
        f"Theo dõi {m['market'].nunique()} thị trường nguồn từ 2019 đến {ui.mlabel(end)}: ai đã vượt mức trước đại dịch, "
        "ai còn chậm chân, và Ban Du lịch nên làm gì tiếp theo.",
        ["Du lịch quốc tế", f"Dữ liệu đến {ui.mlabel(end)}", "So với 2019 = 100"],
    )
    st.write("")
    c = st.columns(4)
    d_idx = tot["index"] - 100
    ui.kpi(c[0], f"{ui.mlabel(end)} so với cùng tháng 2019", ui.n1(tot["index"]),
           f"<span class='{'up' if d_idx >= 0 else 'down'}'>{ui.pct(d_idx)}</span> · {tot['n']} thị trường có mốc 2019")
    g_prev = 100 * (ytd["this"] / ytd["prev"] - 1)
    ui.kpi(c[1], f"Lũy kế T1–T{ytd['month']}/{ytd['year']}", ui.big(ytd["this"]),
           f"<span class='{'up' if g_prev >= 0 else 'down'}'>{ui.pct(g_prev)}</span> so với cùng kỳ {ytd['year'] - 1}")
    g_base = 100 * (ytd["this"] / ytd["base"] - 1)
    ui.kpi(c[2], "Lũy kế so với 2019", ui.pct(g_base), f"cùng {ytd['month']} tháng · {ytd['n']} thị trường đủ số liệu")
    ui.kpi(c[3], "Thị trường đã vượt 2019", f"{len(above)}/{len(has_base)}",
           f"{len(below)} thị trường còn dưới 2019 (chỉ số &lt; 95)")

    # ---- Big Idea v1
    st.write("")
    names_worst = " và ".join(worst["market"])
    names_best = ", ".join(best["market"])
    idx_w = ", ".join(f"{r.market} {ui.n0(r.recovery_index)}" for r in worst.itertuples())
    ui.card(
        f"<h4>💡 Big Idea v1 <span class='tag pill-warn'> Draft </span></h4>"
        f"<p style='font-size:1.05rem'><b>Việt Nam đã vượt mốc 2019 (chỉ số {ui.n0(tot['index'])}), nhưng đà tăng đến từ nhiều thị trường "
        f"mới nổi, còn hai thị trường đang thiếu khách nhiều nhất ({names_worst}) vẫn dưới 2019</b> ({idx_w}) — "
        f"nên bước tiếp theo là kéo họ trở lại và giữ đà ở {names_best}.</p>"
        f"<p style='color:{MUTED};font-size:.86rem;margin:0'>Mọi con số tính từ master table M2; so sánh cùng tập thị trường có mốc 2019.</p>",
        "sun")

    # ---- Chương 1: điểm xuất phát
    ui.chapter(1, "Điểm xuất phát: năm 2019", "Top thị trường theo tổng lượt khách 2019 — mốc mà mọi chỉ số 'phục hồi' so sánh với.")
    y19 = m.loc[(m["year"] == 2019) & m["arrivals"].notna()].groupby("market")["arrivals"].agg(["sum", "count"])
    y19 = y19[y19["count"] == 12].sort_values("sum", ascending=False).head(10).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=y19["sum"], y=[dl.label(k) for k in y19.index], orientation="h",
        marker_color=[colors[k] for k in y19.index], text=[ui.big(v) for v in y19["sum"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} lượt<extra></extra>", cliponaxis=False))
    ui.style_fig(fig, 380, legend=False, margin=dict(l=10, r=70, t=10, b=10))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(showgrid=False)
    full19 = m.loc[(m["year"] == 2019) & m["arrivals"].notna()].groupby("market")["arrivals"].agg(["sum", "count"])
    full19 = full19[full19["count"] == 12]["sum"].sort_values(ascending=False)
    share2 = 100 * full19.head(2).sum() / full19.sum()
    ui.chart_title(f"{full19.index[0]} và {full19.index[1]} chiếm {ui.n0(share2)}% lượt khách năm 2019",
                   f"Tổng lượt khách 2019, 10 thị trường lớn nhất · phần trăm tính trên {len(full19)} thị trường đủ 12 tháng")
    ui.show(fig, key="s1")
    ui.source("VNAT/NSO qua master table M2.")

    # ---- Chương 2: gián đoạn
    ui.chapter(2, "Gián đoạn 2020–2021", "Chỉ số gộp rơi gần như về đáy ngay quý I/2020; sau đó nguồn không có số liệu theo thị trường.")
    ts = dl.total_index_series(m).set_index("date")["index"]
    rng = pd.date_range("2019-10-01", "2022-06-01", freq="MS")
    s2 = ts.reindex(rng)
    fig = go.Figure(go.Scatter(x=s2.index, y=s2.values, mode="lines+markers", connectgaps=False,
                               line=dict(color=P["Poppy"], width=3), marker=dict(size=7),
                               hovertemplate="%{x|%m/%Y}: <b>%{y:.0f}</b><extra></extra>"))
    add_gap_band(fig)
    fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019 = 100", annotation_position="top left")
    ui.style_fig(fig, 340, legend=False)
    fig.update_yaxes(title="Chỉ số gộp (2019 = 100)")
    ui.chart_title("Quý I/2020: chỉ số gộp rơi mạnh, rồi khoảng trống dữ liệu kéo dài đến 2022",
                   "Σ lượt khách ÷ Σ cùng tháng 2019, các thị trường có mốc so sánh")
    ui.show(fig, key="s2")
    ui.source("Master table M2. Khoảng xám = tháng không có số liệu theo thị trường (không phải số 0).")

    # ---- Chương 3: mở cửa lại
    ui.chapter(3, "Mở cửa lại và tăng tốc", "Từ 2022 số liệu quay lại; chỉ số gộp bao giờ chạm mốc 2019?")
    s3 = ts.loc["2022-01-01":]
    cross = s3[s3 >= 100]
    fig = go.Figure(go.Scatter(x=s3.index, y=s3.values, mode="lines+markers", line=dict(color=P["Pea Flower"], width=3),
                               marker=dict(size=6), hovertemplate="%{x|%m/%Y}: <b>%{y:.0f}</b><extra></extra>"))
    fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019 = 100", annotation_position="bottom right")
    if len(cross):
        fig.add_annotation(x=cross.index[0], y=cross.iloc[0], text=f"Lần đầu ≥ 100: {ui.mlabel(cross.index[0])}",
                           ax=-60, ay=-55, showarrow=True, arrowhead=2, arrowcolor=INK, font=dict(size=12))
    ui.style_fig(fig, 360, legend=False)
    fig.update_yaxes(title="Chỉ số gộp (2019 = 100)")
    title3 = (f"Chỉ số gộp lần đầu chạm 2019 vào {ui.mlabel(cross.index[0])} và hiện ở {ui.n0(s3.iloc[-1])}"
              if len(cross) else "Chỉ số gộp vẫn chưa chạm mốc 2019")
    ui.chart_title(title3, "Σ lượt khách ÷ Σ cùng tháng 2019 — biến động theo mùa vụ nên đường có răng cưa")
    ui.show(fig, key="s3")
    ui.source("Master table M2.")

    # ---- Chương 4: không đồng đều
    ui.chapter(4, "Không đồng đều: ai kéo, ai chững", f"Chênh lệch lượt khách {ui.mlabel(end)} so với cùng tháng 2019, tính theo số khách thật.")
    g = has_base.reindex(has_base["gap"].abs().sort_values(ascending=False).index).head(16).sort_values("gap")
    fig = go.Figure(go.Bar(
        x=g["gap"], y=[dl.label(k) for k in g["market"]], orientation="h",
        marker_color=[ui.STATUS_COLOR[s] for s in g["status"]],
        text=[f"{'+' if v > 0 else ''}{ui.big(v)}" for v in g["gap"]], textposition="outside", cliponaxis=False,
        customdata=np.stack([g["arrivals"], g["baseline_2019"], g["recovery_index"]], 1),
        hovertemplate="<b>%{y}</b><br>Tháng này: %{customdata[0]:,.0f}<br>Cùng tháng 2019: %{customdata[1]:,.0f}"
                      "<br>Chỉ số: %{customdata[2]:.0f}<extra></extra>"))
    ui.style_fig(fig, 520, legend=False, margin=dict(l=10, r=80, t=10, b=10))
    fig.add_vline(x=0, line_color=INK, line_width=1)
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, title="Lượt khách chênh so với cùng tháng 2019")
    top_pos = g.sort_values("gap", ascending=False).iloc[0]
    top_neg = g.sort_values("gap").iloc[0]
    ui.chart_title(f"{top_pos['market']} tăng thêm nhiều nhất, trong khi {top_neg['market']} đang thiếu hụt lớn nhất",
                   f"16 thị trường chênh lệch lớn nhất, {ui.mlabel(end)} so với {ui.mlabel(end).replace(str(end.year), '2019')}. "
                   "Cam = chưa phục hồi · Xanh = vượt 2019")
    ui.show(fig, key="s4")
    ui.source("Master table M2. Chỉ gồm thị trường có mốc 2019.")

    # ---- Chương 5: hành động
    ui.chapter(5, "Việc cần làm cho Ban Du lịch", "Ba hướng hành động gợi ý để kiểm chứng — không phải kết luận nhân quả.")
    a, b, c3 = st.columns(3)
    with a:
        ui.card(f"<h4>🛟 Giữ đà tăng</h4><p>Nhóm tăng thêm nhiều nhất: <b>{names_best}</b>.</p>"
                "<p>Kiểm tra sức chứa địa phương và đường bay ở mùa cao điểm trước khi tăng ngân sách.</p>", "sea")
    with b:
        ui.card(f"<h4>🎯 Kéo thị trường lớn trở lại</h4><p><b>{names_worst}</b> còn dưới mốc 2019.</p>"
                f"<p>Hai thị trường này đang thiếu tổng cộng <b>{ui.big(worst['gap'].abs().sum())}</b> lượt trong {ui.mlabel(end)} so với cùng tháng 2019 — xem mục <i>Hỏi nhanh</i>.</p>", "sun")
    with c3:
        ui.card("<h4>📅 Chọn tháng thử nghiệm</h4><p>Thị trường gần có mùa vụ nhẹ hơn; thị trường xa có mùa vụ rõ hơn.</p>"
                "<p>Xem trang <i>Phân khúc</i> và <i>Mùa vụ</i> để chọn khung tháng cho chiến dịch nhỏ trước khi mở rộng.</p>")

    with st.expander("ℹ️ Nguồn dữ liệu & giới hạn cần biết"):
        st.markdown(
            "- **Nguồn:** VNAT/NSO (lượt khách theo thị trường), Google Trends (3 thị trường), Open-Meteo (Đà Nẵng, Nha Trang), "
            "gộp bằng key `market` + `date` trong M2.\n"
            "- **2021:** nguồn không có số liệu theo thị trường → hiển thị là *khoảng trống*, không phải 0.\n"
            f"- **Chỉ số phục hồi** = lượt khách tháng ÷ cùng tháng 2019 × 100. Chỉ tính khi có cả hai vế. "
            f"{len(D['excluded'])} thị trường không vào phần Phân khúc vì thiếu dữ liệu.\n"
            "- **Thị trường nhỏ** có chỉ số rất dao động (vài trăm lượt/tháng) — đọc cùng số khách thật.\n"
            "- Google Trends chỉ có cho Nhật Bản, Hàn Quốc, Đài Loan và là chỉ số *tương đối* 0–100.")


# ============================================================ TRANG 2 · EXPLORER + HỎI NHANH
def _presets(D):
    m, f = D["master"], D["feats"]
    end = dl.latest_date(m)
    last12 = m.loc[m["date"] > end - pd.DateOffset(months=12)].groupby("market")["arrivals"].sum().sort_values(ascending=False)
    return {
        "Top 6 theo lượt khách": last12.index[:6].tolist(),
        "Đông Bắc Á": ["Hàn Quốc", "Trung Quốc", "Nhật Bản", "Đài Loan"],
        "Đông Nam Á": ["Thái Lan", "Malaysia", "Singapore", "Indonesia", "Philippines", "Campuchia"],
        "Phương Tây & Úc": ["Nga", "Hoa Kỳ", "Pháp", "Đức", "Vương quốc Anh", "Úc"],
        "Tăng nhanh nhất": f.sort_values("growth_pct", ascending=False).index[:6].tolist(),
        "Tự chọn": ["Hàn Quốc", "Trung Quốc", "Nhật Bản"],
    }


def page_explorer(D):
    page_header("🔎", "Explorer", "Tự tay lọc, so sánh và đọc câu trả lời cho các câu hỏi thực tế của Ban Du lịch.")
    t1, t2 = st.tabs(["📈 Khám phá tự do", "🎯 Hỏi nhanh cho Ban Du lịch"])
    with t1:
        _explorer_free(D)
    with t2:
        _explorer_qa(D)


def _explorer_free(D):
    m, colors = D["master"], D["colors"]
    end = dl.latest_date(m)
    presets = _presets(D)
    all_dates = [pd.Timestamp(x) for x in sorted(m["date"].unique())]

    with st.container(border=True):
        c1, c2 = st.columns([1.1, 1.5])
        preset = c1.radio("① Nhóm thị trường", list(presets), horizontal=False, key="ex_preset")
        default = [x for x in presets[preset] if x in D["colors"]]
        sel = c2.multiselect("② Thị trường (thêm/bớt tuỳ ý)", sorted(m["market"].unique()), default=default,
                             key=f"ex_mk_{preset}", help="Mỗi thị trường luôn đúng một màu trong mọi biểu đồ.")
        c3, c4 = st.columns([1.1, 1.5])
        metric = c3.radio("③ Chỉ số hiển thị", ["Chỉ số phục hồi (2019 = 100)", "Lượt khách mỗi tháng", "Tỷ trọng trong tổng"],
                          key="ex_metric")
        d0 = pd.Timestamp("2022-01-01")
        start_default = d0 if d0 in all_dates else all_dates[0]
        rng = c4.select_slider("④ Khoảng thời gian", options=all_dates, value=(start_default, all_dates[-1]),
                               format_func=ui.mlabel, key="ex_range")
        c5, c6, _ = st.columns([1.1, 1.1, 1.4])
        smooth = c5.toggle("⑤ Làm mượt 3 tháng", value=False, help="Trung bình trượt 3 tháng để giảm răng cưa mùa vụ.")
        show_base = c6.toggle("⑥ Hiện mốc 2019 = 100", value=True)

    if not sel:
        st.info("Chọn ít nhất một thị trường để bắt đầu.")
        return
    d = m.loc[m["market"].isin(sel) & m["date"].between(*rng)].copy()
    if metric.startswith("Chỉ số"):
        d["y"], ytitle, fmt = d["recovery_index"], "Chỉ số phục hồi (2019 = 100)", ".0f"
    elif metric.startswith("Lượt"):
        d["y"], ytitle, fmt = d["arrivals"], "Lượt khách mỗi tháng", ",.0f"
    else:
        tot_m = m.groupby("date")["arrivals"].transform("sum")
        d = m.loc[m["market"].isin(sel) & m["date"].between(*rng)].copy()
        d["y"], ytitle, fmt = 100 * d["arrivals"] / tot_m.loc[d.index], "Tỷ trọng trong tổng (%)", ".1f"
    if smooth:
        d["y"] = d.sort_values("date").groupby("market")["y"].transform(lambda s: s.rolling(3, min_periods=2).mean())

    fig = go.Figure()
    for mk in sel:
        g = d.loc[d["market"] == mk].sort_values("date")
        g = g.set_index("date")["y"].reindex(pd.date_range(rng[0], rng[1], freq="MS"))
        fig.add_trace(go.Scatter(
            x=g.index, y=g.values, mode="lines+markers", name=dl.label(mk), connectgaps=False,
            line=dict(color=colors[mk], width=3), marker=dict(size=6, symbol=PLOTLY_MARKER.get(hs.MARKET_MARKERS.get(mk, "o"), "circle")),
            hovertemplate=f"<b>{mk}</b> %{{x|%m/%Y}}: %{{y:{fmt}}}<extra></extra>"))
        last = g.dropna()
        if len(last):
            fig.add_trace(go.Scatter(x=[last.index[-1]], y=[last.iloc[-1]], mode="text", text=[f"  {mk}"], textposition="middle right",
                                     textfont=dict(size=12, color=INK), showlegend=False, hoverinfo="skip"))
    if metric.startswith("Chỉ số") and show_base:
        fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019", annotation_position="top left")
    if pd.Timestamp(rng[0]) <= pd.Timestamp("2021-12-01") and pd.Timestamp(rng[1]) >= pd.Timestamp("2020-04-01"):
        add_gap_band(fig, start=str(max(pd.Timestamp(rng[0]), pd.Timestamp("2020-04-01")).date()),
                     end=str(min(pd.Timestamp(rng[1]), pd.Timestamp("2021-12-31")).date()))
    ui.style_fig(fig, 460, legend=False, margin=dict(l=10, r=90, t=10, b=10))
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(title=ytitle)
    fig.update_xaxes(range=[rng[0], pd.Timestamp(rng[1]) + pd.DateOffset(months=4)])
    ui.chart_title(f"{ytitle}: {', '.join(sel[:3])}{'…' if len(sel) > 3 else ''}", f"{ui.mlabel(rng[0])} – {ui.mlabel(rng[1])}"
                   + (" · làm mượt 3 tháng" if smooth else ""))
    ui.show(fig, key="ex_main")

    # thẻ số liệu tháng mới nhất
    cols = st.columns(min(len(sel), 6))
    for col, mk in zip(cols, sel[:6]):
        row = m.loc[(m["market"] == mk) & (m["date"] == end)]
        prev = m.loc[(m["market"] == mk) & (m["date"] == end - pd.DateOffset(years=1)), "arrivals"]
        a = row["arrivals"].iloc[0] if len(row) else np.nan
        ri = row["recovery_index"].iloc[0] if len(row) else np.nan
        yoy = 100 * (a / prev.iloc[0] - 1) if len(prev) and pd.notna(a) and prev.iloc[0] else np.nan
        ui.kpi(col, dl.label(mk), ui.n0(ri) if pd.notna(ri) else "–",
               f"{ui.mlabel(end)} · {ui.big(a)} lượt<br>YoY {ui.pct(yoy)}")

    # xếp hạng tháng
    st.write("")
    avail = [d_ for d_ in all_dates if m.loc[m["date"] == d_, "recovery_index"].notna().sum() >= 10]
    rk_date = st.select_slider("Xếp hạng theo tháng", options=avail, value=avail[-1], format_func=ui.mlabel, key="ex_rank")
    s = dl.market_snapshot(m, rk_date).dropna(subset=["recovery_index"]).sort_values("recovery_index", ascending=False).head(15).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=s["recovery_index"], y=[dl.label(k) for k in s["market"]], orientation="h",
        marker_color=[ui.STATUS_COLOR[x] for x in s["status"]], text=[ui.n0(v) for v in s["recovery_index"]], textposition="outside",
        cliponaxis=False, customdata=np.stack([s["arrivals"]], 1),
        hovertemplate="<b>%{y}</b><br>Chỉ số: %{x:.0f}<br>Lượt khách: %{customdata[0]:,.0f}<extra></extra>"))
    fig.add_vline(x=100, line_dash="dot", line_color=INK)
    ui.style_fig(fig, 440, legend=False, margin=dict(l=10, r=50, t=10, b=10))
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(showgrid=False, visible=False)
    ui.chart_title(f"15 thị trường có chỉ số phục hồi cao nhất, {ui.mlabel(rk_date)}",
                   "Cam = dưới 95 · Xám = quanh 100 · Xanh = trên 105. Thị trường nhỏ có thể cho chỉ số rất cao — xem lượt khách khi di chuột.")
    ui.show(fig, key="ex_rank_chart")

    with st.expander("📄 Xem & tải bảng dữ liệu đang lọc"):
        out = d[["market", "date", "arrivals", "baseline_2019", "recovery_index"]].sort_values(["market", "date"])
        ui.table(out)
        st.download_button("⬇️ Tải CSV", out.to_csv(index=False).encode("utf-8-sig"), "du_lieu_loc.csv", "text/csv")


def _explorer_qa(D):
    m, colors = D["master"], D["colors"]
    end = dl.latest_date(m)
    q = st.radio("Chọn câu hỏi", [
        "1️⃣ Nên ưu tiên kéo khách trở lại từ thị trường nào?",
        "2️⃣ Chạy chiến dịch vào tháng nào cho một thị trường?",
        "3️⃣ Tìm kiếm trực tuyến có báo trước lượt khách không?"], key="qa_q")
    if q.startswith("1"):
        snap = dl.market_snapshot(m, end).dropna(subset=["recovery_index"])
        snap["short"] = snap["baseline_2019"] - snap["arrivals"]
        short = snap.loc[snap["short"] > 0].sort_values("short", ascending=False).head(8).iloc[::-1]
        fig = go.Figure(go.Bar(
            x=short["short"], y=[dl.label(k) for k in short["market"]], orientation="h", marker_color=P["Poppy"],
            text=[ui.big(v) for v in short["short"]], textposition="outside", cliponaxis=False,
            customdata=np.stack([short["recovery_index"], short["arrivals"]], 1),
            hovertemplate="<b>%{y}</b><br>Còn thiếu: %{x:,.0f} lượt/tháng<br>Chỉ số: %{customdata[0]:.0f}<extra></extra>"))
        ui.style_fig(fig, 380, legend=False, margin=dict(l=10, r=70, t=10, b=10))
        fig.update_yaxes(showgrid=False)
        fig.update_xaxes(visible=False)
        top = short.iloc[-1]
        ui.chart_title(f"{top['market']} đang thiếu {ui.big(top['short'])} lượt mỗi tháng so với 2019 — lớn nhất trong các thị trường chưa phục hồi",
                       f"Số khách còn thiếu = cùng tháng 2019 − {ui.mlabel(end)}")
        ui.show(fig, key="qa1")
        recent = m.loc[(m["market"] == top["market"]) & (m["date"] > end - pd.DateOffset(months=6)), ["date", "recovery_index"]].dropna()
        trail = " → ".join(f"{ui.mlabel(r.date)}: {ui.n0(r.recovery_index)}" for r in recent.itertuples())
        ui.card(f"<h4>Đọc nhanh</h4><p>Chỉ số 6 tháng gần nhất của <b>{top['market']}</b>: {trail}.</p>"
                "<p>Nếu đường đang đi xuống, nên kiểm tra rào cản đi lại trước khi tăng ngân sách quảng bá. Đây là gợi ý để kiểm chứng, không phải kết luận nhân quả.</p>", "sun")
    elif q.startswith("2"):
        S = D["season"]
        mk = st.selectbox("Thị trường", S.index.tolist(), index=S.index.tolist().index("Nhật Bản") if "Nhật Bản" in S.index else 0)
        s = S.loc[mk]
        top3 = s.sort_values(ascending=False).head(3).index.tolist()
        low = s.idxmin()
        cols = [P["Pea Flower"] if k in top3 else ("#D9DCDD" if k != low else P["Poppy"]) for k in s.index]
        fig = go.Figure(go.Bar(x=s.index, y=s.values, marker_color=cols, text=[ui.n0(v) for v in s.values], textposition="outside",
                               hovertemplate="%{x}: <b>%{y:.0f}</b><extra></extra>"))
        fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Trung bình năm = 100", annotation_position="top left")
        ui.style_fig(fig, 380, legend=False)
        fig.update_yaxes(title="Chỉ số mùa vụ (T1–T11 trung bình = 100)")
        ui.chart_title(f"{mk}: đông nhất vào {', '.join(top3)}, thưa nhất vào {low}",
                       "Trung vị 2023–2025 của lượt khách mỗi tháng ÷ bình quân tháng 1–11 của chính năm đó")
        ui.show(fig, key="qa2")
        ui.source("Master table M2, cách tính như M6. Chỉ gồm thị trường đủ số liệu 2023–2025.")
        ui.card(f"<h4>Đọc nhanh</h4><p>Muốn <b>tăng khách</b> ở {mk}: thử chiến dịch ngay trước {top3[0]}. Muốn <b>lấp mùa thấp</b>: thử gói ưu đãi quanh {low}. "
                "Gợi ý để chạy thử nhỏ rồi đo phản hồi.</p>", "sea")
    else:
        T = D["trends"]
        c1, c2 = st.columns(2)
        mk = c1.selectbox("Thị trường", sorted(T["market"].unique()))
        lag = c2.slider("Tìm kiếm đi trước (tháng)", 0, 3, 2)
        g = dl.lagged_trends(T, mk, lag)
        pr, sr = dl.simple_corr(g["interest_lag"], g["arrivals"])
        coef = np.polyfit(g["interest_lag"], g["arrivals"], 1)
        xs = np.linspace(g["interest_lag"].min(), g["interest_lag"].max(), 20)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=g["interest_lag"], y=g["arrivals"], mode="markers", marker=dict(size=9, color=colors[mk], line=dict(color=INK, width=.6)),
                                 customdata=g["date"].dt.strftime("%m/%Y"), hovertemplate="Tháng %{customdata}<br>Quan tâm: %{x}<br>Lượt khách: %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=xs, y=np.polyval(coef, xs), mode="lines", line=dict(color=INK, dash="dash", width=1.5), hoverinfo="skip"))
        ui.style_fig(fig, 400, legend=False)
        fig.update_xaxes(title=f"Mức quan tâm tìm kiếm {lag} tháng trước (0–100, tương đối)", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(title="Lượt khách")
        ui.chart_title(f"{mk}: quan tâm tìm kiếm {lag} tháng trước đi cùng lượt khách (Pearson r = {hs._vn(f"{pr:.2f}")})",
                       f"Spearman ρ = {hs._vn(f'{sr:.2f}')} · n = {len(g)} tháng có đủ hai vế")
        ui.show(fig, key="qa3")
        yoy = D["yoy"]
        yrow = yoy.loc[(yoy["market"] == mk) & (yoy["trend_period"] == f"interest_lead_{lag}m_yoy" if lag else yoy["trend_period"] == "interest_yoy")]
        extra = f" Khi so cùng kỳ năm trước, Spearman ρ = {hs._vn(f"{yrow['spearman_r'].iloc[0]:.2f}")}." if len(yrow) else ""
        ui.card("<h4>⚠️ Đọc thận trọng</h4><p>Tương quan gộp chung giai đoạn sụp đổ rồi hồi phục nên bị kéo cao bởi xu hướng chung "
                f"của cả hai chuỗi.{extra} Đây là <b>dấu hiệu sớm</b> để theo dõi, không chứng minh tìm kiếm gây ra lượt khách.</p>")


# ============================================================ TRANG 3 · ĐUA PHỤC HỒI
def page_race(D):
    m = D["master"]
    page_header("🏁", "Cuộc đua phục hồi", "Mỗi thanh là chỉ số phục hồi của một thị trường (2019 = 100). Bấm ▶ và xem ai về đích trước.")
    c1, c2, c3 = st.columns(3)
    topn = c1.slider("Số thị trường (theo quy mô 2019)", 6, 20, 12)
    start = c2.selectbox("Bắt đầu từ", ["2022-01", "2023-01", "2024-01"], index=0)
    speed = c3.select_slider("Tốc độ", ["Chậm", "Vừa", "Nhanh"], value="Vừa")
    dur = {"Chậm": 900, "Vừa": 500, "Nhanh": 250}[speed]

    size = m.groupby("market")["baseline_2019"].mean().sort_values(ascending=False)
    mk = size.index[:topn].tolist()
    piv = m.loc[m["market"].isin(mk)].pivot(index="date", columns="market", values="recovery_index").loc[start:]
    piv = piv.loc[piv.notna().sum(axis=1) >= max(4, int(0.6 * topn))]
    if piv.empty:
        st.warning("Không đủ dữ liệu để dựng cuộc đua với lựa chọn này.")
        return
    xmax = float(np.ceil(piv.max().max() * 1.15 / 50) * 50)

    def bar(date):
        s = piv.loc[date].dropna().sort_values()
        return go.Bar(x=s.values, y=[dl.label(k) for k in s.index], orientation="h",
                      marker_color=[ui.STATUS_COLOR["Chưa phục hồi"] if v < 95 else (ui.STATUS_COLOR["Vượt 2019"] if v > 105 else ui.STATUS_COLOR["Quanh mốc 2019"]) for v in s.values],
                      text=[ui.n0(v) for v in s.values], textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{y}</b>: %{x:.0f}<extra></extra>")

    def date_note(date):
        return [dict(x=0.97, y=0.08, xref="paper", yref="paper", text=f"<b>{ui.mlabel(date)}</b>", showarrow=False,
                     font=dict(size=46, color="rgba(43,43,35,.18)"), xanchor="right")]

    dates = list(piv.index)
    frames = [go.Frame(data=[bar(d)], name=d.strftime("%Y-%m"), layout=dict(annotations=date_note(d))) for d in dates]
    fig = go.Figure(data=[bar(dates[0])], frames=frames)
    ui.style_fig(fig, 560, legend=False, margin=dict(l=10, r=40, t=10, b=90))
    fig.update_layout(
        annotations=date_note(dates[0]), yaxis=dict(categoryorder="total ascending", showgrid=False),
        xaxis=dict(range=[0, xmax], title="Chỉ số phục hồi (2019 = 100)", showgrid=True, gridcolor=GRID),
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.13, xanchor="left", yanchor="top", buttons=[
            dict(label="▶ Chạy", method="animate", args=[None, dict(frame=dict(duration=dur, redraw=True), transition=dict(duration=0),
                                                                    fromcurrent=True, mode="immediate")]),
            dict(label="⏸ Dừng", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])])],
        sliders=[dict(active=0, x=0.18, y=-0.1, len=0.8, currentvalue=dict(prefix="Tháng: ", font=dict(size=13)), pad=dict(t=0, b=10),
                      steps=[dict(label=ui.mlabel(d), method="animate", args=[[d.strftime("%Y-%m")], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))]) for d in dates])])
    fig.add_shape(type="line", x0=100, x1=100, y0=0, y1=1, yref="paper", line=dict(color=INK, dash="dot", width=1.5))
    ui.chart_title("Cuộc đua về mốc 2019: ai về đích trước, ai còn chạy phía sau",
                   "Cam = dưới 95 · Xám = quanh 100 · Xanh = trên 105. Đường chấm = mốc 2019.")
    ui.show(fig, key="race")
    ui.source("Master table M2. 2020–2021 không có số liệu theo thị trường nên cuộc đua bắt đầu từ 2022.")

    # Ai về đích trước
    first = {}
    for k in piv.columns:
        s = piv[k].dropna()
        hit = s[s >= 100]
        first[k] = hit.index[0] if len(hit) else pd.NaT
    fd = pd.Series(first).sort_values()
    crossed, never = fd.dropna(), fd[fd.isna()].index.tolist()
    fig2 = go.Figure(go.Scatter(x=crossed.values, y=[dl.label(k) for k in crossed.index], mode="markers",
                                marker=dict(size=13, color=P["Pea Flower"], line=dict(color=INK, width=.6)),
                                hovertemplate="<b>%{y}</b><br>Lần đầu ≥ 100: %{x|%m/%Y}<extra></extra>"))
    ui.style_fig(fig2, 60 + 28 * max(len(crossed), 3), legend=False, margin=dict(l=10, r=20, t=10, b=30))
    fig2.update_yaxes(autorange="reversed", showgrid=True, gridcolor=GRID)
    fig2.update_xaxes(showgrid=False)
    ui.chart_title("Ai về đích trước?", f"Tháng đầu tiên chỉ số ≥ 100 kể từ {ui.mlabel(piv.index[0])}"
                   + (f" · Chưa về đích: {', '.join(never)}" if never else ""))
    ui.show(fig2, key="race2")


# ============================================================ TRANG 4 · MÙA VỤ & THỜI TIẾT
def page_season(D):
    m, w = D["master"], D["weather"]
    page_header("🌦️", "Mùa vụ & thời tiết", "Khi nào khách đến nhiều, và mưa nắng ở hai điểm đến biển ảnh hưởng thế nào đến việc chọn tháng.")
    t1, t2 = st.tabs(["🔥 Bản đồ nhiệt thị trường × tháng", "☔ Mưa nắng Đà Nẵng · Nha Trang"])
    with t1:
        years = [y for y in sorted(m.loc[m["recovery_index"].notna(), "year"].unique(), reverse=True) if y >= 2022]
        y = st.select_slider("Năm", options=sorted(years), value=2025 if 2025 in years else years[0])
        d = m.loc[(m["year"] == y) & m["recovery_index"].notna()]
        piv = d.pivot(index="market", columns="month", values="recovery_index").reindex(columns=range(1, 13))
        piv = piv.loc[piv.notna().sum(axis=1) >= 6]
        order = m.loc[m["year"] == y].groupby("market")["arrivals"].sum().reindex(piv.index).sort_values(ascending=True).index
        piv = piv.loc[order]
        z = piv.clip(40, 160)
        fig = go.Figure(go.Heatmap(
            z=z.values, x=dl.MONTH_LABEL, y=[dl.label(k) for k in piv.index], colorscale=DIV_SCALE, zmin=40, zmax=160,
            customdata=piv.values, text=piv.round(0).values, texttemplate="%{text:.0f}", textfont=dict(size=10),
            hovertemplate="<b>%{y}</b> %{x}/" + str(y) + "<br>Chỉ số: %{customdata:.0f}<extra></extra>", hoverongaps=False,
            colorbar=dict(title="Chỉ số", tickvals=[40, 70, 100, 130, 160], ticktext=["≤40", "70", "100", "130", "≥160"], len=.8)))
        ui.style_fig(fig, 80 + 24 * len(piv), legend=False, margin=dict(l=10, r=10, t=10, b=10))
        fig.update_yaxes(showgrid=False, tickfont=dict(size=11))
        fig.update_xaxes(side="top")
        ui.chart_title(f"{y}: mỗi ô là chỉ số của một thị trường trong một tháng so với cùng tháng 2019",
                       "Cam = chưa phục hồi · Xám = bằng 2019 · Xanh = vượt 2019. Hàng sắp xếp theo tổng lượt khách trong năm; ô trắng = thiếu số liệu.")
        ui.show(fig, key="se_heat")
        ui.source("Master table M2. Màu cắt ở 40–160 để ngoại lệ không lấn át; số trong ô là giá trị thật.")
    with t2:
        wd = w.loc[w["year"].between(2019, 2025)]
        rain = wd.groupby(["destination", "month"])["precipitation_sum"].median().unstack(0)
        sun = wd.groupby(["destination", "month"])["sunshine_hours"].median().unstack(0)
        dcol = {"Đà Nẵng": P["Pea Flower"], "Nha Trang": P["Florida Oranges"]}
        fig = go.Figure()
        for dest in rain.columns:
            fig.add_trace(go.Bar(x=dl.MONTH_LABEL, y=rain[dest].values, name=dest, marker_color=dcol[dest],
                                 hovertemplate=f"<b>{dest}</b> %{{x}}: %{{y:.0f}} mm<extra></extra>"))
        fig.update_layout(barmode="group")
        ui.style_fig(fig, 360)
        fig.update_yaxes(title="Lượng mưa trung vị (mm/tháng)")
        wet = {c: ", ".join(f"T{k}" for k in rain[c].sort_values(ascending=False).head(3).index.sort_values()) for c in rain.columns}
        ui.chart_title(f"Mưa nhiều nhất: Đà Nẵng vào {wet.get('Đà Nẵng', '–')}; Nha Trang vào {wet.get('Nha Trang', '–')}",
                       "Trung vị lượng mưa từng tháng, 2019–2025")
        ui.show(fig, key="se_rain")
        fig = go.Figure()
        for dest in sun.columns:
            fig.add_trace(go.Scatter(x=dl.MONTH_LABEL, y=sun[dest].values, mode="lines+markers", name=dest,
                                     line=dict(color=dcol[dest], width=3),
                                     hovertemplate=f"<b>{dest}</b> %{{x}}: %{{y:.0f}} giờ<extra></extra>"))
        ui.style_fig(fig, 300)
        fig.update_yaxes(title="Số giờ nắng trung vị")
        ui.chart_title("Số giờ nắng theo tháng", "Trung vị 2019–2025")
        ui.show(fig, key="se_sun")
        ui.source("Open-Meteo Historical Weather qua M2.")
        ui.card("<p>⚠️ Số khách trong master là <b>toàn quốc</b>, còn thời tiết chỉ đo ở Đà Nẵng và Nha Trang — "
                "dữ liệu này giúp chọn <i>tháng đẹp trời để quảng bá điểm đến biển</i>, không chứng minh mưa làm giảm khách.</p>")


# ============================================================ TRANG 5 · PHÂN KHÚC
def page_segments(D):
    seg, prof, evr, sil = D["seg"], D["prof"], D["evr"], D["sil"]
    page_header("🧭", "Phân khúc thị trường", f"{len(seg)} thị trường đủ dữ liệu được chia theo tốc độ phục hồi, mùa vụ, khoảng cách và tăng trưởng (K-means, k = 2).")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure()
        for k, g in seg.groupby("cluster"):
            fig.add_trace(go.Scatter(
                x=g["distance_km"], y=g["seasonal_amplitude"], mode="markers+text", name=CLUSTER_NAME.get(k, f"Cụm {k}"),
                text=[x for x in g.index], textposition="top center", textfont=dict(size=10),
                marker=dict(size=np.sqrt(g["arrivals_latest_ytd"]) / 18 + 8, color=ui.CLUSTER_COLOR[k], opacity=.85, line=dict(color=INK, width=.6)),
                customdata=np.stack([g["recovery_speed"], g["growth_pct"], g["arrivals_latest_ytd"]], 1),
                hovertemplate="<b>%{text}</b><br>Khoảng cách: %{x:,.0f} km<br>Biên độ mùa vụ: %{y:.0f}<br>Tốc độ phục hồi: %{customdata[0]:.1f} điểm/tháng"
                              "<br>Tăng trưởng: %{customdata[1]:.1f}%<br>Lượt khách YTD: %{customdata[2]:,.0f}<extra></extra>"))
        ui.style_fig(fig, 520)
        fig.update_xaxes(title="Khoảng cách địa lý đến Việt Nam (km)", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(title="Biên độ mùa vụ (điểm chỉ số)")
        ui.chart_title("Thị trường gần có mùa vụ nhẹ; thị trường xa có mùa vụ rõ hơn",
                       "Kích thước điểm = lượt khách lũy kế năm nay · màu = cụm K-means")
        ui.show(fig, key="sg_scatter")
        ui.source("Master table M2, đặc trưng tái lập theo M6.")
    with c2:
        for k, r in prof.iterrows():
            top = ", ".join(r["markets"][:6]) + ("…" if len(r["markets"]) > 6 else "")
            ui.card(f"<h4><span class='tag' style='background:{ui.CLUSTER_COLOR[k]};color:#fff'>Cụm {k}</span> {CLUSTER_NAME.get(k, '')}</h4>"
                    f"<p><b>{int(r['n'])} thị trường:</b> {top}</p>"
                    f"<p>Khoảng cách trung vị {ui.n0(r['distance_km'])} km · biên độ mùa vụ {ui.n0(r['seasonal_amplitude'])} · "
                    f"tăng trưởng trung vị {ui.pct(r['growth_pct'])} · tháng đỉnh phổ biến: T{int(r['peak_month_mode'])}</p>"
                    f"<p>🧪 <b>Việc cần thử:</b> {CLUSTER_ACTION.get(k, '')}</p>", "sea" if k == 1 else "sun")
            st.write("")
    ui.card(f"<h4>⚠️ Cụm này KHÔNG có nghĩa là…</h4><p>Hai cụm tách chủ yếu theo <b>khoảng cách</b>, không phải theo tốc độ phục hồi (hai cụm có tốc độ phục hồi trung vị gần nhau). "
            f"Silhouette = {hs._vn(f'{sil:.2f}')} là mức thấp: ranh giới cụm yếu, dùng như <b>gợi ý nhóm</b> chứ không phải ranh giới cứng. "
            f"Cụm cũng không cho biết nguyên nhân thị trường phục hồi nhanh hay chậm. {len(D['excluded'])} thị trường thiếu dữ liệu không được đưa vào "
            f"({', '.join(D['excluded']['market'])}).</p>")
    with st.expander("📄 Bảng đặc trưng từng thị trường"):
        t = seg.reset_index().rename(columns={"market": "Thị trường", "recovery_speed": "Tốc độ phục hồi", "seasonal_amplitude": "Biên độ mùa vụ",
                                              "peak_month": "Tháng đỉnh", "distance_km": "Khoảng cách (km)", "growth_pct": "Tăng trưởng (%)",
                                              "arrivals_latest_ytd": "Lượt khách YTD", "cluster": "Cụm"})
        ui.table(t[["Thị trường", "Cụm", "Tốc độ phục hồi", "Biên độ mùa vụ", "Tháng đỉnh", "Khoảng cách (km)", "Tăng trưởng (%)", "Lượt khách YTD"]].round(2))


# ============================================================ ĐIỀU HƯỚNG
PAGES = {
    "Câu chuyện": page_story,
    "Explorer & Hỏi nhanh": page_explorer,
    "Đua phục hồi": page_race,
    "Mùa vụ & thời tiết": page_season,
    "Phân khúc thị trường": page_segments,
    "Tương tác đa chiều": m78.page_many_dimensions,
    "Góc nhìn 3D & 2D": m78.page_beyond_flat,
    "Kiểm thử & cải tiến": None,
}

with st.sidebar:
    st.markdown("<div class='brand'>🌴 Coming Back<small>Du lịch quốc tế Việt Nam</small></div>", unsafe_allow_html=True)
    st.write("")
    choice = st.radio("Điều hướng", list(PAGES), label_visibility="collapsed")
    st.write("")
    st.caption("Nhóm 04 - Data Visualization")

D = get_data()
with st.sidebar:
    st.caption(f"Dữ liệu đến {ui.mlabel(dl.latest_date(D['master']))}")

if PAGES[choice] is None:
    m10.page(D)
else:
    PAGES[choice](D)
