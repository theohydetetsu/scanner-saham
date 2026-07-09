import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AI Stock Dashboard Pro", page_icon="📈", layout="wide")

st.title("📈 AI AUTOMATED STOCK SCANNER DASHBOARD (PRO EDITION)")
st.markdown("*Sistem Interaktif: Dropdown Bandarmologi + Sensor Warna Font + Ringkasan Grafik Pro*")
st.markdown("---")

# 2. DEFAULT 20 SAHAM BLUECHIP INDONESIA
default_bluechips = "BBCA, BBRI, BMRI, BBNI, TLKM, ASII, UNTR, ICBP, INDF, AMRT, GOTO, PGAS, PTBA, ITMG, KLBF, ADRO, UNVR, BRIS, CPIN, ANTM"

st.sidebar.header("⚙️ Pengaturan Awal")
saham_input = st.sidebar.text_area("Daftar Emiten:", default_bluechips, height=120)
daftar_saham = [s.strip().upper() + ".JK" for s in saham_input.split(",") if s.strip()]

muat_data = st.sidebar.button("🔄 1. TARIK DATA MARKET (CACHED)", use_container_width=True)

# 3. FUNGSI TEKNIKAL & AMBIL DATA (DI-CACHE AGAR ANTI-BLOKIR)
def hitung_rsi(df, periods=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_raw_data(saham_list):
    master_data = []
    for emiten in saham_list:
        try:
            kode = emiten.replace(".JK", "")
            df = yf.download(emiten, period="6mo", progress=False)
            if df.empty: continue
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            # Hitung Indikator Teknikal
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
            
            # Ambil Data Fundamental
            ticker = yf.Ticker(emiten)
            info = ticker.info
            
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            
            if pbv and (pbv > 50 or pbv < 0): 
                pbv = 1.0
                
            div_yield = info.get('dividendYield', 0)
            if div_yield:
                if div_yield < 1.0:
                    div_yield = div_yield * 100
            else:
                div_yield = 0.0
                
            master_data.append({
                "TICKER": kode,
                "HARGA": harga_skg,
                "PER": round(per, 2) if per else 0.0,
                "PBV": round(pbv, 2) if pbv else 0.0,
                "DIV_YIELD": round(div_yield, 2),
                "RSI": round(rsi_skg, 2),
                "UP_EMA20": harga_skg > ema20_skg,
                "MACD_GOLDEN": macd_skg > sig_skg
            })
            time.sleep(0.1)
        except Exception:
            continue
    return master_data

# 4. ALUR PROSES APLIKASI
if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks = []

if muat_data or len(st.session_state.raw_stocks) == 0:
    with st.spinner("⏳ Mengunduh data bursa saham..."):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)

