import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import pytz
import warnings

warnings.filterwarnings('ignore')

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
# 1. KONFIGURASI HALAMAN UTAMA & UI STYLE
# ==========================================
st.set_page_config(page_title="AI Stock Dashboard Pro Max v6.3", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at 50% -20%, #1a1e29, #0f1219); }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 98%; }
    h1 { color: #f8fafc; font-weight: 900; letter-spacing: -1px; font-size: 2.2rem !important; margin-bottom: 0; }
    p { color: #94a3b8; font-weight: 300; }
    
    [data-testid="stSidebar"] { background-color: rgba(15, 18, 25, 0.9) !important; backdrop-filter: blur(12px); border-right: 1px solid rgba(255, 255, 255, 0.05); }
    .premium-card { background: rgba(30, 41, 59, 0.3); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5); }
    
    .ihsg-box { text-align: right; display: flex; flex-direction: column; justify-content: center; height: 100%; padding: 12px 20px !important; }
    .ihsg-title { color: #94a3b8; font-size: 0.7rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; }
    .ihsg-score { color: #f8fafc; font-size: 1.8rem; font-weight: 900; line-height: 1.1; margin: 3px 0; }
    
    .strat-num { font-size: 2.5rem; font-weight: 900; margin: 5px 0; line-height: 1; text-align: center; }
    .strat-label { font-size: 0.8rem; font-weight: 600; text-align: center; letter-spacing: 1px; }
    
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    
    div.stButton > button:first-child { background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important; color: #020617 !important; font-weight: 800 !important; font-size: 1rem !important; border-radius: 8px !important; border: none !important; padding: 10px !important; transition: all 0.3s ease; }
    div.stButton > button:first-child:hover { transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

def get_waktu_wib():
    tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(tz).strftime("%d %b %Y - %H:%M:%S WIB")

if "raw_stocks" not in st.session_state: st.session_state.raw_stocks = []
if "last_update" not in st.session_state: st.session_state.last_update = None
if "page_matrix" not in st.session_state: st.session_state.page_matrix = 0

roster_20_saham = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", "AMRT",
    "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", "CPIN", "ANTM"
]
tahun_sekarang = datetime.now().year
list_tahun = [str(tahun_sekarang), str(tahun_sekarang-1), str(tahun_sekarang-2), str(tahun_sekarang-3)]

# ==========================================
# FUNGSI PEMROSESAN DATA UTAMA (MEMORY OPTIMIZED)
# ==========================================
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
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    ema_gain = gain.ewm(alpha=1/periods, min_periods=periods).mean()
    ema_loss = loss.ewm(alpha=1/periods, min_periods=periods).mean()
    rs = ema_gain / ema_loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=600, show_spinner=False)
def fetch_raw_data(saham_list):
    master_data = []
    
    # 🌟 MURNI MENGGUNAKAN YFINANCE (Mencegah Segfault & Hemat Memori) 🌟
    for emiten in saham_list:
        try:
            kode = emiten.replace(".JK", "")
            
            # Tarik Harga Historis
            df = yf.download(emiten, period="6mo", progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
            df = df.ffill() 
            
            # Kalkulasi Teknikal
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
            
            # Logika Bandarmologi
            if vol_skg > (vol_sma20 * 1.2) and harga_skg > ema20_skg: status_bandar = "AKUMULASI"
            elif vol_skg > (vol_sma20 * 1.2) and harga_skg < ema20_skg: status_bandar = "DISTRIBUSI"
            else: status_bandar = "NEUTRAL"
            
            # Tarik Fundamental Tunggal (Lebih aman dari Crash)
            tkr = yf.Ticker(emiten)
            info = tkr.info if tkr.info else {}
            
            per = info.get('trailingPE', 0.0)
            pbv = info.get('priceToBook', 1.0)
            dy = info.get('dividendYield', 0.0)
            div_yield = (dy * 100) if (dy and dy > 0) else 0.0
                
            master_data.append({
                "TICKER": kode, "HARGA": harga_skg, "PER": round(per, 2), "PBV": round(pbv, 2), 
                "DIV_YIELD": round(div_yield, 2), "RSI": round(float(df['RSI'].iloc[-1]), 2), 
                "UP_EMA20": harga_skg > ema20_skg, "MACD_GOLDEN": float(df['MACD'].iloc[-1]) > float(df['Signal'].iloc[-1]),
                "STATUS_BANDAR": status_bandar
            })
        except Exception as e:
            continue
            
    return master_data

def format_miliar(val):
    if pd.isna(val) or val == 0: return "-"
    return f"{val / 1_000_000_000:,.2f} B"

def format_rupiah(val):
    if pd.isna(val) or val == 0: return "-"
    return f"Rp {val:,.2f}".replace(",", ".")

# ==========================================
# ENGINE LAPORAN KEUANGAN & CHART & ANALYST
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_chart_data(ticker_symbol):
    tkr = yf.Ticker(ticker_symbol + ".JK")
    chart_df = pd.DataFrame(index=list_tahun[::-1], columns=["Revenue", "Net Income"]).fillna(0.0)
    try:
        inc_a = tkr.income_statement
        if inc_a is not None:
            for date_col in inc_a.columns:
                thn = str(date_col.year)
                if thn in chart_df.index:
                    if "Total Revenue" in inc_a.index: chart_df.at[thn, "Revenue"] = float(inc_a.loc["Total Revenue", date_col] or 0)
                    if "Net Income" in inc_a.index: chart_df.at[thn, "Net Income"] = float(inc_a.loc["Net Income", date_col] or 0)
    except: pass
    return chart_df

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

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financial_statement(ticker_symbol, metric_type):
    tkr = yf.Ticker(ticker_symbol + ".JK")
    df_fin = pd.DataFrame(index=["Q1", "Q2", "Q3", "Q4", "Annualised", "TTM"], columns=list_tahun).fillna("-")
    try:
        inc_q = tkr.quarterly_income_statement
        inc_a = tkr.income_statement
        
        if metric_type == "Net Income": target_row = "Net Income"
        elif metric_type == "Revenue": target_row = "Total Revenue"
        else: target_row = "Basic EPS"
        
        if inc_q is not None and target_row in inc_q.index:
            for date_col in inc_q.columns:
                thn = str(date_col.year)
                bln = date_col.month
                val = inc_q.loc[target_row, date_col]
                if thn in list_tahun:
                    if bln <= 3: df_fin.at["Q1", thn] = format_miliar(val) if metric_type != "EPS" else format_rupiah(val)
                    elif bln <= 6: df_fin.at["Q2", thn] = format_miliar(val) if metric_type != "EPS" else format_rupiah(val)
                    elif bln <= 9: df_fin.at["Q3", thn] = format_miliar(val) if metric_type != "EPS" else format_rupiah(val)
                    else: df_fin.at["Q4", thn] = format_miliar(val) if metric_type != "EPS" else format_rupiah(val)
                    
        if inc_a is not None and target_row in inc_a.index:
            for date_col in inc_a.columns:
                thn = str(date_col.year)
                val = inc_a.loc[target_row, date_col]
                if thn in list_tahun:
                    formatted_val = format_miliar(val) if metric_type != "EPS" else format_rupiah(val)
                    df_fin.at["Annualised", thn] = formatted_val
                    df_fin.at["TTM", thn] = formatted_val
    except: pass
    return df_fin

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dividend_history(ticker_symbol):
    tkr = yf.Ticker(ticker_symbol + ".JK")
    df_div = pd.DataFrame(index=["Dividend Per Share", "EPS (Earning Per Share)", "Payout Ratio (%)", "Dividend Yield (%)"], columns=list_tahun).fillna("-")
    try:
        divs = tkr.dividends
        if divs is not None and not divs.empty:
            divs_by_year = divs.groupby(divs.index.year).sum()
            for thn_int, val in divs_by_year.items():
                thn = str(thn_int)
                if thn in list_tahun: df_div.at["Dividend Per Share", thn] = format_rupiah(val)
                    
        inc_a = tkr.income_statement
        if inc_a is not None and "Basic EPS" in inc_a.index:
            for date_col in inc_a.columns:
                thn = str(date_col.year)
                val_eps = inc_a.loc["Basic EPS", date_col]
                if thn in list_tahun:
                    df_div.at["EPS (Earning Per Share)", thn] = format_rupiah(val_eps)
                    div_val = str(df_div.at["Dividend Per Share", thn]).replace("Rp ", "").replace(".", "")
                    if div_val != "-" and val_eps > 0:
                        try:
                            payout = (float(div_val) / float(val_eps)) * 100
                            df_div.at["Payout Ratio (%)", thn] = f"{payout:,.2f}%"
                        except: pass
    except: pass
    return df_div

# ==========================================
# 2. SIDEBAR (CYBER PANEL)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #00f2fe; font-size: 1.5rem; font-weight: 900; margin-bottom: 5px;'>💎 ZETA CORE v6.3</h2>", unsafe_allow_html=True)
    profil_risiko = st.selectbox("🎯 Kategori Profil Risiko:", ["Moderat", "Agresif", "Konservatif"], label_visibility="visible")
    
    daftar_saham = [s.strip().upper() + ".JK" for s in roster_20_saham]
    if st.button("🔄 SCAN MARKET", width='stretch'):
        st.cache_data.clear()
        st.session_state.page_matrix = 0 
        with st.spinner("⏳ Menganalisis Market..."):
            st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
            st.session_state.last_update = get_waktu_wib()
        st.rerun()

# ==========================================
# 3. HEADER & MATRIKS UTAMA
# ==========================================
st.markdown("<h1>📈 Algorithmic Market Intelligence</h1>", unsafe_allow_html=True)

col_h1, col_h2 = st.columns([3.5, 1.5])
with col_h1:
    upd_time = st.session_state.last_update if st.session_state.last_update else "Menunggu Inisiasi..."
    st.markdown(f"<p>🕒 Terakhir Diperbarui: <span style='color:#00f2fe;'>{upd_time}</span><br>Multi-Pilar Integrasi Terminal: Teknikal, Fundamental & Bandarmologi.</p>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()
with col_h2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        st.markdown(f"""
        <div class="premium-card ihsg-box">
            <span class="ihsg-title">IHSG GABUNGAN</span>
            <span class="ihsg-score">{ihsg_now:,.2f}</span>
            <span style="color: {'#10b981' if ihsg_chg >= 0 else '#f43f5e'}; font-weight: 800; font-size: 1rem;">{warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

if len(st.session_state.raw_stocks) == 0:
    with st.spinner("Menghidupkan Engine Pertama Kali... (Mengambil Data Langsung dari Bursa)"):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
        st.session_state.last_update = get_waktu_wib()
        st.rerun()

if st.session_state.raw_stocks:
    st.markdown("---")
    st.markdown("<h3>🧠 AI Pro Max Recommendation Engine</h3>", unsafe_allow_html=True)
    
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
        target = 60 if profil_risiko == "Agresif" else (75 if profil_risiko == "Konservatif" else 70)
        
        if skor >= target: kep, sin = "🟢 ACCUMULATE", "BUY"
        elif skor >= 45: kep, sin = "🟡 HOLD", "NEUTRAL"
        else: kep, sin = "🔴 LIQUIDATE", "SELL"
            
        hasil_rekomendasi.append({
            "TICKER": raw["TICKER"], "HARGA": f"Rp {int(raw['HARGA']):,}".replace(",", "."),
            "PER (x)": f"{raw['PER']:.2f}", "PBV (x)": f"{raw['PBV']:.2f}", "DIV YIELD": f"{raw['DIV_YIELD']:.2f}%",
            "RSI": f"{raw['RSI']:.2f}", "BANDARMOLOGI": raw["STATUS_BANDAR"], "SKOR": skor, "SINYAL": sin, "REKOMENDASI": kep
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)
    
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f"<div class='premium-card'><div class='strat-label' style='color:#34d399;'>🟢 STRATEGI BUY</div><div class='strat-num' style='color:#f8fafc;'>{sum('🟢' in x for x in df_final['REKOMENDASI'])}</div></div>", unsafe_allow_html=True)
    with m2: st.markdown(f"<div class='premium-card'><div class='strat-label' style='color:#fbbf24;'>🟡 STRATEGI HOLD</div><div class='strat-num' style='color:#f8fafc;'>{sum('🟡' in x for x in df_final['REKOMENDASI'])}</div></div>", unsafe_allow_html=True)
    with m3: st.markdown(f"<div class='premium-card'><div class='strat-label' style='color:#fb7185;'>🔴 STRATEGI SELL</div><div class='strat-num' style='color:#f8fafc;'>{sum('🔴' in x for x in df_final['REKOMENDASI'])}</div></div>", unsafe_allow_html=True)
    
    st.write(" ")
    
    def style_tabel(row):
        styles = []
        if '🟢' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(16, 185, 129, 0.1); color: #34d399;'
        elif '🟡' in row['REKOMENDASI']: bg_rek = 'background-color: rgba(245, 158, 11, 0.1); color: #fbbf24;'
        else: bg_rek = 'background-color: rgba(244, 63, 94, 0.1); color: #fb7185;'
        
        for c, val in row.items():
            if c == 'TICKER': 
                styles.append('font-weight: 900; font-size: 16px; color: #00f2fe;')
            elif c in ['BANDARMOLOGI', 'SKOR', 'SINYAL', 'REKOMENDASI']: 
                styles.append(bg_rek)
            elif c == 'RSI':
                try:
                    rsi_val = float(val)
                    if rsi_val > 70: styles.append('color: #f43f5e; font-weight: 800;') # Merah (Overbought)
                    elif rsi_val < 30: styles.append('color: #10b981; font-weight: 800;') # Hijau (Oversold)
                    else: styles.append('')
                except: styles.append('')
            elif c == 'PER (x)':
                try:
                    per_val = float(val)
                    if per_val > 15 or per_val < 0: styles.append('color: #f43f5e;') # Merah (Mahal)
                    elif 0 < per_val < 10: styles.append('color: #10b981;') # Hijau (Murah)
                    else: styles.append('')
                except: styles.append('')
            elif c == 'PBV (x)':
                try:
                    pbv_val = float(val)
                    if pbv_val > 2: styles.append('color: #f43f5e;') # Merah (Mahal)
                    elif 0 < pbv_val < 1: styles.append('color: #10b981;') # Hijau (Murah)
                    else: styles.append('')
                except: styles.append('')
            else: 
                styles.append('')
        return styles

    st.markdown("📄 **Market Radar Matrix (Auto-Paged & Color Coded)**")
    
    ITEMS_PER_PAGE = 10
    total_pages = len(df_final) // ITEMS_PER_PAGE + (1 if len(df_final) % ITEMS_PER_PAGE > 0 else 0)
    
    start_idx = st.session_state.page_matrix * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    df_tampil = df_final.iloc[start_idx:end_idx]
    
    st.dataframe(df_tampil.style.apply(style_tabel, axis=1), width='stretch', hide_index=True)
    
    col_p1, col_p2, col_p3 = st.columns([1, 8, 1])
    with col_p1:
        if st.button("⬅️ Prev", width='stretch', disabled=(st.session_state.page_matrix == 0)):
            st.session_state.page_matrix -= 1
            st.rerun()
    with col_p2:
        st.markdown(f"<p style='text-align: center; font-size:0.8rem; color:#64748b; margin-top:10px;'>Halaman {st.session_state.page_matrix + 1} dari {total_pages}</p>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next ➡️", width='stretch', disabled=(st.session_state.page_matrix >= total_pages - 1)):
            st.session_state.page_matrix += 1
            st.rerun()

    # ==========================================
    # MODUL BARU: ANALISIS LAPORAN KEUANGAN
    # ==========================================
    st.markdown("---")
    st.markdown("<h3 style='color: #f8fafc; font-weight: 800; margin-bottom: 1rem;'>📑 Financials & Analyst Consensus</h3>", unsafe_allow_html=True)
    
    f_col1, f_col2 = st.columns([1, 2])
    with f_col1:
        emiten_pilihan = st.selectbox("🎯 Target Emiten:", roster_20_saham, label_visibility="visible")
    with f_col2:
        metrik_pilihan = st.radio("📊 Tipe Rasio Finansial Tabel:", ["Net Income", "EPS", "Revenue"], horizontal=True, label_visibility="visible")
    
    st.write(" ")
    
    with st.spinner(f"Menarik Data Lengkap {emiten_pilihan} dari Server..."):
        
        analyst_data = fetch_analyst_consensus(emiten_pilihan)
        ac1, ac2, ac3, ac4 = st.columns(4)
        ac1.metric("💡 Rating Analis", analyst_data["Konsensus"])
        ac2.metric("📉 Target Bawah", analyst_data["Target Bawah"])
        ac3.metric("🎯 Target Rata-Rata", analyst_data["Target Rata-Rata"])
        ac4.metric("📈 Target Atas", analyst_data["Target Atas"])
        st.markdown("<br>", unsafe_allow_html=True)
        
        c_col1, c_col2 = st.columns([1.5, 1])
        with c_col1:
            st.markdown(f"<h5 style='color: #38bdf8; margin-bottom: 5px;'>📊 Financials Trend (Annual)</h5>", unsafe_allow_html=True)
            chart_data = fetch_chart_data(emiten_pilihan)
            st.bar_chart(chart_data, color=["#10b981", "#00f2fe"], height=250)
            
        with c_col2:
            st.markdown(f"<h5 style='color: #38bdf8; margin-bottom: 5px;'>💸 Riwayat Dividen & Yield</h5>", unsafe_allow_html=True)
            df_dividends = fetch_dividend_history(emiten_pilihan)
            st.dataframe(df_dividends, width='stretch', height=250)

        st.markdown(f"<h5 style='color: #38bdf8; margin-bottom: 10px; margin-top: 20px;'>📋 Period Statement / {metrik_pilihan}</h5>", unsafe_allow_html=True)
        df_financials = fetch_financial_statement(emiten_pilihan, metrik_pilihan)
        st.dataframe(df_financials, width='stretch')

st.markdown("---")
st.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem;'>⚡ ZETA CORE ENGINE • SECURE ALGORITHMIC TERMINAL v6.3</p>", unsafe_allow_html=True)