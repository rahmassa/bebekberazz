import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="BebekBerazz Analytics Dashboard",
    page_icon="🦆",
    layout="wide"
)

CATALOG_PATH = "databases/shared_catalog.ducklake"

@st.cache_data
def load_data(query):
    conn = duckdb.connect(CATALOG_PATH, read_only=True)
    df = conn.execute(query).df()
    conn.close()
    return df

# Header Utama
st.title("🦆 BebekBerazz — Indonesian Rice Price Data Warehouse & Analytics")
st.markdown("Sistem Pemantauan dan Analisis Harga Beras Indonesia (BPS Grosir, PIHPS Provinsi, SP2KP Pasar)")

# Sidebar Navigasi
st.sidebar.title("📌 Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih Halaman Analisis:",
    ["National Overview", "Province Analysis", "Market Explorer", "Price Gap Analysis"]
)

# -----------------------------------------------------------------------------
# 1. NATIONAL OVERVIEW
# -----------------------------------------------------------------------------
if menu == "National Overview":
    st.header("📊 National Overview")
    
    # Load Data Grosir & Provinsi
    df_grosir = load_data("SELECT * FROM db_grosir.harga_nasional_bulanan ORDER BY bulan_num")
    df_prov = load_data("SELECT * FROM province_summary")
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    avg_grosir = df_grosir['harga'].mean() if not df_grosir.empty else 0
    avg_prov = df_prov['avg_harga'].mean() if not df_prov.empty else 0
    med_prov = df_prov['median_harga'].median() if not df_prov.empty else 0
    
    col1.metric("Rata-rata Harga Grosir Nasional", f"Rp {avg_grosir:,.0f}/kg")
    col2.metric("Rata-rata Harga Provinsi", f"Rp {avg_prov:,.0f}/kg")
    col3.metric("Median Harga Provinsi", f"Rp {med_prov:,.0f}/kg")
    
    st.subheader("📈 Tren Harga Beras Grosir Nasional (BPS 2026)")
    fig_grosir = px.line(
        df_grosir, x='bulan_nama', y='harga', markers=True,
        title="Perkembangan Harga Grosir Nasional per Bulan",
        labels={'bulan_nama': 'Bulan', 'harga': 'Harga (Rp/kg)'}
    )
    st.plotly_chart(fig_grosir, use_container_width=True)

# -----------------------------------------------------------------------------
# 2. PROVINCE ANALYSIS
# -----------------------------------------------------------------------------
elif menu == "Province Analysis":
    st.header("🗺️ Province Price Analysis")
    
    df_prov = load_data("SELECT * FROM province_summary")
    
    list_prov = sorted(df_prov['provinsi'].unique())
    selected_prov = st.selectbox("Pilih Provinsi:", list_prov)
    
    df_filtered = df_prov[df_prov['provinsi'] == selected_prov]
    
    st.subheader(f"Tren Harga Beras di {selected_prov}")
    fig_prov = px.line(
        df_filtered, x='bulan_nama', y='avg_harga', color='jenis_beras', markers=True,
        title=f"Perkembangan Harga per Jenis Beras di {selected_prov}",
        labels={'bulan_nama': 'Bulan', 'avg_harga': 'Rata-rata Harga (Rp/kg)'}
    )
    st.plotly_chart(fig_prov, use_container_width=True)
    
    st.subheader("📋 Ringkasan Data Provinsi")
    st.dataframe(df_filtered, use_container_width=True)

# -----------------------------------------------------------------------------
# 3. MARKET EXPLORER
# -----------------------------------------------------------------------------
elif menu == "Market Explorer":
    st.header("🏪 Market Explorer (SP2KP)")
    
    df_market = load_data("SELECT * FROM market_summary")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_prov = st.selectbox("Pilih Provinsi:", sorted(df_market['provinsi'].unique()))
    
    df_m_prov = df_market[df_market['provinsi'] == selected_prov]
    with col2:
        selected_pasar = st.selectbox("Pilih Pasar:", sorted(df_m_prov['nama_pasar'].unique()))
    
    df_m_filtered = df_m_prov[df_m_prov['nama_pasar'] == selected_pasar]
    
    st.subheader(f"Perkembangan Harga di {selected_pasar}")
    fig_market = px.bar(
        df_m_filtered, x='bulan_nama', y='harga', color='jenis_beras', barmode='group',
        title=f"Harga Beras di {selected_pasar} ({selected_prov})",
        labels={'bulan_nama': 'Bulan', 'harga': 'Harga (Rp/kg)'}
    )
    st.plotly_chart(fig_market, use_container_width=True)

# -----------------------------------------------------------------------------
# 4. PRICE GAP ANALYSIS
# -----------------------------------------------------------------------------
elif menu == "Price Gap Analysis":
    st.header("🔍 Price Gap Analysis (Provinsi vs Grosir)")
    
    df_gap = load_data("SELECT * FROM price_gap_summary")
    
    st.subheader("Selisih Harga Beras Provinsi dibandingkan Grosir Nasional")
    selected_jenis = st.selectbox("Pilih Kualitas Beras:", sorted(df_gap['jenis_beras'].unique()))
    
    df_gap_filtered = df_gap[df_gap['jenis_beras'] == selected_jenis]
    
    fig_gap = px.box(
        df_gap_filtered, x='bulan_nama', y='gap_provinsi_grosir', points="all",
        title=f"Sebaran Gap Harga Provinsi vs Grosir Nasional ({selected_jenis})",
        labels={'bulan_nama': 'Bulan', 'gap_provinsi_grosir': 'Selisih Harga (Rp/kg)'}
    )
    st.plotly_chart(fig_gap, use_container_width=True)
    
    st.dataframe(df_gap_filtered, use_container_width=True)