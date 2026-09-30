# Analisis Harga Beras Indonesia 2026

Repository ini berisi dataset dan pengembangan analisis mengenai **harga beras di Indonesia pada tahun 2026**.

Analisis menggunakan dua kelompok data utama, yaitu harga beras berdasarkan **provinsi dan jenis/kualitas beras** serta rata-rata **harga beras pada tingkat perdagangan besar (grosir) secara nasional**.

Project ini dikembangkan untuk mengeksplorasi pola harga beras antarwilayah, antarjenis beras, serta perubahan harga dari waktu ke waktu. Hasil analisis nantinya akan dikembangkan dalam bentuk visualisasi data, dashboard, atau aplikasi web interaktif.

## Dataset

### 1. Harga Beras Menurut Provinsi dan Jenis Beras

File:

`Harga_Beras_Indonesia_Jan_Jun_2026.xlsx`
sumber: https://www.bi.go.id/hargapangan/TabelHarga/ProdusenDaerah

Dataset berisi harga beras bulanan dari **Januari hingga Juni 2026** berdasarkan provinsi dan jenis/kualitas beras.

Struktur utama dataset:

| Kolom | Keterangan |
|---|---|
| No | Nomor observasi |
| Provinsi | Nama provinsi |
| Jenis Beras | Kategori/kualitas beras |
| Januari 2026 | Harga rata-rata Januari 2026 |
| Februari 2026 | Harga rata-rata Februari 2026 |
| Maret 2026 | Harga rata-rata Maret 2026 |
| April 2026 | Harga rata-rata April 2026 |
| Mei 2026 | Harga rata-rata Mei 2026 |
| Juni 2026 | Harga rata-rata Juni 2026 |

Dataset saat ini mencakup:

- **34 provinsi/wilayah**
- **132 kombinasi provinsi dan jenis beras**
- Periode **Januari–Juni 2026**
- Harga dalam **rupiah per kilogram**
- Beberapa observasi tidak tersedia dan dibiarkan sebagai nilai kosong

Jenis beras yang terdapat dalam dataset:

- Beras Kualitas Bawah 1
- Beras Kualitas Bawah 2
- Beras Kualitas Medium 1
- Beras Kualitas Medium 2
- Beras Kualitas Super 1
- Beras Kualitas Super 2

Kategori tersebut mengikuti klasifikasi komoditas beras yang digunakan dalam **Pusat Informasi Harga Pangan Strategis Nasional (PIHPS) Bank Indonesia**.

---

### 2. Harga Beras Tingkat Perdagangan Besar (Grosir)

File:

`Rata-rata Harga Beras di Tingkat Perdagangan Besar (Grosir) Indonesia, 2026.xlsx`
sumber: https://www.bps.go.id/id/statistics-table/2/Mjk1IzI=/rata-rata-harga-beras-di-tingkat-perdagangan-besar--grosir--indonesia.html

Dataset ini berisi rata-rata harga beras di tingkat perdagangan besar atau grosir secara nasional.

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

Data September–Desember 2026 belum tersedia pada dataset saat ini.

Menurut metadata BPS, indikator harga grosir merupakan rata-rata harga beras per kilogram pada tingkat pedagang besar dan disajikan pada level nasional.

---

## Ruang Lingkup Analisis

Karena dataset harga per provinsi saat ini tersedia hingga Juni 2026, periode utama yang digunakan untuk membandingkan kedua dataset adalah:

**Januari–Juni 2026**

Data Juli–Agustus pada dataset grosir tetap dipertahankan dan dapat digunakan untuk analisis tren nasional tambahan.

Beberapa analisis yang direncanakan meliputi:

1. **Analisis tren harga beras bulanan**
   - Melihat perubahan harga dari Januari hingga Juni 2026.
   - Mengidentifikasi periode kenaikan dan penurunan harga.

