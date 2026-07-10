import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import pytz
import warnings

# Mengabaikan warning bawaan
warnings.filterwarnings('ignore')

# ==========================================
# 0. KONEKTIVITAS ENGINE GRAFIK ADVANCED
# ==========================================
HAS_PLOTLY = False
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA & UI STYLE
# ==========================================
st.set_page_config(page_title="AI Stock Dashboard Pro Max v4.0", page_icon="💎", layout="wide")

# Inject Custom CSS Premium Theme (Glassmorphism & Typography)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&display=swap');
   
    /* Global Font & Background */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1e293b, #020617);
    }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 98%; }
   
    /* Typography Premium */
    h1 { color: #f8fafc; font-weight: 900; letter-spacing: -1px; font-size: 2.2rem !important; margin-bottom: 0; }
    p { color: #94a3b8; font-weight: 300; }
   
    /* Sidebar Premium */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
   
    /* Glassmorphism Cards */
    .premium-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .premium-card:hover {
        transform: translateY(-5px);
        border-color: rgba(0, 255, 204, 0.3);
    }
   
    /* IHSG Box */
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; }
    .ihsg-title { color: #94a3b8; font-size: 0.8rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; }
    .ihsg-score { color: #f8fafc; font-size: 2.5rem; font-weight: 900; line-height: 1.1; margin: 5px 0; }
   
    /* Strategy Metric Numbers */
    .strat-num { font-size: 3rem; font-weight: 900; margin: 5px 0; line-height: 1; text-align: center; }
    .strat-label { font-size: 0.85rem; font-weight: 600; text-align: center; letter-spacing: 1px; }
   
    /* Custom Button */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
        color: #020617 !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 12px !important;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(79, 172, 254, 0.5);
    }
   
    /* Media Query untuk HP */
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; text-align: center; }
        .ihsg-box { text-align: center; margin-top: 15px; }
        .ihsg-score { font-size: 2rem; }
        .strat-num { font-size: 2rem; }
    }
