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
CACHE_FILE = "jihan_ghina_saham_cache_v188.json"

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

if "current_tf" not in st.session_state: st.session_state.current_tf = "1 Hari"

# ==========================================
# 1. KONFIGURASI HALAMAN & MOBILE UI (v18.8)
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA v18.8 - Ultimate Investor", page_icon="💎", layout="wide")

st.markdown("""
<style>
    /* UPGRADE FONT: OUTFIT (LUXURY, MODERN, ELEGANT) */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; scroll-behavior: smooth; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -10%, #060d1a, #02040a) !important; color: #f8fafc !important; overflow-x: hidden; }
    [data-testid="stHeader"] { background: transparent !important; height: 0px !important; }
    
    .block-container { padding-top: 1rem !important; padding-bottom: 1.5rem !important; padding-left: 0.6rem !important; padding-right: 0.6rem !important; max-width: 100% !important; animation: fadeIn 0.3s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    
    h1 { color: #f8fafc; font-weight: 900; letter-spacing: -0.5px; font-size: 1.4rem !important; margin-bottom: 0; text-shadow: 0 2px 10px rgba(0,242,254,0.15); }
    
    ::-webkit-scrollbar { width: 3px; height: 3px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.8); }
    ::-webkit-scrollbar-thumb { background: rgba(0, 242, 254, 0.3); border-radius: 10px; }
    
    /* MINIMIZE / TOGGLE SIDEBAR BUTTON */
    [data-testid="collapsedControl"] {
        background-color: rgba(15, 23, 42, 0.95) !important; border: 1px solid rgba(0, 242, 254, 0.5) !important;
        border-radius: 50% !important; box-shadow: 0 0 12px rgba(0, 242, 254, 0.3) !important;
        top: 0.8rem !important; left: 0.8rem !important; width: 2.5rem !important; height: 2.5rem !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; z-index: 1000 !important;
    }
    [data-testid="collapsedControl"] svg { fill: #00f2fe !important; color: #00f2fe !important; width: 1.4rem !important; height: 1.4rem !important; }
    
    /* MODULAR CARD DESIGN */
    .stocksly-card { background: linear-gradient(145deg, rgba(15,23,42,0.85) 0%, rgba(10,15,30,0.95) 100%); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 10px; box-shadow: 0 4px 12px -4px rgba(0, 0, 0, 0.5); display: flex; flex-direction: column; justify-content: space-between; height: 100%; position: relative; overflow: hidden; }
    .card-title { font-size: 0.7rem; font-weight: 800; color: #64748b; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; display: flex; align-items: center; gap: 4px; }
    
    /* VIP HIGHLIGHT CARDS */
    .vip-card { background: linear-gradient(145deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.9) 100%); backdrop-filter: blur(10px); border: 1px solid rgba(0, 242, 254, 0.2); border-radius: 8px; padding: 5px 8px; position: relative; overflow: hidden; display: flex; flex-direction: column; height: auto;}
    .vip-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: linear-gradient(90deg, #00f2fe, #38bdf8, #00f2fe); }
    .vip-title { font-size: 0.95rem; font-weight: 900; color: #f8fafc; margin: 0; line-height: 1;}
    .vip-price { font-size: 0.8rem; font-weight: 900; margin: 0; }
    .vip-badge { background: rgba(0, 242, 254, 0.15); color: #00f2fe; padding: 2px 5px; border-radius: 3px; font-size: 0.5rem; font-weight: 800; border: 1px solid rgba(0, 242, 254, 0.4);}
    .vip-stat-row { display: flex; justify-content: space-between; margin-top: 5px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.05); }
    .vip-stat { text-align: center; }
    .vip-stat-label { font-size: 0.45rem; color: #64748b; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
    .vip-stat-val { font-size: 0.65rem; font-weight: 900; margin-top: 1px; }
    
    /* SIDEBAR 150PX STRICT */
    section[data-testid="stSidebar"] { width: 150px !important; min-width: 150px !important; max-width: 150px !important; background: linear-gradient(180deg, rgba(2,6,23,0.98) 0%, rgba(15,23,42,0.98) 100%) !important; border-right: 1px solid rgba(255, 255, 255, 0.03); padding-top: 0.8rem !important;}
    section[data-testid="stSidebar"] .stMarkdown h2 { font-size: 0.9rem !important; margin-bottom: -5px !important; font-weight: 800; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { font-size: 0.6rem !important; }
    
    /* RADIO BUTTONS GRID (5 COLUMNS x 3 ROWS) - HANYA UNTUK MAIN BLOCK */
    .block-container div[role="radiogroup"] { display: grid !important; grid-template-columns: repeat(5, minmax(0, 1fr)) !important; gap: 6px !important; justify-items: start !important; align-items: center !important; width: 100% !important; }
    .block-container div[role="radiogroup"] > label { background: rgba(255, 255, 255, 0.02) !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; padding: 6px 8px !important; border-radius: 6px !important; width: 100% !important; transition: all 0.2s ease-in-out !important; margin: 0 !important; }
    .block-container div[role="radiogroup"] > label:hover { border-color: rgba(0, 242, 254, 0.4) !important; background: rgba(0, 242, 254, 0.05) !important; }
    .block-container div[role="radiogroup"] p { font-size: 0.65rem !important; font-weight: 800 !important; color: #cbd5e1 !important; margin: 0 !important; }

    /* IHSG BOXES */
    .ihsg-box { display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 8px 10px !important; background: linear-gradient(135deg, rgba(15,23,42,0.7) 0%, rgba(30,41,59,0.4) 100%); border-radius: 6px; }
    .ihsg-title { color: #64748b; font-size: 0.55rem; font-weight: 800; letter-spacing: 0.5px; }
    .ihsg-score { color: #f8fafc; font-size: 1.05rem; font-weight: 900; line-height: 1.1; margin: 2px 0; }
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE QUOTES & SOP CONTENT
# ==========================================
QUOTES_DATABASE = [
    {"quote": "Disiplin eksekusi melahirkan profit konsisten.", "author": "Quant SOP", "theme": "Discipline"},
    {"quote": "Ekor lilin di support adalah jejak akumulasi nyata.", "author": "Price Action", "theme": "Rejection"}
]
def get_quote_of_the_day(): return QUOTES_DATABASE[datetime.now(pytz.timezone('Asia/Jakarta')).timetuple().tm_yday % len(QUOTES_DATABASE)]

# ==========================================
# 3. CORE ENGINE (REALIST v16.6 - ANTI BONCOS)
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

def get_waktu_wib(): return datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d %b - %H:%M")

def format_financials(val):
    if pd.isna(val) or val == 0: return "-"
    if val >= 1_000_000_000_000 or val <= -1_000_000_000_000: return f"{val/1_000_000_000_000:.1f} T"
    elif val >= 1_000_000_000 or val <= -1_000_000_000: return f"{val/1_000_000_000:.1f} M"
    else: return f"{val/1_000_000:.1f} Jt"

def render_badges(tickers, hex_color):
    if not tickers: return "<span style='color:#475569; font-size:0.6rem; font-style:italic;'>Kosong</span>"
    res = "<div style='display:flex; flex-wrap:wrap; gap:5px; margin-top:5px;'>"
    for t in tickers: res += f"<span style='background:rgba(0,0,0,0.2); border:1px solid {hex_color}40; border-radius:3px; padding:2px 5px; color:{hex_color}; font-size:0.6rem; font-weight:700;'>{t}</span>"
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
        status_ara = "🚀 ARA" if h_skg >= (b_ara * 0.99) else ("🩸 ARB" if h_skg <= (b_arb * 1.01) else "➖")
        wpi_score = ((h_skg - lo_skg) / (hi_skg - lo_skg)) * 100 if hi_skg > lo_skg else 50.0
        
        t_stop = float(df['High'].rolling(22).max().iloc[-1]) - (atr * 3.0)
        if pd.isna(t_stop) or t_stop >= h_skg: t_stop = h_skg - (atr * 2) 
        
        is_bull = h_skg >= o_skg
        b_size, u_shadow, l_shadow = abs(o_skg - h_skg), hi_skg - (h_skg if is_bull else o_skg), (o_skg if is_bull else h_skg) - lo_skg
        is_spike = v_skg > (vol_sma20 * 1.2)
        
        info = yf.Ticker(emiten).info or {}
        bid_price = info.get('bid', 0)
        ask_price = info.get('ask', 0)
        
        low_20 = float(df['Low'].tail(20).min())
        dist_to_low = ((h_skg - low_20) / low_20) * 100
        is_near_support = dist_to_low < 5.0 
        is_vol_dry = v_skg < (vol_sma20 * 0.8) 
        is_hammer = l_shadow > (b_size * 2) and l_shadow > u_shadow
        is_fake_accum = not is_bull and wpi_score < 35 and prev_c > ema20
        
        if is_near_support and is_hammer: s_bandar = "🎯 SEROK BAWAH"
        elif is_near_support and is_vol_dry: s_bandar = "🔍 VOL DRY"
        elif is_fake_accum: s_bandar = "⚠️ FAKE (GUYUR)"
        elif is_spike:
            if l_shadow > (b_size * 1.5): s_bandar = "🐋 AKUM DASAR"
            elif u_shadow > (b_size * 1.5): s_bandar = "🩸 DISTRIBUSI"
            elif is_bull and wpi_score > 70: s_bandar = "🚀 MARK-UP"
            elif is_bull: s_bandar = "🟢 AKUM AWAL"
            else: s_bandar = "💥 MARK-DOWN"
        else: s_bandar = "➖ SEPI"
            
        score = sum([h_skg > ema20, wpi_score > 85, is_spike]) * 2 + (3 if v_skg > vol_sma20*3 and h_skg >= float(df['High'].tail(20).max()) else 0)
        
        if "SEROK" in s_bandar: grade = "🎯 SETUP REACTIVE"
        elif "FAKE" in s_bandar: grade = "⚠️ AVOID"
        elif score >= 6 and wpi_score >= 70: grade = "⭐ SETUP A+" 
        elif score >= 4 and wpi_score >= 80: grade = "⚡ SCALP"
        elif score >= 2: grade = "✔️ SETUP B"
        else: grade = "⚠️ SETUP C"

        vol_ratio = v_skg / vol_sma20 if vol_sma20 > 0 else 1
        sm_raw_score = (wpi_score * 0.5) + (min(vol_ratio, 2.5) * 20)
        sm_score_val = min(int(sm_raw_score), 99)
        
        if wpi_score >= 60 and v_skg > vol_sma20: 
            sm_text = "INFLOW"
            sm_col = "#10b981"
        elif wpi_score < 40: 
            sm_text = "OUTFLOW"
            sm_col = "#f43f5e"
        else: 
            sm_text = "NEUTRAL"
            sm_col = "#facc15"

        target_low = info.get('targetLowPrice') or 0
        target_mean = info.get('targetMeanPrice') or 0
        target_high = info.get('targetHighPrice') or 0
        
        if target_low == 0 or target_mean == 0 or target_high == 0:
            target_low = max(int(h_skg * 0.90), int(t_stop))
            target_mean = int(h_skg + (atr * 2.5))
            target_high = int(h_skg + (atr * 5.0))

        full_company_name = info.get('longName') or info.get('shortName') or kode

        return {
            "TICKER": kode, "HARGA": h_skg, "AREA BELI": ema20 if h_skg > ema20 else (low_20 + (h_skg - low_20)*0.3), 
            "TRAILING STOP": t_stop, "WPI_SCORE": round(wpi_score, 1), "BATAS_ARA": b_ara, "STATUS_ARA_ARB": status_ara, 
            "STATUS_BANDAR": s_bandar, "SETUP_GRADE": grade, "UP_SMA50": h_skg > sma50, 
            "SM_TEXT": sm_text, "SM_SCORE": sm_score_val, "SM_COLOR": sm_col,
            "TGT_LOW": target_low, "TGT_MEAN": target_mean, "TGT_HIGH": target_high,
            "PER": round(info.get('trailingPE', 0), 2), "PBV": round(info.get('priceToBook', 1), 2), "PEG": round(info.get('pegRatio') or 0, 2), 
            "ROE": round(info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0, 2),
            "DIV_YIELD": round((info.get('trailingAnnualDividendRate', 0) / h_skg * 100) if info.get('trailingAnnualDividendRate', 0) else 0, 2),
            "RET_1D": ((h_skg - prev_c) / prev_c * 100) if prev_c > 0 else 0, "MARKET_CAP": info.get('marketCap', 0),
            "BID": bid_price, "OFFER": ask_price, "LONGNAME": full_company_name, "SECTOR": info.get('sector', 'Market')[:12],
            "AVG_VOL": vol_sma20, "TODAY_VOL": v_skg, "ATR": atr, "SMA50": sma50
        }
    except: return None

# ==========================================
# FIX CHART: 4 DATA (REVENUE, NET INCOME, OCF, TOTAL EQUITY) + AXIS MATI
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_quarterly_charts(emiten):
    try:
        tkr = yf.Ticker(f"{emiten}.JK")
        inc = tkr.quarterly_financials
        cf = tkr.quarterly_cashflow
        bs = tkr.quarterly_balance_sheet
        
        if inc.empty and bs.empty: return None, None
        dates = inc.columns[:3][::-1] if not inc.empty else bs.columns[:3][::-1]
        str_dates = [d.strftime('%b%y') for d in dates]
        
        def safe_get(df, keys):
            if df is None or df.empty: return [0] * len(str_dates)
            for k in keys:
                if k in df.index: return df.loc[k][:3][::-1].fillna(0).tolist()
            return [0] * len(str_dates)
            
        rev = safe_get(inc, ['Total Revenue', 'Operating Revenue'])
        net_inc = safe_get(inc, ['Net Income', 'Net Income Continuous Operations'])
        ocf = safe_get(cf, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
        teq = safe_get(bs, ['Total Equity', 'Stockholders Equity'])
        
        return str_dates, (rev, net_inc, ocf, teq)
    except: return None, None

def plot_luxury_bar(x_data, y1, y2, y3, y4, name1, name2, name3, name4, color1, color2, color3, color4):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_data, y=y1, name=name1, marker_color=color1, opacity=0.85))
    fig.add_trace(go.Bar(x=x_data, y=y2, name=name2, marker_color=color2, opacity=0.85))
    fig.add_trace(go.Bar(x=x_data, y=y3, name=name3, marker_color=color3, opacity=0.85))
    fig.add_trace(go.Bar(x=x_data, y=y4, name=name4, marker_color=color4, opacity=0.85))
    
    # FIX: Judul dihapus dari plotly (dimasukkan via st.markdown) & Margins disesuaikan agar tidak tabrakan
    fig.update_layout(
        height=240, 
        barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(family='Outfit', size=8)),
        margin=dict(l=5, r=5, t=10, b=5), 
        # MENONAKTIFKAN ZOOM & PAN SEPENUHNYA
        xaxis=dict(showgrid=False, fixedrange=True, tickfont=dict(family='Outfit', size=8)),
        yaxis=dict(showgrid=True, fixedrange=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(family='Outfit', size=8)),
        dragmode=False 
    )
    return fig

# ==========================================
# 4. CROSS-VALIDATION UI (COMMAND CENTER)
# ==========================================
def render_cross_validation_ui(active_tickers_tuple, market_climate_mult, is_trading_mode):
    st.markdown("---")
    if active_tickers_tuple:
        safe_key = f"cv_target_v188_{st.session_state.current_tf}_{'TRD' if is_trading_mode else 'INV'}"
        valid_targets = [t for t in active_tickers_tuple if next((i for i in st.session_state.raw_stocks if i.get("TICKER")==t), None)]
        if not valid_targets: return
        
        emiten_signal = st.radio("Bedah Target (Top 15):", options=valid_targets[:15], horizontal=True, key=safe_key, label_visibility="collapsed")
        
        r = next((item for item in st.session_state.raw_stocks if item.get("TICKER") == emiten_signal), None)
        if r:
            h_tgt, wpi = r.get('HARGA', 0), r.get('WPI_SCORE', 50)
            long_name = r.get('LONGNAME', emiten_signal)
            sector = r.get('SECTOR', 'Market')
            s_bandar = r.get("STATUS_BANDAR", "")
            sm_text, sm_score, sm_col = r.get('SM_TEXT', '-'), r.get('SM_SCORE', 0), r.get('SM_COLOR', '#38bdf8')
            roe, per, pbv, yld = r.get('ROE', 0), r.get('PER', 0), r.get('PBV', 0), r.get('DIV_YIELD', 0)
            peg = r.get('PEG', 0)
            tgt_low, tgt_mean, tgt_high = r.get('TGT_LOW', h_tgt*0.9), r.get('TGT_MEAN', h_tgt*1.1), r.get('TGT_HIGH', h_tgt*1.25)
            vol_lot = int(r.get('TODAY_VOL', 0) / 100)
            avg_lot = int(r.get('AVG_VOL', 0) / 100)
            atr_val = r.get('ATR', 0)
            volatility_pct = (atr_val / h_tgt) * 100 if h_tgt > 0 else 0

            # --- SUNTIKAN BADGE CLUSTER KHUSUS INVESTING MODE ---
            cluster_badges = ""
            if not is_trading_mode:
                badges = []
                if 0 < per < 10 and 0 < pbv < 1.0:
                    badges.append('<span style="background:rgba(14,165,233,0.15); color:#0ea5e9; padding:2px 6px; border-radius:3px; font-size:0.5rem; font-weight:800; border:1px solid rgba(14,165,233,0.3);">💎 DEEP VALUE</span>')
                if 0 < peg <= 1.0:
                    badges.append('<span style="background:rgba(139,92,246,0.15); color:#8b5cf6; padding:2px 6px; border-radius:3px; font-size:0.5rem; font-weight:800; border:1px solid rgba(139,92,246,0.3);">🚀 HIGH GROWTH</span>')
                if yld >= 5.0:
                    badges.append('<span style="background:rgba(16,185,129,0.15); color:#10b981; padding:2px 6px; border-radius:3px; font-size:0.5rem; font-weight:800; border:1px solid rgba(16,185,129,0.3);">💰 DIV KINGS</span>')
                
                if badges:
                    cluster_badges = f'<div style="display:flex; gap:5px; margin-top:6px; flex-wrap:wrap;">{"".join(badges)}</div>'

            # --- COMMON HEADER ---
            html_header = (
                f'<div class="stocksly-card" style="margin-bottom: 10px; border-color: rgba(0, 242, 254, 0.25);">'
                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<div style="max-width: 65%;"><div style="display:flex; align-items:center; gap:8px;">'
                f'<div style="color:#f8fafc; font-size:1.8rem; font-weight:900; line-height:1;">{emiten_signal}</div>'
                f'<span style="background:rgba(0,242,254,0.1); color:#00f2fe; padding:2px 5px; border-radius:3px; font-size:0.55rem; font-weight:800; border:1px solid rgba(0,242,254,0.3); white-space:nowrap;">{sector}</span>'
                f'</div><p style="color:#cbd5e1; font-size:0.7rem; margin:4px 0 0 0; font-weight:500; white-space:normal; line-height:1.2;">{long_name}</p>'
                f'{cluster_badges}' # Inject Badge Cluster di sini
                f'</div>'
                f'<div style="text-align:right;">'
                f'<div style="font-size:0.45rem; color:#64748b; font-weight:800; letter-spacing:0.5px;">SMART MONEY</div>'
                f'<div style="font-size:1.8rem; font-weight:900; color:{sm_col}; line-height:1; margin-top:2px;">{sm_score}</div>'
                f'<div style="font-size:0.55rem; color:{sm_col}; margin-top:2px; font-weight:700;">{sm_text}</div>'
                f'</div></div></div>'
            )
            st.markdown(html_header, unsafe_allow_html=True)
            
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                # --- STRATEGY & FUNDAMENTAL ---
                html_strategy = (
                    f'<div class="stocksly-card" style="margin-bottom: 8px;">'
                    f'<div class="card-title" style="margin-bottom:8px; display:flex; justify-content:space-between; width:100%;">'
                    f'<span>📊 Strategi & Fundamental</span>'
                    f'<span style="font-size:0.5rem; color:#64748b; font-weight:800; letter-spacing:0.5px;">WPI SCORE</span>'
                    f'</div>'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<div style="flex:1; padding-right:15px; border-right:1px solid rgba(255,255,255,0.05);">'
                    f'<div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:8px; font-size:0.65rem;">'
                    f'<span style="color:#64748b;">ROE: <b style="color:#f8fafc;">{roe:.1f}%</b></span>'
                    f'<span style="color:#64748b;">PER: <b style="color:#f8fafc;">{per:.1f}x</b></span>'
                    f'<span style="color:#64748b;">PBV: <b style="color:#f8fafc;">{pbv:.1f}x</b></span>'
                    f'<span style="color:#64748b;">YIELD: <b style="color:#10b981;">{yld:.1f}%</b></span>'
                    f'</div></div>'
                    f'<div style="width:35%; display:flex; flex-direction:column; justify-content:center; align-items:flex-end; padding-left:10px;">'
                    f'<div style="font-size:2.2rem; font-weight:900; color:{"#10b981" if wpi>=70 else ("#d4af37" if wpi>=40 else "#f43f5e")}; line-height:1; margin-bottom: 2px;">{wpi:.0f}%</div>'
                    f'<div style="font-size:0.6rem; font-weight:800; color:#94a3b8; white-space:nowrap;">{s_bandar}</div>'
                    f'</div></div>'
                    f'<div style="width:100%; margin-top: 8px; border-top: 1px dashed rgba(255,255,255,0.05); padding-top: 8px;">'
                    f'<div style="background:rgba(255,255,255,0.05); height:6px; border-radius:3px; width:100%;">'
                    f'<div style="background:linear-gradient(90deg, #f43f5e, #facc15, #10b981); width:{wpi}%; height:100%; border-radius:3px;"></div>'
                    f'</div>'
                    f'<div style="display:flex; justify-content:space-between; font-size:0.4rem; color:#64748b; margin-top:4px; font-weight:800; letter-spacing:0.5px;">'
                    f'<span>BEARISH</span><span>NEUTRAL</span><span>BULLISH</span>'
                    f'</div></div></div>'
                )
                st.markdown(html_strategy, unsafe_allow_html=True)
                
                # --- ANALYST TARGETS ---
                min_range = min(tgt_low, h_tgt) * 0.90
                max_range = max(tgt_high, h_tgt) * 1.10
                total_span = max_range - min_range if max_range > min_range else 1
                pos_current = max(0, min(100, ((h_tgt - min_range) / total_span) * 100))
                pos_mean = max(0, min(100, ((tgt_mean - min_range) / total_span) * 100))
                pos_current_txt = max(10, min(90, pos_current))
                pos_mean_txt = max(10, min(90, pos_mean))

                html_analyst_target = (
                    f'<div class="stocksly-card" style="margin-bottom: 8px;">'
                    f'<div class="card-title">🎯 Analyst Price Targets</div>'
                    f'<div style="position:relative; margin-top:40px; margin-bottom:45px; padding:0 8px;">'
                    f'<div style="background:rgba(255,255,255,0.1); height:4px; border-radius:2px; width:100%;"></div>'
                    f'<div style="position:absolute; bottom:12px; left:{pos_mean_txt}%; transform:translateX(-50%); display:flex; flex-direction:column; align-items:center; z-index:3; width:60px;">'
                    f'<span style="font-size:0.45rem; color:#94a3b8; font-weight:800; margin-bottom:2px;">Average</span>'
                    f'<div style="background:#00f2fe; padding:2px 6px; border-radius:3px;">'
                    f'<span style="color:#030712; font-size:0.55rem; font-weight:900; line-height:1;">{int(tgt_mean):,}</span>'
                    f'</div></div>'
                    f'<div style="position:absolute; top:-3px; left:{pos_mean}%; transform:translateX(-50%); width:10px; height:10px; background:#00f2fe; border-radius:50%; border:2px solid #0a0f1e; z-index:2;"></div>'
                    f'<div style="position:absolute; top:-3px; left:{pos_current}%; transform:translateX(-50%); width:10px; height:10px; background:#f8fafc; border-radius:50%; border:2px solid #0a0f1e; z-index:4;"></div>'
                    f'<div style="position:absolute; top:12px; left:{pos_current_txt}%; transform:translateX(-50%); display:flex; flex-direction:column; align-items:center; z-index:4; width:60px;">'
                    f'<span style="font-size:0.45rem; color:#94a3b8; font-weight:800; margin-bottom:1px;">Current</span>'
                    f'<span style="font-size:0.65rem; color:#f8fafc; font-weight:900; line-height:1;">{int(h_tgt):,}</span>'
                    f'</div></div>'
                    f'<div style="display:flex; justify-content:space-between; align-items:center; font-size:0.5rem; color:#64748b; font-weight:800; margin-top:10px; padding-top:6px; border-top:1px dashed rgba(255,255,255,0.08);">'
                    f'<span>Low: <b style="color:#f43f5e;">{int(tgt_low):,}</b></span>'
                    f'<span>High: <b style="color:#10b981;">{int(tgt_high):,}</b></span>'
                    f'</div></div>'
                )
                st.markdown(html_analyst_target, unsafe_allow_html=True)
                
            with col_g2:
                # --- PENGKONDISIAN TRADING VS INVESTING ---
                if is_trading_mode:
                    setup_grade = r.get("SETUP_GRADE", "")
                    s_ara = r.get('STATUS_ARA_ARB', "")
                    a_beli = f"{int(r.get('AREA BELI', h_tgt)):,}".replace(",", ".")
                    t_stop_val = r.get('TRAILING STOP', h_tgt * 0.95)
                    t_stop = f"{int(t_stop_val):,}".replace(",", ".")
                    
                    if "REACTIVE" in setup_grade: sys_rec, color, r_mult = "SEROK BAWAH", "#d4af37", 1.5
                    elif "AVOID" in setup_grade: sys_rec, color, r_mult = "AVOID (FAKE)", "#f43f5e", 0.0
                    elif "A+" in setup_grade: sys_rec, color, r_mult = "STRONG ACCUM", "#10b981", 2.0 
                    elif "SCALP" in setup_grade: sys_rec, color, r_mult = "AGRES SCALP", "#8b5cf6", 1.5
                    else: sys_rec, color, r_mult = "ACCUMULATE", "#00f2fe", 1.0 
                    if "ARA" in s_ara: sys_rec, color = "ARA LOCKED", "#facc15"

                    max_lots = int(((modal_trading * (risiko_pct * r_mult * market_climate_mult / 100)) / (h_tgt - t_stop_val)) / 100) if (h_tgt - t_stop_val)>0 and r_mult > 0 else 0
                    
                    entry_border = "#10b981" if "SEROK" in setup_grade or "A+" in setup_grade else "#f43f5e"
                    
                    # Kotak Keputusan Trading
                    html_keputusan = (
                        f'<div class="stocksly-card" style="margin-bottom: 8px;">'
                        f'<div class="card-title">🎯 Keputusan</div>'
                        f'<div style="text-align:center; background:rgba(0,242,254,0.05); border:1px solid rgba(0,242,254,0.2); border-radius:5px; padding:6px; margin-bottom:4px;">'
                        f'<div style="font-size:0.95rem; font-weight:900; color:{color};">{sys_rec}</div>'
                        f'</div>'
                        f'<div style="font-size:0.6rem; color:#94a3b8; text-align:center;">'
                        f'Vol: <b>{vol_lot:,}</b> | Avg: <b>{avg_lot:,}</b>'
                        f'</div></div>'
                    )
                    
                    # Kotak Entry & Stop Trading
                    html_entry_val = (
                        f'<div class="stocksly-card" style="margin-bottom: 8px; border-left: 3px solid {entry_border};">'
                        f'<div class="card-title">🛒 Entry & Stop</div>'
                        f'<div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:5px; margin-bottom:4px;">'
                        f'<div style="background:rgba(255,255,255,0.02); padding:5px; border-radius:5px; text-align:center;">'
                        f'<div style="font-size:0.5rem; color:#64748b; font-weight:800;">BELI</div>'
                        f'<div style="font-size:0.85rem; color:#00f2fe; font-weight:900;">{a_beli}</div>'
                        f'</div>'
                        f'<div style="background:rgba(255,255,255,0.02); padding:5px; border-radius:5px; text-align:center;">'
                        f'<div style="font-size:0.5rem; color:#64748b; font-weight:800;">CUT</div>'
                        f'<div style="font-size:0.85rem; color:#f43f5e; font-weight:900;">{t_stop}</div>'
                        f'</div></div>'
                        f'<div style="text-align:center; font-size:0.7rem; color:#cbd5e1; background:rgba(255,255,255,0.02); padding:3px; border-radius:4px;">'
                        f'Max Alokasi: <b style="color:#00f2fe;">{max_lots:,} Lot</b>'
                        f'</div></div>'
                    )
                else:
                    # LOGIKA INVESTING
                    up_sma50 = r.get('UP_SMA50', False)
                    skor = (20 if 0<per<15 else 0) + (20 if 0<pbv<1.5 else 0) + (20 if yld>4 else 0) + (15 if up_sma50 else 0) + (25 if 0<peg<=1.0 else 0)
                    
                    if skor >= 70: sys_rec_inv, color_inv = "💎 DEEP VALUE", "#0ea5e9"
                    elif skor >= 40: sys_rec_inv, color_inv = "⚖️ FAIR VALUE", "#facc15"
                    else: sys_rec_inv, color_inv = "⚠️ OVERVALUED", "#f43f5e"

                    mos = ((tgt_mean - h_tgt) / tgt_mean * 100) if tgt_mean > h_tgt else 0
                    mos_str = f"+{mos:.1f}%" if mos > 0 else f"{mos:.1f}%"
                    mos_col = "#10b981" if mos > 10 else ("#facc15" if mos > 0 else "#f43f5e")

                    # Kotak Keputusan Investing
                    html_keputusan = (
                        f'<div class="stocksly-card" style="margin-bottom: 8px;">'
                        f'<div class="card-title">🎯 Keputusan Fundamental</div>'
                        f'<div style="text-align:center; background:rgba(0,242,254,0.05); border:1px solid rgba(0,242,254,0.2); border-radius:5px; padding:6px; margin-bottom:4px;">'
                        f'<div style="font-size:0.95rem; font-weight:900; color:{color_inv};">{sys_rec_inv}</div>'
                        f'</div>'
                        f'<div style="font-size:0.6rem; color:#94a3b8; text-align:center;">'
                        f'Vol: <b>{vol_lot:,}</b> | Avg: <b>{avg_lot:,}</b>'
                        f'</div></div>'
                    )
                    
                    # Kotak Valuation & Target Investing
                    html_entry_val = (
                        f'<div class="stocksly-card" style="margin-bottom: 8px; border-left: 3px solid {color_inv};">'
                        f'<div class="card-title">🛡️ Valuation Target</div>'
                        f'<div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:5px; margin-bottom:4px;">'
                        f'<div style="background:rgba(255,255,255,0.02); padding:5px; border-radius:5px; text-align:center;">'
                        f'<div style="font-size:0.5rem; color:#64748b; font-weight:800;">FAIR VALUE</div>'
                        f'<div style="font-size:0.85rem; color:#0ea5e9; font-weight:900;">{int(tgt_mean):,}</div>'
                        f'</div>'
                        f'<div style="background:rgba(255,255,255,0.02); padding:5px; border-radius:5px; text-align:center;">'
                        f'<div style="font-size:0.5rem; color:#64748b; font-weight:800;">M O S</div>'
                        f'<div style="font-size:0.85rem; color:{mos_col}; font-weight:900;">{mos_str}</div>'
                        f'</div></div>'
                        f'<div style="text-align:center; font-size:0.7rem; color:#cbd5e1; background:rgba(255,255,255,0.02); padding:3px; border-radius:4px;">'
                        f'Dividend Yield: <b style="color:#10b981;">{yld:.1f}%</b>'
                        f'</div></div>'
                    )

                st.markdown(html_keputusan, unsafe_allow_html=True)
                st.markdown(html_entry_val, unsafe_allow_html=True)

                # --- HARGA ---
                html_harga = (
                    f'<div class="stocksly-card" style="margin-bottom: 8px;">'
                    f'<div class="card-title">📈 Harga</div>'
                    f'<div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:5px; text-align:center;">'
                    f'<div style="background:rgba(255,255,255,0.02); padding:5px; border-radius:5px; border:1px solid rgba(255,255,255,0.04);">'
                    f'<div style="font-size:0.5rem; color:#64748b; font-weight:800;">LAST</div>'
                    f'<div style="font-size:0.9rem; color:#f8fafc; font-weight:900;">{int(h_tgt):,}</div>'
                    f'</div>'
                    f'<div style="background:rgba(255,255,255,0.02); padding:5px; border-radius:5px; border:1px solid rgba(255,255,255,0.04);">'
                    f'<div style="font-size:0.5rem; color:#64748b; font-weight:800;">ATR</div>'
                    f'<div style="font-size:0.9rem; color:{"#f43f5e" if volatility_pct>5 else "#10b981"}; font-weight:900;">{volatility_pct:.1f}%</div>'
                    f'</div></div></div>'
                )
                st.markdown(html_harga, unsafe_allow_html=True)
                
            # --- RENDER CHART KEUANGAN (AXIS MATI & JUDUL ANTI-TABRAK) ---
            with st.spinner("Mengunduh Laporan Keuangan..."):
                dates, inc_data = fetch_quarterly_charts(emiten_signal)
                if dates: 
                    # Judul diekstrak keluar dari plot plotly untuk menghindari tabrakan selamanya!
                    st.markdown(
                        '<div style="font-size:0.75rem; color:#cbd5e1; font-weight:800; letter-spacing:1px; margin-top:10px; margin-bottom:-5px; padding-left:5px;">'
                        '📊 FINANCIAL FUNDAMENTALS (IS, CF, BS)'
                        '</div>', 
                        unsafe_allow_html=True
                    )
                    
                    # Memanggil Chart dengan konfig displayModeBar False (Meniadakan toolbar Plotly)
                    st.plotly_chart(
                        plot_luxury_bar(
                            dates, inc_data[0], inc_data[1], inc_data[2], inc_data[3], 
                            "Rev (IS)", "Net (IS)", "OCF (CF)", "Eqty (BS)", 
                            "#0ea5e9", "#10b981", "#facc15", "#8b5cf6"
                        ), 
                        use_container_width=True,
                        config={'displayModeBar': False} # Meniadakan tombol-tombol melayang
                    )

            # FOOTER IDENTITY
            html_footer = (
                f'<div style="text-align:center; margin-top:20px; padding-bottom:70px;">'
                f'<span style="font-size:0.55rem; color:#475569; font-weight:900; letter-spacing:1px;">⚡ STOCKS.LY MASTERPIECE ENGINE</span><br>'
                f'<span style="font-size:0.5rem; color:#64748b; font-weight:700; letter-spacing:0.5px;">CREATED BY THEO HYDETETSU</span>'
                f'</div>'
            )
            st.markdown(html_footer, unsafe_allow_html=True)

# ==========================================
# 5. SIDEBAR (150px STRICT)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #f8fafc; font-weight: 900;'>Quantum Matrix</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #00f2fe; letter-spacing: 1px; margin-bottom: 10px; font-weight:700;'>v18.8 LUXURY</p>", unsafe_allow_html=True)
    
    engine_mode = st.radio("MODE ENGINE:", ("⚔️ TRD (Reactive)", "🛡️ INV (Fund)"))
    
    tf_pilihan = st.selectbox("⏱️ TIMEFRAME:", ("1 Hari", "1 Minggu"), index=0)
    tf_berubah = tf_pilihan != st.session_state.current_tf
    if tf_berubah: st.session_state.current_tf = tf_pilihan
        
    profil_risiko = st.selectbox("AGRESIVITAS:", ("⚖️ Moderat", "🔥 Agresif"), index=0)
    
    modal_input_str = st.text_input("💰 MODAL (Rp):", value="50.000.000")
    try: modal_trading = int(modal_input_str.replace(".", "").replace(",", ""))
    except: modal_trading = 50000000
    risiko_pct = st.slider("🚨 RISIKO (%):", 0.5, 5.0, 1.0, 0.5)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_ph = st.empty()
    if btn_ph.button("🔄 SCAN", use_container_width=True) or tf_berubah:
        btn_ph.empty() 
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.raw_stocks = []
        my_bar = st.progress(0, text="Radar...")
        dyn_tickers = get_dynamic_market_roster()
        for i, t in enumerate(dyn_tickers):
            my_bar.progress((i + 1) / len(dyn_tickers), text=f"{t} ({i+1}/{len(dyn_tickers)})")
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
        
    st.markdown("---")
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.clear()
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()

# ==========================================
# 6. HEADER DASHBOARD
# ==========================================
st.markdown("<h1>Stocks.ly Masterpiece</h1>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()

q = get_quote_of_the_day()
upd_time = st.session_state.last_update if st.session_state.last_update else "-"
html_quote = (
    f'<div style="margin-bottom: 10px; margin-top: 4px;">'
    f'<span style="color:#00f2fe; font-size:0.6rem; font-weight:900; letter-spacing:1px;">{q["theme"].upper()}</span><br>'
    f'<span style="color:#cbd5e1; font-size:0.75rem; font-style:italic;">\"{q["quote"]}\"</span><br>'
    f'<span style="font-size:0.6rem; color:#64748b;">Sync: {upd_time}</span>'
    f'</div>'
)
st.markdown(html_quote, unsafe_allow_html=True)

if st.session_state.scan_clicked and st.session_state.raw_stocks:
    up_c = sum(1 for s in st.session_state.raw_stocks if s.get("UP_SMA50", False))
    b_pct = (up_c / len(st.session_state.raw_stocks)) * 100
    c_stat, c_col, c_mult = ("BULLISH", "#10b981", 1.0) if b_pct >= 50 else ("BEARISH", "#f43f5e", 0.5)
else:
    c_stat, c_col, c_mult, b_pct = "-", "#64748b", 1.0, 0

if ihsg_now:
    w_p, w_g = ("▲", '#10b981') if ihsg_chg >= 0 else ("▼", '#f43f5e')
    html_ihsg_grid = (
        f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px;">'
        f'<div class="ihsg-box" style="border-left:3px solid {w_g};">'
        f'<div class="ihsg-title">IHSG</div>'
        f'<div class="ihsg-score">{ihsg_now:,.0f}</div>'
        f'<div style="color:{w_g}; font-weight:800; font-size:0.7rem;">{w_p} {ihsg_chg:+,.1f} ({ihsg_pct:+.2f}%)</div>'
        f'</div>'
        f'<div class="ihsg-box" style="border-left:3px solid {c_col};">'
        f'<div class="ihsg-title">CLIMATE</div>'
        f'<div class="ihsg-score" style="color:{c_col};">{c_stat}</div>'
        f'<div style="color:#64748b; font-weight:800; font-size:0.7rem;">Breadth: {b_pct:.0f}%</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_ihsg_grid, unsafe_allow_html=True)

if not st.session_state.scan_clicked or not st.session_state.raw_stocks:
    st.info("👈 Tekan tombol '🔄 SCAN' di sidebar untuk memulai.")
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
        elif "SCALP" in setup_grade: kep_t, prio, r_mult = "⚡ SCALP", 3, 1.5
        elif "B" in setup_grade: kep_t, prio, r_mult = "🟢 ACCUMULATE", 2, 1.0
        elif "AVOID" in setup_grade: kep_t, prio, r_mult = "⚠️ AVOID", 0, 0.0
        else: kep_t, prio, r_mult = "🟡 HOLD", 1, 0.0
        
        risk_ps = h - t_stop_val
        if ("ACCUM" in kep_t or "SCALP" in kep_t or "SEROK" in kep_t) and risk_ps > 0 and "ARA" not in status_ara:
            final_risk = risiko_pct * r_mult * c_mult
            max_lots = int(((modal_trading * (final_risk / 100)) / risk_ps) / 100)
            rec_lot_text = f"Max {max_lots:,} Lot"
        elif "ARA" in status_ara: rec_lot_text = "ARA LOCKED"
        elif "AVOID" in kep_t: rec_lot_text = "🚫 Dilarang"
        else: rec_lot_text = "🔒 Hold"

        wpi_score = r.get('WPI_SCORE', 50)
        s_bandar = r.get("STATUS_BANDAR", "")
        
        if "FAKE" in s_bandar: wpi_text = f"🚫 {wpi_score:.0f}% (DUMP)"
        elif "SEROK" in s_bandar: wpi_text = f"🎯 {wpi_score:.0f}% (REJECT)"
        elif wpi_score >= 80: wpi_text = f"🐋 {wpi_score:.0f}% (POWER)"
        elif wpi_score <= 30: wpi_text = f"🩸 {wpi_score:.0f}% (DUMP)"
        else: wpi_text = f"{wpi_score:.0f}%"
        
        h_trd.append({
            "PRIORITY": prio, "RAW_WPI": wpi_score, "MAX_LOT": rec_lot_text,
            "TICKER": t, "HARGA": f"{int(h):,}".replace(",", "."), 
            "BID": bid_str, "OFFER": offer_str,
            "1D %": f"{r.get('RET_1D',0):+.1f}%", "RAW_RET": r.get('RET_1D',0),
            "WPI": wpi_text,
            "LOT": rec_lot_text.replace("Max ", ""),
            "STOP": f"{int(t_stop_val):,}".replace(",", "."),
            "BANDAR": s_bandar, "REK": setup_grade, "AREA_BELI": r.get("AREA BELI", h)
        })
        
        per, pbv, peg, yld = r.get("PER", 0), r.get("PBV", 0), r.get("PEG", 0), r.get("DIV_YIELD", 0)
        skor = (20 if 0<per<15 else 0) + (20 if 0<pbv<1.5 else 0) + (20 if yld>4 else 0) + (15 if r.get("UP_SMA50") else 0) + (25 if 0<peg<=1.0 else 0)
        
        h_inv.append({
            "R_YLD": yld, "TICKER": t, "HARGA": f"{int(h):,}".replace(",", "."), "MCAP": format_financials(r.get("MARKET_CAP", 0)),
            "PER": f"{per:.1f}x", "PBV": f"{pbv:.1f}x", "PEG": f"{peg:.1f}x", "YIELD": f"{yld:.1f}%",
            "VALUASI": "💎 UNDERVALUED" if skor>=70 else ("⚖️ FAIR" if skor>=40 else "⚠️ OVER")
        })
        
        if 0 < per < 10 and 0 < pbv < 1.0: c_val.append(t)
        if 0 < peg <= 1.0: c_gro.append(t)
        if yld >= 5.0: c_div.append(t)

    df_trd_full = pd.DataFrame(h_trd).sort_values(["PRIORITY", "RAW_WPI"], ascending=[False, False]) if h_trd else pd.DataFrame()
    df_inv = pd.DataFrame(h_inv).sort_values("R_YLD", ascending=False).drop(columns=["R_YLD"]).set_index("TICKER").head(15) if h_inv else pd.DataFrame()

    if "TRD" in engine_mode:
        tab_c1, tab_c2, tab_c3 = st.tabs(["🚀 ELITE PICKS", "📊 TOP 15 MATRIX", "📖 SOP & DATA"])
        
        with tab_c1:
            st.markdown("<h3 style='font-size: 0.85rem; color:#00f2fe; margin-bottom: 10px; letter-spacing:1px;'>👑 TOP 4 ELITE PICKS</h3>", unsafe_allow_html=True)
            
            if not df_trd_full.empty:
                html_cards = '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 15px;">'
                top_4 = df_trd_full.head(4)
                for row in top_4.to_dict('records'):
                    tkr, prc, ret, bandar = row['TICKER'], row['HARGA'], row['RAW_RET'], row['BANDAR'].replace('🐋 ', '').replace('🎯 ', '').replace('🚀 ', '')
                    lot, ts, area_beli = row['MAX_LOT'].replace('Max ', ''), row['STOP'], f"{int(row['AREA_BELI']):,}".replace(",", ".")
                    ret_color, ret_sign = ("#10b981", "+") if ret >= 0 else ("#f43f5e", "")
                    
                    html_cards += (
                        f'<div class="vip-card">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 2px;">'
                        f'<div class="vip-title">{tkr}</div><span style="color:{ret_color}; font-weight:900; font-size:0.65rem;">{ret_sign}{ret:.1f}%</span>'
                        f'</div>'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 3px;">'
                        f'<div class="vip-price">Rp {prc}</div><div class="vip-badge">{bandar}</div>'
                        f'</div>'
                        f'<div class="vip-stat-row">'
                        f'<div class="vip-stat"><div class="vip-stat-label">Beli</div><div class="vip-stat-val" style="color:#00f2fe;">{area_beli}</div></div>'
                        f'<div class="vip-stat"><div class="vip-stat-label">Cut</div><div class="vip-stat-val" style="color:#f43f5e;">{ts}</div></div>'
                        f'<div class="vip-stat"><div class="vip-stat-label">Lot</div><div class="vip-stat-val" style="color:#38bdf8;">{lot}</div></div>'
                        f'</div></div>'
                    )
                html_cards += '</div>'
                st.markdown(html_cards, unsafe_allow_html=True)
            
            render_cross_validation_ui(tuple(str(x) for x in df_trd_full['TICKER'].head(15)), c_mult, True)

        with tab_c2:
            st.markdown("<h3 style='font-size: 0.85rem; color:#f8fafc; margin-bottom: 8px;'>🛰️ Top 15 Sinyal Aktif & Serok Bawah</h3>", unsafe_allow_html=True)
            df_display = df_trd_full.drop(columns=["PRIORITY", "RAW_WPI", "MAX_LOT", "RAW_RET", "AREA_BELI"]).set_index("TICKER").head(15)
            
            def style_t(row):
                stls = []
                for c, v in row.items():
                    if c in ['BID', 'OFFER']: stls.append('color:#f8fafc; font-weight:800; text-align:center;')
                    elif c == '1D %': stls.append('color:#10b981; font-weight:800; text-align:center;' if '+' in str(v) else ('color:#f43f5e; font-weight:800; text-align:center;' if '-' in str(v) and v!='-0.0%' else 'color:#64748b; text-align:center;'))
                    elif c == 'WPI': stls.append('color:#f43f5e; font-weight:900;' if '🚫' in str(v) else ('color:#d4af37; font-weight:900;' if '🎯' in str(v) else ('color:#10b981; font-weight:900;' if 'POWER' in str(v) else ('color:#f43f5e; font-weight:900;' if 'DUMP' in str(v) else 'color:#94a3b8;'))))
                    elif c == 'LOT': stls.append('color:#00f2fe; font-weight:900;' if 'Lot' in str(v) else ('color:#f43f5e; font-weight:900;' if 'Dilarang' in str(v) else 'color:#64748b;'))
                    elif c == 'STOP': stls.append('color:#f43f5e; font-weight:900; text-align:center;')
                    elif c == 'REK': stls.append('color:#d4af37; font-weight:900;' if 'REACTIVE' in v else ('color:#f43f5e; font-weight:900;' if 'AVOID' in v else ('color:#10b981; font-weight:900;' if 'A+' in v else ('color:#c4b5fd; font-weight:900;' if 'SCALP' in v else ('color:#38bdf8; font-weight:800;' if 'B' in v else 'color:#fb7185;')))))
                    elif c == 'BANDAR': stls.append('color:#d4af37; font-weight:900;' if 'SEROK' in v else ('color:#f43f5e; font-weight:900;' if 'FAKE' in v or 'DISTRIB' in v else ('color:#00f2fe; font-weight:900;' if 'AKUM' in v else ('color:#10b981; font-weight:900;' if 'MARK-UP' in v else 'color:#64748b;'))))
                    else: stls.append('color:#cbd5e1;')
                return stls
            
            if not df_display.empty: st.dataframe(df_display.style.apply(style_t, axis=1), use_container_width=True)

        with tab_c3:
            html_sop = (
                f'<div class="stocksly-card">'
                f'<div class="card-title">📖 Panduan Teknis & Bedah Data v18.8</div>'
                f'<div style="font-size:0.7rem; color:#cbd5e1; line-height: 1.4; padding: 4px;">'
                f'<p><b>1. WPI & Smart Money:</b> Mengukur posisi harga saat ini terhadap rentang High-Low harian serta mendeteksi kekuatan dorongan institusi (Skor Smart Money).</p>'
                f'<p><b>2. Analyst Price Targets:</b> Visualisasi rentang target harga konsensus analis (Low, Average, High) vs Harga Saat Ini (Current).</p>'
                f'<p><b>3. Serok Bawah (Rejection):</b> Dideteksi saat harga menyentuh support 20-hari dengan bentuk candle ekor panjang (Hammer) + volume kering.</p>'
                f'<p><b>4. Manajemen Lot Otomatis:</b> Alokasi <i>\'Max Lot\'</i> dihitung dinamis menggunakan batas risiko % modal terhadap jarak harga ke Trailing Stop.</p>'
                f'</div></div>'
            )
            st.markdown(html_sop, unsafe_allow_html=True)

    else: 
        # FIX: Tab DASHBOARD diubah namanya, dan Tab CLUSTERS diganti SOP
        tab_i1, tab_i2, tab_i3 = st.tabs(["🏦 INVESTMENTS", "🛡️ VALUE MATRIX", "📖 SOP & DATA"])
        
        with tab_i1:
            st.markdown("<h3 style='font-size: 0.85rem; color:#0ea5e9; margin-bottom: 10px; letter-spacing:1px;'>👑 TOP 4 VALUE PICKS</h3>", unsafe_allow_html=True)
            if not df_inv.empty:
                html_cards_inv = '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 15px;">'
                top_4_inv = df_inv.head(4).reset_index()
                
                for row in top_4_inv.to_dict('records'):
                    tkr = row['TICKER']
                    prc = row['HARGA']
                    yld = row['YIELD']
                    val = row['VALUASI'].replace('💎 ', '').replace('⚖️ ', '').replace('⚠️ ', '')
                    per = row['PER']
                    pbv = row['PBV']
                    val_color = "#0ea5e9" if "UNDERVALUED" in val else ("#facc15" if "FAIR" in val else "#f43f5e")

                    html_cards_inv += (
                        f'<div class="vip-card">'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 2px;">'
                        f'<div class="vip-title">{tkr}</div><span style="color:#10b981; font-weight:900; font-size:0.65rem;">Yield: {yld}</span>'
                        f'</div>'
                        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 3px;">'
                        f'<div class="vip-price">Rp {prc}</div><div class="vip-badge" style="color:{val_color}; border-color:{val_color}60; background:{val_color}15;">{val}</div>'
                        f'</div>'
                        f'<div class="vip-stat-row">'
                        f'<div class="vip-stat"><div class="vip-stat-label">PER</div><div class="vip-stat-val" style="color:#38bdf8;">{per}</div></div>'
                        f'<div class="vip-stat"><div class="vip-stat-label">PBV</div><div class="vip-stat-val" style="color:#38bdf8;">{pbv}</div></div>'
                        f'<div class="vip-stat"><div class="vip-stat-label">MCAP</div><div class="vip-stat-val" style="color:#cbd5e1;">{row["MCAP"]}</div></div>'
                        f'</div></div>'
                    )
                html_cards_inv += '</div>'
                st.markdown(html_cards_inv, unsafe_allow_html=True)
            
            render_cross_validation_ui(tuple(str(x) for x in df_inv.index), c_mult, False)
            
        with tab_i2:
            st.markdown("<h3 style='font-size: 0.85rem; color:#f8fafc;'>🛡️ Top 15 Value</h3>", unsafe_allow_html=True)
            def style_i(row):
                stls = []
                for c, v in row.items():
                    if c == 'YIELD': stls.append('color:#10b981; font-weight:800;' if v!='0.0%' else 'color:#64748b;')
                    elif c in ['PER', 'PBV', 'PEG']:
                        try:
                            f_v = float(v.replace('x',''))
                            if (c == 'PER' and 0 < f_v < 15) or (c == 'PBV' and 0 < f_v < 1.2) or (c == 'PEG' and 0 < f_v <= 1.0): stls.append('color: #38bdf8; font-weight: 800;')
                            elif f_v > 20 or f_v > 2.5: stls.append('color: #f43f5e; font-weight: 800;')
                            else: stls.append('color: #cbd5e1;')
                        except: stls.append('color:#cbd5e1;')
                    elif c == 'VALUASI': stls.append('color:#0ea5e9; font-weight:800;' if 'UNDER' in v else ('color:#facc15; font-weight:800;' if 'FAIR' in v else 'color:#f43f5e; font-weight:800;'))
                    else: stls.append('color:#cbd5e1;')
                return stls
            if not df_inv.empty: st.dataframe(df_inv.style.apply(style_i, axis=1), use_container_width=True)
        
        with tab_i3:
            # Mengganti Tab CLUSTERS lama menjadi SOP khusus Fundamental
            html_sop_inv = (
                f'<div class="stocksly-card">'
                f'<div class="card-title">📖 Panduan Teknis & Bedah Data v18.8</div>'
                f'<div style="font-size:0.7rem; color:#cbd5e1; line-height: 1.4; padding: 4px;">'
                f'<p><b>1. WPI & Smart Money:</b> Mengukur posisi harga saat ini terhadap rentang High-Low harian serta mendeteksi kekuatan dorongan institusi (Skor Smart Money).</p>'
                f'<p><b>2. Analyst Price Targets:</b> Visualisasi rentang target harga konsensus analis (Low, Average, High) vs Harga Saat Ini (Current).</p>'
                f'<p><b>3. Serok Bawah (Rejection):</b> Dideteksi saat harga menyentuh support 20-hari dengan bentuk candle ekor panjang (Hammer) + volume kering.</p>'
                f'<p><b>4. Manajemen Lot Otomatis:</b> Alokasi <i>\'Max Lot\'</i> dihitung dinamis menggunakan batas risiko % modal terhadap jarak harga ke Trailing Stop.</p>'
                f'</div></div>'
            )
            st.markdown(html_sop_inv, unsafe_allow_html=True)
