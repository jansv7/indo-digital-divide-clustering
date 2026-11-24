"""Grafik yang dipakai ulang di notebook & dashboard."""

import pandas as pd
import plotly.graph_objects as go

from src.config import FIG_DPI, FIGURES, INDICATORS


def save_matplotlib(fig, name: str):
    """Simpan figure matplotlib ke reports/figures dengan 300 DPI."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=FIG_DPI, bbox_inches="tight")


def radar_chart(profile_scaled: pd.DataFrame, features: list[str], title: str = "") -> go.Figure:
    """Radar chart profil cluster. Input: rata-rata z-score per cluster (index = nama cluster)."""
    labels = [INDICATORS[f][0] for f in features]
    fig = go.Figure()
    for name, row in profile_scaled.iterrows():
        values = row[features].tolist()
        fig.add_trace(go.Scatterpolar(
            r=values + values[:1], theta=labels + labels[:1], name=str(name), fill="toself", opacity=0.5,
        ))
    fig.update_layout(title=title, polar=dict(radialaxis=dict(visible=True)), showlegend=True)
    return fig
