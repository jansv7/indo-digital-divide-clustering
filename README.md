# Peta Kesenjangan Digital Indonesia

Clustering 38 provinsi Indonesia berdasarkan **akses, pemanfaatan, dan keterampilan digital** menggunakan data resmi Badan Pusat Statistik (BPS), dilengkapi rekomendasi kebijakan per kelompok dan dashboard interaktif Streamlit.

> Punya akses belum tentu bisa memanfaatkan.

**Pertanyaan utama:** provinsi mana yang memiliki pola kesiapan digital serupa, di lapis mana tiap kelompok tertahan (infrastruktur, pemanfaatan, atau keterampilan), dan intervensi apa yang paling tepat untuk masing-masing kelompok?

## Struktur Repo

```
├── data/
│   ├── raw/                # 6 file Excel asli unduhan BPS (tidak diedit manual)
│   ├── processed/          # indikator_digital_provinsi.csv, provinsi_cluster.csv, ringkasan_cluster_kebijakan.csv
│   └── geo/                # indonesia_provinsi.geojson (38 provinsi, disederhanakan)
├── notebooks/
│   ├── 01_data_collection_cleaning.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_clustering_modeling.ipynb
│   └── 04_profiling_policy.ipynb
├── src/                    # modul kode ulang pakai (config, preprocessing, clustering, visualization)
├── app/
│   └── streamlit_app.py    # dashboard interaktif 3 halaman (tema Terang & Gelap)
├── reports/figures/        # grafik analisis 300 DPI
└── requirements.txt
```

