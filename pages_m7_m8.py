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
CLUSTER_NAME = {1: "Thị trường xa – Mùa vụ rõ hơn", 2: "Thị trường gần – Mùa vụ nhẹ hơn"}
VIETNAM = (21.0, 105.8)  # Hà Nội, điểm đại diện cho Việt Nam (như M8)


def _header(icon, title, text, guide=""):
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


def _region_color(r: str) -> str:
    return REGION_COLOR.get(r, hs.OTHER_COLOR)


# ============================================================ M7
def page_many_dimensions(D):
    _header(
        "🧩",
        "So sánh thị trường qua nhiều góc nhìn",
        "Xem sự thay đổi lượng khách theo thời gian, so sánh quy mô giữa các thị trường và nhận diện những đặc điểm khác biệt giữa các nhóm.",
        "Chuyển giữa 3 góc nhìn dữ liệu ở các tab bên dưới; tab cuối cùng giải thích nguyên tắc thiết kế và cách đọc từng biểu đồ.",
    )
    t1, t2, t3, t4 = st.tabs(["🔥 Biến động theo tháng", "🟦 Quy mô thị trường", "📈 So sánh đặc điểm", "📝 Cách xây dựng biểu đồ"])
    with t1:
        _heatmap(D)
    with t2:
        _treemap(D)
    with t3:
        _parallel(D)
    with t4:
        _m7_design()



def _heatmap(D):
    m = D["master"].copy()
    end = dl.latest_date(m)

    c1, c2, c3 = st.columns([1.1, 1, 1.3])

    order = c1.radio(
        "Sắp xếp hàng",
        ["Tên thị trường (A–Z)", "Tổng lượt khách", "Chỉ số mới nhất"],
        horizontal=False,
        key="m7_order"
    )

    years = sorted(m["year"].dropna().unique().astype(int).tolist())
    y0 = c2.select_slider(
        "Từ năm",
        options=years,
        value=years[0],
        key="m7_from"
    )

    metric = c3.selectbox(
        "Chỉ số hiển thị",
        ["Lượt khách thực tế", "Chỉ số phục hồi (2019 = 100)"],
        key="m7_heat_metric"
    )

    d = m.loc[m["date"] >= pd.Timestamp(f"{y0}-01-01")].copy()

    if metric == "Lượt khách thực tế":
        value_col = "arrivals"
        color_title = "Lượt khách"
        colorbar_title = "Lượt khách"
        hover_label = "Lượt khách"
        d = d.loc[d["arrivals"].notna()]
    else:
        value_col = "recovery_index"
        color_title = "Chỉ số phục hồi"
        colorbar_title = "Chỉ số"
        hover_label = "Chỉ số phục hồi"
        d = d.loc[d["recovery_index"].notna()]

    if d.empty:
        st.info("Không có dữ liệu cho lựa chọn này.")
        return

    piv = d.pivot_table(
        index="market",
        columns="date",
        values=value_col,
        aggfunc="mean"
    )

    months = pd.date_range(
        start=piv.columns.min(),
        end=piv.columns.max(),
        freq="MS"
    )
    piv = piv.reindex(columns=months).dropna(how="all")

    if piv.empty:
        st.info("Không có dữ liệu để hiển thị.")
        return

    if order.startswith("Tổng"):
        totals = d.groupby("market")["arrivals"].sum().reindex(piv.index)
        piv = piv.loc[totals.sort_values(ascending=True).index]

    elif order.startswith("Chỉ số"):
        latest_values = piv.iloc[:, -1]
        piv = piv.loc[
            latest_values.sort_values(
                ascending=True,
                na_position="first"
            ).index
        ]

    else:
        piv = piv.sort_index(ascending=False)

    if metric == "Lượt khách thực tế":
        z = piv.values
        fig = go.Figure(go.Heatmap(
            z=z,
            x=piv.columns,
            y=[dl.label(k) for k in piv.index],
            colorscale="YlGnBu",
            customdata=piv.values,
            hovertemplate=(
                "<b>%{y}</b> · %{x|%m/%Y}"
                "<br>Lượt khách: %{customdata:,.0f}"
                "<extra></extra>"
            ),
            colorbar=dict(title=colorbar_title),
            hoverongaps=False
        ))

        subtitle = (
            "Mỗi ô thể hiện số lượt khách thực tế của từng thị trường theo tháng. Màu càng đậm, lượng khách càng lớn."
        )

    else:
        z = piv.clip(0, 200).values
        fig = go.Figure(go.Heatmap(
            z=z,
            x=piv.columns,
            y=[dl.label(k) for k in piv.index],
            colorscale=DIV_SCALE,
            zmin=0,
            zmax=200,
            customdata=piv.values,
            hovertemplate=(
                "<b>%{y}</b> · %{x|%m/%Y}"
                "<br>Chỉ số phục hồi: %{customdata:.0f}"
                "<extra></extra>"
            ),
            colorbar=dict(
                title=colorbar_title,
                tickvals=[0, 50, 100, 150, 200],
                ticktext=["0", "50", "100", "150", "≥200"],
                len=.85
            ),
            hoverongaps=False
        ))

        subtitle = (
            "Mỗi ô là chỉ số phục hồi so với cùng tháng năm 2019 (= 100). "
            "Cam: dưới 100 · Xám: quanh 100 · Xanh: trên 100. Dữ liệu trước năm 2019 chưa có chỉ số phục hồi."
        )

    ui.style_fig(
        fig,
        120 + 22 * len(piv),
        legend=False,
        margin=dict(l=10, r=10, t=10, b=10)
    )

    fig.update_yaxes(showgrid=False, tickfont=dict(size=11))
    fig.update_xaxes(tickformat="%Y", dtick="M12", showgrid=False)

    ui.chart_title(
        f"Biến động {metric.lower()} của {len(piv)} thị trường ({y0}–{end.year})",
        subtitle
    )

    ui.show(fig, key="m7_heat")

    ui.source(
        "Bảng dữ liệu tổng hợp VNAT/NSO. "
        + (
            "Giá trị là lượt khách thực tế."
            if metric == "Lượt khách thực tế"
            else "Chỉ số phục hồi lấy cùng tháng 2019 = 100."
        )
    )



