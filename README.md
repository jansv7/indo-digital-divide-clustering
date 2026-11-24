# Peta Kesenjangan Digital Indonesia

Clustering provinsi di Indonesia berdasarkan **akses, pemanfaatan, dan keterampilan digital** dengan data resmi BPS.

> Punya akses belum tentu bisa memanfaatkan.

**Pertanyaan utama:** provinsi mana yang punya pola kesiapan digital serupa, di lapis mana tiap kelompok tertahan (infrastruktur, pemanfaatan, atau keterampilan), dan intervensi apa yang paling cocok untuk masing-masing?

Dokumen ide lengkap: [ide_project_clustering_bps.md](ide_project_clustering_bps.md)

## Struktur repo

```
├── data/
│   ├── raw/          # file asli unduhan BPS (jangan diedit)
│   ├── processed/    # data gabungan + label cluster
│   └── geo/          # GeoJSON batas provinsi
├── notebooks/
│   ├── 01_data_collection_cleaning.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_clustering_modeling.ipynb
│   └── 04_profiling_policy.ipynb
├── src/              # fungsi yang dipakai ulang (config, preprocessing, clustering, visualisasi)
├── app/
│   └── streamlit_app.py
├── reports/figures/  # grafik 300 DPI
└── requirements.txt
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ipykernel install --user --name digital-divide --display-name "Python (digital-divide)"
```

Jalankan notebook secara berurutan (01 → 04), lalu dashboard:

```powershell
streamlit run app/streamlit_app.py
```

## Data

| Kolom | Indikator | Lapis | Sumber BPS | Tahun |
|---|---|---|---|---|
| `pct_internet` | % penduduk 5+ mengakses internet (3 bulan terakhir) | Pemanfaatan | Susenas, Statistik Telekomunikasi Indonesia | _isi_ |
| `pct_hp` | % penduduk memiliki/menguasai HP | Akses | Susenas, Statistik Telekomunikasi Indonesia | _isi_ |
| `pct_komputer` | % rumah tangga memiliki komputer | Akses | Susenas, Statistik Telekomunikasi Indonesia | _isi_ |
| `pct_desa_4g` | % desa/kelurahan dengan sinyal 4G/LTE | Akses | Podes, Statistik Potensi Desa | _isi_ |
| `pct_skill_tik` | % remaja & dewasa dengan keterampilan TIK (SDGs 4.4.1) | Keterampilan | Indikator SDGs | _isi_ |
| `rls` | Rata-rata Lama Sekolah | Keterampilan | IPM | _isi_ |
| `ip_tik` / `pdrb_per_kapita` | Validasi eksternal, tidak masuk clustering | Konteks | BPS | _isi_ |

**Keputusan 34 vs 38 provinsi:** _belum diputuskan. Tulis di sini setelah cek ketersediaan data di semua indikator dan GeoJSON._

## Temuan utama

_Diisi setelah analisis selesai._

## Rekomendasi kebijakan per cluster

_Diisi setelah profiling._
