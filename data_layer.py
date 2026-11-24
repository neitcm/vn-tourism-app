"""
data_layer.py - Lớp dữ liệu cho app "Coming Back" (M9/M10).
Chỉ dùng pandas / numpy / scipy / sklearn (KHÔNG import streamlit, plotly)
=> có thể test độc lập, và app.py chỉ lo phần hiển thị.

Nguồn: master_market_month.csv (M2) + Google Trends + Open-Meteo.
Toàn bộ định nghĩa chỉ số bám theo notebook M4/M6 của nhóm.
"""
from __future__ import annotations

import pandas as pd

df = pd.read_csv("data/master_market_month.csv")

print(df.head())
print(df.shape)
print(df.columns.tolist())

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
BASE_YEAR = 2019

# ---------------------------------------------------------------- tên + cờ
VN_NAME = {
    "Australia": "Úc", "Belgium": "Bỉ", "Cambodia": "Campuchia", "Canada": "Canada",
    "China": "Trung Quốc", "Czechia": "Séc", "Denmark": "Đan Mạch", "Finland": "Phần Lan",
    "France": "Pháp", "Germany": "Đức", "Hong Kong": "Hồng Kông", "India": "Ấn Độ",
    "Indonesia": "Indonesia", "Italy": "Ý", "Japan": "Nhật Bản",
    "Lao People's Democratic Republic": "Lào", "Malaysia": "Malaysia", "Netherlands": "Hà Lan",
    "New Zealand": "New Zealand", "Norway": "Na Uy", "Philippines": "Philippines", "Poland": "Ba Lan",
    "Russian Federation": "Nga", "Singapore": "Singapore", "South Korea": "Hàn Quốc", "Spain": "Tây Ban Nha",
    "Sweden": "Thụy Điển", "Switzerland": "Thụy Sĩ", "Taiwan": "Đài Loan", "Thailand": "Thái Lan",
    "United Kingdom": "Vương quốc Anh", "United States of America": "Hoa Kỳ",
}
FLAG = {
    "Úc": "🇦🇺", "Bỉ": "🇧🇪", "Campuchia": "🇰🇭", "Canada": "🇨🇦", "Trung Quốc": "🇨🇳", "Séc": "🇨🇿",
    "Đan Mạch": "🇩🇰", "Phần Lan": "🇫🇮", "Pháp": "🇫🇷", "Đức": "🇩🇪", "Hồng Kông": "🇭🇰", "Ấn Độ": "🇮🇳",
    "Indonesia": "🇮🇩", "Ý": "🇮🇹", "Nhật Bản": "🇯🇵", "Lào": "🇱🇦", "Malaysia": "🇲🇾", "Hà Lan": "🇳🇱",
    "New Zealand": "🇳🇿", "Na Uy": "🇳🇴", "Philippines": "🇵🇭", "Ba Lan": "🇵🇱", "Nga": "🇷🇺",
    "Singapore": "🇸🇬", "Hàn Quốc": "🇰🇷", "Tây Ban Nha": "🇪🇸", "Thụy Điển": "🇸🇪", "Thụy Sĩ": "🇨🇭",
    "Đài Loan": "🇹🇼", "Thái Lan": "🇹🇭", "Vương quốc Anh": "🇬🇧", "Hoa Kỳ": "🇺🇸",
}
# Toạ độ đại diện (lấy nguyên từ M8)
LATLON = {
    "Úc": (-35.3, 149.1), "Bỉ": (50.8, 4.4), "Campuchia": (11.6, 104.9), "Canada": (45.4, -75.7),
    "Trung Quốc": (39.9, 116.4), "Đan Mạch": (55.7, 12.6), "Pháp": (48.9, 2.4), "Đức": (52.5, 13.4),
    "Ấn Độ": (28.6, 77.2), "Indonesia": (-6.2, 106.8), "Ý": (41.9, 12.5), "Nhật Bản": (35.7, 139.7),
    "Lào": (18.0, 102.6), "Malaysia": (3.1, 101.7), "Hà Lan": (52.4, 4.9), "New Zealand": (-41.3, 174.8),
    "Na Uy": (59.9, 10.8), "Philippines": (14.6, 121.0), "Nga": (55.8, 37.6), "Singapore": (1.3, 103.8),
    "Hàn Quốc": (37.6, 127.0), "Tây Ban Nha": (40.4, -3.7), "Thụy Điển": (59.3, 18.1),
    "Thụy Sĩ": (46.9, 7.4), "Thái Lan": (13.8, 100.5), "Vương quốc Anh": (51.5, -0.1),
    "Hoa Kỳ": (38.9, -77.0), "Đài Loan": (25.0, 121.6),
}
MONTH_LABEL = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]


