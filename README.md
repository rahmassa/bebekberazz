# 🦆 BebekBerazz — Indonesian Rice Price Data Warehouse & Analytics

Project **BebekBerazz** merupakan project akhir Data Warehousing yang mengintegrasikan beberapa sumber data harga beras di Indonesia untuk membangun sistem penyimpanan, pengolahan, analisis, dan visualisasi harga beras berbasis **DuckDB, DuckLake, dan Streamlit**.

Project ini menggunakan tiga kelompok data utama yang disebut sebagai **“3 Bebek”**:

1. 🦆 **Bebek Grosir** — harga beras tingkat perdagangan besar/grosir nasional dari BPS.
2. 🦆 **Bebek Provinsi PIHPS** — harga beras berdasarkan provinsi dan jenis/kualitas beras dari PIHPS Bank Indonesia.
3. 🦆 **Bebek Pasar SP2KP** — harga beras berdasarkan pasar di kabupaten/kota dari SP2KP Kementerian Perdagangan.

Ketiga sumber memiliki tingkat granularitas yang berbeda dan akan disimpan terlebih dahulu dalam database DuckDB masing-masing, kemudian diintegrasikan ke dalam **DuckLake** untuk proses analitik dan visualisasi melalui dashboard Streamlit.

---

# 🎯 Tujuan Project

Project ini bertujuan membangun sebuah **data warehouse harga beras Indonesia** yang memungkinkan pengguna untuk melihat harga beras dari tingkat nasional hingga tingkat pasar.

Analisis diarahkan untuk menjawab pertanyaan seperti:

- Bagaimana perkembangan harga beras dari bulan ke bulan?
- Berapa rata-rata dan median harga beras di suatu provinsi?
- Seberapa besar kenaikan atau penurunan harga dibanding bulan sebelumnya?
- Provinsi mana yang memiliki harga beras relatif tinggi atau rendah?
- Seberapa besar fluktuasi harga beras di masing-masing daerah?
- Bagaimana perbedaan harga antarjenis atau kualitas beras?
- Bagaimana harga pada tingkat pasar dibandingkan dengan harga tingkat provinsi?
- Bagaimana perbedaan harga daerah/pasar dengan harga grosir nasional?
- Kabupaten/kota atau pasar mana yang mengalami perubahan harga paling besar?
- Pasar mana yang memiliki harga relatif stabil dan pasar mana yang lebih fluktuatif?
- Bagaimana pola harga beras jika pengguna memilih lokasi tertentu?

---

# 📦 Dataset

## 1. 🦆 Bebek Grosir — Harga Beras Grosir Nasional

**Sumber:** Badan Pusat Statistik (BPS)

Dataset:

`Rata-rata Harga Beras di Tingkat Perdagangan Besar (Grosir) Indonesia, 2026.xlsx`

Dataset berisi rata-rata harga beras pada tingkat perdagangan besar/grosir secara nasional.

Data yang tersedia saat ini:

| Bulan | Harga (Rp/kg) |
|---|---:|
| Januari 2026 | 14.218 |
| Februari 2026 | 14.282 |
| Maret 2026 | 14.419 |
| April 2026 | 14.476 |
| Mei 2026 | 14.574 |
| Juni 2026 | 14.694 |
| Juli 2026 | 14.783 |
| Agustus 2026 | 14.901 |

Granularitas data:

```text
Nasional × Bulan
```

Dataset ini digunakan terutama sebagai **benchmark harga tingkat grosir nasional**.

---

## 2. 🦆 Bebek Provinsi PIHPS — Harga Beras Provinsi

**Sumber:** Pusat Informasi Harga Pangan Strategis Nasional (PIHPS), Bank Indonesia.

Dataset:

`Harga_Beras_Indonesia_Jan_Jun_2026.xlsx`

Dataset berisi harga beras berdasarkan:

- provinsi,
- jenis/kualitas beras,
- dan bulan.

Periode yang tersedia saat ini:

**Januari–Agustus 2026**

Dataset saat ini mencakup:

- 34 provinsi/wilayah,
- 132 kombinasi provinsi dan jenis beras,
- harga dalam rupiah per kilogram,
- serta beberapa nilai yang tidak tersedia.

Jenis beras:

- Beras Kualitas Bawah 1
- Beras Kualitas Bawah 2
- Beras Kualitas Medium 1
- Beras Kualitas Medium 2
- Beras Kualitas Super 1
- Beras Kualitas Super 2

