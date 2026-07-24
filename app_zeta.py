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
import io

warnings.filterwarnings('ignore')

# ==========================================
# 0. SISTEM CACHE & TRACKING
# ==========================================
CACHE_FILE = "jihan_ghina_saham_cache_v159.json"

def load_smart_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                loaded_stocks = cache_data.get("raw_stocks", [])
                if loaded_stocks and isinstance(loaded_stocks, list):
                    if "REVENUE" not in loaded_stocks[0]:
                        return [], None
                return loaded_stocks, cache_data.get("last_update", None)
        except: pass
    return [], None

if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks, st.session_state.last_update = load_smart_cache()

if "scan_clicked" not in st.session_state: st.session_state.scan_clicked = len(st.session_state.raw_stocks) > 0
if "current_tf" not in st.session_state: st.session_state.current_tf = "1 Hari (Daily)"

# ==========================================
# 1. KONFIGURASI HALAMAN & LUXURY UI STYLE
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA Ultimate v15.9 Luxury", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -20%, #090d16, #020617) !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    h1 { color: #f8fafc; font-weight: 900; letter-spacing: -1.5px; font-size: 2.4rem !important; margin-bottom: 0; text-shadow: 0 4px 25px rgba(0,242,254,0.2); }
    p { color: #94a3b8; font-weight: 300; }
    ::-webkit-scrollbar { width: 6px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(0, 242, 254, 0.5); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0, 242, 254, 1); }
    section[data-testid="stSidebar"] { width: 285px !important; min-width: 285px !important; max-width: 285px !important; background: linear-gradient(180deg, rgba(2,6,23,0.98) 0%, rgba(15,23,42,0.98) 100%) !important; backdrop-filter: blur(25px); border-right: 1px solid rgba(0, 242, 254, 0.1); }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { font-size: 0.8rem !important; }
    section[data-testid="stSidebar"] label { font-size: 0.75rem !important; font-weight: 700 !important; color: #94a3b8 !important; letter-spacing: 0.5px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: rgba(15,23,42,0.7); padding: 6px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.05); }
    .stTabs [data-baseweb="tab"] { padding: 10px 22px; border-radius: 10px; color: #94a3b8; font-weight: 700; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, rgba(0,242,254,0.2) 0%, rgba(59,130,246,0.2) 100%) !important; color: #00f2fe; border: 1px solid rgba(0,242,254,0.4); box-shadow: 0 0 15px rgba(0,242,254,0.2); }
    .premium-card { background: rgba(30, 41, 59, 0.35); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 16px; padding: 20px; box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.6); transition: all 0.3s ease; display: flex; flex-direction: column; }
    .premium-card:hover { transform: translateY(-3px); box-shadow: 0 20px 40px -5px rgba(0, 242, 254, 0.2); border-color: rgba(0, 242, 254, 0.4); }
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 14px 20px !important; background: rgba(15,23,42,0.7); border-radius: 16px !important; }
    .ihsg-title { color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
    .ihsg-score { color: #00f2fe; font-size: 1.6rem; font-weight: 900; line-height: 1.1; margin: 4px 0; text-shadow: 0 0 15px rgba(0,242,254,0.3); }
    div.stButton > button:first-child { background: linear-gradient(90deg, rgba(0,242,254,0.1) 0%, rgba(30,58,138,0.25) 100%) !important; border: 1px solid rgba(0, 242, 254, 0.4) !important; color: #00f2fe !important; border-radius: 10px !important; padding: 10px 18px !important; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); font-weight: 900 !important; font-size: 0.95rem !important; letter-spacing: 1px;}
    div.stButton > button:first-child:hover { background: linear-gradient(90deg, #00f2fe 0%, #3b82f6 100%) !important; color: white !important; transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(0, 242, 254, 0.5); border-color: transparent !important; }
    .stDataFrame { font-size: 13.5px !important; border-radius: 12px !important; overflow: hidden !important; }
    th.row_heading { color: #00f2fe !important; font-weight: 900 !important; font-size: 1.1rem !important; text-align: center !important; }

    /* CSS: KOTAK MENGAMBANG (LUXURY COMPACT CHIPS) */
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] { gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label {
        background: rgba(30,41,59,0.8) !important; border: 1px solid rgba(0, 242, 254, 0.25) !important;
        border-radius: 8px !important; padding: 6px 14px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        cursor: pointer; transition: all 0.3s ease !important;
    }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: rgba(0, 242, 254, 0.2) !important; border-color: #00f2fe !important;
        transform: translateY(-2px) !important; box-shadow: 0 6px 18px rgba(0, 242, 254, 0.3) !important;
    }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label p { color: #00f2fe !important; font-weight: 900 !important; font-size: 0.9rem !important; margin: 0 !important; letter-spacing: 0.5px; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%) !important; border-color: #ffffff !important;
        box-shadow: 0 8px 22px rgba(0, 242, 254, 0.6) !important; transform: scale(1.03) !important;
    }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] p { color: #ffffff !important; text-shadow: 0 2px 4px rgba(0,0,0,0.4) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE QUOTES OF THE DAY
# ==========================================
QUOTES_DATABASE = [
    {"quote": "Dalam jangka pendek, pasar saham adalah mesin pemungutan suara (momentum). Dalam jangka panjang, ia adalah mesin penimbang (fundamental).", "author": "Benjamin Graham", "theme": "Trading vs Investment"},
    {"quote": "Membeli saham dengan Volume Pressure (WPI) di atas 80% adalah seperti menumpang roket yang bahan bakarnya baru saja diisi penuh.", "author": "Quantum Matrix Philosophy", "theme": "Momentum & Whales"},
    {"quote": "Mengetahui di mana titik ARA (Auto Reject Atas) adalah mengetahui batas keserakahan pasar hari itu. Jadikan itu target akhir Anda.", "author": "Sniper Algo Playbook", "theme": "Targeting & Execution"},
    {"quote": "Harga adalah apa yang Anda bayar. Nilai (Value) adalah apa yang Anda dapatkan.", "author": "Warren Buffett", "theme": "Valuasi & Fundamental"}
]

def get_quote_of_the_day():
    day_of_year = datetime.now(pytz.timezone('Asia/Jakarta')).timetuple().tm_yday
    index = day_of_year % len(QUOTES_DATABASE)
    return QUOTES_DATABASE[index]

# ==========================================
# 3. CORE ENGINE DATA FETCHING
# ==========================================
MASTER_UNIVERSE = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", "AMRT", "GOTO", "PGAS", "PTBA", "ITMG", 
    "KLBF", "ADRO", "UNVR", "BRIS", "CPIN", "ANTM", "AMMN", "BREN", "CUAN", "PANI", "BRPT", "MDKA", "MEDC", "ARTO", 
    "SIDO", "MYOR", "INKP", "TKIM", "SMGR", "INTP", "BFIN", "AKRA", "ESSA", "EXCL", "ISAT", "TOWR", "TBIG", "MTEL", 
    "MAPI", "MAPA", "ACES", "ERAA", "AUTO", "NISP", "BDMN", "BTPS", "BBTN", "BNGA", "BRMS", "BUMI", "ENRG", "DEWA", 
    "DOID", "HRUM", "INCO", "PTMP", "VKTR", "GGRM", "HMSP", "WIIM", "JSMR", "WIKA", "PTPP", "ADHI", "SMRA", "BSDE", 
    "CTRA", "PWON", "ASRI", "SSIA", "SRTG", "BMTR", "MNCN", "EMTK", "SCMA", "BUAH", "CLEO", "CMRY", "SILO", "MIKA", 
    "HEAL", "TPIA", "MBMA", "NCKL", "PGEO", "AVIA", "ARNA", "MARK", "INAF", "KAEF", "WOOD", "TAPG", "DSNG", "LSIP", 
    "AALI", "SSMS", "BBYB", "AGRO", "ARKA", "BABP", "BACA", "BGTG", "BHIT", "BIPI", "BKDP", "BVIC", "CARE", "CARS", 
    "CASS", "CBEZ", "CEKA", "CENT", "CFIN", "CINT", "CMNP", "COAL", "DANG", "DART", "DILD", "DKFT", "DMAS", "DSSA", 
    "EAST", "ELSA", "EMDE", "EPMT", "FAST", "FPNI", "FREN", "GJTL", "GLOB", "GZCO", "HOKI", "HOME", "IATA", "IBST", 
    "IGAR", "IMAS", "INPC", "IPCC", "IPCM", "IPTV", "IRRA", "JAWA", "JECC", "JPFA", "KBLI", "KBLV", "KIJA", "KINO", 
    "KPIG", "KRAS", "LINK", "LPCK", "LPKR", "LPPF", "MAIN", "MALA", "MARI", "MBSS", "MCOL", "MDLN", "MGRO", "MICE", 
    "MLBI", "MLIA", "MLPL", "MLPT", "MPMX", "MTDL", "MTLA", "NELY", "NRCA", "OBMD", "OASA", "OMRE", "Pans", "PBRX", 
    "PGLI", "PNBN", "PNBS", "PNIN", "PNLF", "POLU", "PRDA", "PSAB", "PTRO", "PURA", "RALS", "RANC", "RBMS", "RDTX", 
    "RELI", "RICY", "RIGS", "RIMO", "ROTI", "SAMA", "SAME", "SCNP", "SDRA", "SIMP", "SMCB", "SMMT", "SMPL", "SMSM", 
    "SOCI", "SPMA", "SRAI", "SRIL", "SSSC", "STTP", "SUDI", "SUGI", "SULI", "TARA", "TAXI", "TCID", "TEBE", "TGKA", 
    "TINS", "TIRA", "TOTO", "TRIS", "TRST", "TSPC", "TUGU", "ULTJ", "UNIC", "UNIT", "VINS", "VIVA", "VOKS", "WEGE", 
    "WIM", "WOMF", "WSBP", "WSKT", "WTON", "YPAS", "ZBRA"
]
master_tickers = list(set([t.strip().upper() + ".JK" for t in MASTER_UNIVERSE]))

def get_waktu_wib(): return datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %b %Y - %H:%M:%S WIB")

def export_df_to_excel_buffer(df_source, scan_time, sheet_name="Data_Saham"):
    df_export = df_source.copy()
    df_export['WAKTU_SCAN'] = scan_time
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=True, sheet_name=sheet_name[:31])
    return buffer.getvalue()

def format_rupiah(val):
    if pd.isna(val) or val == 0: return "-"
    return f"Rp {val:,.0f}".replace(",", ".")

def format_financials(val):
    if pd.isna(val) or val == 0: return "-"
    if val >= 1_000_000_000_000: return f"Rp {val/1_000_000_000_000:.2f} T"
    elif val >= 1_000_000_000: return f"Rp {val/1_000_000_000:.2f} M"
    else: return f"Rp {val/1_000_000:.2f} Jt"

def render_badges(tickers, hex_color):
    if not tickers: return "<span style='color:#64748b; font-size:0.8rem; font-style:italic; display:block; margin-top:10px;'>Menunggu peluang...</span>"
    res = "<div style='display:flex; flex-wrap:wrap; gap:8px; margin-top:15px;'>"
    for t in tickers: res += f"<span style='background:rgba(0,0,0,0.3); border:1px solid {hex_color}60; border-radius:6px; padding:4px 10px; color:{hex_color}; font-size:0.85rem; font-weight:800; box-shadow: 0 2px 4px rgba(0,0,0,0.3); letter-spacing:0.5px;'>{t}</span>"
    res += "</div>"
    return res

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ihsg_data():
    try:
        df = yf.download("^JKSE", period="1mo", interval="1d", progress=False)
        if df.empty: return None, None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        df = df.ffill() 
        return df, float(df['Close'].iloc[-1]), float(df['Close'].iloc[-1]) - float(df['Close'].iloc[-2]), ((float(df['Close'].iloc[-1]) - float(df['Close'].iloc[-2])) / float(df['Close'].iloc[-2])) * 100
    except: return None, None, None, None

def get_dynamic_market_roster():
    try:
        df_batch = yf.download(master_tickers, period="5d", group_by="ticker", threads=True, progress=False)
        market_data = []
        for ticker in master_tickers:
            try:
                if isinstance(df_batch.columns, pd.MultiIndex): df_t = df_batch[ticker].dropna()
                else:
                    if len(master_tickers) == 1: df_t = df_batch.dropna()
                    else: continue
                
                if len(df_t) < 2: continue
                close_now = float(df_t['Close'].iloc[-1])
                close_prev = float(df_t['Close'].iloc[-2])
                vol_now = float(df_t['Volume'].iloc[-1])
                if close_now < 50 or vol_now < 100000: continue 
                
                pct_change = ((close_now - close_prev) / close_prev) * 100
                trans_val = close_now * vol_now
                market_data.append({'Ticker': ticker, 'Change': pct_change, 'TransVal': trans_val, 'VolatilityScore': abs(pct_change) * trans_val})
            except: continue
            
        df_market = pd.DataFrame(market_data)
        if df_market.empty: return master_tickers[:300] 
        
        top_gainers = df_market.nlargest(120, 'Change')['Ticker'].tolist()
        top_liquid = df_market.nlargest(100, 'TransVal')['Ticker'].tolist()
        top_volatile = df_market.nlargest(80, 'VolatilityScore')['Ticker'].tolist()
        
        dynamic_roster = list(set(top_gainers + top_liquid + top_volatile))
        return dynamic_roster[:300] 
    except Exception as e:
        return master_tickers[:300] 

def hitung_rsi(df, periods=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/periods, min_periods=periods).mean()
    loss = (-1 * delta.clip(upper=0)).ewm(alpha=1/periods, min_periods=periods).mean()
    return 100 - (100 / (1 + (gain / loss)))

def hitung_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    return np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1).rolling(period).mean()

def fetch_single_stock(emiten, mode_tf):
    try:
        if "1 Jam" in mode_tf: per, inv = "60d", "1h"
        elif "4 Jam" in mode_tf: per, inv = "60d", "1h"
        elif "1 Minggu" in mode_tf: per, inv = "3y", "1wk"
        else: per, inv = "1y", "1d" 

        kode = emiten.replace(".JK", "")
        df = yf.download(emiten, period=per, interval=inv, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None: df.index = df.index.tz_localize(None)
        
        df = df.dropna(subset=['Close']) 
        df = df.ffill() 
        if len(df) < 30: return None 
        
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
        df['Signal'] = df['MACD'].ewm(span=9).mean()
        df['RSI'] = hitung_rsi(df)
        df['ATR'] = hitung_atr(df)
        df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()
        df['Chandelier_Exit'] = df['High'].rolling(22).max() - (df['ATR'] * 3.0)
        
        df_higher_tf = df.resample('W').agg({'Close':'last'}).dropna() if "Hari" in mode_tf else df
        df_higher_tf['EMA20_HTF'] = df_higher_tf['Close'].ewm(span=20).mean()
        
        harga_skg = float(df['Close'].iloc[-1])
        open_skg = float(df['Open'].iloc[-1])
        high_skg = float(df['High'].iloc[-1])
        low_skg = float(df['Low'].iloc[-1])
        vol_skg = float(df['Volume'].iloc[-1])
        vol_sma20 = float(df['Vol_SMA20'].iloc[-1])
        ema20_skg = float(df['EMA20'].iloc[-1])
        sma50_skg = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else ema20_skg
        prev_close = float(df['Close'].iloc[-2])
        
        if prev_close < 200: batas_ara, batas_arb = int(prev_close * 1.35), int(prev_close * 0.65)
        elif 200 <= prev_close < 5000: batas_ara, batas_arb = int(prev_close * 1.25), int(prev_close * 0.75)
        else: batas_ara, batas_arb = int(prev_close * 1.20), int(prev_close * 0.80)

        if harga_skg >= (batas_ara * 0.99): status_ara_arb = "🚀 ARA LOCK"
        elif harga_skg <= (batas_arb * 1.01): status_ara_arb = "🩸 ARB LOCK"
        else: status_ara_arb = "➖ NORMAL"

        if high_skg > low_skg: wpi_score = ((harga_skg - low_skg) / (high_skg - low_skg)) * 100
        else: wpi_score = 50.0

        atr_skg = float(df['ATR'].iloc[-1])
        trailing_stop = float(df['Chandelier_Exit'].iloc[-1])
        if pd.isna(trailing_stop) or trailing_stop >= harga_skg: trailing_stop = harga_skg - (atr_skg * 2) 
        
        ret_1d = ((harga_skg - prev_close) / prev_close * 100) if prev_close > 0 else 0
        
        rsi_skg = float(df['RSI'].iloc[-1])
        rsi_lalu = float(df['RSI'].iloc[-2])
        if rsi_lalu < 35 and rsi_skg > rsi_lalu: rsi_status = "🟢 REVERSAL DASAR"
        elif rsi_skg <= 35: rsi_status = "📉 DEEP OVERSOLD"
        elif rsi_lalu > 65 and rsi_skg < rsi_lalu: rsi_status = "🔴 REVERSAL PUCUK"
        elif rsi_skg >= 65: rsi_status = "📈 OVERBOUGHT"
        elif rsi_skg > rsi_lalu: rsi_status = "↗️ NAIK"
        else: rsi_status = "↘️ TURUN"

        is_bullish = harga_skg >= open_skg
        body_size = abs(open_skg - harga_skg)
        lower_shadow = (open_skg if is_bullish else harga_skg) - low_skg
        upper_shadow = high_skg - (harga_skg if is_bullish else open_skg)
        
        is_vol_spike = vol_skg > (vol_sma20 * 1.2)
        
        if is_vol_spike:
            if lower_shadow > (body_size * 1.5): status_bandar = "🐋 AKUMULASI DASAR"
            elif upper_shadow > (body_size * 1.5): status_bandar = "🩸 DISTRIBUSI PUCUK"
            elif is_bullish and wpi_score > 70: status_bandar = "🚀 MARK-UP BERINGAS"
            elif is_bullish: status_bandar = "🟢 AKUMULASI AWAL"
            else: status_bandar = "💥 MARK-DOWN"
        else:
            status_bandar = "➖ SEPI / KONSOLIDASI"
            
        high_20 = float(df['High'].tail(20).max())
        low_20 = float(df['Low'].tail(20).min())
        vcp_tightness = ((high_20 - low_20) / low_20) * 100
        is_volcano = (vol_skg > (vol_sma20 * 3)) and (harga_skg >= high_20) and (vcp_tightness < 15)
        
        is_mtf_bullish = False
        try:
            if len(df_higher_tf) >= 2:
                is_mtf_bullish = float(df_higher_tf['Close'].iloc[-1]) > float(df_higher_tf['EMA20_HTF'].iloc[-1])
        except: pass
        
        setup_score = 0
        if harga_skg > ema20_skg: setup_score += 1
        if is_mtf_bullish: setup_score += 2
        if "REVERSAL DASAR" in rsi_status or "DEEP OVERSOLD" in rsi_status: setup_score += 2
        if "AKUMULASI" in status_bandar or "MARK-UP" in status_bandar: setup_score += 2
        if is_volcano: setup_score += 3
        if wpi_score > 85: setup_score += 2 
        
        if setup_score >= 8 and wpi_score >= 70: setup_grade = "⭐ SETUP A+ (ALL OUT)"
        elif setup_score >= 5 and "AKUMULASI" in status_bandar and wpi_score < 40: setup_grade = "⚠️ SETUP C (UPPER SHADOW)" 
        elif setup_score >= 5 and wpi_score >= 80 and is_vol_spike: setup_grade = "⚡ SETUP AGGRESSIVE"
        elif setup_score >= 5: setup_grade = "✔️ SETUP B (NORMAL)"
        else: setup_grade = "⚠️ SETUP C (WEAK)"

        tkr = yf.Ticker(emiten)
        info = tkr.info if tkr.info else {}
        per_val = info.get('trailingPE', 0.0)
        pbv_val = info.get('priceToBook', 1.0)
        peg_val = info.get('pegRatio') or 0.0  
        div_rate = info.get('trailingAnnualDividendRate', 0)
        div_yield = (div_rate / harga_skg * 100) if (div_rate and harga_skg > 0) else 0.0
        mcap = info.get('marketCap', 0)
        
        rev = info.get('totalRevenue', 0)
        net_inc = info.get('netIncomeToCommon', 0)
        roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
        der = info.get('debtToEquity', 0)

        div_date_unix = info.get('exDividendDate', None)
        div_date_str = "-"
        if div_date_unix:
            try: div_date_str = datetime.fromtimestamp(div_date_unix).strftime('%d %b %Y')
            except: pass
            
        return {
            "TICKER": kode, "HARGA": harga_skg, 
            "AREA BELI": ema20_skg if harga_skg > ema20_skg else (low_20 + (harga_skg - low_20)*0.3), 
            "TRAILING STOP": trailing_stop,  
            "WPI_SCORE": round(wpi_score, 1),
            "BATAS_ARA": batas_ara, 
            "BATAS_ARB": batas_arb, 
            "STATUS_ARA_ARB": status_ara_arb, 
            "STATUS_BANDAR": status_bandar,    
            "SETUP_GRADE": setup_grade,      
            "IS_VOLCANO": is_volcano,        
            "UP_SMA50": harga_skg > sma50_skg,
            "PER": round(per_val, 2), "PBV": round(pbv_val, 2), "PEG": round(peg_val, 2), "DIV_YIELD": round(div_yield, 2),
            "REVENUE": rev, "NET_INCOME": net_inc, "ROE": round(roe, 2), "DER": round(der, 2),
            "RET_1D": ret_1d, "VOLUME": vol_skg, "VOL_SMA20": vol_sma20, "MARKET_CAP": mcap, "DIVIDEND_DATE": div_date_str, "TRANS_VAL": harga_skg * vol_skg
        }
    except Exception as e: 
        return None

# ==========================================
# 4. CROSS-VALIDATION UI (LUXURY COMPACT)
# ==========================================
def render_cross_validation_ui(active_tickers_tuple, market_climate_mult, is_trading_mode):
    st.markdown("---")
    st.markdown(f"""
    <div style="margin-top: 15px; margin-bottom: 15px; padding-left: 5px; border-left: 4px solid #00f2fe;">
        <h3 style="font-size: 1.6rem; font-weight: 900; color: #f8fafc; margin-bottom: 0px; margin-top: 0px; letter-spacing: -0.5px;">🎯 Sniper Cross-Validation {'(Trading Execution)' if is_trading_mode else '(Fundamental Health Check)'}</h3>
        <p style="color: #94a3b8; font-size: 0.8rem; font-weight: 400; margin-top: 2px;">{'Kalkulator otomatis untuk target ARA & Manajemen Risiko.' if is_trading_mode else 'Bedah neraca keuangan riil & kesehatan perusahaan jangka panjang.'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if active_tickers_tuple and len(active_tickers_tuple) > 0:
        safe_key = f"cv_target_v159_{st.session_state.current_tf}_{'TRD' if is_trading_mode else 'INV'}"
        
        valid_targets = []
        for t in active_tickers_tuple:
            raw_data = next((item for item in st.session_state.raw_stocks if item.get("TICKER") == t), None)
            if raw_data:
                if is_trading_mode:
                    grade = raw_data.get("SETUP_GRADE", "")
                    if "A+" in grade or "B" in grade or "AGGRESSIVE" in grade: valid_targets.append(t)
                else:
                    per = raw_data.get("PER", 0)
                    pbv = raw_data.get("PBV", 1)
                    peg = raw_data.get("PEG", 0)
                    div = raw_data.get("DIV_YIELD", 0)
                    up_sma = raw_data.get("UP_SMA50", False)
                    skor_i = 0
                    if 0 < per < 15: skor_i += 20
                    if 0 < pbv < 1.5: skor_i += 20
                    if div > 4.0: skor_i += 20
                    if up_sma: skor_i += 15
                    if 0 < peg <= 1.0: skor_i += 25 
                    if skor_i >= 40: valid_targets.append(t) 
        
        if not valid_targets:
            msg = "Semua emiten saat ini berstatus SETUP C (WEAK). Sistem memblokir Anda untuk masuk demi melindungi modal. Wait & See!" if is_trading_mode else "Tidak ada emiten dengan fundamental (Valuasi) yang cukup aman untuk diinvestasikan saat ini."
            st.markdown(f"""
            <div style='background:rgba(244, 63, 94, 0.1); border:1px solid #f43f5e; padding:12px; border-radius:10px; color:#f8fafc;'>
                ⚠️ <b>TIDAK ADA TARGET VALID.</b> {msg}
            </div>
            """, unsafe_allow_html=True)
            return

        if safe_key in st.session_state and st.session_state[safe_key] not in valid_targets:
            del st.session_state[safe_key]
            
        st.markdown("<p style='color:#00f2fe; font-size:0.75rem; font-weight:800; letter-spacing:1px; margin-bottom:-8px; text-transform:uppercase;'>Pilih Target Eksekusi (Compact Luxury Chips):</p>", unsafe_allow_html=True)
        emiten_signal = st.radio("Target Sniper:", options=valid_targets, horizontal=True, key=safe_key, label_visibility="collapsed")
        
        with st.spinner(f"Membedah anatomi {'Whale' if is_trading_mode else 'Financials'} {emiten_signal}..."):
            raw_target = next((item for item in st.session_state.raw_stocks if item.get("TICKER") == emiten_signal), None)
            
            if raw_target:
                if is_trading_mode:
                    setup_grade = raw_target.get("SETUP_GRADE", "⚠️ SETUP C")
                    harga_tgt = raw_target.get('HARGA', 0)
                    wpi_score = raw_target.get('WPI_SCORE', 50)
                    
                    area_beli = f"{int(raw_target.get('AREA BELI', harga_tgt)):,}".replace(",", ".")
                    trailing_stop_val = raw_target.get('TRAILING STOP', harga_tgt * 0.95)
                    if trailing_stop_val >= harga_tgt: trailing_stop_val = harga_tgt * 0.98 
                    trailing_stop = f"{int(trailing_stop_val):,}".replace(",", ".")
                    batas_ara = f"{int(raw_target.get('BATAS_ARA', 0)):,}".replace(",", ".")
                    status_ara_arb = raw_target.get('STATUS_ARA_ARB', "➖ NORMAL")
                    
                    if "A+" in setup_grade:
                        sys_rec_raw, color = "STRONG ACCUMULATE", "#10b981"
                        desc = "🔥 <b>SUPER TREND & WHALE CONFIRMED:</b> WPI tinggi! Probabilitas loncat (Gap-Up) besok sangat besar. Jadikan angka ARA di sebelah kanan sebagai target TP maksimal."
                        risk_multiplier = 2.0 
                    elif "AGGRESSIVE" in setup_grade:
                        sys_rec_raw, color = "AGGRESSIVE BUY (SCALP)", "#8b5cf6" 
                        desc = "⚡ <b>MOMENTUM GORENGAN CEPAT:</b> Bandar sedang injak gas. Cocok untuk tektok harian! Beli di Area Beli, dan jual di persentase berapapun sebelum menyentuh ARA."
                        risk_multiplier = 1.5
                    else:
                        sys_rec_raw, color = "ACCUMULATE", "#38bdf8"
                        desc = "🟢 Setup momentum solid. Harga memantul dari dasar. Cicil bertahap dan patuhi garis Trailing Stop dengan ketat."
                        risk_multiplier = 1.0 
                        
                    if "ARA LOCK" in status_ara_arb:
                        sys_rec_raw, color = "⚠️ ARA LOCKED (HOLD)", "#facc15"
                        desc += "<br><br>🚀 <b>STATUS ARA:</b> Saham ini sedang mentok kanan! Tidak disarankan Hajar Kanan sekarang. HOLD keras untuk GAP UP besok!"

                    final_risk_pct = risiko_pct * risk_multiplier * market_climate_mult
                    risk_per_share = harga_tgt - trailing_stop_val
                    
                    if risk_multiplier > 0 and risk_per_share > 0 and "ARA LOCK" not in status_ara_arb:
                        max_lots = int(((modal_trading * (final_risk_pct / 100)) / risk_per_share) / 100)
                        lot_rec_target = f"⚠️ AUTO-BRAKE: Max {max_lots:,} Lot (Risk {final_risk_pct:.1f}%)" if market_climate_mult < 1.0 else f"Max {max_lots:,} Lot (Risk Optimal {final_risk_pct:.1f}%)"
                        if market_climate_mult < 1.0: desc += "<br><i>🚨 CATATAN SISTEM: Mode Defensif Aktif. Lot size dipangkas 50% karena IHSG memburuk.</i>"
                    else: 
                        lot_rec_target = "Kunci Profit / Pantau Antrean"
                    
                    col_res1, col_res2 = st.columns([1.5, 1])
                    with col_res1:
                        st.markdown(f"<div style='background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px;'><div style='text-align: center; color: #94a3b8; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px;'>💻 DYNAMIC ALGO DECISION</div><div style='text-align: center; font-size: 1.7rem; font-weight: 900; color: {color}; margin-top: 4px; margin-bottom: 4px;'>{sys_rec_raw}</div><div style='text-align: center; font-size: 0.85rem; color: #facc15; font-weight: 800; margin-bottom: 12px;'>{setup_grade}</div></div>", unsafe_allow_html=True)
                        sub1, sub2, sub3, sub4 = st.columns(4)
                        with sub1: st.markdown(f"<div style='background: rgba(251, 191, 36, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(251, 191, 36, 0.2); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>HARGA AKTIF</div><div style='font-size: 1rem; color: #facc15; font-weight: 900; margin-top: 3px;'>{int(harga_tgt)}</div></div>", unsafe_allow_html=True)
                        with sub2: st.markdown(f"<div style='background: rgba(56, 189, 248, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.2); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>AREA BELI</div><div style='font-size: 1rem; color: #38bdf8; font-weight: 900; margin-top: 3px;'>{area_beli}</div></div>", unsafe_allow_html=True)
                        with sub3: st.markdown(f"<div style='background: rgba(244, 63, 94, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(244, 63, 94, 0.2); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>CUT LOSS</div><div style='font-size: 1rem; color: #f43f5e; font-weight: 900; margin-top: 3px;'>{trailing_stop}</div></div>", unsafe_allow_html=True)
                        with sub4: st.markdown(f"<div style='background: rgba(16, 185, 129, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.35); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>TARGET ARA</div><div style='font-size: 1rem; color: #10b981; font-weight: 900; margin-top: 3px;'>{batas_ara}</div></div>", unsafe_allow_html=True)
                            
                    with col_res2:
                        wpi_color = "#10b981" if wpi_score > 70 else "#fbbf24" if wpi_score > 40 else "#f43f5e"
                        st.markdown(f"<div style='background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;'><div style='text-align: center; color: #94a3b8; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px;'>🐋 WHALE PRESSURE INDEX</div><div style='text-align: center; font-size: 2.1rem; font-weight: 900; color: {wpi_color}; margin-top: 4px;'>{wpi_score}%</div><div style='font-size: 0.65rem; color: #64748b; text-align: center; margin-top: 6px;'>Kekuatan Beli Sesi Penutupan</div></div>", unsafe_allow_html=True)
                    
                    st.markdown(f"<div style='margin-top: 15px; background: rgba(15, 23, 42, 0.85); border: 1px solid {color}60; border-radius: 14px; padding: 22px; text-align: center; box-shadow: 0 10px 30px -10px {color}30;'><div style='color: {color}; font-size: 0.75rem; font-weight: 900; letter-spacing: 3px; margin-bottom: 6px; text-transform: uppercase;'>🏆 V15.9 LUXURY TRADING SIZING</div><div style='color: #cbd5e1; font-size: 0.9rem; font-weight: 300; max-width: 750px; margin: 0 auto; line-height: 1.5; margin-bottom: 15px;'>{desc}</div><div><span style='background: linear-gradient(90deg, rgba(0,242,254,0.15) 0%, rgba(30,58,138,0.3) 100%); border: 1px solid #00f2fe80; padding: 10px 25px; border-radius: 30px; color: #00f2fe; font-size: 0.95rem; font-weight: 900; display: inline-block;'>🎯 KEKUATAN BELI: {lot_rec_target}</span></div></div>", unsafe_allow_html=True)

                else:
                    per = raw_target.get("PER", 0)
                    pbv = raw_target.get("PBV", 1)
                    peg = raw_target.get("PEG", 0)
                    div = raw_target.get("DIV_YIELD", 0)
                    up_sma = raw_target.get("UP_SMA50", False)
                    rev = raw_target.get("REVENUE", 0)
                    net_inc = raw_target.get("NET_INCOME", 0)
                    roe = raw_target.get("ROE", 0)
                    der = raw_target.get("DER", 0)
                    
                    skor_i = 0
                    if 0 < per < 15: skor_i += 20
                    if 0 < pbv < 1.5: skor_i += 20
                    if div > 4.0: skor_i += 20
                    if up_sma: skor_i += 15
                    if 0 < peg <= 1.0: skor_i += 25 
                    
                    if skor_i >= 70: 
                        sys_rec_raw = "💎 UNDERVALUED (GROWTH)" if (0 < peg <= 1.0) else "💎 UNDERVALUED"
                        color = "#00f2fe"
                        desc = "✨ <b>PERMATA TERSEMBUNYI:</b> Saham ini diperdagangkan jauh di bawah nilai intrinsiknya. Sangat layak untuk portofolio jangka menengah-panjang. Kumpulkan secara DCA (Dollar Cost Averaging)!"
                    else: 
                        sys_rec_raw, color = "⚖️ FAIR VALUE", "#10b981"
                        desc = "🛡️ <b>HARGA WAJAR:</b> Perusahaan sehat dengan valuasi rasional. Aman dikoleksi selama metrik ROE dan pertumbuhannya tetap positif."

                    roe_color = "#10b981" if roe > 15 else ("#facc15" if roe > 5 else "#f43f5e")
                    der_color = "#10b981" if der < 100 else ("#facc15" if der < 200 else "#f43f5e")

                    col_res1, col_res2 = st.columns([1.5, 1])
                    with col_res1:
                        st.markdown(f"<div style='background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px;'><div style='text-align: center; color: #94a3b8; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px;'>🏛️ FUNDAMENTAL VALUATION</div><div style='text-align: center; font-size: 1.7rem; font-weight: 900; color: {color}; margin-top: 4px; margin-bottom: 4px;'>{sys_rec_raw}</div><div style='text-align: center; font-size: 0.85rem; color: #facc15; font-weight: 800; margin-bottom: 12px;'>Skor Kesehatan: {skor_i}/100</div></div>", unsafe_allow_html=True)
                        sub1, sub2, sub3, sub4 = st.columns(4)
                        with sub1: st.markdown(f"<div style='background: rgba(251, 191, 36, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(251, 191, 36, 0.2); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>TOTAL REVENUE</div><div style='font-size: 0.85rem; color: #facc15; font-weight: 900; margin-top: 3px;'>{format_financials(rev)}</div></div>", unsafe_allow_html=True)
                        with sub2: st.markdown(f"<div style='background: rgba(56, 189, 248, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.2); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>NET INCOME</div><div style='font-size: 0.85rem; color: #38bdf8; font-weight: 900; margin-top: 3px;'>{format_financials(net_inc)}</div></div>", unsafe_allow_html=True)
                        with sub3: st.markdown(f"<div style='background: rgba(16, 185, 129, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.35); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>ROE (%)</div><div style='font-size: 1rem; color: {roe_color}; font-weight: 900; margin-top: 3px;'>{roe:.1f}%</div></div>", unsafe_allow_html=True)
                        with sub4: st.markdown(f"<div style='background: rgba(244, 63, 94, 0.05); padding: 10px 4px; border-radius: 10px; border: 1px solid rgba(244, 63, 94, 0.2); text-align: center;'><div style='font-size: 0.55rem; color: #94a3b8; font-weight: 800;'>DER (%)</div><div style='font-size: 1rem; color: {der_color}; font-weight: 900; margin-top: 3px;'>{der:.1f}%</div></div>", unsafe_allow_html=True)
                            
                    with col_res2:
                        st.markdown(f"<div style='background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;'><div style='text-align: center; color: #94a3b8; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px;'>📊 METRIK VALUASI</div><div style='text-align: center; font-size: 1.1rem; font-weight: 900; color: #f8fafc; margin-top: 8px;'>PER: <span style='color:#38bdf8;'>{per:.1f}x</span></div><div style='text-align: center; font-size: 1.1rem; font-weight: 900; color: #f8fafc; margin-top: 4px;'>PBV: <span style='color:#38bdf8;'>{pbv:.1f}x</span></div><div style='text-align: center; font-size: 1.1rem; font-weight: 900; color: #f8fafc; margin-top: 4px;'>Yield: <span style='color:#10b981;'>{div:.1f}%</span></div></div>", unsafe_allow_html=True)
                    
                    st.markdown(f"<div style='margin-top: 15px; background: rgba(15, 23, 42, 0.85); border: 1px solid {color}60; border-radius: 14px; padding: 22px; text-align: center; box-shadow: 0 10px 30px -10px {color}30;'><div style='color: {color}; font-size: 0.75rem; font-weight: 900; letter-spacing: 3px; margin-bottom: 6px; text-transform: uppercase;'>🏆 V15.9 LUXURY INVESTMENT VERDICT</div><div style='color: #cbd5e1; font-size: 0.9rem; font-weight: 300; max-width: 750px; margin: 0 auto; line-height: 1.5;'>{desc}</div></div>", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR (DENGAN TOMBOL LOGOUT ELEGAN)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #00f2fe; font-size: 1.25rem; font-weight: 900; margin-bottom: 0px;'>💎 QUANTUM MATRIX</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.65rem; letter-spacing: 1.5px; margin-bottom: 20px;'>V15.9 LUXURY ELITE EDITION</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='font-size:0.75rem; color:#facc15; font-weight:800; letter-spacing:1px; border-bottom: 1px solid rgba(250,204,21,0.2); padding-bottom: 4px; margin-bottom: 8px;'>🎛️ CORE ENGINE MODE</div>", unsafe_allow_html=True)
    engine_mode = st.radio("Pilih Mode Analisis:", ("⚔️ TRADING (Momentum & Technical)", "🛡️ INVESTMENT (Value & Fundamental)"))
    st.markdown("<br>", unsafe_allow_html=True)

    tf_pilihan = st.selectbox("⏱️ Timeframe Analisis:", ("1 Hari (Daily)", "1 Minggu (Weekly)"), index=0)
    tf_berubah = tf_pilihan != st.session_state.current_tf
    if tf_berubah: st.session_state.current_tf = tf_pilihan
        
    st.markdown("<div style='font-size:0.7rem; color:#00f2fe; font-weight:800; letter-spacing:1px; margin-top:15px; border-bottom: 1px solid rgba(0,242,254,0.2); padding-bottom: 4px;'>🎯 RISK PROFILE ENGINE</div>", unsafe_allow_html=True)
    profil_risiko = st.selectbox("Tingkat Agresivitas AI:", ("⚖️ Moderat (Balanced)", "🔥 Agresif (High Signal)", "🛡️ Konservatif (Strict)"), index=0)
    
    st.markdown("<div style='font-size:0.7rem; color:#00f2fe; font-weight:800; letter-spacing:1px; margin-top:15px; border-bottom: 1px solid rgba(0,242,254,0.2); padding-bottom: 4px;'>⚙️ POSITION SIZING</div>", unsafe_allow_html=True)
    modal_input_str = st.text_input("💰 Modal Trading (Rp):", value="50.000.000")
    try: modal_trading = int(modal_input_str.replace(".", "").replace(",", ""))
    except: modal_trading = 50000000
    
    risiko_pct = st.slider("🚨 Batas Risiko Normal /Trade (%):", min_value=0.5, max_value=10.0, value=2.0, step=0.5)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔄 SCAN 300 EMITEN", use_container_width=True) or tf_berubah:
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.page_matrix = 0 
        st.session_state.raw_stocks = []
        
        radar_bar = st.progress(0, text="📡 Radar Super Lebar: Menyaring 300 Saham Aktif...")
        dynamic_tickers = get_dynamic_market_roster()
        radar_bar.empty()
        
        my_bar = st.progress(0, text=f"Deep Scanning {len(dynamic_tickers)} Trending Emiten ({st.session_state.current_tf})...")
        for i, t in enumerate(dynamic_tickers):
            my_bar.progress((i + 1) / len(dynamic_tickers), text=f"Menganalisis Data Emiten {t} ({i+1}/{len(dynamic_tickers)})")
            data = fetch_single_stock(t, st.session_state.current_tf)
            if data: st.session_state.raw_stocks.append(data)
            gc.collect() 
            
        my_bar.empty()
        st.session_state.last_update = get_waktu_wib()

        try:
            with open(CACHE_FILE, "w") as f: json.dump({"raw_stocks": st.session_state.raw_stocks, "last_update": st.session_state.last_update}, f)
        except: pass
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()

    # --- TOMBOL LOGOUT ELEGAN DI SIDEBAR BAWAH ---
    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    if st.button("🔒 LOGOUT / RESET SESI", use_container_width=True):
        st.session_state.clear()
        if os.path.exists(CACHE_FILE):
            try: os.remove(CACHE_FILE)
            except: pass
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()

# ==========================================
# 6. HEADER DASHBOARD
# ==========================================
st.markdown("<h1>🌐 Algorithmic Market Intelligence</h1>", unsafe_allow_html=True)

qotd = get_quote_of_the_day()
st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(0,242,254,0.08) 0%, rgba(30,58,138,0.18) 100%); border: 1px solid rgba(0,242,254,0.35); border-radius: 14px; padding: 15px 22px; margin-top: 15px; margin-bottom: 20px; box-shadow: 0 4px 25px rgba(0,0,0,0.4);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span style="color: #00f2fe; font-size: 0.7rem; font-weight: 900; letter-spacing: 2px; text-transform: uppercase;">💡 QUOTE OF THE DAY • {qotd['theme']}</span>
        <span style="color: #64748b; font-size: 0.7rem; font-weight: 700;">Rotasi Harian Otomatis</span>
    </div>
    <div style="color: #f8fafc; font-size: 0.95rem; font-style: italic; font-weight: 500; line-height: 1.5;">"{qotd['quote']}"</div>
    <div style="color: #facc15; font-size: 0.8rem; font-weight: 800; text-align: right; margin-top: 6px;">— {qotd['author']}</div>
</div>
""", unsafe_allow_html=True)

now_wib_check = datetime.now(pytz.timezone('Asia/Jakarta'))
jam_sekarang = now_wib_check.hour
hari_sekarang = now_wib_check.weekday()
file_timestamp = now_wib_check.strftime("%H_%d_%b_%Y")

alert_msg = "🟢 **ZONA TERAKURAT:** Market tutup. Waktu terbaik membedah kekuatan Whale Index (Trading) atau Valuasi Fundamental (Investment) untuk besok." if (hari_sekarang >= 5 or jam_sekarang >= 16 or jam_sekarang < 9) else "🟡 **ZONA LIVE MARKET:** Waspada delay API. Jangan Entry membabi buta, patuhi batas Trailing Stop!"
alert_color = "rgba(16, 185, 129, 0.2)" if (hari_sekarang >= 5 or jam_sekarang >= 16 or jam_sekarang < 9) else "rgba(251, 191, 36, 0.2)"
alert_border = "#10b981" if (hari_sekarang >= 5 or jam_sekarang >= 16 or jam_sekarang < 9) else "#fbbf24"
st.markdown(f"<div style='border-left: 5px solid {alert_border}; padding: 12px 18px; background: {alert_color}; border-radius: 10px; margin-bottom: 20px; color: #f8fafc; font-size: 0.9rem; font-weight: 500;'>{alert_msg}</div>", unsafe_allow_html=True)

uptrend_count = sum(1 for s in st.session_state.raw_stocks if s.get("UP_SMA50", False)) if "raw_stocks" in st.session_state and st.session_state.raw_stocks else 0
total_scanned = len(st.session_state.raw_stocks) if "raw_stocks" in st.session_state and st.session_state.raw_stocks else 1
breadth_pct = (uptrend_count / total_scanned) * 100

if breadth_pct >= 55: climate_status, climate_icon, climate_color, climate_mult = "RISK ON (BULLISH)", "🌞", "#10b981", 1.0
elif breadth_pct >= 40: climate_status, climate_icon, climate_color, climate_mult = "NEUTRAL (SIDEWAYS)", "⚖️", "#fbbf24", 1.0
else: climate_status, climate_icon, climate_color, climate_mult = "RISK OFF (BEARISH)", "⛈️", "#f43f5e", 0.5

col_h1, col_h2, col_h3 = st.columns([2.5, 1.25, 1.25])
with col_h1:
    upd_time = st.session_state.last_update if st.session_state.last_update else "Menunggu inisiasi radar 300 emiten..."
    tema_warna = "#facc15" if "TRADING" in engine_mode else "#10b981"
    st.markdown(f"<p style='font-size: 0.95rem; margin-top:5px;'>🕒 Last Market Sync: <strong style='color:#00f2fe;'>{upd_time}</strong><br>Sistem Beroperasi Dalam Mode: <strong style='color:{tema_warna};'>{engine_mode}</strong></p>", unsafe_allow_html=True)

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

with col_h3:
    if st.session_state.scan_clicked:
        st.markdown(f"""
        <div class="premium-card ihsg-box" style="border-left: 5px solid {climate_color};">
            <span class="ihsg-title">MARKET CLIMATE</span>
            <span class="ihsg-score" style="color:{climate_color};">{climate_icon} {climate_status}</span>
            <span style="color: #94a3b8; font-weight: 800; font-size: 0.75rem; margin-top:2px;">{breadth_pct:.1f}% Uptrend Breadth</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

if not st.session_state.scan_clicked or not st.session_state.raw_stocks:
    st.info("👈 Tekan tombol '🔄 SCAN 300 EMITEN' di panel kiri. (Peringatan: Loading memakan waktu sekitar 1-2 menit karena memproses data massif).")
else:
    hasil_trading = []
    hasil_invest = [] 
    
    cluster_deep_value = []
    cluster_high_growth = []
    cluster_div_kings = []
    
    for raw in st.session_state.raw_stocks:
        up_sma50 = raw.get("UP_SMA50", False)
        bd_status = raw.get("STATUS_BANDAR", "➖ NEUTRAL")
        setup_grade = raw.get("SETUP_GRADE", "⚠️ SETUP C")
        harga = raw.get("HARGA", 0)
        trailing_stop_val = raw.get("TRAILING STOP", harga * 0.95)
        ret_1d = raw.get("RET_1D", 0.0)
        ticker = raw.get("TICKER", "-")
        wpi_score = raw.get("WPI_SCORE", 50.0)
        status_ara_arb = raw.get("STATUS_ARA_ARB", "➖ NORMAL")
        
        per_val = raw.get("PER", 0.0)
        pbv_val = raw.get("PBV", 1.0)
        peg_val = raw.get("PEG", 0.0) 
        div_yield = raw.get("DIV_YIELD", 0.0)
        div_date = raw.get("DIVIDEND_DATE", "-")
        mcap = raw.get("MARKET_CAP", 0)

        # TRADING LOGIC
        if "A+" in setup_grade: kep_t = "🚀 STRONG ACCUM"
        elif "AGGRESSIVE" in setup_grade: kep_t = "⚡ AGGRESSIVE SCALP"
        elif "B" in setup_grade: kep_t = "🟢 ACCUMULATE"
        else: kep_t = "🟡 HOLD"
        
        risk_per_share = harga - trailing_stop_val
        if ("ACCUM" in kep_t or "SCALP" in kep_t) and risk_per_share > 0 and "ARA LOCK" not in status_ara_arb:
            multiplier = 2.0 if "A+" in setup_grade else (1.5 if "SCALP" in kep_t else 1.0)
            final_risk = risiko_pct * multiplier * climate_mult
            max_lots = int(((modal_trading * (final_risk / 100)) / risk_per_share) / 100)
            rec_lot_text = f"Max {max_lots:,} Lot"
        elif "ARA LOCK" in status_ara_arb: rec_lot_text = "⚠️ ARA LOCKED (HOLD)"
        else: rec_lot_text = "🔒 Proteksi/Hold"

        wpi_text = f"🐋 {wpi_score}% (POWER)" if wpi_score >= 80 else (f"🩸 {wpi_score}% (DUMP)" if wpi_score <= 30 else f"{wpi_score}%")

        hasil_trading.append({
            "RAW_RET": ret_1d, "TICKER": ticker, "HARGA": f"{int(harga):,}".replace(",", "."), "1D GAIN (%)": f"{ret_1d:+.2f}%",
            "WPI 🐋": wpi_text,
            "REKOMENDASI LOT": rec_lot_text, "TRAILING STOP": f"{int(trailing_stop_val):,}".replace(",", "."),
            "BANDARMOLOGI": bd_status, "REKOMENDASI": setup_grade
        })

        # INVESTMENT LOGIC
        skor_i = 0
        if 0 < per_val < 15: skor_i += 20
        if 0 < pbv_val < 1.5: skor_i += 20
        if div_yield > 4.0: skor_i += 20
        if up_sma50: skor_i += 15
        if 0 < peg_val <= 1.0: skor_i += 25 
        
        if skor_i >= 70: kep_i = "💎 UNDERVALUED (GROWTH)" if (0 < peg_val <= 1.0) else "💎 UNDERVALUED"
        elif skor_i >= 40: kep_i = "⚖️ FAIR VALUE"
        else: kep_i = "⚠️ OVERVALUED"
            
        hasil_invest.append({
            "RAW_YIELD": div_yield, "TICKER": ticker, "HARGA": f"{int(harga):,}".replace(",", "."), "MARKET CAP": format_financials(mcap),
            "PER (x)": f"{per_val:.2f}", "PBV (x)": f"{pbv_val:.2f}", "PEG (x)": f"{peg_val:.2f}", "DIV YIELD (%)": f"{div_yield:.2f}%",
            "DIV DATE": str(div_date), "VALUASI": kep_i
        })
        
        # CLUSTERING LOGIC
        if (0 < per_val < 10) and (0 < pbv_val < 1.0): cluster_deep_value.append(ticker)
        if (0 < peg_val <= 1.0): cluster_high_growth.append(ticker)
        if (div_yield >= 5.0): cluster_div_kings.append(ticker)

    df_trading = pd.DataFrame(hasil_trading)
    if not df_trading.empty:
        df_trading = df_trading.sort_values(by="RAW_RET", ascending=False).reset_index(drop=True).drop(columns=["RAW_RET"])
        df_trading.set_index("TICKER", inplace=True)
    top_trading_tickers = tuple(str(x) for x in df_trading.index[:15]) if not df_trading.empty else ()

    df_invest = pd.DataFrame(hasil_invest)
    if not df_invest.empty:
        df_invest = df_invest.sort_values(by="RAW_YIELD", ascending=False).reset_index(drop=True).drop(columns=["RAW_YIELD"])
        df_invest.set_index("TICKER", inplace=True)
    top_invest_tickers = tuple(str(x) for x in df_invest.index[:15]) if not df_invest.empty else ()

    if "TRADING" in engine_mode:
        tab1, tab2 = st.tabs(["🚀 TRADING SIGNAL (TOP 15 ELITE)", "📜 SOP TRADING"])
        
        with tab1:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🛰️ Target Sniper Utama (Top 15 Absolute Momentum)</h3>", unsafe_allow_html=True)
            def style_trading(row):
                styles = []
                if 'A+' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(16, 185, 129, 0.15); color: #10b981; font-weight:900;'
                elif 'AGGRESSIVE' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(139, 92, 246, 0.15); color: #c4b5fd; font-weight:900;'
                elif 'B' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(56, 189, 248, 0.12); color: #38bdf8;'
                else: bg_rek = 'background-color: rgba(244, 63, 94, 0.12); color: #fb7185;'
                
                for c, val in row.items():
                    if c == '1D GAIN (%)':
                        if '+' in str(val): styles.append('color: #10b981; font-weight: 900; text-align:center;')
                        elif '-' in str(val) and val != '-0.00%': styles.append('color: #f43f5e; font-weight: 900; text-align:center;')
                        else: styles.append('color: #94a3b8; text-align:center;')
                    elif c == 'WPI 🐋':
                        if 'POWER' in str(val): styles.append('color: #10b981; font-weight: 900; background: rgba(16,185,129,0.1);')
                        elif 'DUMP' in str(val): styles.append('color: #f43f5e; font-weight: 900;')
                        else: styles.append('color: #94a3b8;')
                    elif c == 'REKOMENDASI LOT':
                        if 'LOCKED' in str(val): styles.append('color: #facc15; font-weight: 900; background: rgba(250, 204, 33, 0.15);')
                        elif 'Max' in str(val): styles.append('color: #facc15; font-weight: 900;')
                        else: styles.append('color: #64748b; font-weight: 400;')
                    elif c == 'TRAILING STOP': styles.append('color: #f43f5e; font-weight: 800; text-align:center;')
                    elif c == 'REKOMENDASI': styles.append(bg_rek)
                    elif c == 'BANDARMOLOGI':
                        if 'AKUMULASI' in str(val): styles.append('color: #00f2fe; font-weight: 800;')
                        elif 'DISTRIBUSI' in str(val): styles.append('color: #f43f5e; font-weight: 800;')
                        elif 'MARK-UP' in str(val): styles.append('color: #10b981; font-weight: 800;')
                        else: styles.append('color: #94a3b8;')
                    else: styles.append('')
                return styles

            if not df_trading.empty:
                st.dataframe(df_trading.head(15).style.apply(style_trading, axis=1), use_container_width=True)
                excel_buffer_trd = export_df_to_excel_buffer(df_trading.head(300), st.session_state.last_update, "Trd_300_Data")
                st.download_button(label="📥 Download Master Excel (Semua 300 Emiten)", data=excel_buffer_trd, file_name=f"{file_timestamp}_Whale300_Trading.xlsx", use_container_width=True)
            
            render_cross_validation_ui(top_trading_tickers, climate_mult, is_trading_mode=True)

        with tab2:
            st.markdown("<br><h3 style='font-size: 1.5rem; color: #00f2fe;'>📜 SOP v15.9: Elite 15 Sniper</h3>", unsafe_allow_html=True)
            st.markdown("""
            **Fokus Eksekusi Harian:**
            *   **Layar Anti-Distraksi:** Tabel otomatis menyaring dan HANYA menyajikan **15 Sinyal Teratas** paling prospektif.
            *   **Whale Pressure Index (WPI 🐋):** Abaikan yang WPI-nya "DUMP". Fokus pada tekanan beli sesi akhir berstatus "POWER".
            *   **Target ARA (Auto Reject Atas):** Klik target pada kotak di bawah tabel, dan jadikan nilai "TARGET ARA" sebagai target lepas barang maksimal.
            """)

    else: 
        tab1, tab2, tab3 = st.tabs(["🛡️ VALUE & GROWTH MATRIX (TOP 15)", "🧬 INVESTMENT CLUSTERS", "📜 SOP INVESTASI"])
        
        with tab1:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🛡️ Top 15 Institutional Investment (Sorted by Yield)</h3>", unsafe_allow_html=True)
            def style_invest(row):
                styles = []
                for c, val in row.items():
                    if c == 'DIV YIELD (%)':
                        if val != '0.00%': styles.append('color: #10b981; font-weight: 900; background: rgba(16,185,129,0.1);')
                        else: styles.append('color: #64748b;')
                    elif c in ['PER (x)', 'PBV (x)', 'PEG (x)']:
                        try:
                            v = float(val)
                            if (c == 'PER (x)' and 0 < v < 15) or (c == 'PBV (x)' and 0 < v < 1.2) or (c == 'PEG (x)' and 0 < v <= 1.0): styles.append('color: #38bdf8; font-weight: 800;')
                            elif v > 20 or v > 2.5: styles.append('color: #f43f5e; font-weight: 800;')
                            else: styles.append('color: #cbd5e1;')
                        except: styles.append('')
                    elif c == 'DIV DATE': styles.append('color: #94a3b8; font-size: 0.85rem; text-align: center;')
                    elif c == 'VALUASI':
                        if 'GROWTH' in val: styles.append('background: linear-gradient(90deg, rgba(16,185,129,0.2) 0%, rgba(0,242,254,0.2) 100%); color: #00f2fe; font-weight:900;')
                        elif 'BUY' in val or 'UNDERVALUED' in val: styles.append('background-color: rgba(16, 185, 129, 0.12); color: #34d399; font-weight:800;')
                        elif 'HOLD' in val or 'FAIR' in val: styles.append('background-color: rgba(245, 158, 11, 0.12); color: #fbbf24; font-weight:800;')
                        else: styles.append('background-color: rgba(244, 63, 94, 0.12); color: #fb7185; font-weight:800;')
                    else: styles.append('')
                return styles

            if not df_invest.empty:
                st.dataframe(df_invest.head(15).style.apply(style_invest, axis=1), use_container_width=True)
                excel_buffer_inv = export_df_to_excel_buffer(df_invest.head(300), st.session_state.last_update, "Inv_300_Data")
                st.download_button(label="📥 Download Master Excel (Semua 300 Emiten)", data=excel_buffer_inv, file_name=f"{file_timestamp}_Whale300_Investment.xlsx", use_container_width=True)
            
            render_cross_validation_ui(top_invest_tickers, climate_mult, is_trading_mode=False)
            
        with tab2:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🧬 Behavioral Investment Clusters (v15.9)</h3>", unsafe_allow_html=True)
            c_val, c_gro, c_div = st.columns(3)
            with c_val:
                badges_val = render_badges(cluster_deep_value, "#00f2fe")
                st.markdown(f"<div class='premium-card' style='border-top: 4px solid #00f2fe; height: 100%;'><div style='color:#00f2fe; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>💎 1. DEEP VALUE GEMS</div><div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Saham sangat murah. Diperdagangkan di bawah nilai buku (PBV < 1) dengan PER rendah (< 10).</div>{badges_val}</div>", unsafe_allow_html=True)
            with c_gro:
                badges_gro = render_badges(cluster_high_growth, "#8b5cf6")
                st.markdown(f"<div class='premium-card' style='border-top: 4px solid #8b5cf6; height: 100%;'><div style='color:#8b5cf6; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>🚀 2. HIGH GROWTH</div><div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Pertumbuhan laba mengalahkan valuasinya (PEG Ratio < 1). Cocok untuk capital gain agresif.</div>{badges_gro}</div>", unsafe_allow_html=True)
            with c_div:
                badges_div = render_badges(cluster_div_kings, "#10b981")
                st.markdown(f"<div class='premium-card' style='border-top: 4px solid #10b981; height: 100%;'><div style='color:#10b981; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>💰 3. DIVIDEND KINGS</div><div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Mesin pencetak uang pasif. Memberikan imbal hasil (Dividend Yield) di atas 5% per tahun.</div>{badges_div}</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown("<br><h3 style='font-size: 1.5rem; color: #10b981;'>📜 SOP Value & Growth Investing</h3>", unsafe_allow_html=True)
            st.markdown("""
            **Buku Putih Portfolio Jangka Panjang:**
            *   **Data Riil Financials:** Saat Anda klik kotak emiten, sistem langsung menarik Laba Bersih, Pendapatan, dan ROE dari API pusat.
            *   **Gunakan Fitur Cluster:** Ingin *passive income*? Ambil langsung dari cluster *Dividend Kings*. Ingin capital gain eksponensial? Fokus kumpulkan *High Growth*.
            """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem; font-weight:600;'>⚡ JIHAN-GHINA ENGINE • INSTITUTIONAL MASTERPIECE v15.9 (Luxury Edition)</p>", unsafe_allow_html=True)
