"""
app.py - "Coming Back": Khách quốc tế trở lại Việt Nam (P07)
M9 (Interaction & Story) + M10 (Evaluate & Improve) - phụ trách: Cẩm Tiên
Chạy:  streamlit run app.py
"""
from __future__ import annotations

import hashlib
import importlib
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import data_layer as dl
import house_style as hs
import m10
import pages_m7_m8 as m78
import ui
if not hasattr(ui, "page_header") or not hasattr(ui, "guide_box") or not hasattr(ui, "set_title"):
    ui = importlib.reload(ui)
    m78 = importlib.reload(m78)
    m10 = importlib.reload(m10)
from ui import INK, MUTED, GRID, P

st.set_page_config(page_title="Coming Back · Du lịch Việt Nam", page_icon="🏝️", layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

PLOTLY_MARKER = {"o": "circle", "s": "square", "^": "triangle-up", "D": "diamond", "v": "triangle-down", "P": "cross"}
DIV_SCALE = [[i / (len(hs.DIV_COLORS) - 1), c] for i, c in enumerate(hs.DIV_COLORS)]
CLUSTER_NAME = {1: "Thị trường xa – Mùa vụ rõ hơn", 2: "Thị trường gần – Mùa vụ nhẹ hơn"}
CLUSTER_ACTION = {
    1: "Theo dõi lịch bay dài hạn và thời điểm đặt tour trước mùa cao điểm.",
    2: "Cân nhắc các gói lưu trú ngắn ngày vào những tháng công suất còn thấp.",
}


# ============================================================ dữ liệu (cache)
def get_data():
    m = dl.load_master()
    feats, excl = dl.build_features(m)
    seg, prof, evr, sil = dl.segment_markets(feats)
    return dict(
        master=m, weather=dl.load_weather(), trends=dl.load_trends(), corr=dl.load_correlations(), yoy=dl.load_yoy(),
        feats=feats, excluded=excl, seg=seg, prof=prof, evr=evr, sil=sil, season=dl.seasonal_index(m),
        colors=ui.market_colors(sorted(m["market"].unique())),
    )


def page_header(icon, title, text, guide=""):
    if hasattr(ui, "page_header"):
        ui.page_header(icon, title, text, guide)
        return
    st.markdown(
        f"<h2 style='margin:.2rem 0 .15rem;font-weight:800'>{icon} {title}</h2>"
        f"<p style='color:{MUTED};margin:0 0 .65rem;font-size:1rem'>{text}</p>",
        unsafe_allow_html=True,
    )
    if guide:
        st.info(guide)


def _guide_box(title: str, body_html: str):
    if hasattr(ui, "guide_box"):
        ui.guide_box(title, body_html)
    else:
        st.markdown(
            f"<div style='background:#fff;border:1px solid #F1EADB;border-left:4px solid #2F7D8C;"
            f"border-radius:12px;padding:.75rem 1rem;margin:.2rem 0 .85rem;font-size:.88rem;color:{INK}'>"
            f"<div style='font-weight:700;margin-bottom:.25rem;color:#25533F'>{title}</div>{body_html}</div>",
            unsafe_allow_html=True,
        )


def _set_title(fig, title: str, top_margin: int | None = None):
    if hasattr(ui, "set_title"):
        return ui.set_title(fig, title, top_margin)
    fig.update_layout(title=dict(text=f"<b>{title}</b>", x=0.01, xanchor="left"), margin=dict(t=top_margin or 56))
    return fig


def add_gap_band(fig, start="2020-04-01", end="2021-12-31", text="Không có số liệu theo thị trường"):
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
        "Du lịch quốc tế Việt Nam: Phục hồi đến đâu sau đại dịch?",
        f"Theo dõi lượng khách từ {m['market'].nunique()} thị trường quốc tế giai đoạn 2017–{end.year} (dữ liệu đến {ui.mlabel(end)}), "
        "so sánh với năm 2019 để nhận diện những thị trường đã phục hồi và những thị trường còn khoảng cách cần thu hẹp.",
        ["Tổng quan phục hồi", f"Dữ liệu đến {ui.mlabel(end)}", "Mốc so sánh: 2019 = 100"],
    )
    st.write("")
    c = st.columns(4)
    d_idx = tot["index"] - 100
    ui.kpi(c[0], f"Chỉ số phục hồi ({ui.mlabel(end)})", ui.n1(tot["index"]),
           f"<span class='{'up' if d_idx >= 0 else 'down'}'>{ui.pct(d_idx)}</span> so với cùng tháng 2019 · {tot['n']} thị trường có mốc so sánh")
    g_prev = 100 * (ytd["this"] / ytd["prev"] - 1)
    ui.kpi(c[1], f"Lũy kế T1–T{ytd['month']}/{ytd['year']}", ui.big(ytd["this"]),
           f"<span class='{'up' if g_prev >= 0 else 'down'}'>{ui.pct(g_prev)}</span> so với cùng kỳ {ytd['year'] - 1}")
    g_base = 100 * (ytd["this"] / ytd["base"] - 1)
    ui.kpi(c[2], "Lũy kế so với cùng kỳ 2019", ui.pct(g_base), f"Tính trên {ytd['month']} tháng đầu năm · {ytd['n']} thị trường đủ số liệu")
    ui.kpi(c[3], "Thị trường đã vượt mốc 2019", f"{len(above)}/{len(has_base)}",
           f"{len(below)} thị trường vẫn dưới mốc 2019 (chỉ số &lt; 95)")

    # ---- Điểm đáng chú ý
    st.write("")
    names_worst = " và ".join(worst["market"])
    names_best = ", ".join(best["market"])
    idx_w = ", ".join(f"{r.market}: {ui.n0(r.recovery_index)}" for r in worst.itertuples())
    ui.card(
        f"<h4>Điểm đáng chú ý</h4>"
        f"<p style='font-size:1.03rem'>Tổng lượng khách trong {ui.mlabel(end)} đạt chỉ số phục hồi <b>{ui.n0(tot['index'])}</b> "
        f"(vượt mốc trước đại dịch = 100), nhưng mức phục hồi giữa các thị trường vẫn khác nhau. "
        f"Những thị trường đóng góp nhiều lượt khách tăng thêm nhất so với cùng kỳ 2019 gồm <b>{names_best}</b>, "
        f"trong khi một số thị trường quy mô lớn như <b>{names_worst}</b> vẫn chưa trở lại mức năm 2019 ({idx_w}). "
        f"Vì vậy, cần xem xét riêng từng thị trường thay vì chỉ dựa vào tổng lượng khách.</p>"
        f"<p style='color:{MUTED};font-size:.86rem;margin:0'>Mọi chỉ số được tính trên cùng tập thị trường có đủ dữ liệu so sánh với năm 2019.</p>",
        "sun")

    # ---- Chương 1: trước đại dịch
    ui.chapter(1, "Trước đại dịch, những thị trường nào gửi nhiều khách đến Việt Nam?",
               "Tổng lượt khách năm 2019 của 10 thị trường lớn nhất — đây là mốc so sánh cho toàn bộ chỉ số phục hồi trong dashboard.")
    y19 = m.loc[(m["year"] == 2019) & m["arrivals"].notna()].groupby("market")["arrivals"].agg(["sum", "count"])
    y19 = y19[y19["count"] == 12].sort_values("sum", ascending=False).head(10).iloc[::-1]
    fig = go.Figure(go.Bar(
        x=y19["sum"], y=[dl.label(k) for k in y19.index], orientation="h",
        marker_color=[colors[k] for k in y19.index], text=[ui.big(v) for v in y19["sum"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Tổng lượt khách 2019: <b>%{x:,.0f} lượt</b><extra></extra>", cliponaxis=False))
    ui.style_fig(fig, 400, legend=False, margin=dict(l=10, r=70, t=10, b=10))
    fig.update_xaxes(visible=True, showgrid=True, gridcolor=GRID, title_text="Tổng lượt khách năm 2019 (lượt)",
                     tickformat=",.0f", range=[0, float(y19["sum"].max()) * 1.18])
    fig.update_yaxes(showgrid=False, title_text="Thị trường")
    full19 = m.loc[(m["year"] == 2019) & m["arrivals"].notna()].groupby("market")["arrivals"].agg(["sum", "count"])
    full19 = full19[full19["count"] == 12]["sum"].sort_values(ascending=False)
    share2 = 100 * full19.head(2).sum() / full19.sum()
    _set_title(fig, "Top thị trường theo tổng lượt khách năm 2019")
    ui.chart_title("", f"{full19.index[0]} và {full19.index[1]} chiếm {ui.n0(share2)}% lượt khách năm 2019 · nhãn cột rút gọn theo nghìn/triệu lượt (trên {len(full19)} thị trường đủ 12 tháng)")
    ui.show(fig, key="s1")
    ui.source("Cục Du lịch Quốc gia Việt Nam (VNAT) và Tổng cục Thống kê (NSO).")

    # ---- Chương 2: gián đoạn
    ui.chapter(2, "Đại dịch đã làm lượng khách giảm mạnh như thế nào?",
               "Đọc đường chỉ số phục hồi gộp từ năm 2017 đến giữa 2022; đường chấm ngang là mốc năm 2019 (= 100), vùng xám là giai đoạn thiếu số liệu theo thị trường.")
    ts = dl.total_index_series(m).set_index("date")["index"]
    rng = pd.date_range("2017-01-01", "2022-06-01", freq="MS")
    s2 = ts.reindex(rng)
    fig = go.Figure(go.Scatter(x=s2.index, y=s2.values, mode="lines+markers", connectgaps=False,
                               line=dict(color=P["Poppy"], width=3), marker=dict(size=7),
                               hovertemplate="Thời gian: %{x|%m/%Y}<br>Chỉ số phục hồi gộp: <b>%{y:,.1f}</b> (2019 = 100)<extra></extra>"))
    add_gap_band(fig)
    fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019 = 100", annotation_position="top left")
    ui.style_fig(fig, 360, legend=False)
    fig.update_xaxes(title_text="Thời gian (tháng/năm)", tickformat="%m/%Y", dtick="M6", tickangle=-20)
    fig.update_yaxes(title_text="Chỉ số phục hồi gộp (2019 = 100)", tickformat=",.0f")
    _set_title(fig, "Diễn biến phục hồi lượng khách quốc tế giai đoạn 2017–2022")
    ui.chart_title("", "Quý I/2020 giảm sâu từ mức 2019 trước khi dữ liệu bị gián đoạn đến 2022 (chỉ số gộp = tổng lượt khách ÷ tổng lượt khách cùng tháng 2019)")
    ui.show(fig, key="s2")
    ui.source("Bảng dữ liệu tổng hợp VNAT/NSO. Vùng xám là giai đoạn không công bố số liệu theo từng thị trường (không phải giá trị 0).")

    # ---- Chương 3: mở cửa lại
    ui.chapter(3, "Lượng khách mất bao lâu để trở lại mức năm 2019?",
               "Từ năm 2022, số liệu theo thị trường được công bố trở lại; theo dõi thời điểm chỉ số phục hồi gộp vượt đường chấm mốc 100.")
    s3 = ts.loc["2022-01-01":]
    cross = s3[s3 >= 100]
    fig = go.Figure(go.Scatter(x=s3.index, y=s3.values, mode="lines+markers", line=dict(color=P["Pea Flower"], width=3),
                               marker=dict(size=6), hovertemplate="Thời gian: %{x|%m/%Y}<br>Chỉ số phục hồi gộp: <b>%{y:,.1f}</b> (2019 = 100)<extra></extra>"))
    fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019 = 100", annotation_position="bottom right")
    if len(cross):
        fig.add_annotation(x=cross.index[0], y=cross.iloc[0], text=f"Lần đầu ≥ 100: {ui.mlabel(cross.index[0])}",
                           ax=-60, ay=-55, showarrow=True, arrowhead=2, arrowcolor=INK, font=dict(size=12))
    ui.style_fig(fig, 380, legend=False)
    fig.update_xaxes(title_text="Thời gian (tháng/năm)", tickformat="%m/%Y", dtick="M6", tickangle=-20)
    fig.update_yaxes(title_text="Chỉ số phục hồi gộp (2019 = 100)", tickformat=",.0f")
    note3 = (f"Tổng lượng khách lần đầu chạm mốc 2019 vào {ui.mlabel(cross.index[0])} và đạt {ui.n0(s3.iloc[-1])} vào {ui.mlabel(s3.index[-1])}"
             if len(cross) else "Tổng lượng khách vẫn chưa chạm mốc 2019")
    _set_title(fig, f"Diễn biến phục hồi của các thị trường giai đoạn 2022–{ui.mlabel(s3.index[-1])}")
    ui.chart_title("", f"{note3} · nhịp lên xuống phản ánh biến động mùa vụ trong năm")
    ui.show(fig, key="s3")
    ui.source("Bảng dữ liệu tổng hợp VNAT/NSO.")

    # ---- Chương 4: không đồng đều
    ui.chapter(4, "Thị trường nào đang đóng góp vào đà phục hồi?",
               f"Biểu đồ so sánh mức chênh lệch số lượt khách thực tế trong {ui.mlabel(end)} so với cùng tháng năm 2019. Màu xanh = vượt mốc 2019; màu cam = còn thấp hơn 2019.")
    g = has_base.reindex(has_base["gap"].abs().sort_values(ascending=False).index).head(16).sort_values("gap")
    max_abs = float(g["gap"].abs().max()) * 1.24 if len(g) else 1.0
    fig = go.Figure(go.Bar(
        x=g["gap"], y=[dl.label(k) for k in g["market"]], orientation="h",
        marker_color=[ui.STATUS_COLOR[s] for s in g["status"]],
        text=[f"{'+' if v > 0 else ''}{ui.big(v)}" for v in g["gap"]], textposition="outside", cliponaxis=False,
        customdata=np.stack([g["arrivals"], g["baseline_2019"], g["recovery_index"]], 1),
        hovertemplate="<b>%{y}</b><br>Chênh lệch: <b>%{x:+,.0f} lượt</b><br>Lượt khách tháng này: %{customdata[0]:,.0f} lượt<br>Cùng tháng 2019: %{customdata[1]:,.0f} lượt"
                      "<br>Chỉ số phục hồi: <b>%{customdata[2]:,.1f}</b><extra></extra>"))
    ui.style_fig(fig, 540, legend=False, margin=dict(l=10, r=70, t=10, b=10))
    fig.add_vline(x=0, line_color=INK, line_width=1)
    fig.update_yaxes(showgrid=False, title_text="Thị trường")
    fig.update_xaxes(showgrid=True, gridcolor=GRID, title_text="Chênh lệch lượt khách so với cùng tháng 2019 (lượt)",
                     tickformat="+,.0f", range=[-max_abs, max_abs])
    top_pos = g.sort_values("gap", ascending=False).iloc[0]
    top_neg = g.sort_values("gap").iloc[0]
    _set_title(fig, f"Chênh lệch lượt khách theo thị trường so với cùng tháng năm 2019 ({ui.mlabel(end)})")
    ui.chart_title("", f"{top_pos['market']} tăng thêm nhiều nhất, trong khi {top_neg['market']} còn thiếu hụt lớn nhất (16 thị trường chênh lệch lớn nhất · Cam: chưa phục hồi · Xám: quanh 2019 · Xanh: vượt 2019)")
    ui.show(fig, key="s4")
    ui.source("Bảng dữ liệu tổng hợp VNAT/NSO. Chỉ gồm các thị trường có số liệu gốc năm 2019.")

    # ---- Chương 5: hàm ý
    ui.chapter(5, "Hàm ý cho việc phát triển thị trường khách quốc tế",
               "Ba hướng theo dõi gợi ý từ dữ liệu để kiểm chứng thêm — không phải kết luận về quan hệ nhân quả.")
    a, b, c3 = st.columns(3)
    with a:
        ui.card(f"<h4>🛟 Duy trì đà tăng ở thị trường đang phát triển</h4><p>Nhóm đóng góp lượng khách tăng thêm lớn nhất: <b>{names_best}</b>.</p>"
                "<p>Theo dõi sức chứa, đường bay và khả năng phục vụ tại các điểm đến trong mùa cao điểm trước khi mở rộng hoạt động quảng bá.</p>", "sea")
    with b:
        ui.card(f"<h4>🎯 Rà soát thị trường chưa phục hồi</h4><p><b>{names_worst}</b> vẫn dưới mốc 2019 "
                f"(thiếu tổng cộng <b>{ui.big(worst['gap'].abs().sum())}</b> lượt trong {ui.mlabel(end)} so với cùng tháng 2019).</p>"
                "<p>Xem xét biến động lượng khách gần đây và những rào cản có thể ảnh hưởng đến khả năng quay trở lại tại mục <i>Khám phá dữ liệu → Trả lời câu hỏi thực tế</i>.</p>", "sun")
    with c3:
        ui.card("<h4>📅 Lựa chọn thời điểm triển khai</h4><p>Mức độ mùa vụ khác nhau giữa nhóm thị trường gần và thị trường xa.</p>"
                "<p>Đối chiếu mùa cao điểm, mùa thấp điểm và điều kiện thời tiết tại trang <i>Mùa vụ và thời tiết</i> và <i>Nhóm thị trường</i> trước khi thử nghiệm chiến dịch.</p>")

    with st.expander("ℹ️ Nguồn dữ liệu và giới hạn cần lưu ý"):
        st.markdown(
            "- **Nguồn dữ liệu:** Lượt khách theo thị trường từ VNAT/NSO; mức quan tâm tìm kiếm từ Google Trends (3 thị trường); "
            "dữ liệu thời tiết từ Open-Meteo (Đà Nẵng, Nha Trang), ghép theo thị trường và tháng.\n"
            "- **Khoảng trống 2020–2021:** Nguồn thống kê không có số liệu tách theo từng thị trường nên biểu đồ hiển thị là *khoảng trống*, không phải giá trị 0.\n"
            f"- **Chỉ số phục hồi** = lượt khách tháng ÷ cùng tháng năm 2019 × 100 (chỉ tính khi có cả hai giá trị). "
            f"{len(D['excluded'])} thị trường không được đưa vào phần phân nhóm do chưa đủ dữ liệu.\n"
            "- **Thị trường quy mô nhỏ:** Có thể xuất hiện biến động chỉ số rất lớn (do nền năm 2019 chỉ vài trăm lượt/tháng) — nên đọc kèm số lượt khách thực tế.\n"
            "- **Google Trends:** Chỉ có cho Nhật Bản, Hàn Quốc, Đài Loan và phản ánh mức độ quan tâm *tương đối* trên thang 0–100.")


# ============================================================ TRANG 2 · KHÁM PHÁ DỮ LIỆU
def _presets(D):
    m, f = D["master"], D["feats"]
    end = dl.latest_date(m)
    last12 = m.loc[m["date"] > end - pd.DateOffset(months=12)].groupby("market")["arrivals"].sum().sort_values(ascending=False)
    return {
        "6 thị trường có lượng khách lớn": last12.index[:6].tolist(),
        "Thị trường Đông Bắc Á": ["Hàn Quốc", "Trung Quốc", "Nhật Bản", "Đài Loan"],
        "Thị trường Đông Nam Á": ["Thái Lan", "Malaysia", "Singapore", "Indonesia", "Philippines", "Campuchia"],
        "Thị trường châu Âu, châu Mỹ và Úc": ["Nga", "Hoa Kỳ", "Pháp", "Đức", "Vương quốc Anh", "Úc"],
        "6 thị trường tăng trưởng cao": f.sort_values("growth_pct", ascending=False).index[:6].tolist(),
        "Tự chọn thị trường": ["Hàn Quốc", "Trung Quốc", "Nhật Bản"],
    }


def page_explorer(D):
    page_header(
        "🔎",
        "Khám phá dữ liệu",
        "Chọn thị trường, khoảng thời gian và chỉ số để theo dõi biến động lượng khách. Bạn cũng có thể so sánh nhiều thị trường trên cùng một biểu đồ.",
        "Bắt đầu từ bước 1 đến 4 trong khung lọc ở tab <b>Tự chọn dữ liệu</b>, hoặc chuyển sang tab <b>Trả lời câu hỏi thực tế</b> để xem sẵn 3 phân tích trọng tâm.",
    )
    t1, t2 = st.tabs(["📈 Tự chọn dữ liệu", "🎯 Trả lời câu hỏi thực tế"])
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
        preset = c1.radio("1. Chọn nhóm thị trường", list(presets), horizontal=False, key="ex_preset")
        default = [x for x in presets[preset] if x in D["colors"]]
        sel = c2.multiselect("2. Chọn thị trường cần xem", sorted(m["market"].unique()), default=default,
                             key=f"ex_mk_{preset}", help="Có thể thêm hoặc bớt thị trường tùy ý. Mỗi thị trường giữ nguyên một màu cố định trên toàn ứng dụng.")
        c3, c4 = st.columns([1.1, 1.5])
        metric = c3.radio("3. Bạn muốn so sánh theo", ["Chỉ số phục hồi (2019 = 100)", "Lượt khách mỗi tháng", "Tỷ trọng trong tổng (%)"],
                          key="ex_metric")
        d0 = pd.Timestamp("2017-01-01")
        start_default = d0 if d0 in all_dates else all_dates[0]

        rng = c4.select_slider(
            "4. Thời gian phân tích",
            options=all_dates,
            value=(start_default, all_dates[-1]),
            format_func=ui.mlabel,
            key="ex_range"
        )
        c5, c6, _ = st.columns([1.1, 1.1, 1.4])
        smooth = c5.toggle("Làm mượt đường biểu diễn", value=False, help="Tính trung bình trượt 3 tháng để giảm dao động ngắn hạn theo mùa vụ.")
        show_base = c6.toggle("Hiện đường mốc năm 2019", value=True, help="Hiển thị đường tham chiếu tại mức 100 khi đang xem Chỉ số phục hồi.")

    _guide_box(
        "Cách đọc 3 chỉ số và thang phục hồi",
        "<ul style='margin:.2rem 0 .45rem 1.1rem;padding:0'>"
        "<li><b>Chỉ số phục hồi:</b> So sánh lượng khách với cùng tháng năm 2019. Mốc 100 tương đương năm 2019.</li>"
        "<li><b>Lượt khách mỗi tháng:</b> Cho biết số khách thực tế đến từ từng thị trường.</li>"
        "<li><b>Tỷ trọng trong tổng:</b> Cho biết mỗi thị trường đóng góp bao nhiêu phần trăm tổng lượt khách quốc tế.</li>"
        "</ul>"
        "<div style='font-size:.82rem;color:#5C605B'>Ví dụ minh họa cách đọc Chỉ số phục hồi (không phải số liệu thực tế):</div>"
        "<div class='scale-grid'>"
        "<div class='scale-item'><div class='num'>80</div><div class='desc'>Thấp hơn cùng tháng 2019: 20%</div></div>"
        "<div class='scale-item'><div class='num'>100</div><div class='desc'>Bằng mức cùng tháng 2019</div></div>"
        "<div class='scale-item'><div class='num'>120</div><div class='desc'>Cao hơn cùng tháng 2019: 20%</div></div>"
        "</div>",
    )

    if not sel:
        st.info("Chọn ít nhất một thị trường để bắt đầu.")
        return
    d = m.loc[m["market"].isin(sel) & m["date"].between(*rng)].copy()
    if metric.startswith("Chỉ số"):
        d["y"], ytitle, fmt, ytick, unit, mname = d["recovery_index"], "Chỉ số phục hồi (2019 = 100)", ",.1f", ",.0f", " (2019 = 100)", "Chỉ số phục hồi"
    elif metric.startswith("Lượt"):
        d["y"], ytitle, fmt, ytick, unit, mname = d["arrivals"], "Lượt khách quốc tế (lượt)", ",.0f", ",.0f", " lượt", "Lượt khách"
    else:
        tot_m = m.groupby("date")["arrivals"].transform("sum")
        d = m.loc[m["market"].isin(sel) & m["date"].between(*rng)].copy()
        d["y"], ytitle, fmt, ytick, unit, mname = 100 * d["arrivals"] / tot_m.loc[d.index], "Tỷ trọng trong tổng lượt khách (%)", ",.1f", ",.1f", "%", "Tỷ trọng"
    if smooth:
        d["y"] = d.sort_values("date").groupby("market")["y"].transform(lambda s: s.rolling(3, min_periods=2).mean())

    fig = go.Figure()
    for mk in sel:
        g = d.loc[d["market"] == mk].sort_values("date")
        g = g.set_index("date")["y"].reindex(pd.date_range(rng[0], rng[1], freq="MS"))
        fig.add_trace(go.Scatter(
            x=g.index, y=g.values, mode="lines+markers", name=dl.label(mk), connectgaps=False,
            line=dict(color=colors[mk], width=3), marker=dict(size=6, symbol=PLOTLY_MARKER.get(hs.MARKET_MARKERS.get(mk, "o"), "circle")),
            hovertemplate=f"<b>{mk}</b> · %{{x|%m/%Y}}<br>{mname}: <b>%{{y:{fmt}}}{unit}</b><extra></extra>"))
        last = g.dropna()
        if len(last):
            fig.add_trace(go.Scatter(x=[last.index[-1]], y=[last.iloc[-1]], mode="text", text=[f"  {mk}"], textposition="middle right",
                                     textfont=dict(size=12, color=INK), showlegend=False, hoverinfo="skip"))
    if metric.startswith("Chỉ số") and show_base:
        fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019 = 100", annotation_position="top left")
    if pd.Timestamp(rng[0]) <= pd.Timestamp("2021-12-01") and pd.Timestamp(rng[1]) >= pd.Timestamp("2020-04-01"):
        add_gap_band(fig, start=str(max(pd.Timestamp(rng[0]), pd.Timestamp("2020-04-01")).date()),
                     end=str(min(pd.Timestamp(rng[1]), pd.Timestamp("2021-12-31")).date()))
    ui.style_fig(fig, 480, legend=False, margin=dict(l=10, r=90, t=10, b=10))
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(title_text=ytitle, tickformat=ytick)
    fig.update_xaxes(title_text="Thời gian (tháng/năm)", tickformat="%m/%Y", range=[rng[0], pd.Timestamp(rng[1]) + pd.DateOffset(months=4)])
    if metric.startswith("Chỉ số"):
        main_title = f"Diễn biến phục hồi của các thị trường ({ui.mlabel(rng[0])} – {ui.mlabel(rng[1])})"
    elif metric.startswith("Lượt"):
        main_title = f"Diễn biến lượt khách quốc tế theo thời gian ({ui.mlabel(rng[0])} – {ui.mlabel(rng[1])})"
    else:
        main_title = f"Tỷ trọng lượt khách theo thị trường qua thời gian ({ui.mlabel(rng[0])} – {ui.mlabel(rng[1])})"
    _set_title(fig, main_title)
    ui.chart_title("", f"Thị trường đang chọn: {', '.join(sel[:4])}{'…' if len(sel) > 4 else ''}"
                   + (" · đang bật làm mượt trung bình trượt 3 tháng" if smooth else "")
                   + " · mỗi đường tương ứng một thị trường")
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
               f"{ui.mlabel(end)} · {ui.big(a)} lượt<br>Cùng kỳ năm trước: {ui.pct(yoy)}")

    # xếp hạng tháng
    st.write("")
    avail = [d_ for d_ in all_dates if m.loc[m["date"] == d_, "recovery_index"].notna().sum() >= 10]
    rc1, rc2 = st.columns([1.4, 1])
    rk_date = rc1.select_slider("Tháng xếp hạng (độc lập với biểu đồ trên)", options=avail, value=avail[-1], format_func=ui.mlabel, key="ex_rank")
    rk_metric = rc2.radio("Chỉ số xếp hạng", ["Chỉ số phục hồi (2019 = 100)", "Lượt khách mỗi tháng", "Tỷ trọng trong tổng (%)"],
                          horizontal=False, key="ex_rank_metric")

    snap_rk = dl.market_snapshot(m, rk_date)
    if rk_metric.startswith("Chỉ số"):
        s = snap_rk.dropna(subset=["recovery_index"]).sort_values("recovery_index", ascending=False).head(15).iloc[::-1]
        fig = go.Figure(go.Bar(
            x=s["recovery_index"], y=[dl.label(k) for k in s["market"]], orientation="h",
            marker_color=[ui.STATUS_COLOR[x] for x in s["status"]], text=[ui.n1(v) for v in s["recovery_index"]], textposition="outside",
            cliponaxis=False, customdata=np.stack([s["arrivals"]], 1),
            hovertemplate="<b>%{y}</b><br>Chỉ số phục hồi: <b>%{x:,.1f}</b> (2019 = 100)<br>Lượt khách: %{customdata[0]:,.0f} lượt<extra></extra>"))
        fig.add_vline(x=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019 = 100", annotation_position="top right")
        rk_xtitle, rk_xtick, rk_xmax = "Chỉ số phục hồi (2019 = 100)", ",.0f", float(s["recovery_index"].max()) * 1.15 if len(s) else 120
        rank_title = f"Mức phục hồi theo từng tháng so với năm 2019 ({ui.mlabel(rk_date)})"
        rank_sub = (f"15 thị trường có chỉ số phục hồi cao nhất trong {ui.mlabel(rk_date)} (Cam: dưới 95 · Xám: 95–105 · Xanh: trên 105). "
                    "Lưu ý: bộ lọc xếp hạng bên dưới độc lập với biểu đồ xu hướng phía trên.")
    elif rk_metric.startswith("Lượt"):
        s = snap_rk.sort_values("arrivals", ascending=False).head(15).iloc[::-1]
        fig = go.Figure(go.Bar(
            x=s["arrivals"], y=[dl.label(k) for k in s["market"]], orientation="h",
            marker_color=[colors[k] for k in s["market"]], text=[ui.big(v) for v in s["arrivals"]], textposition="outside",
            cliponaxis=False, customdata=np.stack([s["recovery_index"].fillna(-1)], 1),
            hovertemplate="<b>%{y}</b><br>Lượt khách: <b>%{x:,.0f} lượt</b><br>Chỉ số phục hồi: %{customdata[0]:,.1f}<extra></extra>"))
        rk_xtitle, rk_xtick, rk_xmax = "Lượt khách quốc tế (lượt)", ",.0f", float(s["arrivals"].max()) * 1.18 if len(s) else 100
        rank_title = f"Quy mô lượt khách giữa các thị trường ({ui.mlabel(rk_date)})"
        rank_sub = (f"15 thị trường có số lượt khách thực tế cao nhất trong {ui.mlabel(rk_date)} (nhãn cột rút gọn theo nghìn/triệu lượt). "
                    "Bộ lọc xếp hạng bên dưới hoạt động độc lập với biểu đồ xu hướng phía trên.")
    else:
        tot_rk = snap_rk["arrivals"].sum()
        snap_rk["share"] = 100 * snap_rk["arrivals"] / tot_rk if tot_rk else np.nan
        s = snap_rk.sort_values("share", ascending=False).head(15).iloc[::-1]
        fig = go.Figure(go.Bar(
            x=s["share"], y=[dl.label(k) for k in s["market"]], orientation="h",
            marker_color=[colors[k] for k in s["market"]], text=[ui.pct(v, signed=False) for v in s["share"]], textposition="outside",
            cliponaxis=False, customdata=np.stack([s["arrivals"]], 1),
            hovertemplate="<b>%{y}</b><br>Tỷ trọng: <b>%{x:,.1f}%</b><br>Lượt khách: %{customdata[0]:,.0f} lượt<extra></extra>"))
        rk_xtitle, rk_xtick, rk_xmax = "Tỷ trọng trong tổng lượt khách (%)", ",.1f", float(s["share"].max()) * 1.18 if len(s) else 100
        rank_title = f"Tỷ trọng đóng góp lượt khách theo thị trường ({ui.mlabel(rk_date)})"
        rank_sub = (f"15 thị trường đóng góp tỷ trọng lớn nhất trong tổng lượt khách {ui.mlabel(rk_date)}. "
                    "Bộ lọc xếp hạng bên dưới hoạt động độc lập với biểu đồ xu hướng phía trên.")

    ui.style_fig(fig, 470, legend=False, margin=dict(l=10, r=70, t=10, b=10))
    fig.update_yaxes(showgrid=False, title_text="Thị trường")
    fig.update_xaxes(visible=True, showgrid=True, gridcolor=GRID, title_text=rk_xtitle, tickformat=rk_xtick, range=[0, rk_xmax])
    _set_title(fig, rank_title)
    ui.chart_title("", rank_sub)
    ui.show(fig, key="ex_rank_chart")

    with st.expander("📄 Xem và tải bảng dữ liệu đang lọc"):
        out = d[["market", "date", "arrivals", "baseline_2019", "recovery_index"]].sort_values(["market", "date"])
        ui.table(out)
        st.download_button("⬇️ Tải CSV", out.to_csv(index=False).encode("utf-8-sig"), "du_lieu_loc.csv", "text/csv")


def _explorer_qa(D):
    m, colors = D["master"], D["colors"]
    end = dl.latest_date(m)
    q = st.radio("Chọn câu hỏi cần phân tích", [
        "1️⃣ Nên ưu tiên kéo khách trở lại từ thị trường nào?",
        "2️⃣ Chạy chiến dịch vào tháng nào cho một thị trường?",
        "3️⃣ Tìm kiếm trực tuyến có báo trước lượt khách không?"], key="qa_q", horizontal=True)
    number = int(q[0])
    st.markdown(f"### Câu {number:02d} · {['Tìm thị trường ưu tiên', 'Đọc mùa vụ', 'Đọc mối liên hệ'][number - 1]}")
    prompts = [
        "Quan sát mức thiếu hụt lượt khách ở tháng mới nhất. Thị trường nào có mức thiếu hụt lớn nhất so với cùng tháng năm 2019?",
        "Dựa vào biểu đồ mùa vụ của thị trường đang chọn, tháng nào có chỉ số mùa vụ cao nhất?",
        "Quan sát biểu đồ phân tán: nhận định nào phù hợp nhất về mối liên hệ giữa tìm kiếm trực tuyến đi trước và lượt khách?",
    ]
    st.info(f"{prompts[number - 1]}\n\nHãy tự đọc biểu đồ trước khi chọn và xác nhận đáp án.")
    if "qa_quiz_results" not in st.session_state:
        st.session_state.qa_quiz_results = {}
    results = st.session_state.qa_quiz_results
    attempts = st.session_state.setdefault("qa_quiz_attempts", {})

    def options(answer, distractors, seed):
        values = [answer] + [x for x in distractors if x != answer]
        values = values[:4]
        if len(values) > 1:
            offset = hashlib.sha256(str(seed).encode()).digest()[0] % len(values)
            values = values[offset:] + values[:offset]
        return values

    def identity(question, filters):
        key = f"q{question}|{filters}"
        return key, hashlib.sha256(key.encode()).hexdigest()[:12]

    def answer_widget(key, token, choices, answer, explanation, answer_title="Đáp án đúng"):
        st.session_state.setdefault("qa_current_keys", {})[f"q{number}"] = key
        result = results.get(key)
        started = f"qa_started_{token}"
        st.session_state.setdefault(started, time.time())
        st.markdown("#### 🧠 Chọn đáp án của bạn")
        selected = st.radio("Phương án", choices, index=None, key=f"qa_choice_{token}",
                             label_visibility="collapsed", disabled=result is not None)
        if result is None:
            if st.button("✅ Xác nhận đáp án", key=f"qa_submit_{token}",
                         disabled=not selected, type="primary"):
                attempts[key] = attempts.get(key, 0) + 1
                results[key] = {
                    "question": f"Câu {number}", "selected": selected, "answer": answer,
                    "correct": selected == answer,
                    "seconds": round(max(0, time.time() - st.session_state[started]), 1),
                    "attempts": attempts[key],
                }
                st.rerun()
            st.caption("Chọn một phương án và xác nhận để xem kết quả cùng lời giải.")
            return
        if result["correct"]:
            st.success("🎉 Chính xác! Bạn đã đọc đúng insight từ biểu đồ.")
        else:
            st.error("Chưa chính xác, hãy cùng xem lại dữ liệu nhé!")
        st.markdown(f"**{answer_title}: {answer}**")
        st.write(explanation)
        st.caption(f"Thời gian trả lời: {result['seconds']:.1f} giây · Số lần xác nhận: {result['attempts']}")
        if st.button("↻ Làm lại câu hỏi", key=f"qa_retry_{token}"):
            results.pop(key, None)
            st.session_state.pop(f"qa_choice_{token}", None)
            st.session_state[started] = time.time()
            st.rerun()

    if q.startswith("1"):
        snap = dl.market_snapshot(m, end).dropna(subset=["recovery_index"])
        snap["short"] = snap["baseline_2019"] - snap["arrivals"]
        ranked = snap.loc[snap["short"] > 0].sort_values("short", ascending=False)
        if ranked.empty:
            st.info("Không có thị trường thiếu hụt lượt khách ở tháng mới nhất để tạo câu hỏi này.")
            return
        shown = ranked.head(8).iloc[::-1]
        fig = go.Figure(go.Bar(
            x=shown["short"], y=[dl.label(k) for k in shown["market"]], orientation="h", marker_color=P["Poppy"],
            text=[ui.big(v) for v in shown["short"]], textposition="outside", cliponaxis=False,
            customdata=np.stack([shown["recovery_index"], shown["arrivals"]], 1),
            hovertemplate="<b>%{y}</b><br>Còn thiếu: <b>%{x:,.0f} lượt</b><br>Lượt khách tháng này: %{customdata[1]:,.0f} lượt<br>Chỉ số phục hồi: <b>%{customdata[0]:,.1f}</b><extra></extra>"))
        ui.style_fig(fig, 400, legend=False, margin=dict(l=10, r=70, t=10, b=10))
        fig.update_yaxes(showgrid=False, title_text="Thị trường")
        fig.update_xaxes(showgrid=True, gridcolor=GRID, title_text="Số lượt khách còn thiếu so với cùng tháng 2019 (lượt)",
                         tickformat=",.0f", range=[0, float(shown["short"].max()) * 1.18])
        _set_title(fig, f"Mức thiếu hụt lượt khách ở các thị trường chưa phục hồi ({ui.mlabel(end)} so với 2019)")
        ui.chart_title("", "So sánh chiều dài các cột để tìm mức thiếu hụt lớn nhất.")
        ui.show(fig, key="qa1")
        top = ranked.iloc[0]
        raw = options(top["market"], ranked["market"].iloc[1:4].tolist(), f"q1|{end}")
        choices = [f"{chr(65+i)}. {dl.label(mk)}" for i, mk in enumerate(raw)]
        answer = next(x for x in choices if x.split(". ", 1)[1] == dl.label(top["market"]))
        key, token = identity(1, ui.mlabel(end))
        answer_widget(key, token, choices, answer,
                      f"Trong {ui.mlabel(end)}, {top['market']} thiếu {ui.n0(top['short'])} lượt so với cùng tháng năm 2019, lớn nhất trong các thị trường chưa phục hồi. Cột dài nhất biểu thị mức thiếu hụt cao nhất.")

    elif q.startswith("2"):
        S = D["season"]
        mk = st.selectbox("Chọn thị trường", S.index.tolist(), index=S.index.tolist().index("Nhật Bản") if "Nhật Bản" in S.index else 0)
        s = S.loc[mk]
        fig = go.Figure(go.Bar(x=s.index, y=s.values, marker_color=P["Blue Berry"], text=[ui.n0(v) for v in s.values], textposition="outside",
                               hovertemplate="Tháng: <b>%{x}</b><br>Chỉ số mùa vụ: <b>%{y:,.1f}</b> (trung bình T1–T11 = 100)<extra></extra>"))
        fig.add_hline(y=100, line_dash="dot", line_color=INK, annotation_text="Trung bình năm = 100", annotation_position="top left")
        ui.style_fig(fig, 400, legend=False)
        fig.update_xaxes(title_text="Tháng trong năm")
        fig.update_yaxes(title_text="Chỉ số mùa vụ (trung bình T1–T11 = 100)", tickformat=",.0f", range=[0, float(s.max()) * 1.16])
        _set_title(fig, f"Đặc điểm mùa vụ của du lịch quốc tế: thị trường {mk} (2023–2025)")
        ui.chart_title("", "So sánh chiều cao các cột với đường tham chiếu 100.")
        ui.show(fig, key="qa2")
        ui.source("Bảng dữ liệu tổng hợp (chỉ tính các thị trường có đủ số liệu giai đoạn 2023–2025).")
        month = s.idxmax()
        distractors = [x for x in s.sort_values(ascending=False).index if x != month][:3]
        raw = options(month, distractors, f"q2|{mk}|{s.to_dict()}")
        choices = [f"{chr(65+i)}. {x}" for i, x in enumerate(raw)]
        answer = next(x for x in choices if x.split(". ", 1)[1] == month)
        key, token = identity(2, f"{mk}|{s.to_dict()}")
        answer_widget(key, token, choices, answer,
                      f"Với thị trường {mk}, {month} có chỉ số mùa vụ cao nhất ({ui.n1(s.loc[month])}), cao hơn đường tham chiếu 100. Chỉ số được tính từ dữ liệu 2023–2025 theo công thức mùa vụ hiện có.",
                      "Tháng có chỉ số mùa vụ cao nhất")

    else:
        T = D["trends"]
        c1, c2 = st.columns(2)
        mk = c1.selectbox("Chọn thị trường", sorted(T["market"].unique()))
        lag = c2.slider("Độ trễ tìm kiếm đi trước (tháng)", 0, 3, 2)
        g = dl.lagged_trends(T, mk, lag)
        if len(g) < 2:
            st.info("Chưa đủ dữ liệu để so sánh tìm kiếm và lượt khách cho lựa chọn này.")
            return
        pr, sr = dl.simple_corr(g["interest_lag"], g["arrivals"])
        coef = np.polyfit(g["interest_lag"], g["arrivals"], 1)
        xs = np.linspace(g["interest_lag"].min(), g["interest_lag"].max(), 20)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=g["interest_lag"], y=g["arrivals"], mode="markers", marker=dict(size=9, color=colors[mk], line=dict(color=INK, width=.6)),
                                 customdata=g["date"].dt.strftime("%m/%Y"), hovertemplate="Thời gian: %{customdata}<br>Mức quan tâm tìm kiếm: %{x:,.0f}/100<br>Lượt khách: <b>%{y:,.0f} lượt</b><extra></extra>"))
        fig.add_trace(go.Scatter(x=xs, y=np.polyval(coef, xs), mode="lines", line=dict(color=INK, dash="dash", width=1.5), hoverinfo="skip"))
        ui.style_fig(fig, 410, legend=False)
        fig.update_xaxes(title_text=f"Mức quan tâm tìm kiếm đi trước {lag} tháng (thang chuẩn hóa 0–100)", tickformat=",.0f", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(title_text="Lượt khách quốc tế (lượt)", tickformat=",.0f")
        _set_title(fig, f"Mối liên hệ giữa tìm kiếm trực tuyến (đi trước {lag} tháng) và lượt khách từ {mk}")
        ui.chart_title("", "Quan sát hướng và độ phân tán của các điểm so với đường xu hướng.")
        ui.show(fig, key="qa3")
        if sr >= 0.5:
            answer_text, strength = "Mối liên hệ dương tương đối rõ (ρ ≥ 0,50)", "dương tương đối rõ"
        elif sr >= 0.2:
            answer_text, strength = "Mối liên hệ dương yếu đến vừa (0,20 ≤ ρ < 0,50)", "dương yếu đến vừa"
        elif sr > -0.2:
            answer_text, strength = "Chưa thấy mối liên hệ đơn điệu rõ (−0,20 ≤ ρ < 0,20)", "chưa rõ"
        else:
            answer_text, strength = "Mối liên hệ âm (ρ < −0,20)", "âm"
        interpretations = ["Mối liên hệ dương tương đối rõ (ρ ≥ 0,50)",
                           "Mối liên hệ dương yếu đến vừa (0,20 ≤ ρ < 0,50)",
                           "Chưa thấy mối liên hệ đơn điệu rõ (−0,20 ≤ ρ < 0,20)",
                           "Mối liên hệ âm (ρ < −0,20)"]
        raw = options(answer_text, [x for x in interpretations if x != answer_text], f"q3|{mk}|{lag}")
        choices = [f"{chr(65+i)}. {x}" for i, x in enumerate(raw)]
        answer = next(x for x in choices if x.split(". ", 1)[1] == answer_text)
        key, token = identity(3, f"{mk}|{lag}|{g['date'].min()}|{g['date'].max()}|{len(g)}")
        answer_widget(key, token, choices, answer,
                      f"Ở độ trễ {lag} tháng với {mk}, Spearman ρ = {hs._vn(f'{sr:.2f}')} và Pearson r = {hs._vn(f'{pr:.2f}')} trên {len(g)} tháng đủ dữ liệu. Kết quả thuộc nhóm {strength}. Đây là tương quan quan sát được, không chứng minh lượt tìm kiếm gây ra lượt khách.")

    current_keys = st.session_state.get("qa_current_keys", {})
    done = sum(current_keys.get(f"q{i}") in results for i in range(1, 4))
    st.progress(done / 3, text=f"Đã xác nhận {done}/3 câu trong phiên này")
    if results:
        with st.expander("📋 Kết quả đã ghi nhận trong phiên này"):
            frame = pd.DataFrame(results.values()).rename(columns={
                "question": "Câu hỏi", "selected": "Đã chọn", "answer": "Đáp án đúng", "correct": "Trả lời đúng",
                "seconds": "Thời gian (giây)", "attempts": "Số lần xác nhận",
            })
            ui.table(frame)
            st.download_button("⬇️ Tải kết quả phiên (CSV)", frame.to_csv(index=False).encode("utf-8-sig"),
                               "ket_qua_quiz.csv", "text/csv", key="qa_quiz_download")

# ============================================================ TRANG 3 · DIỄN BIẾN PHỤC HỒI
def page_race(D):
    m = D["master"]
    page_header(
        "📈",
        "Diễn biến phục hồi",
        "Theo dõi sự thay đổi chỉ số phục hồi theo thời gian và xác định thời điểm từng thị trường trở lại mức năm 2019.",
        "Chọn số lượng thị trường và mốc bắt đầu, sau đó bấm <b>▶ Chạy</b> hoặc kéo thanh trượt tháng để quan sát thứ tự thay đổi.",
    )
    c1, c2, c3 = st.columns(3)
    topn = c1.slider("Số thị trường muốn theo dõi", 6, 20, 12, help="Chọn nhóm thị trường có quy mô lượt khách năm 2019 lớn nhất.")
    start = c2.selectbox("Giai đoạn bắt đầu", ["2022-01", "2023-01", "2024-01"], index=0)
    speed = c3.select_slider("Tốc độ phát lại", ["Chậm", "Vừa", "Nhanh"], value="Vừa")
    dur = {"Chậm": 900, "Vừa": 500, "Nhanh": 250}[speed]

    size = m.groupby("market")["baseline_2019"].mean().sort_values(ascending=False)
    mk = size.index[:topn].tolist()
    piv = m.loc[m["market"].isin(mk)].pivot(index="date", columns="market", values="recovery_index").loc[start:]
    piv = piv.loc[piv.notna().sum(axis=1) >= max(4, int(0.6 * topn))]
    if piv.empty:
        st.warning("Không đủ dữ liệu để hiển thị diễn biến phục hồi với lựa chọn này.")
        return
    xmax = float(np.ceil(piv.max().max() * 1.15 / 50) * 50)

    def bar(date):
        s = piv.loc[date].dropna().sort_values()
        return go.Bar(x=s.values, y=[dl.label(k) for k in s.index], orientation="h",
                      marker_color=[ui.STATUS_COLOR["Chưa phục hồi"] if v < 95 else (ui.STATUS_COLOR["Vượt 2019"] if v > 105 else ui.STATUS_COLOR["Quanh mốc 2019"]) for v in s.values],
                      text=[ui.n0(v) for v in s.values], textposition="outside", cliponaxis=False,
                      hovertemplate="<b>%{y}</b><br>Chỉ số phục hồi: <b>%{x:,.1f}</b> (2019 = 100)<extra></extra>")

    def date_note(date):
        return [dict(x=0.97, y=0.08, xref="paper", yref="paper", text=f"<b>{ui.mlabel(date)}</b>", showarrow=False,
                     font=dict(size=46, color="rgba(43,43,35,.18)"), xanchor="right")]

    dates = list(piv.index)
    frames = [go.Frame(data=[bar(d)], name=d.strftime("%Y-%m"), layout=dict(annotations=date_note(d))) for d in dates]
    fig = go.Figure(data=[bar(dates[0])], frames=frames)
    ui.style_fig(fig, 580, legend=False, margin=dict(l=10, r=40, t=10, b=90))
    fig.update_layout(
        annotations=date_note(dates[0]),
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.13, xanchor="left", yanchor="top", buttons=[
            dict(label="▶ Chạy", method="animate", args=[None, dict(frame=dict(duration=dur, redraw=True), transition=dict(duration=0),
                                                                    fromcurrent=True, mode="immediate")]),
            dict(label="⏸ Dừng", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])])],
        sliders=[dict(active=0, x=0.18, y=-0.1, len=0.8, currentvalue=dict(prefix="Tháng: ", font=dict(size=13)), pad=dict(t=0, b=10),
                      steps=[dict(label=ui.mlabel(d), method="animate", args=[[d.strftime("%Y-%m")], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))]) for d in dates])])
    fig.update_yaxes(title_text="Thị trường", categoryorder="total ascending", showgrid=False)
    fig.update_xaxes(range=[0, xmax], title_text="Chỉ số phục hồi (2019 = 100)", tickformat=",.0f", showgrid=True, gridcolor=GRID)
    fig.add_shape(type="line", x0=100, x1=100, y0=0, y1=1, yref="paper", line=dict(color=INK, dash="dot", width=1.5))
    _set_title(fig, f"Diễn biến phục hồi của các thị trường theo từng tháng (từ {start})")
    ui.chart_title("", "Cam: dưới 95 · Xám: quanh mốc 2019 (95–105) · Xanh: trên 105. Đường chấm dọc đánh dấu mốc năm 2019 = 100.")
    ui.show(fig, key="race")
    ui.source("Bảng dữ liệu tổng hợp VNAT/NSO. Số liệu theo từng thị trường được công bố trở lại từ năm 2022.")

    # Thời điểm lần đầu đạt mốc 2019
    first = {}
    for k in piv.columns:
        s = piv[k].dropna()
        hit = s[s >= 100]
        first[k] = hit.index[0] if len(hit) else pd.NaT
    fd = pd.Series(first).sort_values()
    crossed, never = fd.dropna(), fd[fd.isna()].index.tolist()
    fig2 = go.Figure(go.Scatter(
        x=crossed.values, y=[dl.label(k) for k in crossed.index], mode="markers+text",
        text=[f" {ui.mlabel(d)}" for d in crossed.values], textposition="middle right", textfont=dict(size=11, color=INK),
        marker=dict(size=12, color=P["Pea Flower"], line=dict(color=INK, width=.6)),
        hovertemplate="<b>%{y}</b><br>Lần đầu đạt chỉ số ≥ 100: <b>%{x|%m/%Y}</b><extra></extra>"))
    ui.style_fig(fig2, 90 + 28 * max(len(crossed), 3), legend=False, margin=dict(l=10, r=60, t=10, b=30))
    fig2.update_yaxes(title_text="Thị trường", autorange="reversed", showgrid=True, gridcolor=GRID)
    if len(crossed):
        fig2.update_xaxes(title_text="Thời gian đạt mốc 2019 (tháng/năm)", tickformat="%m/%Y", showgrid=True, gridcolor=GRID,
                          range=[pd.Timestamp(crossed.min()) - pd.DateOffset(months=1), pd.Timestamp(crossed.max()) + pd.DateOffset(months=4)])
    else:
        fig2.update_xaxes(title_text="Thời gian đạt mốc 2019 (tháng/năm)", tickformat="%m/%Y", showgrid=True, gridcolor=GRID)
    _set_title(fig2, f"Thời điểm từng thị trường lần đầu đạt mốc năm 2019 (từ {ui.mlabel(piv.index[0])})")
    ui.chart_title("", f"Tháng đầu tiên ghi nhận chỉ số phục hồi ≥ 100 kể từ {ui.mlabel(piv.index[0])}"
                   + (f" · Chưa đạt mốc 100: {', '.join(never)}" if never else ""))
    ui.show(fig2, key="race2")
    st.caption("Lưu ý: Việc lần đầu chạm mốc 100 không đồng nghĩa thị trường đã duy trì ổn định mức phục hồi đó trong các tháng tiếp theo.")


