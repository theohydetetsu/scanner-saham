import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AI Stock Dashboard Pro Max", page_icon="📈", layout="wide")

# Inisialisasi Memori Aplikasi (Session State)
if "raw_stocks" not in st.session_state:
    st.session_state.raw_stocks = []
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# Fungsi Memuat Data IHSG
@st.cache_data(ttl=600, show_spinner=False)
def fetch_ihsg_data():
    try:
        df_ihsg = yf.download("^JKSE", period="1mo", interval="1d", progress=False)
        df_ihsg.columns = [col[0] if isinstance(col, tuple) else col for col in df_ihsg.columns]
        
        harga_skg = float(df_ihsg['Close'].iloc[-1])
        harga_lalu = float(df_ihsg['Close'].iloc[-2])
        perubahan = harga_skg - harga_lalu
        persen = (perubahan / harga_lalu) * 100
        
        return df_ihsg[['Close']], harga_skg, perubahan, persen
    except Exception:
        return None, None, None, None

# Fungsi Memuat Laporan Keuangan Sederhana (Step 3)
def fetch_simple_financials(ticker_code):
    try:
        ticker = yf.Ticker(ticker_code + ".JK")
        return ticker.financials, ticker.info
    except Exception:
        return None, None

# TAMPILAN HEADER UTAMA
st.title("📈 AI AUTOMATED STOCK SCANNER DASHBOARD (PRO MAX EDITION)")

# MEMUAT & MENAMPILKAN RADAR INDEKS IHSG
df_ihsg_hist, ihsg_now, ihsg_chg, ihsg_pct = fetch_ihsg_data()

col_header1, col_header2 = st.columns([2, 1])

with col_header1:
    if st.session_state.last_update:
        st.markdown(f"🕒 **Terakhir Diperbarui Otomatis:** `{st.session_state.last_update}`")
    else:
        st.markdown("🕒 **Terakhir Diperbarui Otomatis:** `Belum memuat data market`")
    st.markdown("*Sistem Integrasi Multi-Pilar: Teknikal, Fundamental, Bandarmologi, dan Financial Statements*")

with col_header2:
    if ihsg_now:
        warna_panah = "📈" if ihsg_chg >= 0 else "📉"
        st.metric(
            label=f"{warna_panah} INDEKS HARGA SAHAM GABUNGAN (IHSG)",
            value=f"{ihsg_now:,.2f}".replace(",", "."),
            delta=f"{ihsg_chg:+,.2f} ({ihsg_pct:+.2f}%)".replace(",", "."),
        )

# Grafik Tren IHSG Kompak (Bisa diminimize)
if df_ihsg_hist is not None:
    with st.expander("📊 Lihat Grafik Pergerakan Tren IHSG (1 Bulan Terakhir)", expanded=False):
        st.line_chart(df_ihsg_hist, color="#00ffcc", height=200)

st.markdown("---")

# 2. PENGATURAN AWAL & 25 SAHAM PILIHAN BEI
default_stocks = "BBCA, BBRI, BMRI, BBNI, TLKM, ASII, UNTR, ICBP, INDF, AMRT, GOTO, PGAS, PTBA, ITMG, KLBF, ADRO, UNVR, BRIS, CPIN, ANTM, BREN, AMMN, TPIA, BRPT, MDKA"

st.sidebar.header("⚙️ Pengaturan Awal")
saham_input = st.sidebar.text_area("Daftar Emiten Pantauan:", default_stocks, height=150)

# Parsing data emiten
daftar_saham = [s.strip().upper() + ".JK" for s in saham_input.split(",") if s.strip()]

muat_data = st.sidebar.button("🔄 TARIK DATA MARKET", use_container_width=True)

# FUNGSI TEKNIKAL & AMBIL DATA KESELURUHAN
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
            
            if pbv and (pbv > 100 or pbv < 0): pbv = 1.0
            div_yield = info.get('dividendYield', 0)
            if div_yield:
                if div_yield < 1.0: div_yield = div_yield * 100
            else: div_yield = 0.0
                
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
            time.sleep(0.05)
        except Exception:
            continue
    return master_data

# ALUR PROSES UPDATE DASHBOARD
if muat_data:
    if not daftar_saham:
        st.sidebar.error("⚠️ Daftar emiten tidak boleh kosong!")
    else:
        st.cache_data.clear()
        with st.spinner("⏳ Sedang memperbarui data bursa & menghitung metrik AI..."):
            st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
            st.session_state.last_update = datetime.now().strftime("%d %B %Y | %H:%M:%S WIB")
        st.sidebar.success("✅ Berhasil diperbarui!")

