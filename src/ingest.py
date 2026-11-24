import os
import duckdb

def init_databases():
    os.makedirs("databases", exist_ok=True)
    db_paths = {
        "grosir": "databases/bebek_grosir.duckdb",
        "pihps": "databases/bebek_pihps.duckdb",
        "sp2kp": "databases/bebek_sp2kp.duckdb",
        "bdsp": "databases/bebek_bdsp.duckdb",
    }
    print("🦆 Memulai Inisialisasi Database DuckDB BebekBerazz...")
    for name, path in db_paths.items():
        conn = duckdb.connect(path)
        conn.execute("CREATE TABLE IF NOT EXISTS _metadata (initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.close()
        print(f"  [✓] Database {name} berhasil dibuat di: {path}")

if __name__ == "__main__":
    init_databases()
