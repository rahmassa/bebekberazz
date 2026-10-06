import duckdb

def check_all_databases():
    print("🔍 MEMERIKSA ISI DATABASE & DUCKLAKE BEBEKBERAZZ\n" + "="*50)
    
    # Cek Catalog Utama DuckLake
    conn = duckdb.connect("databases/shared_catalog.ducklake")
    
    tables = ['province_summary', 'market_summary', 'price_gap_summary']
    
    for tbl in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"📊 Tabel Catalog [{tbl}]: {count:,} baris data")
    
    print("\n" + "="*50)
    print("👀 SAMPEL DATA HARGA PASAR SP2KP (5 BARIS PERTAMA):")
    sample_df = conn.execute("SELECT provinsi, nama_pasar, jenis_beras, bulan_nama, harga FROM market_summary LIMIT 5").df()
    print(sample_df)
    
    print("\n" + "="*50)
    print("👀 SAMPEL ANALISIS PRICE GAP PROVINSI VS GROSIR:")
    gap_df = conn.execute("SELECT provinsi, jenis_beras, bulan_nama, harga_provinsi, harga_grosir_nasional, gap_provinsi_grosir FROM price_gap_summary LIMIT 5").df()
    print(gap_df)

    conn.close()

if __name__ == "__main__":
    check_all_databases()