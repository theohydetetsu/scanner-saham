import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
from datetime import datetime

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
# 1. KONFIGURASI HALAMAN UTAMA & UI PREMIUM
# ==========================================
st.set_page_config(page_title="ZETA Terminal Pro Max v3.5", page_icon="💎", layout="wide")

# CSS Kustom: Institutional Dark Mode, Bigger Fonts & Clean White Space
st.markdown("""
<style>
    /* Background Dasar & Font Terminal */
    .stApp { background-color: #07090e; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 95%; }
    h1, h2, h3, h4 { font-family: 'Inter', 'Helvetica Neue', sans-serif; color: #f0f3f6; font-weight: 700; }
    h1 { font-size: 32pt !important; letter-spacing: -0.5px; }
    h3 { font-size: 24px !important; }
    
    /* Ukuran Teks Global & Form Diperbesar Untuk Tampilan Zoom 80% */
    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] { 
        font-size: 14pt !important; 
    }
    label { font-size: 13pt !important; font-weight: 600 !important; color: #cdd2d9 !important; }
    
    /* Perbesaran Teks di Dalam Tabel Dataframe */
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th { 
        font-size: 13pt !important; 
        padding: 10px 12px !important;
    }
    
    /* Sidebar Elit */
    [data-testid="stSidebar"] {
        background-color: #0c0f16 !important;
        border-right: 1px solid #1f2430;
    }
    
    /* Premium Glassmorphism Card (Dibuat Menipis Sesuai Request) */
    .metric-card {
        background: linear-gradient(145deg, #111520, #0d1017);
        border: 1px solid #1f2430;
        padding: 12px 20px;
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #00d4ff;
    }
    
    /* Desain Tab & Navigasi */
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: 600; color: #8a90a6; }
    
    /* Tombol Eksekusi Quantum */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00d4ff, #00ffcc) !important;
        color: #05070a !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px !important;
        letter-spacing: 0.5px;
        transition: all 0.3s;
    }
    div.stButton > button:first-child:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
    }
</style>
""", unsafe_allow_html=True)

if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks = []
if "last_update" not in st.session_state:
    st.session_state.last_update = None

@st.cache_data(ttl=600, show_spinner=False)
def fetch_ihsg_data():
    try:
        df_ihsg = yf.download("^JKSE", period="1mo", interval="1d", progress=False)
        if df_ihsg.empty: return None, None, None, None
        df_ihsg.columns = [col[0] if isinstance(col, tuple) else col for col in df_ihsg.columns]
        df_ihsg = df_ihsg.ffill() 
        
        harga_skg = float(df_ihsg['Close'].iloc[-1])
        harga_lalu = float(df_ihsg['Close'].iloc[-2])
        perubahan = harga_skg - harga_lalu
        persen = (perubahan / harga_lalu) * 100
        
        return df_ihsg, harga_skg, perubahan, persen
    except Exception:
        return None, None, None, None

def fetch_advanced_financials(ticker_code):
    try:
        ticker = yf.Ticker(ticker_code + ".JK")
        return ticker.financials, ticker.quarterly_financials, ticker.info, ticker.dividends, ticker.history(period="5y")
    except Exception:
        return None, None, None, None, None

