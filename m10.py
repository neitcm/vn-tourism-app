"""
m10.py - M10 · Evaluate and Improve (phụ trách: Cẩm Tiên)
Khung kiểm thử người dùng chạy NGAY TRONG app: kế hoạch -> ghi kết quả -> phân tích -> improvement log.

LƯU Ý QUAN TRỌNG: file này KHÔNG chứa kết quả kiểm thử nào. Mọi con số trong tab "Phân tích" chỉ xuất hiện
khi nhóm nhập dữ liệu thật từ người thử thật (đề bài cấm dùng AI để tạo kết quả kiểm thử).
"""
from __future__ import annotations

import io
import time
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data_layer as dl
import ui
from ui import GRID, INK, P

LOGS = Path(__file__).parent / "logs"

TEST_COLS = ["Mã người thử", "Ngày", "Nhóm người thử", "Nhiệm vụ", "Thời gian (giây)", "Kết quả", "Số lần nhầm/bí", "Think-aloud (ghi chú)"]
FIVE_COLS = ["Mã người thử", "Ngày", "Màn hình thử", "Nhớ được gì", "Thông điệp chính", "Chấm"]
PEER_COLS = ["Ngày", "Chiều", "Người review", "Nội dung / sản phẩm", "Điểm tốt", "Cần sửa", "Mức độ"]
IMP_COLS = ["ID", "Ngày", "Nguồn phát hiện", "Vấn đề phát hiện", "Mức độ", "Trang/Module", "Cải tiến thực hiện", "Trạng thái", "Bằng chứng (trước/sau)", "Người sửa"]

SOURCES = ["Kiểm thử người dùng", "Kiểm tra 5 giây (Five-second test)", "Đánh giá chéo (Peer review)", "Tự rà soát"]
LEVELS = ["Thấp", "Trung bình", "Cao"]
STATUS = ["Đề xuất", "Đang làm", "Đã làm", "Không làm"]
TASK_RESULTS = ["Hoàn thành", "Hoàn thành một phần", "Không hoàn thành"]
GROUPS = ["Người làm du lịch", "Sinh viên", "Du khách", "Khác"]

# Các đề xuất ban đầu: rủi ro thấy khi dựng app - chưa kiểm chứng, nên để trạng thái "Đề xuất".
SEED = [
    ["IMP-01", "", "Tự rà soát", "Thuật ngữ 'chỉ số phục hồi (2019 = 100)' có thể chưa rõ với người ngoài ngành", "Trung bình", "Tổng quan",
     "Thêm chú giải ngắn ngay dưới bộ lọc hoặc KPI nếu người thử chưa hiểu", "Đề xuất", "", ""],
    ["IMP-02", "", "Tự rà soát", "Khám phá dữ liệu chọn nhiều thị trường cùng lúc có thể rối", "Trung bình", "Khám phá dữ liệu",
     "Giới hạn số đường hiển thị hoặc gợi ý nhóm thị trường nếu người thử bị rối", "Đề xuất", "", ""],
    ["IMP-03", "", "Tự rà soát", "Màu cam/xanh trạng thái chưa kiểm tra trên màn hình điện thoại và với người mù màu", "Trung bình", "Toàn ứng dụng",
     "Thêm nhãn chữ trạng thái cạnh màu; kiểm tra bằng bộ mô phỏng màu sắc", "Đề xuất", "", ""],
    ["IMP-04", "", "Tự rà soát", "Diễn biến phục hồi có thể phát quá nhanh/chậm với người xem lần đầu", "Thấp", "Diễn biến phục hồi",
     "Đo phản hồi tốc độ mặc định; chỉnh lại nếu ≥ 2 người nói khó theo dõi", "Đề xuất", "", ""],
]


# ---------------------------------------------------------------- đọc/ghi CSV
def _read(name: str, cols: list[str]) -> pd.DataFrame:
    p = LOGS / name
    if p.exists():
        try:
            df = pd.read_csv(p, encoding="utf-8-sig")
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            return df[cols]
        except Exception:
            pass
    return pd.DataFrame(columns=cols)


