"""Penentuan k, K-Means, Hierarchical Ward, dan uji kesepakatan."""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from src.config import RANDOM_STATE


def evaluate_k(X, k_range=range(2, 9)) -> pd.DataFrame:
    """Inertia (elbow), Silhouette, Davies-Bouldin, Calinski-Harabasz untuk tiap k."""
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=50, random_state=RANDOM_STATE).fit(X)
        rows.append({
            "k": k,
            "inertia": km.inertia_,
            "silhouette": silhouette_score(X, km.labels_),
            "davies_bouldin": davies_bouldin_score(X, km.labels_),
            "calinski_harabasz": calinski_harabasz_score(X, km.labels_),
        })
    return pd.DataFrame(rows)


def fit_kmeans(X, k: int) -> KMeans:
    return KMeans(n_clusters=k, n_init=50, random_state=RANDOM_STATE).fit(X)


def fit_ward(X, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Mengembalikan (linkage matrix untuk dendrogram, label 0..k-1)."""
    Z = linkage(X, method="ward")
    labels = fcluster(Z, t=k, criterion="maxclust") - 1
    return Z, labels


def agreement(labels_a, labels_b) -> float:
    """Adjusted Rand Index antara dua hasil clustering."""
    return adjusted_rand_score(labels_a, labels_b)


def cluster_profile(df: pd.DataFrame, features: list[str], label_col: str = "cluster") -> pd.DataFrame:
    """Rata-rata tiap indikator per cluster + jumlah anggota."""
    prof = df.groupby(label_col)[features].mean()
    prof["n_provinsi"] = df.groupby(label_col).size()
    return prof
