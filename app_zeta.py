import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# =====================================================================
# 1. KONFIGURASI HALAMAN, THEME PREMIUM & INITIAL STATE
# =====================================================================
st.set_page_config(page_title="ZETA Terminal Pro Max v3.5", layout="wide")

# Custom CSS untuk tampilan Terminal Finansial yang Gelap & Elegan (Cyber Dark Theme)
st.markdown("""
<style>
    /* Styling Main App */
    .stApp { background-color: #05070a; color: #e2e8f0; }
    
    /* Panel Ringkasan Intelijen Sistem (Metrik Lingkaran) */
    .metric-box {
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }
    .box-green { background-color: #0b1c1a; border: 1px solid #00ffcc; color: #00ffcc; }
    .box-yellow { background-color: #1a190e; border: 1px solid #ffcc00; color: #ffcc00; }
    .box-red { background-color: #220f12; border: 1px solid #ff3344; color: #ff3344; }
    
    .circle-indicator {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-block;
    }
    .circle-green { background-color: #00ffcc; box-shadow: 0 0 10px #00ffcc; }
    .circle-yellow { background-color: #ffcc00; box-shadow: 0 0 10px #ffcc00; }
    .circle-red { background-color: #ff3344; box-shadow: 0 0 10px #ff3344; }
    
    .metric-val { font-size: 28px; font-family: 'Courier New', monospace; }
    .metric-lbl { font-size: 14px; color: #8a99ad; }
</style>
""", unsafe_allow_html=True)

# Inisialisasi State Utama
if "last_sync" not in st.session_state:
    st.session_state.last_sync = "10 Jul 2026 - 10:28:41 WIB"
if "bandar_state" not in st.session_state:
    st.session_state.bandar_state = {}
if "eval_page" not in st.session_state:
    st.session_state.eval_page = 0
if "risk_profile" not in st.session_state:
    st.session_state.risk_profile = "Moderat (Standar)"

# Data Mentah Saham Utama (Sesuai Komponen Foto Radar Comprehensive Anda)
if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks = [
        {"TICKER": "BBCA", "HARGA": 6175, "PER": 13.10, "PBV": 2.93, "DIV_YIELD": "5.74%", "RSI": 48.81, "SKOR": 70, "TEKNIKAL": "BUY / ACCUMULATE", "AKSI": "🟢 CICIL BELI"},
        {"TICKER": "BBRI", "HARGA": 2790, "PER": 7.17, "PBV": 1.24, "DIV_YIELD": "15.04%", "RSI": 44.12, "SKOR": 70, "TEKNIKAL": "BUY / ACCUMULATE", "AKSI": "🟢 CICIL BELI"},
        {"TICKER": "BMRI", "HARGA": 4050, "PER": 6.51, "PBV": 1.25, "DIV_YIELD": "11.81%", "RSI": 42.55, "SKOR": 85, "TEKNIKAL": "BUY / ACCUMULATE", "AKSI": "🟢 CICIL BELI"},
        {"TICKER": "BBNI", "HARGA": 3420, "PER": 6.27, "PBV": 0.79, "DIV_YIELD": "10.22%", "RSI": 46.32, "SKOR": 70, "TEKNIKAL": "BUY / ACCUMULATE", "AKSI": "🟢 CICIL BELI"},
        {"TICKER": "TLKM", "HARGA": 2480, "PER": 15.08, "PBV": 1.82, "DIV_YIELD": "8.89%", "RSI": 46.94, "SKOR": 55, "TEKNIKAL": "NEUTRAL", "AKSI": "🟡 HOLD / WATCHING"},
        {"TICKER": "ASII", "HARGA": 4810, "PER": 6.13, "PBV": 0.83, "DIV_YIELD": "7.99%", "RSI": 52.86, "SKOR": 55, "TEKNIKAL": "NEUTRAL", "AKSI": "🟡 HOLD / WATCHING"},
        {"TICKER": "UNTR", "HARGA": 24500, "PER": 7.24, "PBV": 0.91, "DIV_YIELD": "9.11%", "RSI": 67.90, "SKOR": 85, "TEKNIKAL": "BUY / ACCUMULATE", "AKSI": "🟢 CICIL BELI"},
        {"TICKER": "ICBP", "HARGA": 6650, "PER": 8.48, "PBV": 1.42, "DIV_YIELD": "3.97%", "RSI": 64.16, "SKOR": 85, "TEKNIKAL": "BUY / ACCUMULATE", "AKSI": "🟢 CICIL BELI"},
        {"TICKER": "INDF", "HARGA": 6775, "PER": 5.45, "PBV": 0.77, "DIV_YIELD": "4.38%", "RSI": 66.44, "SKOR": 85, "TEKNIKAL": "BUY / ACCUMULATE", "AKSI": "🟢 CICIL BELI"},
        {"TICKER": "AMRT", "HARGA": 1400, "PER": 16.52, "PBV": 3.11, "DIV_YIELD": "2.92%", "RSI": 48.53, "SKOR": 30, "TEKNIKAL": "TAKE PROFIT / SELL", "AKSI": "🔴 STRONG SELL"},
    ]