def _write(name: str, df: pd.DataFrame) -> bool:
    try:
        LOGS.mkdir(exist_ok=True)
        df.to_csv(LOGS / name, index=False, encoding="utf-8-sig")
        return True
    except Exception as e:  # hosting chỉ-đọc
        st.error(f"Không ghi được file ({e}). Hãy dùng nút tải CSV để lưu thủ công.")
        return False


def _append(name: str, cols: list[str], row: dict) -> bool:
    df = _read(name, cols)
    return _write(name, pd.concat([df, pd.DataFrame([row])], ignore_index=True)[cols])


def _zip_logs() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in LOGS.glob("*.csv"):
            z.write(f, f.name)
    return buf.getvalue()


# ---------------------------------------------------------------- đáp án mẫu cho người điều phối (tính từ dữ liệu)
def answer_key(D) -> dict:
    m = D["master"]
    end = dl.latest_date(m)
    snap = dl.market_snapshot(m, end).dropna(subset=["recovery_index"])
    snap["short"] = snap["baseline_2019"] - snap["arrivals"]
    t1 = snap.sort_values("short", ascending=False).iloc[0]
    S = D["season"]
    t2 = S.loc["Nhật Bản"].idxmax() if "Nhật Bản" in S.index else "–"
    kr = snap.loc[snap["market"] == "Hàn Quốc", "recovery_index"]
    cn = snap.loc[snap["market"] == "Trung Quốc", "recovery_index"]
    t3 = "–"
    if len(kr) and len(cn):
        t3 = f"Hàn Quốc ({ui.n0(kr.iloc[0])}) so với Trung Quốc ({ui.n0(cn.iloc[0])}) ở {ui.mlabel(end)}"
    size = m.groupby("market")["baseline_2019"].mean().sort_values(ascending=False).index[:12]
    piv = m.loc[m["market"].isin(size)].pivot(index="date", columns="market", values="recovery_index").loc["2022-01":]
    first = {k: piv[k].dropna()[piv[k].dropna() >= 100].index.min() for k in piv.columns}
    first = pd.Series(first).dropna().sort_values()
    t4 = f"{first.index[0]} ({ui.mlabel(first.iloc[0])})" if len(first) else "–"
    return {"T1": f"{t1['market']} (thiếu {ui.big(t1['short'])} lượt)", "T2": t2, "T3": t3, "T4": t4}


TASKS = [
    ("T1", "Ở tháng mới nhất, thị trường nào đang thiếu nhiều khách nhất so với cùng tháng 2019?", "Khám phá dữ liệu → Trả lời câu hỏi thực tế (câu 1)", 60),
    ("T2", "Nhật Bản đông khách nhất vào tháng nào trong năm?", "Khám phá dữ liệu → Trả lời câu hỏi thực tế (câu 2)", 60),
    ("T3", "Dùng bộ lọc so sánh Hàn Quốc và Trung Quốc từ 2022. Thị trường nào đang cao hơn?", "Khám phá dữ liệu → Tự chọn dữ liệu", 90),
    ("T4", "Ở trang Diễn biến phục hồi, thị trường nào đạt mốc 100 đầu tiên?", "Diễn biến phục hồi", 60),
    ("T5", "Nói bằng lời của bạn: thông điệp chính của trang Tổng quan là gì?", "Tổng quan", 90),
]


# ---------------------------------------------------------------- trang chính
def page(D):
    ui.page_header(
        "🧪",
        "Đánh giá và cải tiến",
        "Lập kế hoạch kiểm thử, ghi nhận kết quả thực tế từ người tham gia, phân tích dữ liệu và theo dõi nhật ký cải tiến.",
    )
    _progress()
    t1, t2, t3, t4 = st.tabs(["📋 Kế hoạch kiểm thử", "📝 Ghi nhận kết quả", "📊 Phân tích kết quả", "🛠️ Nhật ký cải tiến"])
    with t1:
        _plan(D)
    with t2:
        _record(D)
    with t3:
        _analysis()
    with t4:
        _improvements()
    st.write("")
    c1, _ = st.columns([1, 3])
    if any(LOGS.glob("*.csv")) if LOGS.exists() else False:
        c1.download_button("⬇️ Tải toàn bộ nhật ký (ZIP)", _zip_logs(), "m10_logs.zip", "application/zip")
    st.caption("Nếu ứng dụng chạy trên máy chủ miễn phí, file ghi tạm có thể mất khi khởi động lại — hãy tải nhật ký về sau mỗi buổi kiểm thử.")


