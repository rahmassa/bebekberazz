"""BebekBerazz: update database dari snapshot Excel bulanan.
Simpan di root project (atau src/). Jalankan dengan Streamlit berhenti.
python update.py --check  # validasi Excel tanpa menyentuh database
python update.py          # update + backup + bangun ulang analytics mart
python update.py --parquet # tambahan ekspor snapshot Parquet
"""
from pathlib import Path
from datetime import date, datetime
import argparse
import math
import os
import re
import shutil
import tempfile
import pandas as pd

ROOT = Path(__file__).resolve().parent
if ROOT.name == 'src':
    ROOT = ROOT.parent
DB = ROOT / 'databases'
RAW = ROOT / 'data' / 'raw'
MONTHS = 'Januari Februari Maret April Mei Juni Juli Agustus September Oktober November Desember'.split()
MONTH_MAP = {m.lower(): i for i, m in enumerate(MONTHS, 1)}
G = 'bebek_grosir.duckdb'
P = 'bebek_pihps.duckdb'
S = 'bebek_sp2kp.duckdb'
D = 'bebek_produksi.duckdb'
C = 'shared_catalog.ducklake'
FILES = {
    G: ('grosir', 'Rata-rata Harga Beras di Tingkat Perdagangan Besar (Grosir) Indonesia, 2026.xlsx', 'harga_nasional_bulanan', ['Komoditas']),
    P: ('pihps', 'Harga_Beras_Indonesia_Januari_Agustus_2026_Gabungan.xlsx', 'harga_provinsi_bulanan', ['Provinsi', 'Jenis Beras']),
    S: ('sp2kp', 'Harga Beras Bedasarkan Pasar.xlsx', 'harga_pasar_bulanan', ['Provinsi', 'Nama Pasar', 'Jenis Beras']),
}
RENAME = {'Provinsi':'provinsi', 'Nama Pasar':'nama_pasar', 'Jenis Beras':'jenis_beras'}

def parse_period(value):
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return value.year, value.month
    m = re.fullmatch(r'([A-Za-z]+)\s+(\d{4})', str(value).strip())
    if m and m[1].lower() in MONTH_MAP:
        return int(m[2]), MONTH_MAP[m[1].lower()]
    # Date headers may also be exported as ISO strings.
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}( 00:00:00)?', str(value)):
        t = pd.Timestamp(value)
        return t.year, t.month
    raise ValueError(f'Header bulan tidak dikenali: {value!r}. Gunakan Bulan Tahun.')


