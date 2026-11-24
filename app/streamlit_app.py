"""Dashboard Peta Kesenjangan Digital Indonesia.

Jalankan: streamlit run app/streamlit_app.py
Membutuhkan:
- data/processed/provinsi_cluster.csv (output Notebook 01-04)
- data/geo/indonesia_provinsi.geojson (batas 38 provinsi)
"""

import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config import CLUSTER_FILE, FEATURES, GEOJSON_FILE, INDICATORS  # noqa: E402
from src.preprocessing import scale_features  # noqa: E402

st.set_page_config(
    page_title="Peta Kesenjangan Digital Indonesia",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Palet terverifikasi WCAG AA (>= 4.5:1 teks normal, >= 3:1 batas UI) untuk kedua tema.
THEMES = {
    "Terang (Kertas Atlas)": {
        "bg": "#F7F4EE",
        "surface": "#FFFFFF",
        "sidebar": "#EFEAE0",
        "ink": "#14191F",
        "ink_muted": "#434D59",
        "border": "#766F63",
        "border_soft": "#D4CEC2",
        "accent": "#B83B1D",
        "accent_ink": "#FFFFFF",
        "core": "#0F5C6E",
        "grid": "#DED8CC",
        "cluster_colors": {
            0: "#0F5C6E",  # Maritime Teal: Pusat & Motor Digital
            1: "#8A4F08",  # Deep Ochre: Terhubung Seluler
            2: "#3E478C",  # Slate Indigo: Sinyal Tersedia, Adopsi & Skill Tertinggal
            3: "#B83B1D",  # Nusantara Vermilion: Belum Terjangkau
        },
        "plotly_template": "plotly_white",
    },
    "Gelap (Mode Malam)": {
        "bg": "#11161C",
        "surface": "#1A222B",
        "sidebar": "#151C24",
        "ink": "#F2F4F7",
        "ink_muted": "#B8C3CF",
        "border": "#7B8C9E",
        "border_soft": "#2F3B48",
        "accent": "#F58266",
        "accent_ink": "#11161C",
        "core": "#4EC0D4",
        "grid": "#2A3542",
        "cluster_colors": {
            0: "#4EC0D4",
            1: "#F0B654",
            2: "#9EA8F5",
            3: "#F58266",
        },
        "plotly_template": "plotly_dark",
    },
}

CLUSTER_SYMBOLS = {0: "circle", 1: "square", 2: "diamond", 3: "triangle-up"}

CLUSTER_SHORT = {
    0: "C0: Pusat Digital",
    1: "C1: Terhubung Seluler",
    2: "C2: Sinyal Ada, Skill Kurang",
    3: "C3: Belum Terjangkau",
}

SHORT_LABELS = {
    "pct_internet": "Pengguna Internet (%)",
    "pct_hp": "Kepemilikan HP (%)",
    "pct_komputer": "Komputer RT (%)",
    "pct_desa_4g": "Desa Sinyal 4G/5G (%)",
    "pct_skill_tik": "Keterampilan TIK (%)",
    "rls": "Rata-rata Lama Sekolah (thn)",
}

COMPACT_LABELS = {
    "pct_internet": "Internet",
    "pct_hp": "HP",
    "pct_komputer": "Komputer",
    "pct_desa_4g": "Desa 4G/5G",
    "pct_skill_tik": "Skill TIK",
    "rls": "Lama Sekolah",
}

LAYER_ORDER = ["Akses", "Pemanfaatan", "Keterampilan"]


def inject_styles(t: dict) -> None:
    """Terapkan tipografi editorial-atlas, tema terang/gelap penuh, cursor pointer, dan focus ring."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        :root {{
            --atlas-bg: {t["bg"]};
            --atlas-surface: {t["surface"]};
            --atlas-sidebar: {t["sidebar"]};
            --atlas-ink: {t["ink"]};
            --atlas-muted: {t["ink_muted"]};
            --atlas-border: {t["border"]};
            --atlas-border-soft: {t["border_soft"]};
            --atlas-accent: {t["accent"]};
            --atlas-accent-ink: {t["accent_ink"]};
            --atlas-core: {t["core"]};
        }}

        html, body, [data-testid="stAppViewContainer"], .stApp {{
            background-color: var(--atlas-bg) !important;
            color: var(--atlas-ink) !important;
            font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif;
            overflow-x: clip;
        }}

        [data-testid="stHeader"] {{
            background-color: var(--atlas-bg) !important;
            border-bottom: 1px solid var(--atlas-border-soft);
        }}

        [data-testid="stHeader"] button, [data-testid="stHeader"] svg {{
            color: var(--atlas-ink) !important;
            fill: var(--atlas-ink) !important;
        }}

        [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
            background-color: var(--atlas-sidebar) !important;
            border-right: 1px solid var(--atlas-border-soft);
        }}

        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        [data-testid="stSidebar"] [data-testid="stRadio"] p,
        [data-testid="stSidebar"] [data-testid="stCheckbox"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
            color: var(--atlas-ink) !important;
        }}

        h1, h2, h3, .atlas-serif {{
            font-family: 'Newsreader', Georgia, serif !important;
            color: var(--atlas-ink) !important;
            letter-spacing: -0.015em;
        }}

        p, li, label, .stMarkdown, .stCaption, [data-testid="stMarkdownContainer"] {{
            color: var(--atlas-ink);
        }}

        /* Motif identitas: pita taksonomi 3 lapis kesiapan digital */
        .atlas-taxonomy {{
            display: flex;
            flex-wrap: wrap;
            gap: 1.25rem;
            padding: 0.55rem 0;
            margin-bottom: 0.75rem;
            border-top: 2px solid var(--atlas-ink);
            border-bottom: 1px solid var(--atlas-border-soft);
            font-size: 0.84rem;
            font-weight: 600;
            color: var(--atlas-muted);
        }}
        .atlas-taxonomy span strong {{
            color: var(--atlas-ink);
            margin-right: 0.25rem;
        }}

        .atlas-title {{
            font-family: 'Newsreader', Georgia, serif;
            font-size: clamp(1.75rem, 2.8vw, 2.5rem);
            font-weight: 700;
            line-height: 1.15;
            margin: 0 0 0.35rem 0;
            color: var(--atlas-ink);
        }}

        .atlas-lead {{
            font-size: 1rem;
            line-height: 1.55;
            color: var(--atlas-muted);
            max-width: 72ch;
            margin: 0 0 1.25rem 0;
        }}

        .atlas-chart-title {{
            font-family: 'Newsreader', Georgia, serif;
            font-size: 1.15rem;
            font-weight: 600;
            line-height: 1.3;
            color: var(--atlas-ink);
            margin: 0.25rem 0 0.45rem 0;
            overflow-wrap: break-word;
        }}

        .atlas-panel {{
            background-color: var(--atlas-surface);
            border: 1px solid var(--atlas-border-soft);
            border-radius: 6px;
            padding: 1.1rem 1.2rem;
            margin-bottom: 1rem;
        }}

        .atlas-panel-accent {{
            background-color: var(--atlas-surface);
            border: 1px solid var(--atlas-border);
            border-top: 3px solid var(--atlas-accent);
            border-radius: 6px;
            padding: 1.1rem 1.2rem;
            margin-bottom: 1rem;
        }}

        .atlas-kicker {{
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--atlas-muted);
            margin-bottom: 0.3rem;
        }}

        .atlas-big-stat {{
            font-family: 'Newsreader', Georgia, serif;
            font-size: 1.95rem;
            font-weight: 700;
            line-height: 1.15;
            color: var(--atlas-ink);
            margin: 0.15rem 0 0.35rem 0;
            font-variant-numeric: tabular-nums;
        }}

        .atlas-swatch {{
            display: inline-block;
            width: 0.75rem;
            height: 0.75rem;
            border-radius: 2px;
            margin-right: 0.45rem;
            vertical-align: -1px;
        }}

        .atlas-sidebar-brand {{
            font-family: 'Newsreader', Georgia, serif;
            font-size: 1.32rem;
            font-weight: 700;
            line-height: 1.2;
            color: var(--atlas-ink);
            margin-bottom: 0.25rem;
        }}

        .atlas-sidebar-sub {{
            font-size: 0.84rem;
            color: var(--atlas-muted);
            line-height: 1.45;
            padding-bottom: 0.85rem;
            margin-bottom: 0.85rem;
            border-bottom: 1px solid var(--atlas-border-soft);
        }}

        .atlas-sidebar-group {{
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--atlas-muted);
            margin: 0.85rem 0 0.35rem 0;
        }}

        /* Tabel HTML semantik yang adaptif penuh pada tema terang & gelap */
        .atlas-table-wrap {{
            width: 100%;
            overflow-x: auto;
            overflow-y: auto;
            border: 1px solid var(--atlas-border-soft);
            border-radius: 6px;
            background-color: var(--atlas-surface);
            margin-bottom: 1rem;
        }}

        .atlas-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            font-variant-numeric: tabular-nums;
            color: var(--atlas-ink);
        }}

        .atlas-table thead th {{
            position: sticky;
            top: 0;
            z-index: 2;
            background-color: var(--atlas-sidebar);
            color: var(--atlas-ink);
            font-weight: 700;
            text-align: left;
            padding: 0.6rem 0.75rem;
            border-bottom: 2px solid var(--atlas-border);
            white-space: nowrap;
        }}

        .atlas-table tbody td {{
            padding: 0.55rem 0.75rem;
            border-bottom: 1px solid var(--atlas-border-soft);
            color: var(--atlas-ink);
            vertical-align: middle;
        }}

        .atlas-table tbody tr:hover td {{
            background-color: var(--atlas-bg);
        }}

        .atlas-table td.num, .atlas-table th.num {{
            text-align: right;
            white-space: nowrap;
        }}

        /* Kontrol interaktif: cursor pointer, target sentuh >= 44px, focus ring kontras */
        button, [role="button"], [role="tab"], [role="radio"],
        [data-baseweb="select"], [data-baseweb="select"] *,
        [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {{
            cursor: pointer !important;
        }}

        button:disabled, [aria-disabled="true"] {{
            cursor: not-allowed !important;
            opacity: 0.55;
        }}

        button:focus-visible, [role="tab"]:focus-visible, [role="radio"]:focus-visible,
        input:focus-visible, select:focus-visible, a:focus-visible {{
            outline: 2px solid var(--atlas-accent) !important;
            outline-offset: 2px !important;
        }}

        /* Tombol unduh utama dengan kontras teks terjamin pada semua anak elemen */
        [data-testid="stDownloadButton"] button {{
            background-color: var(--atlas-accent) !important;
            color: var(--atlas-accent-ink) !important;
            border: 1px solid var(--atlas-accent) !important;
            border-radius: 5px !important;
            min-height: 44px !important;
            font-weight: 600 !important;
            padding: 0.55rem 1.1rem !important;
            width: 100%;
        }}

        [data-testid="stDownloadButton"] button *,
        [data-testid="stDownloadButton"] button p,
        [data-testid="stDownloadButton"] button span {{
            color: var(--atlas-accent-ink) !important;
        }}

        [data-testid="stDownloadButton"] button:hover {{
            filter: brightness(0.92);
        }}

        /* Radio navigasi sidebar: penanda aktif dengan border, bobot teks, dan latar kontras */
        [data-testid="stSidebar"] [data-testid="stRadio"] label {{
            min-height: 44px;
            padding: 0.45rem 0.65rem;
            border-radius: 5px;
            border: 1px solid transparent;
            margin-bottom: 0.25rem;
            display: flex;
            align-items: center;
        }}

        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
            background-color: var(--atlas-surface);
            border-color: var(--atlas-border-soft);
        }}

        [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{
            background-color: var(--atlas-surface);
            border-color: var(--atlas-accent);
            font-weight: 700;
        }}

        /* Checkbox filter cluster di sidebar: target sentuh nyaman & kontras tinggi */
        [data-testid="stSidebar"] [data-testid="stCheckbox"] label {{
            min-height: 36px;
            padding: 0.25rem 0.35rem;
            border-radius: 4px;
            align-items: flex-start;
        }}

        [data-testid="stSidebar"] [data-testid="stCheckbox"] label:hover {{
            background-color: var(--atlas-surface);
        }}

        /* Selectbox: pastikan permukaan & teks konsisten pada tema terang maupun gelap */
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div > div {{
            background-color: var(--atlas-surface) !important;
            border-color: var(--atlas-border) !important;
            color: var(--atlas-ink) !important;
        }}

        [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
            min-height: 44px;
        }}

        [data-testid="stSelectbox"] [data-baseweb="select"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] span,
        [data-testid="stSelectbox"] [data-baseweb="select"] div {{
            color: var(--atlas-ink) !important;
            -webkit-text-fill-color: var(--atlas-ink) !important;
        }}

        [data-testid="stSelectbox"] [data-baseweb="select"] svg {{
            fill: var(--atlas-ink) !important;
            color: var(--atlas-ink) !important;
        }}

        [data-baseweb="popover"],
        [data-baseweb="popover"] > div,
        [data-baseweb="menu"],
        [role="listbox"] {{
            background-color: var(--atlas-surface) !important;
            color: var(--atlas-ink) !important;
            border-color: var(--atlas-border) !important;
        }}

        [role="option"] {{
            background-color: var(--atlas-surface) !important;
            color: var(--atlas-ink) !important;
        }}

        [role="option"]:hover,
        [role="option"][aria-selected="true"] {{
            background-color: var(--atlas-sidebar) !important;
            color: var(--atlas-ink) !important;
            font-weight: 600;
        }}

        /* Tabs */
        [data-testid="stTabs"] button[role="tab"] {{
            min-height: 44px;
            color: var(--atlas-muted) !important;
            font-weight: 600;
            padding: 0.5rem 0.9rem;
        }}

        [data-testid="stTabs"] button[role="tab"] p {{
            color: inherit !important;
        }}

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
            color: var(--atlas-ink) !important;
            border-bottom: 3px solid var(--atlas-accent) !important;
        }}

        /* Expander */
        [data-testid="stExpander"] {{
            background-color: var(--atlas-surface);
            border: 1px solid var(--atlas-border-soft);
            border-radius: 6px;
        }}

        [data-testid="stExpander"] summary {{
            min-height: 44px;
            cursor: pointer !important;
            color: var(--atlas-ink) !important;
        }}

        [data-testid="stExpander"] summary svg {{
            fill: var(--atlas-ink) !important;
        }}

        @media (max-width: 768px) {{
            .atlas-taxonomy {{
                gap: 0.65rem;
                font-size: 0.78rem;
            }}
            .atlas-panel, .atlas-panel-accent {{
                padding: 0.95rem 1rem;
            }}
            .atlas-chart-title {{
                font-size: 1.05rem;
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                transition: none !important;
                animation: none !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_dataset() -> tuple[pd.DataFrame | None, dict | None, str | None]:
    """Muat CSV hasil clustering dan GeoJSON 38 provinsi dengan penanganan error eksplisit."""
    if not CLUSTER_FILE.exists():
        return None, None, f"File hasil clustering belum ditemukan di `{CLUSTER_FILE.as_posix()}`."

    try:
        df = pd.read_csv(CLUSTER_FILE)
    except Exception as exc:
        return None, None, f"Gagal membaca CSV hasil clustering: {exc}"

    required = {"provinsi", "cluster", *FEATURES}
    missing_cols = sorted(required - set(df.columns))
    if missing_cols:
        return None, None, f"Kolom wajib belum lengkap di CSV: {', '.join(missing_cols)}."

    geo = None
    geo_err = None
    if GEOJSON_FILE.exists():
        try:
            geo = json.loads(GEOJSON_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            geo_err = f"GeoJSON gagal dibaca ({exc}). Peta dinonaktifkan, tabel tetap tersedia."
    else:
        geo_err = "File GeoJSON batas provinsi belum tersedia di data/geo/indonesia_provinsi.geojson."

    return df, geo, geo_err


def apply_plotly_theme(fig: go.Figure, t: dict, height: int = 420) -> go.Figure:
    """Selaraskan warna latar, font, grid, dan legenda Plotly terhadap tema aktif."""
    fig.update_layout(
        template=t["plotly_template"],
        paper_bgcolor=t["surface"],
        plot_bgcolor=t["surface"],
        font=dict(family="Plus Jakarta Sans, Segoe UI, sans-serif", color=t["ink"], size=12),
        title=None,
        height=height,
        margin=dict(l=16, r=16, t=18, b=24),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=t["ink"], size=11),
        ),
    )
    return fig


def render_chart_title(text: str) -> None:
    """Render judul grafik di luar SVG Plotly agar responsif di mobile dan kontras penuh di kedua tema."""
    st.markdown(f'<h3 class="atlas-chart-title">{html.escape(text)}</h3>', unsafe_allow_html=True)


def render_table(df_tbl: pd.DataFrame, max_height: int | None = None, numeric_cols: set[str] | None = None) -> None:
    """Render tabel HTML semantik yang konsisten pada tema terang maupun gelap tanpa glitch canvas."""
    num_set = numeric_cols or set(df_tbl.select_dtypes(include="number").columns)
    headers = []
    for col in df_tbl.columns:
        cls = ' class="num"' if col in num_set else ""
        headers.append(f'<th scope="col"{cls}>{html.escape(str(col))}</th>')

    rows_html = []
    for _, r in df_tbl.iterrows():
        cells = []
        for col in df_tbl.columns:
            val = r[col]
            if isinstance(val, (float, np.floating)):
                txt = f"{val:.2f}"
            elif isinstance(val, (int, np.integer)):
                txt = f"{val:d}"
            else:
                txt = str(val)
            cls = ' class="num"' if col in num_set else ""
            cells.append(f"<td{cls}>{html.escape(txt)}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    style_attr = f' style="max-height:{max_height}px;"' if max_height else ""
    table_html = (
        f'<div class="atlas-table-wrap"{style_attr}>'
        '<table class="atlas-table">'
        f"<thead><tr>{''.join(headers)}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table></div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_header(title: str, lead: str) -> None:
    """Header halaman dengan motif taksonomi 3 lapis kesiapan digital."""
    st.markdown(
        """
        <div class="atlas-taxonomy" aria-label="Kerangka 3 lapis kesiapan digital">
            <span><strong>01</strong> Akses (Sinyal 4G, HP, Komputer)</span>
            <span><strong>02</strong> Pemanfaatan (Pengguna Internet)</span>
            <span><strong>03</strong> Keterampilan (Skill TIK, Lama Sekolah)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<h1 class="atlas-title">{html.escape(title)}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="atlas-lead">{html.escape(lead)}</p>', unsafe_allow_html=True)


def build_cluster_lookup(df: pd.DataFrame, t: dict) -> tuple[dict[int, str], dict[str, str], dict[str, str]]:
    """Siapkan pemetaan cluster id -> nama, warna, dan simbol scatter."""
    id_to_name = {}
    for cid, grp in df.groupby("cluster"):
        name = str(grp["nama_cluster"].iloc[0]) if "nama_cluster" in df.columns else f"Cluster {cid}"
        id_to_name[int(cid)] = name

    name_to_color = {name: t["cluster_colors"].get(cid, t["core"]) for cid, name in id_to_name.items()}
    name_to_symbol = {name: CLUSTER_SYMBOLS.get(cid, "circle") for cid, name in id_to_name.items()}
    return id_to_name, name_to_color, name_to_symbol


# ---------- Sidebar: Shell Navigasi & Tema ----------
with st.sidebar:
    st.markdown('<div class="atlas-sidebar-brand">Peta Kesenjangan Digital</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="atlas-sidebar-sub">Tipologi 38 provinsi Indonesia berdasarkan akses, pemanfaatan, dan keterampilan TIK (data resmi BPS).</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigasi Halaman",
        ["Peta Kesiapan Digital", "Profil & Paradoks", "Rapor Provinsi"],
    )

    theme_name = st.radio(
        "Tema Tampilan",
        list(THEMES.keys()),
    )

theme = THEMES[theme_name]
inject_styles(theme)

# ---------- Loading & Error State ----------
with st.spinner("Memuat data 38 provinsi dan peta batas wilayah Indonesia..."):
    df, geo, load_err = load_dataset()

if df is None:
    render_header(
        "Data Hasil Clustering Belum Tersedia",
        "Dashboard membutuhkan tabel akhir provinsi dari Notebook 01 sampai Notebook 04.",
    )
    st.error(load_err or "Terjadi kesalahan saat memuat data.")
    st.markdown(
        """
        <div class="atlas-panel">
            <div class="atlas-kicker">Langkah pemulihan</div>
            <p>Jalankan berurutan <code>01_data_collection_cleaning.ipynb</code> sampai <code>04_profiling_policy.ipynb</code> hingga file <code>data/processed/provinsi_cluster.csv</code> terbentuk, lalu muat ulang halaman ini.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

label_col = "nama_cluster" if "nama_cluster" in df.columns else "cluster"
df[label_col] = df[label_col].astype(str)
id_to_name, name_to_color, name_to_symbol = build_cluster_lookup(df, theme)
ordered_names = [id_to_name[k] for k in sorted(id_to_name)]

X_scaled, _ = scale_features(df, FEATURES)
ranks_df = df.set_index("provinsi")[FEATURES].rank(ascending=False, method="min")
ranks_df["rata_rank"] = ranks_df[FEATURES].mean(axis=1)
ranks_df["peringkat_gabungan"] = ranks_df["rata_rank"].rank(method="min").astype(int)

with st.sidebar:
    st.markdown('<div class="atlas-sidebar-group">Ringkasan Data</div>', unsafe_allow_html=True)
    st.caption(
        "Cakupan: 38 provinsi Indonesia. Sumber: Susenas 2025 (Internet, HP, Komputer, SDGs 4.4.1), "
        "Podes (Sinyal 4G/5G desa), IPM 2026 (RLS). Model: K-Means K=4 (sepakat 36/38 provinsi dengan Ward)."
    )


# ==============================================================================
# HALAMAN 1: PETA KESIAPAN DIGITAL
# ==============================================================================
if page == "Peta Kesiapan Digital":
    with st.sidebar:
        st.markdown('<div class="atlas-sidebar-group">Filter Tipologi Cluster</div>', unsafe_allow_html=True)
        chosen_clusters = []
        for cid in sorted(id_to_name):
            cname = id_to_name[cid]
            n_prov = int((df["cluster"] == cid).sum())
            if st.checkbox(f"C{cid}: {cname} ({n_prov})", value=True, key=f"filter_c{cid}"):
                chosen_clusters.append(cname)
        map_metric = st.selectbox(
            "Pewarnaan peta menurut",
            options=["Tipologi Cluster (K=4)"] + FEATURES,
            format_func=lambda c: c if c == "Tipologi Cluster (K=4)" else SHORT_LABELS[c],
        )

    render_header(
        "Peta Kesiapan Digital 38 Provinsi",
        "Peta ini memetakan sebaran geografis empat kelompok kesiapan digital Indonesia. Gunakan filter di bilah kiri untuk membandingkan tipologi cluster atau menyorot satu indikator spesifik.",
    )

    if load_err and geo is None:
        st.warning(load_err)

    view = df[df[label_col].isin(chosen_clusters)].copy()

    if view.empty:
        st.markdown(
            """
            <div class="atlas-panel-accent">
                <div class="atlas-kicker">Tidak ada provinsi yang ditampilkan</div>
                <p>Semua filter tipologi cluster di bilah kiri sedang kosong. Pilih minimal satu tipologi cluster untuk memunculkan peta choropleth dan tabel perbandingan provinsi.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # Focal point utama: Peta Choropleth penuh
    if geo is not None:
        hover_cols = {
            label_col: True,
            "pct_internet": ":.2f",
            "pct_desa_4g": ":.2f",
            "pct_skill_tik": ":.2f",
            "pct_komputer": ":.2f",
            "pct_hp": ":.2f",
            "rls": ":.2f",
        }
        if map_metric == "Tipologi Cluster (K=4)":
            render_chart_title(f"Sebaran Geografis Tipologi Kesiapan Digital ({len(view)} Provinsi)")
            fig_map = px.choropleth(
                view,
                geojson=geo,
                locations="provinsi",
                featureidkey="properties.provinsi",
                color=label_col,
                category_orders={label_col: ordered_names},
                color_discrete_map=name_to_color,
                hover_name="provinsi",
                hover_data=hover_cols,
                labels={label_col: "Tipologi", **SHORT_LABELS},
            )
            apply_plotly_theme(fig_map, theme, height=470)
            fig_map.update_layout(
                legend=dict(orientation="h", yanchor="top", y=-0.04, xanchor="left", x=0, title_text=""),
                margin=dict(l=6, r=6, t=12, b=56),
            )
        else:
            render_chart_title(f"Sebaran {SHORT_LABELS[map_metric]} pada {len(view)} Provinsi Terpilih")
            fig_map = px.choropleth(
                view,
                geojson=geo,
                locations="provinsi",
                featureidkey="properties.provinsi",
                color=map_metric,
                color_continuous_scale="YlGnBu" if theme_name.startswith("Terang") else "Tealgrn",
                hover_name="provinsi",
                hover_data=hover_cols,
                labels={label_col: "Tipologi", **SHORT_LABELS},
            )
            apply_plotly_theme(fig_map, theme, height=470)
            fig_map.update_coloraxes(
                colorbar=dict(
                    title=dict(text=COMPACT_LABELS[map_metric], font=dict(color=theme["ink"])),
                    tickfont=dict(color=theme["ink"]),
                )
            )
            fig_map.update_layout(margin=dict(l=6, r=6, t=12, b=12))

        fig_map.update_geos(fitbounds="locations", visible=False, bgcolor=theme["surface"])
        fig_map.update_traces(marker_line_color=theme["bg"], marker_line_width=0.7)
        st.plotly_chart(
            fig_map,
            use_container_width=True,
            theme=None,
            config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
        )

    # Komposisi asimetris di bawah peta: Tabel keputusan (kiri) + Distribusi & sorotan ekstrem (kanan)
    col_table, col_side = st.columns([1.65, 1.0], gap="large")

    with col_table:
        st.subheader(f"Daftar Provinsi Terpilih ({len(view)} dari 38)")
        sort_col = "pct_internet" if map_metric == "Tipologi Cluster (K=4)" else map_metric
        display_df = (
            view[["provinsi", label_col, "pct_internet", "pct_desa_4g", "pct_skill_tik", "pct_komputer", "pct_hp", "rls"]]
            .sort_values(sort_col, ascending=False)
            .rename(columns={"provinsi": "Provinsi", label_col: "Tipologi Cluster", **COMPACT_LABELS})
        )
        render_table(display_df, max_height=370)

    with col_side:
        st.subheader("Komposisi Cluster Terpilih")
        counts = (
            view.groupby(["cluster", label_col], as_index=False)["provinsi"]
            .count()
            .rename(columns={"provinsi": "Jumlah"})
            .sort_values("cluster")
        )
        render_chart_title("Jumlah Provinsi per Kelompok")
        fig_bar = go.Figure()
        for _, r in counts.iterrows():
            cid = int(r["cluster"])
            cname = r[label_col]
            short_y = CLUSTER_SHORT.get(cid, f"C{cid}")
            fig_bar.add_trace(
                go.Bar(
                    y=[short_y],
                    x=[int(r["Jumlah"])],
                    orientation="h",
                    marker_color=name_to_color[cname],
                    text=[f"{int(r['Jumlah'])} prov"],
                    textposition="outside",
                    textfont=dict(color=theme["ink"], size=12),
                    cliponaxis=False,
                    showlegend=False,
                    hovertemplate=f"<b>{cname}</b><br>Jumlah: {int(r['Jumlah'])} provinsi<extra></extra>",
                )
            )
        apply_plotly_theme(fig_bar, theme, height=205)
        fig_bar.update_layout(
            xaxis=dict(visible=False, range=[0, max(counts["Jumlah"]) * 1.38]),
            yaxis=dict(autorange="reversed", title="", automargin=True, tickfont=dict(color=theme["ink"], size=11)),
            margin=dict(l=8, r=36, t=8, b=8),
        )
        st.plotly_chart(fig_bar, use_container_width=True, theme=None, config={"displayModeBar": False})

        focus_col = "pct_internet" if map_metric == "Tipologi Cluster (K=4)" else map_metric
        top_row = view.loc[view[focus_col].idxmax()]
        low_row = view.loc[view[focus_col].idxmin()]
        gap_val = top_row[focus_col] - low_row[focus_col]
        unit_suffix = "&nbsp;tahun" if focus_col == "rls" else "%"
        st.markdown(
            f"""
            <div class="atlas-panel-accent">
                <div class="atlas-kicker">Rentang Kesenjangan ({html.escape(SHORT_LABELS[focus_col])})</div>
                <div class="atlas-big-stat">{gap_val:.2f}{unit_suffix}</div>
                <p style="margin:0; font-size:0.9rem; line-height:1.55; color:var(--atlas-muted);">
                    Tertinggi: <strong style="color:var(--atlas-ink);">{html.escape(str(top_row["provinsi"]))}</strong> ({top_row[focus_col]:.2f}{unit_suffix})<br/>
                    Terendah: <strong style="color:var(--atlas-ink);">{html.escape(str(low_row["provinsi"]))}</strong> ({low_row[focus_col]:.2f}{unit_suffix})
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# HALAMAN 2: PROFIL & PARADOKS
# ==============================================================================
elif page == "Profil & Paradoks":
    render_header(
        "Profil Cluster & Bedah Paradoks Digital",
        "Punya akses tidak otomatis diikuti pemanfaatan dan keterampilan TIK. Halaman ini memetakan di lapis mana tiap kelompok tertahan serta membedah provinsi yang menyimpang dari pola umum.",
    )

    prof_z = X_scaled.assign(cluster=df["cluster"]).groupby("cluster")[FEATURES].mean()
    lapis_map: dict[str, list[str]] = {}
    for col, (_, lapis) in INDICATORS.items():
        lapis_map.setdefault(lapis, []).append(col)
    lapis_z = pd.DataFrame({lapis: prof_z[lapis_map[lapis]].mean(axis=1) for lapis in LAYER_ORDER})

    # Bagian 1 (Asimetris 1.05 : 1.15): Diagnosis 3 Lapis vs Radar 6 Indikator
    col_layer, col_radar = st.columns([1.05, 1.15], gap="large")

    with col_layer:
        render_chart_title("Di Lapis Mana Setiap Cluster Tertahan? (Z-Score)")
        fig_lapis = go.Figure()
        layer_colors = {
            "Akses": theme["core"],
            "Pemanfaatan": theme["cluster_colors"][1],
            "Keterampilan": theme["accent"],
        }
        cluster_codes = [f"Cluster {int(c)}" for c in lapis_z.index]
        cluster_full = [id_to_name[int(c)] for c in lapis_z.index]
        for lapis in LAYER_ORDER:
            fig_lapis.add_trace(
                go.Bar(
                    name=lapis,
                    x=cluster_codes,
                    y=lapis_z[lapis].round(2),
                    customdata=cluster_full,
                    marker_color=layer_colors[lapis],
                    text=[f"{v:+.2f}" for v in lapis_z[lapis]],
                    textposition="outside",
                    textfont=dict(color=theme["ink"], size=10),
                    cliponaxis=False,
                    hovertemplate="<b>%{customdata}</b><br>Lapis " + lapis + ": %{y:+.2f} SD<extra></extra>",
                )
            )
        fig_lapis.add_hline(y=0, line_dash="dash", line_color=theme["border"], line_width=1.2)
        min_z = float(lapis_z.min().min())
        max_z = float(lapis_z.max().max())
        apply_plotly_theme(fig_lapis, theme, height=400)
        fig_lapis.update_layout(
            barmode="group",
            yaxis=dict(
                title=dict(text="Z-Score", font=dict(color=theme["ink"])),
                range=[min_z - 0.85, max_z + 0.75],
                gridcolor=theme["grid"],
                tickfont=dict(color=theme["ink"]),
            ),
            xaxis=dict(title="", tickfont=dict(color=theme["ink"])),
            legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0),
            margin=dict(l=48, r=12, t=16, b=62),
        )
        st.plotly_chart(fig_lapis, use_container_width=True, theme=None, config={"displayModeBar": False})

    with col_radar:
        render_chart_title("Perbandingan Profil 6 Indikator Antar Cluster (Z-Score)")
        theta_labels = [COMPACT_LABELS[f] for f in FEATURES]
        fig_radar = go.Figure()
        for cid, row in prof_z.iterrows():
            cname = id_to_name[int(cid)]
            vals = row[FEATURES].round(2).tolist()
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=vals + vals[:1],
                    theta=theta_labels + theta_labels[:1],
                    name=CLUSTER_SHORT.get(int(cid), f"C{cid}"),
                    line=dict(color=name_to_color[cname], width=2.2),
                    fill="toself",
                    opacity=0.25,
                    hovertemplate=f"<b>{cname}</b><br>%{{theta}}: %{{r:+.2f}} SD<extra></extra>",
                )
            )
        apply_plotly_theme(fig_radar, theme, height=400)
        fig_radar.update_layout(
            polar=dict(
                bgcolor=theme["surface"],
                radialaxis=dict(
                    visible=True,
                    gridcolor=theme["grid"],
                    linecolor=theme["border_soft"],
                    tickfont=dict(color=theme["ink_muted"], size=10),
                ),
                angularaxis=dict(
                    gridcolor=theme["grid"],
                    linecolor=theme["border_soft"],
                    tickfont=dict(color=theme["ink"], size=11),
                ),
            ),
            legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0),
            margin=dict(l=54, r=54, t=24, b=82),
        )
        st.plotly_chart(fig_radar, use_container_width=True, theme=None, config={"displayModeBar": False})

    # Bagian 2 (Full-width spotlight): Bedah 3 Paradoks Digital via Tabs
    st.subheader("Bedah Anomali: Tiga Pola Paradoks Digital")
    med_hp = df["pct_hp"].median()
    med_net = df["pct_internet"].median()
    med_skill = df["pct_skill_tik"].median()

    tab_p1, tab_p2, tab_p3 = st.tabs([
        "Sinyal 4G Tinggi, Skill TIK Rendah",
        "Internet Tinggi, Sinyal 4G Desa Tertinggal",
        "Kepemilikan HP Tinggi, Internet Rendah",
    ])

    with tab_p1:
        p_4g_skill = df[(df["pct_desa_4g"] >= 80) & (df["pct_skill_tik"] < med_skill)].sort_values("pct_skill_tik")
        st.markdown(
            f"**{len(p_4g_skill)} provinsi** sudah memiliki cakupan desa 4G minimal 80%, tetapi keterampilan TIK remaja dan dewasa masih di bawah median nasional ({med_skill:.2f}%). Pembangunan infrastruktur sinyal saja belum cukup tanpa literasi TIK."
        )
        if p_4g_skill.empty:
            st.info("Tidak ada provinsi yang memenuhi kriteria paradoks ini.")
        else:
            render_table(
                p_4g_skill[["provinsi", label_col, "pct_desa_4g", "pct_skill_tik", "pct_internet"]].rename(
                    columns={"provinsi": "Provinsi", label_col: "Tipologi Cluster", **SHORT_LABELS}
                )
            )

    with tab_p2:
        p_net_4g = df[(df["pct_internet"] > med_net) & (df["pct_desa_4g"] < 85)].sort_values("pct_desa_4g")
        st.markdown(
            f"**{len(p_net_4g)} provinsi** mencatat pengguna internet di atas median nasional ({med_net:.2f}%), padahal cakupan desa bersinyal 4G masih di bawah 85%. Adopsi warga kota sudah melaju cepat, namun desa pedalaman dan pulau kecil tertinggal."
        )
        if p_net_4g.empty:
            st.info("Tidak ada provinsi yang memenuhi kriteria paradoks ini.")
        else:
            render_table(
                p_net_4g[["provinsi", label_col, "pct_desa_4g", "pct_internet", "pct_hp"]].rename(
                    columns={"provinsi": "Provinsi", label_col: "Tipologi Cluster", **SHORT_LABELS}
                )
            )

    with tab_p3:
        p_hp_net = df[(df["pct_hp"] > med_hp) & (df["pct_internet"] < med_net)].sort_values("pct_internet")
        st.markdown(
            f"**{len(p_hp_net)} provinsi** memiliki kepemilikan HP di atas median nasional ({med_hp:.2f}%), tetapi proporsi pengguna internet masih di bawah median ({med_net:.2f}%)."
        )
        if p_hp_net.empty:
            st.info("Tidak ada provinsi pada kuadran ini.")
        else:
            render_table(
                p_hp_net[["provinsi", label_col, "pct_hp", "pct_internet", "pct_skill_tik"]].rename(
                    columns={"provinsi": "Provinsi", label_col: "Tipologi Cluster", **SHORT_LABELS}
                )
            )

    # Bagian 3 (Asimetris 1.65 : 1): Eksplorasi Kuadran Interaktif + Tabel Rata-rata Asli
    st.subheader("Eksplorasi Kuadran Antar Indikator")
    col_plot, col_ctrl = st.columns([1.65, 1.0], gap="large")

    with col_ctrl:
        x_col = st.selectbox(
            "Pilih indikator sumbu X",
            FEATURES,
            index=FEATURES.index("pct_desa_4g"),
            format_func=lambda c: SHORT_LABELS[c],
        )
        y_col = st.selectbox(
            "Pilih indikator sumbu Y",
            FEATURES,
            index=FEATURES.index("pct_skill_tik"),
            format_func=lambda c: SHORT_LABELS[c],
        )
        x_med, y_med = df[x_col].median(), df[y_col].median()
        st.markdown(
            f"""
            <div class="atlas-panel">
                <div class="atlas-kicker">Panduan Membaca 4 Kuadran</div>
                <p style="font-size:0.88rem; color:var(--atlas-muted); margin-bottom:0.45rem;">
                    Garis putus-putus menandai median nasional:<br/>
                    <strong style="color:var(--atlas-ink);">{html.escape(SHORT_LABELS[x_col])}</strong> = {x_med:.2f}<br/>
                    <strong style="color:var(--atlas-ink);">{html.escape(SHORT_LABELS[y_col])}</strong> = {y_med:.2f}
                </p>
                <p style="font-size:0.86rem; color:var(--atlas-muted); margin:0;">
                    Kuadran kanan-bawah menandai provinsi yang tinggi di sumbu X tetapi masih rendah di sumbu Y. Bentuk simbol titik membedakan cluster agar tetap terbaca tanpa bergantung pada warna.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_plot:
        render_chart_title(f"Hubungan {SHORT_LABELS[x_col]} terhadap {SHORT_LABELS[y_col]}")
        fig_sc = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=label_col,
            symbol=label_col,
            category_orders={label_col: ordered_names},
            color_discrete_map=name_to_color,
            symbol_map=name_to_symbol,
            hover_name="provinsi",
            hover_data={x_col: ":.2f", y_col: ":.2f", label_col: True},
            labels={x_col: SHORT_LABELS[x_col], y_col: SHORT_LABELS[y_col], label_col: "Tipologi"},
        )
        fig_sc.update_traces(marker=dict(size=11, line=dict(width=1, color=theme["surface"])))
        fig_sc.add_vline(x=x_med, line_dash="dash", line_color=theme["border"], line_width=1.1)
        fig_sc.add_hline(y=y_med, line_dash="dot", line_color=theme["border"], line_width=1.1)
        apply_plotly_theme(fig_sc, theme, height=415)
        fig_sc.update_layout(
            xaxis=dict(gridcolor=theme["grid"], title_font=dict(color=theme["ink"]), tickfont=dict(color=theme["ink"])),
            yaxis=dict(gridcolor=theme["grid"], title_font=dict(color=theme["ink"]), tickfont=dict(color=theme["ink"])),
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0, title_text=""),
            margin=dict(l=48, r=16, t=12, b=92),
        )
        st.plotly_chart(
            fig_sc,
            use_container_width=True,
            theme=None,
            config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
        )

    with st.expander("Lihat tabel rata-rata angka asli per cluster dibandingkan nasional"):
        prof_raw = df.groupby(["cluster", label_col])[FEATURES].mean()
        prof_raw["Jumlah Provinsi"] = df.groupby(["cluster", label_col]).size()
        nat_row = pd.DataFrame(
            [{**df[FEATURES].mean().to_dict(), "Jumlah Provinsi": len(df)}],
            index=pd.MultiIndex.from_tuples([(-1, "Rata-rata Nasional")], names=["cluster", label_col]),
        )
        tbl_prof = (
            pd.concat([prof_raw, nat_row])
            .reset_index()
            .drop(columns=["cluster"])
            .rename(columns={label_col: "Tipologi Cluster", **COMPACT_LABELS})
        )
        render_table(tbl_prof)


# ==============================================================================
# HALAMAN 3: RAPOR PROVINSI & REKOMENDASI
# ==============================================================================
else:
    render_header(
        "Rapor Provinsi & Rekomendasi Kebijakan",
        "Pilih satu provinsi untuk membandingkan keenam indikatornya terhadap rata-rata nasional, melihat hambatan utama kelompoknya, dan mengunduh ringkasan rapor dalam format CSV.",
    )

    col_pick, col_brief = st.columns([1.0, 1.75], gap="large")

    with col_pick:
        prov = st.selectbox("Pilih provinsi (38 wilayah)", sorted(df["provinsi"].tolist()))
        row = df[df["provinsi"] == prov].iloc[0]
        cid = int(row["cluster"])
        cname = str(row[label_col])
        c_color = name_to_color[cname]
        rank_gab = int(ranks_df.loc[prov, "peringkat_gabungan"])

        st.markdown(
            f"""
            <div class="atlas-panel">
                <div class="atlas-kicker">Tipologi Kesiapan Digital</div>
                <p style="font-size:1.03rem; font-weight:700; margin:0.15rem 0 0.75rem 0; color:var(--atlas-ink);">
                    <span class="atlas-swatch" style="background:{c_color};"></span>Cluster {cid}: {html.escape(cname)}
                </p>
                <div class="atlas-kicker">Peringkat Rata-rata Gabungan</div>
                <div class="atlas-big-stat">#{rank_gab} <span style="font-size:1rem; font-weight:500; color:var(--atlas-muted);">dari 38 provinsi</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_brief:
        hambatan = str(row["hambatan_utama"]) if "hambatan_utama" in df.columns else "Belum terisi di dataset."
        rekomendasi = str(row["rekomendasi"]) if "rekomendasi" in df.columns else "Belum terisi di dataset."
        st.markdown(
            f"""
            <div class="atlas-panel-accent">
                <div class="atlas-kicker">Diagnosis Hambatan Utama ({html.escape(prov)})</div>
                <p style="margin:0 0 0.9rem 0; font-size:0.96rem; line-height:1.55;">{html.escape(hambatan)}</p>
                <div class="atlas-kicker">Arah Rekomendasi Kebijakan</div>
                <p style="margin:0; font-size:0.96rem; line-height:1.55; font-weight:500;">{html.escape(rekomendasi)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    nasional = df[FEATURES].mean()
    prov_z = X_scaled.loc[df["provinsi"] == prov, FEATURES].iloc[0]

    rapor_rows = []
    for f in FEATURES:
        val_p = float(row[f])
        val_n = float(nasional[f])
        diff = val_p - val_n
        rk = int(ranks_df.loc[prov, f])
        status = "Di atas nasional" if diff >= 0 else "Di bawah nasional"
        rapor_rows.append(
            {
                "Indikator": COMPACT_LABELS[f],
                "Indikator Lengkap": SHORT_LABELS[f],
                "Lapis": INDICATORS[f][1],
                prov: round(val_p, 2),
                "Nasional": round(val_n, 2),
                "Selisih": f"{diff:+.2f}",
                "Rank": f"#{rk}/38",
                "Posisi": status,
                "Z-Score": round(float(prov_z[f]), 2),
            }
        )
    rapor_df = pd.DataFrame(rapor_rows)

    col_gap, col_card = st.columns([1.15, 1.25], gap="large")

    with col_gap:
        render_chart_title(f"Posisi {prov} Relatif terhadap Nasional (Z-Score)")
        bar_colors = [theme["core"] if z >= 0 else theme["accent"] for z in rapor_df["Z-Score"]]
        fig_gap = go.Figure()
        fig_gap.add_trace(
            go.Bar(
                y=rapor_df["Indikator"],
                x=rapor_df["Z-Score"],
                orientation="h",
                marker_color=bar_colors,
                text=[f"{z:+.2f}" for z in rapor_df["Z-Score"]],
                textposition="outside",
                textfont=dict(color=theme["ink"], size=11),
                cliponaxis=False,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    f"{prov}: %{{customdata[1]}}<br>"
                    "Nasional: %{customdata[2]} (Selisih %{customdata[3]})<br>"
                    "Z-Score: %{x:+.2f} SD<extra></extra>"
                ),
                customdata=np.column_stack(
                    [rapor_df["Indikator Lengkap"], rapor_df[prov], rapor_df["Nasional"], rapor_df["Selisih"]]
                ),
            )
        )
        fig_gap.add_vline(x=0, line_color=theme["ink"], line_width=1.2)
        # Padding datar +1.35 di kiri & kanan menjamin teks negatif tidak pernah menabrak label sumbu Y
        max_abs = max(2.2, float(rapor_df["Z-Score"].abs().max()) + 1.35)
        apply_plotly_theme(fig_gap, theme, height=350)
        fig_gap.update_layout(
            xaxis=dict(
                title=dict(text="Z-Score (0 = Nasional)", font=dict(color=theme["ink"])),
                range=[-max_abs, max_abs],
                gridcolor=theme["grid"],
                tickfont=dict(color=theme["ink"]),
            ),
            yaxis=dict(autorange="reversed", title="", automargin=True, tickfont=dict(color=theme["ink"], size=11)),
            margin=dict(l=12, r=28, t=12, b=42),
        )
        st.plotly_chart(fig_gap, use_container_width=True, theme=None, config={"displayModeBar": False})

    with col_card:
        st.subheader(f"Tabel Rapor {prov}")
        render_table(
            rapor_df[["Indikator", "Lapis", prov, "Nasional", "Selisih", "Rank", "Posisi"]],
            numeric_cols={prov, "Nasional", "Selisih", "Rank"},
        )

        export_df = rapor_df[["Indikator Lengkap", "Lapis", prov, "Nasional", "Selisih", "Rank", "Posisi"]].rename(
            columns={"Indikator Lengkap": "Indikator", "Nasional": "Rata-rata Nasional", "Rank": "Peringkat"}
        )
        export_df["Tipologi Cluster"] = cname
        export_df["Hambatan Utama"] = hambatan
        export_df["Rekomendasi Kebijakan"] = rekomendasi
        safe_slug = prov.lower().replace(" ", "_")
        st.download_button(
            label=f"Unduh Rapor {prov} (CSV)",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"rapor_digital_{safe_slug}.csv",
            mime="text/csv",
        )

    peers = df[(df["cluster"] == cid) & (df["provinsi"] != prov)].sort_values("pct_internet", ascending=False)
    st.subheader(f"Provinsi Pembanding di Cluster {cid}: {cname} ({len(peers)} provinsi lain)")
    if peers.empty:
        st.info(f"{prov} adalah satu-satunya provinsi di Cluster {cid}.")
    else:
        render_table(
            peers[["provinsi"] + FEATURES].rename(columns={"provinsi": "Provinsi", **COMPACT_LABELS}),
            max_height=340,
        )