def _treemap(D):
    m = D["master"]
    end = dl.latest_date(m)
    c1, c2 = st.columns([1, 1.4])
    years = sorted(
        m.loc[m["arrivals"].notna(), "year"]
        .dropna()
        .astype(int)
        .unique()
        .tolist(),
        reverse=True
    )

    year = c1.selectbox(
        "Năm",
        years,
        index=0,
        key="m7_tree_year",
        help="Chọn năm để xem quy mô lượt khách theo thị trường."
    )
    mode = c2.radio("Màu sắc thể hiện", ["Khu vực", "Chỉ số phục hồi"], horizontal=True, key="m7_tree_mode")

    _guide_box(
        "Cách đọc biểu đồ quy mô thị trường",
        "<ul style='margin:.2rem 0 0 1.1rem;padding:0'>"
        "<li>Diện tích ô càng lớn, lượng khách càng nhiều.</li>"
        "<li>Màu sắc thể hiện khu vực hoặc chỉ số phục hồi (tùy lựa chọn ở trên).</li>"
        "<li>Chọn năm để xem quy mô thị trường trong năm đó (nhấp vào ô khu vực để phóng to từng thị trường).</li>"
        "</ul>",
    )

    # Năm đã hoàn tất: lấy đủ 12 tháng.
    # Năm mới nhất: chỉ lấy đến tháng có dữ liệu gần nhất.
    month_limit = end.month if year == end.year else 12

    sub = m.loc[
        (m["year"] == year)
        & (m["month"] <= month_limit)
        & m["arrivals"].notna()
    ].copy()
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
    display_month = end.month if year == end.year else 12
    ui.chart_title(
        f"{top['continent']} chiếm {ui.n0(100 * share)}% lượt khách trong {len(agg)} thị trường",
        f"Lượng khách cộng dồn từ T1–T{display_month}/{year} · lồng theo khu vực → thị trường"
        + (" · màu = chỉ số phục hồi so với cùng kỳ 2019" if mode == "Chỉ số phục hồi" else " · màu = khu vực"),
    )
    ui.show(fig, key="m7_tree")
    ui.source("Bảng dữ liệu tổng hợp VNAT/NSO, cộng dồn các tháng có số liệu."
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
                   f"Mỗi đường biểu diễn một thị trường ({len(seg)} thị trường) · màu = nhóm thị trường · đường nét đứt tại mức 0 = trung bình mẫu")
    ui.show(fig, key="m7_par")
    ui.source("Bảng dữ liệu tổng hợp VNAT/NSO; các đặc trưng được chuẩn hóa theo z-score.")


