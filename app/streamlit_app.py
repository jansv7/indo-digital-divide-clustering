"""Dashboard Peta Kesenjangan Digital Indonesia.

Jalankan: streamlit run app/streamlit_app.py
Butuh file data/processed/provinsi_cluster.csv (output notebook 03/04).
"""

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config import CLUSTER_FILE, FEATURES, GEOJSON_FILE, INDICATORS  # noqa: E402

st.set_page_config(page_title="Peta Kesenjangan Digital Indonesia", layout="wide")


@st.cache_data
def load_data():
    if not CLUSTER_FILE.exists():
        return None, None
    df = pd.read_csv(CLUSTER_FILE)
    geo = json.loads(GEOJSON_FILE.read_text(encoding="utf-8")) if GEOJSON_FILE.exists() else None
    return df, geo


df, geo = load_data()

st.title("Peta Kesenjangan Digital Indonesia")

if df is None:
    st.info("Belum ada data cluster. Jalankan notebook 01–04 dulu sampai "
            f"`{CLUSTER_FILE.relative_to(CLUSTER_FILE.parents[2])}` terbentuk.")
    st.stop()

label_col = "nama_cluster" if "nama_cluster" in df.columns else "cluster"
page = st.sidebar.radio("Halaman", ["Peta Kesiapan Digital", "Profil & Paradoks", "Rapor Provinsi"])

if page == "Peta Kesiapan Digital":
    clusters = sorted(df[label_col].astype(str).unique())
    chosen = st.sidebar.multiselect("Filter cluster", clusters, default=clusters)
    view = df[df[label_col].astype(str).isin(chosen)]
    if geo is None:
        st.warning("GeoJSON belum ada di data/geo/. Menampilkan tabel saja.")
    else:
        # Sesuaikan featureidkey dengan nama properti provinsi di GeoJSON yang dipakai.
        fig = px.choropleth(view, geojson=geo, locations="provinsi", featureidkey="properties.provinsi",
                            color=view[label_col].astype(str), hover_data=FEATURES)
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(view[["provinsi", label_col] + FEATURES], use_container_width=True)

elif page == "Profil & Paradoks":
    prof = df.groupby(label_col)[FEATURES].mean()
    st.subheader("Rata-rata indikator per cluster")
    st.dataframe(prof.round(2), use_container_width=True)
    x = st.selectbox("Sumbu X", FEATURES, index=FEATURES.index("pct_hp"), format_func=lambda c: INDICATORS[c][0])
    y = st.selectbox("Sumbu Y", FEATURES, index=FEATURES.index("pct_internet"), format_func=lambda c: INDICATORS[c][0])
    st.plotly_chart(px.scatter(df, x=x, y=y, color=df[label_col].astype(str), hover_name="provinsi"),
                    use_container_width=True)

else:
    prov = st.selectbox("Pilih provinsi", sorted(df["provinsi"]))
    row = df[df["provinsi"] == prov].iloc[0]
    nasional = df[FEATURES].mean()
    rapor = pd.DataFrame({
        "indikator": [INDICATORS[f][0] for f in FEATURES],
        prov: row[FEATURES].values,
        "rata-rata nasional": nasional.values,
    })
    st.metric("Cluster", str(row[label_col]))
    st.dataframe(rapor.round(2), use_container_width=True)
    if "rekomendasi" in df.columns:
        st.write("**Rekomendasi:**", row["rekomendasi"])
    st.download_button("Unduh rapor (CSV)", rapor.to_csv(index=False), file_name=f"rapor_{prov}.csv")
