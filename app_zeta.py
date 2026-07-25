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
import plotly.graph_objects as go

warnings.filterwarnings('ignore')

# ==========================================
# 0. REACTIVE STATE MANAGEMENT & CACHE
# ==========================================
CACHE_FILE = "jihan_ghina_saham_cache_v170.json"

def load_smart_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                loaded_stocks = cache_data.get("raw_stocks", [])
                if loaded_stocks and isinstance(loaded_stocks, list):
                    if "BID" not in loaded_stocks[0]: return [], None
                return loaded_stocks, cache_data.get("last_update", None)
        except: pass
    return [], None

if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks, st.session_state.last_update = load_smart_cache()

if "scan_clicked" not in st.session_state: st.session_state.scan_clicked = len(st.session_state.raw_stocks) > 0
if "current_tf" not in st.session_state: st.session_state.current_tf = "1 Hari (Daily)"

# ==========================================
# 1. KONFIGURASI HALAMAN & LUXURY UI (v17.0)
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA VIP v17.0", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; scroll-behavior: smooth; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -10%, #060d1a, #010308) !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; padding-left: 2.5rem !important; padding-right: 2.5rem !important; max-width: 100% !important; animation: fadeIn 0.6s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
    
    h1 { color: #f8fafc; font-weight: 800; letter-spacing: -1px; font-size: 2.2rem !important; margin-bottom: 0; text-shadow: 0 4px 20px rgba(212, 175, 55, 0.15); }
    h3 { font-weight: 700; letter-spacing: -0.5px; }
    p { color: #94a3b8; font-weight: 300; }
    
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.8); }
    ::-webkit-scrollbar-thumb { background: rgba(212, 175, 55, 0.4); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(212, 175, 55, 0.9); }
    
    /* VIP CARDS CSS */
    .vip-card { background: linear-gradient(145deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.9) 100%); backdrop-filter: blur(10px); border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 16px; padding: 20px; box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5); position: relative; overflow: hidden; transition: all 0.3s ease; display: flex; flex-direction: column; justify-content: space-between; height: 100%;}
    .vip-card:hover { transform: translateY(-5px); box-shadow: 0 15px 35px -5px rgba(212, 175, 55, 0.2); border-color: rgba(212, 175, 55, 0.6); }
    .vip-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, #d4af37, #facc15, #d4af37); }
    .vip-title { font-size: 1.8rem; font-weight: 800; color: #f8fafc; margin: 0; letter-spacing: 1px;}
    .vip-price { font-size: 1.3rem; font-weight: 800; margin: 5px 0 15px 0; }
    .vip-badge { background: rgba(212, 175, 55, 0.15); color: #d4af37; padding: 6px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; display: inline-block; border: 1px solid rgba(212, 175, 55, 0.5); letter-spacing: 0.5px;}
    .vip-stat-row { display: flex; justify-content: space-between; margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); }
    .vip-stat { text-align: center; }
    .vip-stat-label { font-size: 0.6rem; color: #64748b; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; }
    .vip-stat-val { font-size: 0.95rem; font-weight: 800; margin-top: 3px; }
    
    section[data-testid="stSidebar"] { width: 280px !important; min-width: 280px !important; max-width: 280px !important; background: linear-gradient(180deg, rgba(2,6,23,0.98) 0%, rgba(15,23,42,0.98) 100%) !important; backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.03); }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { font-size: 0.8rem !important; }
    section[data-testid="stSidebar"] label { font-size: 0.75rem !important; font-weight: 700 !important; color: #cbd5e1 !important; letter-spacing: 0.5px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background-color: rgba(15,23,42,0.4); padding: 4px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); margin-bottom: 15px;}
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; border-radius: 6px; color: #64748b; font-weight: 700; font-size:0.85rem; transition: all 0.3s ease; }
    .stTabs [aria-selected="true"] { background-color: rgba(212, 175, 55, 0.1); color: #d4af37; border: 1px solid rgba(212, 175, 55, 0.3); box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    
    .premium-card { background: rgba(30, 41, 59, 0.2); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.04); border-radius: 12px; padding: 16px; box-shadow: 0 8px 30px -10px rgba(0, 0, 0, 0.4); transition: all 0.3s ease; display: flex; flex-direction: column; }
    .premium-card:hover { transform: translateY(-2px); box-shadow: 0 12px 35px -5px rgba(0, 242, 254, 0.1); border-color: rgba(0, 242, 254, 0.25); }
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 10px 16px !important; background: linear-gradient(135deg, rgba(15,23,42,0.7) 0%, rgba(30,41,59,0.4) 100%); }
    .ihsg-title { color: #64748b; font-size: 0.65rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; }
    .ihsg-score { color: #f8fafc; font-size: 1.5rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
    
    div.stButton > button:first-child { background: linear-gradient(90deg, rgba(30,41,59,0.5) 0%, rgba(15,23,42,0.8) 100%) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #cbd5e1 !important; border-radius: 8px !important; padding: 8px 12px !important; transition: all 0.3s ease; font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 0.5px;}
    div.stButton > button:first-child:hover { background: linear-gradient(90deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.05) 100%) !important; color: #d4af37 !important; border-color: rgba(212, 175, 55, 0.5) !important; transform: scale(1.02); }
    
    .stDataFrame { font-size: 13.5px !important; }
    th.row_heading { color: #d4af37 !important; font-weight: 800 !important; font-size: 1rem !important; text-align: center !important; }

    .block-container [data-testid="stRadio"] > div[role="radiogroup"] { gap: 8px; flex-wrap: wrap; margin-top: 5px; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label { background: rgba(30,41,59,0.4) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 6px !important; padding: 6px 14px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important; cursor: pointer; transition: all 0.2s ease !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label:hover { background: rgba(212, 175, 55, 0.08) !important; border-color: rgba(212, 175, 55, 0.4) !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label p { color: #cbd5e1 !important; font-weight: 700 !important; font-size: 0.85rem !important; margin: 0 !important; letter-spacing: 0.5px; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] { background: linear-gradient(135deg, rgba(212,175,55,0.15) 0%, rgba(30,58,138,0.3) 100%) !important; border-color: #d4af37 !important; box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2) !important; transform: scale(1.05) !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] p { color: #d4af37 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE QUOTES
# ==========================================
QUOTES_DATABASE = [
    {"quote": "Eksekusi tajam tanpa emosi. Selamat datang di ruang eksekutif.", "author": "Quantum VIP", "theme": "Prestige"},
    {"quote": "Price Action tidak pernah berbohong. Ekor lilin di area support adalah jejak akumulasi yang nyata.", "author": "Technical Reality", "theme": "Price Action"},
    {"quote": "Harga adalah apa yang Anda bayar. Nilai (Value) adalah apa yang Anda dapatkan.", "author": "Warren Buffett", "theme": "Fundamental"}
]
def get_quote_of_the_day(): return QUOTES_DATABASE[datetime.now(pytz.timezone('Asia/Jakarta')).timetuple().tm_yday % len(QUOTES_DATABASE)]

# ==========================================
# 3. CORE ENGINE (TETAP REALIST v16.6 - ANTI BONCOS)
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

def get_waktu_wib(): return datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %b %Y - %H:%M WIB")

def format_financials(val):
    if pd.isna(val) or val == 0: return "-"
    if val >= 1_000_000_000_000 or val <= -1_000_000_000_000: return f"Rp {val/1_000_000_000_000:.2f} T"
    elif val >= 1_000_000_000 or val <= -1_000_000_000: return f"Rp {val/1_000_000_000:.2f} M"
    else: return f"Rp {val/1_000_000:.2f} Jt"

def render_badges(tickers, hex_color):
    if not tickers: return "<span style='color:#475569; font-size:0.75rem; font-style:italic;'>Tidak ada data...</span>"
    res = "<div style='display:flex; flex-wrap:wrap; gap:6px; margin-top:10px;'>"
    for t in tickers: res += f"<span style='background:rgba(0,0,0,0.2); border:1px solid {hex_color}40; border-radius:4px; padding:3px 8px; color:{hex_color}; font-size:0.75rem; font-weight:700;'>{t}</span>"
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
                else: df_t = df_batch.dropna() if len(master_tickers) == 1 else pd.DataFrame()
                if len(df_t) < 2: continue
                c_now = float(df_t['Close'].iloc[-1])
                if c_now < 50 or float(df_t['Volume'].iloc[-1]) < 50000: continue 
                chg = ((c_now - float(df_t['Close'].iloc[-2])) / float(df_t['Close'].iloc[-2])) * 100
                market_data.append({'Ticker': ticker, 'Change': chg, 'TransVal': c_now * float(df_t['Volume'].iloc[-1])})
            except: continue
        df_market = pd.DataFrame(market_data)
        if df_market.empty: return master_tickers[:300] 
        return list(set(df_market.nlargest(120, 'Change')['Ticker'].tolist() + df_market.nlargest(100, 'TransVal')['Ticker'].tolist()))[:300]
    except: return master_tickers[:300] 

def fetch_single_stock(emiten, mode_tf):
    try:
        per, inv = ("3y", "1wk") if "Minggu" in mode_tf else ("1y", "1d")
        kode = emiten.replace(".JK", "")
        df = yf.download(emiten, period=per, interval=inv, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        df = df.dropna(subset=['Close']).ffill()
        if len(df) < 30: return None 
        
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        df['ATR'] = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1).rolling(14).mean()
        df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()
        
        h_skg, o_skg, hi_skg, lo_skg, v_skg = float(df['Close'].iloc[-1]), float(df['Open'].iloc[-1]), float(df['High'].iloc[-1]), float(df['Low'].iloc[-1]), float(df['Volume'].iloc[-1])
        prev_c = float(df['Close'].iloc[-2])
        ema20, sma50, atr = float(df['EMA20'].iloc[-1]), float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else float(df['EMA20'].iloc[-1]), float(df['ATR'].iloc[-1])
        vol_sma20 = float(df['Vol_SMA20'].iloc[-1])
        
        b_ara, b_arb = (int(prev_c * 1.35), int(prev_c * 0.65)) if prev_c < 200 else ((int(prev_c * 1.25), int(prev_c * 0.75)) if prev_c < 5000 else (int(prev_c * 1.20), int(prev_c * 0.80)))
        status_ara = "🚀 ARA LOCK" if h_skg >= (b_ara * 0.99) else ("🩸 ARB LOCK" if h_skg <= (b_arb * 1.01) else "➖ NORMAL")
        wpi_score = ((h_skg - lo_skg) / (hi_skg - lo_skg)) * 100 if hi_skg > lo_skg else 50.0
        
        t_stop = float(df['High'].rolling(22).max().iloc[-1]) - (atr * 3.0)
        if pd.isna(t_stop) or t_stop >= h_skg: t_stop = h_skg - (atr * 2) 
        
        is_bull = h_skg >= o_skg
        b_size, u_shadow, l_shadow = abs(o_skg - h_skg), hi_skg - (h_skg if is_bull else o_skg), (o_skg if is_bull else h_skg) - lo_skg
        is_spike = v_skg > (vol_sma20 * 1.2)
        
        # Realist Algo: Price Action Murni
        info = yf.Ticker(emiten).info or {}
        bid_price = info.get('bid', 0)
        ask_price = info.get('ask', 0)
        
        low_20 = float(df['Low'].tail(20).min())
        dist_to_low = ((h_skg - low_20) / low_20) * 100
        is_near_support = dist_to_low < 5.0 
        is_vol_dry = v_skg < (vol_sma20 * 0.8) 
        is_hammer = l_shadow > (b_size * 2) and l_shadow > u_shadow
        is_fake_accum = not is_bull and wpi_score < 35 and prev_c > ema20
        
        if is_near_support and is_hammer: s_bandar = "🎯 SEROK BAWAH (REJECTION)"
        elif is_near_support and is_vol_dry: s_bandar = "🔍 VOLUME DRY-UP (PANTAU)"
        elif is_fake_accum: s_bandar = "⚠️ FAKE ACCUMULATION (GUYURAN)"
        elif is_spike:
            if l_shadow > (b_size * 1.5): s_bandar = "🐋 AKUMULASI DASAR"
            elif u_shadow > (b_size * 1.5): s_bandar = "🩸 DISTRIBUSI PUCUK"
            elif is_bull and wpi_score > 70: s_bandar = "🚀 MARK-UP BERINGAS"
            elif is_bull: s_bandar = "🟢 AKUMULASI AWAL"
            else: s_bandar = "💥 MARK-DOWN"
        else: s_bandar = "➖ SEPI"
            
        score = sum([h_skg > ema20, wpi_score > 85, is_spike]) * 2 + (3 if v_skg > vol_sma20*3 and h_skg >= float(df['High'].tail(20).max()) else 0)
        
        if "SEROK" in s_bandar: grade = "🎯 SETUP REACTIVE (BOTTOM)"
        elif "FAKE" in s_bandar: grade = "⚠️ SETUP C (AVOID)"
        elif score >= 6 and wpi_score >= 70: grade = "⭐ SETUP A+" 
        elif score >= 4 and wpi_score >= 80: grade = "⚡ SETUP AGGRESSIVE"
        elif score >= 2: grade = "✔️ SETUP B"
        else: grade = "⚠️ SETUP C"

        div_date_unix = info.get('exDividendDate', None)
        div_date_str = "-"
        if div_date_unix:
            try: div_date_str = datetime.fromtimestamp(div_date_unix).strftime('%d %b %Y')
            except: pass

        return {
            "TICKER": kode, "HARGA": h_skg, "AREA BELI": ema20 if h_skg > ema20 else (low_20 + (h_skg - low_20)*0.3), 
            "TRAILING STOP": t_stop, "WPI_SCORE": round(wpi_score, 1), "BATAS_ARA": b_ara, "STATUS_ARA_ARB": status_ara, 
            "STATUS_BANDAR": s_bandar, "SETUP_GRADE": grade, "UP_SMA50": h_skg > sma50,
            "PER": round(info.get('trailingPE', 0), 2), "PBV": round(info.get('priceToBook', 1), 2), "PEG": round(info.get('pegRatio') or 0, 2), 
            "DIV_YIELD": round((info.get('trailingAnnualDividendRate', 0) / h_skg * 100) if info.get('trailingAnnualDividendRate', 0) else 0, 2),
            "REVENUE": info.get('totalRevenue', 0), "NET_INCOME": info.get('netIncomeToCommon', 0), "ROE": round(info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0, 2),
            "RET_1D": ((h_skg - prev_c) / prev_c * 100) if prev_c > 0 else 0, "MARKET_CAP": info.get('marketCap', 0), "DIVIDEND_DATE": div_date_str,
            "BID": bid_price, "OFFER": ask_price
        }
    except: return None

# ENGINE GRAFIK KUARTAL
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_quarterly_charts(emiten):
    try:
        tkr = yf.Ticker(f"{emiten}.JK")
        inc = tkr.quarterly_financials
        bs = tkr.quarterly_balance_sheet
        cf = tkr.quarterly_cashflow
        if inc.empty and bs.empty: return None, None, None, None
        dates = inc.columns[:4][::-1] if not inc.empty else bs.columns[:4][::-1]
        str_dates = [d.strftime('%b %Y') for d in dates]
        def safe_get(df, keys):
            for k in keys:
                if k in df.index: return df.loc[k][:4][::-1].fillna(0).tolist()
            return [0] * len(str_dates)
        rev = safe_get(inc, ['Total Revenue', 'Operating Revenue'])
        net_inc = safe_get(inc, ['Net Income', 'Net Income Continuous Operations'])
        assets = safe_get(bs, ['Total Assets'])
        liab = safe_get(bs, ['Total Liabilities Net Minority Interest', 'Total Liabilities'])
        ocf = safe_get(cf, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
        fcf = safe_get(cf, ['Free Cash Flow'])
        return str_dates, (rev, net_inc), (assets, liab), (ocf, fcf)
    except: return None, None, None, None

def plot_luxury_bar(x_data, y1, y2, name1, name2, color1, color2, title):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_data, y=y1, name=name1, marker_color=color1, opacity=0.85, textposition='auto'))
    fig.add_trace(go.Bar(x=x_data, y=y2, name=name2, marker_color=color2, opacity=0.85, textposition='auto'))
    fig.update_layout(
        height=320, 
        title=dict(text=title, font=dict(color='#cbd5e1', size=13)),
        barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color='#94a3b8', size=10)),
        margin=dict(l=10, r=10, t=35, b=10), 
        dragmode=False, 
        xaxis=dict(showgrid=False, tickfont=dict(color='#64748b'), fixedrange=True),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#64748b'), zerolinecolor='rgba(255,255,255,0.1)', fixedrange=True)
    )
    return fig

# ==========================================
# 4. CROSS-VALIDATION UI
# ==========================================
def render_cross_validation_ui(active_tickers_tuple, market_climate_mult, is_trading_mode):
    st.markdown("---")
    st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #d4af37;">
        <h3 style="font-size: 1.6rem; font-weight: 800; color: #f8fafc; margin-bottom: 0px; margin-top: 0px;">⚡ Reactive Target Validation</h3>
        <p style="color: #64748b; font-size: 0.8rem; font-weight: 400; margin-top: 2px;">{'Pilih target sekunder untuk membedah Momentum & Titik Reaksi.' if is_trading_mode else 'Bedah Laporan Keuangan Riil Kuartalan (Compact View).'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if active_tickers_tuple:
        safe_key = f"cv_target_v170_{st.session_state.current_tf}_{'TRD' if is_trading_mode else 'INV'}"
        valid_targets = [t for t in active_tickers_tuple if next((i for i in st.session_state.raw_stocks if i.get("TICKER")==t), None)]
        if not valid_targets: return
        
        emiten_signal = st.radio("Target Sekunder:", options=valid_targets[:15], horizontal=True, key=safe_key, label_visibility="collapsed")
        
        raw_target = next((item for item in st.session_state.raw_stocks if item.get("TICKER") == emiten_signal), None)
        if raw_target:
            if is_trading_mode:
                setup_grade = raw_target.get("SETUP_GRADE", "")
                s_bandar = raw_target.get("STATUS_BANDAR", "")
                h_tgt, wpi = raw_target.get('HARGA', 0), raw_target.get('WPI_SCORE', 50)
                a_beli = f"{int(raw_target.get('AREA BELI', h_tgt)):,}".replace(",", ".")
                t_stop_val = raw_target.get('TRAILING STOP', h_tgt * 0.95)
                t_stop = f"{int(t_stop_val):,}".replace(",", ".")
                b_ara = f"{int(raw_target.get('BATAS_ARA', 0)):,}".replace(",", ".")
                s_ara = raw_target.get('STATUS_ARA_ARB', "")
                
                if "REACTIVE" in setup_grade: sys_rec, color, r_mult = "BOTTOM FISHING (SEROK)", "#d4af37", 1.5
                elif "AVOID" in setup_grade: sys_rec, color, r_mult = "AVOID (FAKE SIGNAL)", "#f43f5e", 0.0
                elif "A+" in setup_grade: sys_rec, color, r_mult = "STRONG ACCUMULATE", "#10b981", 2.0 
                elif "AGGRESSIVE" in setup_grade: sys_rec, color, r_mult = "AGGRESSIVE SCALP", "#8b5cf6", 1.5
                else: sys_rec, color, r_mult = "ACCUMULATE", "#0ea5e9", 1.0 
                if "ARA" in s_ara: sys_rec, color = "⚠️ ARA LOCKED", "#facc15"

                max_lots = int(((modal_trading * (risiko_pct * r_mult * market_climate_mult / 100)) / (h_tgt - t_stop_val)) / 100) if (h_tgt - t_stop_val)>0 and r_mult > 0 else 0
                
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.markdown(f"<div class='premium-card' style='padding: 15px;'><div style='text-align: center; color: #64748b; font-size: 0.7rem; font-weight: 800; letter-spacing: 1px;'>DYNAMIC DECISION</div><div style='text-align: center; font-size: 1.5rem; font-weight: 800; color: {color}; margin: 4px 0;'>{sys_rec}</div><div style='text-align: center; font-size: 0.8rem; color: #d4af37; font-weight: 700; margin-bottom: 12px;'>Max Entry: {max_lots:,} Lot</div></div>", unsafe_allow_html=True)
                    s1, s2, s3, s4 = st.columns(4)
                    for col, label, val, c_col in zip([s1,s2,s3,s4], ["HARGA", "AREA BELI", "CUT LOSS", "TARGET ARA"], [int(h_tgt), a_beli, t_stop, b_ara], ["#f8fafc", "#d4af37", "#f43f5e", "#10b981"]):
                        with col: st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 10px 5px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); text-align: center;'><div style='font-size: 0.55rem; color: #64748b; font-weight: 800;'>{label}</div><div style='font-size: 0.95rem; color: {c_col}; font-weight: 800; margin-top: 2px;'>{val}</div></div>", unsafe_allow_html=True)
                with c2:
                    wpi_color = '#f43f5e' if "FAKE" in s_bandar else ('#d4af37' if "SEROK" in s_bandar else ('#10b981' if wpi>70 else '#facc15' if wpi>40 else '#f43f5e'))
                    wpi_label = "REJECTION SIGNAL" if "SEROK" in s_bandar else ("DISTRIBUTION SIGNAL" if "FAKE" in s_bandar else "WHALE PRESSURE")
                    st.markdown(f"<div class='premium-card' style='padding: 15px; height: 100%; justify-content: center; align-items: center;'><div style='color: #64748b; font-size: 0.7rem; font-weight: 800; letter-spacing: 1px;'>{wpi_label}</div><div style='font-size: 2rem; font-weight: 800; color: {wpi_color}; margin-top: 5px;'>{wpi}%</div></div>", unsafe_allow_html=True)

            else:
                per, pbv, yld = raw_target.get("PER", 0), raw_target.get("PBV", 0), raw_target.get("DIV_YIELD", 0)
                st.markdown(f"<div style='display:flex; justify-content:space-around; background:rgba(30,41,59,0.3); border:1px solid rgba(255,255,255,0.05); border-radius:10px; padding:12px; margin-bottom:15px;'><div style='text-align:center;'><span style='color:#64748b; font-size:0.7rem; font-weight:700;'>VALUASI PER</span><br><span style='color:#f8fafc; font-weight:800; font-size:1.1rem;'>{per:.1f}x</span></div><div style='text-align:center;'><span style='color:#64748b; font-size:0.7rem; font-weight:700;'>VALUASI PBV</span><br><span style='color:#f8fafc; font-weight:800; font-size:1.1rem;'>{pbv:.1f}x</span></div><div style='text-align:center;'><span style='color:#64748b; font-size:0.7rem; font-weight:700;'>DIV YIELD</span><br><span style='color:#10b981; font-weight:800; font-size:1.1rem;'>{yld:.1f}%</span></div></div>", unsafe_allow_html=True)
                with st.spinner("Mengunduh Laporan Keuangan Kuartalan dari Bursa..."):
                    dates, inc_data, bs_data, cf_data = fetch_quarterly_charts(emiten_signal)
                    if dates and len(dates) > 0:
                        tab_i, tab_b, tab_c = st.tabs(["📈 Income Statement", "🏛️ Balance Sheet", "💸 Cash Flow"])
                        with tab_i: st.plotly_chart(plot_luxury_bar(dates, inc_data[0], inc_data[1], "Total Revenue", "Net Income", "#0ea5e9", "#10b981", "Revenue vs Net Income (QoQ)"), use_container_width=True)
                        with tab_b: st.plotly_chart(plot_luxury_bar(dates, bs_data[0], bs_data[1], "Total Assets", "Total Liabilities", "#8b5cf6", "#f43f5e", "Assets vs Liabilities (QoQ)"), use_container_width=True)
                        with tab_c: st.plotly_chart(plot_luxury_bar(dates, cf_data[0], cf_data[1], "Operating Cash Flow", "Free Cash Flow", "#facc15", "#d4af37", "Cash Flow Generation (QoQ)"), use_container_width=True)
                    else: st.markdown("<div style='text-align:center; padding:20px; color:#64748b; font-style:italic;'>⚠️ Data riil kuartalan belum dirilis oleh server bursa untuk emiten ini.</div>", unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR REACTIVE
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #f8fafc; font-size: 1.4rem; font-weight: 800; margin-bottom: -5px;'>Quantum Matrix</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #d4af37; font-size: 0.65rem; letter-spacing: 2px; margin-bottom: 25px;'>v17.0 THE PRESTIGE EDITION</p>", unsafe_allow_html=True)
    
    engine_mode = st.radio("PILIH MODE ENGINE:", ("⚔️ TRADING (Momentum & Reactive)", "🛡️ INVESTMENT (Fundamental)"))
    st.markdown("<br>", unsafe_allow_html=True)

    tf_pilihan = st.selectbox("⏱️ TIMEFRAME:", ("1 Hari (Daily)", "1 Minggu (Weekly)"), index=0)
    tf_berubah = tf_pilihan != st.session_state.current_tf
    if tf_berubah: st.session_state.current_tf = tf_pilihan
        
    profil_risiko = st.selectbox("TINGKAT AGRESIVITAS AI:", ("⚖️ Moderat (Balanced)", "🔥 Agresif (High Signal)"), index=0)
    
    modal_input_str = st.text_input("💰 MODAL TRADING (Rp):", value="50.000.000")
    try: modal_trading = int(modal_input_str.replace(".", "").replace(",", ""))
    except: modal_trading = 50000000
    risiko_pct = st.slider("🚨 BATAS RISIKO (%):", 0.5, 5.0, 1.0, 0.5)

    st.markdown("<br>", unsafe_allow_html=True)
    
    btn_ph = st.empty()
    if btn_ph.button("🔄 SCAN MARKET", use_container_width=True) or tf_berubah:
        btn_ph.empty() 
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.raw_stocks = []
        
        my_bar = st.progress(0, text="Menyiapkan Radar VIP...")
        dyn_tickers = get_dynamic_market_roster()
        for i, t in enumerate(dyn_tickers):
            my_bar.progress((i + 1) / len(dyn_tickers), text=f"Menganalisa Price Action {t} ({i+1}/{len(dyn_tickers)})")
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
        
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🚪 LOGOUT SISTEM", use_container_width=True):
        st.session_state.clear()
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()

# ==========================================
# 6. HEADER DASHBOARD
# ==========================================
st.markdown("<h1>Executive Command Center</h1>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()

c_h1, c_h2, c_h3 = st.columns([2, 1, 1])
with c_h1:
    q = get_quote_of_the_day()
    st.markdown(f"<div style='margin-top:15px;'><span style='color:#d4af37; font-size:0.7rem; font-weight:800; letter-spacing:1px;'>{q['theme'].upper()}</span><br><span style='color:#cbd5e1; font-size:0.9rem; font-style:italic;'>\"{q['quote']}\"</span></div>", unsafe_allow_html=True)
    upd_time = st.session_state.last_update if st.session_state.last_update else "-"
    st.markdown(f"<div style='margin-top:10px; font-size:0.75rem; color:#64748b;'>Sync: {upd_time} | Mode: <span style='color:#d4af37;'>{engine_mode}</span></div>", unsafe_allow_html=True)

with c_h2:
    if ihsg_now:
        w_p, w_g = ("▲", '#10b981') if ihsg_chg >= 0 else ("▼", '#f43f5e')
        st.markdown(f"<div class='ihsg-box' style='border-left:3px solid {w_g}; border-radius:8px;'><span class='ihsg-title'>IHSG</span><span class='ihsg-score'>{ihsg_now:,.0f}</span><span style='color:{w_g}; font-weight:700; font-size:0.8rem;'>{w_p} {ihsg_chg:+,.1f} ({ihsg_pct:+.2f}%)</span></div>", unsafe_allow_html=True)

with c_h3:
    if st.session_state.scan_clicked and st.session_state.raw_stocks:
        up_c = sum(1 for s in st.session_state.raw_stocks if s.get("UP_SMA50", False))
        b_pct = (up_c / len(st.session_state.raw_stocks)) * 100
        c_stat, c_col, c_mult = ("BULLISH", "#10b981", 1.0) if b_pct >= 50 else ("BEARISH", "#f43f5e", 0.5)
        st.markdown(f"<div class='ihsg-box' style='border-left:3px solid {c_col}; border-radius:8px;'><span class='ihsg-title'>CLIMATE</span><span class='ihsg-score' style='color:{c_col};'>{c_stat}</span><span style='color:#64748b; font-weight:700; font-size:0.8rem;'>Breadth: {b_pct:.0f}%</span></div>", unsafe_allow_html=True)
    else: c_mult = 1.0

st.markdown("---")

if not st.session_state.scan_clicked or not st.session_state.raw_stocks:
    st.info("👈 Tekan tombol '🔄 SCAN MARKET' untuk memulai Inisiasi VIP Engine v17.0.")
else:
    h_trd, h_inv = [], []
    c_val, c_gro, c_div = [], [], []
    
    for r in st.session_state.raw_stocks:
        t, h = r.get("TICKER", ""), r.get("HARGA", 0)
        setup_grade = r.get("SETUP_GRADE", "⚠️ SETUP C")
        status_ara = r.get("STATUS_ARA_ARB", "")
        t_stop_val = r.get("TRAILING STOP", 0)
        
        bid_p, ask_p = r.get("BID", 0), r.get("OFFER", 0)
        bid_str = f"{int(bid_p):,}" if bid_p > 0 else "-"
        offer_str = f"{int(ask_p):,}" if ask_p > 0 else "-"
        
        if "REACTIVE" in setup_grade: kep_t, prio, r_mult = "🎯 SEROK BAWAH", 5, 1.5
        elif "A+" in setup_grade: kep_t, prio, r_mult = "🚀 STRONG ACCUM", 4, 2.0
        elif "AGGRESSIVE" in setup_grade: kep_t, prio, r_mult = "⚡ AGGRESSIVE SCALP", 3, 1.5
        elif "B" in setup_grade: kep_t, prio, r_mult = "🟢 ACCUMULATE", 2, 1.0
        elif "AVOID" in setup_grade: kep_t, prio, r_mult = "⚠️ AVOID (FAKE)", 0, 0.0
        else: kep_t, prio, r_mult = "🟡 HOLD", 1, 0.0
        
        risk_ps = h - t_stop_val
        if ("ACCUM" in kep_t or "SCALP" in kep_t or "SEROK" in kep_t) and risk_ps > 0 and "ARA" not in status_ara:
            final_risk = risiko_pct * r_mult * c_mult
            max_lots = int(((modal_trading * (final_risk / 100)) / risk_ps) / 100)
            rec_lot_text = f"Max {max_lots:,} Lot"
        elif "ARA" in status_ara: rec_lot_text = "⚠️ ARA LOCKED (HOLD)"
        elif "AVOID" in kep_t: rec_lot_text = "🚫 Dilarang Masuk"
        else: rec_lot_text = "🔒 Proteksi/Hold"

        wpi_score = r.get('WPI_SCORE', 50)
        s_bandar = r.get("STATUS_BANDAR", "")
        
        if "FAKE" in s_bandar: wpi_text = f"🚫 {wpi_score}% (DISTRIBUSI)"
        elif "SEROK" in s_bandar: wpi_text = f"🎯 {wpi_score}% (REJECTION)"
        elif wpi_score >= 80: wpi_text = f"🐋 {wpi_score}% (POWER)"
        elif wpi_score <= 30: wpi_text = f"🩸 {wpi_score}% (DUMP)"
        else: wpi_text = f"{wpi_score}%"
        
        h_trd.append({
            "PRIORITY": prio, "RAW_WPI": wpi_score, "MAX_LOT": rec_lot_text,
            "TICKER": t, "HARGA": f"{int(h):,}".replace(",", "."), 
            "BID": bid_str, "OFFER": offer_str,
            "1D GAIN (%)": f"{r.get('RET_1D',0):+.2f}%", "RAW_RET": r.get('RET_1D',0),
            "WPI 🐋": wpi_text,
            "REKOMENDASI LOT": rec_lot_text,
            "TRAILING STOP": f"{int(t_stop_val):,}".replace(",", "."),
            "BANDARMOLOGI": s_bandar, "REKOMENDASI": setup_grade, "AREA_BELI": r.get("AREA BELI", h)
        })
        
        per, pbv, peg, yld = r.get("PER", 0), r.get("PBV", 0), r.get("PEG", 0), r.get("DIV_YIELD", 0)
        skor = (20 if 0<per<15 else 0) + (20 if 0<pbv<1.5 else 0) + (20 if yld>4 else 0) + (15 if r.get("UP_SMA50") else 0) + (25 if 0<peg<=1.0 else 0)
        
        h_inv.append({
            "R_YLD": yld, "TICKER": t, "HARGA": f"{int(h):,}".replace(",", "."), "MARKET CAP": format_financials(r.get("MARKET_CAP", 0)),
            "PER (x)": f"{per:.2f}", "PBV (x)": f"{pbv:.2f}", "PEG (x)": f"{peg:.2f}", "DIV YIELD (%)": f"{yld:.2f}%",
            "DIV DATE": r.get("DIVIDEND_DATE", "-"),
            "VALUASI": "💎 UNDERVALUED (GROWTH)" if skor>=70 and 0<peg<=1.0 else ("💎 UNDERVALUED" if skor>=70 else ("⚖️ FAIR VALUE" if skor>=40 else "⚠️ OVERVALUED"))
        })
        
        if 0 < per < 10 and 0 < pbv < 1.0: c_val.append(t)
        if 0 < peg <= 1.0: c_gro.append(t)
        if yld >= 5.0: c_div.append(t)

    # FITUR LUXURY: VIP HIGHLIGHT CARDS
    df_trd_full = pd.DataFrame(h_trd).sort_values(["PRIORITY", "RAW_WPI"], ascending=[False, False]) if h_trd else pd.DataFrame()
    df_inv = pd.DataFrame(h_inv).sort_values("R_YLD", ascending=False).drop(columns=["R_YLD"]).set_index("TICKER").head(15) if h_inv else pd.DataFrame()

    if "TRADING" in engine_mode:
        tab_t1, tab_t2 = st.tabs(["💎 COMMAND CENTER", "📜 REACTIVE SOP"])
        with tab_t1:
            st.markdown("<h3 style='font-size: 1.3rem; color:#d4af37; margin-bottom: 15px;'>👑 Top 3 Elite Picks (Prioritas Eksekusi)</h3>", unsafe_allow_html=True)
            
            if not df_trd_full.empty:
                top_3 = df_trd_full.head(3)
                cols = st.columns(3)
                for idx, row in enumerate(top_3.to_dict('records')):
                    with cols[idx]:
                        tkr, prc, ret, bandar, lot, wpi, ts, area_beli = row['TICKER'], row['HARGA'], row['RAW_RET'], row['BANDARMOLOGI'], row['MAX_LOT'], row['WPI 🐋'], row['TRAILING STOP'], f"{int(row['AREA_BELI']):,}".replace(",", ".")
                        ret_color = "#10b981" if ret >= 0 else "#f43f5e"
                        ret_sign = "+" if ret >= 0 else ""
                        
                        st.markdown(f"""
                        <div class="vip-card">
                            <div>
                                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                    <h2 class="vip-title">{tkr}</h2>
                                    <span style="color:{ret_color}; font-weight:800; font-size:1.1rem;">{ret_sign}{ret:.2f}%</span>
                                </div>
                                <div class="vip-price">Rp {prc}</div>
                                <div class="vip-badge">{bandar.replace('🐋 ', '').replace('🎯 ', '').replace('🚀 ', '')}</div>
                                <div style="margin-top: 8px; font-size: 0.8rem; color: #cbd5e1; font-weight:700;">{wpi}</div>
                            </div>
                            <div class="vip-stat-row">
                                <div class="vip-stat">
                                    <div class="vip-stat-label">Area Beli</div>
                                    <div class="vip-stat-val" style="color:#0ea5e9;">{area_beli}</div>
                                </div>
                                <div class="vip-stat">
                                    <div class="vip-stat-label">Cut Loss</div>
                                    <div class="vip-stat-val" style="color:#f43f5e;">{ts}</div>
                                </div>
                                <div class="vip-stat">
                                    <div class="vip-stat-label">Entry</div>
                                    <div class="vip-stat-val" style="color:#d4af37;">{lot.replace('Max ', '')}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("<br><h3 style='font-size: 1.3rem; color:#f8fafc; margin-top: 20px;'>🛰️ Full Reactive Matrix (Top 15)</h3>", unsafe_allow_html=True)
            
            # Membuang kolom teknis dari tampilan tabel
            df_display = df_trd_full.drop(columns=["PRIORITY", "RAW_WPI", "MAX_LOT", "RAW_RET", "AREA_BELI"]).set_index("TICKER").head(15)
            
            def style_t(row):
                stls = []
                for c, v in row.items():
                    if c in ['BID', 'OFFER']: stls.append('color:#f8fafc; font-weight:800; text-align:center;')
                    elif c == '1D GAIN (%)': stls.append('color:#10b981; font-weight:800; text-align:center;' if '+' in str(v) else ('color:#f43f5e; font-weight:800; text-align:center;' if '-' in str(v) and v!='-0.00%' else 'color:#64748b; text-align:center;'))
                    elif c == 'WPI 🐋': stls.append('color:#f43f5e; font-weight:800;' if '🚫' in str(v) else ('color:#d4af37; font-weight:800;' if '🎯' in str(v) else ('color:#10b981; font-weight:800;' if 'POWER' in str(v) else ('color:#f43f5e; font-weight:800;' if 'DUMP' in str(v) else 'color:#94a3b8;'))))
                    elif c == 'REKOMENDASI LOT': stls.append('color:#00f2fe; font-weight:800;' if 'Max' in str(v) else ('color:#f43f5e; font-weight:800;' if 'Dilarang' in str(v) else 'color:#64748b;'))
                    elif c == 'TRAILING STOP': stls.append('color:#f43f5e; font-weight:800; text-align:center;')
                    elif c == 'REKOMENDASI': stls.append('color:#d4af37; font-weight:800;' if 'REACTIVE' in v else ('color:#f43f5e; font-weight:800;' if 'AVOID' in v else ('color:#10b981; font-weight:800;' if 'A+' in v else ('color:#c4b5fd; font-weight:800;' if 'AGGRESSIVE' in v else ('color:#38bdf8; font-weight:700;' if 'B' in v else 'color:#fb7185;')))))
                    elif c == 'BANDARMOLOGI': stls.append('color:#d4af37; font-weight:800;' if 'SEROK' in v else ('color:#f43f5e; font-weight:800;' if 'FAKE' in v or 'DISTRIBUSI' in v else ('color:#00f2fe; font-weight:800;' if 'AKUMULASI' in v else ('color:#10b981; font-weight:800;' if 'MARK-UP' in v else 'color:#64748b;'))))
                    else: stls.append('color:#cbd5e1;')
                return stls
            
            if not df_display.empty: st.dataframe(df_display.style.apply(style_t, axis=1), use_container_width=True)
            render_cross_validation_ui(tuple(str(x) for x in df_display.index), c_mult, True)
            
        with tab_t2: st.info("SOP REAKTIF v17.0: Fokus pada 3 saham di 'Elite Picks'. Mereka adalah saham dengan prioritas serok bawah terkuat. Jangan sentuh saham berlabel 'FAKE ACCUMULATION' di dalam matriks.")

    else: 
        tab_i1, tab_i2 = st.tabs(["🛡️ LUXURY VALUE MATRIX", "🧬 BEHAVIORAL CLUSTERS"])
        with tab_i1:
            st.markdown("<br><h3 style='font-size: 1.3rem; color:#f8fafc;'>🛡️ Top 15 Dividend & Value</h3>", unsafe_allow_html=True)
            def style_i(row):
                stls = []
                for c, v in row.items():
                    if c == 'DIV YIELD (%)': stls.append('color:#10b981; font-weight:800;' if v!='0.00%' else 'color:#64748b;')
                    elif c in ['PER (x)', 'PBV (x)', 'PEG (x)']:
                        try:
                            f_v = float(v)
                            if (c == 'PER (x)' and 0 < f_v < 15) or (c == 'PBV (x)' and 0 < f_v < 1.2) or (c == 'PEG (x)' and 0 < f_v <= 1.0): stls.append('color: #38bdf8; font-weight: 800;')
                            elif f_v > 20 or f_v > 2.5: stls.append('color: #f43f5e; font-weight: 800;')
                            else: stls.append('color: #cbd5e1;')
                        except: stls.append('color:#cbd5e1;')
                    elif c == 'DIV DATE': stls.append('color:#94a3b8; font-size:0.85rem; text-align:center;')
                    elif c == 'VALUASI': stls.append('color:#0ea5e9; font-weight:800;' if 'UNDER' in v else ('color:#facc15; font-weight:800;' if 'FAIR' in v else 'color:#f43f5e; font-weight:800;'))
                    else: stls.append('color:#cbd5e1;')
                return stls
            if not df_inv.empty: st.dataframe(df_inv.style.apply(style_i, axis=1), use_container_width=True)
            render_cross_validation_ui(tuple(str(x) for x in df_inv.index), c_mult, False)
        
        with tab_i2:
            st.markdown("<br><h3 style='font-size: 1.3rem; color:#f8fafc;'>🧬 Institutional Clusters</h3>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown(f"<div class='premium-card' style='border-top: 3px solid #0ea5e9;'><div style='color:#0ea5e9; font-weight:800;'>💎 DEEP VALUE GEMS</div>{render_badges(c_val, '#0ea5e9')}</div>", unsafe_allow_html=True)
            with col2: st.markdown(f"<div class='premium-card' style='border-top: 3px solid #8b5cf6;'><div style='color:#8b5cf6; font-weight:800;'>🚀 HIGH GROWTH</div>{render_badges(c_gro, '#8b5cf6')}</div>", unsafe_allow_html=True)
            with col3: st.markdown(f"<div class='premium-card' style='border-top: 3px solid #10b981;'><div style='color:#10b981; font-weight:800;'>💰 DIVIDEND KINGS</div>{render_badges(c_div, '#10b981')}</div>", unsafe_allow_html=True)