# Trigger muat data awal otomatis jika memori kosong
if len(st.session_state.raw_stocks) == 0 and daftar_saham:
    with st.spinner("⏳ Memuat data bursa awal..."):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
        st.session_state.last_update = datetime.now().strftime("%d %B %Y | %H:%M:%S WIB")

# TAMPILAN DASHBOARD CORE UTAMA
if st.session_state.raw_stocks:
    df_base = pd.DataFrame(st.session_state.raw_stocks)
    df_base["BANDARMOLOGI"] = "NEUTRAL"
    
    # STEP 1: INTERAKTIF INPUT BANDARMOLOGI
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
    
    # STEP 2: DASHBOARD KEPUTUSAN AI & GRAFIK KEKUATAN EMITEN
    st.subheader("📊 STEP 2: Dashboard Hasil Rekomendasi Akhir AI Pro")
    
    hasil_rekomendasi = []
    raw_scores_for_chart = {}
    
    for idx, row in df_edited.iterrows():
        ticker = row["TICKER"]
        raw_info = next(item for item in st.session_state.raw_stocks if item["TICKER"] == ticker)
        
        # Algoritma Scoring AI Komprehensif
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
        raw_scores_for_chart[ticker] = skor
        
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
    
    # PANEL METRIK RINGKASAN
    t_buy = sum('🟢' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_hold = sum('🟡' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_sell = sum('🔴' in x for x in df_final['KEPUTUSAN AKHIR'])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("🟢 REKOMENDASI BUY", f"{t_buy} Emiten", help="Skor AI >= 70")
    m_col2.metric("🟡 REKOMENDASI HOLD", f"{t_hold} Emiten", help="Skor AI 45 - 69")
    m_col3.metric("🔴 REKOMENDASI SELL", f"{t_sell} Emiten", help="Skor AI < 45")
    
    st.write(" ")
    
    # 📌 UPDATE: Grafik Kekuatan Emiten sekarang bisa di-minimize!
    with st.expander("📈 Lihat Grafik Kekuatan Emiten (Top Skor AI)", expanded=False):
        df_chart = pd.DataFrame(list(raw_scores_for_chart.items()), columns=['TICKER', 'SKOR AI']).sort_values(by='SKOR AI', ascending=False)
        st.bar_chart(df_chart.set_index('TICKER'), color="#00af50", height=280)
    
    # TABEL UTAMA DENGAN SENSOR WARNA INDONESIA
    st.write("### 📋 Detail Tabel Analisis Fundamental & Teknikal")
    def sensor_warna_otomatis(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for idx, row in df.iterrows():
            try:
                per = float(row['PER (x)'])
                if per < 15.0: styles.at[idx, 'PER (x)'] = 'color: #00af50; font-weight: bold;'
                elif per > 25.0: styles.at[idx, 'PER (x)'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            try:
                pbv = float(row['PBV (x)'])
                if pbv < 2.0: styles.at[idx, 'PBV (x)'] = 'color: #00af50; font-weight: bold;'
                elif pbv > 4.0: styles.at[idx, 'PBV (x)'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            try:
                div = float(row['DIV YIELD'].replace('%', ''))
                if div > 3.0: styles.at[idx, 'DIV YIELD'] = 'color: #00af50; font-weight: bold;'
                elif div == 0.0: styles.at[idx, 'DIV YIELD'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            try:
                rsi = float(row['RSI'])
                if rsi <= 30.0: styles.at[idx, 'RSI'] = 'color: #00af50; font-weight: bold;'
                elif rsi >= 70.0: styles.at[idx, 'RSI'] = 'color: #ff0000; font-weight: bold;'
            except: pass
            
            kep = row['KEPUTUSAN AKHIR']
            if '🟢' in kep: styles.iloc[idx, -2:] = 'color: #00af50; font-weight: bold;'
            elif '🟡' in kep: styles.iloc[idx, -2:] = 'color: #ffc000; font-weight: bold;'
            elif '🔴' in kep: styles.iloc[idx, -2:] = 'color: #ff0000; font-weight: bold;'
        return styles

    st.dataframe(df_final.style.apply(sensor_warna_otomatis, axis=None), use_container_width=True, hide_index=True, height=450)
    
    st.markdown("---")
    
    # 📌 UPDATE: STEP 3 - Tampilan Laporan Keuangan Simple ala Aplikasi Saham
    st.subheader("📑 STEP 3: Analisis Ringkas Laporan Keuangan & Dividen")
    st.markdown("*Pilih emiten untuk melihat ringkasan performa finansial dan riwayat dividen yang disederhanakan.*")
    
    pilihan_emiten = st.selectbox("🎯 Pilih Kode Emiten untuk Cek Financials:", options=df_final["TICKER"].tolist())
    
    if pilihan_emiten:
        with st.spinner(f"⏳ Menarik data finansial ringkas untuk {pilihan_emiten}..."):
            tahunan, info_tambahan = fetch_simple_financials(pilihan_emiten)
            
        if info_tambahan:
            st.write(f"#### 🏦 Ringkasan Kinerja Tahunan: **{pilihan_emiten}**")
            
            # 1. TABEL PENDAPATAN & LABA YANG DISIMPLIFIKASI (Kolom = Tahun)
            if tahunan is not None and not tahunan.empty:
                df_display = pd.DataFrame()
                
                # Ekstrak metrik penting saja
                if "Net Income" in tahunan.index:
                    df_display["Net Income"] = tahunan.loc["Net Income"]
                if "Total Revenue" in tahunan.index:
                    df_display["Total Revenue"] = tahunan.loc["Total Revenue"]
                if "Basic EPS" in tahunan.index:
                    df_display["EPS (Earning Per Share)"] = tahunan.loc["Basic EPS"]
                elif "Diluted EPS" in tahunan.index:
                    df_display["EPS (Earning Per Share)"] = tahunan.loc["Diluted EPS"]
                    
                if not df_display.empty:
                    # Ubah index jadi tahun (YYYY)
                    df_display.index = [str(idx)[:4] for idx in df_display.index]
                    df_display = df_display.T # Transpose agar Tahun jadi Kolom di atas (persis seperti foto)
                    
                    def format_duit(val):
                        if pd.isna(val) or val == 0: return "-"
                        if abs(val) >= 1e12: return f"Rp {val/1e12:,.2f} Triliun".replace(",", "*").replace(".", ",").replace("*", ".")
                        if abs(val) >= 1e9: return f"Rp {val/1e9:,.2f} Miliar".replace(",", "*").replace(".", ",").replace("*", ".")
                        return f"Rp {val:,.2f}".replace(",", "*").replace(".", ",").replace("*", ".")
                    
                    for row in df_display.index:
                        if "EPS" in row:
                            df_display.loc[row] = df_display.loc[row].apply(lambda x: f"Rp {x:,.2f}".replace(",", "*").replace(".", ",").replace("*", ".") if pd.notnull(x) else "-")
                        else:
                            df_display.loc[row] = df_display.loc[row].apply(format_duit)
                    
                    st.dataframe(df_display, use_container_width=True)
            else:
                st.info("Data laporan tahunan terperinci belum di-update oleh bursa.")
                
            st.markdown("---")
            
            # 2. PANEL METRIK DIVIDEN (Persis seperti bagian bawah di foto)
            st.write(f"#### 💸 Metrik Dividen & Rasio Payout")
            
            div_yield = info_tambahan.get('dividendYield', 0)
            payout_ratio = info_tambahan.get('payoutRatio', 0)
            div_rate = info_tambahan.get('dividendRate', 0)
            
            div_yield_fmt = f"{div_yield * 100:.2f}%".replace(".", ",") if div_yield else "-"
            payout_ratio_fmt = f"{payout_ratio * 100:.2f}%".replace(".", ",") if payout_ratio else "-"
            div_rate_fmt = f"Rp {div_rate:,.2f}".replace(",", "*").replace(".", ",").replace("*", ".") if div_rate else "-"
            
            d_col1, d_col2, d_col3 = st.columns(3)
            d_col1.metric("📈 Dividend Yield", div_yield_fmt)
            d_col2.metric("📊 Payout Ratio", payout_ratio_fmt)
            d_col3.metric("💵 Dividend Rate (Tahunan)", div_rate_fmt)
            
        else:
            st.warning(f"⚠️ Data finansial untuk {pilihan_emiten} sementara tidak dapat ditarik. Coba lagi nanti.")

else:
    st.info("💡 Masukkan kode emiten di kolom sebelah kiri, lalu klik 'TARIK DATA MARKET' untuk memulai sistem.")