def read_prices(path, keys, market=False):
    df = pd.read_excel(path, header=0, engine='openpyxl')
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    if not set(keys).issubset(df.columns):
        raise ValueError(f'{path.name}: kolom wajib {keys} tidak lengkap')
    df = df.dropna(how='all').copy()
    for k in keys:
        if df[k].isna().any():
            raise ValueError(f'{path.name}: kolom {k} kosong')
        df[k] = df[k].astype(str).str.strip()
        if df[k].eq('').any():
            raise ValueError(f'{path.name}: kolom {k} kosong')
    count = len(df)
    df = df.drop_duplicates()
    print(f'  Duplikat identik dibuang: {count-len(df)} baris Excel')
    if df.duplicated(keys).any():
        raise ValueError(f'{path.name}: kunci duplikat dengan harga berbeda; periksa sumber sebelum update')
    if keys == ['Komoditas']:
        df = df[df['Komoditas'].str.casefold() == 'harga beras']
        if len(df) != 1:
            raise ValueError('Excel grosir harus punya satu baris Harga Beras')
    cols = [c for c in df.columns if c not in keys]
    periods = [parse_period(c) for c in cols]
    if not periods or len(set(periods)) != len(periods):
        raise ValueError(f'{path.name}: periode kosong atau duplikat')
    if any(not (1900 <= y <= 2100 and 1 <= m <= 12) for y,m in periods):
        raise ValueError('Periode tidak valid')
    chunks, rejected = [], []
    for col, (year, month) in zip(cols, periods):
        d = df[keys].copy()
        original = df[col]
        price = pd.to_numeric(original, errors='coerce')
        missing = original.isna() | original.astype(str).str.strip().isin(['', '-', '–', '—'])
        if (price.isna() & ~missing).any() or (price.notna() & ~price.map(lambda x: math.isfinite(x))).any():
            raise ValueError(f'{path.name}: harga nonnumerik/tidak valid pada {col}')
        d['tahun'], d['bulan_num'], d['bulan_nama'] = year, month, MONTHS[month-1]
        d['harga'] = price.astype(float)
        bad = d['harga'].notna() & (d['harga'] < 0)
        if market:
            # Nilai 1/10 pada file asli meragukan untuk Rp/kg. Jangan tebak skala.
            bad |= d['harga'].gt(0) & d['harga'].lt(1000)
        if bad.any():
            r = d.loc[bad].copy(); r['alasan'] = 'Harga di luar batas minimum valid'; rejected.append(r)
        d = d.loc[~bad & d['harga'].gt(0)]
        chunks.append(d)
    out = pd.concat(chunks, ignore_index=True).rename(columns=RENAME)
    order = ['tahun','bulan_num','bulan_nama'] + [RENAME[k] for k in keys if k in RENAME] + ['harga']
    out = out[order]
    if set(zip(out.tahun, out.bulan_num)) != set(periods):
        raise ValueError(f'{path.name}: ada bulan tanpa satu pun harga valid')
    rejects = pd.concat(rejected, ignore_index=True) if rejected else pd.DataFrame()
    print(f'  Harga tidak wajar dikeluarkan: {len(rejects)}; harga nol/kosong tidak diimputasi.')
    if market:
        print(f'  Harga > Rp50.000/kg (dipertahankan, perlu cek): {(out.harga>50000).sum()}')
    return out, sorted(periods), rejects


def report(name, data):
    print(f'\n{name}: {len(data):,} baris')
    for y, d in data.groupby('tahun'):
        ms = sorted(d.bulan_num.unique())
        print(f'  {y}: {len(ms)} bulan ({ms[0]}-{ms[-1]}), {len(d):,} baris')