def _progress():
    tests = _read("user_tests.csv", TEST_COLS)
    five = _read("five_second.csv", FIVE_COLS)
    peer = _read("peer_review.csv", PEER_COLS)
    imp = _read("improvement_log.csv", IMP_COLS)
    n_people = tests["Mã người thử"].nunique() if len(tests) else 0
    n_done = int((imp["Trạng thái"] == "Đã làm").sum()) if len(imp) else 0
    dirs = set(peer["Chiều"]) if len(peer) else set()
    items = [
        (n_people >= 5, f"Người ngoài nhóm đã thử: {n_people}/5"),
        (len(five) > 0, f"Kiểm tra 5 giây: {five['Mã người thử'].nunique() if len(five) else 0} người"),
        ({"Cho", "Nhận"} <= dirs, "Đánh giá chéo: cả hai chiều cho và nhận"),
        (n_done >= 8, f"Cải tiến đã thực hiện: {n_done}/8"),
    ]
    cols = st.columns(4)
    for col, (ok, text) in zip(cols, items):
        col.markdown(f"<div class='kpi'><div class='lab'>{'✅ Đạt' if ok else '⬜ Chưa đạt'}</div>"
                     f"<div class='sub' style='color:{ui.INK};font-weight:600;margin-top:.3rem'>{text}</div></div>", unsafe_allow_html=True)
    st.write("")


# ---------------------------------------------------------------- 1. kế hoạch
def _plan(D):
    key = answer_key(D)
    c1, c2 = st.columns([1.2, 1])
    with c1:
        ui.card("<h4>🎯 Mục tiêu</h4><p>Kiểm tra xem người ngoài nhóm có <b>tìm được câu trả lời cho các câu hỏi thực tế</b> bằng bảng điều khiển dữ liệu hay không, "
                "mất bao lâu và gặp khó khăn ở bước nào.</p>"
                "<h4>👥 Người tham gia</h4><p>Tối thiểu 5 người ngoài nhóm (ưu tiên người làm du lịch, sinh viên, du khách). Mỗi người được gắn một mã (P01, P02…) — "
                "<b>không ghi tên thật</b>, chỉ ghi nhận khi có sự đồng ý.</p>"
                "<h4>🧭 Quy trình mỗi lượt (~15 phút)</h4>"
                "<ol><li>Giới thiệu ngắn gọn mục đích, xin phép ghi nhận ẩn danh.</li><li><b>Kiểm tra 5 giây (Five-second test)</b> tại tab Ghi nhận kết quả.</li>"
                "<li>Thực hiện 5 nhiệm vụ bên dưới — <b>vừa thực hiện vừa nói suy nghĩ (Think-aloud)</b>, không gợi ý và bấm giờ.</li>"
                "<li>Phỏng vấn nhanh: chỗ nào khó hiểu nhất? Điểm nào muốn thêm hoặc bỏ?</li></ol>", "sea")
    with c2:
        ui.card("<h4>✅ Quy tắc chấm điểm</h4><ul><li><b>Hoàn thành</b>: đúng đáp án, không cần gợi ý.</li>"
                "<li><b>Hoàn thành một phần</b>: đúng hướng nhưng cần gợi ý hoặc sai chi tiết nhỏ.</li><li><b>Không hoàn thành</b>: bỏ cuộc hoặc trả lời sai.</li></ul>"
                "<p>Ghi nhận thêm số lần người tham gia bị nhầm/bí và các nhận xét đáng chú ý. Mọi vướng mắc thực tế đều là cơ sở để cải tiến.</p>", "sun")
    st.markdown("#### Nhiệm vụ cho người thử")
    rows = [{"Mã": t, "Nhiệm vụ": txt, "Khu vực trong app": where, "Thời gian mục tiêu (giây)": sec} for t, txt, where, sec in TASKS]
    ui.table(pd.DataFrame(rows))
    with st.expander("🔒 Đáp án tham chiếu (chỉ dành cho người điều phối — đừng cho người thử xem)"):
        st.markdown("\n".join(f"- **{k}**: {v}" for k, v in key.items()) + "\n- **T5**: ý chính — Việt Nam đã vượt mốc 2019 nhưng không đồng đều; "
                    "thị trường lớn ở Đông Bắc Á còn dưới 2019.")
        st.caption("Đáp án tự cập nhật theo dữ liệu mới nhất; hãy kiểm tra lại trước buổi thử.")


