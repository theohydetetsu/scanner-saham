import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
from datetime import datetime

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
# 1. KONFIGURASI HALAMAN UTAMA & UI PREMIUM
# ==========================================
st.set_page_config(page_title="ZETA Terminal Pro Max v3.5", page_icon="💎", layout="wide")

# CSS Kustom: Institutional Dark Mode & Paginasi
st.markdown("""
<style>
    .stApp { background-color: #07090e; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 95%; }
    h1, h2, h3, h4 { font-family: 'Inter', 'Helvetica Neue', sans-serif; color: #f0f3f6; font-weight: 700; }
    h1 { font-size: 32pt !important; letter-spacing: -0.5px; }
    h3 { font-size: 24px !important; }
    
    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] { font-size: 14pt !important; }
    label { font-size: 13pt !important; font-weight: 600 !important; color: #cdd2d9 !important; }
    
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th { font-size: 13pt !important; padding: 10px 12px !important; }
    
    [data-testid="stSidebar"] { background-color: #0c0f16 !important; border-right: 1px solid #1f2430; }
    
    .metric-card {
        background: linear-gradient(145deg, #111520, #0d1017);
        border: 1px solid #1f2430;
        padding: 12px 20px;
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover { border-color: #00d4ff; }
    
    /* Tombol Navigasi Page */
    .stButton button {
        background-color: #111520 !important; border: 1px solid #1f2430 !important; color: #00d4ff !important;
        font-weight: bold !important; transition: 0.3s;
    }
    .stButton button:hover { border-color: #00d4ff !important; color: #ffffff !important; }
    
    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(90deg, #00d4ff, #00ffcc) !important; color: #05070a !important;
        font-weight: 700 !important; font-size: 16px !important; border-radius: 8px !important; border: none !important;
    }
    
    /* Expander Premium */
    .streamlit-expanderHeader { background-color: #111520 !important; border-radius: 8px !important; color: #00d4ff !important; font-size: 16px !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State
if "raw_stocks" not in st.session_state: st.session_state.raw_stocks = []
if "last_update" not in st.session_state: st.session_state.last_update = None
if "bandar_state" not in st.session_state: st.session_state.bandar_state = {}
if "radar_page" not in st.session_state: st.session_state.radar_page = 0
if "eval_page" not in st.session_state: st.session_state.eval_page = 0

@st.cache_data(ttl=600, show_spinner=False)
def fetch_ihsg_data(tf="Daily"):
    try:
        if tf == "1 Hour": df_ihsg = yf.download("^JKSE", period="1mo", interval="1h", progress=False)
        elif tf == "4 Hour": 
            df_ihsg = yf.download("^JKSE", period="1mo", interval="1h", progress=False)
            if not df_ihsg.empty: df_ihsg = df_ihsg.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
        elif tf == "Weekly": df_ihsg = yf.download("^JKSE", period="1y", interval="1wk", progress=False)
        else: df_ihsg = yf.download("^JKSE", period="3mo", interval="1d", progress=False)

        if df_ihsg.empty: return None, None, None, None
        df_ihsg.columns = [col[0] if isinstance(col, tuple) else col for col in df_ihsg.columns]
        df_ihsg = df_ihsg.ffill() 
        
        harga_skg = float(df_ihsg['Close'].iloc[-1])
        harga_lalu = float(df_ihsg['Close'].iloc[-2])
        perubahan = harga_skg - harga_lalu
        persen = (perubahan / harga_lalu) * 100
        
        return df_ihsg, harga_skg, perubahan, persen
    except Exception:
        return None, None, None, None

def fetch_advanced_financials(ticker_code):
    try:
        ticker = yf.Ticker(ticker_code + ".JK")
        return ticker.financials, ticker.quarterly_financials, ticker.info, ticker.dividends, ticker.history(period="5y")
    except Exception:
        return None, None, None, None, None

# HEADER UTAMA
st.markdown("<h1 style='margin-bottom:0px;'>📈 PRO MAX ALGORITHMIC TERMINAL</h1>", unsafe_allow_html=True)

col_header1, col_header2 = st.columns([2, 1])

with col_header1:
    if st.session_state.last_update:
        st.markdown(f"🕒 <span style='font-size:13pt;'>**Sinkronisasi Terakhir:** `{st.session_state.last_update}`</span>", unsafe_allow_html=True)
    else:
        st.markdown("🕒 <span style='font-size:13pt;'>**Sinkronisasi Terakhir:** `Menunggu sinkronisasi sistem...`</span>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8a92a6; font-size: 12pt; margin-top:-5px;'>Integrasi Multi-Pilar Terminal: Teknikal Quantum, Analisis Konsensus Fundamental, & Real-Time Bandarmologi</p>", unsafe_allow_html=True)

# ==========================================
# 2. GRAFIK IHSG DENGAN TIMEFRAME SELECTOR
# ==========================================
st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
tf_col1, tf_col2 = st.columns([8, 2])
with tf_col2:
    selected_tf = st.selectbox("⏳ Timeframe IHSG:", ["1 Hour", "4 Hour", "Daily", "Weekly"], index=2, label_visibility="collapsed")

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data(selected_tf)

with col_header2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_hex = "#00ffcc" if ihsg_chg >= 0 else "#ff3366"
        st.markdown(f"""
        <div style="text-align: right; background-color: #111520; padding: 12px 20px; border-radius: 12px; border: 1px solid #1f2430; margin-top:-45px;">
            <span style="color: #8a90a6; font-size: 13px; font-weight: 700; letter-spacing: 1px;">INDEX GABUNGAN (IHSG)</span><br/>
            <span style="color: #ffffff; font-size: 42px; font-weight: 900; line-height: 1.1;">{ihsg_now:,.2f}</span><br/> 
            <span style="color: {warna_hex}; font-size: 17px; font-weight: bold;">{warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

if df_ihsg_hist is not None:
    if HAS_PLOTLY:
        fig = go.Figure(data=[go.Candlestick(
            x=df_ihsg_hist.index, open=df_ihsg_hist['Open'], high=df_ihsg_hist['High'],
            low=df_ihsg_hist['Low'], close=df_ihsg_hist['Close'],
            increasing_line_color='#00ffcc', decreasing_line_color='#ff3366', name="IHSG"
        )])
        fig.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=5, b=5), height=240, xaxis_rangeslider_visible=False,
            yaxis=dict(gridcolor='rgba(255,255,255,0.03)', tickfont=dict(size=13)),
            xaxis=dict(gridcolor='rgba(255,255,255,0.03)', tickfont=dict(size=13))
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.line_chart(df_ihsg_hist[['Close']], color="#00ffcc", height=240)

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
st.sidebar.markdown("""
<div style="padding: 5px 0px 15px 0px;">
    <h2 style="color: #00d4ff; font-size: 24px; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 0px;">💎 CYBER PANEL</h2>
    <p style="color: #6c757d; font-size: 13px; margin-top: 2px; margin-bottom: 0px;">Premium Quantum Engine v3.5</p>
</div>
""", unsafe_allow_html=True)

roster_saham_idx = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", 
    "AMRT", "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", 
    "CPIN", "ANTM", "TPIA", "BREN", "AMMN", "ADMR", "MEDC", "AKRA", "ACES", 
    "MYOR", "SMGR", "INCO", "PGEO", "BUKA", "MDKA", "HRUM", "ISAT", "EXCL"
]

