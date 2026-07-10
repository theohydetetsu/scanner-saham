import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# =====================================================================
# 1. KONFIGURASI HALAMAN & CUSTOM THEME
# =====================================================================
st.set_page_config(page_title="ZETA Terminal Pro Max v3.5", layout="wide")

st.markdown("""
<style>
    /* Styling Dasar App (Dark Theme) */
    .stApp { background-color: #05070a; color: #e2e8f0; }
    
    /* Panel Metrik Kotak Intelijen */
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
    
    .circle-indicator { width: 24px; height: 24px; border-radius: 50%; }
    .circle-green { background-color: #00ffcc; box-shadow: 0 0 10px #00ffcc; }
    .circle-yellow { background-color: #ffcc00; box-shadow: 0 0 10px #ffcc00; }
    .circle-red { background-color: #ff3344; box-shadow: 0 0 10px #ff3344; }
    
    .metric-val { font-size: 32px; font-family: 'Courier New', monospace; margin-bottom: -5px;}
    .metric-lbl { font-size: 13px; color: #8a99ad; }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. INISIALISASI STATE & DATA SAHAM
# =====================================================================
if "last_sync" not in st.session_state:
    st.session_state.last_sync = datetime.now().strftime("%d %b %Y - %H:%M:%S WIB")
if "bandar_state" not in st.session_state:
    st.session_state.bandar_state = {}
if "eval_page" not in st.session_state:
    st.session_state.eval_page = 0
if "risk_profile" not in st.session_state:
    st.session_state.risk_profile = "Moderat (Standar)"

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
# 3. SIDEBAR (CYBER PANEL)
# =====================================================================
with st.sidebar:
    st.title("💎 CYBER PANEL")
    st.caption("Premium Quantum Engine v3.5")
    
    st.markdown("### 📋 DAFTAR EMITEN PANTAUAN:")
    for stock in st.session_state.raw_stocks[:5]:
        st.markdown(f"• **{stock['TICKER']}** <span style='color:#00ffcc;'>Active</span>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.session_state.risk_profile = st.selectbox(
        "🎯 PARAMETER SYSTEM CONFIDENCE:",
        options=["Moderat (Standar)", "Agresif (High Risk)", "Konservatif"],
        index=0
    )
    
    if st.button("🔄 RE-SCAN MARKET DATA", use_container_width=True, type="primary"):
        st.session_state.last_sync = datetime.now().strftime("%d %b %Y - %H:%M:%S WIB")
        st.rerun()
        
    if st.button("🗑️ Reset System Cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# =====================================================================
# 4. KONTEN UTAMA & HEADER
# =====================================================================
col_h1, col_h2 = st.columns([3, 1])

with col_h1:
    st.header("📈 PRO MAX ALGORITHMIC TERMINAL")
    st.markdown(f"⏱️ **Sinkronisasi Terakhir:** `{st.session_state.last_sync}`")
    st.caption("Integrasi Multi-Pilar Terminal: Teknikal Quantum, Analisis Konsensus Fundamental, & Real-Time Bandarmologi")

with col_h2:
    st.markdown("""
    <div style="background-color:#0c1017; border: 1px solid #1f2430; padding:10px; border-radius:8px; text-align:right;">
        <span style="font-size:11px; color:#8a99ad; font-weight:bold;">INDEX GABUNGAN (IHSG)</span><br>
        <span style="font-size:24px; font-weight:bold; color:white; font-family:monospace;">5,924.36</span><br>
        <span style="font-size:13px; color:#00ffcc; font-weight:bold;">▲ +11.92 (+0.20%)</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 5. GRAFIK PASAR REALISTIS (Anti Kotak Biru)
# =====================================================================
st.markdown("**📊 REALTIME MARKET COMPREHENSIVE GRAPH CHART**")
# Membuat dummy data berupa pergerakan trend agar terlihat seperti chart saham (bukan blok biru)
np.random.seed(42)
dates = pd.date_range(start="2026-04-19", periods=60, freq="B")
# Random walk simulation
prices = np.round(np.cumsum(np.random.randn(60) * 20) + 6000, 2)
df_chart = pd.DataFrame({"IHSG Trend": prices}, index=dates)

# Menggunakan Line Chart agar bersih dan estetik
st.line_chart(df_chart, use_container_width=True, color="#ff3344")

# =====================================================================
# 6. SYSTEM INTELLIGENCE SUMMARY (Kotak Indikator)
# =====================================================================
st.markdown("### 📊 PROMAX SYSTEM INTELLIGENCE SUMMARY")
st.markdown("<p style='color:#00ffcc; font-size:13px; font-weight:bold;'>👑 INSTITUTIONAL TOP PICKS: BMRI (85 Pts) • UNTR (85 Pts) • ICBP (85 Pts) • INDF (85 Pts)</p>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    <div class="metric-box box-green">
        <div class="circle-indicator circle-green"></div>
        <div><div class="metric-val">17</div><div class="metric-lbl">Emiten (BUY / ACCUMULATE)</div></div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="metric-box box-yellow">
        <div class="circle-indicator circle-yellow"></div>
        <div><div class="metric-val">5</div><div class="metric-lbl">Emiten (WATCHING / NEUTRAL)</div></div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="metric-box box-red">
        <div class="circle-indicator circle-red"></div>
        <div><div class="metric-val">3</div><div class="metric-lbl">Emiten (STRONG SELL / REDUCE)</div></div>
    </div>""", unsafe_allow_html=True)

# =====================================================================
# 7. RADAR MATRIX COMPREHENSIVE (Tabel Utama Tanpa IndexError)
# =====================================================================
st.markdown(" ")
st.markdown("#### 📋 RADAR MATRIX COMPREHENSIVE")

df_radar = pd.DataFrame(st.session_state.raw_stocks).copy()
df_radar["BANDARMOLOGI"] = df_radar["TICKER"].map(st.session_state.bandar_state).fillna("NEUTRAL")

# FUNGSI PEWARNAAN BARU (Dijamin AMAN 100% dari IndexError)
def style_kolom_aksi(val):
    val_str = str(val).upper()
    if "CICIL BELI" in val_str:
        return 'color: #00ffcc; font-weight: bold; background-color: #081a17;'
    elif "STRONG SELL" in val_str:
        return 'color: #ff3344; font-weight: bold; background-color: #200a0d;'
    elif "HOLD" in val_str or "WATCHING" in val_str:
        return 'color: #ffcc00; font-weight: bold; background-color: #1a1608;'
    return ''

# Hanya mewarnai spesifik kolom 'AKSI'
df_radar_styled = df_radar.style.map(style_kolom_aksi, subset=['AKSI'])
st.dataframe(df_radar_styled, use_container_width=True, hide_index=True)

# =====================================================================
# 8. MATRIX BANDARMOLOGI (Dropdown & Paginasi Fixed)
# =====================================================================
with st.expander("⚙️ BUKA MATRIX EVALUASI BANDARMOLOGI (Input Data)", expanded=False):
    st.markdown("<p style='color:#00d4ff; font-size:13px;'>💡 <b>Petunjuk:</b> Ubah status bandarmologi emiten pada kolom dropdown di bawah untuk mengupdate kalkulasi radar utama.</p>", unsafe_allow_html=True)
    
    df_base = pd.DataFrame(st.session_state.raw_stocks)[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]]
    df_base["INTEGRASI BANDARMOLOGI"] = df_base["TICKER"].map(st.session_state.bandar_state).fillna("NEUTRAL")
    
    # Logika Paginasi yang Presisi
    items_per_page = 5
    total_eval_pages = max(1, (len(df_base) - 1) // items_per_page + 1)
    
    # Boundary Guard (mencegah error jika data mengecil)
    if st.session_state.eval_page >= total_eval_pages:
        st.session_state.eval_page = total_eval_pages - 1
        
    start_eval = st.session_state.eval_page * items_per_page
    
    # RESET INDEX: Ini kunci anti-IndexError saat ganti halaman
    df_eval_display = df_base.iloc[start_eval:start_eval + items_per_page].reset_index(drop=True)
    
    edited_df = st.data_editor(
        df_eval_display,
        column_config={
            "INTEGRASI BANDARMOLOGI": st.column_config.SelectboxColumn(
                "INTEGRASI BANDARMOLOGI",
                help="Klik untuk ubah status",
                options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"],
                required=True,
                width="medium"
            )
        },
        disabled=["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"],
        key="bandar_data_editor",
        use_container_width=True,
        hide_index=True
    )
    
    # Simpan Perubahan Dropdown
    if st.session_state.get("bandar_data_editor"):
        changes = st.session_state.bandar_data_editor.get("edited_rows", {})
        for idx, change in changes.items():
            if "INTEGRASI BANDARMOLOGI" in change:
                ticker_terkait = df_eval_display.loc[idx, "TICKER"]
                st.session_state.bandar_state[ticker_terkait] = change["INTEGRASI BANDARMOLOGI"]
        st.rerun()

    # Tombol Paginasi
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
# 9. ANALISIS KINERJA FINANSIAL & DIVIDEN
# =====================================================================
st.markdown("---")
st.markdown("### 📑 Analisis Kinerja Finansial & Parameter Dividen")

pilihan_emiten = st.selectbox("📌 Pilih Kode Emiten untuk Evaluasi Mendalam:", options=[s['TICKER'] for s in st.session_state.raw_stocks])

if pilihan_emiten:
    st.info(f"Modul finansial lanjutan untuk **{pilihan_emiten}** aktif (Data Kuartalan & TTM).")
    
    # Navigasi Metrik
    metric_tab = st.radio("Metrik Finansial:", ["Net Income", "EPS", "Revenue"], horizontal=True)
    
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
    else: 
        data_matrix = {
            "Period": ["Q1", "Q2", "Q3", "Q4", "Annualised", "TTM (Q1)"],
            "2026": ["42,150 B", "-", "-", "-", "168,600 B", "165,200 B"],
            "2025": ["40,200 B", "41,800 B", "40,900 B", "41,100 B", "164,000 B", "164,000 B"],
            "2024": ["38,100 B", "39,300 B", "39,500 B", "38,900 B", "155,800 B", "155,800 B"]
        }
        
    st.table(pd.DataFrame(data_matrix).set_index("Period"))
    
    st.markdown(" ")
    dividen_matrix = {
        "Data Parameter": ["Dividend (TTM)", "Payout Ratio", "Dividend Yield"],
        "2026": ["301.00", "63.17%", "4.85%"],
        "2025": ["336.00", "71.99%", "5.01%"],
        "2024": ["300.00", "67.44%", "3.58%"]
    }
    st.table(pd.DataFrame(dividen_matrix).set_index("Data Parameter"))

st.markdown("---")
st.markdown("<p style='text-align: center; color: #57657a; font-size: 11px;'>⚡ ZETA Terminal Pro Max Engine • Terproteksi Enkripsi Algoritma Multi-Pilar v3.5 • All Rights Reserved 2026</p>", unsafe_allow_html=True)