2. **Perbandingan harga antarprovinsi**
   - Membandingkan harga rata-rata beras di setiap provinsi.
   - Mengidentifikasi provinsi dengan harga relatif tinggi dan rendah.

3. **Perbandingan berdasarkan kualitas beras**
   - Kualitas Bawah
   - Kualitas Medium
   - Kualitas Super

4. **Analisis perubahan harga**
   - Perubahan harga bulanan (*month-to-month*).
   - Persentase kenaikan atau penurunan harga.

5. **Analisis volatilitas harga**
   - Mengukur seberapa besar perubahan harga pada setiap provinsi dan jenis beras selama periode penelitian.

6. **Perbandingan harga daerah dengan harga grosir nasional**
   - Membandingkan harga beras pada tingkat provinsi dengan rata-rata harga grosir nasional.
   - Mengamati kemungkinan selisih atau *price gap* antara kedua kelompok data.

7. **Analisis distribusi harga**
   - Melihat variasi harga antarprovinsi.
   - Mengidentifikasi wilayah dengan harga yang jauh berbeda dari distribusi nasional.

8. **Ranking harga beras antarprovinsi**
   - Provinsi dengan rata-rata harga tertinggi.
   - Provinsi dengan rata-rata harga terendah.
   - Ranking berdasarkan masing-masing kualitas beras.

---

## Pertanyaan Analisis

Project ini diharapkan dapat menjawab beberapa pertanyaan berikut:

- Bagaimana perkembangan harga beras selama tahun 2026?
- Apakah harga beras menunjukkan kecenderungan meningkat atau menurun?
- Provinsi mana yang memiliki harga beras paling tinggi dan paling rendah?
- Seberapa besar perbedaan harga beras antarprovinsi?
- Bagaimana perbedaan harga antara beras kualitas bawah, medium, dan super?
- Jenis beras mana yang mengalami perubahan harga paling besar?
- Provinsi mana yang memiliki harga beras paling stabil?
- Apakah terdapat pola regional dalam harga beras Indonesia?
- Bagaimana harga beras di tingkat daerah dibandingkan dengan harga grosir nasional?
- Seberapa besar selisih harga antara harga grosir nasional dengan harga yang terpantau di tingkat provinsi?

---

## Tahapan Project

Alur pengembangan project direncanakan sebagai berikut:

`Data Collection` → `Data Cleaning` → `Data Transformation` → `Exploratory Data Analysis` → `Visualization` → `Dashboard / Web Application`

### 1. Data Collection

Mengumpulkan data harga beras dari sumber yang digunakan dalam project.

### 2. Data Cleaning

Proses yang dilakukan antara lain:

- pengecekan data kosong,
- penyamaan nama provinsi,
- penyamaan kategori jenis beras,
- pengecekan tipe data,
- pengecekan duplikasi,
- dan pengecekan konsistensi satuan harga.

### 3. Data Transformation

Dataset akan diubah apabila diperlukan dari format *wide* menjadi format *long/tidy* agar lebih mudah digunakan dalam analisis dan visualisasi.

Contoh struktur data:

| Provinsi | Jenis Beras | Bulan | Harga |
|---|---|---|---:|
| Aceh | Beras Kualitas Medium 1 | Januari 2026 | 15100 |
| Aceh | Beras Kualitas Medium 1 | Februari 2026 | 14650 |
| Aceh | Beras Kualitas Medium 1 | Maret 2026 | 14450 |

### 4. Exploratory Data Analysis

Analisis eksploratif dilakukan untuk memperoleh gambaran mengenai:

- tren harga,
- distribusi harga,
- perbedaan antarprovinsi,
- perbedaan antarjenis beras,
- perubahan bulanan,
- volatilitas,
- serta perbandingan dengan harga grosir nasional.

### 5. Data Visualization

Beberapa visualisasi yang dapat dikembangkan antara lain:

- line chart perkembangan harga bulanan,
- bar chart perbandingan harga antarprovinsi,
- heatmap harga provinsi dan bulan,
- boxplot distribusi harga,
- ranking provinsi,
- peta Indonesia berdasarkan tingkat harga beras,
- dan grafik perbandingan harga provinsi dengan harga grosir nasional.

### 6. Dashboard / Web Application

Tahap akhir project direncanakan berupa visualisasi interaktif atau aplikasi berbasis web.

Fitur yang dapat dikembangkan antara lain:

- filter provinsi,
- filter jenis beras,
- filter periode,
- grafik tren harga,
- perbandingan antarprovinsi,
- perbandingan antarjenis beras,
- indikator perubahan harga,
- ranking provinsi,
- dan visualisasi peta Indonesia.

Platform dan framework yang digunakan akan ditentukan pada tahap pengembangan selanjutnya.

---

## Struktur Repository

Struktur repository akan dikembangkan secara bertahap. Contoh struktur yang direncanakan:

```text
.
├── data/
│   ├── Harga_Beras_Indonesia_Jan_Jun_2026.xlsx
│   └── Rata-rata Harga Beras di Tingkat Perdagangan Besar (Grosir) Indonesia, 2026.xlsx
│
├── notebooks/
│   └── analysis.ipynb
│
├── src/
│   └── data_processing.py
│
├── visualizations/
│   └── ...
│
├── app/
│   └── ...
│
├── README.md
└── requirements.txt
```

Struktur folder dapat berubah sesuai kebutuhan project.

---

## Tools dan Teknologi

Beberapa teknologi yang direncanakan untuk digunakan:

- **Python**
- **Pandas** — pengolahan dan transformasi data
- **NumPy** — perhitungan numerik
- **Matplotlib / Seaborn / Plotly** — visualisasi data
- **Jupyter Notebook** — eksplorasi dan analisis data

Untuk tahap dashboard atau aplikasi web, teknologi akan ditentukan kemudian. Beberapa alternatif yang dapat dipertimbangkan antara lain:

- Streamlit
- Plotly Dash
- Flask
- atau framework visualisasi/web lainnya

---

## Catatan Data

Beberapa hal yang perlu diperhatikan dalam penggunaan dataset:

- Tidak semua provinsi memiliki seluruh kategori beras.
- Terdapat beberapa nilai kosong pada dataset provinsi.
- Nilai kosong tidak langsung diubah menjadi nol karena nilai nol memiliki interpretasi yang berbeda dengan data yang tidak tersedia.
- Dataset harga provinsi saat ini tersedia sampai Juni 2026.
- Dataset harga grosir nasional saat ini tersedia sampai Agustus 2026.
- Perbandingan langsung antara kedua dataset perlu memperhatikan **level observasi dan metodologi pengumpulan data yang berbeda**.
- Harga grosir nasional tidak dapat dianggap sama dengan harga pada tingkat pasar/konsumen di setiap provinsi.

---

## Status Project

**Work in Progress**

Tahapan saat ini:

- [x] Pengumpulan dataset harga beras
- [x] Penggabungan data harga berdasarkan provinsi
- [x] Standardisasi awal struktur dataset
- [x] Penambahan dataset harga grosir nasional
- [ ] Data cleaning lanjutan
- [ ] Transformasi data ke format analisis
- [ ] Exploratory Data Analysis (EDA)
- [ ] Analisis perbandingan harga
- [ ] Visualisasi data
- [ ] Penentuan konsep dashboard/web
- [ ] Pengembangan dashboard/web
- [ ] Deployment

---

## Tujuan Akhir

Project ini diharapkan dapat menghasilkan sebuah sistem analisis dan visualisasi yang memudahkan pengguna dalam memahami **perkembangan, perbedaan, dan pola harga beras di Indonesia berdasarkan wilayah, kualitas beras, serta tingkat perdagangan**.

Project masih dalam tahap pengembangan dan akan diperbarui seiring penambahan data, analisis, serta fitur visualisasi.