# ============================================================ TRANG 4 · MÙA VỤ VÀ THỜI TIẾT
def page_season(D):
    m, w = D["master"], D["weather"]
    page_header(
        "🌦️",
        "Mùa vụ và điều kiện thời tiết",
        "Khám phá những tháng có lượng khách cao điểm và đặc điểm mưa, nắng tại Đà Nẵng và Nha Trang.",
        "Xem biến động phục hồi theo từng tháng ở tab đầu tiên, sau đó đối chiếu đặc điểm mưa nắng tại hai điểm đến biển ở tab thứ hai.",
    )
    t1, t2 = st.tabs(["📅 Mùa khách theo tháng", "☀️ Thời tiết tại Đà Nẵng và Nha Trang"])
    with t1:
        years = sorted(m.loc[m["recovery_index"].notna(), "year"].unique(), reverse=True)
        y = st.select_slider("Chọn năm phân tích", options=sorted(years), value=2025 if 2025 in years else years[0])
        d = m.loc[(m["year"] == y) & m["recovery_index"].notna()]
        piv = d.pivot(index="market", columns="month", values="recovery_index").reindex(columns=range(1, 13))
        piv = piv.loc[piv.notna().sum(axis=1) >= 6]
        order = m.loc[m["year"] == y].groupby("market")["arrivals"].sum().reindex(piv.index).sort_values(ascending=True).index
        piv = piv.loc[order]
        z = piv.clip(40, 160)
        fig = go.Figure(go.Heatmap(
            z=z.values, x=dl.MONTH_LABEL, y=[dl.label(k) for k in piv.index], colorscale=DIV_SCALE, zmin=40, zmax=160,
            customdata=piv.values, text=piv.round(0).values, texttemplate="%{text:.0f}", textfont=dict(size=10),
            hovertemplate="<b>%{y}</b> · %{x}/" + str(y) + "<br>Chỉ số phục hồi: <b>%{customdata:,.1f}</b> (2019 = 100)<extra></extra>", hoverongaps=False,
            colorbar=dict(title="Chỉ số<br>(2019=100)", tickvals=[40, 70, 100, 130, 160], ticktext=["≤40", "70", "100", "130", "≥160"], len=.8)))
        ui.style_fig(fig, 110 + 24 * len(piv), legend=False, margin=dict(l=10, r=10, t=10, b=10))
        fig.update_yaxes(showgrid=False, title_text="Thị trường", tickfont=dict(size=11))
        fig.update_xaxes(side="top", title_text="Tháng trong năm")
        _set_title(fig, f"Mức phục hồi theo từng tháng so với năm 2019 (Năm {y})", top_margin=88)
        ui.chart_title("", "Mỗi ô là chỉ số phục hồi của một thị trường trong một tháng (= 100 là bằng cùng tháng 2019). "
                       "Cam: dưới 100 · Xám: quanh 100 · Xanh: vượt 100 · Ô trắng: thiếu số liệu.")
        ui.show(fig, key="se_heat")
        ui.source("Bảng dữ liệu tổng hợp VNAT/NSO. Các hàng sắp xếp theo tổng lượt khách trong năm; thang màu giới hạn ở 40–160 để tránh ngoại lệ làm mờ xu hướng chung (số trong ô là giá trị thực tế).")
    with t2:
        wd = w.loc[w["year"].between(2017, 2025)]
        rain = wd.groupby(["destination", "month"])["precipitation_sum"].median().unstack(0)
        sun = wd.groupby(["destination", "month"])["sunshine_hours"].median().unstack(0)
        dcol = {"Đà Nẵng": P["Pea Flower"], "Nha Trang": P["Florida Oranges"]}
        fig = go.Figure()
        for dest in rain.columns:
            fig.add_trace(go.Bar(
                x=dl.MONTH_LABEL, y=rain[dest].values, name=dest, marker_color=dcol[dest],
                text=[ui.n0(v) for v in rain[dest].values], textposition="outside", textfont=dict(size=10), cliponaxis=False,
                hovertemplate=f"<b>{dest}</b> · %{{x}}<br>Lượng mưa trung vị: <b>%{{y:,.1f}} mm</b><extra></extra>"))
        fig.update_layout(barmode="group")
        ui.style_fig(fig, 390)
        fig.update_xaxes(title_text="Tháng trong năm")
        fig.update_yaxes(title_text="Lượng mưa trung vị (mm)", tickformat=",.0f", range=[0, float(rain.max().max()) * 1.18])
        wet = {c: ", ".join(f"T{k}" for k in rain[c].sort_values(ascending=False).head(3).index.sort_values()) for c in rain.columns}
        _set_title(fig, "Phân bố lượng mưa trung vị theo tháng tại Đà Nẵng và Nha Trang (2017–2025)")
        ui.chart_title("", f"Cao điểm mưa: Đà Nẵng ({wet.get('Đà Nẵng', '–')}), Nha Trang ({wet.get('Nha Trang', '–')})")
        ui.show(fig, key="se_rain")
        fig = go.Figure()
        for dest in sun.columns:
            fig.add_trace(go.Scatter(x=dl.MONTH_LABEL, y=sun[dest].values, mode="lines+markers", name=dest,
                                     line=dict(color=dcol[dest], width=3),
                                     hovertemplate=f"<b>{dest}</b> · %{{x}}<br>Số giờ nắng trung vị: <b>%{{y:,.1f}} giờ</b><extra></extra>"))
        ui.style_fig(fig, 330)
        fig.update_layout(hovermode="x unified")
        fig.update_xaxes(title_text="Tháng trong năm")
        fig.update_yaxes(title_text="Số giờ nắng trung vị (giờ)", tickformat=",.0f")
        _set_title(fig, "Xu hướng thời tiết giai đoạn 2017–2025: số giờ nắng trung vị theo tháng")
        ui.chart_title("", "Số giờ nắng trung vị mỗi tháng tại Đà Nẵng và Nha Trang, giai đoạn 2017–2025")
        ui.show(fig, key="se_sun")
        ui.source("Open-Meteo Historical Weather.")
        ui.card("<p><b>Lưu ý về phạm vi dữ liệu:</b> Lượt khách quốc tế trong bảng dữ liệu là số liệu <b>toàn quốc</b>, trong khi dữ liệu thời tiết chỉ đo tại Đà Nẵng và Nha Trang. "
                "Các biểu đồ trên giúp tham khảo điều kiện mưa nắng tại hai điểm đến biển để chọn thời điểm quảng bá phù hợp, không chứng minh thời tiết tác động trực tiếp đến tổng lượng khách quốc tế.</p>")


