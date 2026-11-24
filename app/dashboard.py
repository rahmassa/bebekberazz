import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
import glob
import json
import base64
import urllib.request

try:
    import pydeck as pdk
except ImportError:
    pdk = None

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BebekBerazz Analytics",
    page_icon="🦆",
    layout="wide",
    initial_sidebar_state="expanded",
)

CATALOG_PATH = "databases/shared_catalog.ducklake"
COLOR_PALETTE = ['#F6C445', '#4299E1', '#F56565', '#48BB78', '#9F7AEA', '#ED8936']

# ---- Link sumber data -------------------------------------------------------
BPS_URL = "https://www.bps.go.id/id/statistics-table/2/Mjk1IzI=/rata-rata-harga-beras-di-tingkat-perdagangan-besar--grosir--indonesia.html"
PIHPS_URL = "https://www.bi.go.id/hargapangan/TabelHarga/ProdusenDaerah"
SP2KP_URL = "https://sp2kp.kemendag.go.id/statistik/area"

# ---- Pengaturan kartu sidebar (silakan diubah) ------------------------------
TEAM_NAME = "by calon pahlawan"
IMG_PATTERN = "assets/padi.*"
OVERLAY_A = 0.72
CARD_GRADIENT = "linear-gradient(135deg, #FFE08A 0%, #F6C445 45%, #D69E2E 100%)"

# ---- Pengaturan peta --------------------------------------------------------
# File lokal dicari lebih dulu: assets/indonesia_prov.geojson (atau .json)
GEOJSON_URLS = [
    "https://raw.githubusercontent.com/ans-4175/peta-indonesia-geojson/master/indonesia-prov.geojson",
    "https://raw.githubusercontent.com/superpikar/indonesia-geojson/master/indonesia-province-simple.json",
]
PRICE_SCALE = ["#FEF3C7", "#F6C445", "#ED8936", "#E53E3E", "#9B2C2C"]
CHANGE_SCALE = [[0, "#48BB78"], [0.5, "#4A5568"], [1, "#F56565"]]
PRICE_STOPS = PRICE_SCALE
CHANGE_STOPS = ["#48BB78", "#4A5568", "#F56565"]
CAT_COLORS = ["#48BB78", "#F6C445", "#E53E3E"]     # rendah, sedang, tinggi
ALL_JENIS = "Semua jenis"
MAP_BG = "#0B1623"
MAX_ELEV = 450000                                   # tinggi balok 3D maksimum (meter)

