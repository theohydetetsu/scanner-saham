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
CACHE_FILE = "jihan_ghina_saham_cache_v174.json"

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
# 1. KONFIGURASI HALAMAN & MOBILE UI (v17.4)
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA Masterpiece v17.4", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; scroll-behavior: smooth; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -10%, #060d1a, #010308) !important; color: #f8fafc !important; overflow-x: hidden; }
    [data-testid="stHeader"] { background: transparent !important; height: 0px !important; }
    
    .block-container { padding-top: 1.2rem !important; padding-bottom: 1.5rem !important; padding-left: 0.8rem !important; padding-right: 0.8rem !important; max-width: 100% !important; animation: fadeIn 0.4s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    
    h1 { color: #f8fafc; font-weight: 800; letter-spacing: -0.5px; font-size: 1.4rem !important; margin-bottom: 0; text-shadow: 0 2px 10px rgba(0,242,254,0.15); }
    
    ::-webkit-scrollbar { width: 3px; height: 3px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.8); }
    ::-webkit-scrollbar-thumb { background: rgba(0, 242, 254, 0.3); border-radius: 10px; }
    
    /* MODULAR CARD DESIGN */
    .stocksly-card { background: linear-gradient(145deg, rgba(15,23,42,0.85) 0%, rgba(10,15,30,0.95) 100%); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; padding: 12px; box-shadow: 0 4px 12px -4px rgba(0, 0, 0, 0.5); display: flex; flex-direction: column; justify-content: space-between; height: 100%; position: relative; overflow: hidden; }
    .card-title { font-size: 0.75rem; font-weight: 800; color: #64748b; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; display: flex; align-items: center; gap: 4px; }
    
    /* VIP HIGHLIGHT CARDS */
    .vip-card { background: linear-gradient(145deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.9) 100%); backdrop-filter: blur(10px); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 10px; padding: 10px 12px; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between; height: 100%;}
    .vip-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, #00f2fe, #38bdf8, #00f2fe); }
    .vip-title { font-size: 1.25rem; font-weight: 800; color: #f8fafc; margin: 0; line-height: 1.1;}
    .vip-price { font-size: 1.05rem; font-weight: 800; margin: 4px 0 6px 0; }
    .vip-badge { background: rgba(0, 242, 254, 0.15); color: #00f2fe; padding: 3px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 800; display: inline-block; border: 1px solid rgba(0, 242, 254, 0.4);}
    .vip-stat-row { display: flex; justify-content: space-between; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); }
    .vip-stat { text-align: center; }
    .vip-stat-label { font-size: 0.55rem; color: #64748b; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; }
    .vip-stat-val { font-size: 0.8rem; font-weight: 800; margin-top: 2px; }
    
    /* SIDEBAR 150PX STRICT */
    section[data-testid="stSidebar"] { width: 150px !important; min-width: 150px !important; max-width: 150px !important; background: linear-gradient(180deg, rgba(2,6,23,0.98) 0%, rgba(15,23,42,0.98) 100%) !important; border-right: 1px solid rgba(255, 255, 255, 0.03); padding-top: 1rem !important;}
    section[data-testid="stSidebar"] .stMarkdown h2 { font-size: 1rem !important; margin-bottom: -5px !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { font-size: 0.7rem !important; }
    section[data-testid="stSidebar"] label { font-size: 0.65rem !important; font-weight: 700 !important; color: #cbd5e1 !important; }
    section[data-testid="stSidebar"] input { font-size: 0.75rem !important; padding: 4px !important; }
    section[data-testid="stSidebar"] div[data-baseweb="select"] { font-size: 0.75rem !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background-color: rgba(15,23,42,0.4); padding: 4px; border-radius: 8px; margin-bottom: 12px;}
    .stTabs [data-baseweb="tab"] { padding: 6px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }
    
    .ihsg-box { display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 8px 12px !important; background: linear-gradient(135deg, rgba(15,23,42,0.7) 0%, rgba(30,41,59,0.4) 100%); border-radius: 8px; }
    .ihsg-title { color: #64748b; font-size: 0.65rem; font-weight: 800; letter-spacing: 0.5px; }
    .ihsg-score { color: #f8fafc; font-size: 1.2rem; font-weight: 800; line-height: 1.1; margin: 3px 0; }
    
    div.stButton > button:first-child { background: linear-gradient(90deg, rgba(30,41,59,0.5) 0%, rgba(15,23,42,0.8) 100%) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #cbd5e1 !important; border-radius: 6px !important; padding: 6px 10px !important; font-size: 0.75rem !important; font-weight: 800 !important;}
    
    .stDataFrame { font-size: 11px !important; }
    th.row_heading { color: #00f2fe !important; font-size: 0.8rem !important; }

    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label { padding: 4px 10px !important; border-radius: 4px !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label p { font-size: 0.75rem !important; }
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
    if not tickers: return "<span style='color:#475569; font-size:0.65rem; font-style:italic;'>Kosong</span>"
    res = "<div style='display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;'>"
    for t in tickers: res += f"<span style='background:rgba(0,0,0,0.2); border:1px solid {hex_color}40; border-radius:4px; padding:3px 6px; color:{hex_color}; font-size:0.65rem; font-weight:700;'>{t}</span>"
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

        return {
            "TICKER": kode, "HARGA": h_skg, "AREA BELI": ema20 if h_skg > ema20 else (low_20 + (h_skg - low_20)*0.3), 
            "TRAILING STOP": t_stop, "WPI_SCORE": round(wpi_score, 1), "BATAS_ARA": b_ara, "STATUS_ARA_ARB": status_ara, 
            "STATUS_BANDAR": s_bandar, "SETUP_GRADE": grade, "UP_SMA50": h_skg > sma50,
            "PER": round(info.get('trailingPE', 0), 2), "PBV": round(info.get('priceToBook', 1), 2), "PEG": round(info.get('pegRatio') or 0, 2), 
            "DIV_YIELD": round((info.get('trailingAnnualDividendRate', 0) / h_skg * 100) if info.get('trailingAnnualDividendRate', 0) else 0, 2),
            "RET_1D": ((h_skg - prev_c) / prev_c * 100) if prev_c > 0 else 0, "MARKET_CAP": info.get('marketCap', 0),
            "BID": bid_price, "OFFER": ask_price, "LONGNAME": info.get('longName', kode)[:15], "SECTOR": info.get('sector', 'Market')[:10],
            "AVG_VOL": vol_sma20, "TODAY_VOL": v_skg, "ATR": atr
        }
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_quarterly_charts(emiten):
    try:
        tkr = yf.Ticker(f"{emiten}.JK")
        inc = tkr.quarterly_financials
        bs = tkr.quarterly_balance_sheet
        if inc.empty and bs.empty: return None, None
        dates = inc.columns[:3][::-1] if not inc.empty else bs.columns[:3][::-1]
        str_dates = [d.strftime('%b%y') for d in dates]
        def safe_get(df, keys):
            for k in keys:
                if k in df.index: return df.loc[k][:3][::-1].fillna(0).tolist()
            return [0] * len(str_dates)
        rev = safe_get(inc, ['Total Revenue', 'Operating Revenue'])
        net_inc = safe_get(inc, ['Net Income', 'Net Income Continuous Operations'])
        return str_dates, (rev, net_inc)
    except: return None, None

def plot_luxury_bar(x_data, y1, y2, name1, name2, color1, color2, title):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_data, y=y1, name=name1, marker_color=color1, opacity=0.85))
    fig.add_trace(go.Bar(x=x_data, y=y2, name=name2, marker_color=color2, opacity=0.85))
    fig.update_layout(
        height=220, 
        title=dict(text=title, font=dict(color='#cbd5e1', size=11)),
        barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(size=8)),
        margin=dict(l=5, r=5, t=25, b=5), 
        xaxis=dict(showgrid=False, tickfont=dict(size=8)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=8))
    )
    return fig

# ==========================================
# 4. CROSS-VALIDATION UI (COMMAND CENTER)
# ==========================================
def render_cross_validation_ui(active_tickers_tuple, market_climate_mult, is_trading_mode):
    st.markdown("---")
    if active_tickers_tuple:
        safe_key = f"cv_target_v174_{st.session_state.current_tf}_{'TRD' if is_trading_mode else 'INV'}"
        valid_targets = [t for t in active_tickers_tuple if next((i for i in st.session_state.raw_stocks if i.get("TICKER")==t), None)]
        if not valid_targets: return
        
        emiten_signal = st.radio("Bedah Target:", options=valid_targets[:10], horizontal=True, key=safe_key, label_visibility="collapsed")
        
        r = next((item for item in st.session_state.raw_stocks if item.get("TICKER") == emiten_signal), None)
        if r:
            if is_trading_mode:
                setup_grade = r.get("SETUP_GRADE", "")
                s_bandar = r.get("STATUS_BANDAR", "")
                h_tgt, wpi = r.get('HARGA', 0), r.get('WPI_SCORE', 50)
                long_name = r.get('LONGNAME', emiten_signal)
                sector = r.get('SECTOR', 'Market')
                a_beli = f"{int(r.get('AREA BELI', h_tgt)):,}".replace(",", ".")
                t_stop_val = r.get('TRAILING STOP', h_tgt * 0.95)
                t_stop = f"{int(t_stop_val):,}".replace(",", ".")
                b_ara = f"{int(r.get('BATAS_ARA', 0)):,}".replace(",", ".")
                s_ara = r.get('STATUS_ARA_ARB', "")
                per, pbv, roe = r.get('PER', 0), r.get('PBV', 0), r.get('ROE', 0)
                vol_lot = int(r.get('TODAY_VOL', 0) / 100)
                avg_lot = int(r.get('AVG_VOL', 0) / 100)
                atr_val = r.get('ATR', 0)
                volatility_pct = (atr_val / h_tgt) * 100 if h_tgt > 0 else 0
                
                if "REACTIVE" in setup_grade: sys_rec, color, r_mult = "SEROK BAWAH", "#d4af37", 1.5
                elif "AVOID" in setup_grade: sys_rec, color, r_mult = "AVOID (FAKE)", "#f43f5e", 0.0
                elif "A+" in setup_grade: sys_rec, color, r_mult = "STRONG ACCUM", "#10b981", 2.0 
                elif "SCALP" in setup_grade: sys_rec, color, r_mult = "AGRES SCALP", "#8b5cf6", 1.5
                else: sys_rec, color, r_mult = "ACCUMULATE", "#00f2fe", 1.0 
                if "ARA" in s_ara: sys_rec, color = "ARA LOCKED", "#facc15"

                max_lots = int(((modal_trading * (risiko_pct * r_mult * market_climate_mult / 100)) / (h_tgt - t_stop_val)) / 100) if (h_tgt - t_stop_val)>0 and r_mult > 0 else 0

                st.markdown(f"""
                <div class="stocksly-card" style="margin-bottom: 12px; border-color: rgba(0, 242, 254, 0.25);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <h2 style="color:#f8fafc; font-size:1.2rem; margin:0;">{emiten_signal}</h2>
                                <span style="background:rgba(0,242,254,0.1); color:#00f2fe; padding:3px 6px; border-radius:4px; font-size:0.6rem; font-weight:800; border:1px solid rgba(0,242,254,0.3);">{sector}</span>
                            </div>
                            <p style="color:#94a3b8; font-size:0.75rem; margin:2px 0 0 0;">{long_name}</p>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.55rem; color:#64748b; font-weight:800; letter-spacing:0.5px;">WPI SCORE</div>
                            <div style="font-size:1.2rem; font-weight:800; color:{'#10b981' if wpi>=70 else ('#d4af37' if wpi>=40 else '#f43f5e')}; line-height:1;">{wpi:.0f}%</div>
                            <div style="font-size:0.6rem; color:#94a3b8; margin-top:2px;">{s_bandar}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown(f"""
                    <div class="stocksly-card" style="margin-bottom: 10px;">
                        <div class="card-title">📊 Strategi</div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.75rem;">
                            <span style="color:#64748b;">ROE {roe:.0f}%</span>
                            <span style="color:{'#10b981' if 'AKUM' in s_bandar or 'SEROK' in s_bandar else '#f43f5e'}; font-weight:800;">{s_bandar}</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.05); height:6px; border-radius:3px;">
                            <div style="background:linear-gradient(90deg, #f43f5e, #facc15, #10b981); width:{wpi}%; height:100%;"></div>
                        </div>
                    </div>
                    
                    <div class="stocksly-card" style="margin-bottom: 10px;">
                        <div class="card-title">📈 Harga</div>
                        <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:6px; text-align:center;">
                            <div style="background:rgba(255,255,255,0.02); padding:6px; border-radius:6px; border:1px solid rgba(255,255,255,0.04);">
                                <div style="font-size:0.55rem; color:#64748b; font-weight:800;">LAST</div>
                                <div style="font-size:0.9rem; color:#f8fafc; font-weight:800;">{int(h_tgt):,}</div>
                            </div>
                            <div style="background:rgba(255,255,255,0.02); padding:6px; border-radius:6px; border:1px solid rgba(255,255,255,0.04);">
                                <div style="font-size:0.55rem; color:#64748b; font-weight:800;">ATR</div>
                                <div style="font-size:0.9rem; color:{'#f43f5e' if volatility_pct>5 else '#10b981'}; font-weight:800;">{volatility_pct:.1f}%</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_g2:
                    st.markdown(f"""
                    <div class="stocksly-card" style="margin-bottom: 10px;">
                        <div class="card-title">🎯 Keputusan</div>
                        <div style="text-align:center; background:rgba(0,242,254,0.05); border:1px solid rgba(0,242,254,0.2); border-radius:6px; padding:8px; margin-bottom:6px;">
                            <div style="font-size:1.05rem; font-weight:800; color:{color};">{sys_rec}</div>
                        </div>
                        <div style="font-size:0.65rem; color:#94a3b8; text-align:center;">
                            Vol: <b>{vol_lot:,}</b> | Avg: <b>{avg_lot:,}</b>
                        </div>
                    </div>

                    <div class="stocksly-card" style="margin-bottom: 10px; border-left: 3px solid {'#10b981' if 'SEROK' in setup_grade or 'A+' in setup_grade else '#f43f5e'};">
                        <div class="card-title">🛒 Entry & Stop</div>
                        <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:6px; margin-bottom:6px;">
                            <div style="background:rgba(255,255,255,0.02); padding:6px; border-radius:6px; text-align:center;">
                                <div style="font-size:0.55rem; color:#64748b; font-weight:800;">BELI</div>
                                <div style="font-size:0.85rem; color:#00f2fe; font-weight:800;">{a_beli}</div>
                            </div>
                            <div style="background:rgba(255,255,255,0.02); padding:6px; border-radius:6px; text-align:center;">
                                <div style="font-size:0.55rem; color:#64748b; font-weight:800;">CUT</div>
                                <div style="font-size:0.85rem; color:#f43f5e; font-weight:800;">{t_stop}</div>
                            </div>
                        </div>
                        <div style="text-align:center; font-size:0.75rem; color:#cbd5e1; background:rgba(255,255,255,0.02); padding:4px; border-radius:4px;">
                            Max Alokasi: <b style="color:#00f2fe;">{max_lots:,} Lot</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            else:
                per, pbv, yld = r.get("PER", 0), r.get("PBV", 0), r.get("DIV_YIELD", 0)
                st.markdown(f"<div style='display:flex; justify-content:space-around; background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:10px; margin-bottom:12px;'><div style='text-align:center;'><span style='color:#64748b; font-size:0.6rem; font-weight:700;'>PER</span><br><span style='color:#f8fafc; font-weight:800; font-size:1rem;'>{per:.1f}x</span></div><div style='text-align:center;'><span style='color:#64748b; font-size:0.6rem; font-weight:700;'>PBV</span><br><span style='color:#f8fafc; font-weight:800; font-size:1rem;'>{pbv:.1f}x</span></div><div style='text-align:center;'><span style='color:#64748b; font-size:0.6rem; font-weight:700;'>YIELD</span><br><span style='color:#10b981; font-weight:800; font-size:1rem;'>{yld:.1f}%</span></div></div>", unsafe_allow_html=True)
                with st.spinner("Mengunduh Laporan Keuangan..."):
                    dates, inc_data = fetch_quarterly_charts(emiten_signal)
                    if dates: st.plotly_chart(plot_luxury_bar(dates, inc_data[0], inc_data[1], "Rev", "Net", "#0ea5e9", "#10b981", "Revenue vs Net Income"), use_container_width=True)

# ==========================================
# 5. SIDEBAR (150px STRICT)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #f8fafc; font-weight: 800;'>Quantum Matrix</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #00f2fe; letter-spacing: 1px; margin-bottom: 12px;'>v17.4 PERFECTION</p>", unsafe_allow_html=True)
    
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
st.markdown(f"<div style='margin-bottom: 12px; margin-top: 5px;'><span style='color:#00f2fe; font-size:0.65rem; font-weight:800; letter-spacing:1px;'>{q['theme'].upper()}</span><br><span style='color:#cbd5e1; font-size:0.8rem; font-style:italic;'>\"{q['quote']}\"</span><br><span style='font-size:0.65rem; color:#64748b;'>Sync: {upd_time}</span></div>", unsafe_allow_html=True)

if st.session_state.scan_clicked and st.session_state.raw_stocks:
    up_c = sum(1 for s in st.session_state.raw_stocks if s.get("UP_SMA50", False))
    b_pct = (up_c / len(st.session_state.raw_stocks)) * 100
    c_stat, c_col, c_mult = ("BULLISH", "#10b981", 1.0) if b_pct >= 50 else ("BEARISH", "#f43f5e", 0.5)
else:
    c_stat, c_col, c_mult, b_pct = "-", "#64748b", 1.0, 0

if ihsg_now:
    w_p, w_g = ("▲", '#10b981') if ihsg_chg >= 0 else ("▼", '#f43f5e')
    # HTML GRID MURNI: 100% dipaksa bersebelahan di Mobile
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
        <div class='ihsg-box' style='border-left:3px solid {w_g};'><span class='ihsg-title'>IHSG</span><span class='ihsg-score'>{ihsg_now:,.0f}</span><span style='color:{w_g}; font-weight:700; font-size:0.75rem;'>{w_p} {ihsg_chg:+,.1f} ({ihsg_pct:+.2f}%)</span></div>
        <div class='ihsg-box' style='border-left:3px solid {c_col};'><span class='ihsg-title'>CLIMATE</span><span class='ihsg-score' style='color:{c_col};'>{c_stat}</span><span style='color:#64748b; font-weight:700; font-size:0.75rem;'>Breadth: {b_pct:.0f}%</span></div>
    </div>
    """, unsafe_allow_html=True)

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
            st.markdown("<h3 style='font-size: 0.9rem; color:#00f2fe; margin-bottom: 12px;'>👑 Top 4 Elite Picks</h3>", unsafe_allow_html=True)
            if not df_trd_full.empty:
                # HTML GRID MURNI: 2x2 Grid (Kanan 2 Kiri 2)
                html_cards = '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 20px;">'
                top_4 = df_trd_full.head(4)
                for row in top_4.to_dict('records'):
                    tkr, prc, ret, bandar = row['TICKER'], row['HARGA'], row['RAW_RET'], row['BANDAR'].replace('🐋 ', '').replace('🎯 ', '').replace('🚀 ', '')
                    lot, ts, area_beli = row['MAX_LOT'].replace('Max ', ''), row['STOP'], f"{int(row['AREA_BELI']):,}".replace(",", ".")
                    ret_color, ret_sign = ("#10b981", "+") if ret >= 0 else ("#f43f5e", "")
                    
                    html_cards += f"""
                    <div class="vip-card">
                        <div>
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <h2 class="vip-title">{tkr}</h2>
                                <span style="color:{ret_color}; font-weight:800; font-size:0.85rem;">{ret_sign}{ret:.1f}%</span>
                            </div>
                            <div class="vip-price">Rp {prc}</div>
                            <div class="vip-badge">{bandar}</div>
                        </div>
                        <div class="vip-stat-row">
                            <div class="vip-stat">
                                <div class="vip-stat-label">Beli</div>
                                <div class="vip-stat-val" style="color:#00f2fe;">{area_beli}</div>
                            </div>
                            <div class="vip-stat">
                                <div class="vip-stat-label">Cut</div>
                                <div class="vip-stat-val" style="color:#f43f5e;">{ts}</div>
                            </div>
                            <div class="vip-stat">
                                <div class="vip-stat-label">Lot</div>
                                <div class="vip-stat-val" style="color:#38bdf8;">{lot}</div>
                            </div>
                        </div>
                    </div>
                    """
                html_cards += '</div>'
                st.markdown(html_cards, unsafe_allow_html=True)
            
            render_cross_validation_ui(tuple(str(x) for x in df_trd_full['TICKER'].head(15)), c_mult, True)

        with tab_c2:
            st.markdown("<h3 style='font-size: 0.9rem; color:#f8fafc; margin-bottom: 10px;'>🛰️ Top 15 Sinyal Aktif & Serok Bawah</h3>", unsafe_allow_html=True)
            df_display = df_trd_full.drop(columns=["PRIORITY", "RAW_WPI", "MAX_LOT", "RAW_RET", "AREA_BELI"]).set_index("TICKER").head(15)
            
            def style_t(row):
                stls = []
                for c, v in row.items():
                    if c in ['BID', 'OFFER']: stls.append('color:#f8fafc; font-weight:800; text-align:center;')
                    elif c == '1D %': stls.append('color:#10b981; font-weight:800; text-align:center;' if '+' in str(v) else ('color:#f43f5e; font-weight:800; text-align:center;' if '-' in str(v) and v!='-0.0%' else 'color:#64748b; text-align:center;'))
                    elif c == 'WPI': stls.append('color:#f43f5e; font-weight:800;' if '🚫' in str(v) else ('color:#d4af37; font-weight:800;' if '🎯' in str(v) else ('color:#10b981; font-weight:800;' if 'POWER' in str(v) else ('color:#f43f5e; font-weight:800;' if 'DUMP' in str(v) else 'color:#94a3b8;'))))
                    elif c == 'LOT': stls.append('color:#00f2fe; font-weight:800;' if 'Lot' in str(v) else ('color:#f43f5e; font-weight:800;' if 'Dilarang' in str(v) else 'color:#64748b;'))
                    elif c == 'STOP': stls.append('color:#f43f5e; font-weight:800; text-align:center;')
                    elif c == 'REK': stls.append('color:#d4af37; font-weight:800;' if 'REACTIVE' in v else ('color:#f43f5e; font-weight:800;' if 'AVOID' in v else ('color:#10b981; font-weight:800;' if 'A+' in v else ('color:#c4b5fd; font-weight:800;' if 'SCALP' in v else ('color:#38bdf8; font-weight:700;' if 'B' in v else 'color:#fb7185;')))))
                    elif c == 'BANDAR': stls.append('color:#d4af37; font-weight:800;' if 'SEROK' in v else ('color:#f43f5e; font-weight:800;' if 'FAKE' in v or 'DISTRIB' in v else ('color:#00f2fe; font-weight:800;' if 'AKUM' in v else ('color:#10b981; font-weight:800;' if 'MARK-UP' in v else 'color:#64748b;'))))
                    else: stls.append('color:#cbd5e1;')
                return stls
            
            if not df_display.empty: st.dataframe(df_display.style.apply(style_t, axis=1), use_container_width=True)

        with tab_c3:
            st.markdown("""
            <div class="stocksly-card">
                <div class="card-title">📖 Panduan Teknis & Bedah Data v17.4</div>
                <div style="font-size:0.75rem; color:#cbd5e1; line-height: 1.5; padding: 5px;">
                    <p><b>1. WPI (Whale Pressure Index):</b> Mengukur posisi harga saat ini terhadap rentang High-Low harian. WPI tinggi (>70%) menandakan tekanan beli institusi (Bandar) merangsek ke area tertinggi.</p>
                    <p><b>2. Garis Rainbow Strategy:</b> Merepresentasikan level WPI. <span style='color:#f43f5e; font-weight:bold;'>Merah (Distribusi)</span> ➔ <span style='color:#facc15; font-weight:bold;'>Kuning (Netral)</span> ➔ <span style='color:#10b981; font-weight:bold;'>Hijau (Akumulasi kuat)</span>.</p>
                    <p><b>3. Serok Bawah (Rejection):</b> Dideteksi saat harga menyentuh support 20-hari dengan bentuk candle ekor panjang (Hammer) + volume kering. Sinyal kuat untuk menadah guyuran panik ritel.</p>
                    <p><b>4. Manajemen Lot Otomatis:</b> Alokasi <i>'Max Lot'</i> pada kartu dihitung dinamis menggunakan batas risiko % modal yang Anda geser di Sidebar, divalidasi dengan jarak harga ke Trailing Stop.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else: 
        tab_i1, tab_i2 = st.tabs(["🛡️ VALUE MATRIX", "🧬 CLUSTERS"])
        with tab_i1:
            st.markdown("<h3 style='font-size: 0.9rem; color:#f8fafc;'>🛡️ Top 15 Value</h3>", unsafe_allow_html=True)
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
            render_cross_validation_ui(tuple(str(x) for x in df_inv.index), c_mult, False)
        
        with tab_i2:
            st.markdown("<h3 style='font-size: 0.9rem; color:#f8fafc;'>🧬 Clusters</h3>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown(f"<div class='stocksly-card' style='border-top: 2px solid #0ea5e9;'><div style='color:#0ea5e9; font-size:0.65rem; font-weight:800;'>💎 DEEP VALUE</div>{render_badges(c_val, '#0ea5e9')}</div>", unsafe_allow_html=True)
            with col2: st.markdown(f"<div class='stocksly-card' style='border-top: 2px solid #8b5cf6;'><div style='color:#8b5cf6; font-size:0.65rem; font-weight:800;'>🚀 HIGH GROWTH</div>{render_badges(c_gro, '#8b5cf6')}</div>", unsafe_allow_html=True)
            with col3: st.markdown(f"<div class='stocksly-card' style='border-top: 2px solid #10b981;'><div style='color:#10b981; font-size:0.65rem; font-weight:800;'>💰 DIVIDEND KINGS</div>{render_badges(c_div, '#10b981')}</div>", unsafe_allow_html=True)