def label(market: str) -> str:
    """Tên có cờ, dùng trong nhãn/hover."""
    return f"{FLAG.get(market, '🌐')} {market}"


# ---------------------------------------------------------------- tải dữ liệu
def load_master() -> pd.DataFrame:
    df = pd.read_csv(DATA / "master_market_month.csv", encoding="utf-8-sig", parse_dates=["date"])
    df["market_en"] = df["market"]
    df["market"] = df["market_en"].map(VN_NAME).fillna(df["market_en"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def load_weather() -> pd.DataFrame:
    w = pd.read_csv(DATA / "PUB03_OpenMeteo_Monthly_Clean.csv", encoding="utf-8-sig", parse_dates=["date"])
    w["year"] = w["date"].dt.year
    w["month"] = w["date"].dt.month
    w["destination"] = w["destination"].replace({"Da Nang": "Đà Nẵng", "Nha Trang": "Nha Trang"})
    return w


def load_trends() -> pd.DataFrame:
    t = pd.read_csv(DATA / "PUB01_PUB02_All_Markets_Integrated.csv", encoding="utf-8-sig", parse_dates=["date"])
    t["market"] = t["source_market"].map(VN_NAME).fillna(t["source_market"])
    return t


def load_correlations() -> pd.DataFrame:
    c = pd.read_csv(DATA / "PUB02_Correlation_Results_All_Markets.csv", encoding="utf-8-sig")
    c["market"] = c["market"].map(VN_NAME).fillna(c["market"])
    return c


def load_yoy() -> pd.DataFrame:
    c = pd.read_csv(DATA / "PUB02_YoY_Correlation_Robustness.csv", encoding="utf-8-sig")
    c["market"] = c["market"].map(VN_NAME).fillna(c["market"])
    return c


# ---------------------------------------------------------------- chỉ số phục hồi
def latest_date(master: pd.DataFrame) -> pd.Timestamp:
    return master.loc[master["arrivals"].notna(), "date"].max()


def comparable_total(master: pd.DataFrame, date) -> dict:
    """Tổng lượt khách tháng `date` và tổng cùng tháng 2019 - chỉ trên các thị trường có đủ CẢ HAI
    (so sánh cùng tập thị trường, không so táo với cam)."""
    m = master.loc[(master["date"] == pd.Timestamp(date)) & master["arrivals"].notna() & master["baseline_2019"].gt(0)]
    if m.empty:
        return {"arrivals": np.nan, "baseline": np.nan, "index": np.nan, "n": 0}
    a, b = float(m["arrivals"].sum()), float(m["baseline_2019"].sum())
    return {"arrivals": a, "baseline": b, "index": 100 * a / b, "n": int(len(m))}


def total_index_series(master: pd.DataFrame, markets: list[str] | None = None) -> pd.DataFrame:
    """Chỉ số phục hồi gộp theo tháng (Σ lượt / Σ mốc 2019 trên cùng tập thị trường)."""
    m = master.loc[master["arrivals"].notna() & master["baseline_2019"].gt(0)]
    if markets:
        m = m.loc[m["market"].isin(markets)]
    g = m.groupby("date").agg(arrivals=("arrivals", "sum"), baseline=("baseline_2019", "sum"), n=("market", "size"))
    g["index"] = 100 * g["arrivals"] / g["baseline"]
    return g.reset_index()


def ytd_compare(master: pd.DataFrame) -> dict:
    """Lũy kế từ đầu năm đến tháng mới nhất: năm nay vs năm trước vs 2019 (cùng tập thị trường, đủ tháng)."""
    end = latest_date(master)
    months = range(1, end.month + 1)
    sub = master.loc[master["month"].isin(months) & master["year"].isin([BASE_YEAR, end.year - 1, end.year])]
    piv = sub.pivot_table(index="market", columns="year", values="arrivals", aggfunc=["sum", "count"])
    ok = ((piv["count"][[BASE_YEAR, end.year - 1, end.year]] == end.month).all(axis=1))
    tot = piv["sum"].loc[ok]
    return {
        "year": int(end.year), "month": int(end.month), "n": int(ok.sum()),
        "this": float(tot[end.year].sum()), "prev": float(tot[end.year - 1].sum()), "base": float(tot[BASE_YEAR].sum()),
    }


def market_snapshot(master: pd.DataFrame, date=None) -> pd.DataFrame:
    """Bảng 1 tháng: lượt khách, mốc 2019, chỉ số, vùng, trạng thái."""
    date = pd.Timestamp(date) if date is not None else latest_date(master)
    s = master.loc[(master["date"] == date) & master["arrivals"].notna(),
                   ["market", "continent", "arrivals", "baseline_2019", "recovery_index", "distance_km"]].copy()
    s["status"] = np.select([s["recovery_index"] < 95, s["recovery_index"] > 105],
                            ["Chưa phục hồi", "Vượt 2019"], default="Quanh mốc 2019")
    s.loc[s["recovery_index"].isna(), "status"] = "Chưa có mốc 2019"
    return s.sort_values("arrivals", ascending=False).reset_index(drop=True)


def seasonal_index(master: pd.DataFrame, years=(2023, 2024, 2025), months=range(1, 12)) -> pd.DataFrame:
    """Chỉ số mùa vụ (đúng định nghĩa M6): lượt tháng / bình quân tháng 1-11 của chính năm đó x100,
    lấy trung vị theo tháng qua các năm. Chỉ giữ thị trường đủ tháng. Trả về ma trận thị trường x tháng."""
    months = list(months)
    sub = master.loc[master["year"].isin(years) & master["month"].isin(months)]
    rows = {}
    for mk, g in sub.groupby("market"):
        per_year = []
        for y in years:
            gy = g.loc[g["year"] == y].set_index("month")["arrivals"].reindex(months)
            if gy.isna().any() or not (gy > 0).all():
                per_year = None
                break
            per_year.append(100 * gy / gy.mean())
        if per_year:
            rows[mk] = pd.concat(per_year, axis=1).median(axis=1)
    out = pd.DataFrame(rows).T
    out.columns = [f"T{m}" for m in months]
    return out


# ---------------------------------------------------------------- phân khúc (tái lập M6)
RECOVERY_WINDOW = ("2022-04-01", "2024-12-01")
MIN_RECOVERY_SHARE = 0.85
LINEAR = ["recovery_speed", "seasonal_amplitude", "distance_km", "growth_pct"]


def build_features(master: pd.DataFrame, seasons=(2023, 2024, 2025)):
    """Tái lập bảng đặc trưng M6. Trả về (features, excluded)."""
    from scipy.stats import theilslopes

    end = latest_date(master)
    window = pd.date_range(*RECOVERY_WINDOW, freq="MS")
    minimum = int(np.ceil(len(window) * MIN_RECOVERY_SHARE))
    s_idx = seasonal_index(master, seasons)
    rows, excl = [], []
    for mk, g in master.groupby("market"):
        reasons = []
        if mk not in s_idx.index:
            reasons.append("thiếu tháng trong kỳ mùa vụ chung 2023–2025")
        cur = g.loc[(g["year"] == end.year) & (g["month"] <= end.month)].set_index("month")["arrivals"].reindex(range(1, end.month + 1))
        prv = g.loc[(g["year"] == end.year - 1) & (g["month"] <= end.month)].set_index("month")["arrivals"].reindex(range(1, end.month + 1))
        if cur.isna().any() or prv.isna().any() or not (cur.sum() > 0 and prv.sum() > 0):
            reasons.append("thiếu lượt khách cùng kỳ")
        rec = g.set_index("date")["recovery_index"].reindex(window)
        if rec.notna().sum() < minimum:
            reasons.append(f"thiếu chỉ số phục hồi ({int(rec.notna().sum())}/{len(window)} tháng)")
        if reasons:
            excl.append({"market": mk, "reason": " / ".join(reasons)})
            continue
        x = np.arange(len(window))[rec.notna().to_numpy()]
        slope = theilslopes(rec.dropna().to_numpy(), x)[0]
        med = s_idx.loc[mk]
        peak_month = int(str(med.idxmax())[1:])
        rows.append({
            "market": mk,
            "recovery_speed": float(slope),
            "seasonal_amplitude": float(med.max() - med.min()),
            "peak_month": peak_month,
            "distance_km": float(g["distance_km"].iloc[0]),
            "growth_pct": float(100 * (cur.sum() / prv.sum() - 1)),
            "arrivals_latest_ytd": float(cur.sum()),
        })
    f = pd.DataFrame(rows).set_index("market")
    ang = 2 * np.pi * (f["peak_month"] - 1) / 12
    f["peak_sin"], f["peak_cos"] = np.sin(ang), np.cos(ang)
    return f, pd.DataFrame(excl)


def segment_markets(features: pd.DataFrame, k: int = 2, seeds=(42, 97)):
    """K-means trên đặc trưng đã chuẩn hoá (giống M6) + PCA 2 chiều để vẽ. Trả về bảng thị trường + hồ sơ cụm."""
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    z = pd.DataFrame(StandardScaler().fit_transform(features[LINEAR]), index=features.index, columns=LINEAR)
    cyc = features[["peak_sin", "peak_cos"]].to_numpy()
    cyc = cyc - cyc.mean(axis=0)
    scale = np.sqrt(np.mean(np.square(cyc).sum(axis=1)))
    z[["peak_sin", "peak_cos"]] = cyc / scale if scale > 1e-12 else 0
    from sklearn.metrics import silhouette_score
    km = KMeans(n_clusters=k, random_state=seeds[0], n_init=20).fit(z)
    sil = float(silhouette_score(z, km.labels_))
    pcs = PCA(n_components=2).fit(z)
    xy = pcs.transform(z)
    out = features.copy()
    out["cluster"] = km.labels_
    out["PC1"], out["PC2"] = xy[:, 0], xy[:, 1]
    # Đánh số cụm theo khoảng cách trung vị giảm dần: cụm 1 = xa nhất (ổn định giữa các lần chạy)
    order = out.groupby("cluster")["distance_km"].median().sort_values(ascending=False).index.tolist()
    out["cluster"] = out["cluster"].map({c: i + 1 for i, c in enumerate(order)})
    prof = out.groupby("cluster").agg(
        n=("distance_km", "size"), recovery_speed=("recovery_speed", "median"),
        seasonal_amplitude=("seasonal_amplitude", "median"), distance_km=("distance_km", "median"),
        growth_pct=("growth_pct", "median"),
    )
    prof["markets"] = out.sort_values("arrivals_latest_ytd", ascending=False).groupby("cluster").apply(lambda d: list(d.index))
    prof["peak_month_mode"] = out.groupby("cluster")["peak_month"].agg(lambda s: int(s.mode().min()))
    return out, prof, pcs.explained_variance_ratio_, sil


# ---------------------------------------------------------------- Google Trends dẫn trước
def lagged_trends(trends: pd.DataFrame, market: str, lag: int, outcome: str = "arrivals") -> pd.DataFrame:
    """Ghép Trends (lùi `lag` tháng) với lượt khách/ chỉ số. Chỉ giữ tháng có đủ hai bên."""
    t = trends.loc[trends["market"] == market].sort_values("date").copy()
    t["interest_lag"] = t["interest"].shift(lag)  # Trends của lag tháng TRƯỚC
    t = t.dropna(subset=["interest_lag", outcome])
    return t[["date", "interest_lag", outcome]]


def simple_corr(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    from scipy.stats import pearsonr, spearmanr
    if len(x) < 5:
        return np.nan, np.nan
    return float(pearsonr(x, y)[0]), float(spearmanr(x, y)[0])


if __name__ == "__main__":
    m = load_master()
    print("Tháng mới nhất:", latest_date(m).date())
    print("YTD:", ytd_compare(m))
    print("Cùng tập thị trường, tháng mới nhất:", comparable_total(m, latest_date(m)))
    f, ex = build_features(m)
    print(len(f), "thị trường vào phân khúc;", len(ex), "bị loại")
    print(ex.to_string(index=False))
    seg, prof, evr, sil = segment_markets(f)
    print('silhouette', round(sil, 3), 'PCA', evr.round(3))
    print(prof.drop(columns=["markets"]).round(2))
    print(prof["markets"].to_dict())