def _m7_design():
    ui.card("<h4>1. Biến động theo tháng (Heatmap)</h4><p>Các hàng mặc định sắp xếp theo tên thị trường để dễ tra cứu (có thể đổi sang tổng lượt khách hoặc chỉ số mới nhất), "
            "các cột đi theo thứ tự thời gian từng tháng. Khi chọn chỉ số phục hồi, thang màu phân kỳ đặt mốc 100 (= năm 2019) ở giữa: "
            "cam là chưa phục hồi, xám là quanh mốc 2019, xanh là vượt mốc 2019; giá trị trên 200 dùng chung màu đầu thang để tránh ngoại lệ làm mờ phần còn lại.</p>"
            "<h4>2. Quy mô thị trường (Treemap)</h4><p>Các ô lồng theo cấp khu vực → thị trường; diện tích mỗi ô tỷ lệ thuận với tổng lượt khách cộng dồn trong các tháng có dữ liệu của năm đã chọn. "
            "Màu mặc định phân biệt khu vực địa lý, hoặc chuyển sang chỉ số phục hồi để quan sát đồng thời quy mô và mức độ phục hồi.</p>"
            "<h4>3. So sánh đặc điểm (Đường song song · Parallel coordinates)</h4><p>Các trục sắp xếp từ tốc độ phục hồi và tăng trưởng sang đặc điểm mùa vụ rồi khoảng cách địa lý; "
            "hai trục sin và cos đặt cạnh nhau vì cùng biểu diễn tháng cao điểm theo chu kỳ năm. Mọi trục được chuẩn hóa về cùng thang đo (z-score), "
            "với đường nét đứt tại mức 0 thể hiện giá trị trung bình của toàn bộ các thị trường.</p>")


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
    _header(
        "🌍",
        "Bản đồ thị trường khách quốc tế",
        "Quan sát các thị trường gửi khách đến Việt Nam trên bản đồ 2D và địa cầu 3D. So sánh khả năng đọc dữ liệu của hai cách thể hiện.",
        "Chọn cách hiển thị và tháng phân tích ở phía trên; chuyển sang tab <b>Xếp hạng thị trường</b> để đối chiếu số liệu chính xác hoặc tab <b>Kết quả kiểm thử</b> để xem đánh giá 2D vs 3D.",
    )
    t1, t2, t3 = st.tabs(["🗺️ Bản đồ 2D và địa cầu 3D", "📊 Xếp hạng thị trường", "🧪 Kết quả kiểm thử"])

    dates = [pd.Timestamp(x) for x in sorted(m["date"].unique())]
    avail = [d for d in dates if (m.loc[m["date"] == d, "baseline_2019"].gt(0) & m.loc[m["date"] == d, "arrivals"].notna()).sum() >= 10]
    with t1:
        c1, c2, c3 = st.columns([1.1, 1.3, 1])
        view = c1.radio("Cách hiển thị", ["Địa cầu 3D", "Bản đồ 2D", "Cạnh nhau"], horizontal=True, key="m8_view")
        date = c2.select_slider("Tháng phân tích", options=avail, value=avail[-1], format_func=ui.mlabel, key="m8_month")
        rot = c3.slider("Xoay góc nhìn", -180, 180, 85, key="m8_rot", help="Điều chỉnh góc xoay kinh độ (chỉ áp dụng cho chế độ Địa cầu 3D).")
        f, missing = _flow_table(m, date)
        reg = f.groupby("continent")[["arrivals", "baseline_2019"]].sum()
        reg["idx"] = 100 * reg["arrivals"] / reg["baseline_2019"]
        reg = reg.sort_values("idx", ascending=False)
        cols = st.columns(len(reg))
        for col, (name, r) in zip(cols, reg.iterrows()):
            ui.kpi(col, name, ui.n0(r["idx"]), f"{ui.big(r['arrivals'])} lượt · chỉ số phục hồi khu vực")
        st.write("")
        title = f"Lượng khách từ các thị trường quốc tế đến Việt Nam ({ui.mlabel(date)})"
        ui.chart_title(
            title,
            f"Kích thước điểm thể hiện lượng khách; màu sắc phân biệt khu vực. Di chuột vào từng điểm để xem số khách và chỉ số phục hồi (khu vực dẫn đầu: {reg.index[0]} · {ui.n0(reg['idx'].iloc[0])}).",
        )
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
        ui.source("Bảng dữ liệu tổng hợp VNAT/NSO; tọa độ đại diện từng thị trường (thủ đô)."
                  + (f" Chưa có tọa độ nên không hiển thị: {', '.join(missing)}." if missing else ""))
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
            fig.add_vline(x=100, line_dash="dot", line_color=INK, annotation_text="Mốc 2019 = 100", annotation_position="top right")
        ui.style_fig(fig, 60 + 26 * len(s), legend=False, margin=dict(l=10, r=60, t=10, b=10))
        fig.update_yaxes(showgrid=False)
        fig.update_xaxes(visible=False)
        ui.chart_title(f"20 thị trường dẫn đầu theo {metric.lower()} ({ui.mlabel(avail[-1])})",
                       "Màu sắc phân biệt khu vực (đồng bộ với bản đồ). Đường chấm dọc (nếu có) đánh dấu mốc năm 2019 = 100.")
        ui.show(fig, key="m8_bars")
        ui.source("Bảng dữ liệu tổng hợp VNAT/NSO.")
    with t3:
        _m8_experiment()


