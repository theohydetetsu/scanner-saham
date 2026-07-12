import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import pytz
import warnings
import gc

warnings.filterwarnings('ignore')

# ==========================================
# 1. KONFIGURASI HALAMAN & UI STYLE
# ==========================================
st.set_page_config(page_title="JIHAN-GHINA Pro Max v7.7", page_icon="💻", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Paksa Background Gelap ke Container Utama Streamlit */
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at 50% -20%, #1a1e29, #0f1219) !important; color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; }
    
    /* Kunci Layar Utama agar tidak melebar saat Sidebar ditutup */
    .block-container { 
        padding-top: 1.5rem; 
        padding-bottom: 2rem; 
        max-width: 1150px !important; 
        margin: 0 auto !important; 
    }
    
    h1 { color: #f8fafc; font-weight: 900; letter-spacing: -1px; font-size: 2.2rem !important; margin-bottom: 0; }
    p { color: #94a3b8; font-weight: 300; }
    
    /* Sidebar Dipersempit Ekstra */
    section[data-testid="stSidebar"] { 
        width: 210px !important; 
        min-width: 210px !important; 
        max-width: 210px !important; 
        background-color: rgba(15, 18, 25, 0.75) !important; 
        backdrop-filter: blur(15px); 
        border-right: 1px solid rgba(255, 255, 255, 0.05); 
    }
    
    /* Kartu Premium dengan Efek Melayang (Hover Effect) */
    .premium-card { 
        background: rgba(30, 41, 59, 0.3); 
        backdrop-filter: blur(16px); 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        border-radius: 10px; 
        padding: 15px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); 
        transition: all 0.3s ease-in-out;
    }
    .premium-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 25px -5px rgba(0, 242, 254, 0.3);
        border-color: rgba(0, 242, 254, 0.4);
    }

    /* Varian Slim Card untuk Grafik */
    .slim-card {
        padding: 10px !important;
        border-radius: 8px !important;
    }
    .slim-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px -5px rgba(0, 242, 254, 0.2);
    }
    
    /* Kotak IHSG Diperkecil */
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 10px 15px !important; }
    .ihsg-title { color: #94a3b8; font-size: 0.65rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; }
    .ihsg-score { color: #00f2fe; font-size: 1.5rem; font-weight: 900; line-height: 1.1; margin: 2px 0; }
    
    .strat-num { font-size: 2.2rem; font-weight: 900; margin: 2px 0; line-height: 1; text-align: center; }
    .strat-label { font-size: 0.75rem; font-weight: 600; text-align: center; letter-spacing: 1px; }
    
    .stDataFrame { border-radius: 8px; overflow: hidden; font-size: 13px !important; border: 1px solid rgba(255,255,255,0.05); }
    
    /* Tombol Global Diperhalus & Diperkecil */
    div.stButton > button:first-child { 
        background: rgba(0, 242, 254, 0.1) !important; 
        border: 1px solid rgba(0, 242, 254, 0.5) !important; 
        color: #00f2fe !important; 
        border-radius: 6px !important; 
        padding: 8px 12px !important; 
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child p {
        color: #00f2fe !important;
        font-weight: 800 !important; 
        font-size: 0.95rem !important; 
        letter-spacing: 0.5px;
        margin: 0;
    }
    div.stButton > button:first-child:hover { 
        background: #00f2fe !important; 
        transform: scale(1.02); 
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.5); 
    }
    div.stButton > button:first-child:hover p { color: #020617 !important; }
    
    /* Styling Header Login */
    .login-header {
        text-align: center; 
        color: #00f2fe; 
        font-size: 2.2rem; 
        font-weight: 900; 
        margin-top: 80px; 
        margin-bottom: 5px;
    }

    /* ========================================== */
    /* RESPONSIVE MOBILE FIX (EKSTREM UNTUK HP)   */
    /* ========================================== */
    @media (max-width: 768px) {
        .block-container { padding-top: 1rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        
        h1 { font-size: 1.3rem !important; }
        .login-header { font-size: 1.4rem !important; margin-top: 20px !important; } 
        p { font-size: 0.8rem !important; }
        
        .ihsg-score { font-size: 1.2rem !important; }
        .ihsg-title { font-size: 0.6rem !important; }
        
        .strat-num { font-size: 1.4rem !important; margin: 0px !important; }
        .strat-label { font-size: 0.6rem !important; }
        
        .premium-card { padding: 10px !important; }
        
        div.stButton > button:first-child { padding: 4px 8px !important; }
        div.stButton > button:first-child p { font-size: 0.8rem !important; }
        
        label { font-size: 0.8rem !important; }
        input { font-size: 0.85rem !important; padding: 6px !important; height: 35px !important; }
        
        .stDataFrame { font-size: 12px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1.5. SISTEM KEAMANAN (LOGIN GATE 2.0)
# ==========================================
USERNAME_RAHASIA = "theo"
PASSWORD_RAHASIA = "216455"

if "akses_diberikan" not in st.session_state:
    st.session_state.akses_diberikan = False
if "scan_clicked" not in st.session_state:
    st.session_state.scan_clicked = False

if not st.session_state.akses_diberikan:
    st.markdown("<div class='login-header'>🔒 JIHAN-GHINA TERMINAL TERKUNCI</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;'>Sistem intelijen ini bersifat privat. Silakan hubungi admin untuk akses.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.markdown("<div class='premium-card' style='border-left: 5px solid #00f2fe;'>", unsafe_allow_html=True)
        user_input = st.text_input("👤 Username:")
        pwd_input = st.text_input("🔑 Password:", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("VERIFIKASI AKSES", use_container_width=True):
            if user_input.strip().lower() == USERNAME_RAHASIA.lower() and pwd_input.strip() == PASSWORD_RAHASIA:
                st.session_state.akses_diberikan = True
                if hasattr(st, 'rerun'): st.rerun()
                else: st.experimental_rerun()
            else:
                st.error("Akses Ditolak! Username atau Password tidak valid.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 2. FUNGSI PEMROSESAN DATA UTAMA
# ==========================================
def get_waktu_wib():
    tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(tz).strftime("%d %b %Y - %H:%M:%S WIB")

if "raw_stocks" not in st.session_state: st.session_state.raw_stocks = []
if "last_update" not in st.session_state: st.session_state.last_update = None
if "page_matrix" not in st.session_state: st.session_state.page_matrix = 0

roster_30_saham = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", "AMRT",
    "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", "CPIN", "ANTM",
    "AMMN", "BREN", "CUAN", "PANI", "BRPT", "MDKA", "MEDC", "ARTO", "SIDO", "MYOR"
]

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

def fetch_single_stock(emiten):
    try:
        kode = emiten.replace(".JK", "")
        df = yf.download(emiten, period="6mo", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        df = df.ffill() 
        
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['RSI'] = hitung_rsi_akurat(df)
        df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()
        
        harga_skg = float(df['Close'].iloc[-1])
        ema20_skg = float(df['EMA20'].iloc[-1])
        vol_skg = float(df['Volume'].iloc[-1])
        vol_sma20 = float(df['Vol_SMA20'].iloc[-1])
        
        high_1mo = float(df['High'].tail(20).max())
        low_1mo = float(df['Low'].tail(20).min())
        
        status_bandar = "AKUMULASI" if (vol_skg > (vol_sma20 * 1.2) and harga_skg > ema20_skg) else ("DISTRIBUSI" if (vol_skg > (vol_sma20 * 1.2) and harga_skg < ema20_skg) else "NEUTRAL")
        
        tkr = yf.Ticker(emiten)
        info = tkr.info if tkr.info else {}
        
        per = info.get('trailingPE', 0.0)
        pbv = info.get('priceToBook', 1.0)
        div_rate = info.get('trailingAnnualDividendRate', 0)
        div_yield = (div_rate / harga_skg * 100) if (div_rate and harga_skg > 0) else 0.0
            
        return {
            "TICKER": kode, "HARGA": harga_skg, "PER": round(per, 2), "PBV": round(pbv, 2), 
            "DIV_YIELD": round(div_yield, 2), "RSI": round(float(df['RSI'].iloc[-1]), 2), 
            "UP_EMA20": harga_skg > ema20_skg, "MACD_GOLDEN": float(df['MACD'].iloc[-1]) > float(df['Signal'].iloc[-1]),
            "STATUS_BANDAR": status_bandar,
            "EMA20_VAL": ema20_skg, "RESISTANCE": high_1mo, "SUPPORT": low_1mo
        }
    except Exception as e:
        return None

def format_rupiah(val):
    if pd.isna(val) or val == 0: return "-"
    return f"Rp {val:,.0f}".replace(",", ".")

# ==========================================
# 3. ENGINE FINANCIAL CHARTS & HEALTH INDICATOR
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financial_charts(ticker_symbol):
    tkr = yf.Ticker(ticker_symbol + ".JK")
    df_inc, df_bs, df_cf = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    PEMBAGI = 1_000_000_000_000 
    
    try:
        inc = tkr.financials
        if not inc.empty:
            df_inc['Revenue'] = (inc.loc['Total Revenue'] / PEMBAGI) if 'Total Revenue' in inc.index else 0
            df_inc['Net Income'] = (inc.loc['Net Income'] / PEMBAGI) if 'Net Income' in inc.index else 0
            df_inc.index = df_inc.index.year
            df_inc = df_inc.sort_index()
    except: pass
    
    try:
        bs = tkr.balance_sheet
        if not bs.empty:
            df_bs['Total Assets'] = (bs.loc['Total Assets'] / PEMBAGI) if 'Total Assets' in bs.index else 0
            if 'Total Liabilities Net Minority Interest' in bs.index:
                df_bs['Total Liabilities'] = (bs.loc['Total Liabilities Net Minority Interest'] / PEMBAGI)
            elif 'Total Liabilities' in bs.index:
                df_bs['Total Liabilities'] = (bs.loc['Total Liabilities'] / PEMBAGI)
            else:
                df_bs['Total Liabilities'] = 0
            df_bs.index = df_bs.index.year
            df_bs = df_bs.sort_index()
    except: pass
    
    try:
        cf = tkr.cashflow
        if not cf.empty:
            df_cf['Operating Cash'] = (cf.loc['Operating Cash Flow'] / PEMBAGI) if 'Operating Cash Flow' in cf.index else 0
            df_cf['Free Cash Flow'] = (cf.loc['Free Cash Flow'] / PEMBAGI) if 'Free Cash Flow' in cf.index else 0
            df_cf.index = df_cf.index.year
            df_cf = df_cf.sort_index()
    except: pass
    
    return df_inc, df_bs, df_cf

def analyze_financial_health(df_inc, df_bs, df_cf):
    score = 0
    indikator = []
    
    if not df_inc.empty and len(df_inc) >= 1:
        latest_ni = df_inc['Net Income'].iloc[-1]
        if latest_ni > 0:
            score += 25
            indikator.append("✔️ Laba Bersih Positif")
        if len(df_inc) >= 2:
            prev_ni = df_inc['Net Income'].iloc[-2]
            if latest_ni > prev_ni:
                score += 15
                indikator.append("✔️ Laba Bertumbuh (YoY)")
                
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
        if 'Free Cash Flow' in df_cf.columns:
            fcf = df_cf['Free Cash Flow'].iloc[-1]
            if fcf > 0:
                score += 10
                indikator.append("✔️ Free Cash Flow Positif")
                
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
# 4. SIDEBAR (CYBER COMMAND CENTER)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #00f2fe; font-size: 1.6rem; font-weight: 900; margin-bottom: 0px; text-align: center;'>👨‍💻 JIHAN-GHINA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.7rem; letter-spacing: 2px; margin-bottom: 15px;'>TERMINAL v7.7</p>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 10px; margin-bottom: 20px; border-left: 3px solid #10b981;'>
        <div style='font-size: 0.65rem; color: #94a3b8; letter-spacing: 1px; margin-bottom: 5px;'>SYSTEM STATUS</div>
        <div style='font-size: 0.8rem; color: #10b981; margin-bottom: 2px;'>🟢 Core Engine: <strong>Online</strong></div>
        <div style='font-size: 0.8rem; color: #10b981; margin-bottom: 2px;'>🟢 Data Link: <strong>Secured</strong></div>
        <div style='font-size: 0.8rem; color: #00f2fe;'>⚡ Latency: <strong>Optimized</strong></div>
    </div>
    """, unsafe_allow_html=True)
    
    profil_risiko = st.selectbox("🎯 Profil Risiko:", ["Moderat", "Agresif", "Konservatif"], label_visibility="visible")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    daftar_saham = [s.strip().upper() + ".JK" for s in roster_30_saham]
    
    if st.button("🔄 SCAN MARKET", use_container_width=True):
        st.session_state.scan_clicked = True
        st.cache_data.clear()
        st.session_state.page_matrix = 0 
        st.session_state.raw_stocks = []
        
        progress_text = "Memindai Market..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, t in enumerate(daftar_saham):
            my_bar.progress((i + 1) / len(daftar_saham), text=f"Menganalisis {t} ({i+1}/{len(daftar_saham)})")
            data = fetch_single_stock(t)
            if data:
                st.session_state.raw_stocks.append(data)
            gc.collect() 
            
        my_bar.empty()
        st.session_state.last_update = get_waktu_wib()
        
        if hasattr(st, 'rerun'): st.rerun()
        else: st.experimental_rerun()
        
    st.markdown("""
    <div style='margin-top: 20px; text-align: center; color: #475569; font-size: 0.65rem;'>
        Analisis 30 Saham (Bluechip & Multibagger)
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. HEADER & MATRIKS UTAMA
# ==========================================
st.markdown("<h1>🌐 Algorithmic Market Intelligence</h1>", unsafe_allow_html=True)

col_h1, col_h2 = st.columns([3.5, 1.5])
with col_h1:
    upd_time = st.session_state.last_update if st.session_state.last_update else "Menunggu inisiasi radar..."
    st.markdown(f"<p style='font-size: 0.9rem;'>🕒 Terakhir Diperbarui: <span style='color:#00f2fe;'>{upd_time}</span><br>Multi-Pilar Integrasi Terminal: Teknikal, Fundamental & Bandarmologi.</p>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()
with col_h2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_garis = '#10b981' if ihsg_chg >= 0 else '#f43f5e'
        st.markdown(f"""
        <div class="premium-card ihsg-box" style="border-left: 5px solid {warna_garis};">
            <span class="ihsg-title">IHSG GABUNGAN</span>
            <span class="ihsg-score">{ihsg_now:,.2f}</span>
            <span style="color: {warna_garis}; font-weight: 800; font-size: 0.9rem;">{warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

if not st.session_state.scan_clicked or not st.session_state.raw_stocks:
    st.info("👈 Sistem aman dan *standby*. Silakan tekan tombol '🔄 SCAN MARKET' di sidebar untuk memulai analisis radar.")
else:
    st.markdown("<h3>🛰️ Pro Max Recommendation Engine</h3>", unsafe_allow_html=True)
    
    hasil_rekomendasi = []
    for raw in st.session_state.raw_stocks:
        skor = 0
        if raw["UP_EMA20"]: skor += 15
        if raw["MACD_GOLDEN"]: skor += 15
        if raw["RSI"] < 30: skor += 15
        elif 30 <= raw["RSI"] <= 70: skor += 10
        elif raw["RSI"] > 70: skor -= 10
        if raw["STATUS_BANDAR"] == "AKUMULASI": skor += 20
        elif raw["STATUS_BANDAR"] == "DISTRIBUSI": skor -= 15
        else: skor += 5
        if 0 < raw["PER"] < 15: skor += 10
        if 0 < raw["PBV"] < 2: skor += 10
        if raw["DIV_YIELD"] > 3: skor += 5
        
        skor = max(0, min(100, skor))
        target_skor = 60 if profil_risiko == "Agresif" else (75 if profil_risiko == "Konservatif" else 70)
        
        if skor >= target_skor: kep = "🟢 ACCUMULATE"
        elif skor >= 45: kep = "🟡 HOLD"
        else: kep = "🔴 LIQUIDATE"
            
        harga_saat_ini = raw["HARGA"]
        ema20 = raw["EMA20_VAL"]
        resis = raw["RESISTANCE"]
        supp = raw["SUPPORT"]
        
        entry_ideal = ema20 if harga_saat_ini > ema20 else supp
        target_tp = harga_saat_ini * 1.05 if resis <= harga_saat_ini else resis
        stop_ls = harga_saat_ini * 0.97 if supp >= harga_saat_ini else supp
        
        hasil_rekomendasi.append({
            "TICKER": raw["TICKER"], "HARGA": f"{int(harga_saat_ini):,}".replace(",", "."),
            "AREA BELI": f"{int(entry_ideal):,}".replace(",", "."),
            "TARGET (TP)": f"{int(target_tp):,}".replace(",", "."),
            "STOP LOSS": f"{int(stop_ls):,}".replace(",", "."),
            "RSI": f"{raw['RSI']:.2f}", "BANDARMOLOGI": raw["STATUS_BANDAR"], "REKOMENDASI": kep
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)
    
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='premium-card' style='border-left: 5px solid #10b981;'><div class='strat-label' style='color:#34d399;'>🟢 BUY STRATEGY</div><div class='strat-num' style='color:#f8fafc;'>{sum('🟢' in x for x in df_final['REKOMENDASI'])}</div></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='premium-card' style='border-left: 5px solid #fbbf24;'><div class='strat-label' style='color:#fbbf24;'>🟡 HOLD STRATEGY</div><div class='strat-num' style='color:#f8fafc;'>{sum('🟡' in x for x in df_final['REKOMENDASI'])}</div></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='premium-card' style='border-left: 5px solid #fb7185;'><div class='strat-label' style='color:#fb7185;'>🔴 SELL STRATEGY</div><div class='strat-num' style='color:#f8fafc;'>{sum('🔴' in x for x in df_final['REKOMENDASI'])}</div></div>", unsafe_allow_html=True)
    
    st.write(" ")
    
    def style_tabel(row):
        styles = []
        if '🟢' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(16, 185, 129, 0.1); color: #34d399;'
        elif '🟡' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(245, 158, 11, 0.1); color: #fbbf24;'
        else: bg_rek = 'background-color: rgba(244, 63, 94, 0.1); color: #fb7185;'
        
        for c, val in row.items():
            if c == 'TICKER': styles.append('font-weight: 900; font-size: 15px; color: #00f2fe;')
            elif c == 'TARGET (TP)': styles.append('color: #10b981; font-weight: 800;') 
            elif c == 'STOP LOSS': styles.append('color: #f43f5e; font-weight: 800;')  
            elif c == 'AREA BELI': styles.append('color: #38bdf8; font-weight: 800;')  
            elif c in ['BANDARMOLOGI', 'REKOMENDASI']: styles.append(bg_rek)
            elif c == 'RSI':
                try:
                    rsi_val = float(val)
                    if rsi_val > 70: styles.append('color: #f43f5e; font-weight: 800;') 
                    elif rsi_val < 30: styles.append('color: #10b981; font-weight: 800;') 
                    else: styles.append('')
                except: styles.append('')
            else: styles.append('')
        return styles

    st.markdown("📄 **Market Radar Matrix (Auto-Paged & Color Coded)**")
    
    ITEMS_PER_PAGE = 10
    total_pages = len(df_final) // ITEMS_PER_PAGE + (1 if len(df_final) % ITEMS_PER_PAGE > 0 else 0)
    
    start_idx = st.session_state.page_matrix * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    df_tampil = df_final.iloc[start_idx:end_idx]
    
    # HTML siluman dihapus, kita render st.dataframe dengan ukuran penuh agar elegan di scroll di HP
    st.dataframe(df_tampil.style.apply(style_tabel, axis=1), use_container_width=True, hide_index=True)
    
    col_p1, col_p2, col_p3 = st.columns([1.5, 7, 1.5])
    
    with col_p1:
        if st.button("⬅️ Prev", use_container_width=True, disabled=(st.session_state.page_matrix == 0)):
            st.session_state.page_matrix -= 1
            if hasattr(st, 'rerun'): st.rerun()
            else: st.experimental_rerun()
            
    with col_p2:
        st.markdown(f"<p style='text-align: center; font-size:0.75rem; color:#94a3b8; margin-top:8px;'>Halaman {st.session_state.page_matrix + 1} dari {total_pages}</p>", unsafe_allow_html=True)
        
    with col_p3:
        if st.button("Next ➡️", use_container_width=True, disabled=(st.session_state.page_matrix >= total_pages - 1)):
            st.session_state.page_matrix += 1
            if hasattr(st, 'rerun'): st.rerun()
            else: st.experimental_rerun()

    # ==========================================
    # 6. MODUL VISUAL CHART KEUANGAN & HEALTH
    # ==========================================
    st.markdown("---")
    st.markdown("<h3 style='color: #f8fafc; font-weight: 800; margin-bottom: 1rem;'>📊 Financial & Analyst Charts</h3>", unsafe_allow_html=True)
    
    emiten_pilihan = st.selectbox("🎯 Target Emiten untuk Dibedah:", roster_30_saham, label_visibility="visible")
    
    with st.spinner(f"Menarik Visualisasi Finansial {emiten_pilihan} dari Server..."):
        
        analyst_data = fetch_analyst_consensus(emiten_pilihan)
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom: 20px;'>
            <div class='premium-card slim-card' style='flex:1; min-width:140px; text-align:center; border-left: 5px solid #00f2fe;'>
                <div style='font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;'>💡 Rating Analis</div>
                <div style='font-size:1.05rem; font-weight:800; color:#00f2fe; margin-top:5px;'>{analyst_data["Konsensus"]}</div>
            </div>
            <div class='premium-card slim-card' style='flex:1; min-width:140px; text-align:center; border-left: 5px solid #f43f5e;'>
                <div style='font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;'>📉 Target Bawah</div>
                <div style='font-size:1.05rem; font-weight:800; color:#f43f5e; margin-top:5px;'>{analyst_data["Target Bawah"]}</div>
            </div>
            <div class='premium-card slim-card' style='flex:1; min-width:140px; text-align:center; border-left: 5px solid #f8fafc;'>
                <div style='font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;'>🎯 Target Rata-Rata</div>
                <div style='font-size:1.05rem; font-weight:800; color:#f8fafc; margin-top:5px;'>{analyst_data["Target Rata-Rata"]}</div>
            </div>
            <div class='premium-card slim-card' style='flex:1; min-width:140px; text-align:center; border-left: 5px solid #10b981;'>
                <div style='font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;'>📈 Target Atas</div>
                <div style='font-size:1.05rem; font-weight:800; color:#10b981; margin-top:5px;'>{analyst_data["Target Atas"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        df_inc, df_bs, df_cf = fetch_financial_charts(emiten_pilihan)
        
        status_text, color_hex, reason_list = analyze_financial_health(df_inc, df_bs, df_cf)
        reasons_html = "".join([f"<li style='margin-bottom: 4px;'>{r}</li>" for r in reason_list])
        
        st.markdown(f"""
        <div class='premium-card' style='margin-bottom: 25px; border-left: 5px solid {color_hex};'>
            <h4 style='color: #f8fafc; margin-top: 0; margin-bottom: 10px; font-size: 1.1rem;'>💠 Financial Health Status: <span style='color: {color_hex};'>{status_text}</span></h4>
            <p style='color: #94a3b8; font-size: 0.85rem; margin-bottom: 5px;'>Faktor Pendukung Berdasarkan Laporan Terbaru:</p>
            <ul style='color: #cbd5e1; font-size: 0.8rem; padding-left: 20px; margin: 0;'>
                {reasons_html if reason_list else "<li>Belum cukup data untuk melakukan skoring.</li>"}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown("<div class='premium-card slim-card'>", unsafe_allow_html=True)
            st.markdown(f"<h5 style='color: #00f2fe; text-align:center; font-size: 0.95rem; margin-bottom: 10px;'>📈 Income Statement</h5>", unsafe_allow_html=True)
            if not df_inc.empty: st.bar_chart(df_inc, color=["#00f2fe", "#10b981"], height=250)
            else: st.warning("Data Kosong")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c2:
            st.markdown("<div class='premium-card slim-card'>", unsafe_allow_html=True)
            st.markdown(f"<h5 style='color: #3b82f6; text-align:center; font-size: 0.95rem; margin-bottom: 10px;'>⚖️ Balance Sheet</h5>", unsafe_allow_html=True)
            if not df_bs.empty: st.bar_chart(df_bs, color=["#3b82f6", "#f43f5e"], height=250)
            else: st.warning("Data Kosong")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c3:
            st.markdown("<div class='premium-card slim-card'>", unsafe_allow_html=True)
            st.markdown(f"<h5 style='color: #8b5cf6; text-align:center; font-size: 0.95rem; margin-bottom: 10px;'>💵 Cash Flow</h5>", unsafe_allow_html=True)
            if not df_cf.empty: st.bar_chart(df_cf, color=["#8b5cf6", "#f59e0b"], height=250)
            else: st.warning("Data Kosong")
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem;'>⚡ JIHAN-GHINA ENGINE • SECURE ALGORITHMIC TERMINAL v7.7</p>", unsafe_allow_html=True)
