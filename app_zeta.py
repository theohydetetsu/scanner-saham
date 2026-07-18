import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import pytz
import warnings
import gc
import json
import os
import plotly.graph_objects as go
import requests

warnings.filterwarnings('ignore')

# ==========================================
# 0. SISTEM CACHE, CONFIG & TRACKING
# ==========================================
CACHE_FILE = "jihan_ghina_saham_cache.json"
CONFIG_FILE = "jihan_ghina_config.json" # File khusus untuk Telegram agar permanen

# Fungsi Auto-Save Telegram Config
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {"tg_token": "", "tg_chat_id": ""}

def save_config(token, chat_id):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"tg_token": token, "tg_chat_id": chat_id}, f)

app_config = load_config()

# State Management
if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks = []
    st.session_state.last_update = None
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                st.session_state.raw_stocks = cache_data.get("raw_stocks", [])
                st.session_state.last_update = cache_data.get("last_update", None)
        except: pass

if "scan_clicked" not in st.session_state: st.session_state.scan_clicked = len(st.session_state.raw_stocks) > 0
if "page_matrix" not in st.session_state: st.session_state.page_matrix = 0
if "current_tf" not in st.session_state: st.session_state.current_tf = "1 Hari (Daily)"

# ==========================================
# 1. KONFIGURASI HALAMAN & UI STYLE (LUXURY)
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA Ultimate v10.5", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -20%, #0f172a, #020617) !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 98% !important; }
    h1 { color: #f8fafc; font-weight: 900; letter-spacing: -1.5px; font-size: 2.4rem !important; margin-bottom: 0; text-shadow: 0 4px 20px rgba(0,242,254,0.15); }
    p { color: #94a3b8; font-weight: 300; }
    
    ::-webkit-scrollbar { width: 6px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(0, 242, 254, 0.4); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0, 242, 254, 1); }
    
    /* MODIFIKASI SIDEBAR COMPACT & LUXURY */
    section[data-testid="stSidebar"] { width: 260px !important; min-width: 260px !important; max-width: 260px !important; background: linear-gradient(180deg, rgba(2,6,23,0.95) 0%, rgba(15,23,42,0.95) 100%) !important; backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.05); }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { font-size: 0.8rem !important; }
    section[data-testid="stSidebar"] label { font-size: 0.75rem !important; font-weight: 700 !important; color: #94a3b8 !important; letter-spacing: 0.5px; }
    
    .premium-card { background: rgba(30, 41, 59, 0.3); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 14px; padding: 18px; box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5); transition: all 0.3s ease; }
    .premium-card:hover { transform: translateY(-3px); box-shadow: 0 15px 35px -5px rgba(0, 242, 254, 0.15); border-color: rgba(0, 242, 254, 0.3); }
    
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 12px 18px !important; background: rgba(15,23,42,0.6); }
    .ihsg-title { color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
    .ihsg-score { color: #00f2fe; font-size: 1.6rem; font-weight: 900; line-height: 1.1; margin: 4px 0; text-shadow: 0 0 15px rgba(0,242,254,0.3); }
    .strat-num { font-size: 2.2rem; font-weight: 900; margin: 2px 0; line-height: 1; text-align: center; }
    .strat-label { font-size: 0.75rem; font-weight: 700; text-align: center; letter-spacing: 1px; color: #cbd5e1; }
    
    div.stButton > button:first-child { background: linear-gradient(90deg, rgba(0,242,254,0.1) 0%, rgba(30,58,138,0.2) 100%) !important; border: 1px solid rgba(0, 242, 254, 0.4) !important; color: #00f2fe !important; border-radius: 8px !important; padding: 10px 15px !important; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
    div.stButton > button:first-child p { color: #00f2fe !important; font-weight: 900 !important; font-size: 0.95rem !important; letter-spacing: 1px; margin: 0; }
    div.stButton > button:first-child:hover { background: linear-gradient(90deg, #00f2fe 0%, #3b82f6 100%) !important; transform: translateY(-2px); box-shadow: 0 10px 20px -5px rgba(0, 242, 254, 0.4); border-color: transparent !important; }
    div.stButton > button:first-child:hover p { color: #020617 !important; text-shadow: none; }
    
    .login-header { text-align: center; color: #00f2fe; font-size: 2.4rem; font-weight: 900; margin-top: 80px; margin-bottom: 5px; letter-spacing: -1px; }
    .stDataFrame { font-size: 13.5px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1.5. SISTEM KEAMANAN (TETAP)
# ==========================================
USERNAME_RAHASIA = "theo"
PASSWORD_RAHASIA = "216455"

if "akses_diberikan" not in st.session_state: st.session_state.akses_diberikan = False

if not st.session_state.akses_diberikan:
    st.markdown("<div class='login-header'>🔒 EXCLUSIVE INTELLIGENCE TERMINAL</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.9rem; margin-bottom: 30px;'>Authorized Personnel Only. Please verify your identity.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        with st.form(key="login_form"):
            user_input = st.text_input("👤 Username:")
            pwd_input = st.text_input("🔑 Password:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("VERIFY & ACCESS TERMINAL", use_container_width=True):
                if user_input.strip().lower() == USERNAME_RAHASIA.lower() and pwd_input.strip() == PASSWORD_RAHASIA:
                    st.session_state.akses_diberikan = True
                    if hasattr(st, 'rerun'): st.rerun()
                    else: st.experimental_rerun()
                else: st.error("❌ Akses Ditolak! Kredensial tidak valid.")
    st.stop()

# ==========================================
# 2. CORE ENGINE & MAPPING SEKTOR
# ==========================================
roster_30_saham = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", "AMRT",
    "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", "CPIN", "ANTM",
    "AMMN", "BREN", "CUAN", "PANI", "BRPT", "MDKA", "MEDC", "ARTO", "SIDO", "MYOR"
]

daftar_saham = [s.strip().upper() + ".JK" for s in roster_30_saham]

sektor_mapping = {
    "BBCA": "Finance", "BBRI": "Finance", "BMRI": "Finance", "BBNI": "Finance", "ARTO": "Finance", "BRIS": "Finance",
    "ICBP": "Consumer", "INDF": "Consumer", "AMRT": "Consumer", "UNVR": "Consumer", "MYOR": "Consumer", "SIDO": "Consumer", "CPIN": "Consumer", "KLBF": "Consumer",
    "UNTR": "Energy & Mining", "PGAS": "Energy & Mining", "PTBA": "Energy & Mining", "ITMG": "Energy & Mining", "ADRO": "Energy & Mining", "ANTM": "Energy & Mining", "AMMN": "Energy & Mining", "MEDC": "Energy & Mining", "MDKA": "Energy & Mining", "CUAN": "Energy & Mining",
    "TLKM": "Tech & Infra", "GOTO": "Tech & Infra", "BREN": "Tech & Infra", "PANI": "Tech & Infra", "BRPT": "Tech & Infra", "ASII": "Tech & Infra"
}

def get_waktu_wib():
    return datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %b %Y - %H:%M:%S WIB")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ihsg_data():
    try:
        df = yf.download("^JKSE", period="1mo", interval="1d", progress=False)
        if df.empty: return None, None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        df = df.ffill() 
        harga_skg = float(df['Close'].iloc[-1])
        harga_lalu = float(df['Close'].iloc[-2])
        perubahan = harga_skg - harga_lalu
        persen = (perubahan / harga_lalu) * 100
        return df, harga_skg, perubahan, persen
    except: return None, None, None, None

def hitung_rsi_akurat(df, periods=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/periods, min_periods=periods).mean()
    loss = (-1 * delta.clip(upper=0)).ewm(alpha=1/periods, min_periods=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def hitung_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    return np.max(ranges, axis=1).rolling(period).mean()

def fetch_single_stock(emiten, mode_tf):
    try:
        # PERBAIKAN TIMEFRAME: Dikalibrasi agar API Yahoo Finance tidak error/blank
        if "1 Jam" in mode_tf: per, inv = "60d", "1h"
        elif "4 Jam" in mode_tf: per, inv = "60d", "1h" # Akan di-resample ke 4h
        elif "1 Minggu" in mode_tf: per, inv = "2y", "1wk"
        else: per, inv = "1y", "1d" # 1 Hari

        kode = emiten.replace(".JK", "")
        df = yf.download(emiten, period=per, interval=inv, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None: df.index = df.index.tz_localize(None)
        
        # Hapus baris yang benar-benar tidak ada transaksi sebelum forward fill
        df = df.dropna(subset=['Close']) 
        
        if "4 Jam" in mode_tf:
            df = df.resample('4h').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna(subset=['Close'])
            
        df = df.ffill() 
        if len(df) < 25: return None # Butuh minimal data untuk indikator panjang
        
        # TEKNIKAL PRESISI TINGGI
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean() # PENAMBAHAN: Detektor Trend Besar
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['RSI'] = hitung_rsi_akurat(df)
        df['ATR'] = hitung_atr(df)
        df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()
        
        harga_skg = float(df['Close'].iloc[-1])
        open_skg = float(df['Open'].iloc[-1])
        ema20_skg = float(df['EMA20'].iloc[-1])
        sma50_skg = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else ema20_skg
        vol_skg = float(df['Volume'].iloc[-1])
        vol_sma20 = float(df['Vol_SMA20'].iloc[-1])
        atr_skg = float(df['ATR'].iloc[-1])
        
        # Penilaian Volatilitas
        volatilitas_pct = (atr_skg / harga_skg) * 100 if harga_skg > 0 else 0
        if volatilitas_pct >= 3.5: volatilitas_stat = "🔥 TINGGI"
        elif volatilitas_pct >= 1.5: volatilitas_stat = "⚡ MODERAT"
        else: volatilitas_stat = "❄️ RENDAH"
        
        # Penilaian Bandarmologi Presisi (Volume Cukup & Candle Hijau)
        is_bullish_candle = harga_skg >= open_skg
        if (vol_skg > (vol_sma20 * 1.2)) and is_bullish_candle and (harga_skg > ema20_skg): 
            status_bandar = "AKUMULASI" 
        elif (vol_skg > (vol_sma20 * 1.2)) and not is_bullish_candle: 
            status_bandar = "DISTRIBUSI" 
        else: 
            status_bandar = "NEUTRAL"
        
        high_history = float(df['High'].tail(20).max())
        low_history = float(df['Low'].tail(20).min())
        
        tkr = yf.Ticker(emiten)
        info = tkr.info if tkr.info else {}
        per_val = info.get('trailingPE', 0.0)
        pbv_val = info.get('priceToBook', 1.0)
        div_rate = info.get('trailingAnnualDividendRate', 0)
        div_yield = (div_rate / harga_skg * 100) if (div_rate and harga_skg > 0) else 0.0
            
        return {
            "TICKER": kode, "HARGA": harga_skg, 
            "AREA BELI": ema20_skg if harga_skg > ema20_skg else (low_history + (harga_skg - low_history)*0.3), 
            "TARGET (TP)": harga_skg * 1.05 if high_history <= harga_skg else high_history,
            "STOP LOSS": harga_skg * 0.96 if low_history >= harga_skg else low_history,
            "VOLATILITAS": volatilitas_stat, "RSI": round(float(df['RSI'].iloc[-1]), 2),
            "STATUS_BANDAR": status_bandar,
            "UP_EMA20": harga_skg > ema20_skg, 
            "UP_SMA50": harga_skg > sma50_skg, # Data Trend Menengah
            "MACD_GOLDEN": float(df['MACD'].iloc[-1]) > float(df['Signal'].iloc[-1]),
            "PER": round(per_val, 2), "PBV": round(pbv_val, 2), "DIV_YIELD": round(div_yield, 2),
            "SEKTOR": sektor_mapping.get(kode, "Others")
        }
    except Exception as e: 
        return None

def format_rupiah(val):
    if pd.isna(val) or val == 0: return "-"
    return f"Rp {val:,.0f}".replace(",", ".")

# ==========================================
# 3. CHART & ANALYST DATA FETCHING (TETAP)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financial_charts(ticker_symbol):
    tkr = yf.Ticker(ticker_symbol + ".JK")
    df_inc, df_bs, df_cf = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    PEMBAGI = 1_000_000_000_000 
    try:
        inc = tkr.quarterly_financials
        if not inc.empty:
            rev = (inc.loc['Total Revenue'] / PEMBAGI) if 'Total Revenue' in inc.index else pd.Series(dtype=float)
            ni = (inc.loc['Net Income'] / PEMBAGI) if 'Net Income' in inc.index else pd.Series(dtype=float)
            df_inc = pd.DataFrame({'Revenue': rev, 'Net Income': ni}).dropna(how='all')
            df_inc.index = pd.to_datetime(df_inc.index).strftime('%b %Y')
            df_inc = df_inc.iloc[::-1] 
    except: pass
    try:
        bs = tkr.quarterly_balance_sheet
        if not bs.empty:
            assets = (bs.loc['Total Assets'] / PEMBAGI) if 'Total Assets' in bs.index else pd.Series(dtype=float)
            liab = (bs.loc['Total Liabilities Net Minority Interest'] / PEMBAGI) if 'Total Liabilities Net Minority Interest' in bs.index else (bs.loc['Total Liabilities'] / PEMBAGI if 'Total Liabilities' in bs.index else pd.Series(dtype=float))
            df_bs = pd.DataFrame({'Total Assets': assets, 'Total Liabilities': liab}).dropna(how='all')
            df_bs.index = pd.to_datetime(df_bs.index).strftime('%b %Y')
            df_bs = df_bs.iloc[::-1]
    except: pass
    try:
        cf = tkr.quarterly_cashflow
        if not cf.empty:
            ocf = (cf.loc['Operating Cash Flow'] / PEMBAGI) if 'Operating Cash Flow' in cf.index else pd.Series(dtype=float)
            fcf = (cf.loc['Free Cash Flow'] / PEMBAGI) if 'Free Cash Flow' in cf.index else pd.Series(dtype=float)
            df_cf = pd.DataFrame({'Operating Cash': ocf, 'Free Cash Flow': fcf}).dropna(how='all')
            df_cf.index = pd.to_datetime(df_cf.index).strftime('%b %Y')
            df_cf = df_cf.iloc[::-1]
    except: pass
    return df_inc, df_bs, df_cf

def create_locked_plotly_chart(df, color1, color2):
    fig = go.Figure()
    if not df.empty and len(df.columns) >= 2:
        col1, col2 = df.columns[0], df.columns[1]
        fig.add_trace(go.Bar(x=df.index, y=df[col1], name=col1, marker_color=color1))
        fig.add_trace(go.Bar(x=df.index, y=df[col2], name=col2, marker_color=color2))
    fig.update_layout(
        barmode='group', height=250, margin=dict(l=10, r=10, t=10, b=10), 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, font=dict(size=10)),
        dragmode=False, hovermode='x unified'
    )
    fig.update_xaxes(fixedrange=True, showgrid=False)
    fig.update_yaxes(fixedrange=True, gridcolor='rgba(255,255,255,0.05)')
    return fig

def analyze_financial_health(df_inc, df_bs, df_cf):
    score = 0
    indikator = []
    if not df_inc.empty and len(df_inc) >= 1:
        latest_ni = df_inc['Net Income'].iloc[-1]
        if latest_ni > 0:
            score += 25
            indikator.append("✔️ Laba Bersih Positif (QoQ)")
        if len(df_inc) >= 2:
            prev_ni = df_inc['Net Income'].iloc[-2]
            if latest_ni > prev_ni:
                score += 15
                indikator.append("✔️ Laba Bertumbuh Kuartal Ini")
    if not df_bs.empty and len(df_bs) >= 1:
        assets = df_bs['Total Assets'].iloc[-1]
        liab = df_bs['Total Liabilities'].iloc[-1]
        if assets > liab:
            score += 20
            indikator.append("✔️ Ekuitas Kuat (Aset > Hutang)")
        if assets > (liab * 1.5):
            score += 10
            indikator.append("✔️ Rasio Hutang Sangat Rendah")
    if not df_cf.empty and len(df_cf) >= 1:
        ocf = df_cf['Operating Cash'].iloc[-1]
        if ocf > 0:
            score += 20
            indikator.append("✔️ Arus Kas Operasi Positif")
    if score >= 80: return "🚀 POTENSI BAGGER (SANGAT SEHAT)", "#10b981", indikator
    elif score >= 60: return "🟢 SEHAT & BAGUS", "#00f2fe", indikator
    elif score >= 40: return "🟡 STABIL / MODERAT", "#fbbf24", indikator
    else: return "🔴 BERISIKO / KURANG SEHAT", "#f43f5e", indikator

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_analyst_consensus(ticker_symbol):
    data = {"Konsensus": "N/A", "Target Bawah": "-", "Target Rata-Rata": "-", "Target Atas": "-"}
    try:
        info = yf.Ticker(ticker_symbol + ".JK").info
        rec = info.get('recommendationKey', 'none').replace('_', ' ').title()
        if rec and rec.lower() != 'none': data["Konsensus"] = rec
        if info.get('targetLowPrice'): data["Target Bawah"] = format_rupiah(info['targetLowPrice'])
        if info.get('targetMeanPrice'): data["Target Rata-Rata"] = format_rupiah(info['targetMeanPrice'])
        if info.get('targetHighPrice'): data["Target Atas"] = format_rupiah(info['targetHighPrice'])
    except: pass
    return data

# ==========================================
# 4. SIDEBAR (ULTIMATE RADAR CONTROL)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #00f2fe; font-size: 1.25rem; font-weight: 900; margin-bottom: 0px;'>💎 JIHAN-GHINA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.65rem; letter-spacing: 1.5px; margin-bottom: 25px;'>ULTIMATE PRO v10.5</p>", unsafe_allow_html=True)
    
    tf_pilihan = st.selectbox("⏱️ Timeframe Analisis:", ["1 Jam", "4 Jam", "1 Hari (Daily)", "1 Minggu (Weekly)"], index=2)
    tf_berubah = tf_pilihan != st.session_state.current_tf
    if tf_berubah: st.session_state.current_tf = tf_pilihan
        
    profil_risiko = st.selectbox("🎯 Profil Risiko:", ["Moderat", "Agresif", "Konservatif"])
    
    st.markdown("<div style='font-size:0.7rem; color:#00f2fe; font-weight:800; letter-spacing:1px; margin-top:20px; border-bottom: 1px solid rgba(0,242,254,0.2); padding-bottom: 5px;'>⚙️ POSITION SIZING ENGINE</div>", unsafe_allow_html=True)
    modal_trading = st.number_input("💰 Modal Trading (Rp):", min_value=1_000_000, value=50_000_000, step=1_000_000)
    risiko_pct = st.slider("🚨 Batas Risiko /Trade (%):", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
    
    # TELEGRAM ENGINE (AUTO-SAVE)
    with st.expander("🤖 Telegram Automation Alert"):
        st.markdown("<p style='font-size: 0.7rem; color: #10b981;'>Data otomatis tersimpan secara permanen.</p>", unsafe_allow_html=True)
        # Ambil value dari config file
        new_token = st.text_input("Bot Token:", value=app_config["tg_token"], type="password")
        new_chat_id = st.text_input("Chat ID:", value=app_config["tg_chat_id"])
        
        # Logika simpan otomatis jika ada perubahan ketikan
        if new_token != app_config["tg_token"] or new_chat_id != app_config["tg_chat_id"]:
            save_config(new_token, new_chat_id)
            app_config["tg_token"] = new_token
            app_config["tg_chat_id"] = new_chat_id

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔄 EXECUTE SCANNER", use_container_width=True) or tf_berubah:
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.page_matrix = 0 
        st.session_state.raw_stocks = []
        
        my_bar = st.progress(0, text=f"Initializing Terminal Radar ({st.session_state.current_tf})...")
        
        for i, t in enumerate(daftar_saham):
            my_bar.progress((i + 1) / len(daftar_saham), text=f"Analyzing {t} ({i+1}/{len(daftar_saham)})")
            data = fetch_single_stock(t, st.session_state.current_tf)
            if data: st.session_state.raw_stocks.append(data)
            gc.collect() 
            
        my_bar.empty()
        st.session_state.last_update = get_waktu_wib()
        
        # LOGIKA PENGIRIMAN TELEGRAM OTOMATIS (Menggunakan config tersimpan)
        token_aktif = app_config["tg_token"]
        chat_aktif = app_config["tg_chat_id"]
        
        if token_aktif and chat_aktif and len(st.session_state.raw_stocks) > 0:
            alert_text = f"🤖 *JIHAN-GHINA ALERTS* | {st.session_state.current_tf}\n\n"
            has_buys = False
            for raw in st.session_state.raw_stocks:
                # Skoring Ketat v10.5
                skor = 0
                if raw["UP_EMA20"]: skor += 10
                if raw.get("UP_SMA50", False): skor += 10 # Cek Trend Menengah
                if raw["MACD_GOLDEN"]: skor += 15
                if raw["RSI"] < 40: skor += 15
                elif 40 <= raw["RSI"] <= 65: skor += 10
                elif raw["RSI"] > 70: skor -= 15
                
                if raw["STATUS_BANDAR"] == "AKUMULASI": skor += 25
                elif raw["STATUS_BANDAR"] == "DISTRIBUSI": skor -= 20
                else: skor += 5
                
                if 0 < raw["PER"] < 15: skor += 10
                if 0 < raw["PBV"] < 2: skor += 10
                if raw["DIV_YIELD"] > 3: skor += 5
                
                target_skor = 65 if profil_risiko == "Agresif" else (78 if profil_risiko == "Konservatif" else 72)
                kep = "ACCUMULATE" if skor >= target_skor else ("HOLD" if skor >= 50 else "LIQUIDATE")
                
                if raw["VOLATILITAS"] == "🔥 TINGGI" and raw["STATUS_BANDAR"] == "DISTRIBUSI": kep = "LIQUIDATE"  
                elif raw["VOLATILITAS"] == "❄️ RENDAH" and kep == "ACCUMULATE": kep = "HOLD"
                
                if kep == "ACCUMULATE":
                    has_buys = True
                    alert_text += f"✅ *{raw['TICKER']}* | Hrg: Rp{int(raw['HARGA']):,} | TP: Rp{int(raw['TARGET (TP)']):,} | Bndr: {raw['STATUS_BANDAR']}\n"
            
            if has_buys:
                try:
                    requests.post(f"https://api.telegram.org/bot{token_aktif}/sendMessage", json={"chat_id": chat_aktif, "text": alert_text, "parse_mode": "Markdown"})
                except: pass

        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"raw_stocks": st.session_state.raw_stocks, "last_update": st.session_state.last_update}, f)
        except: pass
        
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.akses_diberikan = False
        st.session_state.scan_clicked = False
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()

# ==========================================
# 5. HEADER DASHBOARD
# ==========================================
st.markdown("<h1>🌐 Algorithmic Market Intelligence</h1>", unsafe_allow_html=True)

col_h1, col_h2 = st.columns([3.5, 1.5])
with col_h1:
    upd_time = st.session_state.last_update if st.session_state.last_update else "Menunggu inisiasi radar..."
    st.markdown(f"<p style='font-size: 0.95rem; margin-top:5px;'>🕒 Last Market Sync: <strong style='color:#00f2fe;'>{upd_time}</strong><br>Terminal Engine v10.5 Pro: Precision Technicals, Quarter Fundamentals, Volume-Price Analysis, Dynamic Position Sizing.</p>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()
with col_h2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_garis = '#10b981' if ihsg_chg >= 0 else '#f43f5e'
        st.markdown(f"""
        <div class="premium-card ihsg-box" style="border-left: 5px solid {warna_garis};">
            <span class="ihsg-title">IHSG COMPOSITE</span>
            <span class="ihsg-score">{ihsg_now:,.2f}</span>
            <span style="color: {warna_garis}; font-weight: 800; font-size: 0.95rem;">{warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

if not st.session_state.scan_clicked or not st.session_state.raw_stocks:
    st.info("👈 Sistem terminal siaga. Silakan tekan tombol '🔄 EXECUTE SCANNER' di panel navigasi kiri.")
else:
    # ------------------------------------------
    # FITUR 10.5: SECTORAL HEAT RADAR MATRIX 
    # ------------------------------------------
    st.markdown("<h3 style='font-size: 1.5rem;'>📊 Sectoral Heat Flow Matrix</h3>", unsafe_allow_html=True)
    
    sektor_counts = {"Finance": 0, "Consumer": 0, "Energy & Mining": 0, "Tech & Infra": 0}
    sektor_accum = {"Finance": 0, "Consumer": 0, "Energy & Mining": 0, "Tech & Infra": 0}
    sektor_tickers_accum = {"Finance": [], "Consumer": [], "Energy & Mining": [], "Tech & Infra": []}
    
    hasil_rekomendasi = []
    for raw in st.session_state.raw_stocks:
        # Perhitungan Skor Presisi
        skor = 0
        if raw["UP_EMA20"]: skor += 10
        if raw.get("UP_SMA50", False): skor += 10 # Penilaian Trend Major
        if raw["MACD_GOLDEN"]: skor += 15
        if raw["RSI"] < 40: skor += 15
        elif 40 <= raw["RSI"] <= 65: skor += 10
        elif raw["RSI"] > 70: skor -= 15
        
        if raw["STATUS_BANDAR"] == "AKUMULASI": skor += 25
        elif raw["STATUS_BANDAR"] == "DISTRIBUSI": skor -= 20
        else: skor += 5
        
        if 0 < raw["PER"] < 15: skor += 10
        if 0 < raw["PBV"] < 2: skor += 10
        if raw["DIV_YIELD"] > 3: skor += 5
        
        skor = max(0, min(100, skor))
        target_skor = 65 if profil_risiko == "Agresif" else (78 if profil_risiko == "Konservatif" else 72)
        
        if skor >= target_skor: kep = "🟢 ACCUMULATE"
        elif skor >= 50: kep = "🟡 HOLD"
        else: kep = "🔴 LIQUIDATE"
        
        if raw["VOLATILITAS"] == "🔥 TINGGI" and raw["STATUS_BANDAR"] == "DISTRIBUSI": kep = "🔴 LIQUIDATE"  
        elif raw["VOLATILITAS"] == "❄️ RENDAH" and kep == "🟢 ACCUMULATE": kep = "🟡 HOLD"       
        
        sec_name = raw.get("SEKTOR", "Others")
        if sec_name in sektor_counts:
            sektor_counts[sec_name] += 1
            if kep == "🟢 ACCUMULATE": 
                sektor_accum[sec_name] += 1
                sektor_tickers_accum[sec_name].append(raw["TICKER"])
            
        max_loss_money = modal_trading * (risiko_pct / 100)
        risk_per_share = raw["HARGA"] - raw["STOP LOSS"]
        if "ACCUMULATE" in kep and risk_per_share > 0:
            max_shares = max_loss_money / risk_per_share
            max_lots = int(max_shares / 100)
            rec_lot_text = f"🔥 Max {max_lots:,} Lot" if max_lots > 0 else "Beli Minimal"
        else:
            rec_lot_text = "🔒 Proteksi/Hold"
            
        hasil_rekomendasi.append({
            "TICKER": raw["TICKER"], 
            "HARGA": f"{int(raw['HARGA']):,}".replace(",", "."),
            "AREA BELI": f"{int(raw['AREA BELI']):,}".replace(",", "."),
            "TARGET (TP)": f"{int(raw['TARGET (TP)']):,}".replace(",", "."),
            "STOP LOSS": f"{int(raw['STOP LOSS']):,}".replace(",", "."),
            "REKOMENDASI LOT": rec_lot_text,
            "VOLATILITAS": raw["VOLATILITAS"],
            "RSI": f"{raw['RSI']:.2f}", 
            "BANDARMOLOGI": raw["STATUS_BANDAR"], 
            "REKOMENDASI": kep
        })
        
    sec_col1, sec_col2, sec_col3, sec_col4 = st.columns(4)
    
    t_fin = ", ".join(sektor_tickers_accum["Finance"]) if sektor_tickers_accum["Finance"] else "N/A"
    t_cons = ", ".join(sektor_tickers_accum["Consumer"]) if sektor_tickers_accum["Consumer"] else "N/A"
    t_eng = ", ".join(sektor_tickers_accum["Energy & Mining"]) if sektor_tickers_accum["Energy & Mining"] else "N/A"
    t_tech = ", ".join(sektor_tickers_accum["Tech & Infra"]) if sektor_tickers_accum["Tech & Infra"] else "N/A"

    with sec_col1: st.markdown(f"<div class='premium-card' style='border-top: 4px solid #3b82f6;'><div class='strat-label'>🏦 FINANCE SECTOR</div><div class='strat-num' style='color:#3b82f6;'>{sektor_accum['Finance']}/{sektor_counts['Finance']}</div><div style='font-size:0.7rem; color:#94a3b8; text-align:center; margin-top:5px;'>Active Bull: <strong style='color:#f8fafc;'>{t_fin}</strong></div></div>", unsafe_allow_html=True)
    with sec_col2: st.markdown(f"<div class='premium-card' style='border-top: 4px solid #10b981;'><div class='strat-label'>🛒 CONSUMER GOODS</div><div class='strat-num' style='color:#10b981;'>{sektor_accum['Consumer']}/{sektor_counts['Consumer']}</div><div style='font-size:0.7rem; color:#94a3b8; text-align:center; margin-top:5px;'>Active Bull: <strong style='color:#f8fafc;'>{t_cons}</strong></div></div>", unsafe_allow_html=True)
    with sec_col3: st.markdown(f"<div class='premium-card' style='border-top: 4px solid #f59e0b;'><div class='strat-label'>⚡ ENERGY & MINING</div><div class='strat-num' style='color:#f59e0b;'>{sektor_accum['Energy & Mining']}/{sektor_counts['Energy & Mining']}</div><div style='font-size:0.7rem; color:#94a3b8; text-align:center; margin-top:5px;'>Active Bull: <strong style='color:#f8fafc;'>{t_eng}</strong></div></div>", unsafe_allow_html=True)
    with sec_col4: st.markdown(f"<div class='premium-card' style='border-top: 4px solid #8b5cf6;'><div class='strat-label'>🌐 TECH & INFRA</div><div class='strat-num' style='color:#8b5cf6;'>{sektor_accum['Tech & Infra']}/{sektor_counts['Tech & Infra']}</div><div style='font-size:0.7rem; color:#94a3b8; text-align:center; margin-top:5px;'>Active Bull: <strong style='color:#f8fafc;'>{t_tech}</strong></div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h3 style='font-size: 1.5rem;'>🛰️ Pro Max Signal Data Matrix</h3>", unsafe_allow_html=True)
    
    df_final = pd.DataFrame(hasil_rekomendasi)
    df_final = df_final.sort_values(by="TICKER").reset_index(drop=True)
    
    def style_tabel(row):
        styles = []
        if '🟢' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(16, 185, 129, 0.12); color: #34d399;'
        elif '🟡' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(245, 158, 11, 0.12); color: #fbbf24;'
        else: bg_rek = 'background-color: rgba(244, 63, 94, 0.12); color: #fb7185;'
        
        for c, val in row.items():
            if c == 'TICKER': 
                styles.append('font-weight: 900; font-size: 1.15rem; color: #00f2fe; text-shadow: 0px 0px 10px rgba(0,242,254,0.3); text-align:center;')
            elif c == 'TARGET (TP)': styles.append('color: #10b981; font-weight: 800;') 
            elif c == 'STOP LOSS': styles.append('color: #f43f5e; font-weight: 800;')  
            elif c == 'AREA BELI': styles.append('color: #38bdf8; font-weight: 800;')  
            elif c == 'REKOMENDASI LOT':
                if 'Max' in str(val): styles.append('color: #facc15; font-weight: 900; background-color: rgba(250,204,21,0.08);')
                else: styles.append('color: #64748b; font-weight: 400;')
            elif c in ['BANDARMOLOGI', 'REKOMENDASI']: styles.append(bg_rek)
            elif c == 'VOLATILITAS':
                if '🔥' in str(val): styles.append('color: #f43f5e; font-weight: 800;')
                elif '⚡' in str(val): styles.append('color: #fbbf24; font-weight: 800;')
                else: styles.append('color: #38bdf8; font-weight: 800;')
            elif c == 'RSI':
                try:
                    rsi_val = float(val)
                    if rsi_val > 65: styles.append('color: #f43f5e; font-weight: 800;') 
                    elif rsi_val < 40: styles.append('color: #10b981; font-weight: 800;') 
                    else: styles.append('')
                except: styles.append('')
            else: styles.append('')
        return styles

    ITEMS_PER_PAGE = 10
    total_pages = len(df_final) // ITEMS_PER_PAGE + (1 if len(df_final) % ITEMS_PER_PAGE > 0 else 0)
    if total_pages == 0: total_pages = 1
    
    start_idx = st.session_state.page_matrix * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    df_tampil = df_final.iloc[start_idx:end_idx]
    
    st.dataframe(df_tampil.style.apply(style_tabel, axis=1), use_container_width=True, hide_index=True)
    
    col_space1, col_prev, col_page, col_next, col_space2 = st.columns([3, 1, 2, 1, 3])
    with col_prev:
        if st.button("⬅️ Prev Data", use_container_width=True, disabled=(st.session_state.page_matrix == 0)):
            st.session_state.page_matrix -= 1
            if hasattr(st, 'rerun'): st.rerun()
            else: st.experimental_rerun()
    with col_page:
        st.markdown(f"<p style='text-align: center; font-size:0.75rem; color:#94a3b8; margin-top:8px;'>Halaman {st.session_state.page_matrix + 1} / {total_pages}</p>", unsafe_allow_html=True)
    with col_next:
        if st.button("Next Data ➡️", use_container_width=True, disabled=(st.session_state.page_matrix >= total_pages - 1)):
            st.session_state.page_matrix += 1
            if hasattr(st, 'rerun'): st.rerun()
            else: st.experimental_rerun()

    # ==========================================
    # 5.5. MODUL MASTERPIECE SIGNAL TRADING
    # ==========================================
    st.markdown("---")
    st.markdown("<h3 style='font-size: 1.5rem;'>🎯 Executive Cross-Validation</h3>", unsafe_allow_html=True)
    
    scanned_tickers = df_final['TICKER'].tolist()
    emiten_signal = None 
    
    if scanned_tickers:
        emiten_signal = st.selectbox("⚡ Pilih Target Emiten (Algo vs Analyst):", scanned_tickers, key="signal_select")
        
        with st.spinner(f"Mengkalkulasi Konfirmasi Ganda untuk {emiten_signal}..."):
            sys_rec_raw = df_final[df_final['TICKER'] == emiten_signal]['REKOMENDASI'].values[0]
            vol_target = df_final[df_final['TICKER'] == emiten_signal]['VOLATILITAS'].values[0]
            bandar_target = df_final[df_final['TICKER'] == emiten_signal]['BANDARMOLOGI'].values[0]
            lot_rec_target = df_final[df_final['TICKER'] == emiten_signal]['REKOMENDASI LOT'].values[0]
            
            analyst_data_signal = fetch_analyst_consensus(emiten_signal)
            konsensus_raw = analyst_data_signal["Konsensus"].upper()
            
            sys_is_buy = "ACCUMULATE" in sys_rec_raw
            sys_is_sell = "LIQUIDATE" in sys_rec_raw
            sys_is_hold = "HOLD" in sys_rec_raw
            
            ana_is_buy = any(x in konsensus_raw for x in ["BUY", "OUTPERFORM", "OVERWEIGHT"])
            ana_is_sell = any(x in konsensus_raw for x in ["SELL", "UNDERPERFORM", "UNDERWEIGHT"])
            ana_is_hold = "HOLD" in konsensus_raw or "NEUTRAL" in konsensus_raw
            
            is_trap = "🔥 TINGGI" in vol_target and "DISTRIBUSI" in bandar_target
            is_sleeping = "❄️ RENDAH" in vol_target
            
            if is_trap:
                final_decision = "🚨 CRITICAL WARNING (BULL TRAP FILTERED)"
                color = "#f43f5e"
                desc = "PROTEKSI DIALIRKAN: Saham mengalami volatilitas tinggi dengan distribusi bandar masif. Sistem memblokir sinyal beli demi keselamatan portfolio."
            elif sys_is_buy and ana_is_buy:
                final_decision = "🚀 STRONG BUY (DOUBLE CONFIRMED)"
                color = "#10b981"
                desc = "Sistem Kuantitatif dan Analis Global SEPAKAT. Saham berada dalam zona akumulasi dengan probabilitas kemenangan tinggi."
            elif sys_is_sell and ana_is_sell:
                final_decision = "🩸 STRONG SELL (DOUBLE CONFIRMED)"
                color = "#f43f5e"
                desc = "Sistem Kuantitatif dan Analis Global SEPAKAT. Risiko koreksi tinggi, segera lakukan proteksi likuiditas."
            elif sys_is_buy and not ana_is_buy:
                final_decision = "🟢 CAUTIOUS BUY (ALGO-DRIVEN)"
                color = "#34d399"
                desc = "Bandarmologi dan Teknikal mendeteksi pergerakan beli, namun Analis belum menaikkan rating. Akumulasi bertahap (Cicil Beli)."
            elif sys_is_sell and not ana_is_sell:
                final_decision = "🟠 CAUTIOUS SELL (ALGO-DRIVEN)"
                color = "#fb923c"
                desc = "Mesin mendeteksi pelemahan tren & distribusi bandar, meskipun Analis masih optimis. Pasang Trailing Stop ketat."
            elif sys_is_hold and ana_is_hold:
                final_decision = "⚖️ SOLID HOLD"
                color = "#fbbf24"
                desc = "Konsolidasi market. Tidak ada tekanan jual/beli signifikan. Tahan posisi (Hold)."
            else:
                final_decision = "🔍 MIXED SIGNAL (MONITOR)"
                color = "#a855f7"
                desc = "Terdapat deviasi antara data algoritma dan konsensus analis. Disarankan memantau ketat pergerakan harga."

            if is_sleeping and "HOLD" in sys_rec_raw:
                desc += " (Sistem mengunci di posisi HOLD karena volatilitas RENDAH/saham sedang 'tidur')."

            if "1 Jam" in st.session_state.current_tf or "4 Jam" in st.session_state.current_tf:
                durasi_valid = "⏳ 1 - 3 Hari Bursa (Short-Term Trade)"
            elif "1 Hari" in st.session_state.current_tf:
                durasi_valid = "⏳ 1 - 3 Minggu (Medium-Term Swing)"
            else:
                durasi_valid = "⏳ 1 - 3 Bulan (Long-Term Trend)"
                
            st.markdown(f"""
            <div class='premium-card' style='border-left: 5px solid {color}; margin-top: 10px; margin-bottom: 25px;'>
                <div style='display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;'>
                    <div style='flex: 1; min-width: 150px; text-align: center; border-right: 1px solid rgba(255,255,255,0.1);'>
                        <span style='color: #94a3b8; font-size: 0.75rem; letter-spacing: 1px; font-weight:700;'>💻 JIHAN-GHINA ALGO</span><br>
                        <span style='font-weight: 900; font-size: 1.15rem; color: #f8fafc;'>{sys_rec_raw}</span>
                    </div>
                    <div style='flex: 1; min-width: 150px; text-align: center;'>
                        <span style='color: #94a3b8; font-size: 0.75rem; letter-spacing: 1px; font-weight:700;'>🌍 GLOBAL ANALYST</span><br>
                        <span style='font-weight: 900; font-size: 1.15rem; color: #f8fafc;'>{konsensus_raw if konsensus_raw != 'N/A' else 'DATA UNAVAILABLE'}</span>
                    </div>
                </div>
                <div style='margin-top: 18px; text-align: center; background: rgba(0,0,0,0.3); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.02);'>
                    <span style='color: #94a3b8; font-size: 0.75rem; letter-spacing: 2px; font-weight:700;'>🏆 ULTIMATE FINAL DECISION</span><br>
                    <span style='color: {color}; font-weight: 900; font-size: 1.5rem; display: block; margin: 8px 0; letter-spacing: -0.5px;'>{final_decision}</span>
                    <span style='color: #cbd5e1; font-size: 0.85rem; margin-bottom: 12px; display: block; font-weight: 300;'>{desc}</span>
                    <div style='display:flex; justify-content:center; gap:15px; flex-wrap:wrap; margin-top: 15px;'>
                        <span style='background: rgba(0,242,254,0.1); border: 1px solid rgba(0,242,254,0.3); padding: 8px 15px; border-radius: 8px; color: #00f2fe; font-size: 0.8rem; font-weight: 800;'>🎯 SIZING: {lot_rec_target}</span>
                        <span style='background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 8px 15px; border-radius: 8px; color: #facc15; font-size: 0.8rem; font-weight: 800;'>{durasi_valid}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # 6. MODUL VISUAL CHART KEUANGAN & HEALTH
    # ==========================================
    if emiten_signal: 
        st.markdown("---")
        st.markdown(f"<h3 style='font-size: 1.5rem;'>📊 Quarterly Financial Matrix : {emiten_signal}</h3>", unsafe_allow_html=True)
        
        with st.spinner(f"Sinkronisasi Data Finansial (QoQ) {emiten_signal}..."):
            
            analyst_data = fetch_analyst_consensus(emiten_signal)
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom: 20px;'>
                <div class='premium-card' style='flex:1; min-width:140px; text-align:center; padding:15px; border-left: 4px solid #00f2fe;'>
                    <div style='font-size:0.7rem; color:#94a3b8; font-weight:700; letter-spacing:1px;'>💡 CONSENSUS</div>
                    <div style='font-size:1.1rem; font-weight:900; color:#00f2fe; margin-top:5px;'>{analyst_data["Konsensus"]}</div>
                </div>
                <div class='premium-card' style='flex:1; min-width:140px; text-align:center; padding:15px; border-left: 4px solid #f43f5e;'>
                    <div style='font-size:0.7rem; color:#94a3b8; font-weight:700; letter-spacing:1px;'>📉 LOW TARGET</div>
                    <div style='font-size:1.1rem; font-weight:900; color:#f43f5e; margin-top:5px;'>{analyst_data["Target Bawah"]}</div>
                </div>
                <div class='premium-card' style='flex:1; min-width:140px; text-align:center; padding:15px; border-left: 4px solid #f8fafc;'>
                    <div style='font-size:0.7rem; color:#94a3b8; font-weight:700; letter-spacing:1px;'>🎯 MEAN TARGET</div>
                    <div style='font-size:1.1rem; font-weight:900; color:#f8fafc; margin-top:5px;'>{analyst_data["Target Rata-Rata"]}</div>
                </div>
                <div class='premium-card' style='flex:1; min-width:140px; text-align:center; padding:15px; border-left: 4px solid #10b981;'>
                    <div style='font-size:0.7rem; color:#94a3b8; font-weight:700; letter-spacing:1px;'>📈 HIGH TARGET</div>
                    <div style='font-size:1.1rem; font-weight:900; color:#10b981; margin-top:5px;'>{analyst_data["Target Atas"]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            df_inc, df_bs, df_cf = fetch_financial_charts(emiten_signal)
            
            status_text, color_hex, reason_list = analyze_financial_health(df_inc, df_bs, df_cf)
            reasons_html = "".join([f"<li style='margin-bottom: 4px;'>{r}</li>" for r in reason_list])
            
            st.markdown(f"""
            <div class='premium-card' style='margin-bottom: 25px; border-left: 4px solid {color_hex};'>
                <h4 style='color: #f8fafc; margin-top: 0; margin-bottom: 10px; font-size: 1.1rem; font-weight:800;'>💠 Company Health Grade: <span style='color: {color_hex};'>{status_text}</span></h4>
                <p style='color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px;'>Algoritma Skor Berdasarkan Laporan Keuangan Kuartal Terakhir:</p>
                <ul style='color: #cbd5e1; font-size: 0.8rem; padding-left: 20px; margin: 0;'>
                    {reasons_html if reason_list else "<li>Menunggu rilis data keuangan kuartal terbaru dari bursa.</li>"}
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            lock_config = {'displayModeBar': False, 'scrollZoom': False}
            
            with c1:
                st.markdown("<h5 style='color: #00f2fe; text-align:center; font-size: 0.9rem; font-weight:700; margin-bottom: 5px;'>📈 Income Statement</h5>", unsafe_allow_html=True)
                if not df_inc.empty:
                    fig1 = create_locked_plotly_chart(df_inc, "#00f2fe", "#10b981")
                    st.plotly_chart(fig1, use_container_width=True, config=lock_config)
                else: st.warning("No Data")
                
            with c2:
                st.markdown("<h5 style='color: #3b82f6; text-align:center; font-size: 0.9rem; font-weight:700; margin-bottom: 5px;'>⚖️ Balance Sheet</h5>", unsafe_allow_html=True)
                if not df_bs.empty:
                    fig2 = create_locked_plotly_chart(df_bs, "#3b82f6", "#f43f5e")
                    st.plotly_chart(fig2, use_container_width=True, config=lock_config)
                else: st.warning("No Data")
                
            with c3:
                st.markdown("<h5 style='color: #8b5cf6; text-align:center; font-size: 0.9rem; font-weight:700; margin-bottom: 5px;'>💵 Cash Flow</h5>", unsafe_allow_html=True)
                if not df_cf.empty:
                    fig3 = create_locked_plotly_chart(df_cf, "#8b5cf6", "#f59e0b")
                    st.plotly_chart(fig3, use_container_width=True, config=lock_config)
                else: st.warning("No Data")

    # ==========================================
    # 7. FITUR 10.5: TERMINAL ACADEMY
    # ==========================================
    st.markdown("---")
    st.markdown("<h3 style='font-size: 1.5rem; text-align: center;'>📚 Jihan-Ghina Academy & User Guide</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;'>Panduan analitika level institusi di dalam terminal.</p>", unsafe_allow_html=True)

    with st.expander("📖 1. Analitika Teknikal (Trend & Momentum)"):
        st.markdown("""
        **Penyempurnaan V10.5:**
        *   **SMA50 & EMA20 (Double Trend Check):** Mesin kini mengecek apakah tren menengah (50-hari) mendukung tren pendek (20-hari). Ini sangat meminimalisir risiko tersangkut saat *downtrend* besar.
        *   **MACD Golden Cross:** Detektor letupan harga awal sebelum banyak orang sadar.
        *   **RSI Dinamis:** RSI disetel di bawah angka 40 untuk mencari momentum diskon optimal, dan menghindari RSI di atas 70 (Overbought).
        """)

    with st.expander("📖 2. Bandarmologi V2 & Volatility Lock"):
        st.markdown("""
        **Proteksi Cerdas Algoritma:**
        *   **Candle Assessment:** Mesin tidak hanya melihat volume besar, namun mengecek letak penutupan harga (Close vs Open). Jika volume besar tapi harga ditekan turun = **DISTRIBUSI**.
        *   **Bull Trap Filter:** Jika volatilitas sangat tinggi (liar) dan Bandar terdeteksi jualan, mesin mem-veto sinyal beli menjadi 🔴 `LIQUIDATE`.
        *   **Sleeping Stock Lock:** Jika saham kurang likuid/volatilitas rendah, sinyal akan tertahan di 🟡 `HOLD` agar dana Anda tidak mati.
        """)

    with st.expander("📖 3. Position Sizing (Manajemen Risiko Kuantitatif)"):
        st.markdown("""
        **Cara Mengamankan Psikologi Trading:**
        1. Isi modal asli Anda di kiri.
        2. Set toleransi rugi di `1.0%` (Sangat disarankan).
        3. Kolom **REKOMENDASI LOT** akan menghitung berapa lembar persisnya yang boleh Anda beli berdasarkan jarak harga saat ini ke angka *Stop Loss*. Jika terpaksa *cut-loss*, kerugian di RDN Anda dijamin hanya 1% dari total uang Anda.
        """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem; font-weight:600; letter-spacing: 1px;'>⚡ JIHAN-GHINA ENGINE • INSTITUTIONAL TERMINAL PRO MAX v10.5</p>", unsafe_allow_html=True)