</style>
""", unsafe_allow_html=True)

# Helper Waktu WIB
def get_waktu_wib():
    tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(tz).strftime("%d %b %Y - %H:%M:%S WIB")

# Inisialisasi Session State
if "raw_stocks" not in st.session_state: st.session_state.raw_stocks = []
if "last_update" not in st.session_state: st.session_state.last_update = None
if "bandar_state" not in st.session_state: st.session_state.bandar_state = {}

# Daftar 20 Saham Bluechip & Unggulan BEI
roster_20_saham = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", "AMRT",
    "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", "CPIN", "ANTM"
]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ihsg_data(tf="Daily"):
    try:
        if tf == "1 Jam": df = yf.download("^JKSE", period="1mo", interval="1h", progress=False)
        elif tf == "4 Jam":
            df = yf.download("^JKSE", period="1mo", interval="1h", progress=False)
            if not df.empty: df = df.resample('4h').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last'}).dropna()
        elif tf == "Weekly": df = yf.download("^JKSE", period="1y", interval="1wk", progress=False)
        else: df = yf.download("^JKSE", period="3mo", interval="1d", progress=False)

        if df.empty: return None, None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        df = df.ffill()
       
        harga_skg = float(df['Close'].iloc[-1])
        harga_lalu = float(df['Close'].iloc[-2])
        perubahan = harga_skg - harga_lalu
        persen = (perubahan / harga_lalu) * 100
        return df, harga_skg, perubahan, persen
    except Exception: return None, None, None, None

# PENYEMPURNAAN: RSI menggunakan metode Wilder's Smoothing (EMA)
def hitung_rsi_akurat(df, periods=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    ema_gain = gain.ewm(alpha=1/periods, min_periods=periods).mean()
    ema_loss = loss.ewm(alpha=1/periods, min_periods=periods).mean()
    rs = ema_gain / ema_loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=600, show_spinner=False)
def fetch_raw_data(saham_list):
    master_data = []
    for emiten in saham_list:
        try:
            kode = emiten.replace(".JK", "")
            df = yf.download(emiten, period="6mo", progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
            df = df.ffill()
            if pd.isna(df['Close'].iloc[-1]): continue
           
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['RSI'] = hitung_rsi_akurat(df) # Menggunakan RSI yang sudah diperbaiki
           
            harga_skg = float(df['Close'].iloc[-1])
            ema20_skg = float(df['EMA20'].iloc[-1])
            macd_skg = float(df['MACD'].iloc[-1])
            sig_skg = float(df['Signal'].iloc[-1])
            rsi_skg = float(df['RSI'].iloc[-1]) if not np.isnan(df['RSI'].iloc[-1]) else 50.0
           
            ticker = yf.Ticker(emiten)
            info = ticker.info
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            if pbv and (pbv > 100 or pbv < 0): pbv = 1.0
            div_yield = info.get('dividendYield', 0)
            if div_yield and div_yield < 1.0: div_yield = div_yield * 100
               
            master_data.append({
                "TICKER": kode, "HARGA": harga_skg, "PER": round(per, 2) if per else 0.0,
                "PBV": round(pbv, 2) if pbv else 0.0, "DIV_YIELD": round(div_yield, 2) if div_yield else 0.0,
                "RSI": round(rsi_skg, 2), "UP_EMA20": harga_skg > ema20_skg, "MACD_GOLDEN": macd_skg > sig_skg
            })
        except: continue
    return master_data

# ==========================================
# 2. SIDEBAR (CYBER PANEL)
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0px 20px 0px; text-align: center;">
        <h2 style="background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.8rem; font-weight: 900; margin-bottom: 0px;">💎 ZETA CORE</h2>
        <p style="color: #64748b; font-size: 0.8rem; margin-top: 5px; font-weight: 600; letter-spacing: 1px;">AI PREMIUM SCANNER v4.0</p>
    </div>
    """, unsafe_allow_html=True)

    daftar_saham = [s.strip().upper() + ".JK" for s in roster_20_saham]
   
    st.markdown("<span style='color:#cbd5e1; font-size:0.85rem; font-weight:600;'>🎯 PROFIL RISIKO TRADING</span>", unsafe_allow_html=True)
    profil_risiko = st.selectbox("", ["Moderat (Standar)", "Agresif (High Risk)", "Konservatif (Aman)"], label_visibility="collapsed")
   
    st.write(" ")
    if st.button("🔄 JALANKAN PEMINDAIAN", use_container_width=True):
        st.cache_data.clear()
        with st.spinner("⏳ Memindai Market BEI..."):
            st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
            st.session_state.last_update = get_waktu_wib()
        st.rerun()

    st.markdown("---")
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.5); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
        <p style="margin:0; font-size: 0.85rem; color: #94a3b8;">📊 <b>Active Watchlist:</b> {len(daftar_saham)} Saham</p>
        <p style="margin:5px 0 0 0; font-size: 0.85rem; color: {'#10b981' if st.session_state.last_update else '#f59e0b'};">
            ● <b>NETWORK:</b> {'ONLINE' if st.session_state.last_update else 'IDLE'}
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. HEADER UTAMA & IHSG
# ==========================================
st.markdown("<h1>📈 Algorithmic Market Intelligence</h1>", unsafe_allow_html=True)

col_header1, col_header2 = st.columns([1.5, 1])

with col_header1:
    if st.session_state.last_update:
        st.markdown(f"<p style='margin-top: 8px;'>🕒 Terakhir Diperbarui: <span style='color:#00f2fe; font-weight: 600;'>{st.session_state.last_update}</span></p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='margin-top: 8px;'>🕒 Terakhir Diperbarui: <code>Menunggu Inisiasi...</code></p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.95rem; margin-top:-5px;'>Multi-Pilar Integrasi Terminal: Teknikal Quantum, Analisis Konsensus Fundamental, & Real-Time Bandarmologi.</p>", unsafe_allow_html=True)

# Ambil data IHSG
timeframe_pilihan = "Daily" # Default agar clean
df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data(tf=timeframe_pilihan)