# ---------------------------------------------------------------- 2. ghi kết quả
def _five_stimulus(D, kind: str):
    m = D["master"]
    end = dl.latest_date(m)
    if kind.startswith("Biểu đồ chênh"):
        s = dl.market_snapshot(m, end).dropna(subset=["recovery_index"])
        s["gap"] = s["arrivals"] - s["baseline_2019"]
        g = s.reindex(s["gap"].abs().sort_values(ascending=False).index).head(16).sort_values("gap")
        fig = go.Figure(go.Bar(x=g["gap"], y=[dl.label(k) for k in g["market"]], orientation="h",
                               marker_color=[ui.STATUS_COLOR[x] for x in g["status"]]))
        ui.style_fig(fig, 480, legend=False)
        fig.update_yaxes(showgrid=False)
        ui.chart_title("Ai tăng, ai thiếu so với 2019?", f"{ui.mlabel(end)} so với cùng tháng 2019")
    else:
        ts = dl.total_index_series(m).set_index("date")["index"].loc["2022-01-01":]
        fig = go.Figure(go.Scatter(x=ts.index, y=ts.values, mode="lines+markers", line=dict(color=P["Pea Flower"], width=3)))
        fig.add_hline(y=100, line_dash="dot", line_color=INK)
        ui.style_fig(fig, 400, legend=False)
        ui.chart_title("Chỉ số gộp so với 2019", "2019 = 100")
    return fig


