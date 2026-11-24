"""Path, daftar indikator, dan daftar provinsi yang dipakai di seluruh project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_GEO = ROOT / "data" / "geo"
FIGURES = ROOT / "reports" / "figures"

MASTER_FILE = DATA_PROCESSED / "indikator_digital_provinsi.csv"
CLUSTER_FILE = DATA_PROCESSED / "provinsi_cluster.csv"
GEOJSON_FILE = DATA_GEO / "indonesia_provinsi.geojson"

RANDOM_STATE = 42
FIG_DPI = 300

# Kolom indikator -> (label, lapis). Lapis dipakai untuk radar chart & diagnosis hambatan.
INDICATORS = {
    "pct_internet": ("% penduduk 5+ mengakses internet", "Pemanfaatan"),
    "pct_hp": ("% penduduk memiliki/menguasai HP", "Akses"),
    "pct_komputer": ("% rumah tangga memiliki komputer", "Akses"),
    "pct_desa_4g": ("% desa/kelurahan dengan sinyal 4G/LTE", "Akses"),
    "pct_skill_tik": ("% remaja & dewasa dengan keterampilan TIK", "Keterampilan"),
    "rls": ("Rata-rata Lama Sekolah (tahun)", "Keterampilan"),
}

# Variabel validasi eksternal: TIDAK masuk clustering.
VALIDATION_VARS = {
    "ip_tik": "Indeks Pembangunan TIK",
    "pdrb_per_kapita": "PDRB per kapita (ribu Rp)",
}

FEATURES = list(INDICATORS)

PROVINSI_38 = [
    "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi",
    "Sumatera Selatan", "Bengkulu", "Lampung", "Kepulauan Bangka Belitung",
    "Kepulauan Riau", "DKI Jakarta", "Jawa Barat", "Jawa Tengah",
    "DI Yogyakarta", "Jawa Timur", "Banten", "Bali", "Nusa Tenggara Barat",
    "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah",
    "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara",
    "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan",
    "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku",
    "Maluku Utara", "Papua Barat", "Papua Barat Daya", "Papua",
    "Papua Selatan", "Papua Tengah", "Papua Pegunungan",
]

PAPUA_BARU = ["Papua Barat Daya", "Papua Selatan", "Papua Tengah", "Papua Pegunungan"]
PROVINSI_34 = [p for p in PROVINSI_38 if p not in PAPUA_BARU]

# Ejaan nama provinsi yang sering muncul di tabel BPS / GeoJSON -> nama baku di atas.
PROVINSI_ALIASES = {
    "KEP. BANGKA BELITUNG": "Kepulauan Bangka Belitung",
    "BANGKA BELITUNG": "Kepulauan Bangka Belitung",
    "KEP. RIAU": "Kepulauan Riau",
    "DKI JAKARTA": "DKI Jakarta",
    "D K I JAKARTA": "DKI Jakarta",
    "JAKARTA RAYA": "DKI Jakarta",
    "DI YOGYAKARTA": "DI Yogyakarta",
    "D I YOGYAKARTA": "DI Yogyakarta",
    "DAERAH ISTIMEWA YOGYAKARTA": "DI Yogyakarta",
    "YOGYAKARTA": "DI Yogyakarta",
    "NTB": "Nusa Tenggara Barat",
    "NTT": "Nusa Tenggara Timur",
    "PAPUA BARAT DAYA": "Papua Barat Daya",
    "PAPUA PEGUNUNGAN": "Papua Pegunungan",
}