with col_header2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_hex = "#10b981" if ihsg_chg >= 0 else "#f43f5e"
        st.markdown(f"""
        <div class="premium-card ihsg-box">
            <span class="ihsg-title">Indeks Harga Saham Gabungan</span>
            <span class="ihsg-score">{ihsg_now:,.2f}</span>
            <span style="color: {warna_hex}; font-size: 1.1rem; font-weight: 800;">
                {warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)
            </span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. AUTO-LOAD JIKA KOSONG
# ==========================================
if len(st.session_state.raw_stocks) == 0:
    with st.spinner("⏳ Menghidupkan Engine Pertama Kali..."):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
        st.session_state.last_update = get_waktu_wib()
        st.rerun()

# ==========================================
# 5. KALKULASI AI & UI PRESENTATION
# ==========================================
if st.session_state.raw_stocks:
    st.markdown("---")
    st.markdown("<h3 style='color: #f8fafc; font-weight: 800; margin-bottom: 1rem;'>🧠 AI Pro Max Recommendation Engine</h3>", unsafe_allow_html=True)
   
    skor_buy_target = 70
    if "Agresif" in profil_risiko: skor_buy_target = 60
    elif "Konservatif" in profil_risiko: skor_buy_target = 75
   
    hasil_rekomendasi = []
    list_top_picks = []
   
    for raw_info in st.session_state.raw_stocks:
        ticker = raw_info["TICKER"]
        status_bandar = st.session_state.bandar_state.get(ticker, "NEUTRAL")
       
        skor = 0
        if raw_info["UP_EMA20"]: skor += 15
        if raw_info["MACD_GOLDEN"]: skor += 15
        if 30 <= raw_info["RSI"] <= 70: skor += 10
        if raw_info["PER"] != 0 and raw_info["PER"] < 15: skor += 15
        if raw_info["PBV"] != 0 and raw_info["PBV"] < 2: skor += 15
        if raw_info["DIV_YIELD"] > 3: skor += 10
           
        if status_bandar == "AKUMULASI": skor += 20
        elif status_bandar == "DISTRIBUSI": skor -= 10
        else: skor += 5
       
        skor = max(0, min(100, skor))
       
        if skor >= skor_buy_target:
            keputusan, sinyal = "🟢 ACCUMULATE", "BUY"
            list_top_picks.append((ticker, skor))
        elif skor >= 45:
            keputusan, sinyal = "🟡 HOLD", "NEUTRAL"
        else:
            keputusan, sinyal = "🔴 LIQUIDATE", "SELL"
           
        hasil_rekomendasi.append({
            "TICKER": ticker,
            "HARGA": f"Rp {int(raw_info['HARGA']):,}".replace(",", "."),
            "PER (x)": f"{float(raw_info['PER']):.2f}" if raw_info['PER'] > 0 else "-",
            "PBV (x)": f"{float(raw_info['PBV']):.2f}" if raw_info['PBV'] > 0 else "-",
            "DIV YIELD": f"{float(raw_info['DIV_YIELD']):.2f}%",
            "RSI": f"{float(raw_info['RSI']):.2f}",
            "BANDARMOLOGI": status_bandar,
            "SKOR AI": skor,
            "SINYAL": sinyal,
            "REKOMENDASI": keputusan
        })
       
    df_final = pd.DataFrame(hasil_rekomendasi)
   
    # Tampilan Institutional Top Picks (Glassmorphism Highlight)
    if list_top_picks:
        list_top_picks.sort(key=lambda x: x[1], reverse=True)
        string_picks = " • ".join([f"{t} ({s})" for t, s in list_top_picks[:6]])
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(2, 6, 23, 0) 100%); border-left: 4px solid #10b981; padding: 15px 20px; border-radius: 0 12px 12px 0; margin-bottom: 25px;">
            <span style="color: #34d399; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">🔥 AI Top Picks Hari Ini</span><br/>
            <span style="color: #f8fafc; font-size: 1.1rem; font-weight: 600;">{string_picks}</span>
        </div>
        """, unsafe_allow_html=True)

    t_buy = sum('🟢' in x for x in df_final['REKOMENDASI'])
    t_hold = sum('🟡' in x for x in df_final['REKOMENDASI'])
    t_sell = sum('🔴' in x for x in df_final['REKOMENDASI'])
   
    # --- METRIC CARDS STRATEGI ---
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""<div class='premium-card' style='border-top: 3px solid #10b981;'>
            <div class='strat-label' style='color:#34d399;'>🟢 STRATEGI BUY</div>
            <div class='strat-num' style='color:#f8fafc;'>{t_buy}</div>
        </div>""", unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""<div class='premium-card' style='border-top: 3px solid #f59e0b;'>
            <div class='strat-label' style='color:#fbbf24;'>🟡 STRATEGI HOLD</div>
            <div class='strat-num' style='color:#f8fafc;'>{t_hold}</div>
        </div>""", unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""<div class='premium-card' style='border-top: 3px solid #f43f5e;'>
            <div class='strat-label' style='color:#fb7185;'>🔴 STRATEGI SELL</div>
            <div class='strat-num' style='color:#f8fafc;'>{t_sell}</div>
        </div>""", unsafe_allow_html=True)
   
    # --- TABEL RADAR MATRIX ---
    st.markdown("<h4 style='font-size: 1.1rem; margin-top: 30px; color:#e2e8f0; font-weight: 600;'>📋 Market Radar Matrix</h4>", unsafe_allow_html=True)
   
    def style_tabel_premium(row):
        styles = [''] * len(row)
        kep = row['REKOMENDASI']
       
        # Pewarnaan baris berdasarkan rekomendasi
        if '🟢' in kep: bg = 'background-color: rgba(16, 185, 129, 0.1); color: #34d399; font-weight: 600;'
        elif '🟡' in kep: bg = 'background-color: rgba(245, 158, 11, 0.1); color: #fbbf24;'
        elif '🔴' in kep: bg = 'background-color: rgba(244, 63, 94, 0.1); color: #fb7185;'
        else: bg = ''
           
        for i, col in enumerate(row.index):
            if col in ['BANDARMOLOGI', 'SKOR AI', 'SINYAL', 'REKOMENDASI']: styles[i] = bg
            if col == 'PER (x)':
                try:
                    p = float(row[col])
                    if p < 15.0: styles[i] = 'color: #34d399; font-weight: bold;'
                    elif p > 25.0: styles[i] = 'color: #fb7185;'
                except: pass
        return styles

    st.dataframe(df_final.style.apply(style_tabel_premium, axis=1), use_container_width=True, hide_index=True)
   
    # --- MATRIX EVALUASI BANDARMOLOGI ---
    st.write(" ")
    with st.expander("🛠️ SESUAIKAN DATA BANDARMOLOGI (BROKER SUMMARY)", expanded=False):
        st.markdown("<p style='font-size:0.85rem;'>Ubah parameter akumulasi bandar di sini. Tabel di atas akan dihitung ulang secara otomatis berdasarkan input Anda.</p>", unsafe_allow_html=True)
       
        df_base_eval = pd.DataFrame(st.session_state.raw_stocks)[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]]
        df_base_eval["BANDARMOLOGI"] = df_base_eval["TICKER"].map(st.session_state.bandar_state).fillna("NEUTRAL")
       
        df_edited = st.data_editor(
            df_base_eval,
            column_config={
                "BANDARMOLOGI": st.column_config.SelectboxColumn("STATUS BANDAR", options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"], required=True),
                "TICKER": st.column_config.Column(disabled=True), "HARGA": st.column_config.Column(disabled=True),
                "PER": st.column_config.Column(disabled=True), "PBV": st.column_config.Column(disabled=True),
                "DIV_YIELD": st.column_config.Column(disabled=True), "RSI": st.column_config.Column(disabled=True),
            },
            hide_index=True, use_container_width=True, key="editor_saham_bandar"
        )
       
        if st.session_state.get("editor_saham_bandar"):
            changes = st.session_state.editor_saham_bandar.get("edited_rows", {})
            state_changed = False
            for idx, change in changes.items():
                if "BANDARMOLOGI" in change:
                    ticker_berubah = df_base_eval.loc[idx, "TICKER"]
                    st.session_state.bandar_state[ticker_berubah] = change["BANDARMOLOGI"]
                    state_changed = True
            if state_changed: st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem; font-weight: 600; letter-spacing: 1px;'>⚡ ZETA CORE ENGINE • SECURE ALGORITHMIC TERMINAL v4.0</p>", unsafe_allow_html=True)