# -----------------------------------------------------------------------------
# 2. CSS GLOBAL
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    .block-container { padding-top: 3.5rem; max-width: 1300px; }
    .main-title { font-size: 2.2rem; font-weight: 800; color: #F6C445; margin-bottom: 0; line-height: 1.3; }
    .sub-title { font-size: 0.95rem; color: #A0AAB8; margin-bottom: 20px; }

    .metric-card {
        background: linear-gradient(135deg, #1E232A 0%, #161A1E 100%);
        border: 1px solid #2D3748;
        border-left: 4px solid #F6C445;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,.35);
        height: 100%;
        min-height: 118px;
    }
    .metric-label { font-size: .75rem; color: #A0AAB8; font-weight: 600;
                    text-transform: uppercase; letter-spacing: .05em; }
    .metric-value { font-size: 1.7rem; font-weight: 700; color: #FFF; margin-top: 4px; }
    .metric-value.small { font-size: 1.15rem; line-height: 1.5; padding: 4px 0; }
    .metric-sub   { font-size: .8rem; margin-top: 2px; }
    .up   { color: #FC8181; }
    .down { color: #68D391; }
    .flat { color: #A0AAB8; }

    .insight-box {
        background: #1A202C; border: 1px dashed #F6C445; border-radius: 10px;
        padding: 12px 16px; color: #E2E8F0; font-size: .92rem; margin: 10px 0 18px 0;
    }
    .section-note { color: #A0AAB8; font-size: .85rem; margin: -6px 0 10px 0; }

    /* ---------- Legenda peta ---------- */
    .legend { display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
              background: #111A27; border: 1px solid #1F2A3A; border-radius: 10px;
              padding: 10px 14px; margin-top: 8px; color: #CBD5E0; font-size: .8rem; }
    .legend .bar { height: 12px; width: 220px; border-radius: 6px; }
    .legend .chip { display: inline-flex; align-items: center; gap: 6px; }
    .legend .dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }

    /* ---------- Footer sumber data ---------- */
    .src-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 8px; }
    .src-row .lbl { color: #718096; font-size: .8rem; margin-right: 4px; }
    a.src-chip {
        background: #1A202C; border: 1px solid #2D3748; color: #F6C445 !important;
        border-radius: 999px; padding: 6px 14px; font-size: .8rem; font-weight: 600;
        text-decoration: none !important; transition: all .15s ease;
    }
    a.src-chip:hover { background: #F6C445; color: #1A1200 !important; border-color: #F6C445; }

    /* ---------- SIDEBAR ---------- */
    [data-testid="stSidebar"] { background-color: #12161C; border-right: 1px solid #1F2630; }

    .nav-label {
        font-size: .72rem; color: #718096; font-weight: 600;
        margin: 18px 0 4px 8px; letter-spacing: .04em;
    }
    .src-list { font-size: .85rem; line-height: 1.8; margin-left: 8px; color: #A0AAB8; }
    .src-list a { color: #CBD5E0 !important; text-decoration: none !important; }
    .src-list a:hover { color: #F6C445 !important; text-decoration: underline !important; }

    [data-testid="stSidebar"] .stButton > button {
        justify-content: flex-start;
        background: transparent;
        border: 1px solid transparent;
        color: #CBD5E0;
        border-radius: 10px;
        padding: .55rem .8rem;
        font-weight: 600;
        transition: all .15s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(246,196,69,.10);
        border-color: rgba(246,196,69,.25);
        color: #F6C445;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
        background: rgba(246,196,69,.16);
        border: 1px solid rgba(246,196,69,.45);
        color: #F6C445;
    }

    /* Kartu bawah sidebar */
    .side-card {
        position: relative; overflow: hidden;
        border-radius: 18px; padding: 16px;
        color: #2B1D00;
        box-shadow: 0 6px 18px rgba(0,0,0,.35);
    }
    .side-card .top { display: flex; align-items: center; gap: 10px; }
    .side-card .circle {
        width: 42px; height: 42px; border-radius: 50%;
        border: 1.5px solid rgba(43,29,0,.45);
        background: rgba(255,255,255,.35);
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; flex-shrink: 0;
    }
    .side-card .by   { font-size: .68rem; font-weight: 600; opacity: .85; line-height: 1.1; }
    .side-card .name { font-size: 1.15rem; font-weight: 800; line-height: 1.2; }
    .side-card .desc { font-size: .78rem; margin: 10px 0 10px 0; line-height: 1.35; font-weight: 500; }
    .side-card .hint { font-size: .66rem; font-weight: 600; opacity: .75; margin-bottom: 6px; }
    .side-card .pills { display: flex; gap: 6px; }
    .side-card a.pill {
        flex: 1; background: #FFFFFF; color: #2B1D00 !important;
        border-radius: 999px; text-align: center; padding: 8px 2px;
        font-weight: 800; font-size: .72rem; text-decoration: none !important;
        transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
    }
    .side-card a.pill:hover {
        transform: translateY(-2px); box-shadow: 0 5px 12px rgba(0,0,0,.30);
        background: #2B1D00; color: #FFE08A !important;
    }
    .side-card.mini { padding: 8px; display: flex; justify-content: center; }
    .side-card.mini .circle { width: 38px; height: 38px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. HELPER DATA & GRAFIK
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner="Memuat data...")
def load_data(query: str) -> pd.DataFrame:
    if not os.path.exists(CATALOG_PATH) or os.path.getsize(CATALOG_PATH) == 0:
        raise FileNotFoundError("Catalog belum siap. Jalankan `python src/transform.py` dulu.")
    conn = duckdb.connect(CATALOG_PATH, read_only=True)
    try:
        if os.path.exists("databases/bebek_grosir.duckdb"):
            conn.execute("ATTACH IF NOT EXISTS 'databases/bebek_grosir.duckdb' AS db_grosir (READ_ONLY);")
        if os.path.exists("databases/bebek_produksi.duckdb"):
            conn.execute("ATTACH IF NOT EXISTS 'databases/bebek_produksi.duckdb' AS db_produksi (READ_ONLY);")
        return conn.execute(query).df()
    finally:
        conn.close()


def safe_load(query: str) -> pd.DataFrame:
    try:
        return load_data(query)
    except Exception as e:
        st.error(f"⚠️ Gagal membaca data: {e}")
        st.stop()


def style_fig(fig, height=400, legend_bottom=True):
    fig.update_layout(
        template="plotly_dark", height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        title=dict(x=0, font=dict(size=16)),
    )
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", y=-0.2, x=0, title=None))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#2D3748", tickformat=",")
    return fig


def rp(x):
    return f"Rp {x:,.0f}"


def kpi(label, value, delta=None, note="", small=False):
    if delta is None:
        sub = f'<span class="flat">{note}</span>'
    else:
        cls = "up" if delta > 0.05 else "down" if delta < -0.05 else "flat"
        arrow = "▲" if delta > 0.05 else "▼" if delta < -0.05 else "■"
        sub = f'<span class="{cls}">{arrow} {abs(delta):.1f}% vs bulan lalu</span>'
    size_cls = "metric-value small" if small else "metric-value"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="{size_cls}">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)


def insight(text):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)


def pct_change(series, periods=None):
    if len(series) < 2 or series.iloc[-2] == 0:
        return None
    if periods is not None:
        if periods.iloc[-1] - pd.DateOffset(months=1) != periods.iloc[-2]:
            return None
    if pd.isna(series.iloc[-2]) or pd.isna(series.iloc[-1]):
        return None
    return (series.iloc[-1] - series.iloc[-2]) / series.iloc[-2] * 100


MONTH_NAMES = dict(enumerate([
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
], 1))


def with_period(df):
    """Tambahkan periode tanpa mengubah tahun dan bulan sumber."""
    d = df.copy()
    d['periode'] = pd.to_datetime(dict(year=d['tahun'], month=d['bulan_num'], day=1))
    d['periode_label'] = d['periode'].dt.month.map(MONTH_NAMES) + ' ' + d['periode'].dt.year.astype(str)
    return d.sort_values('periode').reset_index(drop=True)


def month_order(df):
    return df.sort_values('periode').drop_duplicates('periode')['periode_label'].tolist()


def month_map(df):
    return df.drop_duplicates('periode').set_index('periode_label')['periode'].to_dict()


def style_period_fig(fig, height=500, legend_bottom=True):
    fig = style_fig(fig, height, legend_bottom)
    fig.update_xaxes(type='date', dtick='M1', tickformat='%b %Y',
                     tickangle=-45, tickfont=dict(size=10), hoverformat='%B %Y')
    fig.update_layout(xaxis_title='Periode', margin=dict(l=10, r=10, t=50, b=110))
    if legend_bottom:
        fig.update_layout(legend=dict(orientation='h', y=-0.35, x=0, title=None))
    return fig


def source_footer():
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"""
        <div class="src-row">
            <span class="lbl">📚 Sumber data:</span>
            <a class="src-chip" href="{BPS_URL}" target="_blank" rel="noopener">🏭 BPS · Grosir ↗</a>
            <a class="src-chip" href="{PIHPS_URL}" target="_blank" rel="noopener">🏬 PIHPS · Provinsi ↗</a>
            <a class="src-chip" href="{SP2KP_URL}" target="_blank" rel="noopener">🛒 SP2KP · Pasar ↗</a>
        </div>""", unsafe_allow_html=True)


@st.cache_data
def load_card_image(pattern: str) -> str:
    files = sorted(glob.glob(pattern))
    if not files:
        return ""
    path = files[0]
    ext = os.path.splitext(path)[1].lower().strip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext)
    if mime is None:
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/{mime};base64,{b64}"


def card_background() -> str:
    img = load_card_image(IMG_PATTERN)
    if img:
        overlay = (f"linear-gradient(135deg, rgba(255,224,138,{OVERLAY_A}), "
                   f"rgba(214,158,46,{min(OVERLAY_A + .1, 1)}))")
        return f"{overlay}, url('{img}') center/cover no-repeat"
    return CARD_GRADIENT

# -----------------------------------------------------------------------------
# 3b. HELPER PETA 3D (pydeck)
# -----------------------------------------------------------------------------
ALIAS = {
    "DI ACEH": "ACEH", "NANGGROE ACEH DARUSSALAM": "ACEH", "NAD": "ACEH",
    "YOGYAKARTA": "DI YOGYAKARTA", "DIY": "DI YOGYAKARTA",
    "BANGKA BELITUNG": "KEPULAUAN BANGKA BELITUNG",
    "JAKARTA": "DKI JAKARTA", "JAKARTA RAYA": "DKI JAKARTA",
    "IRIAN JAYA BARAT": "PAPUA BARAT", "IRIAN JAYA": "PAPUA",
    "NTB": "NUSA TENGGARA BARAT", "NTT": "NUSA TENGGARA TIMUR",
    "NUSATENGGARA BARAT": "NUSA TENGGARA BARAT", "NUSATENGGARA TIMUR": "NUSA TENGGARA TIMUR",
}

# Titik tengah provinsi (dipakai kalau file batas wilayah gagal dimuat)
COORDS = {
    "ACEH": (4.7, 96.7), "SUMATERA UTARA": (2.1, 99.5), "SUMATERA BARAT": (-0.7, 100.8),
    "RIAU": (0.5, 101.5), "JAMBI": (-1.6, 103.6), "SUMATERA SELATAN": (-3.3, 104.0),
    "BENGKULU": (-3.8, 102.3), "LAMPUNG": (-4.9, 105.0),
    "KEPULAUAN BANGKA BELITUNG": (-2.7, 106.5), "KEPULAUAN RIAU": (3.9, 108.1),
    "DKI JAKARTA": (-6.2, 106.8), "JAWA BARAT": (-6.9, 107.6), "JAWA TENGAH": (-7.2, 110.0),
    "DI YOGYAKARTA": (-7.9, 110.4), "JAWA TIMUR": (-7.7, 112.8), "BANTEN": (-6.4, 106.1),
    "BALI": (-8.4, 115.2), "NUSA TENGGARA BARAT": (-8.6, 117.4),
    "NUSA TENGGARA TIMUR": (-9.6, 121.0), "KALIMANTAN BARAT": (0.0, 110.8),
    "KALIMANTAN TENGAH": (-1.7, 113.4), "KALIMANTAN SELATAN": (-3.1, 115.3),
    "KALIMANTAN TIMUR": (0.8, 116.5), "KALIMANTAN UTARA": (3.0, 116.5),
    "SULAWESI UTARA": (0.9, 124.5), "SULAWESI TENGAH": (-1.4, 121.4),
    "SULAWESI SELATAN": (-3.7, 120.0), "SULAWESI TENGGARA": (-4.1, 122.1),
    "GORONTALO": (0.6, 122.4), "SULAWESI BARAT": (-2.5, 119.4),
    "MALUKU": (-3.2, 129.5), "MALUKU UTARA": (1.6, 127.8),
    "PAPUA BARAT": (-1.3, 133.0), "PAPUA BARAT DAYA": (-1.1, 132.0), "PAPUA": (-4.0, 138.0),
    "PAPUA TENGAH": (-3.9, 136.0), "PAPUA PEGUNUNGAN": (-4.1, 139.0),
    "PAPUA SELATAN": (-7.5, 139.5),
}


def norm(name) -> str:
    """Samakan penulisan nama provinsi: 'DI. ACEH' -> 'ACEH', 'Kep. Riau' -> 'KEPULAUAN RIAU'."""
    s = str(name).upper()
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace(".", " ").replace(",", " ").replace("-", " ")
    s = " ".join(s.split())
    for pre in ("PROVINSI ", "PROV "):
        if s.startswith(pre):
            s = s[len(pre):]
    s = s.replace("KEP ", "KEPULAUAN ").replace("DAERAH ISTIMEWA ", "DI ")
    return ALIAS.get(s, s)


def key_of(name) -> str:
    """Kunci pencocokan: huruf besar tanpa spasi/tanda baca."""
    return re.sub(r"[^A-Z0-9]", "", norm(name))


@st.cache_data(ttl=600, show_spinner="Memuat peta Indonesia...")
def load_geojson():
    """Cari file lokal dulu, kalau tidak ada baru unduh dari internet."""
    local = (sorted(glob.glob("assets/indonesia_prov*.geojson"))
             + sorted(glob.glob("assets/indonesia_prov*.json")))
    for p in local:
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    for url in GEOJSON_URLS:
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            continue
    return None


@st.cache_data(show_spinner=False)
def feature_centers(_geo):
    """Titik tengah (lon, lat) tiap wilayah, diambil dari daratan terbesarnya (untuk label nama)."""
    out = []
    for f in _geo.get("features", []):
        g = f.get("geometry") or {}
        polys = g.get("coordinates", [])
        if g.get("type") == "Polygon":
            polys = [polys]
        elif g.get("type") != "MultiPolygon":
            out.append((None, None))
            continue
        best, area = (None, None), -1
        for p in polys:
            try:
                ring = p[0]
                xs, ys = [c[0] for c in ring], [c[1] for c in ring]
                a = (max(xs) - min(xs)) * (max(ys) - min(ys))
                if a > area:
                    area = a
                    best = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
            except Exception:
                continue
        out.append(best)
    return out


def pick_geo(geo, provinces):
    """Pilih properti GeoJSON yang namanya paling cocok dengan data provinsi."""
    feats = geo.get("features", []) if geo else []
    if not feats:
        return None
    want = {key_of(p) for p in provinces}
    best, score = None, 0
    for k in feats[0].get("properties", {}):
        names = {key_of(f["properties"][k]) for f in feats
                 if isinstance(f.get("properties", {}).get(k), str)}
        s = len(want & names)
        if s > score:
            best, score = k, s
    return best


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def grad(stops, t):
    """Warna (r,g,b) pada posisi t (0..1) di sepanjang daftar warna hex."""
    t = min(max(t, 0.0), 1.0)
    n = len(stops) - 1
    i = min(int(t * n), n - 1)
    f = t * n - i
    a, b = hex_rgb(stops[i]), hex_rgb(stops[i + 1])
    return [round(a[k] + (b[k] - a[k]) * f) for k in range(3)]


def make_deck(dfv, label, fmt, midpoint, highlight, height, style, three_d, show_names):
    """Bangun peta 3D. Return (deck, unmatched, no_data, legend_html) atau (None, ...) kalau gagal."""
    geo = load_geojson()
    prop = pick_geo(geo, dfv["provinsi"]) if geo else None
    if not prop or pdk is None:
        return None, [], [], ""

    is_change = (midpoint == 0)
    d = dfv.dropna(subset=["nilai"]).copy()
    d["k"] = d["provinsi"].map(key_of)
    d = d.drop_duplicates("k")
    if d.empty:
        return None, [], [], ""

    val = dict(zip(d["k"], d["nilai"]))
    name_of = dict(zip(d["k"], d["provinsi"]))
    rank_of = dict(zip(d["k"], d["nilai"].rank(ascending=False, method="min").astype(int)))
    total = len(d)
    lo, hi = float(d["nilai"].min()), float(d["nilai"].max())
    mabs = max(abs(lo), abs(hi)) or 1.0

    # ---- kategori (opsional) ----
    cat_names, cat_cols, cuts = [], [], None
    if style == "kategori":
        if is_change:
            cuts = (-0.1, 0.1)
            cat_names = ["Turun (< -0.1%)", "Stabil (±0.1%)", "Naik (> +0.1%)"]
            cat_cols = ["#48BB78", "#718096", "#F56565"]
        else:
            q1, q2 = d["nilai"].quantile([1 / 3, 2 / 3])
            if q2 <= q1:
                q2 = q1 + 1e-9
            cuts = (q1, q2)
            cat_names = [f"Rendah (< {q1:,.0f})", f"Sedang ({q1:,.0f} – {q2:,.0f})",
                         f"Tinggi (> {q2:,.0f})"]
            cat_cols = CAT_COLORS

    hk = key_of(highlight) if highlight else None
    centers = feature_centers(geo)
    feats, texts, no_data, used = [], [], [], set()

    for f, (lon, lat) in zip(geo["features"], centers):
        raw = str(f["properties"].get(prop, ""))
        k = key_of(raw)
        v = val.get(k)
        nm = name_of.get(k, raw.title())

        if v is None:
            fill, elev, vtxt, rk = [45, 55, 72, 210], 0, "Tidak ada data", "-"
            no_data.append(raw.title())
        else:
            used.add(k)
            v = float(v)
            if style == "kategori":
                idx = 0 if v < cuts[0] else (1 if v <= cuts[1] else 2)
                rgb = hex_rgb(cat_cols[idx])
            elif is_change:
                rgb = grad(CHANGE_STOPS, 0.5 + 0.5 * v / mabs)
            else:
                rgb = grad(PRICE_STOPS, (v - lo) / (hi - lo) if hi > lo else 0.5)
            fill = rgb + [235]
            th = abs(v) / mabs if is_change else ((v - lo) / (hi - lo) if hi > lo else 0.5)
            elev = (0.12 + 0.88 * th) * MAX_ELEV if three_d else 0
            vtxt = f"{v:+.2f}%" if is_change else f"Rp {v:,.0f}/kg"
            rk = f"{rank_of[k]} dari {total}"

        is_hl = (hk is not None and k == hk)
        if is_hl and three_d:
            elev *= 1.15

        feats.append({
            "type": "Feature",
            "geometry": f["geometry"],
            "properties": {
                "name": nm, "vtxt": vtxt, "rank": rk,
                "fill": fill, "elev": float(elev),
                "line": [255, 255, 255, 255] if is_hl else [11, 22, 35, 255],
                "lw": 4 if is_hl else 1,
            },
        })
        if lon is not None:
            texts.append({"name": nm, "lon": lon, "lat": lat, "z": float(elev) + 15000})

    unmatched = sorted(set(d.loc[~d["k"].isin(used), "provinsi"]))

    layers = [pdk.Layer(
        "GeoJsonLayer",
        data={"type": "FeatureCollection", "features": feats},
        pickable=True, stroked=True, filled=True,
        extruded=three_d, wireframe=False,
        get_fill_color="properties.fill",
        get_line_color="properties.line",
        get_line_width="properties.lw",
        line_width_units="pixels",
        get_elevation="properties.elev",
        auto_highlight=True, highlight_color=[255, 255, 255, 70],
    )]
    if show_names and texts:
        layers.append(pdk.Layer(
            "TextLayer",
            data=pd.DataFrame(texts),
            get_position="[lon, lat, z]",
            get_text="name", get_size=12,
            get_color=[255, 255, 255, 240],
            get_text_anchor="'middle'", get_alignment_baseline="'center'",
            billboard=True, pickable=False,
            parameters={"depthTest": False},
        ))

    view = pdk.ViewState(latitude=-2.3, longitude=118.0, zoom=3.3,
                         pitch=55 if three_d else 0, bearing=-8 if three_d else 0)
    tooltip = {
        "html": "<div style='font-family:sans-serif'><b style='font-size:14px'>{name}</b>"
                f"<br/>{label}: <b>{{vtxt}}</b><br/>Peringkat: {{rank}}</div>",
        "style": {"backgroundColor": "#111A27", "color": "#E2E8F0",
                  "border": "1px solid #F6C445", "borderRadius": "8px", "padding": "8px 10px"},
    }
    deck = pdk.Deck(layers=layers, initial_view_state=view, map_style="dark",
                    tooltip=tooltip, height=height)

    # ---- legenda ----
    if style == "kategori":
        chips = "".join(f'<span class="chip"><span class="dot" style="background:{c}"></span>{n}</span>'
                        for n, c in zip(cat_names, cat_cols))
        legend = f'<div class="legend"><b>{label}</b> {chips}' \
                 f'<span class="chip"><span class="dot" style="background:#2D3748"></span>Tidak ada data</span></div>'
    else:
        stops = CHANGE_STOPS if is_change else PRICE_STOPS
        lo_t = f"{lo:+.2f}%" if is_change else f"{lo:,.0f}"
        hi_t = f"{hi:+.2f}%" if is_change else f"{hi:,.0f}"
        legend = (f'<div class="legend"><b>{label}</b> <span>{lo_t}</span>'
                  f'<div class="bar" style="background:linear-gradient(90deg,{",".join(stops)})"></div>'
                  f'<span>{hi_t}</span>'
                  f'<span class="chip"><span class="dot" style="background:#2D3748"></span>Tidak ada data</span></div>')
    return deck, unmatched, no_data, legend


def fallback_map(dfv, label, fmt, scale, midpoint, highlight, height):
    """Peta titik sederhana (tanpa GeoJSON/pydeck)."""
    d = dfv.dropna(subset=["nilai"]).copy()
    d["lat"] = d["provinsi"].map(lambda p: COORDS.get(norm(p), (None, None))[0])
    d["lon"] = d["provinsi"].map(lambda p: COORDS.get(norm(p), (None, None))[1])
    miss = d[d["lat"].isna()]["provinsi"].tolist()
    d = d.dropna(subset=["lat"])
    fig = px.scatter_geo(d, lat="lat", lon="lon", color="nilai", color_continuous_scale=scale,
                         color_continuous_midpoint=midpoint, hover_name="provinsi",
                         hover_data={"nilai": f":{fmt}", "lat": False, "lon": False},
                         labels={"nilai": label})
    fig.update_traces(marker=dict(size=17, line=dict(width=1, color=MAP_BG)))
    fig.update_geos(fitbounds="locations", projection_type="mercator", showland=True,
                    landcolor="#1A202C", showocean=True, oceancolor=MAP_BG,
                    showcountries=True, countrycolor="#2D3748", showframe=False, bgcolor=MAP_BG)
    fig.update_layout(template="plotly_dark", height=height, paper_bgcolor=MAP_BG,
                      margin=dict(l=0, r=0, t=10, b=0), font=dict(color="#E2E8F0"))
    return fig, miss


def show_map(dfv, label, fmt=",.0f", scale=PRICE_SCALE, midpoint=None, highlight=None, height=520):
    sk = "prov" if highlight else "home"          # supaya key widget tidak bentrok

    c1, c2, c3 = st.columns([3, 1.3, 1.5])
    with c1:
        pilih = st.radio("Gaya warna peta:", ["🌈 Gradasi", "🎯 Kategori (Rendah/Sedang/Tinggi)"],
                         horizontal=True, key=f"{sk}_map_style")
    with c2:
        three_d = st.toggle("Mode 3D", value=True, key=f"{sk}_map_3d")
    with c3:
        names = st.toggle("Nama provinsi", value=True, key=f"{sk}_map_names")
    style = "kategori" if pilih.startswith("🎯") else "gradasi"

    if pdk is None:
        st.error("Library **pydeck** belum terpasang. Jalankan `pip install pydeck` di terminal, "
                 "lalu restart Streamlit. Sementara ini ditampilkan peta titik.")
    deck, unmatched, no_data, legend = make_deck(dfv, label, fmt, midpoint, highlight,
                                                 height, style, three_d, names)
    if deck is not None:
        try:
            st.pydeck_chart(deck, use_container_width=True, height=height)
        except TypeError:
            st.pydeck_chart(deck, use_container_width=True)
        st.markdown(legend, unsafe_allow_html=True)
        tips = ("🖱️ Scroll = zoom · Drag = geser · **Ctrl + drag** (atau klik kanan + drag) = putar & miringkan · "
                "Arahkan kursor ke provinsi untuk detail") if three_d else \
               "🖱️ Scroll = zoom · Drag = geser · Arahkan kursor ke provinsi untuk detail"
        st.caption(tips)
    else:
        fig, unmatched = fallback_map(dfv, label, fmt, scale, midpoint, highlight, height)
        st.plotly_chart(fig, use_container_width=True, theme=None)
        st.caption("⚠️ Peta 3D belum bisa dibuat (pydeck belum terpasang atau file batas wilayah gagal dimuat). "
                   "Simpan GeoJSON provinsi Indonesia sebagai `assets/indonesia_prov.geojson`.")
        no_data = []

    if unmatched or no_data:
        with st.expander("ℹ️ Cek kecocokan nama provinsi"):
            if unmatched:
                st.markdown("**Ada di datamu tapi tidak ketemu di peta:**")
                st.write(", ".join(unmatched))
            if no_data:
                st.markdown("**Ada di peta tapi tidak ada datanya (abu-abu):**")
                st.write(", ".join(no_data))


def prov_values(df, jenis_list, periode):
    """Rata-rata harga per provinsi pada satu bulan -> kolom: provinsi, nilai."""
    d = df[df["periode"] == periode]
    if jenis_list:
        d = d[d["jenis_beras"].isin(jenis_list)]
    return (d.groupby("provinsi")["avg_harga"].mean().reset_index()
             .rename(columns={"avg_harga": "nilai"}))


def prov_change(df, jenis_list, periode):
    """Bandingkan dengan bulan kalender sebelumnya, termasuk lintas tahun."""
    prev = pd.Timestamp(periode) - pd.DateOffset(months=1)
    cur = prov_values(df, jenis_list, periode)
    old = prov_values(df, jenis_list, prev).rename(columns={"nilai": "lama"})
    if old.empty:
        return None
    m = cur.merge(old, on="provinsi")
    m = m[m["lama"] > 0]
    m["nilai"] = (m["nilai"] - m["lama"]) / m["lama"] * 100
    return m[["provinsi", "nilai"]]

# -----------------------------------------------------------------------------
# 4. SIDEBAR
# -----------------------------------------------------------------------------
PAGES = [
    ("home",   "Ringkasan Nasional", ":material/dashboard:"),
    ("prov",   "Analisis Provinsi",  ":material/map:"),
    ("market", "Jelajah Pasar",      ":material/storefront:"),
    ("gap",    "Selisih Harga",      ":material/compare_arrows:"),
]

if "page" not in st.session_state:
    st.session_state.page = "home"
if "compact" not in st.session_state:
    st.session_state.compact = False


# CATATAN: jangan beri nama fungsi "go" -> bentrok dengan plotly.graph_objects as go
def set_page(key):
    st.session_state.page = key


def toggle_compact():
    st.session_state.compact = not st.session_state.compact


compact = st.session_state.compact

if compact:
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            width: 84px !important; min-width: 84px !important; max-width: 84px !important;
        }
        [data-testid="stSidebar"] .stButton > button { justify-content: center; padding: .55rem .4rem; }
        [data-testid="stSidebar"] .stButton > button [data-testid="stMarkdownContainer"] { display: none; }
        [data-testid="stSidebar"] .stButton > button span { margin: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    if compact:
        st.image("https://img.icons8.com/emoji/96/duck-emoji.png", width=40)
        st.button("", icon=":material/chevron_right:", key="toggle",
                  on_click=toggle_compact, help="Lebarkan sidebar", use_container_width=True)
    else:
        h1, h2 = st.columns([5, 1])
        with h1:
            st.image("https://img.icons8.com/emoji/96/duck-emoji.png", width=56)
            st.markdown("### BebekBerazz")
            st.caption("Data Warehouse & Rice Price Intelligence")
        with h2:
            st.button("", icon=":material/chevron_left:", key="toggle",
                      on_click=toggle_compact, help="Ciutkan sidebar")

    if not compact:
        st.markdown('<div class="nav-label">Menu</div>', unsafe_allow_html=True)
    for key, label, icon in PAGES:
        st.button(
            label, icon=icon, key=f"nav_{key}",
            on_click=set_page, args=(key,),
            type="primary" if st.session_state.page == key else "secondary",
            use_container_width=True, help=label,
        )

    if not compact:
        st.markdown('<div class="nav-label">Sumber data</div>', unsafe_allow_html=True)
        st.markdown(
            f"<div class='src-list'>"
            f"🏭 <a href='{BPS_URL}' target='_blank' rel='noopener'><b>BPS</b></a> → harga grosir<br>"
            f"🏬 <a href='{PIHPS_URL}' target='_blank' rel='noopener'><b>PIHPS</b></a> → harga provinsi<br>"
            f"🛒 <a href='{SP2KP_URL}' target='_blank' rel='noopener'><b>SP2KP</b></a> → harga pasar</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    bg = card_background()
    if compact:
        st.markdown(
            f'<div class="side-card mini" style="background:{bg}">'
            f'<div class="circle">🌾</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"""
        <div class="side-card" style="background:{bg}">
            <div class="top">
                <div class="circle">🌾</div>
                <div>
                    <div class="by">{TEAM_NAME}</div>
                    <div class="name">BebekBerazz</div>
                </div>
            </div>
            <div class="desc">Pantau harga beras dari grosir sampai pasar, dalam satu dashboard.</div>
            <div class="hint">Klik untuk buka sumber data ↗</div>
            <div class="pills">
                <a class="pill" href="{BPS_URL}" target="_blank" rel="noopener" title="BPS: harga grosir">BPS</a>
                <a class="pill" href="{PIHPS_URL}" target="_blank" rel="noopener" title="PIHPS BI: harga provinsi">PIHPS</a>
                <a class="pill" href="{SP2KP_URL}" target="_blank" rel="noopener" title="SP2KP Kemendag: harga pasar">SP2KP</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

menu = st.session_state.page

# -----------------------------------------------------------------------------
# 5. HEADER HALAMAN
# -----------------------------------------------------------------------------
st.markdown('<p class="main-title">🦆 BebekBerazz Analytics</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Pemantauan harga beras Indonesia dari tingkat grosir hingga pasar</p>',
            unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HALAMAN 1: RINGKASAN NASIONAL
# -----------------------------------------------------------------------------
if menu == "home":
    st.subheader("🏠 Ringkasan Nasional")

    try:
        df_grosir = load_data(
            "SELECT * FROM db_grosir.harga_nasional_bulanan ORDER BY tahun, bulan_num"
        )
    except Exception:
        df_grosir = pd.DataFrame(
            columns=['tahun', 'bulan_num', 'bulan_nama', 'harga']
        )

    df_prov = safe_load(
        "SELECT * FROM province_summary ORDER BY tahun, bulan_num"
    )

    df_prov = with_period(df_prov)
    df_grosir = with_period(df_grosir)
    if df_prov.empty:
        st.warning("Data ritel belum tersedia.")
        st.stop()

    ritel_bulan = (
        df_prov.groupby(['periode', 'tahun', 'bulan_num', 'bulan_nama', 'periode_label'])['avg_harga']
        .mean().reset_index().sort_values('periode')
    )

    # Mengambil periode terbaru
    last_m = df_prov['periode'].max()

    last_prov = (
        df_prov[df_prov['periode'] == last_m]
        .groupby('provinsi')['avg_harga']
        .mean()
        .sort_values(ascending=False)
    )

    grosir_last = df_grosir['harga'].iloc[-1] if not df_grosir.empty else 0
    ritel_last = ritel_bulan['avg_harga'].iloc[-1]
    common = ritel_bulan.merge(df_grosir[['periode', 'harga']], on='periode', how='inner').dropna(subset=['avg_harga', 'harga'])
    common = common.sort_values('periode')
    gap_last = common['avg_harga'].iloc[-1] - common['harga'].iloc[-1] if not common.empty else None
    gap_note = f"Periode: {common['periode_label'].iloc[-1]}" if not common.empty else "Tidak ada periode yang cocok"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Grosir Nasional (terbaru)", rp(grosir_last),
            pct_change(df_grosir['harga'], df_grosir['periode']) if not df_grosir.empty else None)
    with c2:
        kpi("Rata-rata Ritel Provinsi", rp(ritel_last), pct_change(ritel_bulan['avg_harga'], ritel_bulan['periode']))
    with c3:
        kpi("Selisih Ritel − Grosir",
            rp(gap_last) if gap_last is not None else "-",
            note=gap_note)
    with c4:
        kpi("Provinsi Termahal", last_prov.index[0],
            note=f"{rp(last_prov.iloc[0])}/kg", small=True)

    if len(ritel_bulan) >= 2:
        first, last = ritel_bulan['avg_harga'].iloc[0], ritel_bulan['avg_harga'].iloc[-1]
        arah = "naik" if last > first else "turun"
        insight(f"Sejak <b>{ritel_bulan['periode_label'].iloc[0]}</b> hingga "
                f"<b>{ritel_bulan['periode_label'].iloc[-1]}</b>, harga ritel rata-rata <b>{arah} "
                f"{abs(last-first)/first*100:.1f}%</b>. Provinsi termurah saat ini: "
                f"<b>{last_prov.index[-1]}</b> ({rp(last_prov.iloc[-1])}/kg).")

    # ------------------------- PETA NASIONAL 3D -------------------------
    st.markdown("##### 🗺️ Peta Harga Beras Nasional (3D)")
    st.markdown('<p class="section-note">Makin tinggi dan makin merah balok provinsi = makin mahal harga berasnya. '
                'Arahkan kursor ke provinsi untuk melihat detail.</p>', unsafe_allow_html=True)

    bulan_opts = month_order(df_prov)
    bmap = month_map(df_prov)
    jenis_all = sorted(df_prov['jenis_beras'].unique())

    m1, m2, m3 = st.columns(3)
    with m1:
        bulan_sel = st.selectbox("Periode:", bulan_opts, index=len(bulan_opts) - 1, key="home_bulan")
    with m2:
        mode_sel = st.selectbox("Tampilkan:", ["Harga rata-rata (Rp/kg)", "Perubahan vs bulan lalu (%)"],
                                key="home_mode")
    with m3:
        jenis_sel = st.selectbox("Jenis beras:", [ALL_JENIS] + jenis_all, key="home_jenis")

    jenis_filter = None if jenis_sel == ALL_JENIS else [jenis_sel]
    periode_sel = bmap[bulan_sel]

    is_change = mode_sel.startswith("Perubahan")
    vals = None
    if is_change:
        vals = prov_change(df_prov, jenis_filter, periode_sel)
        if vals is None or vals.empty:
            st.info("Data bulan sebelumnya tidak tersedia, jadi ditampilkan harga rata-rata.")
            is_change = False
    if not is_change:
        vals = prov_values(df_prov, jenis_filter, periode_sel)

    if is_change:
        label, fmt, scale, mid = "Perubahan (%)", "+.2f", CHANGE_SCALE, 0
        fmt_txt = lambda v: f"{v:+.2f}%"
    else:
        label, fmt, scale, mid = "Rp/kg", ",.0f", PRICE_SCALE, None
        fmt_txt = lambda v: f"{v:,.0f}"

    if vals.empty:
        st.info("Tidak ada data untuk jenis beras dan periode pilihan.")
    else:
        show_map(vals, label, fmt=fmt, scale=scale, midpoint=mid, height=600)
    st.caption(f"📅 {bulan_sel} · {jenis_sel}")

    # ------------------------- PERINGKAT -------------------------
    asc = vals.sort_values("nilai")
    top5 = asc.tail(5)
    bot5 = asc.head(5).sort_values("nilai", ascending=False)
    rk1, rk2 = st.columns(2)
    for col, d, color, ttl in [(rk1, top5, "#F56565", "🔺 5 Provinsi Tertinggi"),
                               (rk2, bot5, "#48BB78", "🔻 5 Provinsi Terendah")]:
        with col:
            f = px.bar(d, x='nilai', y='provinsi', orientation='h',
                       text=d['nilai'].map(fmt_txt), title=ttl)
            f.update_traces(marker_color=color, textposition="inside")
            f.update_layout(xaxis_title=label, yaxis_title=None, hovermode="closest")
            if not is_change and not d.empty:
                f.update_xaxes(range=[d['nilai'].min() * 0.9, d['nilai'].max() * 1.02])
            st.plotly_chart(style_fig(f, 300, False), use_container_width=True)

      # ------------------------- TREN -------------------------
    st.markdown("<br>", unsafe_allow_html=True)

    # Rentang periode penuh dari gabungan data grosir & ritel
    semua_periode = pd.concat([df_grosir['periode'], ritel_bulan['periode']]).dropna()
    min_periode = semua_periode.min()
    max_periode = semua_periode.max()

    full_periods = pd.DataFrame({
        'periode': pd.date_range(start=min_periode, end=max_periode, freq='MS')
    })

    # Merge grosir ke timeline penuh
    grosir_plot = full_periods.merge(
        df_grosir[['periode', 'harga']],
        on='periode',
        how='left'
    )

    # Merge ritel ke timeline penuh
    ritel_plot = full_periods.merge(
        ritel_bulan[['periode', 'avg_harga']],
        on='periode',
        how='left'
    )

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=grosir_plot['periode'],
        y=grosir_plot['harga'],
        name="Grosir (BPS)",
        mode="lines+markers",
        line=dict(color="#F6C445", width=3),
        fill="tozeroy",
        fillcolor="rgba(246,196,69,.08)",
        connectgaps=False
    ))

    fig.add_trace(go.Scatter(
        x=ritel_plot['periode'],
        y=ritel_plot['avg_harga'],
        name="Ritel Provinsi (PIHPS)",
        mode="lines+markers",
        line=dict(color="#4299E1", width=3),
        connectgaps=False
    ))

    fig.update_layout(
        title="Tren Harga: Grosir vs Ritel (Rp/kg)",
        xaxis_title="Periode",
        yaxis_title="Harga (Rp/kg)"
    )

    fig.update_xaxes(
        type="date",
        dtick="M1",
        tickformat="%b %Y",
        tickangle=-45,
        hoverformat="%B %Y",
        tickfont=dict(size=10)
    )

    ys = []
    if 'harga' in grosir_plot.columns:
        ys += list(grosir_plot['harga'].dropna())
    if 'avg_harga' in ritel_plot.columns:
        ys += list(ritel_plot['avg_harga'].dropna())

    if ys:
        fig.update_yaxes(range=[min(ys) * 0.97, max(ys) * 1.03])

    fig = style_fig(fig, 470)
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=110),
        legend=dict(orientation="h", y=-0.35, x=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # ------------------------- PRODUKSI BERAS NASIONAL -------------------------
    try:
        df_prod = load_data("SELECT * FROM db_produksi.produksi_beras ORDER BY periode")
    except Exception:
        df_prod = pd.DataFrame(columns=['tahun', 'bulan_num', 'bulan_nama', 'produksi_ton'])

    if not df_prod.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("##### 🌾 Produksi Beras Nasional Bulanan (BDSP)")
        st.markdown(
            '<p class="section-note">Gambaran pasokan dan pola musim panen beras nasional '
            '(dalam satuan ton).</p>',
            unsafe_allow_html=True,
        )

        tahun_opts = sorted(df_prod['tahun'].unique())
        py1, _ = st.columns([1, 3])
        with py1:
            tahun_prod_sel = st.selectbox(
                "Tahun Produksi:",
                tahun_opts,
                index=len(tahun_opts) - 1,
                key="home_tahun_prod",
            )

        dp = df_prod[df_prod['tahun'] == tahun_prod_sel].sort_values('bulan_num')

        total_prod = dp['produksi_ton'].sum()
        puncak_row = dp.loc[dp['produksi_ton'].idxmax()]
        terendah_row = dp.loc[dp['produksi_ton'].idxmin()]

        pk1, pk2, pk3 = st.columns(3)
        with pk1:
            kpi(f"Total Produksi ({tahun_prod_sel})", f"{total_prod:,.0f} ton",
                note=f"Rata-rata {dp['produksi_ton'].mean():,.0f} ton/bulan")
        with pk2:
            kpi("Puncak Panen (Tertinggi)", puncak_row['bulan_nama'],
                note=f"{puncak_row['produksi_ton']:,.0f} ton", small=True)
        with pk3:
            kpi("Produksi Terendah (Paceklik)", terendah_row['bulan_nama'],
                note=f"{terendah_row['produksi_ton']:,.0f} ton", small=True)

        insight(
            f"Pada tahun <b>{tahun_prod_sel}</b>, puncak produksi beras nasional terjadi pada bulan "
            f"<b>{puncak_row['bulan_nama']}</b> ({puncak_row['produksi_ton']:,.0f} ton) dan "
            f"titik terendah pada bulan <b>{terendah_row['bulan_nama']}</b> "
            f"({terendah_row['produksi_ton']:,.0f} ton)."
        )

        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(
            x=dp['bulan_nama'],
            y=dp['produksi_ton'],
            name="Produksi (Ton)",
            marker_color="#48BB78",
            text=dp['produksi_ton'].map(lambda v: f"{v/1e6:.2f} jt"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:,.2f} ton<extra></extra>",
        ))
        fig_prod.add_trace(go.Scatter(
            x=dp['bulan_nama'],
            y=dp['produksi_ton'],
            name="Tren Bulanan",
            mode="lines+markers",
            line=dict(color="#F6C445", width=2.5),
            hoverinfo="skip",
        ))
        fig_prod.update_layout(
            title=f"Tren Produksi Beras Nasional Tahun {tahun_prod_sel} (Ton)",
            xaxis_title="Bulan",
            yaxis_title="Produksi (Ton)",
        )
        fig_prod.update_yaxes(range=[0, dp['produksi_ton'].max() * 1.15])
        st.plotly_chart(style_fig(fig_prod, 400), use_container_width=True)

        # ---------------- PERBANDINGAN PRODUKSI & HARGA PASAR ----------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("##### 📊 Perbandingan Produksi Beras dan Harga Pasar")
        st.markdown(
            '<p class="section-note">Harga pasar dihitung sebagai rata-rata '
            'harga Beras Medium dari pasar yang tercatat pada bulan yang sama.</p>',
            unsafe_allow_html=True,
        )

        try:
            df_market_cmp = load_data("SELECT * FROM market_summary")
        except Exception as e:
            df_market_cmp = pd.DataFrame()
            st.warning(f"Data harga pasar belum dapat dibaca: {e}")

        # Pencocokan hanya valid jika data harga pasar memiliki kolom tahun.
        if df_market_cmp.empty:
            st.info("Data harga pasar belum tersedia untuk dibandingkan.")
        elif "tahun" not in df_market_cmp.columns:
            st.warning(
                "Perbandingan belum dihitung karena tabel market_summary belum memiliki "
                "kolom tahun. Kolom tahun diperlukan agar Februari 2024 tidak tercampur "
                "dengan Februari 2025. Tambahkan tahun pada proses transformasi data SP2KP."
            )
        else:
            # Pilih kategori Medium sebagai pembanding utama.
            medium_mask = df_market_cmp["jenis_beras"].astype(str).str.contains(
                "medium", case=False, na=False
            )
            df_medium = df_market_cmp.loc[medium_mask].copy()

            if df_medium.empty:
                st.warning(
                    "Kategori Beras Medium tidak ditemukan pada data pasar. "
                    "Periksa penamaan pada kolom jenis_beras."
                )
            else:
                # Agregasi seluruh pasar per tahun-bulan. Setiap baris pasar
                # menjadi satu observasi dalam rata-rata sederhana.
                harga_bulanan = (
                    df_medium.groupby(["tahun", "bulan_num"], as_index=False)
                    .agg(
                        harga_pasar_rata=("harga", "mean"),
                        jumlah_observasi=("harga", "count"),
                    )
                )

                produksi_bulanan = (
                    df_prod.groupby(["tahun", "bulan_num"], as_index=False)
                    .agg(produksi_ton=("produksi_ton", "mean"))
                )

                perbandingan = produksi_bulanan.merge(
                    harga_bulanan,
                    on=["tahun", "bulan_num"],
                    how="inner",
                )

                nama_bulan = {
                    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
                }

                if perbandingan.empty:
                    st.info(
                        "Belum ada pasangan periode tahun-bulan yang cocok antara "
                        "data produksi dan harga pasar."
                    )
                else:
                    perbandingan["bulan_nama"] = perbandingan["bulan_num"].map(nama_bulan)
                    perbandingan["periode_label"] = (
                        perbandingan["bulan_nama"] + " " +
                        perbandingan["tahun"].astype(str)
                    )
                    perbandingan = perbandingan.sort_values(["tahun", "bulan_num"])

                    st.caption(
                        f"Periode yang berhasil dicocokkan: {len(perbandingan)} bulan · "
                        "Kategori harga: Beras Medium · Agregasi: rata-rata sederhana antarobservasi pasar"
                    )

                    fig_compare = go.Figure()
                    fig_compare.add_trace(go.Scatter(
                        x=perbandingan["periode_label"],
                        y=perbandingan["produksi_ton"],
                        name="Produksi (ton)",
                        mode="lines+markers",
                        line=dict(color="#48BB78", width=3),
                        yaxis="y",
                    ))
                    fig_compare.add_trace(go.Scatter(
                        x=perbandingan["periode_label"],
                        y=perbandingan["harga_pasar_rata"],
                        name="Rata-rata harga Medium (Rp/kg)",
                        mode="lines+markers",
                        line=dict(color="#F6C445", width=3),
                        yaxis="y2",
                    ))
                    fig_compare.update_layout(
                        title="Tren Produksi Beras vs Rata-rata Harga Pasar Medium",
                        xaxis_title="Periode",
                        yaxis=dict(title="Produksi (ton)", side="left"),
                        yaxis2=dict(
                            title="Harga pasar (Rp/kg)",
                            overlaying="y",
                            side="right",
                            showgrid=False,
                        ),
                        legend=dict(orientation="h", y=-0.25, x=0),
                    )
                    st.plotly_chart(
                        style_fig(fig_compare, 440, False),
                        use_container_width=True,
                    )

                    if len(perbandingan) >= 2:
                        korelasi = perbandingan[
                            ["produksi_ton", "harga_pasar_rata"]
                        ].corr(method="pearson").iloc[0, 1]
                        kc1, kc2, kc3 = st.columns(3)
                        with kc1:
                            kpi(
                                "Korelasi Pearson",
                                f"{korelasi:.3f}" if pd.notna(korelasi) else "-",
                                note="Produksi vs harga pasar Medium",
                            )
                        with kc2:
                            kpi(
                                "Rata-rata Produksi",
                                f"{perbandingan['produksi_ton'].mean():,.0f} ton",
                                note="Pada periode yang cocok",
                            )
                        with kc3:
                            kpi(
                                "Rata-rata Harga Pasar",
                                rp(perbandingan["harga_pasar_rata"].mean()),
                                note="Beras Medium (Rp/kg)",
                            )

                        if pd.isna(korelasi):
                            interpretasi = "Korelasi tidak dapat dihitung karena salah satu variabel tidak bervariasi."
                        elif korelasi <= -0.5:
                            interpretasi = "Hubungan linear negatif cukup kuat: produksi yang lebih tinggi cenderung beriringan dengan harga yang lebih rendah."
                        elif korelasi < -0.2:
                            interpretasi = "Hubungan linear negatif lemah hingga sedang."
                        elif korelasi < 0.2:
                            interpretasi = "Hubungan linear sangat lemah atau hampir tidak terlihat."
                        elif korelasi < 0.5:
                            interpretasi = "Hubungan linear positif lemah hingga sedang."
                        else:
                            interpretasi = "Hubungan linear positif cukup kuat."
                        insight(
                            interpretasi +
                            " Korelasi menunjukkan keterkaitan, bukan bukti sebab-akibat."
                        )

                    with st.expander("📋 Lihat data hasil pencocokan produksi dan harga"):
                        st.dataframe(
                            perbandingan[
                                ["tahun", "bulan_nama", "produksi_ton",
                                 "harga_pasar_rata", "jumlah_observasi"]
                            ].rename(columns={
                                "tahun": "Tahun",
                                "bulan_nama": "Bulan",
                                "produksi_ton": "Produksi (ton)",
                                "harga_pasar_rata": "Rata-rata harga Medium (Rp/kg)",
                                "jumlah_observasi": "Jumlah observasi pasar",
                            }).style.format({
                                "Produksi (ton)": "{:,.0f}",
                                "Rata-rata harga Medium (Rp/kg)": "Rp {:,.0f}",
                            }),
                            use_container_width=True,
                        )

# -----------------------------------------------------------------------------
# HALAMAN 2: ANALISIS PROVINSI
# -----------------------------------------------------------------------------
elif menu == "prov":
    st.subheader("🗺️ Analisis Provinsi")
    df_prov = with_period(safe_load("SELECT * FROM province_summary ORDER BY tahun, bulan_num"))
    if df_prov.empty:
        st.warning("Data provinsi belum tersedia.")
        st.stop()

    c1, c2 = st.columns([1, 2])
    with c1:
        selected_prov = st.selectbox("Pilih Provinsi:", sorted(df_prov['provinsi'].unique()))
    with c2:
        all_jenis = sorted(df_prov['jenis_beras'].unique())
        selected_jenis = st.multiselect("Jenis Beras:", all_jenis, default=all_jenis)

    if not selected_jenis:
        st.warning("Pilih minimal satu jenis beras.")
        st.stop()

    d = df_prov[(df_prov['provinsi'] == selected_prov) &
                (df_prov['jenis_beras'].isin(selected_jenis))]
    if d.empty:
        st.warning("Tidak ada data untuk provinsi dan jenis beras pilihan.")
        st.stop()
    nasional = (df_prov[df_prov['jenis_beras'].isin(selected_jenis)]
                .groupby('periode', as_index=False)['avg_harga'].mean()
                .sort_values('periode'))

    prov_bulan = d.groupby('periode', as_index=False)['avg_harga'].mean().sort_values('periode')
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi("Harga Terbaru (rata-rata)", rp(prov_bulan['avg_harga'].iloc[-1]),
            pct_change(prov_bulan['avg_harga'], prov_bulan['periode']))
    with k2:
        selisih = prov_bulan['avg_harga'].iloc[-1] - nasional.loc[nasional['periode'] == prov_bulan['periode'].iloc[-1], 'avg_harga'].iloc[0]
        kpi("vs Rata-rata Nasional", f"{'+' if selisih >= 0 else '−'}{rp(abs(selisih))}",
            note="lebih mahal dari nasional" if selisih > 0 else "lebih murah dari nasional")
    with k3:
        kpi("Rentang Periode", f"{rp(prov_bulan['avg_harga'].min())} – {rp(prov_bulan['avg_harga'].max())}",
            note="harga terendah – tertinggi", small=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig = px.line(d, x='periode', y='avg_harga', color='jenis_beras', markers=True,
                  title=f"Perkembangan Harga Beras di {selected_prov}",
                  labels={'periode': 'Periode', 'avg_harga': 'Rp/kg', 'jenis_beras': 'Jenis'},
                  color_discrete_sequence=COLOR_PALETTE)
    fig.add_trace(go.Scatter(x=nasional['periode'], y=nasional['avg_harga'],
                             name="Rata-rata Nasional", mode="lines",
                             line=dict(color="#FFFFFF", dash="dash", width=2)))
    st.plotly_chart(style_period_fig(fig), use_container_width=True)

    # ------------------------- PETA PROVINSI 3D -------------------------
    st.markdown("##### 🗺️ Peta Perbandingan Antar Provinsi (3D)")
    st.markdown(f'<p class="section-note">Provinsi pilihanmu (<b>{selected_prov}</b>) ditandai garis putih tebal. '
                'Makin tinggi dan makin merah = makin mahal.</p>', unsafe_allow_html=True)

    bulan_opts = month_order(df_prov)
    bmap = month_map(df_prov)
    mc1, _ = st.columns([1, 2])
    with mc1:
        bulan_peta = st.selectbox("Periode pada peta:", bulan_opts,
                                  index=len(bulan_opts) - 1, key="prov_bulan")

    vals = prov_values(df_prov, selected_jenis, bmap[bulan_peta])
    if vals.empty:
        st.info("Tidak ada data untuk jenis beras dan periode pilihan.")
        st.stop()
    ranked = vals.sort_values("nilai", ascending=False).reset_index(drop=True)
    pos = ranked.index[ranked["provinsi"] == selected_prov]
    if len(pos):
        insight(f"Pada <b>{bulan_peta}</b>, <b>{selected_prov}</b> berada di peringkat "
                f"<b>{pos[0] + 1} dari {len(ranked)}</b> provinsi termahal "
                f"({rp(ranked.loc[pos[0], 'nilai'])}/kg).")
    else:
        st.info(f"{selected_prov} belum punya data pada {bulan_peta}.")

    h = max(580, len(ranked) * 17)
    col_map, col_bar = st.columns([3, 2])
    with col_map:
        show_map(vals, "Rp/kg", highlight=selected_prov, height=h)
    with col_bar:
        asc = vals.sort_values("nilai")
        colors = ["#F6C445" if p == selected_prov else "#4A5568" for p in asc["provinsi"]]
        fb = go.Figure(go.Bar(
            x=asc["nilai"], y=asc["provinsi"], orientation="h",
            marker_color=colors, text=asc["nilai"].map(lambda v: f"{v:,.0f}"),
            textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Rp %{x:,.0f}/kg<extra></extra>",
        ))
        fb.update_layout(title="Peringkat Harga per Provinsi")
        fb.update_xaxes(range=[asc["nilai"].min() * 0.9, asc["nilai"].max() * 1.08])
        fb = style_fig(fb, h, False)
        fb.update_layout(hovermode="closest", margin=dict(l=10, r=40, t=50, b=10))
        fb.update_yaxes(tickfont=dict(size=10), tickformat=None)
        st.plotly_chart(fb, use_container_width=True)

# -----------------------------------------------------------------------------
# HALAMAN 3: JELAJAH PASAR
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# HALAMAN 3: JELAJAH PASAR
# -----------------------------------------------------------------------------
elif menu == "market":
    st.subheader("🏪 Jelajah Pasar")
    df_market = with_period(safe_load("SELECT * FROM market_summary ORDER BY tahun, bulan_num"))
    if df_market.empty:
        st.warning("Data pasar belum tersedia.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        selected_prov = st.selectbox("Pilih Provinsi:", sorted(df_market['provinsi'].unique()))
    df_mp = df_market[df_market['provinsi'] == selected_prov]
    with c2:
        selected_pasar = st.selectbox("Pilih Pasar:", sorted(df_mp['nama_pasar'].unique()))

    d = df_mp[df_mp['nama_pasar'] == selected_pasar]

    last_m = d['periode'].max()
    latest = d[d['periode'] == last_m].groupby('jenis_beras')['harga'].mean()
    cols = st.columns(max(len(latest), 1))
    for col, (jenis, val) in zip(cols, latest.items()):
        hist = d[d['jenis_beras'] == jenis].groupby('periode', as_index=False)['harga'].mean().sort_values('periode')
        with col:
            kpi(jenis, rp(val), pct_change(hist['harga'], hist['periode']))

    st.markdown("<br>", unsafe_allow_html=True)

    mode = st.radio("Tampilan grafik:", ["📈 Garis (tren)", "📊 Batang (bandingkan)"], horizontal=True)
    if mode.startswith("📈"):
        fig = px.line(d, x='periode', y='harga', color='jenis_beras', markers=True,
                      color_discrete_sequence=COLOR_PALETTE)
    else:
        fig = px.bar(d, x='periode', y='harga', color='jenis_beras', barmode='group',
                     color_discrete_sequence=COLOR_PALETTE)
    fig.update_layout(title=f"Harga di {selected_pasar} ({selected_prov})",
                      xaxis_title="Bulan", yaxis_title="Rp/kg", legend_title=None)
    fig.update_yaxes(range=[d['harga'].min() * 0.9, d['harga'].max() * 1.05])
    st.plotly_chart(style_period_fig(fig), use_container_width=True)

    with st.expander("📋 Lihat & unduh tabel data"):
        tbl = (d.pivot_table(index='periode_label', columns='jenis_beras', values='harga')
                 .reindex(month_order(d)))
        st.dataframe(tbl.style.format("{:,.0f}"), use_container_width=True)
        st.download_button("⬇️ Unduh CSV", tbl.to_csv().encode("utf-8"),
                           file_name=f"harga_{selected_pasar}.csv", mime="text/csv")

    # ------------------------- PERBANDINGAN ANTAR PASAR -------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"##### ⚖️ Perbandingan Antar Pasar di {selected_prov}")
    st.markdown(
        f'<p class="section-note">Bandingkan harga antar pasar dalam satu provinsi. '
        f'Pasar yang sedang kamu pilih (<b>{selected_pasar}</b>) ditandai warna emas.</p>',
        unsafe_allow_html=True,
    )

    daftar_pasar = sorted(df_mp['nama_pasar'].unique())
    if len(daftar_pasar) < 2:
        st.info(f"Saat ini hanya tersedia 1 pasar di {selected_prov}, sehingga perbandingan antar pasar belum dapat ditampilkan.")
    else:
        cp1, cp2 = st.columns(2)
        with cp1:
            jenis_cmp = st.selectbox(
                "Jenis Beras (Perbandingan):",
                sorted(df_mp['jenis_beras'].unique()),
                key="cmp_jenis_pasar",
            )
        df_cmp_j = df_mp[df_mp['jenis_beras'] == jenis_cmp]
        bulan_cmp_opts = month_order(df_cmp_j)
        with cp2:
            bulan_cmp = st.selectbox(
                "Periode:",
                bulan_cmp_opts,
                index=len(bulan_cmp_opts) - 1,
                key="cmp_bulan_pasar",
            )

        # Data perbandingan pada bulan terpilih
        dm_bulan = (
            df_cmp_j[df_cmp_j['periode_label'] == bulan_cmp]
            .groupby('nama_pasar', as_index=False)['harga']
            .mean()
            .sort_values('harga')
        )

        if not dm_bulan.empty:
            pasar_termurah = dm_bulan.iloc[0]
            pasar_termahal = dm_bulan.iloc[-1]
            rata_prov_pasar = dm_bulan['harga'].mean()
            selisih_pasar = pasar_termahal['harga'] - pasar_termurah['harga']

            pk1, pk2, pk3 = st.columns(3)
            with pk1:
                kpi("Rata-rata Pasar Provinsi", rp(rata_prov_pasar), note=f"{len(dm_bulan)} pasar terdata")
            with pk2:
                kpi("Pasar Termahal", pasar_termahal['nama_pasar'],
                    note=f"{rp(pasar_termahal['harga'])}/kg", small=True)
            with pk3:
                kpi("Pasar Termurah", pasar_termurah['nama_pasar'],
                    note=f"{rp(pasar_termurah['harga'])}/kg (selisih {rp(selisih_pasar)})", small=True)

            # Insight posisi pasar yang sedang dipilih
            pos_sel = dm_bulan[dm_bulan['nama_pasar'] == selected_pasar]
            if not pos_sel.empty:
                harga_sel = pos_sel['harga'].iloc[0]
                diff_avg = harga_sel - rata_prov_pasar
                status_str = (
                    f"<b>{rp(abs(diff_avg))}/kg lebih mahal</b> dari"
                    if diff_avg > 0
                    else (
                        f"<b>{rp(abs(diff_avg))}/kg lebih murah</b> dari"
                        if diff_avg < 0
                        else "<b>sama dengan</b>"
                    )
                )
                insight(
                    f"Pada <b>{bulan_cmp}</b> untuk <b>{jenis_cmp}</b>, harga di "
                    f"<b>{selected_pasar}</b> ({rp(harga_sel)}/kg) tercatat {status_str} "
                    f"rata-rata pasar di {selected_prov}."
                )

            # Tab visualisasi: Peringkat per Bulan vs Tren Multi-Pasar
            tab_rank, tab_trend = st.tabs(["📊 Peringkat Harga Bulan Ini", "📈 Tren Antar Pasar"])

            with tab_rank:
                bar_colors = [
                    "#F6C445" if p == selected_pasar else "#4299E1"
                    for p in dm_bulan['nama_pasar']
                ]
                fig_rank = go.Figure(go.Bar(
                    x=dm_bulan['harga'],
                    y=dm_bulan['nama_pasar'],
                    orientation='h',
                    marker_color=bar_colors,
                    text=dm_bulan['harga'].map(lambda v: f"Rp {v:,.0f}"),
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate="<b>%{y}</b><br>Rp %{x:,.0f}/kg<extra></extra>",
                ))
                fig_rank.update_layout(
                    title=f"Perbandingan Harga {jenis_cmp} Antar Pasar ({bulan_cmp})",
                    xaxis_title="Harga (Rp/kg)",
                    yaxis_title=None,
                )
                fig_rank.update_xaxes(range=[dm_bulan['harga'].min() * 0.92, dm_bulan['harga'].max() * 1.08])
                fig_rank = style_fig(fig_rank, max(350, len(dm_bulan) * 32), False)
                fig_rank.update_layout(hovermode="closest", margin=dict(l=10, r=55, t=50, b=10))
                fig_rank.update_yaxes(tickformat=None)
                st.plotly_chart(fig_rank, use_container_width=True)

            with tab_trend:
                pasar_pilih = st.multiselect(
                    "Pilih pasar yang ingin dibandingkan trennya:",
                    sorted(df_cmp_j['nama_pasar'].unique()),
                    default=sorted(df_cmp_j['nama_pasar'].unique())[:5],  # maksimal 5 default agar grafik tetap rapi
                    key="cmp_multi_pasar",
                )
                if pasar_pilih:
                    d_trend = df_cmp_j[df_cmp_j['nama_pasar'].isin(pasar_pilih)]
                    fig_tr = px.line(
                        d_trend,
                        x='periode',
                        y='harga',
                        color='nama_pasar',
                        markers=True,
                        title=f"Tren Harga {jenis_cmp} Antar Pasar di {selected_prov}",
                        labels={'periode': 'Periode', 'harga': 'Rp/kg', 'nama_pasar': 'Pasar'},
                        color_discrete_sequence=COLOR_PALETTE,
                    )
                    fig_tr.update_yaxes(range=[d_trend['harga'].min() * 0.95, d_trend['harga'].max() * 1.03])
                    st.plotly_chart(style_period_fig(fig_tr), use_container_width=True)
                else:
                    st.warning("Pilih minimal satu pasar untuk melihat grafik tren.")

            with st.expander("📋 Lihat matriks perbandingan seluruh pasar & bulan"):
                tbl_cmp = (
                    df_cmp_j.pivot_table(index='nama_pasar', columns='periode_label', values='harga')
                    .reindex(columns=bulan_cmp_opts)
                )
                st.dataframe(tbl_cmp.style.format("{:,.0f}", na_rep="-"), use_container_width=True)

# -----------------------------------------------------------------------------
# HALAMAN 4: PRICE GAP
# -----------------------------------------------------------------------------
elif menu == "gap":
    st.subheader("🔍 Selisih Harga Provinsi vs Grosir Nasional")
    st.markdown('<p class="section-note">Gap positif (merah) = harga provinsi LEBIH MAHAL dari grosir nasional. '
                'Gap negatif (hijau) = LEBIH MURAH.</p>', unsafe_allow_html=True)

    df_gap = with_period(safe_load("SELECT * FROM price_gap_summary ORDER BY tahun, bulan_num"))
    df_gap = df_gap.dropna(subset=['gap_provinsi_grosir'])
    if df_gap.empty:
        st.warning("Belum ada data ritel dan grosir dengan periode yang cocok.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        selected_jenis = st.selectbox("Jenis Beras:", sorted(df_gap['jenis_beras'].unique()))
    d = df_gap[df_gap['jenis_beras'] == selected_jenis]
    with c2:
        bulan_opts = month_order(d)
        selected_bulan = st.selectbox("Periode:", bulan_opts, index=len(bulan_opts) - 1)

    has_prov = 'provinsi' in d.columns
    if has_prov:
        dm = d[d['periode_label'] == selected_bulan].groupby('provinsi')['gap_provinsi_grosir'] \
              .mean().reset_index().sort_values('gap_provinsi_grosir')

        k1, k2, k3 = st.columns(3)
        with k1:
            kpi("Rata-rata Gap", rp(dm['gap_provinsi_grosir'].mean()), note=f"Bulan {selected_bulan}")
        with k2:
            top = dm.iloc[-1]
            kpi("Paling Mahal vs Grosir", top['provinsi'],
                note=f"{rp(top['gap_provinsi_grosir'])}/kg", small=True)
        with k3:
            low = dm.iloc[0]
            kpi("Paling Murah vs Grosir", low['provinsi'],
                note=f"{rp(low['gap_provinsi_grosir'])}/kg", small=True)

        st.markdown("<br>", unsafe_allow_html=True)
        dm['warna'] = dm['gap_provinsi_grosir'].apply(lambda v: "Lebih mahal" if v > 0 else "Lebih murah")
        fig = px.bar(dm, x='gap_provinsi_grosir', y='provinsi', orientation='h', color='warna',
                     color_discrete_map={"Lebih mahal": "#F56565", "Lebih murah": "#48BB78"},
                     title=f"Gap Harga per Provinsi — {selected_jenis} ({selected_bulan})",
                     labels={'gap_provinsi_grosir': 'Selisih (Rp/kg)', 'provinsi': ''})
        fig.update_layout(legend_title=None, hovermode="closest")
        st.plotly_chart(style_fig(fig, max(450, len(dm) * 22)), use_container_width=True)

    with st.expander("📦 Lihat sebaran gap sepanjang waktu (box plot)"):
        st.caption("Kotak = 50% provinsi di tengah. Garis tengah = median. Titik = tiap provinsi.")
        fig_b = px.box(d, x='periode', y='gap_provinsi_grosir', points="all",
                       labels={'periode': 'Periode', 'gap_provinsi_grosir': 'Selisih (Rp/kg)'},
                       color_discrete_sequence=['#F6C445'])
        fig_b.add_hline(y=0, line_dash="dash", line_color="#FFFFFF")
        st.plotly_chart(style_period_fig(fig_b, 500, False), use_container_width=True)

# -----------------------------------------------------------------------------
# FOOTER (muncul di semua halaman)
# -----------------------------------------------------------------------------
source_footer()
