import pandas as pd


# =========================================================
# PATH DATA
# =========================================================

GROSIR_FILE = "data/raw/grosir/Rata-rata Harga Beras di Tingkat Perdagangan Besar (Grosir) Indonesia, 2026.xlsx"

PIHPS_FILE = "data/raw/pihps/Harga_Beras_Indonesia_Januari_Agustus_2026_Gabungan.xlsx"

SP2KP_FILE = "data/raw/sp2kp/Harga Beras Bedasarkan Pasar.xlsx"

OUTPUT_DIR = "data/processed"


# =========================================================
# 1. TRANSFORM GROSIR
# =========================================================

def transform_grosir():

    print("\n=== TRANSFORM GROSIR ===")

    df = pd.read_excel(
        GROSIR_FILE,
        sheet_name="Sheet1",
        header=None
    )

    # Ambil bulan dari baris ke-4
    bulan = df.iloc[3, 1:9].tolist()

    # Ambil harga dari baris ke-5
    harga = df.iloc[4, 1:9].tolist()

    df_grosir = pd.DataFrame({
        "bulan": bulan,
        "harga": harga
    })

    # Tambahkan tahun
    df_grosir["tahun"] = 2026

    # Ubah nama bulan menjadi angka
    bulan_map = {
        "Januari": 1,
        "Februari": 2,
        "Maret": 3,
        "April": 4,
        "Mei": 5,
        "Juni": 6,
        "Juli": 7,
        "Agustus": 8
    }

    df_grosir["bulan_num"] = df_grosir["bulan"].map(bulan_map)

    # Buat tanggal
    df_grosir["tanggal"] = pd.to_datetime(
        df_grosir["tahun"].astype(str)
        + "-"
        + df_grosir["bulan_num"].astype(str)
        + "-01"
    )

    # Harga menjadi numerik
    df_grosir["harga"] = pd.to_numeric(
        df_grosir["harga"],
        errors="coerce"
    )

    # Tambahkan sumber
    df_grosir["sumber"] = "Grosir"

    # Pilih kolom akhir
    df_grosir = df_grosir[
        ["tanggal", "harga", "sumber"]
    ]

    return df_grosir


# =========================================================
# 2. TRANSFORM PIHPS
# =========================================================

def transform_pihps():

    print("\n=== TRANSFORM PIHPS ===")

    df = pd.read_excel(
        PIHPS_FILE,
        sheet_name="Gabungan Provinsi",
        header=None
    )

    # Data dimulai dari baris setelah header
    df = df.iloc[15:].copy()

    # Ambil hanya 10 kolom pertama:
    # No, Provinsi, Jenis Beras, Jan - Ags
    df = df.iloc[:, :11]

    df.columns = [
        "no",
        "provinsi",
        "jenis_beras",
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus"
    ]

    # Buang baris kosong
    df = df.dropna(
        subset=["provinsi", "jenis_beras"]
    )

    # Ubah format wide → long
    df_pihps = df.melt(
        id_vars=["no", "provinsi", "jenis_beras"],
        value_vars=[
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus"
        ],
        var_name="bulan",
        value_name="harga"
    )

    # Mapping bulan
    bulan_map = {
        "Januari": 1,
        "Februari": 2,
        "Maret": 3,
        "April": 4,
        "Mei": 5,
        "Juni": 6,
        "Juli": 7,
        "Agustus": 8
    }

    df_pihps["bulan_num"] = df_pihps["bulan"].map(
        bulan_map
    )

    # Buat tanggal
    df_pihps["tanggal"] = pd.to_datetime(
        "2026-"
        + df_pihps["bulan_num"].astype(str)
        + "-01"
    )

    # Harga menjadi numerik
    df_pihps["harga"] = pd.to_numeric(
        df_pihps["harga"],
        errors="coerce"
    )

    # Data 0 berarti tidak tersedia
    df_pihps.loc[
        df_pihps["harga"] <= 0,
        "harga"
    ] = pd.NA

    # Tambahkan sumber
    df_pihps["sumber"] = "PIHPS"

    # Pilih kolom akhir
    df_pihps = df_pihps[
        [
            "tanggal",
            "provinsi",
            "jenis_beras",
            "harga",
            "sumber"
        ]
    ]

    return df_pihps


# =========================================================
# 3. TRANSFORM SP2KP
# =========================================================

def transform_sp2kp():

    print("\n=== TRANSFORM SP2KP ===")

    df = pd.read_excel(
        SP2KP_FILE,
        sheet_name="pasar semua indo"
    )

    # Bersihkan nama kolom
    df.columns = df.columns.str.strip()

    # Ubah wide → long
    df_sp2kp = df.melt(
        id_vars=[
            "Provinsi",
            "Nama Pasar",
            "Jenis Beras"
        ],
        value_vars=[
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus"
        ],
        var_name="bulan",
        value_name="harga"
    )

    # Rename kolom
    df_sp2kp = df_sp2kp.rename(
        columns={
            "Provinsi": "provinsi",
            "Nama Pasar": "nama_pasar",
            "Jenis Beras": "jenis_beras"
        }
    )

    # Mapping bulan
    bulan_map = {
        "Januari": 1,
        "Februari": 2,
        "Maret": 3,
        "April": 4,
        "Mei": 5,
        "Juni": 6,
        "Juli": 7,
        "Agustus": 8
    }

    df_sp2kp["bulan_num"] = df_sp2kp["bulan"].map(
        bulan_map
    )

    # Buat tanggal
    df_sp2kp["tanggal"] = pd.to_datetime(
        "2026-"
        + df_sp2kp["bulan_num"].astype(str)
        + "-01"
    )

    # Harga numerik
    df_sp2kp["harga"] = pd.to_numeric(
        df_sp2kp["harga"],
        errors="coerce"
    )

    # SP2KP menggunakan satuan Rp/kg.
    # Nilai seperti 14.700 dari Excel terbaca sebagai 14.7,
    # sehingga dikembalikan ke nilai harga sebenarnya.
    df_sp2kp.loc[
        df_sp2kp["harga"].notna() &
        (df_sp2kp["harga"] < 1000),
        "harga"
    ] = df_sp2kp.loc[
        df_sp2kp["harga"].notna() &
        (df_sp2kp["harga"] < 1000),
        "harga"
    ] * 1000

    # Harga tidak valid
    df_sp2kp.loc[
        df_sp2kp["harga"] <= 0,
        "harga"
    ] = pd.NA

    # Tambahkan sumber
    df_sp2kp["sumber"] = "SP2KP"

    # Pilih kolom akhir
    df_sp2kp = df_sp2kp[
        [
            "tanggal",
            "provinsi",
            "nama_pasar",
            "jenis_beras",
            "harga",
            "sumber"
        ]
    ]

    return df_sp2kp


# =========================================================
# 4. JALANKAN TRANSFORM
# =========================================================

if __name__ == "__main__":

    grosir = transform_grosir()
    pihps = transform_pihps()
    sp2kp = transform_sp2kp()

    # Buat folder processed jika belum ada
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Simpan hasil transform
    grosir.to_csv(
        f"{OUTPUT_DIR}/grosir_clean.csv",
        index=False
    )

    pihps.to_csv(
        f"{OUTPUT_DIR}/pihps_clean.csv",
        index=False
    )

    sp2kp.to_csv(
        f"{OUTPUT_DIR}/sp2kp_clean.csv",
        index=False
    )

    # Informasi hasil
    print("\n=== HASIL TRANSFORM ===")

    print("Grosir :", grosir.shape)
    print("PIHPS  :", pihps.shape)
    print("SP2KP  :", sp2kp.shape)

    print("\nTransform berhasil!")