Granularitas:

```text
Provinsi × Jenis Beras × Bulan
```

Contoh:

| Provinsi | Jenis Beras | Bulan | Harga |
|---|---|---|---:|
| Aceh | Beras Kualitas Medium 1 | Januari 2026 | 15100 |
| Aceh | Beras Kualitas Medium 1 | Februari 2026 | 14650 |
| Aceh | Beras Kualitas Medium 1 | Maret 2026 | 14450 |

---

## 3. 🦆 Bebek Pasar SP2KP — Harga Beras Tingkat Pasar

**Sumber:** Sistem Pemantauan Pasar dan Kebutuhan Pokok (SP2KP), Kementerian Perdagangan.

Dataset ini akan ditambahkan pada tahap selanjutnya.

Data yang direncanakan mencakup harga beras berdasarkan:

```text
Provinsi
   ↓
Kabupaten/Kota
   ↓
Pasar
   ↓
Jenis Beras
   ↓
Bulan
   ↓
Harga
```

Granularitas utama yang akan digunakan:

```text
Pasar × Kabupaten/Kota × Provinsi × Jenis Beras × Bulan
```

Contoh struktur yang diharapkan:

| Provinsi | Kabupaten/Kota | Pasar | Jenis Beras | Bulan | Harga |
|---|---|---|---|---|---:|
| Jawa Timur | Surabaya | Pasar A | Medium | Januari 2026 | ... |
| Jawa Timur | Surabaya | Pasar A | Medium | Februari 2026 | ... |
| Jawa Timur | Surabaya | Pasar B | Medium | Januari 2026 | ... |

Dataset ini memungkinkan analisis yang lebih detail dibandingkan dua sumber lainnya karena pengguna dapat melakukan **drill-down hingga tingkat pasar**.

> Catatan: apabila dataset SP2KP yang digunakan dalam project merupakan hasil agregasi bulanan, maka perubahan yang dianalisis adalah perubahan antarbulan. Analisis kenaikan atau penurunan harga harian memerlukan data SP2KP pada granularitas harian.

---

# 🔗 Integrasi Tiga Sumber Data

Ketiga dataset memiliki tingkat granularitas berbeda:

| Sumber | Level Wilayah | Waktu | Detail |
|---|---|---|---|
| BPS Grosir | Nasional | Bulanan | Harga grosir |
| PIHPS | Provinsi | Bulanan | Jenis/kualitas beras |
| SP2KP | Pasar / Kab/Kota / Provinsi | Bulanan | Harga pasar dan jenis beras |

Karena granularitas dan metodologi sumber data berbeda, data tidak langsung dianggap sebagai harga yang identik.

Integrasi digunakan untuk menghasilkan **perbandingan dan indikator selisih harga**, bukan untuk mengasumsikan bahwa perbedaan harga otomatis merupakan keuntungan atau margin pelaku perdagangan.

Contoh:

```text
Harga Grosir Nasional
        ↓
     Rp14.500

Harga Provinsi
        ↓
     Rp15.300

Harga Pasar
        ↓
     Rp15.800
```

Dari data tersebut dapat dihitung:

```text
Gap Provinsi – Grosir
Gap Pasar – Provinsi
Gap Pasar – Grosir
```

Kemudian perubahan gap dapat diamati dari bulan ke bulan.

---

# 🏗️ Arsitektur Data Warehousing

Project mengikuti arsitektur:

```text
                 DATA SOURCES
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    BPS Grosir     PIHPS Provinsi   SP2KP Pasar
        │              │              │
        ▼              ▼              ▼
 bebek_grosir     bebek_pihps     bebek_sp2kp
   .duckdb           .duckdb         .duckdb
        │              │              │
        └──────────────┼──────────────┘
                       │
                 ETL / ELT
                       │
                       ▼
                 DUCKLAKE
                       │
          shared_catalog.ducklake
                       +
              lakehouse_storage/
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      grosir          pihps          sp2kp
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
                ANALYTICS MART
                       │
                       ▼
            SQL AGGREGATION & KPI
                       │
                       ▼
               STREAMLIT DASHBOARD
```

---

# 🗄️ Local DuckDB

Setiap sumber data memiliki database DuckDB tersendiri.

Rencana database:

```text
bebek_grosir.duckdb
bebek_pihps.duckdb
bebek_sp2kp.duckdb
```

Fungsi local DuckDB adalah sebagai **raw/staging layer** sebelum data terintegrasi ke DuckLake.