def read_production(path):
    df = pd.read_csv(path, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df = df.rename(columns={'Tahun':'tahun','Nama_Bulan':'bulan_nama','Produksi_Beras':'produksi_ton'})
    df['tahun'] = pd.to_numeric(df['tahun'], errors='raise')
    if df['tahun'].isna().any() or (df['tahun'] % 1 != 0).any():
        raise ValueError('Tahun produksi tidak valid')
    df['tahun'] = df['tahun'].astype(int)
    df['bulan_num'] = df['bulan_nama'].astype(str).str.strip().str.lower().map(MONTH_MAP)
    if df['bulan_num'].isna().any():
        raise ValueError('Bulan produksi tidak valid')
    df['bulan_num'] = df['bulan_num'].astype(int)
    df['bulan_nama'] = df['bulan_num'].map(dict(enumerate(MONTHS, 1)))
    df['produksi_ton'] = pd.to_numeric(df['produksi_ton'], errors='raise').astype(float)
    if not df['produksi_ton'].map(lambda x: math.isfinite(x) and x >= 0).all():
        raise ValueError('Produksi tidak valid')
    df['periode'] = pd.to_datetime(dict(year=df['tahun'], month=df['bulan_num'], day=1))
    df = df[['periode','tahun','bulan_num','bulan_nama','produksi_ton']].drop_duplicates()
    if df.duplicated(['tahun','bulan_num']).any() or df.empty:
        raise ValueError('Data produksi kosong atau duplikat periode')
    return df, sorted(set(zip(df.tahun, df.bulan_num)))


def qident(s):
    return '"' + s.replace('"','""') + '"'


def qpath(p):
    return "'" + Path(p).resolve().as_posix().replace("'", "''") + "'"


def replace_periods(duckdb, path, table, data, periods):
    # Replace only months present in authoritative full monthly snapshots.
    # Keep historical months absent from the input file.
    with duckdb.connect(str(path)) as con:
        con.register('incoming', data)
        con.register('incoming_months', pd.DataFrame(periods, columns=['tahun','bulan_num']))
        name = qident(table)
        exists = con.execute('SELECT count(*) FROM information_schema.tables WHERE table_schema=\'main\' AND table_name=?', [table]).fetchone()[0]
        con.execute('BEGIN TRANSACTION')
        try:
            if exists:
                columns = [r[0] for r in con.execute(f'DESCRIBE {name}').fetchall()]
                if set(columns) != set(data.columns):
                    raise ValueError(f'{table}: skema berbeda ({columns}); backup tetap aman')
                con.execute(f'DELETE FROM {name} AS t WHERE EXISTS (SELECT 1 FROM incoming_months m WHERE t.tahun=m.tahun AND t.bulan_num=m.bulan_num)')
                con.execute(f'INSERT INTO {name} BY NAME SELECT * FROM incoming')
            else:
                con.execute(f'CREATE TABLE {name} AS SELECT * FROM incoming')
            actual = con.execute(f'SELECT count(*) FROM {name} t WHERE EXISTS (SELECT 1 FROM incoming_months m WHERE t.tahun=m.tahun AND t.bulan_num=m.bulan_num)').fetchone()[0]
            if actual != len(data):
                raise RuntimeError(f'{table}: jumlah baris tidak cocok')
            con.execute('COMMIT')
        except Exception:
            con.execute('ROLLBACK'); raise
        print(f'\n{table} setelah update:')
        print(con.execute(f'SELECT tahun, count(DISTINCT bulan_num) AS jumlah_bulan, min(bulan_num) AS awal, max(bulan_num) AS akhir, count(*) AS baris FROM {name} GROUP BY tahun ORDER BY tahun').fetchdf().to_string(index=False))
        con.execute('CHECKPOINT')


def build_mart(duckdb, stage, parquet=False):
    with duckdb.connect(str(stage/C)) as con:
        for f, alias in [(G,'db_grosir'),(P,'db_pihps'),(S,'db_sp2kp'),(D,'db_produksi')]:
            if (stage/f).exists():
                con.execute(f'ATTACH {qpath(stage/f)} AS {alias} (READ_ONLY)')
        con.execute('BEGIN TRANSACTION')
        try:
            con.execute('''CREATE OR REPLACE TABLE province_summary AS
                SELECT tahun, bulan_num, bulan_nama, provinsi, jenis_beras,
                       AVG(harga) AS avg_harga, MEDIAN(harga) AS median_harga,
                       MIN(harga) AS min_harga, MAX(harga) AS max_harga, COUNT(*) AS total_records
                FROM db_pihps.harga_provinsi_bulanan GROUP BY ALL''')
            con.execute('''CREATE OR REPLACE TABLE market_summary AS
                SELECT tahun, bulan_num, bulan_nama, provinsi, nama_pasar, jenis_beras, harga
                FROM db_sp2kp.harga_pasar_bulanan''')
            con.execute('''CREATE OR REPLACE TABLE price_gap_summary AS
                SELECT p.tahun,p.bulan_num,p.bulan_nama,p.provinsi,p.jenis_beras,
                       p.avg_harga AS harga_provinsi,g.harga AS harga_grosir_nasional,
                       p.avg_harga-g.harga AS gap_provinsi_grosir
                FROM province_summary p LEFT JOIN db_grosir.harga_nasional_bulanan g
                ON p.tahun=g.tahun AND p.bulan_num=g.bulan_num''')
            if (stage/D).exists():
                con.execute('CREATE OR REPLACE TABLE produksi_summary AS SELECT * FROM db_produksi.produksi_beras')
            for table in ['province_summary','market_summary','price_gap_summary']:
                print(f'\n{table}:')
                print(con.execute(f'SELECT tahun,count(DISTINCT bulan_num) AS jumlah_bulan,count(*) AS baris FROM {table} GROUP BY tahun ORDER BY tahun').fetchdf().to_string(index=False))
            con.execute('COMMIT')
        except Exception:
            con.execute('ROLLBACK'); raise
        if parquet:
            folder = stage/'parquet'; folder.mkdir()
            tables = {'grosir':'db_grosir.harga_nasional_bulanan','pihps':'db_pihps.harga_provinsi_bulanan','sp2kp':'db_sp2kp.harga_pasar_bulanan','province_summary':'province_summary','market_summary':'market_summary','price_gap_summary':'price_gap_summary'}
            if (stage/D).exists(): tables['produksi']='db_produksi.produksi_beras'
            for name, table in tables.items():
                con.execute(f'COPY (SELECT * FROM {table}) TO {qpath(folder/(name+".parquet"))} (FORMAT PARQUET, COMPRESSION ZSTD)')
        con.execute('CHECKPOINT')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validasi Excel tanpa mengubah database')
    parser.add_argument('--parquet', action='store_true', help='Ekspor snapshot Parquet (bukan migrasi DuckLake)')
    for flag in ['grosir','pihps','sp2kp','produksi']:
        parser.add_argument('--'+flag, type=Path, help='Path file input pengganti')
    args = parser.parse_args()
    updates, audit = {}, []
    for file, (folder, filename, table, keys) in FILES.items():
        path = getattr(args, folder) or RAW/folder/filename
        if not path.is_file():
            raise FileNotFoundError(f'File tidak ditemukan: {path}. Gunakan --{folder} "path Excel".')
        print(f'\nMembaca {path.name}')
        data, periods, rejected = read_prices(path, keys, market=(file==S))
        updates[file] = (table, data, periods)
        report(table, data)
        if not rejected.empty:
            rejected['sumber'] = path.name; audit.append(rejected)
    prod = args.produksi or RAW/'bdsp'/'produksibraz.csv'
    if prod.exists():
        data, periods = read_production(prod)
        updates[D] = ('produksi_beras', data, periods)
        report('produksi_beras', data)
    elif args.produksi:
        raise FileNotFoundError(prod)
    else:
        print('\nCSV produksi tidak tersedia: database produksi lama dipertahankan.')
    print('Database bencana tidak diubah karena tidak ada sumber bencana baru.')
    if args.check:
        print('\nVALIDASI SUMBER SELESAI. Tidak ada database yang diubah.'); return
    import duckdb
    DB.mkdir(exist_ok=True)
    names = list(updates) + [C]
    copy_names = list(dict.fromkeys(names + [D]))
    for f in copy_names:
        if (DB/(f+'.wal')).exists():
            raise RuntimeError(f'Ada WAL {f}; tutup semua koneksi dan Streamlit dulu.')
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup = DB/'backup'/stamp; backup.mkdir(parents=True)
    for f in copy_names:
        if (DB/f).exists(): shutil.copy2(DB/f, backup/f)
    if audit:
        pd.concat(audit, ignore_index=True).to_csv(backup/'harga_perlu_diperiksa.csv', index=False, encoding='utf-8-sig')
    print(f'\nBackup dan audit: {backup}')
    with tempfile.TemporaryDirectory(prefix='.update_', dir=DB) as tmp:
        stage = Path(tmp)
        for f in copy_names:
            if (backup/f).exists(): shutil.copy2(backup/f, stage/f)
        for f,(table,data,periods) in updates.items():
            replace_periods(duckdb, stage/f, table, data, periods)
        build_mart(duckdb, stage, args.parquet)
        # Commit files only after all database transformations succeed.
        replaced = []
        try:
            for f in names:
                os.replace(stage/f, DB/f); replaced.append(f)
        except Exception:
            for f in reversed(replaced):
                if (backup/f).exists(): shutil.copy2(backup/f, DB/f)
                else: (DB/f).unlink(missing_ok=True)
            raise
        if args.parquet:
            target = ROOT/'data'/'parquet'/'snapshots'/stamp
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(stage/'parquet'), str(target))
            print(f'Parquet: {target}')
    print('\nUPDATE SELESAI. Jalankan streamlit cache clear, lalu dashboard.')

if __name__ == '__main__':
    main()
