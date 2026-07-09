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
# 1. KONFIGURASI HALAMAN UTAMA & UI STYLE
# ==========================================
st.set_page_config(page_title="AI Stock Dashboard Pro Max v3.3", page_icon="💎", layout="wide")

# Inject Custom CSS Premium Theme (Luxury Dark Slate Style)
st.markdown("""
<style>
    /* Global Background & Container Padding */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    /* Typography Customization */
    h1 { color: #ffffff; font-weight: 800; letter-spacing: -0.5px; font-size: 26pt !important; }
    h3 { color: #ffffff; font-weight: 700; letter-spacing: -0.3px; }
    h4 { color: #00ffcc; font-weight: 600; }
    
    /* Elegant Sidebar Tuning */
    [data-testid="stSidebar"] {
        background-color: #111318 !important;
        border-right: 1px solid #232731;
    }
    
    /* Premium Metric & Element Cards */
    .metric-card {
        background-color: #161920;
        border: 1px solid #242936;
        padding: 18px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        border-color: #384154;
    }
    
    /* Streamlit Widget Polishing */
    .stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: bold; }
    div.stButton > button:first-child {
        background-color: #00ffcc !important;
        color: #0b0c10 !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        border: none !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #00cc55 !important;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.4);
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
        return ticker.financials, ticker.quarterly_financials, ticker.info
    except Exception:
        return None, None, None

# TAMPILAN HEADER UTAMA (INSTITUTIONAL STYLE)
st.markdown("<h1 style='margin-bottom:0px;'>📈 AI AUTOMATED STOCK SCANNER</h1>", unsafe_allow_html=True)

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()
col_header1, col_header2 = st.columns([2, 1])

with col_header1:
    if st.session_state.last_update:
        st.markdown(f"🕒 **Terakhir Diperbarui Otomatis:** `{st.session_state.last_update}`")
    else:
        st.markdown("🕒 **Terakhir Diperbarui Otomatis:** `Menunggu sinkronisasi bursa...`")
    st.markdown("<p style='color: #6c757d; font-size: 11pt; margin-top:-5px;'>Multi-Pilar Integrasi Terminal: Teknikal Quantum, Analisis Konsensus Fundamental, & Real-Time Bandarmologi</p>", unsafe_allow_html=True)

with col_header2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_hex = "#00ffcc" if ihsg_chg >= 0 else "#ff3366"
        st.markdown(f"""
        <div style="text-align: right; background-color: #161920; padding: 10px 15px; border-radius: 8px; border: 1px solid #242936;">
            <span style="color: #8a90a6; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;">INDEX GABUNGAN (IHSG)</span><br/>
            <span style="color: #ffffff; font-size: 20px; font-weight: 800;">{ihsg_now:,.2f}</span> 
            <span style="color: {warna_hex}; font-size: 12px; font-weight: bold;">{warna_panah} {ihsg_pct:+.2f}%</span>
        </div>
        """, unsafe_allow_html=True)

# --- REVISI GRAFIK REEL IHSG (3 TYPE TAMPILAN) ---
if df_ihsg_hist is not None:
    with st.expander("📊 LIVE MARKET CHART: Tren Pergerakan Riil IHSG (Klik untuk Melipat)", expanded=True):
        tipe_grafik = st.radio(
            "Pilih Tipe Grafik Tampilan:",
            options=["🕯️ Candlestick (Pro Trader)", "📉 Line Chart (Garis Tren)", "🗺️ Area Chart (Volume Wilayah)"],
            horizontal=True,
            label_visibility="visible"
        )
        
        st.write(" ")
        if "Candlestick" in tipe_grafik:
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
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    xaxis_rangeslider_visible=False,
                    yaxis=dict(gridcolor='rgba(255,255,255,0.04)', title="Poin Indeks"),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.04)', title="Tanggal")
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.bar_chart(df_ihsg_hist[['Close']], color="#00ffcc", height=250)
                
        elif "Line Chart" in tipe_grafik:
            st.line_chart(df_ihsg_hist[['Close']], color="#00ffcc", height=260)
            
        elif "Area Chart" in tipe_grafik:
            st.area_chart(df_ihsg_hist[['Close']], color="#00af50", height=260)

st.markdown("---")

# ==========================================
# 2. PREMIUM CYBER PANEL (SIDEBAR UPGRADED)
# ==========================================
st.sidebar.markdown("""
<div style="padding: 5px 0px 15px 0px;">
    <h2 style="color: #00ffcc; font-size: 22px; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 0px;">💎 CYBER PANEL</h2>
    <p style="color: #6c757d; font-size: 11px; margin-top: 2px; margin-bottom: 0px;">AI Premium Scanner Engine v3.3</p>
</div>
""", unsafe_allow_html=True)

# Master Data Roster untuk Token Chips Elegan
roster_saham_idx = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", 
    "AMRT", "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", 
    "CPIN", "ANTM", "TPIA", "BREN", "AMMN", "ADMR", "MEDC", "AKRA", "ACES", 
    "MYOR", "SMGR", "INCO", "PGEO", "BUKA", "MDKA", "HRUM", "ISAT", "EXCL"
]

# Transformasi Komponen menjadi Multiselect Token Chips yang Elegan
saham_terpilih = st.sidebar.multiselect(
    "📋 DAFTAR EMITEN PANTAUAN:",
    options=roster_saham_idx,
    default=roster_saham_idx[:30], # Memuat otomatis 30 emiten utama standar Anda
    help="Klik untuk menghapus atau ketik kode emiten baru untuk menambahkan ke radar pantauan."
)

# Parsing data untuk kebutuhan query bursa Yahoo Finance
daftar_saham = [s.strip().upper() + ".JK" for s in saham_terpilih if s.strip()]

st.sidebar.write(" ")
muat_data = st.sidebar.button("🔄 RE-SCAN MARKET DATA", use_container_width=True, type="primary")
st.sidebar.markdown("<br/>", unsafe_allow_html=True)

st.sidebar.markdown("<span style='color:#8a90a6; font-size:11px; font-weight:bold;'>🎛️ PARAMETER AI CONFIDENCE</span>", unsafe_allow_html=True)
profil_risiko = st.sidebar.selectbox(
    "🎯 Profil Risiko Trading:",
    ["Moderat (Standar)", "Agresif (High Risk)", "Konservatif (Aman)"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")

st.sidebar.markdown("<span style='color:#8a90a6; font-size:11px; font-weight:bold;'>📡 ENGINE CONNECTIVITY</span>", unsafe_allow_html=True)
st.sidebar.info(f"📊 **Active Watchlist:** {len(daftar_saham)} Emiten")
if st.session_state.last_update:
    st.sidebar.success("● NETWORK STATUS: ONLINE")
else:
    st.sidebar.warning("○ NETWORK STATUS: IDLE")
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reset System Cache", use_container_width=True):
    st.cache_data.clear()
    st.session_state.clear()
    st.sidebar.success("Cache Cleared! Mengulang sistem...")
    st.rerun()

# ==========================================
# 3. CORE ANALYTICS ENGINE
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
            time.sleep(0.05) 
        except: continue
    return master_data

if muat_data or len(st.session_state.raw_stocks) == 0:
    if daftar_saham:
        with st.spinner("⏳ Menghubungkan ke Bursa Efek Indonesia..."):
            st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
            st.session_state.last_update = datetime.now().strftime("%H:%M:%S WIB")

# ==========================================
# 4. DASHBOARD PRESENTASI REKOMENDASI AI
# ==========================================
if st.session_state.raw_stocks:
    df_base = pd.DataFrame(st.session_state.raw_stocks)
    
    with st.expander("📥 MATRIX EVALUASI BANDARMOLOGI (Klik untuk Membuka)", expanded=False):
        st.markdown("<p style='color: #8a90a6; font-size:13px;'>Tentukan parameter pergerakan akumulasi bandar. AI akan otomatis mengalkulasi skor secara real-time.</p>", unsafe_allow_html=True)
        df_edited = st.data_editor(
            df_base[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]].assign(BANDARMOLOGI="NEUTRAL"),
            column_config={
                "BANDARMOLOGI": st.column_config.SelectboxColumn("INTEGRASI BANDARMOLOGI", options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"], required=True),
                "TICKER": st.column_config.Column(disabled=True), "HARGA": st.column_config.Column(disabled=True),
                "PER": st.column_config.Column(disabled=True), "PBV": st.column_config.Column(disabled=True),
                "DIV_YIELD": st.column_config.Column(disabled=True), "RSI": st.column_config.Column(disabled=True),
            },
            hide_index=True, use_container_width=True, key="editor_saham_v3"
        )
    
    st.markdown("---")
    st.markdown("<h3 style='margin-bottom:12px;'>📊 AI PRO MAX INTELLIGENCE RECOMMENDATION</h3>", unsafe_allow_html=True)
    
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
            "SKOR AI": skor,
            "SINYAL TEKNIKAL": sinyal,
            "KEPUTUSAN AKHIR": keputusan
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)
    
    # PREMIUM BOX HIGHLIGHT: AI TOP PICKS
    if list_top_picks:
        list_top_picks.sort(key=lambda x: x[1], reverse=True)
        string_picks = ", ".join([f"**{t}** ({s} Pts)" for t, s in list_top_picks[:5]])
        st.markdown(f"""
        <div style="background-color: #0c1f1a; border: 1px solid #00e676; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <span style="color: #00ffcc; font-weight: bold; font-size: 15px;">🔥 AI INSTITUTIONAL TOP PICKS HARI INI:</span><br/>
            <span style="color: #ffffff; font-size: 13px;">Emiten dengan konformitas teknikal terbaik & akumulasi masif: {string_picks}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #241418; border: 1px solid #ff1744; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <span style="color: #ff80ab; font-weight: bold; font-size: 13px;">⚠ MARKET WARNING:</span> <span style="color: #ffffff; font-size: 12px;">Alokasikan dana tunai lebih banyak. Belum ada emiten yang menyentuh batas konfirmasi aman AI.</span>
        </div>
        """, unsafe_allow_html=True)

    # Grid Ringkasan Strategi 3 Kolom
    t_buy = sum('🟢' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_hold = sum('🟡' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_sell = sum('🔴' in x for x in df_final['KEPUTUSAN AKHIR'])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"<div class='metric-card'><span style='color:#00e676; font-size:11px; font-weight:bold;'>🟢 STRATEGI BUY ACCUMULATE</span><br/><h2 style='margin:5px 0 0 0; color:#ffffff;'>{t_buy} <span style='font-size:13px; color:#6c757d; font-weight:normal;'>Emiten</span></h2></div>", unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"<div class='metric-card'><span style='color:#ffb300; font-size:11px; font-weight:bold;'>🟡 STRATEGI WATCHING / HOLD</span><br/><h2 style='margin:5px 0 0 0; color:#ffffff;'>{t_hold} <span style='font-size:13px; color:#6c757d; font-weight:normal;'>Emiten</span></h2></div>", unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"<div class='metric-card'><span style='color:#ff1744; font-size:11px; font-weight:bold;'>🔴 STRATEGI LIQUIDATE / SELL</span><br/><h2 style='margin:5px 0 0 0; color:#ffffff;'>{t_sell} <span style='font-size:13px; color:#6c757d; font-weight:normal;'>Emiten</span></h2></div>", unsafe_allow_html=True)
    
    st.write(" ")
    st.markdown("#### 📋 Comprehensive Radar Matrix Table")
    
    # Fungsi Conditional Formatting Otomatis Tabel
    def style_tabel_premium(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for idx, row in df.iterrows():
            try:
                per = float(row['PER (x)'])
                if per < 15.0: styles.at[idx, 'PER (x)'] = 'color: #00ffcc; font-weight: bold;'
                elif per > 25.0: styles.at[idx, 'PER (x)'] = 'color: #ff1744;'
            except: pass
            try:
                pbv = float(row['PBV (x)'])
                if pbv < 2.0: styles.at[idx, 'PBV (x)'] = 'color: #00ffcc; font-weight: bold;'
            except: pass
            
            kep = row['KEPUTUSAN AKHIR']
            if '🟢' in kep: styles.iloc[idx, -3:] = 'background-color: #092015; color: #00ffcc; font-weight: bold;'
            elif '🟡' in kep: styles.iloc[idx, -3:] = 'background-color: #1f1b0a; color: #ffb300;'
            elif '🔴' in kep: styles.iloc[idx, -3:] = 'background-color: #240f13; color: #ff1744;'
        return styles

    st.dataframe(df_final.style.apply(style_tabel_premium, axis=None), use_container_width=True, hide_index=True, height=400)
    
    # ==========================================
    # 5. STEP 3: FINANCIAL DEEP-DIVE
    # ==========================================
    st.markdown("---")
    st.subheader("📑 STEP 3: Analisis Ringkas Laporan Keuangan & Dividen")
    
    pilihan_emiten = st.selectbox("🎯 Pilih Kode Emiten untuk Cek Financials:", options=df_final["TICKER"].tolist())
    
    if pilihan_emiten:
        with st.spinner(f"⏳ Menarik data finansial {pilihan_emiten}..."):
            tahunan, kuartalan, info_tambahan = fetch_advanced_financials(pilihan_emiten)
            
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
            list_tahun = sorted([str(y) for y in set_tahun], reverse=True)[:3]
            if not list_tahun: list_tahun = ["2026", "2025", "2024"]

            df_grid = pd.DataFrame(index=["Q1", "Q2", "Q3", "Q4", "Annualised"], columns=list_tahun).fillna("-")

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

            is_eps_mode = (pilihan_metrik == "EPS")
            for c in df_grid.columns:
                df_grid[c] = df_grid[c].apply(lambda x: safe_format_duit(x, is_eps=is_eps_mode))

            st.markdown(f"**Period / {pilihan_metrik}**")
            st.dataframe(df_grid, use_container_width=True)
            
            # PROTEKSI DIVIDEN YIELD & PR ACCURACY
            div_yield_raw = info_tambahan.get('dividendYield', 0)
            payout_raw = info_tambahan.get('payoutRatio', 0)
            div_rate = info_tambahan.get('dividendRate', 0)
            
            div_yield = (div_yield_raw * 100) if (div_yield_raw and div_yield_raw < 1.0) else (div_yield_raw or 0.0)
            payout_ratio = (payout_raw * 100) if (payout_raw and payout_raw < 1.0) else (payout_raw or 0.0)
            
            if div_yield > 100.0: div_yield /= 100.0
            if payout_ratio > 100.0: payout_ratio /= 100.0
            
            st.markdown("**📊 Ringkasan Data Dividen Riil (Current)**")
            df_div_bottom = pd.DataFrame({
                "Dividend Rate (TTM)": [f"Rp {div_rate:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".") if div_rate else "-"],
                "Payout Ratio (%)": [f"{payout_ratio:.2f}%".replace(".", ",") if payout_ratio else "-"],
                "Dividend Yield (%)": [f"{div_yield:.2f}%".replace(".", ",") if div_yield else "-"]
            }, index=["Metrik Saham Terpilih"])
            st.dataframe(df_div_bottom, use_container_width=True)
else:
    st.info("💡 Klik tombol 'RE-SCAN MARKET DATA' pada Cyber Panel untuk memuat dashboard utama.")