def _record(D):
    a, b, c = st.tabs(["Nhiệm vụ", "Kiểm tra 5 giây", "Đánh giá chéo"])
    with a:
        with st.form("f_task", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            pid = c1.text_input("Mã người thử", placeholder="P01")
            grp = c2.selectbox("Nhóm người thử", GROUPS)
            task = c3.selectbox("Nhiệm vụ", [f"{t} · {txt[:50]}…" for t, txt, _, _ in TASKS])
            c4, c5, c6 = st.columns(3)
            secs = c4.number_input("Thời gian (giây)", min_value=0.0, step=1.0)
            res = c5.selectbox("Kết quả", TASK_RESULTS)
            errs = c6.number_input("Số lần nhầm/bí", min_value=0, step=1)
            note = st.text_area("Ghi chú lúc nói suy nghĩ (Think-aloud)", height=80)
            ok = st.checkbox("Người thử đã đồng ý cho ghi nhận (ẩn danh)")
            if st.form_submit_button("➕ Lưu lượt thử", type="primary"):
                if not (pid.strip() and ok and secs > 0):
                    st.warning("Cần mã người thử, thời gian > 0 và xác nhận đồng ý.")
                elif _append("user_tests.csv", TEST_COLS, {
                        "Mã người thử": pid.strip(), "Ngày": date.today().isoformat(), "Nhóm người thử": grp, "Nhiệm vụ": task.split(" ·")[0],
                        "Thời gian (giây)": secs, "Kết quả": res, "Số lần nhầm/bí": errs, "Think-aloud (ghi chú)": note.strip()}):
                    st.success("Đã lưu.")
        df = _read("user_tests.csv", TEST_COLS)
        if len(df):
            ui.table(df.tail(10))
    with b:
        st.caption("Màn hình hiển thị đúng 5 giây rồi ẩn đi. Sau đó hỏi: *bạn nhớ được gì? thông điệp chính là gì?*")
        kind = st.radio("Màn hình thử", ["Biểu đồ chênh lệch so với 2019", "Đường chỉ số gộp"], horizontal=True)
        holder = st.empty()
        if st.button("▶ Bắt đầu 5 giây"):
            with holder.container():
                ui.show(_five_stimulus(D, kind), key="five_stim")
            time.sleep(5)
            holder.empty()
            st.info("Hết 5 giây. Hỏi người thử rồi ghi câu trả lời bên dưới.")
        with st.form("f_five", clear_on_submit=True):
            c1, c2 = st.columns(2)
            pid = c1.text_input("Mã người thử", key="five_pid", placeholder="P01")
            grade = c2.selectbox("Chấm thông điệp chính", ["Đúng", "Một phần", "Sai"])
            rec = st.text_area("Người thử nhớ được gì? (ghi nguyên văn)", height=70)
            msg = st.text_input("Họ nói thông điệp chính là gì?")
            if st.form_submit_button("➕ Lưu kiểm tra 5 giây", type="primary"):
                if not pid.strip():
                    st.warning("Cần mã người thử.")
                elif _append("five_second.csv", FIVE_COLS, {"Mã người thử": pid.strip(), "Ngày": date.today().isoformat(), "Màn hình thử": kind,
                                                            "Nhớ được gì": rec.strip(), "Thông điệp chính": msg.strip(), "Chấm": grade}):
                    st.success("Đã lưu.")
    with c:
        with st.form("f_peer", clear_on_submit=True):
            c1, c2 = st.columns(2)
            way = c1.radio("Chiều đánh giá", ["Nhận", "Cho"], horizontal=True, help="Nhận = nhóm khác đánh giá bài mình; Cho = mình đánh giá bài nhóm khác")
            who = c2.text_input("Người/nhóm đánh giá")
            what = st.text_input("Nội dung / sản phẩm được đánh giá")
            good = st.text_area("Điểm tốt", height=60)
            fix = st.text_area("Cần sửa", height=60)
            lvl = st.select_slider("Mức độ cần sửa", LEVELS, value="Trung bình")
            if st.form_submit_button("➕ Lưu đánh giá chéo", type="primary"):
                if not (who.strip() and what.strip()):
                    st.warning("Cần tên người đánh giá và nội dung được đánh giá.")
                elif _append("peer_review.csv", PEER_COLS, {"Ngày": date.today().isoformat(), "Chiều": way, "Người review": who.strip(),
                                                            "Nội dung / sản phẩm": what.strip(), "Điểm tốt": good.strip(), "Cần sửa": fix.strip(), "Mức độ": lvl}):
                    st.success("Đã lưu. Nhớ chuyển mục 'Cần sửa' sang Nhật ký cải tiến.")
        pr = _read("peer_review.csv", PEER_COLS)
        if len(pr):
            ui.table(pr.tail(10))


# ---------------------------------------------------------------- 3. phân tích
def _analysis():
    df = _read("user_tests.csv", TEST_COLS)
    five = _read("five_second.csv", FIVE_COLS)
    if df.empty and five.empty:
        ui.card("<h4>Chưa có dữ liệu</h4><p>Tab này chỉ hiện số liệu khi nhóm nhập kết quả thật từ người tham gia kiểm thử. "
                "Không có số liệu mẫu hay số liệu do AI tạo.</p>")
        return
    if len(df):
        df["Thời gian (giây)"] = pd.to_numeric(df["Thời gian (giây)"], errors="coerce")
        n = df["Mã người thử"].nunique()
        k = df.groupby("Nhiệm vụ").agg(lượt=("Kết quả", "size"), tg_trung_vi=("Thời gian (giây)", "median"),
                                       hoan_thanh=("Kết quả", lambda s: 100 * (s == "Hoàn thành").mean()))
        c = st.columns(3)
        ui.kpi(c[0], "Người đã thử", str(n), "mục tiêu ≥ 5")
        ui.kpi(c[1], "Tỷ lệ hoàn thành chung", ui.pct(100 * (df["Kết quả"] == "Hoàn thành").mean(), signed=False), f"{len(df)} lượt nhiệm vụ")
        ui.kpi(c[2], "Thời gian trung vị", f"{ui.n0(df['Thời gian (giây)'].median())} giây", "mỗi nhiệm vụ")
        st.write("")
        order = [t for t, *_ in TASKS if t in k.index]
        k = k.reindex(order)
        fig = go.Figure(go.Bar(x=k.index, y=k["hoan_thanh"], marker_color=[P["Pea Flower"] if v >= 80 else P["Poppy"] for v in k["hoan_thanh"]],
                               text=[ui.pct(v, signed=False) for v in k["hoan_thanh"]], textposition="outside",
                               customdata=np.stack([k["lượt"], k["tg_trung_vi"]], 1),
                               hovertemplate="<b>%{x}</b><br>Hoàn thành: %{y:.0f}%<br>Số lượt: %{customdata[0]}<br>Thời gian trung vị: %{customdata[1]:.0f} s<extra></extra>"))
        ui.style_fig(fig, 340, legend=False)
        fig.update_yaxes(title="% người hoàn thành", range=[0, 115])
        low = k["hoan_thanh"].idxmin()
        ui.chart_title(f"Nhiệm vụ {low} có tỷ lệ hoàn thành thấp nhất ({ui.pct(k.loc[low, 'hoan_thanh'], signed=False)})",
                       f"{n} người thử · xanh ≥ 80% · cam &lt; 80%")
        ui.show(fig, key="an_task")
        if n < 10:
            st.caption(f"⚠️ Chỉ có {n} người thử: nên đọc như dấu hiệu định tính, không suy diễn thống kê.")
        with st.expander("Bảng chi tiết & ghi chú nói suy nghĩ"):
            ui.table(df)
    if len(five):
        st.markdown("#### Kiểm tra 5 giây")
        share = 100 * (five["Chấm"] == "Đúng").mean()
        st.metric("Nắm đúng thông điệp chính sau 5 giây", ui.pct(share, signed=False), f"{len(five)} người")
        ui.table(five[["Mã người thử", "Màn hình thử", "Nhớ được gì", "Thông điệp chính", "Chấm"]])


# ---------------------------------------------------------------- 4. nhật ký cải tiến
def _improvements():
    df = _read("improvement_log.csv", IMP_COLS)
    if df.empty:
        df = pd.DataFrame(SEED, columns=IMP_COLS)
        df["Ngày"] = date.today().isoformat()
    done = int((df["Trạng thái"] == "Đã làm").sum())
    st.markdown(f"**{done}/8** cải tiến đã làm · yêu cầu tối thiểu 8 · mỗi dòng nên ghi rõ nguồn phát hiện và bằng chứng trước/sau.")
    st.caption("Bốn dòng đầu là *đề xuất tự rà soát* khi xây dựng ứng dụng, chưa kiểm chứng — giữ, sửa hoặc xóa tùy theo kết quả kiểm thử thật.")
    edited = st.data_editor(
        df, num_rows="dynamic", key="imp_editor", hide_index=True, **ui._stretch(),
        column_config={
            "Nguồn phát hiện": st.column_config.SelectboxColumn(options=SOURCES),
            "Mức độ": st.column_config.SelectboxColumn(options=LEVELS),
            "Trạng thái": st.column_config.SelectboxColumn(options=STATUS),
            "Vấn đề phát hiện": st.column_config.TextColumn(width="large"),
            "Cải tiến thực hiện": st.column_config.TextColumn(width="large"),
        })
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button("💾 Lưu nhật ký cải tiến", type="primary"):
        out = edited.copy()
        out["ID"] = [x if isinstance(x, str) and x.strip() else f"IMP-{i + 1:02d}" for i, x in enumerate(out["ID"])]
        if _write("improvement_log.csv", out[IMP_COLS]):
            st.success("Đã lưu. Tải CSV để nộp kèm bài.")
    c2.download_button("⬇️ Tải nhật ký (CSV)", edited.to_csv(index=False).encode("utf-8-sig"), "improvement_log.csv", "text/csv")