if st.session_state.raw_stocks:
    df_base = pd.DataFrame(st.session_state.raw_stocks)
    df_base["BANDARMOLOGI"] = "NEUTRAL"
    
    st.subheader("📥 STEP 1: Isi Analisis Bandarmologi Anda di Sini")
    
    df_edited = st.data_editor(
        df_base[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI", "BANDARMOLOGI"]],
        column_config={
            "BANDARMOLOGI": st.column_config.SelectboxColumn(
                "BANDARMOLOGI (Pilihan)",
                options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"],
                required=True,
            ),
            "TICKER": st.column_config.Column(disabled=True),
            "HARGA": st.column_config.Column(disabled=True),
            "PER": st.column_config.Column(disabled=True),
            "PBV": st.column_config.Column(disabled=True),
            "DIV_YIELD": st.column_config.Column(disabled=True),
            "RSI": st.column_config.Column(disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_saham"
    )
    
    st.markdown("---")
    st.subheader("📊 STEP 2: Dashboard Hasil Rekomendasi Akhir AI Pro")
    
    hasil_rekomendasi = []
    raw_scores_for_chart = {} # Memori simpan skor untuk grafik
    
    for idx, row in df_edited.iterrows():
        ticker = row["TICKER"]
        raw_info = next(item for item in st.session_state.raw_stocks if item["TICKER"] == ticker)
        
        # Hitung Skor AI
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
        raw_scores_for_chart[ticker] = skor # catat skor asli
        
        # Penentuan Sinyal Bulatan 3D
        if skor >= 70:
            keputusan = "🟢 CICIL BELI"
            sinyal = "BUY / ACCUMULATE"
        elif skor >= 45:
            keputusan = "🟡 HOLD / WATCHING"
            sinyal = "NEUTRAL"
        else:
            keputusan = "🔴 STRONG SELL"
            sinyal = "TAKE PROFIT / SELL"
            
        per_val = f"{float(row['PER']):.2f}" if row['PER'] and float(row['PER']) > 0 else "-"
        pbv_val = f"{float(row['PBV']):.2f}" if row['PBV'] and float(row['PBV']) > 0 else "-"
        div_val = f"{float(row['DIV_YIELD']):.2f}%"
        rsi_val = f"{float(row['RSI']):.2f}"

        hasil_rekomendasi.append({
            "TICKER": row["TICKER"],
            "HARGA TERAKHIR": f"Rp {int(row['HARGA']):,}".replace(",", "."),
            "PER (x)": per_val,
            "PBV (x)": pbv_val,
            "DIV YIELD": div_val,
            "RSI": rsi_val,
            "BANDARMOLOGI": row["BANDARMOLOGI"],
            "SKOR AI": skor,
            "SINYAL TEKNIKAL": sinyal,
            "KEPUTUSAN AKHIR": keputusan
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)
    
    # --- TAMBAHAN BARU: METRICS PANEL (RINGKASAN COUNTER) ---
    total_buy = sum('🟢' in x for x in df_final['KEPUTUSAN AKHIR'])
    total_hold = sum('🟡' in x for x in df_final['KEPUTUSAN AKHIR'])
    total_sell = sum('🔴' in x for x in df_final['KEPUTUSAN AKHIR'])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("🟢 REKOMENDASI BUY", f"{total_buy} Emiten", help="Saham dengan skor AI >= 70")
    m_col2.metric("🟡 REKOMENDASI HOLD", f"{total_hold} Emiten", help="Saham dengan skor AI antara 45 - 69")
    m_col3.metric("🔴 REKOMENDASI SELL", f"{total_sell} Emiten", help="Saham dengan skor AI di bawah 45")
    
    st.markdown(" ") # Beri jarak spasi sedikit

    # --- TAMBAHAN BARU: PRO STOCK CHART VISUALIZATION ---
    st.write("### 📈 Grafik Kekuatan Emiten (Top Skor AI)")
    # Buat DataFrame khusus grafik dan urutkan dari skor tertinggi
    df_chart = pd.DataFrame(list(raw_scores_for_chart.items()), columns=['TICKER', 'SKOR AI'])
    df_chart = df_chart.sort_values(by='SKOR AI', ascending=False).reset_index(drop=True)
    df_chart_indexed = df_chart.set_index('TICKER')
    
    # Munculkan Grafik Batang Premium Streamlit
    st.bar_chart(df_chart_indexed, color="#00af50", height=280)
    
    st.write("### 📋 Detail Tabel Analisis Fundamental & Teknikal")
    
    # 5. ENGINE SENSOR WARNA OTOMATIS (FONT HIJAU & MERAH)
    def sensor_warna_otomatis(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for idx, row in df.iterrows():
            # Sensor PER
            try:
                per = float(row['PER (x)'])
                if per < 15.0: styles.at[idx, 'PER (x)'] = 'color: #00af50; font-weight: bold;'
                elif per > 25.0: styles.at[idx, 'PER (x)'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            
            # Sensor PBV
            try:
                pbv = float(row['PBV (x)'])
                if pbv < 2.0: styles.at[idx, 'PBV (x)'] = 'color: #00af50; font-weight: bold;'
                elif pbv > 4.0: styles.at[idx, 'PBV (x)'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            
            # Sensor Dividend Yield
            try:
                div = float(row['DIV YIELD'].replace('%', ''))
                if div > 3.0: styles.at[idx, 'DIV YIELD'] = 'color: #00af50; font-weight: bold;'
                elif div == 0.0: styles.at[idx, 'DIV YIELD'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            
            # Sensor RSI
            try:
                rsi = float(row['RSI'])
                if rsi <= 30.0: styles.at[idx, 'RSI'] = 'color: #00af50; font-weight: bold;'
                elif rsi >= 70.0: styles.at[idx, 'RSI'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            
            # Sensor Sinyal & Keputusan Akhir
            kep = row['KEPUTUSAN AKHIR']
            if '🟢' in kep:
                styles.at[idx, 'KEPUTUSAN AKHIR'] = 'color: #00af50; font-weight: bold;'
                styles.at[idx, 'SINYAL TEKNIKAL'] = 'color: #00af50; font-weight: bold;'
            elif '🟡' in kep:
                styles.at[idx, 'KEPUTUSAN AKHIR'] = 'color: #ffc000; font-weight: bold;'
                styles.at[idx, 'SINYAL TEKNIKAL'] = 'color: #ffc000; font-weight: bold;'
            elif '🔴' in kep:
                styles.at[idx, 'KEPUTUSAN AKHIR'] = 'color: #ff0000; font-weight: bold;'
                styles.at[idx, 'SINYAL TEKNIKAL'] = 'color: #ff0000; font-weight: bold;'
                
        return styles

    df_styled = df_final.style.apply(sensor_warna_otomatis, axis=None)
    st.dataframe(df_styled, use_container_width=True, hide_index=True, height=500)
    
    st.caption("💡 *Info: Grafik batang di atas akan otomatis bergeser naik/turun posisinya secara dinamis setiap kali Anda mengganti opsi Bandarmologi di tabel atas.*")
else:
    st.info("Silakan klik tombol di sidebar kiri untuk memuat data saham.")