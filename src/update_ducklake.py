
import duckdb
import os
from pathlib import Path

# Mengatur lokasi folder utama repository
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

# Memastikan file database tersedia
catalog = Path("databases/shared_catalog.ducklake")
bencana = Path("databases/bencana.duckdb")

for file in [catalog, bencana]:
    if not file.is_file():
        raise FileNotFoundError(f"File tidak ditemukan: {file}")

# Membuka koneksi DuckDB
con = duckdb.connect()

con.execute("INSTALL ducklake")
con.execute("LOAD ducklake")

# Membuka DuckLake yang sudah ada
con.execute("""
    ATTACH 'ducklake:databases/shared_catalog.ducklake'
    AS lake
""")

# Membaca database bencana
con.execute("""
    ATTACH 'databases/bencana.duckdb'
    AS bencana_db (READ_ONLY)
""")

# Daftar tabel bencana
tables = [
    "dim_bulan",
    "dim_provinsi",
    "dim_jenis_bencana",
    "fact_bencana"
]

# Update DuckLake
con.execute("BEGIN TRANSACTION")

try:
    con.execute("""
        CREATE SCHEMA IF NOT EXISTS lake.bencana
    """)

    for table in tables:
        con.execute(f"""
            DROP TABLE IF EXISTS lake.bencana.{table}
        """)

        con.execute(f"""
            CREATE TABLE lake.bencana.{table} AS
            SELECT * FROM bencana_db.main.{table}
        """)

        jumlah = con.execute(f"""
            SELECT COUNT(*) FROM lake.bencana.{table}
        """).fetchone()[0]

        print(f"{table}: {jumlah} baris berhasil disalin")

    con.execute("COMMIT")
    print("\nDuckLake berhasil diperbarui!")

except Exception:
    con.execute("ROLLBACK")
    raise

finally:
    con.close()
