import os

import base64

from pathlib import Path



import duckdb

import streamlit as st

import pandas as pd

import plotly.express as px





# =========================================================

# 1. KONFIGURASI DASHBOARD

# =========================================================



st.set_page_config(

    page_title="BebekBerazz | Rice Price Analytics",

    page_icon="🌾",

    layout="wide",

)



DATABASE_DIR = "databases"

LAKEHOUSE_DIR = "lakehouse_storage"

CATALOG_PATH = f"{DATABASE_DIR}/shared_catalog.ducklake"

BACKGROUND_PATH = Path("assets/background.jpg")





# =========================================================

# 2. BACKGROUND DAN STYLE

# =========================================================



def set_background(image_path):
    """Pasang background gambar dengan overlay krem soft agar tampilan lebih hangat."""
    image_css = ""
    if Path(image_path).exists():
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        image_css = f"""
            background-image:
                linear-gradient(
                    rgba(248, 243, 234, 0.86),
                    rgba(248, 243, 234, 0.86)
                ),
                url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        """
    else:
        st.warning(
            "Background belum ditemukan. Pastikan gambar tersimpan di "
            "assets/background.jpg pada folder utama project."
        )
        image_css = "background: #F8F3EA;"

    st.markdown(
        f"""
        <style>
        :root {{
            --cream: #F8F3EA;
            --card: #FFFCF7;
            --beige: #E9DDCB;
            --beige-border: #E5D7C5;
            --coffee: #594638;
            --terracotta: #B98764;
            --muted: #8B7968;
        }}

        .stApp {{
            {image_css}
            color: var(--coffee);
        }}

        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2.5rem;
            max-width: 1500px;
        }}

        h1, h2, h3, p, label, [data-testid="stCaptionContainer"] {{
            color: var(--coffee);
        }}

        h1, h2, h3 {{
            font-weight: 700;
        }}

        [data-testid="stSidebar"] {{
            background: rgba(233, 221, 203, 0.97);
            border-right: 1px solid var(--beige-border);
        }}

        [data-testid="stSidebar"] * {{
            color: var(--coffee);
        }}

        [data-testid="stMetric"] {{
            background: rgba(255, 252, 247, 0.96);
            border: 1px solid rgba(185, 135, 100, 0.30);
            border-radius: 16px;
            padding: 20px 22px;
            box-shadow: 0 5px 16px rgba(89, 70, 56, 0.08);
            min-height: 125px;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--muted);
            font-size: 0.9rem;
            font-weight: 600;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--coffee);
            font-weight: 750;
        }}

        [data-testid="stMetricDelta"] {{
            color: var(--terracotta);
        }}

        div[data-testid="stDataFrame"] {{
            background: rgba(255, 252, 247, 0.97);
            border: 1px solid var(--beige-border);
            border-radius: 14px;
            padding: 7px;
            overflow: hidden;
        }}

        div[data-testid="stPlotlyChart"] {{
            background: rgba(255, 252, 247, 0.94);
            border: 1px solid rgba(229, 215, 197, 0.9);
            border-radius: 16px;
            padding: 10px 10px 2px 10px;
            box-shadow: 0 4px 14px rgba(89, 70, 56, 0.05);
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {{
            background-color: #FFFCF7;
            border-color: #D8C5AF;
            border-radius: 10px;
        }}

        div.stButton > button {{
            background: var(--coffee);
            color: #FFFCF7;
            border: 1px solid var(--coffee);
            border-radius: 10px;
        }}

        div.stButton > button:hover {{
            background: var(--terracotta);
            color: white;
            border-color: var(--terracotta);
        }}

        hr {{
            border-color: rgba(185, 135, 100, 0.28);
        }}

        [data-testid="stAlert"] {{
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


set_background(BACKGROUND_PATH)





# =========================================================

# 3. KONEKSI DUCKLAKE

# =========================================================



@st.cache_resource

def get_connection():

    con = duckdb.connect()

    con.execute("INSTALL ducklake;")

    con.execute("LOAD ducklake;")



    con.execute(

        f"""

        ATTACH 'ducklake:{CATALOG_PATH}'

        AS lake

        (DATA_PATH '{LAKEHOUSE_DIR}/');

        """

    )

    return con





# =========================================================

# 4. MEMUAT DATA ANALYTICAL MART

# =========================================================



@st.cache_data(ttl=300)

def load_data():

    con = get_connection()



    province = con.execute(

        """

        SELECT *

        FROM lake.analytics.province_summary

        """

    ).df()



    market = con.execute(

        """

        SELECT *

        FROM lake.analytics.market_summary

        """

    ).df()



    national = con.execute(

        """

        SELECT *

        FROM lake.analytics.national_trend

        ORDER BY tanggal

        """

    ).df()



    gap = con.execute(

        """

        SELECT *

        FROM lake.analytics.price_gap

        """

    ).df()



    volatility = con.execute(

        """

        SELECT *

        FROM lake.analytics.volatility_summary

        """

    ).df()



    for df in [province, market, national, gap]:

        if "tanggal" in df.columns:

            df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")



    if "tanggal" in volatility.columns:

        volatility["tanggal"] = pd.to_datetime(

            volatility["tanggal"], errors="coerce"

        )



    return province, market, national, gap, volatility





# Jika koneksi atau nama tabel salah, tampilkan pesan yang lebih mudah dipahami.

try:

    province_df, market_df, national_df, gap_df, volatility_df = load_data()

except Exception as error:

    st.error(

        "Dashboard belum berhasil membaca data dari DuckLake. "

        "Pastikan pipeline load, ducklake, dan analytic sudah dijalankan."

    )

    st.code(str(error))

    st.stop()





# =========================================================

# 5. FUNGSI BANTUAN

# =========================================================



def rupiah(value):

    if pd.isna(value):

        return "—"

    return "Rp" + f"{value:,.0f}".replace(",", ".")





def month_name(date_value):

    if pd.isna(date_value):

        return "—"

    return pd.to_datetime(date_value).strftime("%b %Y")





def show_empty():

    st.info("Tidak ada data yang sesuai dengan filter yang dipilih.")





def format_date_column(df, column="tanggal"):

    result = df.copy()

    if column in result.columns:

        result[column] = pd.to_datetime(

            result[column], errors="coerce"

        ).dt.strftime("%B %Y")

    return result





def style_chart(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(255,252,247,0.0)",
        plot_bgcolor="rgba(255,252,247,0.0)",
        font=dict(color="#594638", family="Arial, sans-serif"),
        margin=dict(l=20, r=20, t=50, b=20),
        legend_title_text="",
        colorway=["#B98764", "#8B6950", "#D8BFA5", "#A87855", "#6F5848"],
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#DCCBB8",
        tickfont=dict(color="#594638"),
    )
    fig.update_yaxes(
        gridcolor="#E9DDCB",
        zeroline=False,
        linecolor="#DCCBB8",
        tickfont=dict(color="#594638"),
    )
    return fig


# =========================================================

# 6. HEADER

# =========================================================



st.title("🌾 BebekBerazz")

st.subheader("Indonesian Rice Price Data Warehouse & Analytics")



st.markdown(

    """

    Dashboard analitik harga beras yang mengintegrasikan data

    **Grosir Nasional, PIHPS, dan SP2KP** ke dalam lakehouse

    menggunakan DuckDB dan DuckLake.

    """

)



st.divider()





# =========================================================

# 7. SIDEBAR NAVIGASI

# =========================================================



st.sidebar.title("🌾 BebekBerazz")

st.sidebar.caption("Rice Price Analytics")



menu = st.sidebar.radio(

    "Pilih Menu",

    [

        "National Overview",

        "Province Analysis",

        "Market Explorer",

        "Price Comparison",

    ],

)



st.sidebar.divider()

st.sidebar.caption("Data warehouse: DuckDB + DuckLake")

st.sidebar.caption("Periode data: 2026")





# =========================================================

# MENU 1: NATIONAL OVERVIEW

# =========================================================



if menu == "National Overview":

    st.header("National Overview")

    st.caption("Ringkasan perkembangan harga beras grosir nasional.")



    national = national_df.sort_values("tanggal").copy()



    if national.empty:

        show_empty()

    else:

        latest = national.iloc[-1]

        perubahan = latest.get("perubahan_persen", None)



        col1, col2, col3, col4 = st.columns(4)



        col1.metric(

            "Harga Grosir Terbaru",

            rupiah(latest.get("harga_grosir")),

            month_name(latest.get("tanggal")),

        )

        col2.metric(

            "Perubahan Bulanan",

            f"{perubahan:.2f}%" if pd.notna(perubahan) else "—",

        )

        col3.metric(

            "Harga Tertinggi",

            rupiah(national["harga_grosir"].max()),

        )

        col4.metric(

            "Harga Terendah",

            rupiah(national["harga_grosir"].min()),

        )



        st.divider()

        st.subheader("Tren Harga Beras Grosir Nasional")



        fig = px.line(

            national,

            x="tanggal",

            y="harga_grosir",

            markers=True,

            text="harga_grosir",

            labels={

                "tanggal": "Bulan",

                "harga_grosir": "Harga Grosir (Rp)",

            },

        )

        fig.update_traces(

            line=dict(color="#B98764", width=3),

            marker=dict(size=8, color="#8B6950"),

            texttemplate="%{y:,.0f}",

            textposition="top center",

        )

        fig.update_yaxes(tickformat=",.0f")

        st.plotly_chart(style_chart(fig), use_container_width=True)



        st.subheader("Perubahan Harga Bulanan")



        columns = [

            "tanggal",

            "harga_grosir",

            "harga_bulan_sebelumnya",

            "perubahan_harga",

            "perubahan_persen",

        ]

        available_columns = [

            column for column in columns if column in national.columns

        ]

        trend_display = format_date_column(national[available_columns])



        trend_display = trend_display.rename(

            columns={

                "tanggal": "Bulan",

                "harga_grosir": "Harga Grosir",

                "harga_bulan_sebelumnya": "Harga Bulan Sebelumnya",

                "perubahan_harga": "Perubahan Harga",

                "perubahan_persen": "Perubahan (%)",

            }

        )

        st.dataframe(

            trend_display,

            use_container_width=True,

            hide_index=True,

        )





# =========================================================

# MENU 2: PROVINCE ANALYSIS

# =========================================================



elif menu == "Province Analysis":

    st.header("Province Analysis")

    st.caption("Analisis statistik harga beras berdasarkan provinsi.")



    province = province_df.copy()



    if province.empty:

        show_empty()

    else:

        provinces = sorted(province["provinsi"].dropna().unique().tolist())



        if not provinces:

            show_empty()

            st.stop()



        selected_province = st.selectbox("Pilih Provinsi", provinces)

        province = province[province["provinsi"] == selected_province].copy()



        rice_types = sorted(

            province["jenis_beras"].dropna().unique().tolist()

        )



        if not rice_types:

            show_empty()

            st.stop()



        selected_type = st.selectbox("Pilih Jenis Beras", rice_types)

        province = province[

            province["jenis_beras"] == selected_type

        ].sort_values("tanggal")



        if province.empty:

            show_empty()

        else:

            latest = province.iloc[-1]

            col1, col2, col3, col4 = st.columns(4)



            col1.metric(

                "Rata-rata Harga Terbaru",

                rupiah(latest.get("rata_rata_harga")),

            )

            col2.metric(

                "Median Harga",

                rupiah(latest.get("median_harga")),

            )

            col3.metric(

                "Harga Minimum",

                rupiah(latest.get("min_harga")),

            )

            col4.metric(

                "Harga Maksimum",

                rupiah(latest.get("max_harga")),

            )



            st.divider()

            st.subheader(f"Tren Harga — {selected_province}")



            fig = px.line(

                province,

                x="tanggal",

                y="rata_rata_harga",

                markers=True,

                labels={

                    "tanggal": "Bulan",

                    "rata_rata_harga": "Rata-rata Harga (Rp)",

                },

            )

            fig.update_traces(

                line=dict(color="#B98764", width=3),

                marker=dict(size=7, color="#8B6950"),

            )

            fig.update_yaxes(tickformat=",.0f")

            st.plotly_chart(style_chart(fig), use_container_width=True)



            st.subheader("Statistik Harga Bulanan")



            columns = [

                "tanggal",

                "rata_rata_harga",

                "median_harga",

                "min_harga",

                "max_harga",

                "jumlah_harga_valid",

            ]

            available_columns = [

                column for column in columns if column in province.columns

            ]

            display = format_date_column(province[available_columns])

            display = display.rename(

                columns={

                    "tanggal": "Bulan",

                    "rata_rata_harga": "Rata-rata Harga",

                    "median_harga": "Median Harga",

                    "min_harga": "Harga Minimum",

                    "max_harga": "Harga Maksimum",

                    "jumlah_harga_valid": "Jumlah Harga Valid",

                }

            )

            st.dataframe(display, use_container_width=True, hide_index=True)



    st.divider()

    st.subheader("Volatilitas Harga Antarprovinsi")



    vol = volatility_df.copy()

    if vol.empty:

        show_empty()

    else:

        vol_types = sorted(

            vol["jenis_beras"].dropna().unique().tolist()

        )

        if vol_types:

            selected_vol_type = st.selectbox(

                "Jenis Beras untuk Analisis Volatilitas",

                vol_types,

            )

            vol = vol[vol["jenis_beras"] == selected_vol_type].copy()

            vol = vol.sort_values(

                "standar_deviasi_harga", ascending=False

            )



            fig_vol = px.bar(

                vol,

                x="provinsi",

                y="standar_deviasi_harga",

                labels={

                    "provinsi": "Provinsi",

                    "standar_deviasi_harga": "Standar Deviasi Harga (Rp)",

                },

            )

            fig_vol.update_traces(marker_color="#C7A487")

            fig_vol.update_yaxes(tickformat=",.0f")

            st.plotly_chart(

                style_chart(fig_vol), use_container_width=True

            )



            st.caption(

                "Semakin tinggi standar deviasi, semakin besar variasi "

                "harga pada data yang dianalisis."

            )





# =========================================================

# MENU 3: MARKET EXPLORER

# =========================================================



elif menu == "Market Explorer":

    st.header("Market Explorer")

    st.caption(

        "Eksplorasi harga berdasarkan pasar, provinsi, dan jenis beras."

    )



    market = market_df.copy()



    if market.empty:

        show_empty()

    else:

        provinces = sorted(market["provinsi"].dropna().unique().tolist())



        if not provinces:

            show_empty()

            st.stop()



        selected_province = st.selectbox("Pilih Provinsi", provinces)

        market = market[market["provinsi"] == selected_province].copy()



        rice_types = sorted(

            market["jenis_beras"].dropna().unique().tolist()

        )

        if not rice_types:

            show_empty()

            st.stop()



        selected_type = st.selectbox("Pilih Jenis Beras", rice_types)

        market = market[market["jenis_beras"] == selected_type].copy()



        markets = sorted(

            market["nama_pasar"].dropna().unique().tolist()

        )

        selected_market = st.selectbox(

            "Pilih Pasar", ["Semua Pasar"] + markets

        )



        if selected_market != "Semua Pasar":

            market = market[market["nama_pasar"] == selected_market].copy()



        market = market.sort_values("tanggal")



        if market.empty:

            show_empty()

        else:

            col1, col2, col3 = st.columns(3)

            col1.metric(

                "Rata-rata Harga",

                rupiah(market["rata_rata_harga"].mean()),

            )

            col2.metric(

                "Harga Minimum",

                rupiah(market["min_harga"].min()),

            )

            col3.metric(

                "Harga Maksimum",

                rupiah(market["max_harga"].max()),

            )



            st.divider()

            st.subheader("Perbandingan Harga Antar Pasar")



            market_latest = (

                market.sort_values("tanggal")

                .groupby(

                    ["nama_pasar", "jenis_beras"],

                    as_index=False,

                )

                .tail(1)

                .sort_values("rata_rata_harga")

            )



            fig = px.bar(

                market_latest,

                x="nama_pasar",

                y="rata_rata_harga",

                labels={

                    "nama_pasar": "Nama Pasar",

                    "rata_rata_harga": "Harga Rata-rata (Rp)",

                },

            )

            fig.update_traces(marker_color="#C7A487")

            fig.update_yaxes(tickformat=",.0f")

            st.plotly_chart(style_chart(fig), use_container_width=True)



            st.subheader("Riwayat Harga Pasar")



            fig_history = px.line(

                market,

                x="tanggal",

                y="rata_rata_harga",

                color="nama_pasar",

                markers=True,

                labels={

                    "tanggal": "Bulan",

                    "rata_rata_harga": "Harga Rata-rata (Rp)",

                    "nama_pasar": "Pasar",

                },

            )

            fig_history.update_yaxes(tickformat=",.0f")

            st.plotly_chart(

                style_chart(fig_history), use_container_width=True

            )



            st.subheader("Detail Data Pasar")

            display = format_date_column(

                market.sort_values(["tanggal", "nama_pasar"])

            )

            st.dataframe(display, use_container_width=True, hide_index=True)





# =========================================================

# MENU 4: PRICE COMPARISON

# =========================================================



elif menu == "Price Comparison":

    st.header("Price Comparison")

    st.caption(

        "Perbandingan deskriptif harga PIHPS tingkat provinsi "

        "dengan harga grosir nasional."

    )



    gap = gap_df.copy()



    if gap.empty:

        show_empty()

    else:

        provinces = sorted(gap["provinsi"].dropna().unique().tolist())

        rice_types = sorted(

            gap["jenis_beras"].dropna().unique().tolist()

        )



        selected_province = st.selectbox(

            "Pilih Provinsi", ["Semua Provinsi"] + provinces

        )

        selected_type = st.selectbox(

            "Pilih Jenis Beras", ["Semua Jenis"] + rice_types

        )



        if selected_province != "Semua Provinsi":

            gap = gap[gap["provinsi"] == selected_province].copy()



        if selected_type != "Semua Jenis":

            gap = gap[gap["jenis_beras"] == selected_type].copy()



        if gap.empty:

            show_empty()

        else:

            col1, col2, col3 = st.columns(3)

            col1.metric(

                "Rata-rata Harga Provinsi",

                rupiah(gap["rata_rata_harga_provinsi"].mean()),

            )

            col2.metric(

                "Rata-rata Harga Grosir Nasional",

                rupiah(gap["harga_grosir_nasional"].mean()),

            )

            col3.metric(

                "Rata-rata Gap Harga",

                rupiah(gap["gap_provinsi_grosir"].mean()),

            )



            st.divider()

            st.subheader("Tren Perbandingan Harga")



            if (

                selected_province != "Semua Provinsi"

                and selected_type != "Semua Jenis"

            ):

                chart_data = gap.sort_values("tanggal")

                fig = px.line(

                    chart_data,

                    x="tanggal",

                    y=[

                        "rata_rata_harga_provinsi",

                        "harga_grosir_nasional",

                    ],

                    markers=True,

                    labels={

                        "tanggal": "Bulan",

                        "value": "Harga (Rp)",

                        "variable": "Sumber Harga",

                        "rata_rata_harga_provinsi": "Harga Provinsi (PIHPS)",

                        "harga_grosir_nasional": "Harga Grosir Nasional",

                    },

                )

                fig.update_yaxes(tickformat=",.0f")

                st.plotly_chart(

                    style_chart(fig), use_container_width=True

                )

            else:

                latest_date = gap["tanggal"].max()

                latest_gap = gap[gap["tanggal"] == latest_date]



                province_gap = (

                    latest_gap.groupby("provinsi", as_index=False)[

                        "gap_provinsi_grosir"

                    ]

                    .mean()

                    .sort_values("gap_provinsi_grosir")

                )



                fig = px.bar(

                    province_gap,

                    x="provinsi",

                    y="gap_provinsi_grosir",

                    labels={

                        "provinsi": "Provinsi",

                        "gap_provinsi_grosir": "Gap Harga (Rp)",

                    },

                )

                fig.update_traces(marker_color="#C7A487")

                fig.update_yaxes(tickformat=",.0f")

                st.plotly_chart(

                    style_chart(fig), use_container_width=True

                )



            st.subheader("Detail Selisih Harga")



            columns = [

                "tanggal",

                "provinsi",

                "jenis_beras",

                "rata_rata_harga_provinsi",

                "harga_grosir_nasional",

                "gap_provinsi_grosir",

                "gap_persen",

            ]

            available_columns = [

                column for column in columns if column in gap.columns

            ]

            display = format_date_column(

                gap[available_columns].sort_values(

                    ["tanggal", "provinsi", "jenis_beras"]

                )

            )

            display = display.rename(

                columns={

                    "tanggal": "Bulan",

                    "provinsi": "Provinsi",

                    "jenis_beras": "Jenis Beras",

                    "rata_rata_harga_provinsi": "Harga Provinsi (PIHPS)",

                    "harga_grosir_nasional": "Harga Grosir Nasional",

                    "gap_provinsi_grosir": "Gap Harga",

                    "gap_persen": "Gap (%)",

                }

            )

            st.dataframe(display, use_container_width=True, hide_index=True)



            st.warning(

                "Gap ini adalah selisih deskriptif. Harga PIHPS "

                "berdasarkan jenis beras dibandingkan dengan harga grosir "

                "nasional yang tidak dirinci menurut jenis. Karena itu, "

                "gap bukan margin keuntungan dan tidak selalu merupakan "

                "perbandingan kategori yang setara."

            )





# =========================================================

# FOOTER

# =========================================================



st.divider()

st.caption(

    "BebekBerazz | Indonesian Rice Price Data Warehouse & Analytics"

)
