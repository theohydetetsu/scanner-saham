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
CONFIG_FILE = "jihan_ghina_config.json" 

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
# 1. KONFIGURASI HALAMAN & UI STYLE (FULL WIDE)
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA Ultimate v12.4", page_icon="🧬", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -20%, #0f172a, #020617) !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    [data-testid="stAppViewBlockContainer"] { max-width: 100% !important; }
    
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
    
    div.stButton > button:first-child { background: linear-gradient(90deg, rgba(0,242,254,0.1) 0%, rgba(30,58,138,0.2) 100%) !important; border: 1px solid rgba(0, 242, 254, 0.4) !important; color: #00f2fe !important; border-radius: 8px !important; padding: 10px 15px !important; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
    div.stButton > button:first-child p { color: #00f2fe !important; font-weight: 900 !important; font-size: 0.95rem !important; letter-spacing: 1px; margin: 0; }
    div.stButton > button:first-child:hover { background: linear-gradient(90deg, #00f2fe 0%, #3b82f6 100%) !important; transform: translateY(-2px); box-shadow: 0 10px 20px -5px rgba(0, 242, 254, 0.4); border-color: transparent !important; }
    
    .login-header { text-align: center; color: #00f2fe; font-size: 2.4rem; font-weight: 900; margin-top: 80px; margin-bottom: 5px; letter-spacing: -1px; }
    .stDataFrame { font-size: 13.5px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1.5. SISTEM KEAMANAN
# ==========================================
USERNAME_RAHASIA = "theo"
PASSWORD_RAHASIA = "216455"

if "akses_diberikan" not in st.session_state: st.session_state.akses_diberikan = False

if not st.session_state.akses_diberikan:
    st.markdown("<div class='login-header'>🔒 QUANTUM MATRIX TERMINAL</div>", unsafe_allow_html=True)
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
# 2. CORE ENGINE DATA FETCHING & UI HELPERS
# ==========================================
roster_100_saham = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", "AMRT",
    "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", "CPIN", "ANTM",
    "AMMN", "BREN", "CUAN", "PANI", "BRPT", "MDKA", "MEDC", "ARTO", "SIDO", "MYOR",
    "INKP", "TKIM", "SMGR", "INTP", "BFIN", "AKRA", "ESSA", "EXCL", "ISAT", "TOWR",
    "TBIG", "MTEL", "MAPI", "MAPA", "ACES", "ERAA", "AUTO", "NISP", "BDMN", "BTPS",
    "BBTN", "BNGA", "BRMS", "BUMI", "ENRG", "DEWA", "DOID", "HRUM", "INCO", "PTMP",
    "VKTR", "GGRM", "HMSP", "WIIM", "JSMR", "WIKA", "PTPP", "ADHI", "SMRA", "BSDE",
    "CTRA", "PWON", "ASRI", "SSIA", "SRTG", "BMTR", "MNCN", "EMTK", "SCMA", "BUAH",
    "CLEO", "CMRY", "SILO", "MIKA", "HEAL", "TPIA", "MBMA", "NCKL", "PGEO", "AVIA",
    "ARNA", "MARK", "INAF", "KAEF", "WOOD", "TAPG", "DSNG", "LSIP", "AALI", "SSMS"
]
daftar_saham = [s.strip().upper() + ".JK" for s in roster_100_saham]

def render_badges(tickers, hex_color):
    if not tickers: 
        return "<span style='color:#64748b; font-size:0.8rem; font-style:italic; display:block; margin-top:10px;'>Belum ada emiten terdeteksi di zona ini.</span>"
    res = "<div style='display:flex; flex-wrap:wrap; gap:8px; margin-top:15px;'>"
    for t in tickers:
        res += f"<span style='background:rgba(0,0,0,0.3); border:1px solid {hex_color}60; border-radius:6px; padding:4px 10px; color:{hex_color}; font-size:0.85rem; font-weight:800; box-shadow: 0 2px 4px rgba(0,0,0,0.3); letter-spacing:0.5px;'>{t}</span>"
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
        if "1 Jam" in mode_tf: per, inv = "60d", "1h"
        elif "4 Jam" in mode_tf: per, inv = "60d", "1h"
        elif "1 Minggu" in mode_tf: per, inv = "2y", "1wk"
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
        if len(df) < 25: return None 
        
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['SMA5'] = df['Close'].rolling(window=5).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['RSI'] = hitung_rsi_akurat(df)
        df['ATR'] = hitung_atr(df)
        df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()
        df['Val_SMA10'] = (df['Close'] * df['Volume']).rolling(window=10).mean()
        
        harga_skg = float(df['Close'].iloc[-1])
        open_skg = float(df['Open'].iloc[-1])
        high_skg = float(df['High'].iloc[-1])
        low_skg = float(df['Low'].iloc[-1])
        ema20_skg = float(df['EMA20'].iloc[-1])
        sma5_skg = float(df['SMA5'].iloc[-1]) if not pd.isna(df['SMA5'].iloc[-1]) else ema20_skg
        sma50_skg = float(df['SMA50'].iloc[-1]) if not pd.isna(df['SMA50'].iloc[-1]) else ema20_skg
        vol_skg = float(df['Volume'].iloc[-1])
        vol_sma20 = float(df['Vol_SMA20'].iloc[-1])
        atr_skg = float(df['ATR'].iloc[-1])
        
        prev_close = float(df['Close'].iloc[-2])
        prev_vol = float(df['Volume'].iloc[-2])
        ret_1d = ((harga_skg - prev_close) / prev_close * 100) if prev_close > 0 else 0
        trans_val = harga_skg * vol_skg
        trans_val_ma10 = float(df['Val_SMA10'].iloc[-1])
        
        volatilitas_pct = (atr_skg / harga_skg) * 100 if harga_skg > 0 else 0
        if volatilitas_pct >= 3.5: volatilitas_stat = "🔥 TINGGI"
        elif volatilitas_pct >= 1.5: volatilitas_stat = "⚡ MODERAT"
        else: volatilitas_stat = "❄️ RENDAH"
        
        is_bullish_candle = harga_skg >= open_skg
        if (vol_skg > (vol_sma20 * 1.2)) and is_bullish_candle and (harga_skg > ema20_skg): status_bandar = "AKUMULASI" 
        elif (vol_skg > (vol_sma20 * 1.2)) and not is_bullish_candle: status_bandar = "DISTRIBUSI" 
        else: status_bandar = "NEUTRAL"
        
        high_history = float(df['High'].tail(20).max())
        low_history = float(df['Low'].tail(20).min())
        
        tkr = yf.Ticker(emiten)
        info = tkr.info if tkr.info else {}
        per_val = info.get('trailingPE', 0.0)
        pbv_val = info.get('priceToBook', 1.0)
        div_rate = info.get('trailingAnnualDividendRate', 0)
        div_yield = (div_rate / harga_skg * 100) if (div_rate and harga_skg > 0) else 0.0
        
        mcap = info.get('marketCap', 0)
        eps_ttm = info.get('trailingEps', 0.0)
        div_date_unix = info.get('exDividendDate', None)
        div_date_str = "-"
        if div_date_unix:
            try: div_date_str = datetime.fromtimestamp(div_date_unix).strftime('%d %b %Y')
            except: pass
        
        float_shares = info.get('floatShares', 0)
        out_shares = info.get('sharesOutstanding', 0)
        float_pct = (float_shares / out_shares * 100) if out_shares and float_shares else 0
            
        return {
            "TICKER": kode, "HARGA": harga_skg, 
            "AREA BELI": ema20_skg if harga_skg > ema20_skg else (low_history + (harga_skg - low_history)*0.3), 
            "TARGET (TP)": harga_skg * 1.05 if high_history <= harga_skg else high_history,
            "STOP LOSS": harga_skg * 0.96 if low_history >= harga_skg else low_history,
            "VOLATILITAS": volatilitas_stat, "RSI": round(float(df['RSI'].iloc[-1]), 2),
            "STATUS_BANDAR": status_bandar,
            "UP_EMA20": harga_skg > ema20_skg, 
            "UP_SMA50": harga_skg > sma50_skg,
            "MACD_GOLDEN": float(df['MACD'].iloc[-1]) > float(df['Signal'].iloc[-1]),
            "PER": round(per_val, 2), "PBV": round(pbv_val, 2), "DIV_YIELD": round(div_yield, 2),
            "PREV_VOL": prev_vol, "VOL_SMA20": vol_sma20, "RET_1D": ret_1d, "HIGH": high_skg, 
            "LOW": low_skg, "SMA5": sma5_skg, "SMA50": sma50_skg, "TRANS_VAL": trans_val, 
            "TRANS_VAL_MA10": trans_val_ma10, "FLOAT_PCT": float_pct, "VOLUME": vol_skg,
            "MARKET_CAP": mcap, "EPS_TTM": eps_ttm, "DIVIDEND_DATE": div_date_str
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

# ==========================================
# 3. CHART & ANALYST DATA FETCHING
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

# ==========================================
# 4. FUNGSI RENDER CROSS-VALIDATION UI (OVERHAULED)
# ==========================================
def render_cross_validation_ui(active_tickers_list):
    st.markdown("---")
    st.markdown("""
    <div style="margin-top: 15px; margin-bottom: 20px; padding-left: 5px; border-left: 5px solid #00f2fe;">
        <h3 style="font-size: 1.8rem; font-weight: 900; color: #f8fafc; margin-bottom: 0px; margin-top: 0px; letter-spacing: -0.5px;">🎯 Executive Cross-Validation</h3>
        <p style="color: #94a3b8; font-size: 0.85rem; font-weight: 400; margin-top: 4px;">Pilih salah satu kode emiten dari tabel di atas untuk membandingkan kalkulasi <strong style="color:#00f2fe;">JIHAN-GHINA AI</strong> dengan <strong style="color:#fbbf24;">Sentimen Analis Global</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if active_tickers_list:
        emiten_signal = st.selectbox(
            "Pindai Detil Emiten:", 
            active_tickers_list, 
            key=f"signal_select_{st.session_state.current_tf}"
        )
        
        with st.spinner(f"Mengkalkulasi Konfirmasi Ganda untuk {emiten_signal}..."):
            raw_target = next((item for item in st.session_state.raw_stocks if item["TICKER"] == emiten_signal), None)
            
            if raw_target:
                vol_target = raw_target['VOLATILITAS']
                bandar_target = raw_target['STATUS_BANDAR']
                area_beli = f"{int(raw_target['AREA BELI']):,}".replace(",", ".")
                target_tp = f"{int(raw_target['TARGET (TP)']):,}".replace(",", ".")
                stop_loss = f"{int(raw_target['STOP LOSS']):,}".replace(",", ".")
                
                skor_algo = 0
                if raw_target["UP_EMA20"]: skor_algo += 10
                if raw_target.get("UP_SMA50", False): skor_algo += 10 
                if raw_target["MACD_GOLDEN"]: skor_algo += 15
                if raw_target["RSI"] < 40: skor_algo += 15
                elif 40 <= raw_target["RSI"] <= 65: skor_algo += 10
                elif raw_target["RSI"] > 70: skor_algo -= 15
                if raw_target["STATUS_BANDAR"] == "AKUMULASI": skor_algo += 25
                elif raw_target["STATUS_BANDAR"] == "DISTRIBUSI": skor_algo -= 20
                else: skor_algo += 5
                
                target_skor = 65 if "Agresif" in profil_risiko else (78 if "Konservatif" in profil_risiko else 72)
                sys_rec_raw = "ACCUMULATE" if skor_algo >= target_skor else ("HOLD" if skor_algo >= 50 else "LIQUIDATE")
                if vol_target == "🔥 TINGGI" and bandar_target == "DISTRIBUSI": sys_rec_raw = "LIQUIDATE"  
                elif vol_target == "❄️ RENDAH" and sys_rec_raw == "ACCUMULATE": sys_rec_raw = "HOLD"
                
                risk_per_share = raw_target["HARGA"] - raw_target["STOP LOSS"]
                if "ACCUMULATE" in sys_rec_raw and risk_per_share > 0:
                    max_lots = int(((modal_trading * (risiko_pct / 100)) / risk_per_share) / 100)
                    lot_rec_target = f"Max {max_lots:,} Lot" if max_lots > 0 else "Beli Minimal"
                else: lot_rec_target = "Proteksi / Tahan Posisi"
                
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
                    desc = "PROTEKSI DIALIRKAN: Saham mengalami volatilitas tinggi dengan distribusi bandar masif. Sistem memblokir sinyal beli."
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
                    desc = "Bandarmologi mendeteksi pergerakan beli, namun Analis belum menaikkan rating. Akumulasi bertahap."
                elif sys_is_sell and not ana_is_sell:
                    final_decision = "🟠 CAUTIOUS SELL (ALGO-DRIVEN)"
                    color = "#fb923c"
                    desc = "Mesin mendeteksi pelemahan tren, meskipun Analis masih optimis. Pasang Trailing Stop ketat."
                elif sys_is_hold and ana_is_hold:
                    final_decision = "⚖️ SOLID HOLD"
                    color = "#fbbf24"
                    desc = "Konsolidasi market. Tidak ada tekanan jual/beli signifikan. Tahan posisi (Hold)."
                else:
                    final_decision = "🔍 MIXED SIGNAL (MONITOR)"
                    color = "#a855f7"
                    desc = "Terdapat deviasi antara data algoritma dan konsensus analis. Disarankan memantau ketat pergerakan harga."

                if is_sleeping and "HOLD" in sys_rec_raw:
                    desc += " (Sistem mengunci di posisi HOLD karena saham sedang 'tidur')."
                    
                # NEW REFACTORED HTML FOR ELEGANT VALIDATION BOX
                final_box_html = f"""
<div style='background: linear-gradient(145deg, rgba(15,23,42,0.8) 0%, rgba(2,6,23,0.9) 100%); border: 1px solid {color}50; border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px -10px {color}40; position: relative; overflow: hidden; margin-top: 10px; margin-bottom: 30px; backdrop-filter: blur(10px);'>
    <div style='position: absolute; top: 0; left: 0; right: 0; height: 4px; background: {color}; box-shadow: 0 0 20px {color};'></div>
    
    <div style='display: flex; flex-wrap: wrap; gap: 20px;'>
        <div style='flex: 1.5; min-width: 300px; background: rgba(0,0,0,0.4); border-radius: 12px; padding: 20px; border: 1px solid rgba(255,255,255,0.05);'>
            <div style='display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 10px;'>
                <span style='background: rgba(0,242,254,0.1); padding: 8px; border-radius: 8px; font-size:1.2rem;'>💻</span>
                <span style='color: #94a3b8; font-size: 0.85rem; font-weight: 800; letter-spacing: 1.5px;'>JIHAN-GHINA ALGO SCORE</span>
            </div>
            <div style='text-align: center; font-size: 1.8rem; font-weight: 900; color: #f8fafc; letter-spacing: -0.5px; margin-bottom: 20px;'>{sys_rec_raw}</div>
            
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;'>
                <div style='text-align: center; background: rgba(56, 189, 248, 0.05); padding: 12px 8px; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.15); transition: transform 0.2s;'>
                    <div style='font-size: 0.65rem; color: #94a3b8; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 4px;'>AREA BELI</div>
                    <div style='font-size: 1rem; color: #38bdf8; font-weight: 900;'>{area_beli}</div>
                </div>
                <div style='text-align: center; background: rgba(16, 185, 129, 0.05); padding: 12px 8px; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.15); transition: transform 0.2s;'>
                    <div style='font-size: 0.65rem; color: #94a3b8; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 4px;'>TARGET (TP)</div>
                    <div style='font-size: 1rem; color: #10b981; font-weight: 900;'>{target_tp}</div>
                </div>
                <div style='text-align: center; background: rgba(244, 63, 94, 0.05); padding: 12px 8px; border-radius: 10px; border: 1px solid rgba(244, 63, 94, 0.15); transition: transform 0.2s;'>
                    <div style='font-size: 0.65rem; color: #94a3b8; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 4px;'>STOP LOSS</div>
                    <div style='font-size: 1rem; color: #f43f5e; font-weight: 900;'>{stop_loss}</div>
                </div>
            </div>
        </div>

        <div style='flex: 1; min-width: 250px; background: rgba(0,0,0,0.4); border-radius: 12px; padding: 20px; border: 1px solid rgba(255,255,255,0.05); display: flex; flex-direction: column; justify-content: center; align-items: center;'>
            <div style='display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 10px;'>
                <span style='background: rgba(251, 191, 36, 0.1); padding: 8px; border-radius: 8px; font-size:1.2rem;'>🌍</span>
                <span style='color: #94a3b8; font-size: 0.85rem; font-weight: 800; letter-spacing: 1.5px;'>GLOBAL ANALYST CONSENSUS</span>
            </div>
            <div style='text-align: center; font-size: 1.8rem; font-weight: 900; color: #f8fafc; letter-spacing: -0.5px;'>{konsensus_raw if konsensus_raw != 'N/A' else 'DATA UNAVAILABLE'}</div>
            <div style='margin-top: 15px; font-size: 0.75rem; color: #64748b; text-align: center; max-width: 80%;'>Agregasi data sentimen institusi & analis sekuritas global.</div>
        </div>
    </div>

    <div style='margin-top: 20px; background: rgba(0,0,0,0.6); border: 1px solid {color}40; border-radius: 12px; padding: 25px; text-align: center;'>
        <div style='color: {color}; font-size: 0.8rem; font-weight: 900; letter-spacing: 3px; margin-bottom: 10px; text-transform: uppercase;'>🏆 Ultimate Final Decision</div>
        <div style='color: {color}; font-size: 2rem; font-weight: 900; letter-spacing: -0.5px; margin-bottom: 12px; text-shadow: 0 0 20px {color}60;'>{final_decision}</div>
        <div style='color: #cbd5e1; font-size: 0.95rem; font-weight: 300; max-width: 700px; margin: 0 auto; line-height: 1.6;'>{desc}</div>
        
        <div style='margin-top: 25px;'>
            <span style='background: linear-gradient(90deg, rgba(0,242,254,0.1) 0%, rgba(30,58,138,0.2) 100%); border: 1px solid #00f2fe60; padding: 12px 30px; border-radius: 30px; color: #00f2fe; font-size: 0.9rem; font-weight: 900; letter-spacing: 1px; box-shadow: 0 5px 15px rgba(0,242,254,0.15); display: inline-block;'>🎯 LOT SIZING: {lot_rec_target}</span>
        </div>
    </div>
</div>
"""
                st.markdown(final_box_html, unsafe_allow_html=True)
    else:
        st.info("Belum ada data emiten untuk disinkronkan.")


# ==========================================
# 5. SIDEBAR (DUAL CORE CONTROL)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #00f2fe; font-size: 1.25rem; font-weight: 900; margin-bottom: 0px;'>🧬 QUANTUM MATRIX</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.65rem; letter-spacing: 1.5px; margin-bottom: 25px;'>DUAL-CORE EDITION v12.4</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='font-size:0.75rem; color:#facc15; font-weight:800; letter-spacing:1px; border-bottom: 1px solid rgba(250,204,21,0.2); padding-bottom: 5px; margin-bottom: 10px;'>🎛️ CORE ENGINE MODE</div>", unsafe_allow_html=True)
    engine_mode = st.radio("Pilih Mode Analisis:", ["⚔️ TRADING (Momentum & Technical)", "🛡️ INVESTMENT (Value & Fundamental)"])
    st.markdown("<br>", unsafe_allow_html=True)

    tf_pilihan = st.selectbox("⏱️ Timeframe Analisis:", ["1 Jam", "4 Jam", "1 Hari (Daily)", "1 Minggu (Weekly)"], index=2)
    tf_berubah = tf_pilihan != st.session_state.current_tf
    if tf_berubah: st.session_state.current_tf = tf_pilihan
        
    st.markdown("<div style='font-size:0.7rem; color:#00f2fe; font-weight:800; letter-spacing:1px; margin-top:20px; border-bottom: 1px solid rgba(0,242,254,0.2); padding-bottom: 5px;'>🎯 RISK PROFILE ENGINE</div>", unsafe_allow_html=True)
    profil_risiko = st.selectbox("Tingkat Agresivitas AI:", ["⚖️ Moderat (Balanced)", "🔥 Agresif (High Signal)", "🛡️ Konservatif (Strict)"], index=0, help="Fungsi SANGAT PENTING. Mengatur seberapa ketat AI memfilter sinyal beli.")
    
    st.markdown("<div style='font-size:0.7rem; color:#00f2fe; font-weight:800; letter-spacing:1px; margin-top:20px; border-bottom: 1px solid rgba(0,242,254,0.2); padding-bottom: 5px;'>⚙️ POSITION SIZING</div>", unsafe_allow_html=True)
    modal_input_str = st.text_input("💰 Modal Trading (Rp):", value="50.000.000", help="Gunakan titik untuk memisahkan ribuan")
    try: modal_trading = int(modal_input_str.replace(".", "").replace(",", ""))
    except: modal_trading = 50000000
    risiko_pct = st.slider("🚨 Batas Risiko /Trade (%):", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
    
    with st.expander("🤖 Telegram Automation Alert"):
        st.markdown("<p style='font-size: 0.7rem; color: #10b981;'>Data otomatis tersimpan ke server.</p>", unsafe_allow_html=True)
        bot_token = st.text_input("Bot Token:", value=app_config["tg_token"], type="password")
        chat_id = st.text_input("Chat ID:", value=app_config["tg_chat_id"])
        if bot_token != app_config["tg_token"] or chat_id != app_config["tg_chat_id"]:
            save_config(bot_token, chat_id)
            app_config["tg_token"] = bot_token
            app_config["tg_chat_id"] = chat_id
            st.success("Config Telegram Tersimpan!")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔄 SCAN 100 SAHAM", use_container_width=True) or tf_berubah:
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.page_matrix = 0 
        st.session_state.raw_stocks = []
        
        my_bar = st.progress(0, text=f"Scanning 100 Emiten Terlikuid ({st.session_state.current_tf})...")
        for i, t in enumerate(daftar_saham):
            my_bar.progress((i + 1) / len(daftar_saham), text=f"Analyzing {t} ({i+1}/100)")
            data = fetch_single_stock(t, st.session_state.current_tf)
            if data: st.session_state.raw_stocks.append(data)
            gc.collect() 
            
        my_bar.empty()
        st.session_state.last_update = get_waktu_wib()
        
        token_aktif = app_config["tg_token"]
        chat_aktif = app_config["tg_chat_id"]
        
        if token_aktif and chat_aktif and len(st.session_state.raw_stocks) > 0:
            alert_text = f"🤖 *JIHAN-GHINA ALERTS* | {st.session_state.current_tf}\nMode: {engine_mode}\n\n"
            has_buys = False
            for raw in st.session_state.raw_stocks:
                skor = 0
                if raw["UP_EMA20"]: skor += 10
                if raw.get("UP_SMA50", False): skor += 10 
                if raw["MACD_GOLDEN"]: skor += 15
                if raw["RSI"] < 40: skor += 15
                elif 40 <= raw["RSI"] <= 65: skor += 10
                elif raw["RSI"] > 70: skor -= 15
                if raw["STATUS_BANDAR"] == "AKUMULASI": skor += 25
                elif raw["STATUS_BANDAR"] == "DISTRIBUSI": skor -= 20
                else: skor += 5
                
                target_skor = 65 if "Agresif" in profil_risiko else (78 if "Konservatif" in profil_risiko else 72)
                kep = "ACCUMULATE" if skor >= target_skor else ("HOLD" if skor >= 50 else "LIQUIDATE")
                if raw["VOLATILITAS"] == "🔥 TINGGI" and raw["STATUS_BANDAR"] == "DISTRIBUSI": kep = "LIQUIDATE"  
                elif raw["VOLATILITAS"] == "❄️ RENDAH" and kep == "ACCUMULATE": kep = "HOLD"
                
                if kep == "ACCUMULATE":
                    has_buys = True
                    alert_text += f"✅ *{raw['TICKER']}* | Hrg: Rp{int(raw['HARGA']):,} | {raw['VOLATILITAS']}\n"
            
            if has_buys:
                try: requests.post(f"https://api.telegram.org/bot{token_aktif}/sendMessage", json={"chat_id": chat_aktif, "text": alert_text[:4000], "parse_mode": "Markdown"})
                except: pass

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

col_h1, col_h2 = st.columns([3.5, 1.5])
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

st.markdown("---")

if not st.session_state.scan_clicked or not st.session_state.raw_stocks:
    st.info("👈 Sistem terminal siaga. Silakan tekan tombol '🔄 SCAN 100 SAHAM' di panel navigasi kiri.")
else:
    hasil_trading = []
    hasil_invest = []
    
    cluster_ara = []
    cluster_scalp = []
    cluster_accum = []
    cluster_div = []
    cluster_undervalued = []
    cluster_bluechip = []
    
    for raw in st.session_state.raw_stocks:
        skor_t = 0
        if raw["UP_EMA20"]: skor_t += 10
        if raw.get("UP_SMA50", False): skor_t += 10 
        if raw["MACD_GOLDEN"]: skor_t += 15
        if raw["RSI"] < 40: skor_t += 15
        elif 40 <= raw["RSI"] <= 65: skor_t += 10
        elif raw["RSI"] > 70: skor_t -= 15
        if raw["STATUS_BANDAR"] == "AKUMULASI": skor_t += 25
        elif raw["STATUS_BANDAR"] == "DISTRIBUSI": skor_t -= 20
        else: skor_t += 5
        
        target_skor_t = 65 if "Agresif" in profil_risiko else (78 if "Konservatif" in profil_risiko else 72)
        if skor_t >= target_skor_t: kep_t = "🟢 ACCUMULATE"
        elif skor_t >= 50: kep_t = "🟡 HOLD"
        else: kep_t = "🔴 LIQUIDATE"
        
        if raw["VOLATILITAS"] == "🔥 TINGGI" and raw["STATUS_BANDAR"] == "DISTRIBUSI": kep_t = "🔴 LIQUIDATE"  
        elif raw["VOLATILITAS"] == "❄️ RENDAH" and kep_t == "🟢 ACCUMULATE": kep_t = "🟡 HOLD"       
        
        max_loss_money = modal_trading * (risiko_pct / 100)
        risk_per_share = raw["HARGA"] - raw["STOP LOSS"]
        if "ACCUMULATE" in kep_t and risk_per_share > 0:
            max_lots = int((max_loss_money / risk_per_share) / 100)
            rec_lot_text = f"🔥 Max {max_lots:,} Lot" if max_lots > 0 else "Beli Minimal"
        else: rec_lot_text = "🔒 Proteksi/Hold"

        skor_i = 0
        if 0 < raw["PER"] < 15: skor_i += 30
        if 0 < raw["PBV"] < 1.5: skor_i += 30
        if raw["DIV_YIELD"] > 4.0: skor_i += 20
        if raw["UP_SMA50"]: skor_i += 20
        
        if skor_i >= 70: kep_i = "💎 UNDERVALUED (BUY)"
        elif skor_i >= 40: kep_i = "⚖️ FAIR VALUE (HOLD)"
        else: kep_i = "⚠️ OVERVALUED (AVOID)"
            
        hasil_trading.append({
            "RAW_RET": raw["RET_1D"], 
            "TICKER": raw["TICKER"], 
            "HARGA": f"{int(raw['HARGA']):,}".replace(",", "."),
            "1D GAIN (%)": f"{raw['RET_1D']:+.2f}%",
            "REKOMENDASI LOT": rec_lot_text,
            "VOLATILITAS": raw["VOLATILITAS"],
            "RSI": f"{raw['RSI']:.2f}", 
            "BANDARMOLOGI": raw["STATUS_BANDAR"], 
            "REKOMENDASI": kep_t
        })
        
        hasil_invest.append({
            "RAW_YIELD": raw["DIV_YIELD"], 
            "TICKER": raw["TICKER"], 
            "HARGA": f"{int(raw['HARGA']):,}".replace(",", "."),
            "MARKET CAP": format_market_cap(raw.get("MARKET_CAP", 0)),
            "PER (x)": f"{raw['PER']:.2f}",
            "PBV (x)": f"{raw['PBV']:.2f}",
            "DIV YIELD (%)": f"{raw['DIV_YIELD']:.2f}%",
            "VALUASI": kep_i
        })
        
        if (raw["PREV_VOL"] > (2 * raw["VOL_SMA20"])) and (raw["TRANS_VAL"] > raw["TRANS_VAL_MA10"]) and (raw["RET_1D"] > 3) and (raw["HIGH"] > raw["SMA5"]) and (raw["LOW"] > raw["SMA50"]):
            cluster_ara.append(raw["TICKER"])
        if (1 < raw["RET_1D"] < 10) and (raw["TRANS_VAL"] > 2_000_000_000) and (raw["HARGA"] < 3000) and (raw["VOLUME"] > 50_000_000):
            cluster_scalp.append(raw["TICKER"])
        harga_tengah = (raw["HIGH"] + raw["LOW"]) / 2
        if (raw["VOLUME"] > (1.5 * raw["VOL_SMA20"])) and (raw["HARGA"] > raw["UP_EMA20"]) and (raw["HARGA"] >= harga_tengah):
            cluster_accum.append(raw["TICKER"])
            
        if raw["DIV_YIELD"] >= 5.0: cluster_div.append(raw["TICKER"])
        if (0 < raw["PBV"] <= 1.2) and (0 < raw["PER"] <= 12): cluster_undervalued.append(raw["TICKER"])
        if raw["TICKER"] in roster_100_saham[:30]: cluster_bluechip.append(raw["TICKER"])

    df_trading = pd.DataFrame(hasil_trading).sort_values(by="RAW_RET", ascending=False).reset_index(drop=True).drop(columns=["RAW_RET"])
    df_invest = pd.DataFrame(hasil_invest).sort_values(by="RAW_YIELD", ascending=False).reset_index(drop=True).drop(columns=["RAW_YIELD"])

    top_trading_tickers = df_trading.head(15)["TICKER"].tolist()
    top_invest_tickers = df_invest.head(15)["TICKER"].tolist()

    # ------------------------------------------
    # RENDER TABS BERDASARKAN MODE
    # ------------------------------------------
    if "TRADING" in engine_mode:
        tab1, tab2, tab3, tab4 = st.tabs(["🚀 TRADING SIGNAL (TOP GAINERS)", "🧬 MOMENTUM CLUSTERS", "📊 FUNDAMENTAL CHARTS", "📚 ACADEMY"])
        
        with tab1:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🛰️ Pro Max Trading Matrix (Sorted by Top Gainers)</h3>", unsafe_allow_html=True)
            def style_trading(row):
                styles = []
                if '🟢' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(16, 185, 129, 0.12); color: #34d399;'
                elif '🟡' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(245, 158, 11, 0.12); color: #fbbf24;'
                else: bg_rek = 'background-color: rgba(244, 63, 94, 0.12); color: #fb7185;'
                
                for c, val in row.items():
                    if c == 'TICKER': styles.append('font-weight: 900; font-size: 1.15rem; color: #00f2fe; text-shadow: 0px 0px 10px rgba(0,242,254,0.3); text-align:center;')
                    elif c == '1D GAIN (%)':
                        if '+' in str(val): styles.append('color: #10b981; font-weight: 900; background: rgba(16,185,129,0.1);')
                        elif '-' in str(val) and val != '-0.00%': styles.append('color: #f43f5e; font-weight: 900;')
                        else: styles.append('color: #94a3b8;')
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

            st.dataframe(df_trading.head(15).style.apply(style_trading, axis=1), use_container_width=True, hide_index=True)
            st.markdown("<p style='color:#94a3b8; font-size:0.8rem; text-align:center;'>Menampilkan Top 15 Saham Penggerak Hari Ini.</p>", unsafe_allow_html=True)
            
            render_cross_validation_ui(top_trading_tickers)

        with tab2:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🧬 Behavioral Trading Clusters</h3>", unsafe_allow_html=True)
            c_ara, c_scalp, c_accum = st.columns(3)
            with c_ara:
                badges_ara = render_badges(cluster_ara, "#f43f5e")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #f43f5e; height: 100%;'>
                    <div style='color:#f43f5e; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>🚀 1. ARA HUNTER</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Lonjakan volume transaksi meledak menembus resisten pendek. Target naik agresif.</div>
                    {badges_ara}
                </div>
                """, unsafe_allow_html=True)
            with c_scalp:
                badges_scalp = render_badges(cluster_scalp, "#00f2fe")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #00f2fe; height: 100%;'>
                    <div style='color:#00f2fe; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>⚡ 2. SCALPING DAILY</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Saham lapis dua dengan volatilitas lincah dan perputaran uang miliaran harian.</div>
                    {badges_scalp}
                </div>
                """, unsafe_allow_html=True)
            with c_accum:
                badges_accum = render_badges(cluster_accum, "#10b981")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #10b981; height: 100%;'>
                    <div style='color:#10b981; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>🐋 3. BIG ACCUMULATION</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Jejak paus terdeteksi! Harga ditutup kuat di pucuk disertai volume serok masif.</div>
                    {badges_accum}
                </div>
                """, unsafe_allow_html=True)

    else:
        # MODE INVESTMENT
        tab1, tab2, tab3, tab4 = st.tabs(["🛡️ VALUE MATRIX (TOP DIVIDEND)", "🏦 FUNDAMENTAL CLUSTERS", "📊 FUNDAMENTAL CHARTS", "📚 ACADEMY"])
        
        with tab1:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🛡️ Pro Max Investment Matrix (Sorted by Div Yield)</h3>", unsafe_allow_html=True)
            def style_invest(row):
                styles = []
                for c, val in row.items():
                    if c == 'TICKER': styles.append('font-weight: 900; font-size: 1.15rem; color: #facc15; text-shadow: 0px 0px 10px rgba(250,204,21,0.3); text-align:center;')
                    elif c == 'DIV YIELD (%)':
                        if val != '0.00%': styles.append('color: #10b981; font-weight: 900; background: rgba(16,185,129,0.1);')
                        else: styles.append('color: #64748b;')
                    elif c in ['PER (x)', 'PBV (x)']:
                        try:
                            v = float(val)
                            if (c == 'PER (x)' and 0 < v < 15) or (c == 'PBV (x)' and 0 < v < 1.2): styles.append('color: #38bdf8; font-weight: 800;')
                            elif v > 20 or v > 2.5: styles.append('color: #f43f5e; font-weight: 800;')
                            else: styles.append('color: #cbd5e1;')
                        except: styles.append('')
                    elif c == 'VALUASI':
                        if 'BUY' in val: styles.append('background-color: rgba(16, 185, 129, 0.12); color: #34d399; font-weight:800;')
                        elif 'HOLD' in val: styles.append('background-color: rgba(245, 158, 11, 0.12); color: #fbbf24; font-weight:800;')
                        else: styles.append('background-color: rgba(244, 63, 94, 0.12); color: #fb7185; font-weight:800;')
                    else: styles.append('')
                return styles

            st.dataframe(df_invest.head(15).style.apply(style_invest, axis=1), use_container_width=True, hide_index=True)
            st.markdown("<p style='color:#94a3b8; font-size:0.8rem; text-align:center;'>Menampilkan Top 15 Saham dengan Dividend Yield Tertinggi. Cocok untuk strategi Nabung Saham.</p>", unsafe_allow_html=True)
            
            render_cross_validation_ui(top_invest_tickers)

        with tab2:
            st.markdown("<br><h3 style='font-size: 1.5rem;'>🏦 Value Investing Clusters</h3>", unsafe_allow_html=True)
            c_div, c_uv, c_blue = st.columns(3)
            with c_div:
                badges_div = render_badges(cluster_div, "#10b981")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #10b981; height: 100%;'>
                    <div style='color:#10b981; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>💰 1. DIVIDEND HUNTER</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Emiten dermawan pencetak pasif income dengan Yield di atas bunga deposito (>5%).</div>
                    {badges_div}
                </div>
                """, unsafe_allow_html=True)
            with c_uv:
                badges_uv = render_badges(cluster_undervalued, "#38bdf8")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #38bdf8; height: 100%;'>
                    <div style='color:#38bdf8; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>💎 2. DEEP UNDERVALUED</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Perusahaan salah harga dengan valuasi buku dan laba bersih yang terlampau murah.</div>
                    {badges_uv}
                </div>
                """, unsafe_allow_html=True)
            with c_blue:
                badges_blue = render_badges(cluster_bluechip, "#facc15")
                st.markdown(f"""
                <div class='premium-card' style='border-top: 4px solid #facc15; height: 100%;'>
                    <div style='color:#facc15; font-weight:900; font-size:1.1rem; letter-spacing:0.5px;'>🏦 3. BLUECHIP ROSTER</div>
                    <div style='color:#94a3b8; font-size:0.75rem; margin-top:5px; line-height:1.4;'>Pilar penggerak IHSG berfundamental baja untuk stabilitas portofolio Anda.</div>
                    {badges_blue}
                </div>
                """, unsafe_allow_html=True)

    # ==========================================
    # TAB 3 & 4 (GLOBAL UNTUK KEDUA MODE)
    # ==========================================
    with tab3:
        emiten_terpilih = st.session_state.get(f"signal_select_{st.session_state.current_tf}")
        if emiten_terpilih: 
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='font-size: 1.5rem;'>📊 Quarterly Financial Matrix : {emiten_terpilih}</h3>", unsafe_allow_html=True)
            with st.spinner(f"Sinkronisasi Data Finansial (QoQ) {emiten_terpilih}..."):
                analyst_data = fetch_analyst_consensus(emiten_terpilih)
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
                
                df_inc, df_bs, df_cf = fetch_financial_charts(emiten_terpilih)
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
                    if not df_inc.empty: st.plotly_chart(create_locked_plotly_chart(df_inc, "#00f2fe", "#10b981"), use_container_width=True, config=lock_config)
                    else: st.warning("No Data")
                with c2:
                    st.markdown("<h5 style='color: #3b82f6; text-align:center; font-size: 0.9rem; font-weight:700; margin-bottom: 5px;'>⚖️ Balance Sheet</h5>", unsafe_allow_html=True)
                    if not df_bs.empty: st.plotly_chart(create_locked_plotly_chart(df_bs, "#3b82f6", "#f43f5e"), use_container_width=True, config=lock_config)
                    else: st.warning("No Data")
                with c3:
                    st.markdown("<h5 style='color: #8b5cf6; text-align:center; font-size: 0.9rem; font-weight:700; margin-bottom: 5px;'>💵 Cash Flow</h5>", unsafe_allow_html=True)
                    if not df_cf.empty: st.plotly_chart(create_locked_plotly_chart(df_cf, "#8b5cf6", "#f59e0b"), use_container_width=True, config=lock_config)
                    else: st.warning("No Data")
        else:
            st.info("Pilih emiten di bagian Executive Cross-Validation (Tab 1) terlebih dahulu.")

    with tab4:
        st.markdown("<br><h3 style='font-size: 1.5rem; text-align: center;'>📚 Jihan-Ghina Academy & User Guide</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;'>Panduan analitika level institusi di dalam terminal.</p>", unsafe_allow_html=True)
        with st.expander("📖 1. Dual-Core Mode (Trading vs Investment)"):
            st.markdown("""
            * **Mode Trading:** Dirancang untuk mencari cuan cepat berdasarkan momentum, volatilitas, dan akumulasi bandar. Matriks utama otomatis mengurutkan saham dari *Top Gainers* hari ini.
            * **Mode Investment:** Dirancang untuk menabung saham jangka panjang. Matriks utama otomatis mengurutkan saham berdasarkan peraih *Dividend Yield* terbesar, PER murah, dan kesehatan perusahaan.
            """)
        with st.expander("📖 2. Clustering Matrix (Proxy Logics)"):
            st.markdown("""
            * **ARA Hunter:** Mengekstrak saham dengan volume harian meledak 2x lipat dan menembus resisten pendek MA5.
            * **Scalping Daily:** Melacak saham *second liner* dengan omset miliaran rupiah per hari namun harga di bawah batas psikologis 3000.
            * **Big Accumulation:** Melacak jejak akumulasi dengan memastikan penutupan hari tersebut berada di area pucuk (*high*) tanpa jarum atas (*upper shadow*).
            """)
        with st.expander("📖 3. Position Sizing (Manajemen Risiko Kuantitatif)"):
            st.markdown("""
            1. Isi modal asli Anda di panel kiri.
            2. Set toleransi rugi di `1.0%` (Sangat disarankan).
            3. Mesin otomatis akan menghitung maksimal Lot yang aman untuk Anda beli berdasarkan jarak Target Stop Loss.
            """)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem; font-weight:600; letter-spacing: 1px;'>⚡ JIHAN-GHINA ENGINE • DUAL CORE TERMINAL v12.4</p>", unsafe_allow_html=True)
