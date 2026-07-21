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

warnings.filterwarnings('ignore')

# ==========================================
# 0. SISTEM CACHE & TRACKING
# ==========================================
CACHE_FILE = "jihan_ghina_saham_cache_v15.json"

def load_smart_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                loaded_stocks = cache_data.get("raw_stocks", [])
                if loaded_stocks and isinstance(loaded_stocks, list):
                    if "SETUP_GRADE" not in loaded_stocks[0]:
                        return [], None
                return loaded_stocks, cache_data.get("last_update", None)
        except: pass
    return [], None

if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks, st.session_state.last_update = load_smart_cache()

if "scan_clicked" not in st.session_state: st.session_state.scan_clicked = len(st.session_state.raw_stocks) > 0
if "current_tf" not in st.session_state: st.session_state.current_tf = "1 Hari (Daily)"

# ==========================================
# 1. KONFIGURASI HALAMAN & UI STYLE
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA Ultimate v15.0", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -20%, #0f172a, #020617) !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    h1 { color: #f8fafc; font-weight: 900; letter-spacing: -1.5px; font-size: 2.4rem !important; margin-bottom: 0; text-shadow: 0 4px 20px rgba(0,242,254,0.15); }
    p { color: #94a3b8; font-weight: 300; }
    ::-webkit-scrollbar { width: 6px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(0, 242, 254, 0.4); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0, 242, 254, 1); }
    section[data-testid="stSidebar"] { width: 280px !important; min-width: 280px !important; max-width: 280px !important; background: linear-gradient(180deg, rgba(2,6,23,0.95) 0%, rgba(15,23,42,0.95) 100%) !important; backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.05); }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { font-size: 0.8rem !important; }
    section[data-testid="stSidebar"] label { font-size: 0.75rem !important; font-weight: 700 !important; color: #94a3b8 !important; letter-spacing: 0.5px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: rgba(15,23,42,0.5); padding: 5px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 8px; color: #94a3b8; font-weight: 700; transition: all 0.3s; }
    .stTabs [aria-selected="true"] { background-color: rgba(0,242,254,0.15); color: #00f2fe; border: 1px solid rgba(0,242,254,0.3); }
    .premium-card { background: rgba(30, 41, 59, 0.3); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 14px; padding: 18px; box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5); transition: all 0.3s ease; display: flex; flex-direction: column; }
    .premium-card:hover { transform: translateY(-3px); box-shadow: 0 15px 35px -5px rgba(0, 242, 254, 0.15); border-color: rgba(0, 242, 254, 0.3); }
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 12px 18px !important; background: rgba(15,23,42,0.6); }
    .ihsg-title { color: #94a3b8; font-size: 0.65rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
    .ihsg-score { color: #00f2fe; font-size: 1.6rem; font-weight: 900; line-height: 1.1; margin: 4px 0; text-shadow: 0 0 15px rgba(0,242,254,0.3); }
    div.stButton > button:first-child { background: linear-gradient(90deg, rgba(0,242,254,0.1) 0%, rgba(30,58,138,0.2) 100%) !important; border: 1px solid rgba(0, 242, 254, 0.4) !important; color: #00f2fe !important; border-radius: 8px !important; padding: 10px 15px !important; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); font-weight: 900 !important; font-size: 0.95rem !important; letter-spacing: 1px;}
    div.stButton > button:first-child:hover { background: linear-gradient(90deg, #00f2fe 0%, #3b82f6 100%) !important; color: white !important; transform: translateY(-2px); box-shadow: 0 10px 20px -5px rgba(0, 242, 254, 0.4); border-color: transparent !important; }
    
    .stDataFrame { font-size: 13.5px !important; }
    th.row_heading { color: #00f2fe !important; font-weight: 900 !important; font-size: 1.1rem !important; text-align: center !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CORE ENGINE DATA FETCHING & UI HELPERS
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

def render_badges(tickers, hex_color):
    if not tickers: return "<span style='color:#64748b; font-size:0.8rem; font-style:italic; display:block; margin-top:10px;'>Menunggu pergerakan pasar...</span>"
    res = "<div style='display:flex; flex-wrap:wrap; gap:8px; margin-top:15px;'>"
    for t in tickers: res += f"<span style='background:rgba(0,0,0,0.3); border:1px solid {hex_color}60; border-radius:6px; padding:4px 10px; color:{hex_color}; font-size:0.85rem; font-weight:800; box-shadow: 0 2px 4px rgba(0,0,0,0.3); letter-spacing:0.5px;'>{t}</span>"
    res += "</div>"
    return res

def get_waktu_wib():
    return datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %b %Y - %H:%M:%S WIB")

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
        if df_market.empty: return master_tickers[:100] 
        
        top_gainers = df_market.nlargest(50, 'Change')['Ticker'].tolist()
        top_liquid = df_market.nlargest(30, 'TransVal')['Ticker'].tolist()
        top_volatile = df_market.nlargest(20, 'VolatilityScore')['Ticker'].tolist()
        
        dynamic_roster = list(set(top_gainers + top_liquid + top_volatile))
        return dynamic_roster[:100]
    except Exception as e:
        return master_tickers[:100] 

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
        if "4 Jam" in mode_tf:
            df = df.resample('4h').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna(subset=['Close'])
            
        df = df.ffill() 
        if len(df) < 30: return None 
        
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['MACD'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
        df['Signal'] = df['MACD'].ewm(span=9).mean()
        df['RSI'] = hitung_rsi(df)
        df['ATR'] = hitung_atr(df)
        df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()
        
        # Chandelier Exit
        df['Chandelier_Exit'] = df['High'].rolling(22).max() - (df['ATR'] * 3.0)
        
        df_higher_tf = df.resample('W').agg({'Close':'last'}).dropna() if "Hari" in mode_tf or "Jam" in mode_tf else df
        df_higher_tf['EMA20_HTF'] = df_higher_tf['Close'].ewm(span=20).mean()
        
        harga_skg = float(df['Close'].iloc[-1])
        open_skg = float(df['Open'].iloc[-1])
        high_skg = float(df['High'].iloc[-1])
        low_skg = float(df['Low'].iloc[-1])
        vol_skg = float(df['Volume'].iloc[-1])
        vol_sma20 = float(df['Vol_SMA20'].iloc[-1])
        ema20_skg = float(df['EMA20'].iloc[-1])
        sma50_skg = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else ema20_skg
        
        atr_skg = float(df['ATR'].iloc[-1])
        trailing_stop = float(df['Chandelier_Exit'].iloc[-1])
        if pd.isna(trailing_stop) or trailing_stop >= harga_skg: trailing_stop = harga_skg - (atr_skg * 2) # SAFEGUARD
        
        prev_close = float(df['Close'].iloc[-2])
        ret_1d = ((harga_skg - prev_close) / prev_close * 100) if prev_close > 0 else 0
        
        volatilitas_pct = (atr_skg / harga_skg) * 100 if harga_skg > 0 else 0
        if volatilitas_pct >= 4.0: volatilitas_stat = "🔥 EKSTREM"
        elif volatilitas_pct >= 2.0: volatilitas_stat = "⚡ MODERAT"
        else: volatilitas_stat = "❄️ RENDAH"
        
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
        
        is_vol_spike = vol_skg > (vol_sma20 * 1.5)
        
        if is_vol_spike:
            if lower_shadow > (body_size * 1.5): status_bandar = "🐋 AKUMULASI DASAR"
            elif upper_shadow > (body_size * 1.5): status_bandar = "🩸 DISTRIBUSI PUCUK"
            elif is_bullish: status_bandar = "🚀 MARK-UP BERINGAS"
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
        
        if setup_score >= 6: setup_grade = "⭐ SETUP A+ (ALL OUT)"
        elif setup_score >= 4: setup_grade = "✔️ SETUP B (NORMAL)"
        else: setup_grade = "⚠️ SETUP C (WEAK)"

        # V15.0 FEATURE: Fetch PEG Ratio & Advance Financials
        tkr = yf.Ticker(emiten)
        info = tkr.info if tkr.info else {}
        per_val = info.get('trailingPE', 0.0)
        pbv_val = info.get('priceToBook', 1.0)
        peg_val = info.get('pegRatio') or 0.0  # Menarik rasio Harga terhadap Pertumbuhan Laba
        
        div_rate = info.get('trailingAnnualDividendRate', 0)
        div_yield = (div_rate / harga_skg * 100) if (div_rate and harga_skg > 0) else 0.0
        mcap = info.get('marketCap', 0)
        
        div_date_unix = info.get('exDividendDate', None)
        div_date_str = "-"
        if div_date_unix:
            try: div_date_str = datetime.fromtimestamp(div_date_unix).strftime('%d %b %Y')
            except: pass
            
        return {
            "TICKER": kode, "HARGA": harga_skg, 
            "AREA BELI": ema20_skg if harga_skg > ema20_skg else (low_20 + (harga_skg - low_20)*0.3), 
            "TRAILING STOP": trailing_stop,  
            "VOLATILITAS": volatilitas_stat, 
            "RSI": round(rsi_skg, 2), "RSI_STATUS": rsi_status,          
            "STATUS_BANDAR": status_bandar,    
            "SETUP_GRADE": setup_grade,      
            "IS_VOLCANO": is_volcano,        
            "IS_MTF_BULLISH": is_mtf_bullish,
            "UP_EMA20": harga_skg > ema20_skg, "UP_SMA50": harga_skg > sma50_skg,
            "MACD_GOLDEN": float(df['MACD'].iloc[-1]) > float(df['Signal'].iloc[-1]),
            "PER": round(per_val, 2), "PBV": round(pbv_val, 2), "PEG": round(peg_val, 2), "DIV_YIELD": round(div_yield, 2),
            "RET_1D": ret_1d, "HIGH": high_skg, "LOW": low_skg, "VOLUME": vol_skg, "VOL_SMA20": vol_sma20,
            "MARKET_CAP": mcap, "DIVIDEND_DATE": div_date_str, "TRANS_VAL": harga_skg * vol_skg
        }
    except Exception as e: 
        return None

def format_rupiah(val):
    if pd.isna(val) or val == 0: return "-"
    return f"Rp {val:,.0f}".replace(",", ".")

def format_market_cap(val):
    if pd.isna(val) or val == 0: return "-"
    if val >= 1_000_000_000_000: return f"Rp {val/1_000_000_000_000:.2f} T"
    elif val >= 1_000_000_000: return f"Rp {val/1_000_000_000:.2f} M"
    else: return f"Rp {val/1_000_000:.2f} Jt"

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
# 4. CROSS-VALIDATION UI (TRIPLE BLOCKS)
# ==========================================
def render_cross_validation_ui(active_tickers_tuple, market_climate_mult):
    st.markdown("---")
    st.markdown("""
    <div style="margin-top: 15px; margin-bottom: 20px; padding-left: 5px; border-left: 5px solid #00f2fe;">
        <h3 style="font-size: 1.8rem; font-weight: 900; color: #f8fafc; margin-bottom: 0px; margin-top: 0px; letter-spacing: -0.5px;">🎯 Sniper Cross-Validation (v15)</h3>
        <p style="color: #94a3b8; font-size: 0.85rem; font-weight: 400; margin-top: 4px;">Analisis mendalam dengan <strong style="color:#10b981;">Macro-Climate Auto-Brake</strong> & Trailing Stop.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if active_tickers_tuple and len(active_tickers_tuple) > 0:
        safe_key = f"cv_target_v15_{st.session_state.current_tf}_{engine_mode[:3]}"
        if safe_key in st.session_state and st.session_state[safe_key] not in active_tickers_tuple:
            del st.session_state[safe_key]
            
        emiten_signal = st.selectbox("Pindai Detil Emiten:", options=active_tickers_tuple, key=safe_key)
        
        with st.spinner(f"Membedah anatomi harga {emiten_signal}..."):
            raw_target = next((item for item in st.session_state.raw_stocks if item.get("TICKER") == emiten_signal), None)
            
            if raw_target:
                bd_status = raw_target.get("STATUS_BANDAR", "➖ NEUTRAL")
                rs_status = raw_target.get("RSI_STATUS", "➖ NEUTRAL")
                setup_grade = raw_target.get("SETUP_GRADE", "⚠️ SETUP C")
                harga_tgt = raw_target.get('HARGA', 0)
                
                area_beli = f"{int(raw_target.get('AREA BELI', harga_tgt)):,}".replace(",", ".")
                trailing_stop_val = raw_target.get('TRAILING STOP', harga_tgt * 0.95)
                if trailing_stop_val >= harga_tgt: trailing_stop_val = harga_tgt * 0.98 
                trailing_stop = f"{int(trailing_stop_val):,}".replace(",", ".")
                
                is_volcano = raw_target.get("IS_VOLCANO", False)
                
                if "A+" in setup_grade:
                    sys_rec_raw = "STRONG ACCUMULATE"
                    color = "#10b981"
                    desc = "🔥 <b>SUPER TREND TERDETEKSI:</b> Multi-Timeframe Resonance menyala! Probabilitas cuan bagger sangat tinggi. Beli dan biarkan profit berlari (Let Your Profits Run) sampai menyentuh garis Trailing Stop."
                    risk_multiplier = 2.0 
                elif "B" in setup_grade:
                    sys_rec_raw = "ACCUMULATE"
                    color = "#38bdf8"
                    desc = "🟢 Setup momentum solid. Harga memantul dari dasar dengan bandarmologi mendukung. Cicil bertahap."
                    risk_multiplier = 1.0 
                elif "DISTRIBUSI" in bd_status or "PUCUK" in rs_status:
                    sys_rec_raw = "LIQUIDATE / TAKE PROFIT"
                    color = "#f43f5e"
                    desc = "🩸 <b>WARNING:</b> Indikator menunjuk jenuh beli dan bandar mulai guyur barang. Amankan cash Anda!"
                    risk_multiplier = 0
                else:
                    sys_rec_raw = "HOLD / WAIT"
                    color = "#fbbf24"
                    desc = "⚖️ Market masih bimbang. Jika sudah punya barang, HOLD selama harga di atas Trailing Stop."
                    risk_multiplier = 0
                    
                if is_volcano and "ACCUM" in sys_rec_raw:
                    desc += "<br><br>🌋 <b>VOLCANO ERUPTION:</b> Saham menembus masa tidurnya dengan volume raksasa!"

                # V15 AUTO-BRAKE SYSTEM INJECTION
                final_risk_pct = risiko_pct * risk_multiplier * market_climate_mult
                risk_per_share = harga_tgt - trailing_stop_val
                
                if risk_multiplier > 0 and risk_per_share > 0:
                    max_loss_money = modal_trading * (final_risk_pct / 100)
                    max_lots = int((max_loss_money / risk_per_share) / 100)
                    
                    if market_climate_mult < 1.0:
                        lot_rec_target = f"⚠️ AUTO-BRAKE: Max {max_lots:,} Lot (Risk Dipangkas jadi {final_risk_pct:.1f}%)"
                        desc += "<br><br><i>🚨 CATATAN SISTEM: Mode Defensif Aktif. Lot size Anda dipangkas 50% karena cuaca pasar (IHSG) sedang buruk. Lindungi modal Anda!</i>"
                    else:
                        lot_rec_target = f"Max {max_lots:,} Lot (Risk Optimal {final_risk_pct:.1f}%)" if max_lots > 0 else "Beli Minimal"
                else: 
                    lot_rec_target = "Kunci Profit / Hindari Membeli"
                
                analyst_data_signal = fetch_analyst_consensus(emiten_signal)
                konsensus_raw = analyst_data_signal["Konsensus"].upper()
                
                col_res1, col_res2 = st.columns([1.5, 1])
                with col_res1:
                    st.markdown(f"""
                    <div style='background: rgba(30,41,59,0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px;'>
                        <div style='text-align: center; color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1px;'>💻 DYNAMIC ALGO DECISION</div>
                        <div style='text-align: center; font-size: 1.8rem; font-weight: 900; color: {color}; margin-top: 5px; margin-bottom: 5px;'>{sys_rec_raw}</div>
                        <div style='text-align: center; font-size: 0.9rem; color: #facc15; font-weight: 800; margin-bottom: 15px;'>{setup_grade}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    sub1, sub2, sub3 = st.columns(3)
                    with sub1:
                        st.markdown(f"""
                        <div style='background: rgba(251, 191, 36, 0.05); padding: 12px 8px; border-radius: 10px; border: 1px solid rgba(251, 191, 36, 0.15); text-align: center;'>
                            <div style='font-size: 0.65rem; color: #94a3b8; font-weight: 800;'>HARGA AKTIF</div>
                            <div style='font-size: 1.1rem; color: #facc15; font-weight: 900; margin-top: 4px;'>{int(harga_tgt)}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with sub2:
                        st.markdown(f"""
                        <div style='background: rgba(56, 189, 248, 0.05); padding: 12px 8px; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.15); text-align: center;'>
                            <div style='font-size: 0.65rem; color: #94a3b8; font-weight: 800;'>AREA BELI (SUPP)</div>
                            <div style='font-size: 1.1rem; color: #38bdf8; font-weight: 900; margin-top: 4px;'>{area_beli}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with sub3:
                        st.markdown(f"""
                        <div style='background: rgba(244, 63, 94, 0.05); padding: 12px 8px; border-radius: 10px; border: 1px solid rgba(244, 63, 94, 0.15); text-align: center;'>
                            <div style='font-size: 0.65rem; color: #94a3b8; font-weight: 800;'>TRAILING STOP</div>
                            <div style='font-size: 1.1rem; color: #f43f5e; font-weight: 900; margin-top: 4px;'>{trailing_stop}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                with col_res2:
                    st.markdown(f"""
                    <div style='background: rgba(30,41,59,0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;'>
                        <div style='text-align: center; color: #94a3b8; font-size: 0.8rem; font-weight: 800; letter-spacing: 1px;'>🌍 GLOBAL ANALYST</div>
                        <div style='text-align: center; font-size: 1.6rem; font-weight: 900; color: #f8fafc; margin-top: 5px;'>{konsensus_raw if konsensus_raw != 'N/A' else 'UNAVAILABLE'}</div>
                        <div style='font-size: 0.7rem; color: #64748b; text-align: center; margin-top: 8px;'>Agregasi Institusi Global</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='margin-top: 20px; background: rgba(15, 23, 42, 0.8); border: 1px solid {color}50; border-radius: 14px; padding: 25px; text-align: center; box-shadow: 0 10px 30px -10px {color}30;'>
                    <div style='color: {color}; font-size: 0.8rem; font-weight: 900; letter-spacing: 3px; margin-bottom: 8px; text-transform: uppercase;'>🏆 V15 INSTITUTIONAL SIZING</div>
                    <div style='color: #cbd5e1; font-size: 0.95rem; font-weight: 300; max-width: 750px; margin: 0 auto; line-height: 1.6; margin-bottom: 20px;'>{desc}</div>
                    <div>
                        <span style='background: linear-gradient(90deg, rgba(0,242,254,0.1) 0%, rgba(30,58,138,0.2) 100%); border: 1px solid #00f2fe60; padding: 12px 30px; border-radius: 30px; color: #00f2fe; font-size: 1rem; font-weight: 900; display: inline-block;'>🎯 KEKUATAN BELI: {lot_rec_target}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR (DUAL CORE CONTROL)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #00f2fe; font-size: 1.25rem; font-weight: 900; margin-bottom: 0px;'>🧬 QUANTUM MATRIX</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.65rem; letter-spacing: 1.5px; margin-bottom: 25px;'>INSTITUTIONAL EDITION v15.0</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='font-size:0.75rem; color:#facc15; font-weight:800; letter-spacing:1px; border-bottom: 1px solid rgba(250,204,21,0.2); padding-bottom: 5px; margin-bottom: 10px;'>🎛️ CORE ENGINE MODE</div>", unsafe_allow_html=True)
    engine_mode = st.radio("Pilih Mode Analisis:", ("⚔️ TRADING (Momentum & Technical)", "🛡️ INVESTMENT (Value & Fundamental)"))
    st.markdown("<br>", unsafe_allow_html=True)

    tf_pilihan = st.selectbox("⏱️ Timeframe Analisis:", ("1 Hari (Daily)", "1 Minggu (Weekly)"), index=0)
    tf_berubah = tf_pilihan != st.session_state.current_tf
    if tf_berubah: st.session_state.current_tf = tf_pilihan
        
    st.markdown("<div style='font-size:0.7rem; color:#00f2fe; font-weight:800; letter-spacing:1px; margin-top:20px; border-bottom: 1px solid rgba(0,242,254,0.2); padding-bottom: 5px;'>🎯 RISK PROFILE ENGINE</div>", unsafe_allow_html=True)
    profil_risiko = st.selectbox("Tingkat Agresivitas AI:", ("⚖️ Moderat (Balanced)", "🔥 Agresif (High Signal)", "🛡️ Konservatif (Strict)"), index=0)
    
    st.markdown("<div style='font-size:0.7rem; color:#00f2fe; font-weight:800; letter-spacing:1px; margin-top:20px; border-bottom: 1px solid rgba(0,242,254,0.2); padding-bottom: 5px;'>⚙️ POSITION SIZING</div>", unsafe_allow_html=True)
    modal_input_str = st.text_input("💰 Modal Trading (Rp):", value="50.000.000")
    try: modal_trading = int(modal_input_str.replace(".", "").replace(",", ""))
    except: modal_trading = 50000000
    risiko_pct = st.slider("🚨 Batas Risiko Normal /Trade (%):", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔄 SCAN REAL-TIME MARKET", use_container_width=True) or tf_berubah:
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.page_matrix = 0 
        st.session_state.raw_stocks = []
        
        radar_bar = st.progress(0, text="📡 Radar Sapu Jagat: Mencari Saham Bergejolak Hari Ini...")
        dynamic_tickers = get_dynamic_market_roster()
        radar_bar.empty()
        
        my_bar = st.progress(0, text=f"Deep Scanning {len(dynamic_tickers)} Trending Emiten ({st.session_state.current_tf})...")
        for i, t in enumerate(dynamic_tickers):
            my_bar.progress((i + 1) / len(dynamic_tickers), text=f"Menganalisis Anatomi {t} ({i+1}/{len(dynamic_tickers)})")
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
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.akses_diberikan = False
        st.session_state.scan_clicked = False
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()

# ==========================================
# 6. HEADER DASHBOARD & MULTI-TABS
# ==========================================
st.markdown("<h1>🌐 Algorithmic Market Intelligence</h1>", unsafe_allow_html=True)

# V15.0 FEATURE: Menghitung Macro Market Climate
uptrend_count = sum(1 for s in st.session_state.raw_stocks if s.get("UP_SMA50", False)) if "raw_stocks" in st.session_state and st.session_state.raw_stocks else 0
total_scanned = len(st.session_state.raw_stocks) if "raw_stocks" in st.session_state and st.session_state.raw_stocks else 1
breadth_pct = (uptrend_count / total_scanned) * 100

if breadth_pct >= 55:
    climate_status, climate_icon, climate_color, climate_mult = "RISK ON (BULLISH)", "🌞", "#10b981", 1.0
elif breadth_pct >= 40:
    climate_status, climate_icon, climate_color, climate_mult = "NEUTRAL (SIDEWAYS)", "⚖️", "#fbbf24", 1.0
else:
    climate_status, climate_icon, climate_color, climate_mult = "RISK OFF (BEARISH)", "⛈️", "#f43f5e", 0.5 # Potong Lot 50%

col_h1, col_h2, col_h3 = st.columns([2.5, 1.25, 1.25])
with col_h1:
    upd_time = st.session_state.last_update if st.session_state.last_update else "Menunggu inisiasi radar..."
    tema_warna = "#facc15" if "TRADING" in engine_mode else "#10b981"
    st.markdown(f"<p style='font-size: 0.95rem; margin-top:5px;'>🕒 Last Market Sync: <strong style='color:#00f2fe;'>{upd_time}</strong><br>Sistem Beroperasi Dalam Mode: <strong style='color:{tema_warna};'>{engine_mode}</strong></p>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()
with col_h2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_garis = '#10b981' if ihsg_chg >= 0 else '#f43f5e'
        st.markdown(f"""
        <div class="premium-card ihsg-box" style="border-left: 5px solid {warna_garis}; height:100%;">
            <span class="ihsg-title">IHSG COMPOSITE</span>
            <span class="ihsg-score">{ihsg_now:,.2f}</span>
            <span style="color: {warna_garis}; font-weight: 800; font-size: 0.95rem;">{warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

with col_h3:
    if st.session_state.scan_clicked:
        st.markdown(f"""
        <div class="premium-card ihsg-box" style="border-left: 5px solid {climate_color}; height:100%;">
            <span class="ihsg-title">MARKET CLIMATE (BREADTH)</span>
            <span class="ihsg-score" style="color:{climate_color};">{climate_icon} {climate_status}</span>
            <span style="color: #94a3b8; font-weight: 800; font-size: 0.75rem; margin-top:2px;">{breadth_pct:.1f}% Saham Uptrend</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

if not st.session_state.scan_clicked or not st.session_state.raw_stocks:
    st.info("👈 Sistem terminal siaga. Tekan tombol '🔄 SCAN REAL-TIME MARKET' di panel kiri untuk mendeteksi saham potensial hari ini.")
else:
    hasil_trading = []
    hasil_invest = []
    
    cluster_volcano = []
    cluster_scalp = []
    cluster_accum = []
    
    for raw in st.session_state.raw_stocks:
        up_ema20 = raw.get("UP_EMA20", False)
        up_sma50 = raw.get("UP_SMA50", False)
        rs_status = raw.get("RSI_STATUS", "➖ NEUTRAL")
        bd_status = raw.get("STATUS_BANDAR", "➖ NEUTRAL")
        setup_grade = raw.get("SETUP_GRADE", "⚠️ SETUP C")
        is_volcano = raw.get("IS_VOLCANO", False)
        
        harga = raw.get("HARGA", 0)
        trailing_stop_val = raw.get("TRAILING STOP", harga * 0.95)
        if trailing_stop_val >= harga: trailing_stop_val = harga * 0.98
        
        ret_1d = raw.get("RET_1D", 0.0)
        per_val = raw.get("PER", 0.0)
        pbv_val = raw.get("PBV", 1.0)
        peg_val = raw.get("PEG", 0.0) # V15.0 Fetch PEG
        div_yield = raw.get("DIV_YIELD", 0.0)
        div_date = raw.get("DIVIDEND_DATE", "-")
        mcap = raw.get("MARKET_CAP", 0)
        ticker = raw.get("TICKER", "-")
        
        trans_val = raw.get("TRANS_VAL", 0)
        vol_sma20 = raw.get("VOL_SMA20", 0)
        volume = raw.get("VOLUME", 0)

        if "A+" in setup_grade: kep_t = "🚀 STRONG ACCUM"
        elif "B" in setup_grade: kep_t = "🟢 ACCUMULATE"
        elif "DISTRIBUSI" in bd_status: kep_t = "🔴 LIQUIDATE"
        else: kep_t = "🟡 HOLD"
        
        risk_per_share = harga - trailing_stop_val
        if ("ACCUM" in kep_t) and risk_per_share > 0:
            multiplier = 2.0 if "A+" in setup_grade else 1.0
            # V15: Climate multiplier applied
            final_risk = risiko_pct * multiplier * climate_mult
            max_lots = int(((modal_trading * (final_risk / 100)) / risk_per_share) / 100)
            if climate_mult < 1.0: rec_lot_text = f"⚠️ Max {max_lots:,} Lot (Brake)"
            else: rec_lot_text = f"Max {max_lots:,} Lot"
        else: rec_lot_text = "🔒 Proteksi/Hold"

        # V15.0 Refined Investment Score with PEG
        skor_i = 0
        if 0 < per_val < 15: skor_i += 20
        if 0 < pbv_val < 1.5: skor_i += 20
        if div_yield > 4.0: skor_i += 20
        if up_sma50: skor_i += 15
        if 0 < peg_val <= 1.0: skor_i += 25 # Canslim / Growth value
        
        if skor_i >= 70: kep_i = "💎 UNDERVALUED (GROWTH)" if (0 < peg_val <= 1.0) else "💎 UNDERVALUED"
        elif skor_i >= 40: kep_i = "⚖️ FAIR VALUE"
        else: kep_i = "⚠️ OVERVALUED"
            
        hasil_trading.append({
            "RAW_RET": ret_1d, "TICKER": ticker, "HARGA": f"{int(harga):,}".replace(",", "."), "1D GAIN (%)": f"{ret_1d:+.2f}%",
            "REKOMENDASI LOT": rec_lot_text, "TRAILING STOP": f"{int(trailing_stop_val):,}".replace(",", "."),
            "BANDARMOLOGI (SUPPLY/DEMAND)": bd_status, "REKOMENDASI": setup_grade
        })
        
        hasil_invest.append({
            "RAW_YIELD": div_yield, "TICKER": ticker, "HARGA": f"{int(harga):,}".replace(",", "."), "MARKET CAP": format_market_cap(mcap),
            "PER (x)": f"{per_val:.2f}", "PBV (x)": f"{pbv_val:.2f}", "PEG (x)": f"{peg_val:.2f}", "DIV YIELD (%)": f"{div_yield:.2f}%",
            "DIV DATE": str(div_date), "VALUASI": kep_i
        })
        
        if is_volcano: cluster_volcano.append(ticker)
        if (1 < ret_1d < 10) and (trans_val > 2_000_000_000) and (harga < 3000) and (volume > 50_000_000): cluster_scalp.append(ticker)
        if "AKUMULASI" in bd_status or "MARK-UP" in bd_status: cluster_accum.append(ticker)

    df_trading = pd.DataFrame(hasil_trading)
    if not df_trading.empty:
        df_trading = df_trading.sort_values(by="RAW_RET", ascending=False).reset_index(drop=True).drop(columns=["RAW_RET"])
        df_trading.set_index("TICKER", inplace=True)
        
    df_invest = pd.DataFrame(hasil_invest)
    if not df_invest.empty:
        df_invest = df_invest.sort_values(by="RAW_YIELD", ascending=False).reset_index(drop=True).drop(columns=["RAW_YIELD"])
        df_invest.set_index("TICKER", inplace=True)

    top_trading_tickers = tuple(str(x) for x in df_trading.index[:20]) if not df_trading.empty else ()
    top_invest_tickers = tuple(str(x) for x in df_invest.index[:20]) if not df_invest.empty else ()

    if "TRADING" in engine_mode:
        tab1, tab2, tab3 = st.tabs(["🚀 TRADING SIGNAL (TOP GAINERS)", "🧬 VOLATILITY CLUSTERS", "📚 V15 ACADEMY"])
        
        with tab1:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🛰️ Institutional Trading Matrix (Dynamic Roster)</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color:#94a3b8; font-size:0.75rem;'>💡 <i>Geser tabel ke kiri/kanan untuk melihat data. Jika Market Climate 'RISK OFF', lot rekomendasi ditebang 50% otomatis.</i></p>", unsafe_allow_html=True)
            
            def style_trading(row):
                styles = []
                if 'A+' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(16, 185, 129, 0.15); color: #10b981; font-weight:900;'
                elif 'B' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(56, 189, 248, 0.12); color: #38bdf8;'
                else: bg_rek = 'background-color: rgba(244, 63, 94, 0.12); color: #fb7185;'
                
                for c, val in row.items():
                    if c == '1D GAIN (%)':
                        if '+' in str(val): styles.append('color: #10b981; font-weight: 900; background: rgba(16,185,129,0.1); text-align:center;')
                        elif '-' in str(val) and val != '-0.00%': styles.append('color: #f43f5e; font-weight: 900; text-align:center;')
                        else: styles.append('color: #94a3b8; text-align:center;')
                    elif c == 'REKOMENDASI LOT':
                        if '⚠️' in str(val): styles.append('color: #f43f5e; font-weight: 900; background-color: rgba(244,63,94,0.1);')
                        elif 'Max' in str(val): styles.append('color: #facc15; font-weight: 900; background-color: rgba(250,204,21,0.08);')
                        else: styles.append('color: #64748b; font-weight: 400;')
                    elif c == 'TRAILING STOP': styles.append('color: #f43f5e; font-weight: 800; background: rgba(244,63,94,0.05); text-align:center;')
                    elif c == 'REKOMENDASI': styles.append(bg_rek)
                    elif c == 'BANDARMOLOGI (SUPPLY/DEMAND)':
                        if 'AKUMULASI' in str(val): styles.append('color: #00f2fe; font-weight: 800; background: rgba(0,242,254,0.1);')
                        elif 'DISTRIBUSI' in str(val): styles.append('color: #f43f5e; font-weight: 800; background: rgba(244,63,94,0.1);')
                        elif 'MARK-UP' in str(val): styles.append('color: #10b981; font-weight: 800;')
                        else: styles.append('color: #94a3b8;')
                    else: styles.append('')
                return styles

            if not df_trading.empty:
                st.dataframe(df_trading.head(20).style.apply(style_trading, axis=1), use_container_width=True)
            
            render_cross_validation_ui(top_trading_tickers, climate_mult)

        with tab2:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🧬 Behavioral Trading Clusters</h3>", unsafe_allow_html=True)
            c_ara, c_scalp, c_accum = st.columns(3)
            with c_ara:
                badges_volcano = render_badges(cluster_volcano, "#f43f5e")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #f43f5e; height: 100%;'>
                    <div style='color:#f43f5e; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>🌋 1. VOLCANO ERUPTION</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>VCP Breakout. Saham yang lama tidur kini meledak dengan volume >300%. Fase Mark-up dimulai!</div>
                    {badges_volcano}
                </div>
                """, unsafe_allow_html=True)
            with c_scalp:
                badges_scalp = render_badges(cluster_scalp, "#00f2fe")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #00f2fe; height: 100%;'>
                    <div style='color:#00f2fe; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>⚡ 2. SCALPING DAILY</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Saham dengan volatilitas liar dan perputaran uang miliaran harian. Cocok untuk Day Trade.</div>
                    {badges_scalp}
                </div>
                """, unsafe_allow_html=True)
            with c_accum:
                badges_accum = render_badges(cluster_accum, "#10b981")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #10b981; height: 100%;'>
                    <div style='color:#10b981; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>🐋 3. PAUS TERDETEKSI</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Harga ditutup kuat (Mark-up) atau ditarik naik dari bawah (Akumulasi Rejection).</div>
                    {badges_accum}
                </div>
                """, unsafe_allow_html=True)

    else:
        tab1, tab2 = st.tabs(["🛡️ VALUE & GROWTH MATRIX", "📚 V15 ACADEMY"])
        
        with tab1:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🛡️ Institutional Investment Matrix (Sorted by Yield)</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color:#94a3b8; font-size:0.75rem;'>💡 <i>Kini dilengkapi dengan fitur <b>PEG Ratio</b> untuk mendeteksi saham yang murah dan labanya bertumbuh pesat (Growth/CANSLIM).</i></p>", unsafe_allow_html=True)
            
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
                st.dataframe(df_invest.head(20).style.apply(style_invest, axis=1), use_container_width=True)
            
            render_cross_validation_ui(top_invest_tickers, climate_mult)

    with (tab3 if "TRADING" in engine_mode else tab2):
        st.markdown("<br><h3 style='font-size: 1.5rem; text-align: center;'>📚 Institutional Academy v15.0</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;'>Panduan fitur-fitur level pro-trader Wall Street.</p>", unsafe_allow_html=True)
        
        with st.expander("📖 1. Sistem Auto-Brake (Kesehatan Pasar / Breadth) — BARU"):
            st.markdown("""
            **Lihat Kotak 'MARKET CLIMATE' di Atas Kanan!**
            *   Jika pasar berstatus **🌞 RISK ON (BULLISH)**: Berarti IHSG sedang sehat. Mesin mengizinkan Anda menggunakan 100% dari Lot Sizing Anda. Gas penuh!
            *   Jika pasar berstatus **⛈️ RISK OFF (BEARISH)**: Mayoritas saham di bursa sedang hancur. Mesin akan mengaktifkan *Auto-Brake* dan memangkas ukuran lot rekomendasi Anda **sebanyak 50%**. Jangan melawan pasar, selamatkan modal Anda!
            """)
        with st.expander("📖 2. Misteri PEG Ratio (Growth Investing) — BARU"):
            st.markdown("""
            **Murah saja tidak cukup. Saham murah yang labanya turun = Value Trap.**
            Kini, di Tab Investment, Anda akan melihat kolom **PEG (Price/Earnings-to-Growth)**.
            *   **PEG < 1.0 (Warna Biru):** Ini adalah permata tersembunyi! Harganya murah, DAN labanya sedang bertumbuh pesat.
            *   Jika mesin mendeteksi ini, ia akan memberi gelar eksklusif: **💎 UNDERVALUED (GROWTH)**. Beli dan simpan!
            """)
        with st.expander("📖 3. Studi Kasus: Fundamental Bagus tapi Sinyal HOLD/WEAK?"):
            st.markdown("""
            **Kenapa di tabel Investment statusnya 'Fair Value / Undervalued', tapi di Sniper statusnya 'HOLD / SETUP C (Weak)'?**
            *   **Otak Fundamental:** Menilai apakah harga saham wajar berdasarkan laporan keuangan.
            *   **Otak Technical & Bandarmologi:** Menilai apakah *hari ini* ada **uang besar (Paus)** yang menggerakkan harga.
            **Kesimpulan:** Jika saham Undervalued tapi statusnya HOLD, artinya saham itu **Bagus, tapi bandar belum masuk**. Tunggu sampai mesin mendeteksi momentum (berubah menjadi SETUP B atau A+), barulah kita serok! 
            """)
        with st.expander("📖 4. Cara Kerja Trailing Stop (Let Your Profits Run)"):
            st.markdown("""
            **Jangan buang barang Anda jika saham sedang uptrend gila-gilaan!** 
            Target TP statis sudah dibuang. Selama harga saham hari ini *masih di atas* angka Trailing Stop (garis merah), **HOLD TERUS**. Anda baru boleh Take Profit/Cut Loss saat harga ditutup menjebol Trailing Stop tersebut.
            """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem; font-weight:600; letter-spacing: 1px;'>⚡ JIHAN-GHINA ENGINE • INSTITUTIONAL MASTERPIECE v15.0</p>", unsafe_allow_html=True)