# ============================================================ TRANG 5 · NHÓM THỊ TRƯỜNG
def page_segments(D):
    seg, prof, evr, sil = D["seg"], D["prof"], D["evr"], D["sil"]
    page_header(
        "🧭",
        "Các nhóm thị trường khách quốc tế",
        f"Phân loại {len(seg)} thị trường có đủ dữ liệu dựa trên tốc độ phục hồi, đặc điểm mùa vụ, khoảng cách địa lý và tăng trưởng. Kết quả giúp nhận diện những nhóm thị trường có đặc điểm tương đồng.",
        "Trục ngang thể hiện khoảng cách địa lý đến Việt Nam, trục dọc thể hiện biên độ dao động mùa vụ. Di chuột vào từng điểm để xem đầy đủ các chỉ số của thị trường.",
    )
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure()
        for k, g in seg.groupby("cluster"):
            fig.add_trace(go.Scatter(
                x=g["distance_km"], y=g["seasonal_amplitude"], mode="markers+text", name=CLUSTER_NAME.get(k, f"Nhóm {k}"),
                text=[x for x in g.index], textposition="top center", textfont=dict(size=10),
                marker=dict(size=np.sqrt(g["arrivals_latest_ytd"]) / 18 + 8, color=ui.CLUSTER_COLOR[k], opacity=.85, line=dict(color=INK, width=.6)),
                customdata=np.stack([g["recovery_speed"], g["growth_pct"], g["arrivals_latest_ytd"]], 1),
                hovertemplate="<b>%{text}</b><br>Khoảng cách: %{x:,.0f} km<br>Biên độ mùa vụ: %{y:,.1f} điểm chỉ số<br>Tốc độ phục hồi: %{customdata[0]:,.1f} điểm/tháng"
                              "<br>Tăng trưởng cùng kỳ: %{customdata[1]:+,.1f}%<br>Lượt khách từ đầu năm: %{customdata[2]:,.0f} lượt<extra></extra>"))
        ui.style_fig(fig, 540)
        fig.update_xaxes(title_text="Khoảng cách địa lý đến Việt Nam (km)", tickformat=",.0f", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(title_text="Biên độ mùa vụ (điểm chỉ số)", tickformat=",.0f")
        _set_title(fig, "Phân nhóm thị trường theo khoảng cách địa lý và biên độ mùa vụ")
        ui.chart_title("", "Mỗi điểm đại diện cho một thị trường. Kích thước thể hiện lượng khách lũy kế từ đầu năm, màu sắc thể hiện nhóm phân khúc (K-means, k = 2).")
        ui.show(fig, key="sg_scatter")
        ui.source("Bảng dữ liệu tổng hợp VNAT/NSO; đặc trưng thị trường tính từ chuỗi phục hồi và mùa vụ.")
    with c2:
        for k, r in prof.iterrows():
            top = ", ".join(r["markets"][:6]) + ("…" if len(r["markets"]) > 6 else "")
            ui.card(f"<h4><span class='tag' style='background:{ui.CLUSTER_COLOR[k]};color:#fff'>Nhóm {k}</span> {CLUSTER_NAME.get(k, '')}</h4>"
                    f"<p><b>{int(r['n'])} thị trường:</b> {top}</p>"
                    f"<p>Khoảng cách trung vị {ui.n0(r['distance_km'])} km · biên độ mùa vụ {ui.n0(r['seasonal_amplitude'])} · "
                    f"tăng trưởng trung vị {ui.pct(r['growth_pct'])} · tháng cao điểm phổ biến: T{int(r['peak_month_mode'])}</p>"
                    f"<p><b>Hướng theo dõi:</b> {CLUSTER_ACTION.get(k, '')}</p>", "sea" if k == 1 else "sun")
            st.write("")
    ui.card(f"<h4>⚠️ Lưu ý khi đọc kết quả phân nhóm</h4><p>Hai nhóm tách biệt chủ yếu theo <b>khoảng cách địa lý</b> và mức độ mùa vụ, không tách biệt rõ theo tốc độ phục hồi (hai nhóm có tốc độ phục hồi trung vị gần nhau). "
            f"Chỉ số Silhouette = {hs._vn(f'{sil:.2f}')} (mức thấp) cho thấy ranh giới giữa hai cụm còn yếu — nên xem đây là <b>gợi ý tham khảo</b> chứ không phải phân loại cứng. "
            f"Kết quả phân nhóm cũng không giải thích nguyên nhân thị trường phục hồi nhanh hay chậm. {len(D['excluded'])} thị trường chưa đủ dữ liệu không nằm trong phân tích này "
            f"({', '.join(D['excluded']['market'])}).</p>")
    with st.expander("📄 Bảng đặc trưng từng thị trường"):
        t = seg.reset_index().rename(columns={"market": "Thị trường", "recovery_speed": "Tốc độ phục hồi", "seasonal_amplitude": "Biên độ mùa vụ",
                                              "peak_month": "Tháng đỉnh", "distance_km": "Khoảng cách (km)", "growth_pct": "Tăng trưởng (%)",
                                              "arrivals_latest_ytd": "Lượt khách YTD", "cluster": "Nhóm"})
        ui.table(t[["Thị trường", "Nhóm", "Tốc độ phục hồi", "Biên độ mùa vụ", "Tháng đỉnh", "Khoảng cách (km)", "Tăng trưởng (%)", "Lượt khách YTD"]].round(2))


# ============================================================ ĐIỀU HƯỚNG
PAGES = {
    "Tổng quan": page_story,
    "Khám phá dữ liệu": page_explorer,
    "Diễn biến phục hồi": page_race,
    "Mùa vụ và thời tiết": page_season,
    "Nhóm thị trường": page_segments,
    "Bản đồ thị trường": m78.page_beyond_flat,
    "So sánh đa chiều": m78.page_many_dimensions,
    "Đánh giá và cải tiến": None,
}

with st.sidebar:
    st.markdown("<div class='brand'>🌴 Coming Back<small>Phân tích du lịch quốc tế Việt Nam</small></div>", unsafe_allow_html=True)
    st.write("")
    st.caption("Hành trình đọc dữ liệu")
    choice = st.radio("Điều hướng", list(PAGES), label_visibility="collapsed")
    st.write("")
    st.caption("Bước 1: Tổng quan → Bước 2: Khám phá → Bước 3: Diễn biến & Mùa vụ → Bước 4: Nhóm & Bản đồ → Bước 5: Đánh giá")
    st.caption("Nhóm 04 · Trực quan hóa dữ liệu")

D = get_data()
with st.sidebar:
    st.caption(f"Dữ liệu đến {ui.mlabel(dl.latest_date(D['master']))}")

if PAGES[choice] is None:
    m10.page(D)
else:
    PAGES[choice](D)