## Setup & Cara Menjalankan

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ipykernel install --user --name digital-divide --display-name "Python (digital-divide)"
```

Jalankan notebook secara berurutan (`01` sampai `04`), lalu jalankan dashboard:

```powershell
streamlit run app/streamlit_app.py
```

## Data & Keputusan Metodologi

| Kolom | Indikator | Lapis | Sumber BPS | Tahun |
|---|---|---|---|---|
| `pct_internet` | % penduduk usia 5+ mengakses internet (3 bulan terakhir) | Pemanfaatan | Susenas, Statistik Telekomunikasi Indonesia | 2025 |
| `pct_hp` | % penduduk memiliki/menguasai telepon seluler | Akses | Susenas, Statistik Telekomunikasi Indonesia | 2025 |
| `pct_komputer` | % rumah tangga memiliki/menguasai komputer | Akses | Susenas, Statistik Telekomunikasi Indonesia | 2025 |
| `pct_desa_4g` | % desa/kelurahan dengan sinyal 5G/4G/LTE (dihitung dari jumlah desa) | Akses | Podes, Statistik Potensi Desa | Podes terbaru (38 prov) |
| `pct_skill_tik` | % remaja & dewasa usia 15-24 dengan keterampilan TIK (SDGs 4.4.1) | Keterampilan | Indikator SDGs BPS | 2025 |
| `rls` | Rata-rata Lama Sekolah (tahun, metode baru) | Keterampilan | IPM BPS | 2026 |

**Keputusan 34 vs 38 provinsi:** Project ini memakai kerangka penuh **38 provinsi** (mencakup 4 provinsi pemekaran Papua: Papua Selatan, Papua Tengah, Papua Pegunungan, dan Papua Barat Daya). Seluruh 6 tabel BPS dan file batas wilayah GeoJSON ([AlfianAliM/Indonesia-GeoJSON](https://github.com/AlfianAliM/Indonesia-GeoJSON), dinormalisasi & disederhanakan menjadi 1,59 MB di `data/geo/indonesia_provinsi.geojson`) telah diverifikasi cocok **38/38 provinsi** tanpa *missing value*.

## Temuan Utama

- **Rentang kesenjangan antar-provinsi sangat lebar:** Pengguna internet berkisar dari `15,40%` (Papua Pegunungan) sampai `91,32%` (Kepulauan Riau), cakupan desa 4G/5G dari `19,53%` sampai `100,00%` (DKI Jakarta), dan keterampilan TIK dari `15,79%` sampai `99,54%` (DI Yogyakarta).
- **Konsistensi model tinggi:** K-Means (`K = 4`, setelah standardisasi z-score) dan Hierarchical Ward sepakat pada **36 dari 38 provinsi (94,7%)**. Hanya 2 provinsi zona perbatasan yang berbeda penempatan, yaitu Kalimantan Utara dan Nusa Tenggara Timur.
- **Paradoks digital terbukti pada data nyata:**
  - **Sinyal bagus belum cukup tanpa adopsi & keterampilan:** Papua Selatan (`86,38%` desa 4G) dan Nusa Tenggara Timur (`82,82%` desa 4G) tertinggal jauh pada keterampilan TIK (`57,49%` dan `86,40%`) serta pengguna internet (`50,02%` dan `62,91%`).
  - **Adopsi kota melaju lebih cepat dari sinyal desa:** Kalimantan Utara (`71,07%` desa 4G) dan Kalimantan Tengah (`73,68%` desa 4G) sudah melampaui median nasional pengguna internet, namun pemerataan jaringan desa pedalaman masih tertinggal.
  - **Pembeda utama kelas atas vs menengah ada pada perangkat produktif:** Kepemilikan komputer rumah tangga di Cluster 0 berkisar `25,95%` sampai `38,42%`, jauh melampaui mayoritas provinsi di Cluster 1 (`12,87%` sampai `23,97%`) meski kepemilikan HP relatif berdekatan.

## Rekomendasi Kebijakan per Cluster

| Cluster | Nama Tipologi | Jumlah Provinsi | Hambatan Utama | Arah Rekomendasi |
|---|---|---|---|---|
| **0** | Pusat & Motor Digital | 6 (DKI Jakarta, Kep. Riau, DI Yogyakarta, Bali, Kaltim, Kaltara) | Pemerataan sinyal pedalaman/pulau (Kaltara, Kaltim, Kepri), keamanan siber, dan talenta digital lanjut | Dorong ekonomi digital bernilai tambah, startup hub, keamanan siber, serta tuntaskan blankspot desa terpencil. |
| **1** | Terhubung Seluler, Produktivitas Belum Optimal | 28 provinsi (mayoritas Sumatera, Jawa, Kalimantan, Sulawesi, Maluku, Papua Barat/Barat Daya/Papua) | Akses perangkat produktif (komputer rumah tangga rendah) dan pemanfaatan produktif UMKM/pendidikan | Perluas akses perangkat produktif (lab komputer sekolah/balai desa), pelatihan UMKM go-digital, dan literasi produktif. |
| **2** | Sinyal Tersedia, Adopsi & Skill Tertinggal | 2 (Nusa Tenggara Timur, Papua Selatan) | Adopsi internet, keterjangkauan perangkat, dan keterampilan TIK meski sinyal 4G desa >82% | Fokus literasi digital intensif, program subsidi/akses perangkat belajar bersama, dan pendampingan komunitas lokal. |
| **3** | Belum Terjangkau (Prioritas Infrastruktur) | 2 (Papua Tengah, Papua Pegunungan) | Infrastruktur dasar (sinyal 4G ~20%, listrik/akses fisik) dan pendidikan dasar (RLS rendah) | Prioritas darurat pembangunan BTS/BAKTI & satelit (SATRIA), internet publik gratis di sekolah/puskesmas, dan percepatan pendidikan dasar. |

## Fitur Dashboard Streamlit (`app/streamlit_app.py`)

1. **Peta Kesiapan Digital:** Choropleth interaktif 38 provinsi dengan filter cluster, mode pewarnaan menurut Tipologi Cluster atau 6 indikator, grafik komposisi cluster, serta kartu rentang kesenjangan dinamis.
2. **Profil & Paradoks:** Grafik diagnosis 3 lapis (*Akses, Pemanfaatan, Keterampilan*), radar chart 6 indikator, tab bedah 3 pola paradoks digital, dan scatterplot kuadran interaktif.
3. **Rapor Provinsi:** Perbandingan satu provinsi terhadap rata-rata nasional (diverging gap chart & tabel skor), peringkat gabungan dari 38 provinsi, diagnosis hambatan + rekomendasi kebijakan, daftar provinsi pembanding setipologi, dan tombol unduh rapor CSV.
4. **Tema Terang & Gelap:** Pengalih tema di bilah kiri yang menyelaraskan seluruh komponen UI, tabel, dan grafik Plotly dengan kontras terverifikasi WCAG AA.
