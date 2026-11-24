"""
pages_m7_m8.py - Hai trang mới cho app:
  * page_many_dimensions(D)  -> M7 · Many Dimensions (heatmap, treemap, parallel coordinates)
  * page_beyond_flat(D)      -> M8 · Beyond the Flat Screen (quả địa cầu 3D vs bản đồ 2D + kết quả thử nghiệm)

Dùng lại dữ liệu D đã nạp trong app.py (D["master"], D["seg"], D["feats"], D["colors"]) -
KHÔNG cần thêm file dữ liệu nào, trừ file tuỳ chọn data/M8_Experiment_Results.csv (xem README).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data_layer as dl
import house_style as hs
import ui
from ui import GRID, INK, MUTED, P

DATA = Path(__file__).parent / "data"
DIV_SCALE = [[i / (len(hs.DIV_COLORS) - 1), c] for i, c in enumerate(hs.DIV_COLORS)]  # 0 -> 100 -> 200, 100 ở giữa
REGION_ORDER = ["Châu Á", "Châu Âu", "Châu Mỹ", "Châu Úc"]
REGION_COLOR = dict(zip(REGION_ORDER, hs.CAT_COLORS))  # đúng như notebook M7/M8
CLUSTER_NAME = {1: "Thị trường xa - Mùa vụ rõ hơn", 2: "Thị trường gần - Mùa vụ nhẹ hơn"}
VIETNAM = (21.0, 105.8)  # Hà Nội, điểm đại diện cho Việt Nam (như M8)


def _header(icon, title, text):
    st.markdown(f"<h2 style='margin:.2rem 0 .1rem;font-weight:800'>{icon} {title}</h2>"
                f"<p style='color:{MUTED};margin:0 0 .8rem;font-size:1rem'>{text}</p>", unsafe_allow_html=True)


def _region_color(r: str) -> str:
    return REGION_COLOR.get(r, hs.OTHER_COLOR)


# ============================================================ M7
def page_many_dimensions(D):
    _header("🧩", "Đa chiều", "Nhìn cùng lúc nhiều chiều: thị trường × thời gian × quy mô × đặc điểm — bằng bản đồ nhiệt, treemap và đường song song.")
    t1, t2, t3, t4 = st.tabs(["🔥 Bản đồ nhiệt", "🟦 Treemap", "📈 Đường song song", "📝 Quyết định thiết kế"])
    with t1:
        _heatmap(D)
    with t2:
        _treemap(D)
    with t3:
        _parallel(D)
    with t4:
        _m7_design()


def _heatmap(D):
    m = D["master"]
    end = dl.latest_date(m)
    c1, c2 = st.columns([1.3, 1])
    order = c1.radio("Sắp xếp hàng", ["Tên thị trường (A–Z)", "Tổng lượt khách", "Chỉ số mới nhất"], horizontal=True, key="m7_order")
    years = sorted(m["year"].unique())
    y0 = c2.select_slider("Từ năm", options=years, value=years[0], key="m7_from")

    d = m.loc[m["date"] >= pd.Timestamp(f"{y0}-01-01")]
    piv = d.pivot(index="market", columns="date", values="recovery_index")
    months = pd.date_range(piv.columns.min(), piv.columns.max(), freq="MS")
    piv = piv.reindex(columns=months).dropna(how="all")  # thị trường không có chỉ số nào thì ẩn
    if order.startswith("Tổng"):
        tot = d.groupby("market")["arrivals"].sum().reindex(piv.index)
        piv = piv.loc[tot.sort_values(ascending=True).index]
    elif order.startswith("Chỉ số"):
        last = piv.iloc[:, -1]
        piv = piv.loc[last.sort_values(ascending=True, na_position="first").index]
    else:
        piv = piv.sort_index(ascending=False)  # A–Z từ trên xuống (trục y vẽ từ dưới lên)

    last_col = piv.iloc[:, -1].dropna()
    n_above = int((last_col > 100).sum())
    fig = go.Figure(go.Heatmap(
        z=piv.clip(0, 200).values, x=piv.columns, y=[dl.label(k) for k in piv.index],
        colorscale=DIV_SCALE, zmin=0, zmax=200, customdata=piv.values, hoverongaps=False, xgap=0, ygap=1,
        hovertemplate="<b>%{y}</b> · %{x|%m/%Y}<br>Chỉ số: %{customdata:.0f}<extra></extra>",
        colorbar=dict(title="Chỉ số", tickvals=[0, 50, 100, 150, 200], ticktext=["0", "50", "100", "150", "≥200"], len=.85)))
    ui.style_fig(fig, 120 + 22 * len(piv), legend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_yaxes(showgrid=False, tickfont=dict(size=11))
    fig.update_xaxes(tickformat="%Y", dtick="M12", showgrid=False)
    ui.chart_title(f"{n_above}/{len(last_col)} thị trường có số liệu vượt mức 2019 vào {ui.mlabel(end)}",
                   "Mỗi ô là chỉ số phục hồi của một thị trường trong một tháng (cùng tháng 2019 = 100). Cam = dưới 2019 · Xám = bằng 2019 · Xanh = vượt 2019 · Ô trắng = thiếu chỉ số")
    ui.show(fig, key="m7_heat")
    ui.source("Master table M2. Màu cắt ở 200 (ô vượt 200 dùng chung màu cuối thang); số thật hiện khi di chuột.")


def _treemap(D):
    m = D["master"]
    end = dl.latest_date(m)
    c1, c2 = st.columns([1, 1.4])
    years = sorted(m["year"].unique(), reverse=True)
    year = c1.selectbox("Năm", years, index=0, key="m7_tree_year",
                        help=f"Cộng dồn tháng 1–{end.month} của năm được chọn, để các năm so sánh công bằng với năm mới nhất.")
    mode = c2.radio("Tô màu theo", ["Khu vực", "Chỉ số phục hồi"], horizontal=True, key="m7_tree_mode")

    sub = m.loc[(m["year"] == year) & m["month"].le(end.month) & m["arrivals"].notna()].copy()
    both = sub.loc[sub["baseline_2019"].gt(0)]
    agg = sub.groupby(["continent", "market"])["arrivals"].sum().rename("arr").to_frame()
    agg["a_b"] = both.groupby(["continent", "market"])["arrivals"].sum()
    agg["base"] = both.groupby(["continent", "market"])["baseline_2019"].sum()
    agg = agg.reset_index()
    agg["idx"] = 100 * agg["a_b"] / agg["base"]
    if mode == "Chỉ số phục hồi":
        dropped = agg.loc[agg["idx"].isna(), "market"].tolist()
        agg = agg.dropna(subset=["idx"])
    else:
        dropped = []
    if agg.empty:
        st.info("Không có dữ liệu cho lựa chọn này.")
        return

    reg = agg.groupby("continent").agg(arr=("arr", "sum"), a_b=("a_b", "sum"), base=("base", "sum")).reset_index()
    reg["idx"] = 100 * reg["a_b"] / reg["base"]
    root_idx = 100 * agg["a_b"].sum() / agg["base"].sum() if agg["base"].sum() else np.nan

    ids, labels, parents, values, cols, idxs = ["root"], ["Tất cả thị trường"], [""], [agg["arr"].sum()], [GRID], [root_idx]
    for r in reg.itertuples():
        ids.append(r.continent); labels.append(r.continent); parents.append("root"); values.append(r.arr)
        cols.append(_region_color(r.continent)); idxs.append(r.idx)
    for r in agg.itertuples():
        ids.append(f"{r.continent}|{r.market}"); labels.append(dl.label(r.market)); parents.append(r.continent); values.append(r.arr)
        cols.append(_region_color(r.continent)); idxs.append(r.idx)

    if mode == "Chỉ số phục hồi":
        marker = dict(colors=[(0 if pd.isna(v) else v) for v in idxs], colorscale=DIV_SCALE, cmin=0, cmax=200,
                      colorbar=dict(title="Chỉ số", tickvals=[0, 50, 100, 150, 200], len=.8), line=dict(width=1.5, color="white"))
    else:
        marker = dict(colors=cols, line=dict(width=1.5, color="white"))
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total", marker=marker,
        customdata=np.array(idxs, dtype=float).reshape(-1, 1),
        texttemplate="<b>%{label}</b><br>%{value:,.0f}", textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} lượt khách<br>Chỉ số phục hồi: %{customdata[0]:.0f}<extra></extra>"))
    ui.style_fig(fig, 560, legend=False, margin=dict(l=5, r=5, t=5, b=5))
    top = reg.sort_values("arr", ascending=False).iloc[0]
    share = top["arr"] / reg["arr"].sum()
    ui.chart_title(f"{top['continent']} chiếm {ui.n0(100 * share)}% lượt khách trong {len(agg)} thị trường, T1–T{end.month}/{year}",
                   "Diện tích ô theo số lượt khách · lồng theo khu vực → thị trường"
                   + (" · màu = chỉ số phục hồi cùng kỳ 2019" if mode == "Chỉ số phục hồi" else " · màu = khu vực"))
    ui.show(fig, key="m7_tree")
    ui.source("Master table M2, cộng dồn các tháng có số liệu."
              + (f" Ẩn vì chưa có mốc 2019: {', '.join(dropped)}." if dropped else ""))


def _zmatrix(feats: pd.DataFrame) -> pd.DataFrame:
    """z-score đúng như M6: 4 đặc trưng tuyến tính chuẩn hoá; sin/cos tháng đỉnh được căn giữa rồi chia cùng một hệ số."""
    from sklearn.preprocessing import StandardScaler
    z = pd.DataFrame(StandardScaler().fit_transform(feats[dl.LINEAR]), index=feats.index, columns=dl.LINEAR)
    cyc = feats[["peak_sin", "peak_cos"]].to_numpy()
    cyc = cyc - cyc.mean(axis=0)
    scale = np.sqrt(np.mean(np.square(cyc).sum(axis=1)))
    z[["peak_sin", "peak_cos"]] = cyc / scale if scale > 1e-12 else 0
    return z


def _parallel(D):
    seg, feats = D["seg"], D["feats"]
    z = _zmatrix(feats).loc[seg.index]
    axes = {"recovery_speed": "Tốc độ<br>phục hồi", "growth_pct": "Tăng<br>trưởng", "seasonal_amplitude": "Biên độ<br>mùa vụ",
            "peak_sin": "Tháng đỉnh<br>(sin)", "peak_cos": "Tháng đỉnh<br>(cos)", "distance_km": "Khoảng<br>cách"}
    xs = list(axes.values())
    pick = st.multiselect("Làm nổi bật thị trường (tuỳ chọn)", sorted(seg.index), key="m7_par_pick",
                          help="Các thị trường còn lại mờ đi để dễ lần theo một đường.")
    fig = go.Figure()
    shown = set()
    for k, name in seg["cluster"].items():
        c = ui.CLUSTER_COLOR.get(name, hs.OTHER_COLOR)
        dim = bool(pick) and k not in pick
        fig.add_trace(go.Scatter(
            x=xs, y=z.loc[k, list(axes)].to_numpy(), mode="lines+markers", name=f"{CLUSTER_NAME.get(name, f'Cụm {name}')} ({int((seg['cluster'] == name).sum())})",
            legendgroup=str(name), showlegend=name not in shown, line=dict(color=c, width=3 if (pick and not dim) else 1.6),
            marker=dict(size=5), opacity=0.12 if dim else (1 if pick else 0.55),
            hovertemplate=f"<b>{k}</b><br>%{{x}}: %{{y:.2f}} (z)<extra></extra>"))
        shown.add(name)
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED, annotation_text="Trung bình mẫu", annotation_position="bottom right")
    ui.style_fig(fig, 480)
    fig.update_yaxes(title="Giá trị chuẩn hoá (z-score)", showgrid=True, gridcolor=GRID)
    fig.update_xaxes(showgrid=True, gridcolor=GRID)
    ui.chart_title("Nhóm thị trường xa có biên độ mùa vụ trung bình cao hơn",
                   f"Mỗi đường là một thị trường ({len(seg)} thị trường) · màu = cụm M6 · đường đứt = trung bình mẫu")
    ui.show(fig, key="m7_par")
    ui.source("Master table M2; đặc trưng và z-score tái lập theo M6.")


def _m7_design():
    ui.card("<h4>7.1 Heatmap</h4><p>Các hàng mặc định xếp theo tên thị trường để dễ tra cứu (có thể đổi sang tổng lượt khách hoặc chỉ số mới nhất), "
            "các cột đi theo thứ tự tháng. Mỗi ô là chỉ số lượt khách so với cùng tháng năm 2019. Thang màu phân kỳ đặt mốc 100 ở giữa. "
            "Ô trắng là tháng thiếu chỉ số; chỉ số trên 200 dùng chung màu ở đầu thang. Thị trường không có chỉ số nào trong kỳ bị ẩn.</p>"
            "<h4>7.2 Treemap</h4><p>Ô lồng theo khu vực → thị trường; diện tích tỷ lệ với tổng lượt khách trong các tháng đã chọn. "
            "Màu mặc định phân biệt khu vực; có thể đổi sang chỉ số phục hồi để thêm một chiều thứ ba.</p>"
            "<h4>7.3 Parallel coordinates</h4><p>Trục xếp từ tốc độ phục hồi và tăng trưởng sang đặc điểm mùa vụ rồi khoảng cách; "
            "hai trục sin và cos đặt cạnh nhau vì cùng biểu diễn tháng cao điểm theo chu kỳ. Các trục dùng z-score của M6 để so sánh trên cùng thang đo. "
            "Mỗi đường là một thị trường, màu đường là cụm M6, đường đứt tại 0 là trung bình mẫu.</p>")


# ============================================================ M8
def _flow_table(m: pd.DataFrame, date) -> tuple[pd.DataFrame, list[str]]:
    f = m.loc[(m["date"] == pd.Timestamp(date)) & m["arrivals"].notna() & m["baseline_2019"].gt(0),
              ["market", "continent", "arrivals", "baseline_2019"]].copy()
    missing = sorted(set(f["market"]) - set(dl.LATLON))
    f = f.loc[f["market"].isin(dl.LATLON)].copy()
    f["lat"] = f["market"].map(lambda k: dl.LATLON[k][0])
    f["lon"] = f["market"].map(lambda k: dl.LATLON[k][1])
    f["market_recovery"] = 100 * f["arrivals"] / f["baseline_2019"]
    reg = f.groupby("continent")[["arrivals", "baseline_2019"]].sum()
    reg["recovery_index"] = 100 * reg["arrivals"] / reg["baseline_2019"]
    f["region_recovery"] = f["continent"].map(reg["recovery_index"])
    return f, missing


def _draw_map(f: pd.DataFrame, projection: str, view_name: str, date, lon_rot: int, height: int = 560):
    size_ref = 2 * f["arrivals"].max() / 24 ** 2
    fig = go.Figure()
    for r in f.itertuples(index=False):  # đường nối từ thị trường nguồn đến Việt Nam
        fig.add_trace(go.Scattergeo(lat=[r.lat, VIETNAM[0]], lon=[r.lon, VIETNAM[1]], mode="lines",
                                    line=dict(color=_region_color(r.continent), width=1.2), opacity=0.45,
                                    hoverinfo="skip", legendgroup=r.continent, showlegend=False))
    for region, g in f.groupby("continent"):  # diện tích điểm = lượt khách, màu = khu vực
        fig.add_trace(go.Scattergeo(
            lat=g["lat"], lon=g["lon"], text=[dl.label(k) for k in g["market"]],
            customdata=g[["continent", "arrivals", "market_recovery", "region_recovery"]].to_numpy(),
            mode="markers", name=region, legendgroup=region,
            marker=dict(color=_region_color(region), size=g["arrivals"], sizemode="area", sizeref=size_ref, sizemin=5,
                        line=dict(color="white", width=0.6)),
            hovertemplate=("<b>%{text}</b> · %{customdata[0]}<br>Lượt khách: %{customdata[1]:,.0f}<br>"
                           "Chỉ số phục hồi thị trường: %{customdata[2]:.1f}<br>Chỉ số phục hồi khu vực: %{customdata[3]:.1f}<extra></extra>")))
    fig.add_trace(go.Scattergeo(lat=[VIETNAM[0]], lon=[VIETNAM[1]], mode="markers+text", marker=dict(size=11, color="#242424", symbol="star"),
                                text=["Việt Nam"], textposition="bottom right", showlegend=False, hoverinfo="skip"))
    fig.update_geos(projection_type=projection, showland=True, landcolor="#DCE9D5", showocean=True, oceancolor="#D8EBF8",
                    coastlinecolor="#7B9BA9", showcountries=False, showframe=False)
    if projection == "orthographic":
        fig.update_geos(projection_rotation=dict(lon=lon_rot, lat=20))
    fig.update_layout(
        height=height, margin=dict(t=10, l=5, r=5, b=45), paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Be Vietnam Pro, Segoe UI, Roboto, Arial, sans-serif", color=INK), separators=",.",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.02))
    return fig


def _load_m8_log() -> pd.DataFrame | None:
    """File tuỳ chọn: data/M8_Experiment_Results.csv với cột person, order, version, question, result, seconds."""
    p = DATA / "M8_Experiment_Results.csv"
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p, encoding="utf-8-sig")
        need = {"person", "version", "question", "result", "seconds"}
        if not need <= set(df.columns):
            return None
        df["seconds"] = pd.to_numeric(df["seconds"].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        df["correct"] = df["result"].astype(str).str.strip().map({"Đúng": 1, "Sai": 0})
        df["version"] = df["version"].astype(str).str.strip()
        return df.dropna(subset=["seconds", "correct"])
    except Exception:
        return None


def page_beyond_flat(D):
    m = D["master"]
    _header("🌍", "Góc nhìn 3D & 2D", "Cùng một dữ liệu luồng khách, hai cách nhìn: quả địa cầu 3D và bản đồ phẳng 2D — và nhóm đã thử xem cách nào thật sự nhanh hơn.")
    t1, t2, t3 = st.tabs(["🗺️ Địa cầu 3D & bản đồ 2D", "📊 Thanh xếp hạng (đối chứng)", "🧪 Kết quả thử nghiệm 2D vs 3D"])

    dates = [pd.Timestamp(x) for x in sorted(m["date"].unique())]
    avail = [d for d in dates if (m.loc[m["date"] == d, "baseline_2019"].gt(0) & m.loc[m["date"] == d, "arrivals"].notna()).sum() >= 10]
    with t1:
        c1, c2, c3 = st.columns([1.1, 1.3, 1])
        view = c1.radio("Chế độ xem", ["Địa cầu 3D", "Bản đồ 2D", "Cạnh nhau"], horizontal=True, key="m8_view")
        date = c2.select_slider("Tháng", options=avail, value=avail[-1], format_func=ui.mlabel, key="m8_month")
        rot = c3.slider("Xoay địa cầu (kinh độ)", -180, 180, 85, key="m8_rot", help="Chỉ áp dụng cho địa cầu 3D.")
        f, missing = _flow_table(m, date)
        reg = f.groupby("continent")[["arrivals", "baseline_2019"]].sum()
        reg["idx"] = 100 * reg["arrivals"] / reg["baseline_2019"]
        reg = reg.sort_values("idx", ascending=False)
        cols = st.columns(len(reg))
        for col, (name, r) in zip(cols, reg.iterrows()):
            ui.kpi(col, name, ui.n0(r["idx"]), f"{ui.big(r['arrivals'])} lượt · chỉ số phục hồi khu vực")
        st.write("")
        title = f"Luồng khách đến Việt Nam {ui.mlabel(date)}: {reg.index[0]} có chỉ số phục hồi cao nhất ({ui.n0(reg['idx'].iloc[0])})"
        ui.chart_title(title, f"Kích thước điểm = lượt khách · màu = khu vực · chỉ số phục hồi: cùng tháng 2019 = 100 · {len(f)} thị trường có mốc so sánh")
        if view == "Cạnh nhau":
            a, b = st.columns(2)
            with a:
                st.caption("Quả địa cầu 3D")
                ui.show(_draw_map(f, "orthographic", "Quả địa cầu 3D", date, rot, 480), key="m8_globe_c")
            with b:
                st.caption("Bản đồ 2D")
                ui.show(_draw_map(f, "natural earth", "Bản đồ 2D", date, rot, 480), key="m8_flat_c")
        elif view == "Địa cầu 3D":
            ui.show(_draw_map(f, "orthographic", "Quả địa cầu 3D", date, rot), key="m8_globe")
        else:
            ui.show(_draw_map(f, "natural earth", "Bản đồ 2D", date, rot), key="m8_flat")
        ui.source("Master table M2; toạ độ đại diện từng thị trường (thủ đô) theo M8."
                  + (f" Chưa có toạ độ nên không vẽ: {', '.join(missing)}." if missing else ""))
    with t2:
        metric = st.radio("Xếp hạng theo", ["Chỉ số phục hồi", "Lượt khách"], horizontal=True, key="m8_bar_metric")
        f2, _ = _flow_table(m, avail[-1])
        key = "market_recovery" if metric == "Chỉ số phục hồi" else "arrivals"
        s = f2.sort_values(key, ascending=True).tail(20)
        fig = go.Figure(go.Bar(
            x=s[key], y=[dl.label(k) for k in s["market"]], orientation="h", marker_color=[_region_color(c) for c in s["continent"]],
            text=[ui.n0(v) for v in s[key]], textposition="outside", cliponaxis=False,
            customdata=np.stack([s["arrivals"], s["market_recovery"]], 1),
            hovertemplate="<b>%{y}</b><br>Lượt khách: %{customdata[0]:,.0f}<br>Chỉ số: %{customdata[1]:.0f}<extra></extra>"))
        if key == "market_recovery":
            fig.add_vline(x=100, line_dash="dot", line_color=INK)
        ui.style_fig(fig, 60 + 26 * len(s), legend=False, margin=dict(l=10, r=60, t=10, b=10))
        fig.update_yaxes(showgrid=False)
        fig.update_xaxes(visible=False)
        ui.chart_title(f"20 thị trường đứng đầu theo {metric.lower()}, {ui.mlabel(avail[-1])}", "Màu = khu vực (cùng bảng màu với bản đồ)")
        ui.show(fig, key="m8_bars")
        ui.source("Master table M2.")
    with t3:
        _m8_experiment()


def _m8_experiment():
    ui.card("<h4>Cách thử</h4><p>Năm người ngoài nhóm trả lời cùng ba câu hỏi trên bản đồ 2D và quả địa cầu 3D. Thứ tự xem được xáo "
            "(ba người xem 3D trước, hai người xem 2D trước). Nhóm ghi thời gian và chấm đúng/sai từng câu: 15 lượt trả lời mỗi phiên bản.</p>", "sea")
    st.write("")
    c = st.columns(4)
    ui.kpi(c[0], "Độ chính xác 2D", "15/15", "100% câu đúng")
    ui.kpi(c[1], "Độ chính xác 3D", "15/15", "100% câu đúng")
    ui.kpi(c[2], "Thời gian trung bình · 2D", "13,7 giây", "mỗi câu")
    ui.kpi(c[3], "Thời gian trung bình · 3D", "24,0 giây", "mỗi câu · chậm hơn 10,3 giây")
    st.write("")
    log = _load_m8_log()
    if log is not None and not log.empty:
        g = log.groupby(["version", "question"])["seconds"].mean().unstack(0)
        overall = log.groupby("version")["seconds"].mean()
        xs = [f"Câu {int(q)}" for q in g.index] + ["Chung"]
        fig = go.Figure()
        for v, color in [("2D", P["Pea Flower"]), ("3D", P["Florida Oranges"])]:
            if v in g.columns:
                ys = list(g[v].values) + [overall[v]]
                fig.add_trace(go.Bar(x=xs, y=ys, name=v, marker_color=color, text=[ui.n1(y) for y in ys], textposition="outside"))
        fig.update_layout(barmode="group")
        ui.style_fig(fig, 380)
        fig.update_yaxes(title="Giây/câu trung bình")
        ui.chart_title("Thời gian trả lời trung bình từng câu: bản đồ 2D so với địa cầu 3D", f"{log['person'].nunique() if 'person' in log else 5} người thử · dữ liệu từ M8_Experiment_Results.csv")
        ui.show(fig, key="m8_exp_full")
    else:
        fig = go.Figure()
        xs = ["Trung bình mọi câu", "Câu: khu vực có chỉ số phục hồi cao nhất"]
        for v, vals, color in [("2D", [13.7, 18.6], P["Pea Flower"]), ("3D", [24.0, 33.4], P["Florida Oranges"])]:
            fig.add_trace(go.Bar(x=xs, y=vals, name=v, marker_color=color, text=[ui.n1(y) for y in vals], textposition="outside"))
        fig.update_layout(barmode="group")
        ui.style_fig(fig, 380)
        fig.update_yaxes(title="Giây/câu trung bình", range=[0, 40])
        ui.chart_title("Bản đồ 2D cho câu trả lời nhanh hơn quả địa cầu 3D, cùng độ chính xác",
                       "5 người thử · 15 lượt trả lời mỗi phiên bản · số liệu tổng hợp từ M8")
        ui.show(fig, key="m8_exp_sum")
    ui.card("<h4>Kết luận</h4><p>Trong ba tác vụ đã thử, <b>bản đồ 2D phù hợp hơn để tra cứu nhanh</b>, với cùng độ chính xác như bản 3D "
            "(câu hỏi về khu vực có chỉ số phục hồi cao nhất: 18,6 giây ở 2D so với 33,4 giây ở 3D). "
            "Quả địa cầu 3D vẫn hữu ích để gây ấn tượng và cảm nhận khoảng cách, nhưng không nên là công cụ chính để đọc số liệu.</p>"
            "<h4>Giới hạn</h4><p>Chỉ có năm người thử. Lặp lại cùng bộ câu hỏi ở hai phiên bản có thể khiến người thử nhớ đáp án từ lượt đầu và ảnh hưởng thời gian ở lượt sau.</p>")
