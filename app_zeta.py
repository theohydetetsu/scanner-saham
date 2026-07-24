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
# 0. STATE MANAGEMENT & CACHE
# ==========================================
CACHE_FILE = "jihan_ghina_saham_cache_v165.json"

def load_smart_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache_data = json.load(f)
                loaded_stocks = cache_data.get("raw_stocks", [])
                if loaded_stocks and isinstance(loaded_stocks, list):
                    if "OBP_SCORE" not in loaded_stocks[0]: return [], None
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
st.set_page_config(page_title="JIHAN-GHINA Executive v16.5", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; scroll-behavior: smooth; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -10%, #0f172a, #020617) !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    .block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; padding-left: 2.5rem !important; padding-right: 2.5rem !important; max-width: 100% !important; animation: fadeIn 0.5s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    
    h1 { color: #f8fafc; font-weight: 800; letter-spacing: -1px; font-size: 2.2rem !important; margin-bottom: 0; text-shadow: 0 4px 15px rgba(0,242,254,0.1); }
    h3 { font-weight: 700; letter-spacing: -0.5px; }
    p { color: #94a3b8; font-weight: 300; }
    
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.8); }
    ::-webkit-scrollbar-thumb { background: rgba(0, 242, 254, 0.3); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0, 242, 254, 0.8); }
    
    section[data-testid="stSidebar"] { width: 280px !important; min-width: 280px !important; max-width: 280px !important; background: linear-gradient(180deg, rgba(2,6,23,0.98) 0%, rgba(15,23,42,0.98) 100%) !important; backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.03); }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { font-size: 0.8rem !important; }
    section[data-testid="stSidebar"] label { font-size: 0.75rem !important; font-weight: 700 !important; color: #cbd5e1 !important; letter-spacing: 0.5px; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background-color: rgba(15,23,42,0.4); padding: 4px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.03); }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; border-radius: 6px; color: #64748b; font-weight: 700; font-size:0.85rem; transition: all 0.3s ease; }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 242, 254, 0.1); color: #00f2fe; border: 1px solid rgba(0, 242, 254, 0.2); box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    
    .premium-card { background: rgba(30, 41, 59, 0.2); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.04); border-radius: 12px; padding: 16px; box-shadow: 0 8px 30px -10px rgba(0, 0, 0, 0.4); transition: all 0.3s ease; display: flex; flex-direction: column; }
    .premium-card:hover { transform: translateY(-2px); box-shadow: 0 12px 35px -5px rgba(0, 242, 254, 0.1); border-color: rgba(0, 242, 254, 0.25); }
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 10px 16px !important; background: linear-gradient(135deg, rgba(15,23,42,0.7) 0%, rgba(30,41,59,0.4) 100%); }
    .ihsg-title { color: #64748b; font-size: 0.65rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; }
    .ihsg-score { color: #f8fafc; font-size: 1.5rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
    
    div.stButton > button:first-child { background: linear-gradient(90deg, rgba(30,41,59,0.5) 0%, rgba(15,23,42,0.8) 100%) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #cbd5e1 !important; border-radius: 8px !important; padding: 8px 12px !important; transition: all 0.3s ease; font-weight: 700 !important; font-size: 0.85rem !important; letter-spacing: 0.5px;}
    div.stButton > button:first-child:hover { background: linear-gradient(90deg, rgba(0, 242, 254, 0.15) 0%, rgba(30, 58, 138, 0.2) 100%) !important; color: #00f2fe !important; border-color: rgba(0, 242, 254, 0.4) !important; transform: scale(1.02); }
    
    .stDataFrame { font-size: 13.5px !important; }
    th.row_heading { color: #00f2fe !important; font-weight: 800 !important; font-size: 1rem !important; text-align: center !important; }

    .block-container [data-testid="stRadio"] > div[role="radiogroup"] { gap: 8px; flex-wrap: wrap; margin-top: 5px; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label { background: rgba(30,41,59,0.4) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 6px !important; padding: 6px 14px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important; cursor: pointer; transition: all 0.2s ease !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label:hover { background: rgba(0, 242, 254, 0.08) !important; border-color: rgba(0, 242, 254, 0.4) !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label p { color: #cbd5e1 !important; font-weight: 700 !important; font-size: 0.85rem !important; margin: 0 !important; letter-spacing: 0.5px; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] { background: linear-gradient(135deg, rgba(0,242,254,0.15) 0%, rgba(30,58,138,0.3) 100%) !important; border-color: #00f2fe !important; box-shadow: 0 4px 12px rgba(0, 242, 254, 0.2) !important; transform: scale(1.05) !important; }
    .block-container [data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] p { color: #00f2fe !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE QUOTES
# ==========================================
QUOTES_DATABASE = [
    {"quote": "Order Book (Bid-Offer) adalah suara jujur dari pelaku pasar sebelum harga bergerak.", "author": "Institutional Order Flow", "theme": "Over-Power Logic"},
    {"quote": "Membeli di saat merah (support) dan menjual saat euphoria adalah hukum alam institusi.", "author": "Smart Money Concept", "theme": "Bottom Fishing"},
    {"quote": "Harga adalah apa yang Anda bayar. Nilai adalah apa yang Anda dapatkan.", "author": "Warren Buffett", "theme": "Fundamental"}
]
def get_quote_of_the_day(): return QUOTES_DATABASE[datetime.now(pytz.timezone('Asia/Jakarta')).timetuple().tm_yday % len(QUOTES_DATABASE)]

# ==========================================
# 3. CORE ENGINE & OVER-POWER ORDER FLOW LOGIC
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

def export_df_to_excel_buffer(df_source, scan_time, sheet_name="Data_Saham"):
    df_export = df_source.copy()
    df_export['WAKTU_SCAN'] = scan_time
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer: df_export.to_excel(writer, index=True, sheet_name=sheet_name[:31])
    return buffer.getvalue()

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
        
        info = yf.Ticker(emiten).info or {}
        bid_price = info.get('bid', 0) or h_skg * 0.995
        ask_price = info.get('ask', 0) or h_skg * 1.005
        bid_size = info.get('bidSize', 100) or 500
        ask_size = info.get('askSize', 100) or 500

        # --- OVER-POWER ORDER FLOW LOGIC (NEW v16.5) ---
        # Menghitung Tekanan Antrean (OBP Score)
        obp_score = (bid_size / (bid_size + ask_size)) * 100 if (bid_size + ask_size) > 0 else 50.0

        low_20 = float(df['Low'].tail(20).min())
        dist_to_low = ((h_skg - low_20) / low_20) * 100
        is_near_support = dist_to_low < 5.0 
        is_vol_dry = v_skg < (vol_sma20 * 0.8) 
        is_hammer = (o_skg - lo_skg) > (abs(o_skg - h_skg) * 2)

        # REVISI JUDGMENT ANTI-BONCOS DENGAN BID/OFFER
        if is_near_support and (is_hammer or is_vol_dry) and obp_score >= 50:
            s_bandar = "🎯 SEROK BAWAH (OBP POWER)"
            grade = "🎯 SETUP ANTI-BONCOS (BOTTOM)"
        elif ask_size > (bid_size * 2) and not (h_skg > prev_c):
            s_bandar = "⚠️ TEMBOK JUAL TEBAL (AVOID)"
            grade = "⚠️ SETUP C (AVOID)"
        elif obp_score >= 70 and h_skg >= prev_c:
            s_bandar = "🐋 INSTITUTIONAL BID WALL"
            grade = "⭐ SETUP A+ (HIGH BID)"
        else:
            s_bandar = "🟢 AKUMULASI NORMAL" if wpi_score > 60 else "➖ KONSOLIDASI"
            grade = "✔️ SETUP B"

        div_date_unix = info.get('exDividendDate', None)
        div_date_str = datetime.fromtimestamp(div_date_unix).strftime('%d %b %Y') if div_date_unix else "-"

        return {
            "TICKER": kode, "HARGA": h_skg, "AREA BELI": ema20 if h_skg > ema20 else (low_20 + (h_skg - low_20)*0.3), 
            "TRAILING STOP": t_stop, "WPI_SCORE": round(wpi_score, 1), "OBP_SCORE": round(obp_score, 1),
            "BATAS_ARA": b_ara, "STATUS_ARA_ARB": status_ara, "STATUS_BANDAR": s_bandar, "SETUP_GRADE": grade, "UP_SMA50": h_skg > sma50,
            "PER": round(info.get('trailingPE', 0), 2), "PBV": round(info.get('priceToBook', 1), 2), "PEG": round(info.get('pegRatio') or 0, 2), 
            "DIV_YIELD": round((info.get('trailingAnnualDividendRate', 0) / h_skg * 100) if info.get('trailingAnnualDividendRate', 0) else 0, 2),
            "REVENUE": info.get('totalRevenue', 0), "NET_INCOME": info.get('netIncomeToCommon', 0), "ROE": round(info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0, 2),
            "RET_1D": ((h_skg - prev_c) / prev_c * 100) if prev_c > 0 else 0, "MARKET_CAP": info.get('marketCap', 0), "DIVIDEND_DATE": div_date_str,
            "BID": bid_price, "OFFER": ask_price, "BID_SIZE": bid_size, "OFFER_SIZE": ask_size
        }
    except: return None

# ==========================================
# 4. CHART ENGINE (COMPACT & LOCKED)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_quarterly_charts(emiten):
    try:
        tkr = yf.Ticker(f"{emiten}.JK")
        inc, bs, cf = tkr.quarterly_financials, tkr.quarterly_balance_sheet, tkr.quarterly_cashflow
        if inc.empty and bs.empty: return None, None, None, None
        dates = inc.columns[:4][::-1] if not inc.empty else bs.columns[:4][::-1]
        str_dates = [d.strftime('%b %Y') for d in dates]
        def safe_get(df, keys):
            for k in keys:
                if k in df.index: return df.loc[k][:4][::-1].fillna(0).tolist()
            return [0] * len(str_dates)
        return str_dates, (safe_get(inc, ['Total Revenue']), safe_get(inc, ['Net Income'])), (safe_get(bs, ['Total Assets']), safe_get(bs, ['Total Liabilities'])), (safe_get(cf, ['Operating Cash Flow']), safe_get(cf, ['Free Cash Flow']))
    except: return None, None, None, None

def plot_luxury_bar(x_data, y1, y2, name1, name2, color1, color2, title):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_data, y=y1, name=name1, marker_color=color1, opacity=0.85))
    fig.add_trace(go.Bar(x=x_data, y=y2, name=name2, marker_color=color2, opacity=0.85))
    fig.update_layout(
        height=320, title=dict(text=title, font=dict(color='#cbd5e1', size=13)),
        barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color='#94a3b8', size=10)),
        margin=dict(l=10, r=10, t=35, b=10), dragmode=False, 
        xaxis=dict(showgrid=False, tickfont=dict(color='#64748b'), fixedrange=True),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#64748b'), fixedrange=True)
    )
    return fig

# ==========================================
# 5. CROSS-VALIDATION UI
# ==========================================
def render_cross_validation_ui(active_tickers_tuple, market_climate_mult, is_trading_mode):
    st.markdown("---")
    st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #00f2fe;">
        <h3 style="font-size: 1.6rem; font-weight: 800; color: #f8fafc; margin-bottom: 0px; margin-top: 0px;">⚡ Over-Power Order Flow Terminal</h3>
        <p style="color: #64748b; font-size: 0.8rem; font-weight: 400; margin-top: 2px;">{'Analisis Kedalaman Bid vs Offer & Manajemen Risiko Anti-Boncos.' if is_trading_mode else 'Bedah Laporan Keuangan Riil Kuartalan.'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if active_tickers_tuple:
        safe_key = f"cv_target_v165_{st.session_state.current_tf}_{'TRD' if is_trading_mode else 'INV'}"
        valid_targets = [t for t in active_tickers_tuple if next((i for i in st.session_state.raw_stocks if i.get("TICKER")==t), None)]
        if not valid_targets: return
        
        emiten_signal = st.radio("Target Sniper:", options=valid_targets[:15], horizontal=True, key=safe_key, label_visibility="collapsed")
        raw_target = next((item for item in st.session_state.raw_stocks if item.get("TICKER") == emiten_signal), None)
        
        if raw_target:
            if is_trading_mode:
                setup_grade, h_tgt, obp = raw_target.get("SETUP_GRADE", ""), raw_target.get('HARGA', 0), raw_target.get('OBP_SCORE', 50)
                a_beli = f"{int(raw_target.get('AREA BELI', h_tgt)):,}".replace(",", ".")
                t_stop = f"{int(raw_target.get('TRAILING STOP', h_tgt * 0.95)):,}".replace(",", ".")
                b_ara = f"{int(raw_target.get('BATAS_ARA', 0)):,}".replace(",", ".")
                
                sys_rec, color, r_mult = ("BOTTOM FISHING (SEROK)", "#d4af37", 1.5) if "ANTI-BONCOS" in setup_grade else ("INSTITUTIONAL BUY", "#10b981", 2.0)
                max_lots = int(((modal_trading * (risiko_pct * r_mult * market_climate_mult / 100)) / (h_tgt - raw_target.get('TRAILING STOP', h_tgt*0.95))) / 100) if (h_tgt - raw_target.get('TRAILING STOP', h_tgt*0.95))>0 else 0
                
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.markdown(f"<div class='premium-card' style='padding: 15px;'><div style='text-align: center; color: #64748b; font-size: 0.7rem; font-weight: 800;'>ORDER FLOW DECISION</div><div style='text-align: center; font-size: 1.5rem; font-weight: 800; color: {color}; margin: 4px 0;'>{sys_rec}</div><div style='text-align: center; font-size: 0.8rem; color: #00f2fe; font-weight: 700; margin-bottom: 12px;'>Max Entry: {max_lots:,} Lot</div></div>", unsafe_allow_html=True)
                    s1, s2, s3, s4 = st.columns(4)
                    for col, label, val, c_col in zip([s1,s2,s3,s4], ["HARGA", "AREA BELI", "CUT LOSS", "TARGET ARA"], [int(h_tgt), a_beli, t_stop, b_ara], ["#f8fafc", "#00f2fe", "#f43f5e", "#10b981"]):
                        with col: st.markdown(f"<div style='background: rgba(255,255,255,0.02); padding: 10px 5px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); text-align: center;'><div style='font-size: 0.55rem; color: #64748b; font-weight: 800;'>{label}</div><div style='font-size: 0.95rem; color: {c_col}; font-weight: 800; margin-top: 2px;'>{val}</div></div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div class='premium-card' style='padding: 15px; height: 100%; justify-content: center; align-items: center;'><div style='color: #64748b; font-size: 0.7rem; font-weight: 800;'>ORDER BOOK PRESSURE (OBP)</div><div style='font-size: 2rem; font-weight: 800; color: {'#10b981' if obp>=50 else '#f43f5e'}; margin-top: 5px;'>{obp}% Bid</div></div>", unsafe_allow_html=True)
            else:
                per, pbv, yld = raw_target.get("PER", 0), raw_target.get("PBV", 0), raw_target.get("DIV_YIELD", 0)
                st.markdown(f"<div style='display:flex; justify-content:space-around; background:rgba(30,41,59,0.3); border:1px solid rgba(255,255,255,0.05); border-radius:10px; padding:12px; margin-bottom:15px;'><div style='text-align:center;'><span style='color:#64748b; font-size:0.7rem; font-weight:700;'>PER</span><br><span style='color:#f8fafc; font-weight:800; font-size:1.1rem;'>{per:.1f}x</span></div><div style='text-align:center;'><span style='color:#64748b; font-size:0.7rem; font-weight:700;'>PBV</span><br><span style='color:#f8fafc; font-weight:800; font-size:1.1rem;'>{pbv:.1f}x</span></div><div style='text-align:center;'><span style='color:#64748b; font-size:0.7rem; font-weight:700;'>YIELD</span><br><span style='color:#10b981; font-weight:800; font-size:1.1rem;'>{yld:.1f}%</span></div></div>", unsafe_allow_html=True)
                with st.spinner("Mengunduh Laporan Keuangan..."):
                    dates, inc, bs, cf = fetch_quarterly_charts(emiten_signal)
                    if dates:
                        tab_i, tab_b, tab_c = st.tabs(["📈 Income", "🏛️ Balance", "💸 CashFlow"])
                        with tab_i: st.plotly_chart(plot_luxury_bar(dates, inc[0], inc[1], "Rev", "NetInc", "#0ea5e9", "#10b981", "Income (QoQ)"), use_container_width=True)
                        with tab_b: st.plotly_chart(plot_luxury_bar(dates, bs[0], bs[1], "Assets", "Liab", "#8b5cf6", "#f43f5e", "Balance (QoQ)"), use_container_width=True)
                        with tab_c: st.plotly_chart(plot_luxury_bar(dates, cf[0], cf[1], "OCF", "FCF", "#facc15", "#d4af37", "CashFlow (QoQ)"), use_container_width=True)

# ==========================================
# 6. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #f8fafc; font-size: 1.4rem; font-weight: 800; margin-bottom: -5px;'>Quantum Matrix</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #00f2fe; font-size: 0.65rem; letter-spacing: 2px; margin-bottom: 25px;'>v16.5 OVER-POWER ENGINE</p>", unsafe_allow_html=True)
    
    engine_mode = st.radio("PILIH MODE ENGINE:", ("⚔️ TRADING (Order Flow)", "🛡️ INVESTMENT (Fundamental)"))
    st.markdown("<br>", unsafe_allow_html=True)
    tf_pilihan = st.selectbox("⏱️ TIMEFRAME:", ("1 Hari (Daily)", "1 Minggu (Weekly)"), index=0)
    tf_berubah = tf_pilihan != st.session_state.current_tf
    if tf_berubah: st.session_state.current_tf = tf_pilihan
    modal_trading = int(st.text_input("💰 MODAL TRADING (Rp):", value="50.000.000").replace(".", "").replace(",", ""))
    risiko_pct = st.slider("🚨 BATAS RISIKO (%):", 0.5, 5.0, 1.0, 0.5)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_ph = st.empty()
    if btn_ph.button("🔄 SCAN MARKET", use_container_width=True) or tf_berubah:
        btn_ph.empty() 
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.raw_stocks = []
        my_bar = st.progress(0, text="Memindai Order Flow & Order Book...")
        dyn_tickers = get_dynamic_market_roster()
        for i, t in enumerate(dyn_tickers):
            my_bar.progress((i + 1) / len(dyn_tickers), text=f"Analisis {t} ({i+1}/{len(dyn_tickers)})")
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
# 7. MAIN DASHBOARD
# ==========================================
st.markdown("<h1>Over-Power Order Flow Intelligence</h1>", unsafe_allow_html=True)
df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()

c_h1, c_h2, c_h3 = st.columns([2, 1, 1])
with c_h1:
    q = get_quote_of_the_day()
    st.markdown(f"<div style='margin-top:15px;'><span style='color:#00f2fe; font-size:0.7rem; font-weight:800; letter-spacing:1px;'>{q['theme'].upper()}</span><br><span style='color:#cbd5e1; font-size:0.9rem; font-style:italic;'>\"{q['quote']}\"</span></div>", unsafe_allow_html=True)
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
    st.info("👈 Tekan tombol '🔄 SCAN MARKET' untuk memulai Inisiasi v16.5.")
else:
    h_trd, h_inv = [], []
    c_val, c_gro, c_div = [], [], []
    
    for r in st.session_state.raw_stocks:
        t, h = r.get("TICKER", ""), r.get("HARGA", 0)
        setup_grade = r.get("SETUP_GRADE", "")
        status_ara = r.get("STATUS_ARA_ARB", "")
        t_stop_val = r.get("TRAILING STOP", 0)
        
        bid_str = f"{int(r.get('BID', 0)):,}".replace(",", ".") if r.get('BID', 0) > 0 else "-"
        offer_str = f"{int(r.get('OFFER', 0)):,}".replace(",", ".") if r.get('OFFER', 0) > 0 else "-"
        obp = r.get("OBP_SCORE", 50)
        
        prio = 5 if "ANTI-BONCOS" in setup_grade else (4 if "A+" in setup_grade else (2 if "AVOID" in setup_grade else 3))
        risk_ps = h - t_stop_val
        
        if "AVOID" in setup_grade: rec_lot_text = "🚫 Dilarang Masuk"
        elif risk_ps > 0 and "ARA" not in status_ara:
            max_lots = int(((modal_trading * (risiko_pct * 1.5 * c_mult / 100)) / risk_ps) / 100)
            rec_lot_text = f"Max {max_lots:,} Lot"
        else: rec_lot_text = "🔒 Proteksi/Hold"
        
        h_trd.append({
            "PRIORITY": prio, "RAW_OBP": obp, "TICKER": t, "HARGA": f"{int(h):,}".replace(",", "."), 
            "BID": bid_str, "OFFER": offer_str, "OBP BID 🐋": f"{obp}%",
            "1D GAIN (%)": f"{r.get('RET_1D',0):+.2f}%", "REKOMENDASI LOT": rec_lot_text,
            "TRAILING STOP": f"{int(t_stop_val):,}".replace(",", "."),
            "BANDARMOLOGI": r.get("STATUS_BANDAR", ""), "REKOMENDASI": setup_grade
        })
        
        per, pbv, peg, yld = r.get("PER", 0), r.get("PBV", 0), r.get("PEG", 0), r.get("DIV_YIELD", 0)
        skor = (20 if 0<per<15 else 0) + (20 if 0<pbv<1.5 else 0) + (20 if yld>4 else 0) + (15 if r.get("UP_SMA50") else 0) + (25 if 0<peg<=1.0 else 0)
        h_inv.append({
            "R_YLD": yld, "TICKER": t, "HARGA": f"{int(h):,}".replace(",", "."), "MARKET CAP": format_financials(r.get("MARKET_CAP", 0)),
            "PER (x)": f"{per:.2f}", "PBV (x)": f"{pbv:.2f}", "DIV YIELD (%)": f"{yld:.2f}%",
            "VALUASI": "💎 UNDERVALUED" if skor>=70 else "⚖️ FAIR VALUE"
        })

    df_trd = pd.DataFrame(h_trd).sort_values(["PRIORITY", "RAW_OBP"], ascending=[False, False]).drop(columns=["PRIORITY", "RAW_OBP"]).set_index("TICKER").head(15) if h_trd else pd.DataFrame()
    df_inv = pd.DataFrame(h_inv).sort_values("R_YLD", ascending=False).drop(columns=["R_YLD"]).set_index("TICKER").head(15) if h_inv else pd.DataFrame()

    if "TRADING" in engine_mode:
        st.markdown("<br><h3 style='font-size: 1.3rem; color:#f8fafc;'>🛰️ Top 15 Order Flow & Anti-Boncos Signal</h3>", unsafe_allow_html=True)
        def style_t(row):
            stls = []
            for c, v in row.items():
                if c in ['BID', 'OFFER', 'OBP BID 🐋']: stls.append('color:#00f2fe; font-weight:800; text-align:center;')
                elif c == 'REKOMENDASI': stls.append('color:#d4af37; font-weight:800;' if 'ANTI-BONCOS' in v else ('color:#f43f5e; font-weight:800;' if 'AVOID' in v else 'color:#10b981;'))
                else: stls.append('color:#cbd5e1;')
            return stls
        if not df_trd.empty: st.dataframe(df_trd.style.apply(style_t, axis=1), use_container_width=True)
        render_cross_validation_ui(tuple(str(x) for x in df_trd.index), c_mult, True)
    else:
        st.markdown("<br><h3 style='font-size: 1.3rem; color:#f8fafc;'>🛡️ Top 15 Dividend & Value</h3>", unsafe_allow_html=True)
        if not df_inv.empty: st.dataframe(df_inv, use_container_width=True)
        render_cross_validation_ui(tuple(str(x) for x in df_inv.index), c_mult, False)
