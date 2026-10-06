import os
import duckdb
import pandas as pd

# Path Database Staging & Catalog
DB_GROSIR = "databases/bebek_grosir.duckdb"
DB_PIHPS = "databases/bebek_pihps.duckdb"
DB_SP2KP = "databases/bebek_sp2kp.duckdb"
CATALOG_PATH = "databases/shared_catalog.ducklake"

# Mapping nama bulan
MONTH_MAP = {
    'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4,
    'Mei': 5, 'Juni': 6, 'Juli': 7, 'Agustus': 8,
    'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
}

def transform_grosir():
    print("🦆 [1/3] Processing Grosir (BPS)...")
    file_path = os.path.join("data", "raw", "grosir", "Rata-rata Harga Beras di Tingkat Perdagangan Besar (Grosir) Indonesia, 2026.xlsx")
    if not os.path.exists(file_path):
        print(f"  [X] File Grosir tidak ditemukan di: {file_path}")
        return

    df_raw = pd.read_excel(file_path)
    months = df_raw.iloc[2, 1:9].values  # Januari - Agustus
    prices = df_raw.iloc[3, 1:9].values

    data = []
    for m, p in zip(months, prices):
        if m in MONTH_MAP and pd.notna(p) and p != '-':
            data.append({
                'tahun': 2026,
                'bulan_nama': m,
                'bulan_num': MONTH_MAP[m],
                'harga': float(p)
            })

    df_clean = pd.DataFrame(data)
    
    conn = duckdb.connect(DB_GROSIR)
    conn.execute("CREATE OR REPLACE TABLE harga_nasional_bulanan AS SELECT * FROM df_clean")
    conn.close()
    print("  [✓] Grosir data loaded successfully into bebek_grosir.duckdb")

def transform_pihps():
    print("🦆 [2/3] Processing PIHPS Provinsi...")
    file_path = os.path.join("data", "raw", "pihps", "Harga_Beras_Indonesia_Januari_Agustus_2026_Gbg.xlsx")
    if not os.path.exists(file_path):
        print(f"  [X] File PIHPS tidak ditemukan di: {file_path}")
        return

    # Header PIHPS pas di baris ke-6 (header index 5)
    df_raw = pd.read_excel(file_path, header=5)
    df_raw.columns = df_raw.columns.astype(str).str.strip()
    
    # Ambil baris yang memiliki 'No.' angka valid
    df_raw = df_raw[pd.to_numeric(df_raw['No.'], errors='coerce').notna()].copy()
    
    month_cols = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus']
    
    # Melt dari Wide ke Long format
    df_long = pd.melt(
        df_raw,
        id_vars=['Provinsi', 'Jenis Beras'],
        value_vars=month_cols,
        var_name='bulan_nama',
        value_name='harga'
    )
    
    df_long['tahun'] = 2026
    df_long['bulan_num'] = df_long['bulan_nama'].map(MONTH_MAP)
    
    # Cleaning harga
    df_long['harga'] = pd.to_numeric(df_long['harga'], errors='coerce').fillna(0)
    df_clean = df_long[df_long['harga'] > 0].copy()
    
    df_clean = df_clean[['tahun', 'bulan_num', 'bulan_nama', 'Provinsi', 'Jenis Beras', 'harga']]
    df_clean.rename(columns={'Provinsi': 'provinsi', 'Jenis Beras': 'jenis_beras'}, inplace=True)

    conn = duckdb.connect(DB_PIHPS)
    conn.execute("CREATE OR REPLACE TABLE harga_provinsi_bulanan AS SELECT * FROM df_clean")
    conn.close()
    print("  [✓] PIHPS data loaded successfully into bebek_pihps.duckdb")

