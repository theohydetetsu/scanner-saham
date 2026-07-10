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
st.set_page_config(page_title="ZETA Terminal Pro Max", page_icon="💎", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #07090e; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 95%; }
    h1, h2, h3, h4 { font-family: 'Inter', 'Helvetica Neue', sans-serif; color: #f0f3f6; font-weight: 700; }
    h1 { font-size: 28pt !important; letter-spacing: -0.5px; }
    h3 { font-size: 20px !important; }
    
    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] { font-size: 12pt !important; }
    label { font-size: 11pt !important; font-weight: 600 !important; color: #cdd2d9 !important; }
    
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th { font-size: 11pt !important; padding: 8px 10px !important; }
    
    [data-testid="stSidebar"] { background-color: #0c0f16 !important; border-right: 1px solid #1f2430; }
    
    /* Box Metric Ramping & Responsif untuk HP (Flexbox) */
    .metric-card-thin {
        background: linear-gradient(145deg, #111520, #0d1017);
        border: 1px solid #1f2430;
        padding: 10px 15px;
        border-radius: 10px;
        box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    
    /* Tombol Eksekusi Gradient */
    div.stButton > button:first-child[kind="primary"] {
        background: linear-gradient(90deg, #00d4ff, #00ffcc) !important; color: #05070a !important;
        font-weight: 700 !important; font-size: 14px !important; border-radius: 8px !important; border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State Global
if "raw_stocks" not in st.session_state: st.session_state.raw_stocks = []
if "last_update" not in st.session_state: st.session_state.last_update = None
if "bandar_state" not in st.session_state: st.session_state.bandar_state = {}
if "radar_page" not in st.session_state: st.session_state.radar_page = 0
if "eval_page" not in st.session_state: st.session_state.eval_page = 0

@st.cache_data(ttl=600, show_spinner=False)
def fetch_ihsg_data(tf="Daily"):
    try:
        if tf == "1 Hour": df_ihsg = yf.download("^JKSE", period="1mo", interval="1h", progress=False)
        elif tf == "4 Hour": 
            df_ihsg = yf.download("^JKSE", period="1mo", interval="1h", progress=False)
            if not df_ihsg.empty: df_ihsg = df_ihsg.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
        elif tf == "Weekly": df_ihsg = yf.download("^JKSE", period="1y", interval="1wk", progress=False)
        else: df_ihsg = yf.download("^JKSE", period="3mo", interval="1d", progress=False)

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

# HEADER TERMINAL
st.markdown("<h1 style='margin-bottom:0px;'>📈 PRO MAX ALGORITHMIC TERMINAL</h1>", unsafe_allow_html=True)
col_header1, col_header2 = st.columns([2, 1])

with col_header1:
    if st.session_state.last_update:
        st.markdown(f"🕒 <span style='font-size:11pt;'>**Sinkronisasi Terakhir:** `{st.session_state.last_update}`</span>", unsafe_allow_html=True)
    else:
        st.markdown("🕒 <span style='font-size:11pt;'>**Sinkronisasi Terakhir:** `Menunggu kustomisasi scan...`</span>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8a92a6; font-size: 11pt; margin-top:-5px;'>Integrasi Multi-Pilar Terminal: Teknikal Quantum, Analisis Konsensus Fundamental, & Real-Time Bandarmologi</p>", unsafe_allow_html=True)

# ==========================================
# 2. GRAFIK IHSG DENGAN TIMEFRAME SELECTOR
# ==========================================
tf_col1, tf_col2 = st.columns([8, 2])
with tf_col2:
    selected_tf = st.selectbox("⏳ Timeframe IHSG:", ["1 Hour", "4 Hour", "Daily", "Weekly"], index=2, label_visibility="collapsed")

df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data(selected_tf)

with col_header2:
    if ihsg_now:
        warna_panah = "▲" if ihsg_chg >= 0 else "▼"
        warna_hex = "#00ffcc" if ihsg_chg >= 0 else "#ff3366"
        st.markdown(f"""
        <div style="text-align: right; background-color: #111520; padding: 10px 15px; border-radius: 12px; border: 1px solid #1f2430; margin-top:-45px;">
            <span style="color: #8a90a6; font-size: 11px; font-weight: 700;">INDEX GABUNGAN (IHSG)</span><br/>
            <span style="color: #ffffff; font-size: 32px; font-weight: 900; line-height: 1.1;">{ihsg_now:,.2f}</span><br/> 
            <span style="color: {warna_hex}; font-size: 14px; font-weight: bold;">{warna_panah} {ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)</span>
        </div>
        """, unsafe_allow_html=True)

if df_ihsg_hist is not None:
    if HAS_PLOTLY:
        fig = go.Figure(data=[go.Candlestick(
            x=df_ihsg_hist.index, open=df_ihsg_hist['Open'], high=df_ihsg_hist['High'],
            low=df_ihsg_hist['Low'], close=df_ihsg_hist['Close'],
            increasing_line_color='#00ffcc', decreasing_line_color='#ff3366', name="IHSG"
        )])
        fig.update_xaxes(
            rangebreaks=[dict(bounds=["sat", "mon"])],
            tickformat="%d %b\n%Y",
            gridcolor='rgba(255,255,255,0.03)'
        )
        fig.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=5, r=5, t=5, b=5), height=220, xaxis_rangeslider_visible=False,
            yaxis=dict(gridcolor='rgba(255,255,255,0.03)', tickfont=dict(size=11))
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.line_chart(df_ihsg_hist[['Close']], color="#00ffcc", height=220)

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
st.sidebar.markdown("""
<div style="padding: 5px 0px 15px 0px;">
    <h2 style="color: #00d4ff; font-size: 22px; font-weight: 800; margin-bottom: 0px;">💎 CYBER PANEL</h2>
    <p style="color: #6c757d; font-size: 12px; margin-top: 2px;">Premium Quantum Engine v3.5</p>
</div>
""", unsafe_allow_html=True)

roster_saham_idx = [
    "BBCA", "BBRI", "BMRI", "BBNI", "TLKM", "ASII", "UNTR", "ICBP", "INDF", 
    "AMRT", "GOTO", "PGAS", "PTBA", "ITMG", "KLBF", "ADRO", "UNVR", "BRIS", 
    "CPIN", "ANTM", "TPIA", "BREN", "AMMN", "ADMR", "MEDC", "AKRA", "ACES"
]

saham_terpilih = st.sidebar.multiselect("📋 DAFTAR EMITEN PANTAUAN:", options=roster_saham_idx, default=roster_saham_idx[:15])
daftar_saham = [s.strip().upper() + ".JK" for s in saham_terpilih if s.strip()]

# Inisialisasi state awal bandarmologi default ke NEUTRAL jika emiten baru dimasukkan
for s in daftar_saham:
    ticker_name = s.replace(".JK", "")
    if ticker_name not in st.session_state.bandar_state:
        st.session_state.bandar_state[ticker_name] = "NEUTRAL"

st.sidebar.write(" ")

# PERBAIKAN UTAMA: Tombol Re-Scan membersihkan cache secara paksa agar memicu animasi loading spinner
muat_data = st.sidebar.button("🔄 RE-SCAN MARKET DATA", use_container_width=True, type="primary")
st.sidebar.markdown("<br/>", unsafe_allow_html=True)

profil_risiko = st.sidebar.selectbox("🎯 Profil Risiko Trading:", ["Moderat (Standar)", "Agresif (High Risk)", "Konservatif (Aman)"])
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reset System Cache", use_container_width=True):
    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()

# ==========================================
# 4. CORE ENGINE CALCULATION (INDIKATOR)
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
            ticker = yf.Ticker(emiten)
            info = ticker.info
            
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            if pbv and (pbv > 100 or pbv < 0): pbv = 1.0
            div_yield = info.get('dividendYield', 0)
            if div_yield < 1.0: div_yield = div_yield * 100
                
            master_data.append({
                "TICKER": kode, "HARGA": harga_skg, "PER": round(per, 2) if per else 0.0,
                "PBV": round(pbv, 2) if pbv else 0.0, "DIV_YIELD": round(div_yield, 2) if div_yield else 0.0,
                "RSI": round(float(df['RSI'].iloc[-1]), 2) if not np.isnan(df['RSI'].iloc[-1]) else 50.0,
                "UP_EMA20": harga_skg > float(df['EMA20'].iloc[-1]),
                "MACD_GOLDEN": float(df['MACD'].iloc[-1]) > float(df['Signal'].iloc[-1])
            })
            time.sleep(0.04) 
        except: continue
    return master_data

# Eksekusi pembersihan cache & reload data bursa secara riil jika tombol ditekan
if muat_data:
    st.cache_data.clear()  # Bersihkan memori cache agar yfinance dipaksa mendownload ulang
    with st.spinner("⏳ Mengkalibrasi Ulang Data Pasar..."):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
        st.session_state.last_update = datetime.now().strftime("%d %b %Y - %H:%M:%S WIB")
        st.session_state.radar_page = 0
        st.session_state.eval_page = 0
    st.rerun()

# Otomatis meload data pertama kali jika session state kosong
if len(st.session_state.raw_stocks) == 0 and daftar_saham:
    with st.spinner("⏳ Menginisialisasi Data Pasar Awal..."):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
        st.session_state.last_update = datetime.now().strftime("%d %b %Y - %H:%M:%S WIB")

# ==========================================
# 5. INTEGRASI ALGORITMA SKORING SYSTEM
# ==========================================
if st.session_state.raw_stocks:
    skor_buy_target = 70
    if "Agresif" in profil_risiko: skor_buy_target = 60
    elif "Konservatif" in profil_risiko: skor_buy_target = 75
    
    hasil_rekomendasi = []
    list_top_picks = []
    
    for raw_info in st.session_state.raw_stocks:
        ticker = raw_info["TICKER"]
        status_bandar = st.session_state.bandar_state.get(ticker, "NEUTRAL")
        
        skor = 0
        if raw_info["UP_EMA20"]: skor += 15
        if raw_info["MACD_GOLDEN"]: skor += 15
        if 30 <= raw_info["RSI"] <= 70: skor += 10
        if raw_info["PER"] != 0 and raw_info["PER"] < 15: skor += 15
        if raw_info["PBV"] != 0 and raw_info["PBV"] < 2: skor += 15
        if raw_info["DIV_YIELD"] > 3: skor += 10
        if status_bandar == "AKUMULASI": skor += 20
        elif status_bandar == "DISTRIBUSI": skor -= 10
        else: skor += 5
        
        skor = max(0, min(100, skor))
        
        if skor >= skor_buy_target:
            keputusan, sinyal = "🟢 CICIL BELI", "BUY / ACCUMULATE"
            list_top_picks.append((ticker, skor))
        elif skor >= 45:
            keputusan, sinyal = "🟡 HOLD / WATCHING", "NEUTRAL"
        else:
            keputusan, sinyal = "🔴 STRONG SELL", "TAKE PROFIT / SELL"
            
        try:
            harga_bersih = int(float(raw_info['HARGA']))
            harga_format = f"Rp {harga_bersih:,}".replace(",", ".")
        except:
            harga_format = f"Rp {raw_info['HARGA']}"
            
        hasil_rekomendasi.append({
            "TICKER": ticker,
            "HARGA TERAKHIR": harga_format,
            "PER (x)": f"{float(raw_info['PER']):.2f}" if raw_info['PER'] > 0 else "-",
            "PBV (x)": f"{float(raw_info['PBV']):.2f}" if raw_info['PBV'] > 0 else "-",
            "DIV YIELD": f"{float(raw_info['DIV_YIELD']):.2f}%",
            "RSI": f"{float(raw_info['RSI']):.2f}",
            "BANDARMOLOGI": status_bandar,
            "SKOR AI": skor,
            "SINYAL TEKNIKAL": sinyal,
            "KEPUTUSAN AKHIR": keputusan
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)

    # ==========================================
    # 6. SUMMARY PANEL & TOP PICKS
    # ==========================================
    st.markdown("<h3 style='margin-bottom:10px;'>📊 PROMAX SYSTEM INTELLIGENCE SUMMARY</h3>", unsafe_allow_html=True)
    
    if list_top_picks:
        list_top_picks.sort(key=lambda x: x[1], reverse=True)
        string_picks = " &nbsp;&nbsp;·&nbsp;&nbsp; ".join([f"<strong style='color:#ffffff;'>{t}</strong> <span style='color:#00d4ff;'>({s})</span>" for t, s in list_top_picks[:6]])
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #0f141c, #07090d); border-left: 3px solid #00d4ff; padding: 10px 15px; border-radius: 4px; margin-bottom: 15px;">
            <span style="color: #00d4ff; font-size: 11px; font-weight: bold; letter-spacing: 1px;">INSTITUTIONAL TOP PICKS</span><br/>
            <span style="font-size: 13px;">{string_picks}</span>
        </div>
        """, unsafe_allow_html=True)

    t_buy = sum('🟢' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_hold = sum('🟡' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_sell = sum('🔴' in x for x in df_final['KEPUTUSAN AKHIR'])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""
        <div class='metric-card-thin'>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style='font-size:24px;'>🟢</span>
                <span style='color:#ffffff; font-size:32px; font-weight:900;'>{t_buy}</span>
            </div>
            <div style="text-align:right;">
                <span style='color:#00e676; font-size:11px; font-weight:bold;'>STRATEGI BUY ACCUMULATE</span><br/>
                <span style='font-size:11px; color:#8a90a6;'>Emiten</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class='metric-card-thin'>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style='font-size:24px;'>🟡</span>
                <span style='color:#ffffff; font-size:32px; font-weight:900;'>{t_hold}</span>
            </div>
            <div style="text-align:right;">
                <span style='color:#ffb300; font-size:11px; font-weight:bold;'>STRATEGI WATCHING / HOLD</span><br/>
                <span style='font-size:11px; color:#8a90a6;'>Emiten</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class='metric-card-thin'>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style='font-size:24px;'>🔴</span>
                <span style='color:#ffffff; font-size:32px; font-weight:900;'>{t_sell}</span>
            </div>
            <div style="text-align:right;">
                <span style='color:#ff1744; font-size:11px; font-weight:bold;'>STRATEGI LIQUIDATE / SELL</span><br/>
                <span style='font-size:11px; color:#8a90a6;'>Emiten</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 7. RADAR MATRIX COMPREHENSIVE (TABEL UTAMA)
    # ==========================================
    st.markdown(f"<h4 style='font-size: 15px; color:#8a90a6; margin-bottom:5px;'>📋 Comprehensive Radar Matrix Table</h4>", unsafe_allow_html=True)
    
    # PERBAIKAN TOTAL MUTLAK: Menggunakan penanda .loc berbasis nama kolom & indeks asli (Anti IndexError)
    def style_tabel_premium(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for idx, row in df.iterrows():
            try:
                per_val = row['PER (x)']
                if per_val != "-" and float(per_val) < 15.0: 
                    styles.loc[idx, 'PER (x)'] = 'color: #00ffcc; font-weight: bold;'
            except: pass
            
            kep = str(row.get('KEPUTUSAN AKHIR', ''))
            target_cols = ['SKOR AI', 'SINYAL TEKNIKAL', 'KEPUTUSAN AKHIR']
            valid_cols = [c for c in target_cols if c in df.columns]
            
            if '🟢' in kep: 
                styles.loc[idx, valid_cols] = 'background-color: #0b1a13; color: #00ffcc; font-weight: bold;'
            elif '🟡' in kep: 
                styles.loc[idx, valid_cols] = 'background-color: #1a160b; color: #ffb300; font-weight: bold;'
            elif '🔴' in kep: 
                styles.loc[idx, valid_cols] = 'background-color: #1f0b0d; color: #ff1744; font-weight: bold;'
        return styles

    items_per_page = 10
    total_radar_pages = max(1, len(df_final) // items_per_page + (1 if len(df_final) % items_per_page > 0 else 0))
    start_radar = st.session_state.radar_page * items_per_page
    df_radar_display = df_final.iloc[start_radar:start_radar + items_per_page]
    
    st.dataframe(df_radar_display.style.apply(style_tabel_premium, axis=None), use_container_width=True, hide_index=True)
    
    # Pagination Kontrol Radar Matrix
    r_col1, r_col2, r_col3 = st.columns([1, 8, 1])
    with r_col1:
        if st.button("⬅️", key="prev_radar", use_container_width=True, disabled=st.session_state.radar_page == 0):
            st.session_state.radar_page -= 1; st.rerun()
    with r_col2:
        st.markdown(f"<div style='text-align: center; color: #8a90a6; font-size:12px;'>Page {st.session_state.radar_page + 1} of {total_radar_pages}</div>", unsafe_allow_html=True)
    with r_col3:
        if st.button("➡️", key="next_radar", use_container_width=True, disabled=st.session_state.radar_page >= total_radar_pages - 1):
            st.session_state.radar_page += 1; st.rerun()

    # ==========================================
    # 8. MATRIX EVALUASI BANDARMOLOGI (INPUT DATA)
    # ==========================================
    with st.expander("⚙️ BUKA MATRIX EVALUASI BANDARMOLOGI (Input Data)", expanded=False):
        st.markdown("<p style='color:#00d4ff; font-size:12px; font-weight:bold;'>💡 Petunjuk: Ubah status bandarmologi emiten pada kolom dropdown di bawah untuk mengupdate kalkulasi radar utama.</p>", unsafe_allow_html=True)
        
        df_base = pd.DataFrame(st.session_state.raw_stocks)[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]]
        df_base["INTEGRASI BANDARMOLOGI"] = df_base["TICKER"].map(st.session_state.bandar_state)
        
        total_eval_pages = max(1, len(df_base) // items_per_page + (1 if len(df_base) % items_per_page > 0 else 0))
        start_eval = st.session_state.eval_page * items_per_page
        df_eval_display = df_base.iloc[start_eval:start_eval + items_per_page].copy()
        
        # Data Editor dengan konfigurasi Dropdown manual berbentuk segitiga presisi
        edited_df = st.data_editor(
            df_eval_display,
            column_config={
                "INTEGRASI BANDARMOLOGI": st.column_config.SelectboxColumn(
                    "🔽 INTEGRASI BANDARMOLOGI", 
                    options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"], 
                    required=True,
                    width="medium"
                ),
                "TICKER": st.column_config.Column(disabled=True), "HARGA": st.column_config.Column(disabled=True),
                "PER": st.column_config.Column(disabled=True), "PBV": st.column_config.Column(disabled=True),
                "DIV_YIELD": st.column_config.Column(disabled=True), "RSI": st.column_config.Column(disabled=True),
            },
            hide_index=True, use_container_width=True, key=f"editor_eval_v36_{st.session_state.eval_page}"
        )
        
        # Logika Sinkronisasi anti-infinite loop
        state_changed = False
        if edited_df is not None:
            for _, row in edited_df.iterrows():
                ticker = row["TICKER"]
                new_val = row["INTEGRASI BANDARMOLOGI"]
                if st.session_state.bandar_state.get(ticker) != new_val:
                    st.session_state.bandar_state[ticker] = new_val
                    state_changed = True
            if state_changed: 
                st.rerun()

        # Pagination Kontrol Matrix Evaluasi
        e_col1, e_col2, e_col3 = st.columns([1, 8, 1])
        with e_col1:
            if st.button("⬅️", key="prev_eval", use_container_width=True, disabled=st.session_state.eval_page == 0):
                st.session_state.eval_page -= 1; st.rerun()
        with e_col2:
            st.markdown(f"<div style='text-align: center; color: #8a90a6; font-size:12px;'>Page {st.session_state.eval_page + 1} of {total_eval_pages}</div>", unsafe_allow_html=True)
        with e_col3:
            if st.button("➡️", key="next_eval", use_container_width=True, disabled=st.session_state.eval_page >= total_eval_pages - 1):
                st.session_state.eval_page += 1; st.rerun()

    st.markdown("---")
    
    # ==========================================
    # 9. ANALISIS KINERJA FINANSIAL & DIVIDEN
    # ==========================================
    st.markdown("<h3 style='margin-bottom:10px;'>📑 Analisis Kinerja Finansial & Parameter Dividen</h3>", unsafe_allow_html=True)
    pilihan_emiten = st.selectbox("🎯 Pilih Kode Emiten untuk Evaluasi Mendalam:", options=df_final["TICKER"].tolist())
    
    if pilihan_emiten:
        with st.spinner(f"⏳ Mengunduh data fundamental {pilihan_emiten}..."):
            fin_annual, fin_quarter, info_emiten, dividen, hist_5y = fetch_advanced_financials(pilihan_emiten)
            if fin_annual is not None and not fin_annual.empty:
                tab1, tab2, tab3 = st.tabs(["💰 Laporan Keuangan", "📊 Valuasi & Profitabilitas", "💸 Historis Dividen"])
                
                with tab1:
                    st.dataframe(fin_annual.fillna(0).astype(int), use_container_width=True)
                with tab2:
                    col_v1, col_v2, col_v3 = st.columns(3)
                    col_v1.metric("P/E Ratio", f"{info_emiten.get('trailingPE', 0):.2f}x")
                    col_v1.metric("Price to Book (PBV)", f"{info_emiten.get('priceToBook', 0):.2f}x")
                    roe = info_emiten.get('returnOnEquity', 0) * 100 if info_emiten.get('returnOnEquity') else 0
                    col_v2.metric("Return on Equity (ROE)", f"{roe:.2f}%")
                    op_margin = info_emiten.get('operatingMargins', 0) * 100 if info_emiten.get('operatingMargins') else 0
                    col_v3.metric("Operating Margin", f"{op_margin:.2f}%")
                with tab3:
                    if dividen is not None and not dividen.empty:
                        div_recent = dividen.tail(15)
                        if HAS_PLOTLY:
                            fig_div = go.Figure([go.Bar(x=div_recent.index, y=div_recent.values, marker_color='#00d4ff')])
                            fig_div.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=5, r=5, t=10, b=5), height=250)
                            st.plotly_chart(fig_div, use_container_width=True)
                        else:
                            st.bar_chart(div_recent, color="#00d4ff")
            else:
                st.warning("⚠️ Data fundamental sedang tidak tersedia.")