# HEADER UTAMA (INSTITUTIONAL STYLE)
st.markdown("<h1 style='margin-bottom:0px;'>📈 PRO MAX ALGORITHMIC TERMINAL</h1>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()
col_header1, col_header2 = st.columns([2, 1])

with col_header1:
    if st.session_state.last_update:
        st.markdown(f"🕒 <span style='font-size:13pt;'>**Sinkronisasi Terakhir:** `{st.session_state.last_update}`</span>", unsafe_allow_html=True)
    else:
        st.markdown("🕒 <span style='font-size:13pt;'>**Sinkronisasi Terakhir:** `Menunggu sinkronisasi bursa...`</span>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8a92a6; font-size: 12pt; margin-top:-5px;'>Integrasi Multi-Pilar Terminal: Teknikal Quantum, Analisis Konsensus Fundamental, & Real-Time Bandarmologi</p>", unsafe_allow_html=True)

with col_header2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_hex = "#00ffcc" if ihsg_chg >= 0 else "#ff3366"
        st.markdown(f"""
        <div style="text-align: right; background-color: #111520; padding: 12px 20px; border-radius: 12px; border: 1px solid #1f2430;">
            <span style="color: #8a90a6; font-size: 13px; font-weight: 700; letter-spacing: 1px;">INDEX GABUNGAN (IHSG)</span><br/>
            <span style="color: #ffffff; font-size: 42px; font-weight: 900; line-height: 1.1;">{ihsg_now:,.2f}</span><br/> 
            <span style="color: {warna_hex}; font-size: 17px; font-weight: bold;">{warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 2. GRAFIK IHSG RAMPING (SLIM VIEW)
# ==========================================
if df_ihsg_hist is not None:
    if HAS_PLOTLY:
        fig = go.Figure(data=[go.Candlestick(
            x=df_ihsg_hist.index,
            open=df_ihsg_hist['Open'],
            high=df_ihsg_hist['High'],
            low=df_ihsg_hist['Low'],
            close=df_ihsg_hist['Close'],
            increasing_line_color='#00ffcc', 
            decreasing_line_color='#ff3366',
            name="IHSG"
        )])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=5, b=5),
            height=200,
            xaxis_rangeslider_visible=False,
            yaxis=dict(gridcolor='rgba(255,255,255,0.03)', tickfont=dict(size=13)),
            xaxis=dict(gridcolor='rgba(255,255,255,0.03)', tickfont=dict(size=13))
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.line_chart(df_ihsg_hist[['Close']], color="#00ffcc", height=200)

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
st.sidebar.markdown("""
<div style="padding: 5px 0px 15px 0px;">
    <h2 style="color: #00d4ff; font-size: 24px; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 0px;">💎 CYBER PANEL</h2>
    <p style="color: #6c757d; font-size: 13px; margin-top: 2px; margin-bottom: 0px;">Premium Quantum Engine v3.5</p>
</div>
""", unsafe_allow_html=True)

roster_saham_idx = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", 
    "AMRT", "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", 
    "CPIN", "ANTM", "TPIA", "BREN", "AMMN", "ADMR", "MEDC", "AKRA", "ACES", 
    "MYOR", "SMGR", "INCO", "PGEO", "BUKA", "MDKA", "HRUM", "ISAT", "EXCL"
]

saham_terpilih = st.sidebar.multiselect(
    "📋 DAFTAR EMITEN PANTAUAN:",
    options=roster_saham_idx,
    default=roster_saham_idx[:30]
)

daftar_saham = [s.strip().upper() + ".JK" for s in saham_terpilih if s.strip()]

st.sidebar.write(" ")
muat_data = st.sidebar.button("🔄 RE-SCAN MARKET DATA", use_container_width=True, type="primary")
st.sidebar.markdown("<br/>", unsafe_allow_html=True)

st.sidebar.markdown("<span style='color:#8a90a6; font-size:12px; font-weight:bold;'>🎛️ PARAMETER SYSTEM CONFIDENCE</span>", unsafe_allow_html=True)
profil_risiko = st.sidebar.selectbox("🎯 Profil Risiko Trading:", ["Moderat (Standar)", "Agresif (High Risk)", "Konservatif (Aman)"], label_visibility="collapsed")
st.sidebar.markdown("---")

st.sidebar.info(f"📊 WATCHLIST AKTIF: {len(daftar_saham)} Emiten")
if st.session_state.last_update: st.sidebar.success("● SYSTEM STATUS: ONLINE")
else: st.sidebar.warning("○ SYSTEM STATUS: IDLE")
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reset System Cache", use_container_width=True):
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# ==========================================
# 4. CORE ENGINE CALCULATION
# ==========================================
def hitung_rsi(df, periods=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_raw_data(saham_list):
    master_data = []
    for emiten in saham_list:
        try:
            kode = emiten.replace(".JK", "")
            df = yf.download(emiten, period="6mo", progress=False)
            if df.empty: continue
            
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            df = df.ffill() 
            if pd.isna(df['Close'].iloc[-1]): continue 
            
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['RSI'] = hitung_rsi(df)
            
            harga_skg = float(df['Close'].iloc[-1])
            ema20_skg = float(df['EMA20'].iloc[-1])
            macd_skg = float(df['MACD'].iloc[-1])
            sig_skg = float(df['Signal'].iloc[-1])
            rsi_skg = float(df['RSI'].iloc[-1]) if not np.isnan(df['RSI'].iloc[-1]) else 50.0
            
            ticker = yf.Ticker(emiten)
            info = ticker.info
            
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            if pbv and (pbv > 100 or pbv < 0): pbv = 1.0
            div_yield = info.get('dividendYield', 0)
            if div_yield < 1.0: div_yield = div_yield * 100
                
            master_data.append({
                "TICKER": kode,
                "HARGA": harga_skg,
                "PER": round(per, 2) if per else 0.0,
                "PBV": round(pbv, 2) if pbv else 0.0,
                "DIV_YIELD": round(div_yield, 2) if div_yield else 0.0,
                "RSI": round(rsi_skg, 2),
                "UP_EMA20": harga_skg > ema20_skg,
                "MACD_GOLDEN": macd_skg > sig_skg
            })
            time.sleep(0.04) 
        except: continue
    return master_data

if muat_data or len(st.session_state.raw_stocks) == 0:
    if daftar_saham:
        with st.spinner("⏳ Menghubungkan ke Bursa Efek Indonesia..."):
            st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
            st.session_state.last_update = datetime.now().strftime("%H:%M:%S WIB")

# ==========================================
# 5. INTEGRASI MATRIKS EVALUASI (10 ITEM)
# ==========================================
if st.session_state.raw_stocks:
    df_base = pd.DataFrame(st.session_state.raw_stocks)
    
    st.markdown("<h4 style='font-size: 18px; color:#8a90a6; margin-bottom:8px;'>📥 MATRIX EVALUASI BANDARMOLOGI (Tampilan per 10 Emiten)</h4>", unsafe_allow_html=True)
    
    # Height ditingkatkan sedikit ke 410 agar font ukuran 13pt tampil sempurna per 10 baris beserta scrollbar
    df_edited = st.data_editor(
        df_base[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]].assign(BANDARMOLOGI="NEUTRAL"),
        column_config={
            "BANDARMOLOGI": st.column_config.SelectboxColumn("INTEGRASI BANDARMOLOGI", options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"], required=True),
            "TICKER": st.column_config.Column(disabled=True), "HARGA": st.column_config.Column(disabled=True),
            "PER": st.column_config.Column(disabled=True), "PBV": st.column_config.Column(disabled=True),
            "DIV_YIELD": st.column_config.Column(disabled=True), "RSI": st.column_config.Column(disabled=True),
        },
        hide_index=True, use_container_width=True, height=410, key="editor_saham_v35"
    )
    
    # Proses Perhitungan Skor Strategi
    skor_buy_target = 70
    if "Agresif" in profil_risiko: skor_buy_target = 60
    elif "Konservatif" in profil_risiko: skor_buy_target = 75
    
    hasil_rekomendasi = []
    list_top_picks = []
    
    for idx, row in df_edited.iterrows():
        ticker = row["TICKER"]
        raw_info = next((item for item in st.session_state.raw_stocks if item["TICKER"] == ticker), None)
        if not raw_info: continue
        
        skor = 0
        if raw_info["UP_EMA20"]: skor += 15
        if raw_info["MACD_GOLDEN"]: skor += 15
        if 30 <= row["RSI"] <= 70: skor += 10
        if row["PER"] != 0 and row["PER"] < 15: skor += 15
        if row["PBV"] != 0 and row["PBV"] < 2: skor += 15
        if row["DIV_YIELD"] > 3: skor += 10
            
        if row["BANDARMOLOGI"] == "AKUMULASI": skor += 20
        elif row["BANDARMOLOGI"] == "DISTRIBUSI": skor -= 10
        else: skor += 5
        
        skor = max(0, min(100, skor))
        
        if skor >= skor_buy_target:
            keputusan = "🟢 CICIL BELI"
            sinyal = "BUY / ACCUMULATE"
            list_top_picks.append((ticker, skor))
        elif skor >= 45:
            keputusan = "🟡 HOLD / WATCHING"
            sinyal = "NEUTRAL"
        else:
            keputusan = "🔴 STRONG SELL"
            sinyal = "TAKE PROFIT / SELL"
            
        hasil_rekomendasi.append({
            "TICKER": row["TICKER"],
            "HARGA TERAKHIR": f"Rp {int(row['HARGA']):,}".replace(",", "."),
            "PER (x)": f"{float(row['PER']):.2f}" if row['PER'] > 0 else "-",
            "PBV (x)": f"{float(row['PBV']):.2f}" if row['PBV'] > 0 else "-",
            "DIV YIELD": f"{float(row['DIV_YIELD']):.2f}%",
            "RSI": f"{float(row['RSI']):.2f}",
            "BANDARMOLOGI": row["BANDARMOLOGI"],
            "SKOR SYSTEM": skor,
            "SINYAL TEKNIKAL": sinyal,
            "AKSI TRADE": keputusan
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 6. BLOK PROMAX SYSTEM INTELLIGENCE SUMMARY
    # ==========================================
    st.markdown("<h3 style='margin-bottom:15px;'>📊 PROMAX SYSTEM INTELLIGENCE SUMMARY</h3>", unsafe_allow_html=True)
    
    # Kunci Utama 1: Desain Institutional Top Picks Super Elegan & Minimalis
    if list_top_picks:
        list_top_picks.sort(key=lambda x: x[1], reverse=True)
        string_picks = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join([f"<strong style='color:#ffffff;'>{t}</strong> <span style='color:#00d4ff;'>({s} Pts)</span>" for t, s in list_top_picks[:5]])
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #0f141c, #07090d); border-left: 4px solid #00d4ff; border-top: 1px solid #1f2430; border-right: 1px solid #1f2430; border-bottom: 1px solid #1f2430; padding: 15px 22px; border-radius: 4px 12px 12px 4px; margin-bottom: 25px;">
            <span style="color: #00d4ff; font-weight: 800; font-size: 13px; letter-spacing: 1.5px; text-transform: uppercase; display: block; margin-bottom: 4px;">INSTITUTIONAL TOP PICKS</span>
            <span style="font-size: 16px; letter-spacing: 0.3px;">{string_picks}</span>
        </div>
        """, unsafe_allow_html=True)

    t_buy = sum('🟢' in x for x in df_final['AKSI TRADE'])
    t_hold = sum('🟡' in x for x in df_final['AKSI TRADE'])
    t_sell = sum('🔴' in x for x in df_final['AKSI TRADE'])
    
    # Kunci Utama 2: Teks Strategi Dihilangkan, Tinggi Kotak Menipis Ekstrem dengan Font Angka 68px
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h2 style='margin:0; color:#ffffff; font-size:68px; font-weight:900; line-height: 1.1;'><span style='color:#00e676;'>🟢</span> {t_buy} <span style='font-size:20px; color:#8a90a6; font-weight:normal;'>Emiten</span></h2>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class='metric-card'>
            <h2 style='margin:0; color:#ffffff; font-size:68px; font-weight:900; line-height: 1.1;'><span style='color:#ffb300;'>🟡</span> {t_hold} <span style='font-size:20px; color:#8a90a6; font-weight:normal;'>Emiten</span></h2>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class='metric-card'>
            <h2 style='margin:0; color:#ffffff; font-size:68px; font-weight:900; line-height: 1.1;'><span style='color:#ff1744;'>🔴</span> {t_sell} <span style='font-size:20px; color:#8a90a6; font-weight:normal;'>Emiten</span></h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 7. TABEL RADAR MATRIX (AKSI TRADE)
    # ==========================================
    st.markdown("<h4 style='font-size: 18px; color:#8a90a6; margin-bottom:8px;'>📋 RADAR MATRIX COMPREHENSIVE (Tampilan per 10 Emiten)</h4>", unsafe_allow_html=True)
    
    def style_tabel_premium(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for idx, row in df.iterrows():
            try:
                per = float(row['PER (x)'])
                if per < 15.0: styles.at[idx, 'PER (x)'] = 'color: #00ffcc; font-weight: bold;'
                elif per > 25.0: styles.at[idx, 'PER (x)'] = 'color: #ff1744;'
            except: pass
            
            # Pengecekan kolom baru AKSI TRADE
            kep = row['AKSI TRADE']
            if '🟢' in kep: styles.iloc[idx, -3:] = 'background-color: #0b1a13; color: #00ffcc; font-weight: bold;'
            elif '🟡' in kep: styles.iloc[idx, -3:] = 'background-color: #1a160b; color: #ffb300;'
            elif '🔴' in kep: styles.iloc[idx, -3:] = 'background-color: #1f0b0d; color: #ff1744;'
        return styles

    # Height disesuaikan pada 410 untuk 10 baris dengan font yang diperbesar
    st.dataframe(df_final.style.apply(style_tabel_premium, axis=None), use_container_width=True, hide_index=True, height=410)
    
    st.markdown("---")
    
    # ==========================================
    # 8. ANALISIS KINERJA & HISTORIS DEVIDEND
    # ==========================================
    st.markdown("<h3 style='margin-bottom:10px;'>📑 Analisis Kinerja Finansial & Parameter Dividen</h3>", unsafe_allow_html=True)
    pilihan_emiten = st.selectbox("🎯 Pilih Kode Emiten untuk Evaluasi Mendalam:", options=df_final["TICKER"].tolist())
    
    if pilihan_emiten:
        with st.spinner(f"⏳ Mengunduh Laporan Finansial {pilihan_emiten}..."):
            tahunan, kuartalan, info_tambahan, div_history, hist_price = fetch_advanced_financials(pilihan_emiten)
            
        if info_tambahan:
            def safe_extract_row(df, row_name):
                if df is None or row_name not in df.index: return None
                data = df.loc[row_name]
                if isinstance(data, pd.DataFrame): data = data.iloc[0]
                return data

            def safe_format_duit(val, is_eps=False):
                try:
                    if pd.isna(val) or val == "-" or val == 0: return "-"
                    val_float = float(val)
                    if is_eps: return f"{val_float:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".")
                    else: return f"{val_float / 1e9:,.2f} B"
                except: return "-"

            pilihan_metrik = st.radio("Pilih Kategori Tampilan Metrik Keuangan:", options=["Net Income", "EPS", "Revenue"], horizontal=True)
            
            yahoo_row_name = "Net Income"
            if pilihan_metrik == "EPS": yahoo_row_name = "Basic EPS"
            elif pilihan_metrik == "Revenue": yahoo_row_name = "Total Revenue"
            
            set_tahun = set()
            if tahunan is not None: set_tahun.update([pd.to_datetime(c).year for c in tahunan.columns])
            if kuartalan is not None: set_tahun.update([pd.to_datetime(c).year for c in kuartalan.columns])
            
            list_tahun = sorted([str(y) for y in set_tahun], reverse=True)[:4]
            if not list_tahun: list_tahun = ["2026", "2025", "2024", "2023"]

            df_grid = pd.DataFrame(index=["Q1", "Q2", "Q3", "Q4", "Annualised", "TTM"], columns=list_tahun).fillna("-")

            data_k = safe_extract_row(kuartalan, yahoo_row_name)
            if data_k is not None:
                for col_date in data_k.index:
                    dt = pd.to_datetime(col_date)
                    y_str = str(dt.year)
                    m = dt.month
                    if y_str in df_grid.columns:
                        if m in [1, 2, 3]: df_grid.at["Q1", y_str] = data_k[col_date]
                        elif m in [4, 5, 6]: df_grid.at["Q2", y_str] = data_k[col_date]
                        elif m in [7, 8, 9]: df_grid.at["Q3", y_str] = data_k[col_date]
                        elif m in [10, 11, 12]: df_grid.at["Q4", y_str] = data_k[col_date]

            data_t = safe_extract_row(tahunan, yahoo_row_name)
            if data_t is not None:
                for col_date in data_t.index:
                    dt = pd.to_datetime(col_date)
                    y_str = str(dt.year)
                    if y_str in df_grid.columns:
                        df_grid.at["Annualised", y_str] = data_t[col_date]
                        df_grid.at["TTM", y_str] = data_t[col_date]

            is_eps_mode = (pilihan_metrik == "EPS")
            for c in df_grid.columns:
                df_grid[c] = df_grid[c].apply(lambda x: safe_format_duit(x, is_eps=is_eps_mode))

            st.markdown(f"<p style='font-size:16px; font-weight:bold; color:#00d4ff; margin-top:10px;'>Period / {pilihan_metrik}</p>", unsafe_allow_html=True)
            st.dataframe(df_grid, use_container_width=True)
            
            st.write(" ")
            
            # Tabel Riwayat Yield Dividen (4 Tahun)
            st.markdown("<p style='font-size:16px; font-weight:bold; color:#00d4ff;'>💸 Riwayat Dividen & Yield (4 Tahun Terakhir)</p>", unsafe_allow_html=True)
            df_div_grid = pd.DataFrame(index=["Dividend Per Share", "EPS (Earning Per Share)", "Payout Ratio (%)", "Dividend Yield (%)"], columns=list_tahun).fillna("-")
            
            eps_data = safe_extract_row(tahunan, "Basic EPS")
            if eps_data is not None:
                for col_date in eps_data.index:
                    y_str = str(pd.to_datetime(col_date).year)
                    if y_str in df_div_grid.columns:
                        df_div_grid.at["EPS (Earning Per Share)", y_str] = eps_data[col_date]
            
            if div_history is not None and not div_history.empty:
                for y_str in list_tahun:
                    mask = div_history.index.year == int(y_str)
                    if mask.any():
                        df_div_grid.at["Dividend Per Share", y_str] = div_history[mask].sum()
                        
            yearly_close = {}
            if hist_price is not None and not hist_price.empty:
                for y_str in list_tahun:
                    mask = hist_price.index.year == int(y_str)
                    if mask.any():
                        yearly_close[y_str] = hist_price[mask]['Close'].iloc[-1]
            
            for c in df_div_grid.columns:
                div_val = df_div_grid.at["Dividend Per Share", c]
                eps_val = df_div_grid.at["EPS (Earning Per Share)", c]
                
                if div_val != "-":
                    if eps_val != "-" and eps_val > 0:
                        pr = (div_val / eps_val) * 100
                        df_div_grid.at["Payout Ratio (%)", c] = f"{pr:,.2f}%".replace(".", ",")
                        
                    if c in yearly_close and yearly_close[c] > 0:
                        dy = (div_val / yearly_close[c]) * 100
                        df_div_grid.at["Dividend Yield (%)", c] = f"{dy:,.2f}%".replace(".", ",")
                
                if div_val != "-": df_div_grid.at["Dividend Per Share", c] = f"Rp {div_val:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".")
                if eps_val != "-": df_div_grid.at["EPS (Earning Per Share)", c] = f"Rp {eps_val:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".")
            
            st.dataframe(df_div_grid, use_container_width=True)
        else:
            st.warning(f"⚠️ Berkas Keuangan {pilihan_emiten} Sedang Sibuk. Silakan Klik Ulang.")
else:
    st.info("💡 Klik tombol 'RE-SCAN MARKET DATA' pada Cyber Panel untuk memuat dashboard utama.")