def transform_sp2kp():
    print("🦆 [3/3] Processing SP2KP Pasar...")
    file_path = os.path.join("data", "raw", "sp2kp", "Harga Beras Bedasarkan Pasar.xlsx")
    if not os.path.exists(file_path):
        print(f"  [X] File SP2KP tidak ditemukan di: {file_path}")
        return

    df_raw = pd.read_excel(file_path)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    
    month_cols = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus']
    
    df_long = pd.melt(
        df_raw,
        id_vars=['Provinsi', 'Nama Pasar', 'Jenis Beras'],
        value_vars=month_cols,
        var_name='bulan_nama',
        value_name='harga'
    )
    
    df_long['tahun'] = 2026
    df_long['bulan_num'] = df_long['bulan_nama'].map(MONTH_MAP)
    
    def clean_price(val):
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val * 1000) if 0 < val < 100 else float(val)
        val_str = str(val).replace('.', '').replace(',', '.').strip()
        try:
            return float(val_str)
        except:
            return 0.0

    df_long['harga'] = df_long['harga'].apply(clean_price)
    df_clean = df_long[df_long['harga'] > 0].copy()
    
    df_clean = df_clean[['tahun', 'bulan_num', 'bulan_nama', 'Provinsi', 'Nama Pasar', 'Jenis Beras', 'harga']]
    df_clean.rename(columns={
        'Provinsi': 'provinsi',
        'Nama Pasar': 'nama_pasar',
        'Jenis Beras': 'jenis_beras'
    }, inplace=True)

    conn = duckdb.connect(DB_SP2KP)
    conn.execute("CREATE OR REPLACE TABLE harga_pasar_bulanan AS SELECT * FROM df_clean")
    conn.close()
    print("  [✓] SP2KP data loaded successfully into bebek_sp2kp.duckdb")

def create_analytics_mart():
    print("🦆 Building Analytics Mart & DuckLake Integration...")
    
    conn = duckdb.connect(CATALOG_PATH)
    
    conn.execute(f"ATTACH '{DB_GROSIR}' AS db_grosir;")
    conn.execute(f"ATTACH '{DB_PIHPS}' AS db_pihps;")
    conn.execute(f"ATTACH '{DB_SP2KP}' AS db_sp2kp;")
    
    # Mart 1: Ringkasan Provinsi
    conn.execute("""
    CREATE OR REPLACE TABLE province_summary AS
    SELECT 
        tahun,
        bulan_num,
        bulan_nama,
        provinsi,
        jenis_beras,
        AVG(harga) AS avg_harga,
        MEDIAN(harga) AS median_harga,
        MIN(harga) AS min_harga,
        MAX(harga) AS max_harga,
        COUNT(*) AS total_records
    FROM db_pihps.harga_provinsi_bulanan
    GROUP BY tahun, bulan_num, bulan_nama, provinsi, jenis_beras;
    """)

    # Mart 2: Ringkasan Pasar
    conn.execute("""
    CREATE OR REPLACE TABLE market_summary AS
    SELECT 
        tahun,
        bulan_num,
        bulan_nama,
        provinsi,
        nama_pasar,
        jenis_beras,
        harga
    FROM db_sp2kp.harga_pasar_bulanan;
    """)

    # Mart 3: Price Gap Analysis
    conn.execute("""
    CREATE OR REPLACE TABLE price_gap_summary AS
    SELECT 
        p.tahun,
        p.bulan_num,
        p.bulan_nama,
        p.provinsi,
        p.jenis_beras,
        p.avg_harga AS harga_provinsi,
        g.harga AS harga_grosir_nasional,
        (p.avg_harga - g.harga) AS gap_provinsi_grosir
    FROM province_summary p
    LEFT JOIN db_grosir.harga_nasional_bulanan g 
        ON p.tahun = g.tahun AND p.bulan_num = g.bulan_num;
    """)

    conn.close()
    print("  [✓] Analytics Mart built successfully at databases/shared_catalog.ducklake")

if __name__ == "__main__":
    transform_grosir()
    transform_pihps()
    transform_sp2kp()
    create_analytics_mart()