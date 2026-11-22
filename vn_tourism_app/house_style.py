"""
house_style.py - House Style cho đồ án P07 "Coming Back"
Dùng chung cho MỌI biểu đồ của nhóm:  import house_style as hs; hs.apply()
Không cần cài thêm thư viện (chỉ numpy + matplotlib, Colab có sẵn).
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, to_rgb
from matplotlib.ticker import FuncFormatter

# ------------------------------------------------------------------ 1. MÀU
# NGUỒN: bảng màu của nhóm (24 màu, tên + hex nguyên bản).
PALETTE = {
    "Lilac Grey": "#D3C2CD", "Spring Leaves": "#849E15", "Good Surf": "#92A2A6", "Gold Velvet": "#B28622",
    "Brink of Pink": "#F8CABA", "Poppy": "#D8560E", "Butter Yellow": "#EFCE7B", "Florida Oranges": "#E1903E",
    "Pea Flower": "#6777B6", "Night Forest": "#2B2B23", "Dusty Berry": "#D17089", "Pistachio": "#CBD183",
    "Tea Green": "#AACC96", "Forest": "#25533F", "Peach Frost": "#F4BEAE", "Blue Berry": "#52A5CE",
    "Bubble-gum": "#FF7BAC", "Dry Earth": "#876029", "Grape Juice": "#6D1F42", "Lilacs": "#D3B6D3",
    "Halt and Catch Fire": "#FF6230", "Peach Fuzz": "#FFBE98", "Plasma Trail": "#D599FB", "Medium Slate Blue": "#7669E9",
}
P = PALETTE

# Categorical: THỨ TỰ CỐ ĐỊNH, mỗi thị trường luôn đúng một màu trong mọi biểu đồ.
# 6 màu được chọn từ 23 ứng viên bằng tìm kiếm tổ hợp: tối đa hóa khoảng cách màu (ΔE) trong mắt thường,
# 3 dạng mù màu và có xét độ sáng thang xám (xem audit_table).
MARKET_ORDER = ["Hàn Quốc", "Trung Quốc", "Nhật Bản", "Hoa Kỳ", "Đài Loan", "Nga"]
_CAT_NAMES = ["Medium Slate Blue", "Florida Oranges", "Plasma Trail", "Forest", "Pistachio", "Dry Earth"]
_CAT = [P[n] for n in _CAT_NAMES]
OTHER_COLOR = P["Good Surf"]                    # "Khác" / tổng / ngữ cảnh
MARKET_COLORS = dict(zip(MARKET_ORDER, _CAT)); MARKET_COLORS["Khác"] = OTHER_COLOR
CAT_COLORS = _CAT + [OTHER_COLOR]
# Marker đi kèm (mã hóa dự phòng, không chỉ dựa vào màu)
MARKET_MARKERS = dict(zip(MARKET_ORDER, ["o", "s", "^", "D", "v", "P"]))
EDGE = P["Night Forest"]   # viền mảnh cho màu sáng (Pistachio, Plasma Trail) để không chìm vào nền trắng

# Sequential: thấp -> cao (độ sáng giảm đơn điệu), Butter Yellow -> Grape Juice
_SEQ_NAMES = ["Butter Yellow", "Florida Oranges", "Poppy", "Grape Juice"]
SEQ_COLORS = [P[n] for n in _SEQ_NAMES]
SEQ_CMAP = LinearSegmentedColormap.from_list("hs_seq", SEQ_COLORS, N=256)

# Diverging: <100 (chưa phục hồi) Poppy | =100 Lilac Grey | >100 (vượt 2019) xanh
_DIV_NAMES = ["Poppy", "Peach Fuzz", "Lilac Grey", "Blue Berry", "Pea Flower"]
DIV_COLORS = [P[n] for n in _DIV_NAMES]
DIV_CMAP = LinearSegmentedColormap.from_list("hs_div", DIV_COLORS, N=256)
def div_norm(vmin=40, vmax=160, center=100):
    """Chuẩn hóa để giá trị 100 luôn nằm đúng màu trung tính."""
    return TwoSlopeNorm(vcenter=center, vmin=vmin, vmax=vmax)

# Màu ngữ nghĩa cho 3 trạng thái phục hồi
STATUS = {"below": P["Poppy"], "at": P["Good Surf"], "above": P["Pea Flower"]}
# Chữ/lưới: dẫn xuất từ Night Forest và Good Surf (Good Surf nguyên bản quá nhạt để làm chữ phụ)
TEXT, MUTED, GRID = P["Night Forest"], "#5C605B", "#E3E6E7"

def swatch_figure(path="palette_swatches.png"):
    """Ảnh bảng mã màu house style (tên + hex + vai trò)."""
    roles = {}
    def add(n, r): roles[n] = (roles[n] + " + " if n in roles else "") + r
    for n, m in zip(_CAT_NAMES, MARKET_ORDER): add(n, "Categorical: " + m)
    for n in _SEQ_NAMES: add(n, "Sequential")
    for n in _DIV_NAMES: add(n, "Diverging")
    add("Good Surf", "Khác / mức 'bằng 2019' / nền ngữ cảnh"); add("Night Forest", "Chữ chính, viền")
    add("Spring Leaves", "Chỉ dùng cho biểu đồ gây hiểu lầm")
    items = list(P.items()); fig, ax = plt.subplots(figsize=(11, 0.42*len(items)+0.8)); ax.set_axis_off()
    for i, (n, h) in enumerate(items):
        y = len(items) - i
        ax.add_patch(plt.Rectangle((0, y-0.8), 1.2, 0.8, color=h)); ax.text(1.4, y-0.4, f"{n}  {h}", va="center", fontsize=10)
        ax.text(5.2, y-0.4, roles.get(n, "(dự phòng)"), va="center", fontsize=9, color=MUTED)
    ax.set_xlim(0, 11); ax.set_ylim(0, len(items)+1); fig.savefig(path); return fig

# ------------------------------------------------------------------ 2. FONT + RC
FONT_PREF = ["Be Vietnam Pro", "Roboto", "Arial", "DejaVu Sans"]  # DejaVu có sẵn ở Colab, hỗ trợ tiếng Việt

def apply():
    """Gọi 1 lần ở đầu notebook."""
    avail = {f.name for f in mpl.font_manager.fontManager.ttflist}
    fam = next((f for f in FONT_PREF if f in avail), "DejaVu Sans")
    mpl.rcParams.update({
        "font.family": fam, "font.size": 11, "text.color": TEXT,
        "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 11, "axes.labelcolor": MUTED,
        "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.axisbelow": True, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.prop_cycle": mpl.cycler(color=CAT_COLORS),
        "legend.frameon": False, "figure.dpi": 110, "savefig.dpi": 200,
        "savefig.bbox": "tight", "figure.facecolor": "white", "axes.facecolor": "white",
    })
    return fam

# ------------------------------------------------------------------ 3. ĐỊNH DẠNG SỐ (kiểu Việt Nam: 1.234,5)
def _vn(s):  # đổi 1,234.5 -> 1.234,5
    return s.replace(",", "§").replace(".", ",").replace("§", ".")
def fmt_int(x, _=None):        return _vn(f"{x:,.0f}")
def fmt_million(x, _=None):    return _vn(f"{x:,.1f}") + " tr"      # x tính bằng triệu
def fmt_pct(x, _=None):        return _vn(f"{x:,.0f}") + "%"
def fmt_index(x, _=None):      return _vn(f"{x:,.0f}")
def axis_fmt(kind="int"):
    f = {"int": fmt_int, "million": fmt_million, "pct": fmt_pct, "index": fmt_index}[kind]
    return FuncFormatter(f)

# ------------------------------------------------------------------ 4. TIÊU ĐỀ / NHÃN
def title(ax, headline, sub=None, source=None):
    """Tiêu đề = thông điệp (câu khẳng định), phụ đề = đơn vị/phạm vi, nguồn ở chân."""
    ax.set_title(headline, loc="left", pad=26 if sub else 10)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, color=MUTED, fontsize=10, va="bottom")
    if source:
        ax.text(0, -0.14, "Nguồn: " + source, transform=ax.transAxes, color=MUTED, fontsize=8.5)

def label_end(ax, x, y, text, color=None, dx=0.1):
    """Nhãn trực tiếp cuối đường (thay cho legend). Chữ luôn đậm màu TEXT để dễ đọc."""
    ax.text(x + dx, y, text, color=color or TEXT, va="center", fontsize=10, fontweight="bold")

# ------------------------------------------------------------------ 5. KIỂM TRA MÀU (CVD + GRAYSCALE)
# Ma trận Machado et al. (2009), mức nghiêm trọng 1.0, áp dụng trên RGB tuyến tính
_CVD = {
 "Protanopia (thiếu đỏ)":   [[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]],
 "Deuteranopia (thiếu lục)":[[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]],
 "Tritanopia (thiếu lam)":  [[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]],
}
def _lin(c):  c = np.asarray(c, float); return np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
def _gam(c):  c = np.clip(c, 0, 1);     return np.where(c <= 0.0031308, c*12.92, 1.055*c**(1/2.4)-0.055)

def simulate(colors, mode):
    """colors: list hex/rgb -> list rgb mô phỏng. mode: tên CVD hoặc 'Grayscale'."""
    rgb = np.array([to_rgb(c) for c in colors]); L = _lin(rgb)
    if mode == "Grayscale":
        y = _gam(L @ np.array([0.2126, 0.7152, 0.0722]))
        return np.stack([y, y, y], 1)
    if mode == "Normal": return rgb
    return _gam(np.clip(L @ np.array(_CVD[mode]).T, 0, 1))

def to_lab(rgb):
    M = np.array([[0.4124,0.3576,0.1805],[0.2126,0.7152,0.0722],[0.0193,0.1192,0.9505]])
    xyz = (_lin(rgb) @ M.T) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216/24389, np.cbrt(xyz), (24389/27*xyz + 16)/116)
    return np.stack([116*f[:,1]-16, 500*(f[:,0]-f[:,1]), 200*(f[:,1]-f[:,2])], 1)

def min_delta_e(colors, mode):
    """Khoảng cách màu (ΔE76) nhỏ nhất giữa mọi cặp màu sau mô phỏng."""
    lab = to_lab(simulate(colors, mode)); n = len(lab); worst = (1e9, None)
    for i in range(n):
        for j in range(i+1, n):
            d = float(np.linalg.norm(lab[i]-lab[j]))
            if d < worst[0]: worst = (d, (i, j))
    return worst

MODES = ["Normal"] + list(_CVD) + ["Grayscale"]

def audit_table(colors=None, names=None, threshold=15):
    import pandas as pd
    colors = colors or CAT_COLORS; names = names or MARKET_ORDER + ["Khác"]
    rows = []
    for m in MODES:
        d, (i, j) = min_delta_e(colors, m)
        rows.append({"Chế độ nhìn": m, "ΔE nhỏ nhất": round(d, 1),
                     "Cặp gần nhất": f"{names[i]} ~ {names[j]}",
                     "Đánh giá": "Phân biệt được" if d >= threshold else "Dễ nhầm -> cần nhãn/marker"})
    return pd.DataFrame(rows)

def audit_figure(path="evidence_color_check.png"):
    """Xuất 1 ảnh bằng chứng: 3 bảng màu x 5 chế độ nhìn."""
    sets = [("Categorical (6 thị trường + Khác)", CAT_COLORS),
            ("Sequential (thấp -> cao)", [SEQ_CMAP(v) for v in np.linspace(0, 1, 7)]),
            ("Diverging (<100 | 100 | >100)", [DIV_CMAP(v) for v in np.linspace(0, 1, 9)])]
    fig, axes = plt.subplots(len(MODES), 3, figsize=(13, 6.2))
    for c, (nm, cols) in enumerate(sets):
        cols = [to_rgb(x) for x in cols]
        for r, m in enumerate(MODES):
            ax = axes[r, c]; sim = simulate(cols, m)
            ax.imshow(sim[None, :, :], aspect="auto"); ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values(): s.set_visible(False)
            ax.grid(False)
            if c == 0: ax.set_ylabel(m, rotation=0, ha="right", va="center", fontsize=9, color=TEXT)
            if r == 0: ax.set_title(nm, fontsize=10.5, loc="left")
    fig.suptitle("Kiểm tra khả năng tiếp cận màu: mô phỏng thiếu hụt thị giác màu + thang xám",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.savefig(path); return fig

if __name__ == "__main__":
    print("Font:", apply()); print(audit_table().to_string(index=False))