saham_terpilih = st.sidebar.multiselect("📋 DAFTAR EMITEN PANTAUAN:", options=roster_saham_idx, default=roster_saham_idx[:25])
daftar_saham = [s.strip().upper() + ".JK" for s in saham_terpilih if s.strip()]

# Inisialisasi State Bandarmologi untuk saham yang dipilih
for s in daftar_saham:
    ticker_name = s.replace(".JK", "")
    if ticker_name not in st.session_state.bandar_state:
        st.session_state.bandar_state[ticker_name] = "NEUTRAL"

st.sidebar.write(" ")
muat_data = st.sidebar.button("🔄 RE-SCAN MARKET DATA", use_container_width=True, type="primary")
st.sidebar.markdown("<br/>", unsafe_allow_html=True)

st.sidebar.markdown("<span style='color:#8a90a6; font-size:12px; font-weight:bold;'>🎛️ PARAMETER SYSTEM CONFIDENCE</span>", unsafe_allow_html=True)
profil_risiko = st.sidebar.selectbox("🎯 Profil Risiko Trading:", ["Moderat (Standar)", "Agresif (High Risk)", "Konservatif (Aman)"], label_visibility="collapsed")
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reset System Cache", use_container_width=True):
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# ==========================================
# 4. CORE ENGINE CALCULATION
# ==========================================
def hitung_rsi(df, periods=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_raw_data(saham_list):
    master_data = []
    for emiten in saham_list:
        try:
            kode = emiten.replace(".JK", "")
            df = yf.download(emiten, period="6mo", progress=False)
            if df.empty: continue
            
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            df = df.ffill() 
            if pd.isna(df['Close'].iloc[-1]): continue 
            
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['RSI'] = hitung_rsi(df)
            
            harga_skg = float(df['Close'].iloc[-1])
            ticker = yf.Ticker(emiten)
            info = ticker.info
            
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            if pbv and (pbv > 100 or pbv < 0): pbv = 1.0
            div_yield = info.get('dividendYield', 0)
            if div_yield < 1.0: div_yield = div_yield * 100
                
            master_data.append({
                "TICKER": kode,
                "HARGA": harga_skg,
                "PER": round(per, 2) if per else 0.0,
                "PBV": round(pbv, 2) if pbv else 0.0,
                "DIV_YIELD": round(div_yield, 2) if div_yield else 0.0,
                "RSI": round(float(df['RSI'].iloc[-1]), 2) if not np.isnan(df['RSI'].iloc[-1]) else 50.0,
                "UP_EMA20": harga_skg > float(df['EMA20'].iloc[-1]),
                "MACD_GOLDEN": float(df['MACD'].iloc[-1]) > float(df['Signal'].iloc[-1])
            })
            time.sleep(0.04) 
        except: continue
    return master_data

if muat_data or len(st.session_state.raw_stocks) == 0:
    if daftar_saham:
        with st.spinner("⏳ Mengkalibrasi Data Pasar..."):
            st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
            st.session_state.last_update = datetime.now().strftime("%d %b %Y - %H:%M:%S WIB")
            st.session_state.radar_page = 0
            st.session_state.eval_page = 0
            st.rerun()

# ==========================================
# 5. PEMROSESAN ALGORITMA (BACKGROUND)
# ==========================================
if st.session_state.raw_stocks:
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
            keputusan = "🟢 CICIL BELI"
            sinyal = "BUY / ACCUMULATE"
            list_top_picks.append((ticker, skor))
        elif skor >= 45:
            keputusan = "🟡 HOLD / WATCHING"
            sinyal = "NEUTRAL"
        else:
            keputusan = "🔴 STRONG SELL"
            sinyal = "TAKE PROFIT / SELL"
            
        hasil_rekomendasi.append({
            "TICKER": ticker,
            "HARGA TERAKHIR": f"Rp {int(raw_info['HARGA']):,}".replace(",", "."),
            "PER (x)": f"{float(raw_info['PER']):.2f}" if raw_info['PER'] > 0 else "-",
            "PBV (x)": f"{float(raw_info['PBV']):.2f}" if raw_info['PBV'] > 0 else "-",
            "DIV YIELD": f"{float(raw_info['DIV_YIELD']):.2f}%",
            "RSI": f"{float(raw_info['RSI']):.2f}",
            "BANDARMOLOGI": status_bandar,
            "SKOR SYSTEM": skor,
            "SINYAL TEKNIKAL": sinyal,
            "AKSI TRADE": keputusan
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)

    # ==========================================
    # 6. BLOK PROMAX SYSTEM INTELLIGENCE SUMMARY
    # ==========================================
    st.markdown("<h3 style='margin-bottom:15px;'>📊 PROMAX SYSTEM INTELLIGENCE SUMMARY</h3>", unsafe_allow_html=True)
    
    if list_top_picks:
        list_top_picks.sort(key=lambda x: x[1], reverse=True)
        string_picks = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join([f"<strong style='color:#ffffff;'>{t}</strong> <span style='color:#00d4ff;'>({s} Pts)</span>" for t, s in list_top_picks[:5]])
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #0f141c, #07090d); border-left: 4px solid #00d4ff; border: 1px solid #1f2430; padding: 15px 22px; border-radius: 4px 12px 12px 4px; margin-bottom: 25px;">
            <span style="color: #00d4ff; font-weight: 800; font-size: 13px; letter-spacing: 1.5px; text-transform: uppercase; display: block; margin-bottom: 4px;">INSTITUTIONAL TOP PICKS</span>
            <span style="font-size: 16px; letter-spacing: 0.3px;">{string_picks}</span>
        </div>
        """, unsafe_allow_html=True)

    t_buy = sum('🟢' in x for x in df_final['AKSI TRADE'])
    t_hold = sum('🟡' in x for x in df_final['AKSI TRADE'])
    t_sell = sum('🔴' in x for x in df_final['AKSI TRADE'])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"<div class='metric-card'><h2 style='margin:0; color:#ffffff; font-size:68px; font-weight:900; line-height: 1.1;'><span style='color:#00e676;'>🟢</span> {t_buy} <span style='font-size:20px; color:#8a90a6; font-weight:normal;'>Emiten</span></h2></div>", unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"<div class='metric-card'><h2 style='margin:0; color:#ffffff; font-size:68px; font-weight:900; line-height: 1.1;'><span style='color:#ffb300;'>🟡</span> {t_hold} <span style='font-size:20px; color:#8a90a6; font-weight:normal;'>Emiten</span></h2></div>", unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"<div class='metric-card'><h2 style='margin:0; color:#ffffff; font-size:68px; font-weight:900; line-height: 1.1;'><span style='color:#ff1744;'>🔴</span> {t_sell} <span style='font-size:20px; color:#8a90a6; font-weight:normal;'>Emiten</span></h2></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 7. TABEL RADAR MATRIX (POSISI ATAS + PAGINATION)
    # ==========================================
    st.markdown(f"<h4 style='font-size: 18px; color:#8a90a6; margin-bottom:8px;'>📋 RADAR MATRIX COMPREHENSIVE</h4>", unsafe_allow_html=True)
    
    def style_tabel_premium(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for idx, row in df.iterrows():
            try:
                per = float(row['PER (x)'])
                if per < 15.0: styles.at[idx, 'PER (x)'] = 'color: #00ffcc; font-weight: bold;'
                elif per > 25.0: styles.at[idx, 'PER (x)'] = 'color: #ff1744;'
            except: pass
            kep = row['AKSI TRADE']
            if '🟢' in kep: styles.iloc[idx, -3:] = 'background-color: #0b1a13; color: #00ffcc; font-weight: bold;'
            elif '🟡' in kep: styles.iloc[idx, -3:] = 'background-color: #1a160b; color: #ffb300;'
            elif '🔴' in kep: styles.iloc[idx, -3:] = 'background-color: #1f0b0d; color: #ff1744;'
        return styles

    # Pagination Logic Radar Matrix
    items_per_page = 10
    total_radar_pages = max(1, len(df_final) // items_per_page + (1 if len(df_final) % items_per_page > 0 else 0))
    start_radar = st.session_state.radar_page * items_per_page
    end_radar = start_radar + items_per_page
    
    df_radar_display = df_final.iloc[start_radar:end_radar]
    st.dataframe(df_radar_display.style.apply(style_tabel_premium, axis=None), use_container_width=True, hide_index=True)
    
    # Tombol Navigasi Radar
    r_col1, r_col2, r_col3 = st.columns([1, 8, 1])
    with r_col1:
        if st.button("⬅️ Previous", key="prev_radar", use_container_width=True, disabled=st.session_state.radar_page == 0):
            st.session_state.radar_page -= 1
            st.rerun()
    with r_col2:
        st.markdown(f"<div style='text-align: center; color: #8a90a6; margin-top: 5px;'>Page {st.session_state.radar_page + 1} of {total_radar_pages}</div>", unsafe_allow_html=True)
    with r_col3:
        if st.button("Next ➡️", key="next_radar", use_container_width=True, disabled=st.session_state.radar_page >= total_radar_pages - 1):
            st.session_state.radar_page += 1
            st.rerun()

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 8. MATRIX EVALUASI (POSISI BAWAH + EXPANDER + PAGINATION)
    # ==========================================
    with st.expander("⚙️ BUKA MATRIX EVALUASI BANDARMOLOGI (Input Data)", expanded=False):
        df_base = pd.DataFrame(st.session_state.raw_stocks)[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]]
        df_base["INTEGRASI BANDARMOLOGI"] = df_base["TICKER"].map(st.session_state.bandar_state)
        
        total_eval_pages = max(1, len(df_base) // items_per_page + (1 if len(df_base) % items_per_page > 0 else 0))
        start_eval = st.session_state.eval_page * items_per_page
        end_eval = start_eval + items_per_page
        df_eval_display = df_base.iloc[start_eval:end_eval]
        
        edited_df = st.data_editor(
            df_eval_display,
            column_config={
                "INTEGRASI BANDARMOLOGI": st.column_config.SelectboxColumn("INTEGRASI BANDARMOLOGI", options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"], required=True),
                "TICKER": st.column_config.Column(disabled=True), "HARGA": st.column_config.Column(disabled=True),
                "PER": st.column_config.Column(disabled=True), "PBV": st.column_config.Column(disabled=True),
                "DIV_YIELD": st.column_config.Column(disabled=True), "RSI": st.column_config.Column(disabled=True),
            },
            hide_index=True, use_container_width=True, key=f"editor_eval_{st.session_state.eval_page}"
        )
        
        # Pengecekan Perubahan State
        state_changed = False
        for idx, row in edited_df.iterrows():
            ticker = row["TICKER"]
            new_val = row["INTEGRASI BANDARMOLOGI"]
            if st.session_state.bandar_state.get(ticker) != new_val:
                st.session_state.bandar_state[ticker] = new_val
                state_changed = True
                
        if state_changed:
            st.rerun()

        # Tombol Navigasi Evaluasi
        e_col1, e_col2, e_col3 = st.columns([1, 8, 1])
        with e_col1:
            if st.button("⬅️ Previous", key="prev_eval", use_container_width=True, disabled=st.session_state.eval_page == 0):
                st.session_state.eval_page -= 1
                st.rerun()
        with e_col2:
            st.markdown(f"<div style='text-align: center; color: #8a90a6; margin-top: 5px;'>Page {st.session_state.eval_page + 1} of {total_eval_pages}</div>", unsafe_allow_html=True)
        with e_col3:
            if st.button("Next ➡️", key="next_eval", use_container_width=True, disabled=st.session_state.eval_page >= total_eval_pages - 1):
                st.session_state.eval_page += 1
                st.rerun()

    st.markdown("---")
    
    # ==========================================
    # 9. ANALISIS KINERJA & HISTORIS DEVIDEND
    # ==========================================
    st.markdown("<h3 style='margin-bottom:10px;'>📑 Analisis Kinerja Finansial & Parameter Dividen</h3>", unsafe_allow_html=True)
    pilihan_emiten = st.selectbox("🎯 Pilih Kode Emiten untuk Evaluasi Mendalam:", options=df_final["TICKER"].tolist())
    
    # [Logika finansial dan fundamental lainnya tetap utuh seperti versi sebelumnya]
    # (Kode disingkat untuk keterbacaan, silakan pertahankan blok "9. Analisis Kinerja" milik Anda yang sudah berfungsi dengan baik)
    if pilihan_emiten:
        st.info(f"Modul finansial lanjutan untuk {pilihan_emiten} aktif (Gunakan skrip fundamental Anda di bagian ini).")
else:
    st.info("💡 Klik tombol 'RE-SCAN MARKET DATA' pada Cyber Panel untuk memuat dashboard utama.")