Contoh:

```text
BPS Excel
   ↓
bebek_grosir.duckdb
   ↓
cleaning / transformation
   ↓
DuckLake
```

---

# 🦆 DuckLake

Data yang telah diproses kemudian diintegrasikan ke satu environment DuckLake.

Rencana struktur:

```text
DuckLake
│
├── grosir
│   └── harga_nasional_bulanan
│
├── pihps
│   └── harga_provinsi_bulanan
│
├── sp2kp
│   └── harga_pasar_bulanan
│
└── analytics
    ├── harga_bulanan
    ├── province_summary
    ├── market_summary
    ├── price_gap
    └── volatility_summary
```

DuckLake menggunakan:

```text
shared_catalog.ducklake
```

sebagai catalog/metadata dan:

```text
lakehouse_storage/
```

sebagai lokasi penyimpanan data fisik.

---

# 🔄 ETL / ELT Process

## 1. Extract

Mengambil data dari ketiga sumber:

```text
BPS
PIHPS
SP2KP
```

Data sumber dipertahankan dalam bentuk raw agar data asli tetap dapat ditelusuri.

---

## 2. Transform

Transformasi yang direncanakan antara lain:

- mengubah format wide menjadi long/tidy,
- mengubah kolom harga menjadi numerik,
- standardisasi format tanggal,
- membuat kolom tahun dan bulan,
- standardisasi nama provinsi,
- standardisasi nama kabupaten/kota,
- standardisasi nama pasar,
- standardisasi kategori beras,
- standardisasi satuan menjadi Rp/kg,
- pengecekan missing value,
- pengecekan duplikasi,
- validasi harga,
- menambahkan informasi sumber data,
- dan menyesuaikan granularitas data.

Contoh transformasi PIHPS:

```text
SEBELUM

Provinsi | Jenis | Jan | Feb | Mar | Apr
Aceh     | Medium| ... | ... | ... | ...


SESUDAH

Provinsi | Jenis | Bulan | Harga
Aceh     | Medium| Jan   | ...
Aceh     | Medium| Feb   | ...
Aceh     | Medium| Mar   | ...
```

---

## 3. Load

Data hasil transformasi dimuat ke DuckLake sesuai schema masing-masing:

```text
BPS   → grosir.harga_nasional_bulanan

PIHPS → pihps.harga_provinsi_bulanan

SP2KP → sp2kp.harga_pasar_bulanan
```

---

# 📊 Proses Agregasi

Data detail akan diagregasi menggunakan SQL agar dapat menghasilkan informasi yang dibutuhkan dashboard.

Contoh:

### Rata-rata harga per provinsi

```sql
SELECT
    provinsi,
    bulan,
    AVG(harga) AS rata_rata_harga
FROM pihps.harga_provinsi_bulanan
GROUP BY provinsi, bulan;
```

### Median harga

Median digunakan untuk melihat **harga tengah** sehingga hasil tidak terlalu dipengaruhi harga yang sangat tinggi atau rendah.

```text
Median Harga Provinsi
```

akan menjadi salah satu indikator utama.

### Harga pasar per kabupaten/kota

```text
Provinsi
   ↓
Kabupaten/Kota
   ↓
Pasar
   ↓
AVG / MEDIAN / MIN / MAX Harga
```

---

# 📈 Arah Analisis

## 1. Tren Harga Bulanan

Melihat bagaimana harga beras berubah dari satu bulan ke bulan berikutnya.

Output:

- grafik bulanan,
- nilai perubahan harga,
- persentase perubahan harga,
- tren naik/turun.

Contoh:

```text
Jan → Rp14.500
Feb → Rp14.800
Mar → Rp14.600
Apr → Rp15.100
```

---

## 2. Perubahan Month-to-Month

Menghitung:

```text
Perubahan Harga
= Harga Bulan Sekarang - Harga Bulan Sebelumnya
```

dan:

```text
MoM (%)
=
(Harga Sekarang - Harga Sebelumnya)
─────────────────────────────────── × 100%
        Harga Sebelumnya
```

---

## 3. Harga Tengah Provinsi

Untuk setiap provinsi dapat dihitung:

- mean,
- median,
- minimum,
- maksimum.

Median digunakan untuk menjawab pertanyaan seperti:

> “Harga tengah beras di Jawa Timur bulan ini berapa?”

---

## 4. Fluktuasi Harga

Fluktuasi dapat dianalisis menggunakan:

- range harga,
- standard deviation,
- perubahan bulanan,
- persentase perubahan,
- nilai tertinggi,
- nilai terendah.

Tujuannya untuk mengetahui daerah atau pasar dengan harga yang relatif:

```text
stabil
vs
fluktuatif
```

---

## 5. Perbandingan Antarprovinsi

Analisis meliputi:

- provinsi dengan harga tertinggi,
- provinsi dengan harga terendah,
- median harga provinsi,
- perbedaan harga antarprovinsi,
- perbandingan berdasarkan jenis beras.

---

## 6. Drill-down Provinsi → Kabupaten/Kota → Pasar

Dataset SP2KP akan memungkinkan pengguna melakukan eksplorasi:

```text
Jawa Timur
    ↓
Surabaya
    ↓
Pasar tertentu
    ↓
Jenis beras
    ↓
Grafik bulanan
```

Setelah pasar dipilih, dashboard dapat menampilkan:

```text
Harga saat ini
Harga bulan sebelumnya
Perubahan Rp
Perubahan %
Harga tertinggi
Harga terendah
Rata-rata
Median
Fluktuasi
```

---

## 7. Perbandingan Antarlevel Harga

Analisis dapat membandingkan:

```text
BPS Grosir Nasional
        vs
PIHPS Provinsi
        vs
SP2KP Pasar
```

Indikator yang dapat dihitung:

```text
Gap Pasar vs Provinsi

Gap Provinsi vs Grosir

Gap Pasar vs Grosir
```

Perbandingan dilakukan dengan memperhatikan bahwa masing-masing dataset memiliki metodologi dan granularitas yang berbeda.

---

# 🖥️ Dashboard Streamlit

Dashboard akan dikembangkan menggunakan **Streamlit**.

## Halaman 1 — National Overview

Menampilkan:

- harga grosir nasional,
- rata-rata harga provinsi,
- median harga provinsi,
- tren harga nasional,
- perubahan harga bulanan,
- provinsi harga tertinggi,
- provinsi harga terendah.

---

## Halaman 2 — Province Analysis

Filter:

```text
Provinsi
Jenis Beras
Periode
```

Visualisasi:

- grafik harga bulanan,
- rata-rata harga,
- median harga,
- perubahan MoM,
- ranking provinsi,
- volatilitas harga.

---

## Halaman 3 — Market Explorer

Filter bertingkat:

```text
Provinsi
   ↓
Kabupaten/Kota
   ↓
Pasar
   ↓
Jenis Beras
```

Output:

- harga per bulan,
- perubahan harga,
- rata-rata harga,
- median,
- harga minimum,
- harga maksimum,
- indikator fluktuasi.

---

## Halaman 4 — Price Comparison

Membandingkan:

```text
Grosir
vs
Provinsi
vs
Pasar
```

Visualisasi:

- multi-line chart,
- price gap,
- perubahan gap bulanan,
- tabel perbandingan.

---

# 🧭 Contoh User Flow Dashboard

Misalnya pengguna ingin mengetahui kondisi harga beras di Surabaya.

Pengguna memilih:

```text
Provinsi        : Jawa Timur
Kabupaten/Kota  : Surabaya
Pasar           : Pasar Wonokromo
Jenis Beras     : Medium
```

Jika data tersebut tersedia, dashboard dapat memberikan:

```text
Harga bulan terakhir      Rp ...
Harga bulan sebelumnya    Rp ...

Perubahan                 +Rp ...
Perubahan (%)             +...%

Harga rata-rata           Rp ...
Harga median              Rp ...

Harga tertinggi           Rp ...
Harga terendah            Rp ...

Fluktuasi                 ...
```

Kemudian:

```text
          GRAFIK HARGA BULANAN

Harga
  │
  │             ●
  │       ●           ●
  │   ●
  │
  └────────────────────────── Bulan
      Jan Feb Mar Apr Mei ...
```

Di bawahnya dapat ditampilkan perbandingan dengan:

```text
Rata-rata Jawa Timur
Rata-rata nasional/grosir
```

---

# 📁 Rencana Struktur Repository

```text
bebekberazz/
│
├── data/
│   ├── raw/
│   │   ├── grosir/
│   │   ├── pihps/
│   │   └── sp2kp/
│   │
│   └── processed/
│
├── databases/
│   ├── bebek_grosir.duckdb
│   ├── bebek_pihps.duckdb
│   ├── bebek_sp2kp.duckdb
│   └── shared_catalog.ducklake
│
├── lakehouse_storage/
│
├── src/
│   ├── ingest.py
│   ├── transform.py
│   └── analytics.py
│
├── app/
│   └── dashboard.py
│
├── README.md
└── requirements.txt
```

