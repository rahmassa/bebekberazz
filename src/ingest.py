
import os
import duckdb
import pandas as pd
from pathlib import Path


# Menentukan lokasi utama project
BASE_DIR = Path(__file__).resolve().parents[1]


def init_databases():
    # Pastikan folder databases tersedia
    db_dir = BASE_DIR / "databases"
    db_dir.mkdir(parents=True, exist_ok=True)

    db_paths = {
        "grosir": db_dir / "bebek_grosir.duckdb",
        "pihps": db_dir / "bebek_pihps.duckdb",
        "sp2kp": db_dir / "bebek_sp2kp.duckdb",
        "produksi": db_dir / "bebek_produksi.duckdb"
    }

    print("🦆 Memulai Inisialisasi Database DuckDB BebekBerazz...")

    # Inisialisasi seluruh database
    for name, path in db_paths.items():
        conn = duckdb.connect(str(path))

        conn.execute("""
            CREATE TABLE IF NOT EXISTS _metadata (
                initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.close()
        print(f"  [✓] Database {name} berhasil dibuat: {path}")

    # Import data produksi beras
    import_data_produksi(db_paths["produksi"])


def import_data_produksi(db_path):
    print("\n🌾 Memulai Import Data Produksi Beras...")

    csv_path = BASE_DIR / "data" / "raw" / "bdsp" / "produksibraz.csv"

    if not csv_path.exists():
        print(f"  [!] File CSV tidak ditemukan: {csv_path}")
        return

    # Membaca dataset
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Mapping nama bulan Indonesia
    bulan_mapping = {
        "Januari": 1,
        "Februari": 2,
        "Maret": 3,
        "April": 4,
        "Mei": 5,
        "Juni": 6,
        "Juli": 7,
        "Agustus": 8,
        "September": 9,
        "Oktober": 10,
        "November": 11,
        "Desember": 12
    }

    # Membersihkan nama kolom
    df.columns = df.columns.str.strip()

    # Mengubah nama bulan menjadi angka
    df["bulan_num"] = (
        df["Nama_Bulan"]
        .astype(str)
        .str.strip()
        .map(bulan_mapping)
    )

    # Memastikan data bulan valid
    if df["bulan_num"].isna().any():
        raise ValueError("Terdapat nama bulan yang tidak dikenali!")

    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="raise")
    df["Produksi_Beras"] = pd.to_numeric(
        df["Produksi_Beras"], errors="raise"
    )

    # Membentuk periode data
    df["periode"] = pd.to_datetime(
        dict(
            year=df["Tahun"],
            month=df["bulan_num"],
            day=1
        )
    )

    # Menyesuaikan nama kolom
    df = df.rename(columns={
        "Tahun": "tahun",
        "Nama_Bulan": "bulan_nama",
        "Produksi_Beras": "produksi_ton"
    })

    # Memilih kolom yang digunakan
    df = df[
        [
            "periode",
            "tahun",
            "bulan_num",
            "bulan_nama",
            "produksi_ton"
        ]
    ]

    # Menyimpan ke DuckDB
    conn = duckdb.connect(str(db_path))

    conn.register("df_produksi", df)

    conn.execute("""
        CREATE OR REPLACE TABLE produksi_beras AS
        SELECT * FROM df_produksi
    """)

    jumlah_data = conn.execute(
        "SELECT COUNT(*) FROM produksi_beras"
    ).fetchone()[0]

    conn.close()

    print(f"  [✓] Data produksi berhasil diimport: {jumlah_data} baris")
    print("  [✓] Tabel: produksi_beras")
    print("  [✓] Satuan produksi: Ton")


if __name__ == "__main__":
    init_databases()