# =====================================================================
# 2. SIDEBAR (CYBER PANEL)
# =====================================================================
with st.sidebar:
    st.title("💎 CYBER PANEL")
    st.caption("Premium Quantum Engine v3.5")
    
    st.markdown("### 📋 DAFTAR EMITEN PANTAUAN:")
    for stock in st.session_state.raw_stocks[:5]:
        st.markdown(f"• **{stock['TICKER']}** <span style='color:#00ffcc;'>Active</span>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Dropdown Profil Risiko Tradings
    st.session_state.risk_profile = st.selectbox(
        "🎯 PARAMETER SYSTEM CONFIDENCE:",
        options=["Moderat (Standar)", "Agresif (High Risk)", "Konservatif"],
        index=0
    )
    
    # Tombol Re-Scan dengan fungsi pembaruan waktu dinamik
    if st.button("🔄 RE-SCAN MARKET DATA", use_container_width=True, type="primary"):
        st.session_state.last_sync = datetime.now().strftime("%d %b %Y - %H:%M:%S WIB")
        st.rerun()
        
    if st.button("🗑️ Reset System Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache Terhapus!")
        st.rerun()

# =====================================================================
# 3. KONTEN UTAMA & MARKET INDEX (IHSG WIDGET)
# =====================================================================
head_col1, head_col2 = st.columns([3, 1])

with head_col1:
    st.header("📈 PRO MAX ALGORITHMIC TERMINAL")
    st.markdown(f"⏱️ **Sinkronisasi Terakhir:** `{st.session_state.last_sync}`")
    st.caption("Integrasi Multi-Pilar Terminal: Teknikal Quantum, Analisis Konsensus Fundamental, & Real-Time Bandarmologi")

with head_col2:
    # Tampilan Indeks Gabungan IHSG Sesuai Foto
    st.markdown("""
    <div style="background-color:#0c1017; border: 1px solid #1f2430; padding:10px; border-radius:8px; text-align:right;">
        <span style="font-size:11px; color:#8a99ad; font-weight:bold;">INDEX GABUNGAN (IHSG)</span><br>
        <span style="font-size:24px; font-weight:bold; color:white; font-family:monospace;">5,924.36</span><br>
        <span style="font-size:13px; color:#00ffcc; font-weight:bold;">▲ +11.92 (+0.20%)</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 4. MARKET CHART SIMULATION (CHART GRAFIK PASAR)
# =====================================================================
# Membuat visualisasi data tren pergerakan pasar (IHSG Candle-Simulation)
chart_data = pd.DataFrame(
    np.random.randn(20, 1) + [5900],
    columns=['IHSG Trend Line']
)
st.markdown("**📊 REALTIME MARKET COMPREHENSIVE GRAPH CHART**")
st.area_chart(chart_data, use_container_width=True)

# =====================================================================
# 5. PROMAX SYSTEM INTELLIGENCE SUMMARY (INDIKATOR LINGKARAN)
# =====================================================================
st.markdown("### 📊 PROMAX SYSTEM INTELLIGENCE SUMMARY")
st.markdown("<p style='color:#00ffcc; font-size:13px;'>👑 INSTITUTIONAL TOP PICKS: BMRI (85 Pts) • UNTR (85 Pts) • ICBP (85 Pts) • INDF (85 Pts)</p>", unsafe_allow_html=True)

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.markdown("""
    <div class="metric-box box-green">
        <div class="circle-indicator circle-green"></div>
        <div>
            <div class="metric-val">17</div>
            <div class="metric-lbl">Emiten (BUY / ACCUMULATE)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown("""
    <div class="metric-box box-yellow">
        <div class="circle-indicator circle-yellow"></div>
        <div>
            <div class="metric-val">5</div>
            <div class="metric-lbl">Emiten (WATCHING / NEUTRAL)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown("""
    <div class="metric-box box-red">
        <div class="circle-indicator circle-red"></div>
        <div>
            <div class="metric-val">3</div>
            <div class="metric-lbl">Emiten (STRONG SELL / REDUCE)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================================
# 6. RADAR MATRIX COMPREHENSIVE (TABEL UTAMA)
# =====================================================================
st.markdown(" ")
st.markdown("#### 📋 RADAR MATRIX COMPREHENSIVE")

df_radar = pd.DataFrame(st.session_state.raw_stocks).copy()
df_radar["BANDARMOLOGI"] = df_radar["TICKER"].map(st.session_state.bandar_state).fillna("NEUTRAL")

# Fungsi Elegan untuk mewarnai baris aksi trade secara presisi & aman dari IndexError
def style_radar_table(row):
    styles = [''] * len(row)
    if "CICIL BELI" in str(row["AKSI"]):
        styles[-1] = 'color: #00ffcc; font-weight: bold; background-color: #081a17;'
    elif "STRONG SELL" in str(row["AKSI"]):
        styles[-1] = 'color: #ff3344; font-weight: bold; background-color: #200a0d;'
    elif "HOLD" in str(row["AKSI"]):
        styles[-1] = 'color: #ffcc00; font-weight: bold; background-color: #1a1608;'
    return styles

df_radar_styled = df_radar.style.apply(style_radar_table, axis=1)
st.dataframe(df_radar_styled, use_container_width=True, hide_index=True)

# =====================================================================
# 7. MATRIX EVALUASI BANDARMOLOGI (INPUT DATA + PAGINATION FIX)
# =====================================================================
with st.expander("⚙️ BUKA MATRIX EVALUASI BANDARMOLOGI (Input Data Dropdown)", expanded=False):
    st.markdown("<p style='color:#00d4ff; font-size:13px;'>💡 TIPS: Pilih status bandarmologi emiten pada kolom dropdown, sistem akan menyinkronkan status ke tabel radar utama secara realtime.</p>", unsafe_allow_html=True)
    
    df_base = pd.DataFrame(st.session_state.raw_stocks)[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]]
    df_base["INTEGRASI BANDARMOLOGI"] = df_base["TICKER"].map(st.session_state.bandar_state).fillna("-")
    
    # Sistem Navigasi Paginasi yang Presisi
    items_per_page = 5
    total_eval_pages = max(1, (len(df_base) - 1) // items_per_page + 1)
    start_eval = st.session_state.eval_page * items_per_page
    
    # RESET INDEX: Menghindari IndexError saat data dimodifikasi di halaman berikutnya
    df_eval_display = df_base.iloc[start_eval:start_eval + items_per_page].reset_index(drop=True)
    
    edited_df = st.data_editor(
        df_eval_display,
        column_config={
            "INTEGRASI BANDARMOLOGI": st.column_config.SelectboxColumn(
                "INTEGRASI BANDARMOLOGI",
                help="Klik kotak kolom untuk mengubah status bandar",
                options=["-", "AKUMULASI", "NEUTRAL", "DISTRIBUSI"],
                required=True,
                width="medium"
            )
        },
        disabled=["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"],
        key="bandar_data_editor",
        use_container_width=True
    )
    
    # Deteksi perubahan dan simpan ke session_state menggunakan mapping Ticker asli
    if st.session_state.get("bandar_data_editor"):
        changes = st.session_state.bandar_data_editor.get("edited_rows", {})
        for idx, change in changes.items():
            if "INTEGRASI BANDARMOLOGI" in change:
                ticker_terkait = df_eval_display.loc[idx, "TICKER"]
                st.session_state.bandar_state[ticker_terkait] = change["INTEGRASI BANDARMOLOGI"]
        st.rerun()

    # Navigasi Kontrol Tombol Pagination
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous", disabled=st.session_state.eval_page == 0, use_container_width=True):
            st.session_state.eval_page -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<p style='text-align: center; font-weight: bold; margin-top:5px;'>Page {st.session_state.eval_page + 1} of {total_eval_pages}</p>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next ➡️", disabled=st.session_state.eval_page >= total_eval_pages - 1, use_container_width=True):
            st.session_state.eval_page += 1
            st.rerun()

# =====================================================================
# 8. ANALISIS KINERJA FINANSIAL & PARAMETER DIVIDEN (FORMAT REPLIKA FOTO)
# =====================================================================
st.markdown("---")
st.subheader("📑 Analisis Kinerja Finansial & Parameter Dividen")

pilihan_emiten = st.selectbox("📌 Pilih Kode Emiten untuk Evaluasi Mendalam:", options=[s['TICKER'] for s in st.session_state.raw_stocks])

if pilihan_emiten:
    # Seleksi Filter Metrik Menggunakan Mode Pills Tab yang Elegan
    metric_tab = st.radio("Metrik Finansial:", ["Net Income", "EPS", "Revenue"], horizontal=True)
    
    # 1. Penyusunan Data Finansial Terstruktur Periodik (Q1 - TTM) Sesuai Gambar Pendukung Anda
    if metric_tab == "Net Income":
        data_matrix = {
            "Period": ["Q1", "Q2", "Q3", "Q4", "Annualised", "TTM (Q1)"],
            "2026": ["14,684 B", "-", "-", "-", "58,736 B", "58,075 B"],
            "2025": ["14,146 B", "14,870 B", "14,381 B", "14,140 B", "57,537 B", "57,537 B"],
            "2024": ["12,879 B", "13,997 B", "14,198 B", "13,762 B", "54,836 B", "54,836 B"]
        }
    elif metric_tab == "EPS":
        data_matrix = {
            "Period": ["Q1", "Q2", "Q3", "Q4", "Annualised", "TTM (Q1)"],
            "2026": ["120.00", "-", "-", "-", "480.00", "475.00"],
            "2025": ["115.00", "118.00", "113.00", "112.00", "458.00", "458.00"],
            "2024": ["102.00", "109.00", "110.00", "105.00", "426.00", "426.00"]
        }
    else: # Revenue
        data_matrix = {
            "Period": ["Q1", "Q2", "Q3", "Q4", "Annualised", "TTM (Q1)"],
            "2026": ["42,150 B", "-", "-", "-", "168,600 B", "165,200 B"],
            "2025": ["40,200 B", "41,800 B", "40,900 B", "41,100 B", "164,000 B", "164,000 B"],
            "2024": ["38,100 B", "39,300 B", "39,500 B", "38,900 B", "155,800 B", "155,800 B"]
        }
        
    df_financial_matrix = pd.DataFrame(data_matrix)
    
    # Tampilkan Tabel Finansial Utama
    st.table(df_financial_matrix.set_index("Period"))
    
    st.markdown(" ")
    
    # 2. Penyusunan Bagian Bawah Tabel: Parameter Dividen Historis Sesuai Gambar 
    dividen_matrix = {
        "Data Parameter": ["Dividend (TTM)", "Payout Ratio", "Dividend Yield"],
        "2026": ["301.00", "63.17%", "4.85%"],
        "2025": ["336.00", "71.99%", "5.01%"],
        "2024": ["300.00", "67.44%", "3.58%"]
    }
    df_dividen_matrix = pd.DataFrame(dividen_matrix)
    
    st.table(df_dividen_matrix.set_index("Data Parameter"))

# =====================================================================
# 9. FOOTER SYSTEM TERMINAL SECURITY
# =====================================================================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #57657a; font-size: 11px;'>"
    "⚡ ZETA Terminal Pro Max Engine • Terproteksi Enkripsi Algoritma Quantum Multi-Pilar v3.5 • All Rights Reserved 2026"
    "</p>", 
    unsafe_allow_html=True
)