"""Cleaning & merge tabel BPS per provinsi."""

import re

import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.config import PROVINSI_38, PROVINSI_ALIASES

_BAKU = {p.upper(): p for p in PROVINSI_38}


def normalize_provinsi(name: str) -> str | None:
    """Samakan ejaan nama provinsi. Mengembalikan None untuk baris non-provinsi (mis. 'INDONESIA')."""
    if pd.isna(name):
        return None
    key = re.sub(r"\s+", " ", str(name).strip().upper())
    if key in PROVINSI_ALIASES:
        return PROVINSI_ALIASES[key]
    return _BAKU.get(key)


def load_bps_table(path, prov_col: str, value_col: str, new_name: str, **read_kwargs) -> pd.DataFrame:
    """Baca satu tabel BPS (CSV/XLSX) dan kembalikan kolom [provinsi, new_name]."""
    path = str(path)
    reader = pd.read_excel if path.endswith((".xlsx", ".xls")) else pd.read_csv
    df = reader(path, **read_kwargs)
    out = pd.DataFrame({
        "provinsi": df[prov_col].map(normalize_provinsi),
        new_name: pd.to_numeric(
            df[value_col].astype(str).str.replace(",", ".", regex=False), errors="coerce"
        ),
    })
    return out.dropna(subset=["provinsi"])


def merge_indicators(tables: list[pd.DataFrame], provinces: list[str]) -> pd.DataFrame:
    """Gabungkan beberapa tabel indikator ke kerangka provinsi yang dipilih (34 atau 38)."""
    master = pd.DataFrame({"provinsi": provinces})
    for t in tables:
        master = master.merge(t, on="provinsi", how="left")
    return master


def scale_features(df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, StandardScaler]:
    """Z-score standardisasi. Mengembalikan DataFrame terstandardisasi + scaler-nya."""
    scaler = StandardScaler()
    scaled = pd.DataFrame(scaler.fit_transform(df[features]), columns=features, index=df.index)
    return scaled, scaler