Struktur dapat berubah selama proses implementasi.

---

# ⚙️ Alur Menjalankan Project

Secara umum project akan dijalankan dengan urutan:

```text
1. INGEST DATA
        ↓
2. CREATE LOCAL DUCKDB
        ↓
3. CLEAN & TRANSFORM
        ↓
4. LOAD TO DUCKLAKE
        ↓
5. BUILD ANALYTICAL TABLES
        ↓
6. RUN STREAMLIT DASHBOARD
```

Secara teknis nantinya kurang lebih:

```bash
python src/ingest.py
```

kemudian:

```bash
python src/transform.py
```

dan setelah proses data selesai:

```bash
streamlit run app/dashboard.py
```

---

# 🛠️ Tools dan Teknologi

Project direncanakan menggunakan:

- **Python**
- **DuckDB** — local database dan SQL processing
- **DuckLake** — integrated lakehouse/catalog
- **Pandas** — cleaning dan transformasi
- **SQL** — integrasi, agregasi, dan analytical query
- **Streamlit** — dashboard interaktif
- **Plotly** — visualisasi interaktif
- **Git / GitHub** — version control dan repository

---

# ⚠️ Catatan Data

Beberapa hal yang perlu diperhatikan:

- Tidak semua provinsi memiliki seluruh jenis beras.
- Missing value tidak otomatis diubah menjadi nol.
- Nama provinsi, kabupaten/kota, dan pasar perlu distandardisasi sebelum integrasi.
- Klasifikasi jenis beras antar sumber mungkin berbeda dan membutuhkan mapping.
- BPS, PIHPS, dan SP2KP memiliki granularitas serta metode pengumpulan yang berbeda.
- Harga grosir tidak dapat langsung dianggap sama dengan harga pasar.
- Selisih harga antar sumber disebut sebagai **price gap**, bukan otomatis sebagai margin keuntungan.
- Analisis harian hanya dapat dilakukan apabila data harian tersedia.
- Perbandingan lintas sumber hanya dilakukan pada periode dan kategori yang dapat disejajarkan.

---

# 🚧 Status Project

**Work in Progress**

### Data

- [x] Dataset harga beras provinsi PIHPS
- [x] Dataset harga grosir nasional BPS
- [ ] Dataset harga pasar SP2KP
- [x] Standardisasi awal dataset PIHPS
- [ ] Standardisasi seluruh sumber data

### Data Warehousing

- [ ] Membuat `bebek_grosir.duckdb`
- [ ] Membuat `bebek_pihps.duckdb`
- [ ] Membuat `bebek_sp2kp.duckdb`
- [ ] Implementasi ETL
- [ ] Implementasi DuckLake
- [ ] Membuat analytical/data mart tables

### Analytics

- [ ] Analisis tren harga
- [ ] Analisis perubahan bulanan
- [ ] Analisis median harga
- [ ] Analisis volatilitas
- [ ] Analisis antarprovinsi
- [ ] Analisis kabupaten/kota dan pasar
- [ ] Analisis price gap
- [ ] Validasi perbandingan antar sumber

### Dashboard

- [ ] National Overview
- [ ] Province Analysis
- [ ] Market Explorer
- [ ] Price Comparison
- [ ] Deployment Streamlit

---

# 🎯 Expected Output

Output akhir project berupa sebuah **data warehouse dan dashboard analitik harga beras Indonesia** yang dapat digunakan untuk mengeksplorasi perkembangan harga dari tingkat nasional hingga pasar.

Sistem diharapkan memungkinkan pengguna melakukan analisis:

```text
NASIONAL
   ↓
PROVINSI
   ↓
KABUPATEN / KOTA
   ↓
PASAR
   ↓
JENIS BERAS
   ↓
PERIODE
```

dan menghasilkan informasi mengenai:

```text
Harga
Tren
Perubahan
Median
Fluktuasi
Perbandingan wilayah
Price gap
```

Dengan demikian, **BebekBerazz** tidak hanya berfungsi sebagai project visualisasi data, tetapi sebagai implementasi proses **Data Ingestion → ETL → Data Warehouse/Lakehouse → Analytics → Interactive Dashboard** menggunakan DuckDB, DuckLake, dan Streamlit.