def _m8_experiment():
    ui.card("<h4>Phương pháp kiểm thử</h4><p>Năm người ngoài nhóm thực hiện trả lời cùng ba câu hỏi trên bản đồ 2D và địa cầu 3D. Thứ tự tiếp xúc được đảo ngẫu nhiên "
            "(ba người xem 3D trước, hai người xem 2D trước). Nhóm đo thời gian và chấm độ chính xác từng câu: tổng cộng 15 lượt trả lời cho mỗi phiên bản.</p>", "sea")
    st.write("")
    c = st.columns(4)
    ui.kpi(c[0], "Độ chính xác 2D", "15/15", "100% câu trả lời đúng")
    ui.kpi(c[1], "Độ chính xác 3D", "15/15", "100% câu trả lời đúng")
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
        ui.chart_title("Thời gian trả lời trung bình từng câu: bản đồ 2D so với địa cầu 3D", f"{log['person'].nunique() if 'person' in log else 5} người tham gia · dữ liệu từ nhật ký kiểm thử")
        ui.show(fig, key="m8_exp_full")
    else:
        fig = go.Figure()
        xs = ["Trung bình mọi câu", "Câu: khu vực có chỉ số phục hồi cao nhất"]
        for v, vals, color in [("2D", [13.7, 18.6], P["Pea Flower"]), ("3D", [24.0, 33.4], P["Florida Oranges"])]:
            fig.add_trace(go.Bar(x=xs, y=vals, name=v, marker_color=color, text=[ui.n1(y) for y in vals], textposition="outside"))
        fig.update_layout(barmode="group")
        ui.style_fig(fig, 380)
        fig.update_yaxes(title="Giây/câu trung bình", range=[0, 40])
        ui.chart_title("Bản đồ 2D giúp tìm thông tin nhanh hơn địa cầu 3D với cùng độ chính xác",
                       "5 người tham gia · 15 lượt trả lời mỗi phiên bản")
        ui.show(fig, key="m8_exp_sum")
    ui.card("<h4>Kết quả chính</h4><p><b>Kết quả kiểm thử cho thấy bản đồ 2D giúp người tham gia tìm thông tin nhanh hơn địa cầu 3D, trong khi tỷ lệ trả lời đúng ở hai phiên bản tương đương</b> "
            "(câu hỏi xác định khu vực có chỉ số phục hồi cao nhất: 18,6 giây ở bản 2D so với 33,4 giây ở bản 3D). "
            "Địa cầu 3D vẫn có giá trị khi muốn quan sát vị trí địa lý và tạo góc nhìn tổng thể, nhưng bản đồ 2D phù hợp hơn với nhu cầu tra cứu số liệu.</p>"
            "<h4>Giới hạn nghiên cứu</h4><p>Kiểm thử mới thực hiện trên nhóm năm người tham gia. Việc lặp lại cùng bộ câu hỏi giữa hai phiên bản có thể khiến người tham gia ghi nhớ đáp án từ lượt đầu và ảnh hưởng đến thời gian ở lượt sau.</p>")
