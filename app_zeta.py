import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN UTAMA
# ==========================================
st.set_page_config(page_title="AI Stock Dashboard Pro Max", page_icon="📈", layout="wide")

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
        df_ihsg = df_ihsg.ffill() # Perbaiki data bolong
        
        harga_skg = float(df_ihsg['Close'].iloc[-1])
        harga_lalu = float(df_ihsg['Close'].iloc[-2])
        perubahan = harga_skg - harga_lalu
        persen = (perubahan / harga_lalu) * 100
        
        return df_ihsg[['Close']], harga_skg, perubahan, persen
    except Exception:
        return None, None, None, None

def fetch_advanced_financials(ticker_code):
    try:
        ticker = yf.Ticker(ticker_code + ".JK")
        return ticker.financials, ticker.quarterly_financials, ticker.info
    except Exception:
        return None, None, None

# TAMPILAN HEADER UTAMA
st.title("📈 AI AUTOMATED STOCK SCANNER DASHBOARD")

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

if df_ihsg_hist is not None:
    with st.expander("📊 Lihat Grafik Pergerakan Tren IHSG (1 Bulan Terakhir)", expanded=False):
        st.line_chart(df_ihsg_hist, color="#00ffcc", height=200)

st.markdown("---")

# ==========================================
# 2. CYBER PANEL KENDALI
# ==========================================
default_stocks = "BBCA, BBRI, BMRI, BBNI, TLKM, ASII, UNTR, ICBP, INDF, AMRT, GOTO, PGAS, PTBA, ITMG, KLBF, ADRO, UNVR, BRIS, CPIN, ANTM, TPIA, BREN, AMMN, ADMR, MEDC, AKRA, ACES, MYOR, SMGR, INCO"

st.sidebar.title("⚙️ CYBER PANEL KENDALI")
st.sidebar.markdown("Kelola parameter dan integrasi sistem Anda di sini.")

saham_input = st.sidebar.text_area("📝 Daftar Emiten Pantauan (30 Saham):", default_stocks, height=150)
daftar_saham = [s.strip().upper() + ".JK" for s in saham_input.split(",") if s.strip()]

muat_data = st.sidebar.button("🔄 TARIK DATA MARKET", use_container_width=True, type="primary")
st.sidebar.markdown("---")

st.sidebar.subheader("🎛️ Parameter AI Engine")
profil_risiko = st.sidebar.selectbox(
    "🎯 Profil Risiko Trading:",
    ["Moderat (Standar)", "Agresif (High Risk)", "Konservatif (Aman)"],
    help="Menentukan tingkat ketatnya filter AI dalam memberikan sinyal BUY."
)
st.sidebar.markdown("---")

st.sidebar.subheader("📡 Status Sistem")
st.sidebar.info(f"📊 **Total Emiten Dimuat:** {len(daftar_saham)} Saham")
if st.session_state.last_update:
    st.sidebar.success("✅ **Koneksi Bursa:** TERHUBUNG (ONLINE)")
else:
    st.sidebar.warning("⏳ **Koneksi Bursa:** MENUNGGU DATA...")
st.sidebar.markdown("---")

st.sidebar.subheader("🧹 Utilitas")
if st.sidebar.button("🗑️ Bersihkan Cache Memori", use_container_width=True):
    st.cache_data.clear()
    st.session_state.clear()
    st.sidebar.success("Memori berhasil direset! Silakan Tarik Data ulang.")
st.sidebar.caption("AI Pro Scanner v3.1 | System Running Normal")

# ==========================================
# 3. CORE ENGINE (ANTI-CRASH UPDATED)
# ==========================================
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
            df = df.ffill() # Mencegah data kosong (NaN) dari Yahoo Finance
            
            if pd.isna(df['Close'].iloc[-1]): continue # Skip jika benar-benar rusak
            
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
            time.sleep(0.1) # Dipercepat sedikit
        except Exception:
            continue
    return master_data

if muat_data:
    if not daftar_saham:
        st.sidebar.error("⚠️ Daftar emiten tidak boleh kosong!")
    else:
        st.cache_data.clear()
        with st.spinner("⏳ Sedang memperbarui data bursa & menghitung metrik AI..."):
            st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
            st.session_state.last_update = datetime.now().strftime("%d %B %Y | %H:%M:%S WIB")
        st.sidebar.success("✅ Berhasil diperbarui!")

if len(st.session_state.raw_stocks) == 0 and daftar_saham:
    with st.spinner("⏳ Memuat data bursa awal..."):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)
        st.session_state.last_update = datetime.now().strftime("%d %B %Y | %H:%M:%S WIB")

# ==========================================
# 4. HALAMAN UTAMA DASHBOARD
# ==========================================
if st.session_state.raw_stocks:
    df_base = pd.DataFrame(st.session_state.raw_stocks)
    
    with st.expander("📥 STEP 1: Isi Analisis Bandarmologi (Klik untuk Melipat/Membuka)", expanded=True):
        st.write("Silakan pilih status bandarmologi untuk masing-masing emiten. Data akan langsung terintegrasi dengan AI.")
        df_edited = st.data_editor(
            df_base[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI"]].assign(BANDARMOLOGI="NEUTRAL"),
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
    
    skor_buy_target = 70
    if "Agresif" in profil_risiko: skor_buy_target = 60
    elif "Konservatif" in profil_risiko: skor_buy_target = 75
        
    st.caption(f"*Mode Aktif: {profil_risiko} | Batas Minimal Skor Buy >= {skor_buy_target}*")
    
    hasil_rekomendasi = []
    raw_scores_for_chart = {}
    
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
        raw_scores_for_chart[ticker] = skor
        
        if skor >= skor_buy_target:
            keputusan = "🟢 CICIL BELI"
            sinyal = "BUY / ACCUMULATE"
        elif skor >= 45:
            keputusan = "🟡 HOLD / WATCHING"
            sinyal = "NEUTRAL"
        else:
            keputusan = "🔴 STRONG SELL"
            sinyal = "TAKE PROFIT / SELL"
            
        # PENGAMAN (ANTI-CRASH) UNTUK ANGKA HARGA
        try:
            harga_final = f"Rp {int(row['HARGA']):,}".replace(",", ".")
        except:
            harga_final = "-"

        per_val = f"{float(row['PER']):.2f}" if row['PER'] and float(row['PER']) > 0 else "-"
        pbv_val = f"{float(row['PBV']):.2f}" if row['PBV'] and float(row['PBV']) > 0 else "-"
        div_val = f"{float(row['DIV_YIELD']):.2f}%"
        rsi_val = f"{float(row['RSI']):.2f}"

        hasil_rekomendasi.append({
            "TICKER": row["TICKER"],
            "HARGA TERAKHIR": harga_final,
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
    
    t_buy = sum('🟢' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_hold = sum('🟡' in x for x in df_final['KEPUTUSAN AKHIR'])
    t_sell = sum('🔴' in x for x in df_final['KEPUTUSAN AKHIR'])
    
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("🟢 REKOMENDASI BUY", f"{t_buy} Emiten")
    m_col2.metric("🟡 REKOMENDASI HOLD", f"{t_hold} Emiten")
    m_col3.metric("🔴 REKOMENDASI SELL", f"{t_sell} Emiten")
    
    st.write(" ")
    
    with st.expander("📈 Lihat Grafik Kekuatan Emiten (Top Skor AI)", expanded=False):
        if raw_scores_for_chart:
            df_chart = pd.DataFrame(list(raw_scores_for_chart.items()), columns=['TICKER', 'SKOR AI']).sort_values(by='SKOR AI', ascending=False)
            st.bar_chart(df_chart.set_index('TICKER'), color="#00af50", height=280)
    
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
    
    # ==========================================
    # 5. STEP 3: ANALISIS KINERJA & RIWAYAT DIVIDEN
    # ==========================================
    st.subheader("📑 STEP 3: Analisis Ringkas Laporan Keuangan & Dividen")
    
    pilihan_emiten = st.selectbox("🎯 Pilih Kode Emiten untuk Cek Financials:", options=df_final["TICKER"].tolist())
    
    if pilihan_emiten:
        with st.spinner(f"⏳ Menarik berkas finansial untuk {pilihan_emiten}..."):
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
                    if is_eps:
                        return f"{val_float:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".")
                    else:
                        return f"{val_float / 1e9:,.2f} B"
                except:
                    return "-"

            st.write(f"### 🏦 Ringkasan Kinerja Performa: **{pilihan_emiten}**")
            
            pilihan_metrik = st.radio(
                "Pilih Kategori Tampilan:", 
                options=["Net Income", "EPS", "Revenue"], 
                horizontal=True, 
                label_visibility="collapsed"
            )
            
            yahoo_row_name = "Net Income"
            if pilihan_metrik == "EPS": yahoo_row_name = "Basic EPS"
            elif pilihan_metrik == "Revenue": yahoo_row_name = "Total Revenue"
            
            set_tahun = set()
            if tahunan is not None: set_tahun.update([pd.to_datetime(c).year for c in tahunan.columns])
            if kuartalan is not None: set_tahun.update([pd.to_datetime(c).year for c in kuartalan.columns])
            list_tahun = sorted([str(y) for y in set_tahun], reverse=True)[:3]
            if not list_tahun: list_tahun = ["2026", "2025", "2024"]

            df_grid = pd.DataFrame(
                index=["Q1", "Q2", "Q3", "Q4", "Annualised", "TTM"],
                columns=list_tahun
            ).fillna("-")

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

            st.markdown(f"**Period / {pilihan_metrik}**")
            st.dataframe(df_grid, use_container_width=True)
            
            st.write(" ")
            st.markdown("**Dividend Summary**")
            
            div_yield = info_tambahan.get('dividendYield', 0)
            payout_ratio = info_tambahan.get('payoutRatio', 0)
            div_rate = info_tambahan.get('dividendRate', 0)
            
            df_div_bottom = pd.DataFrame({
                "Metrik Dividen": ["Dividend", "Payout Ratio", "Dividend Yield"],
                "Nilai": [
                    f"Rp {div_rate:,.2f}".replace(",", "x").replace(".", ",").replace("x", ".") if div_rate else "-",
                    f"{payout_ratio * 100:.2f}%".replace(".", ",") if payout_ratio else "-",
                    f"{div_yield * 100:.2f}%".replace(".", ",") if div_yield else "-"
                ]
            })
            st.dataframe(df_div_bottom, use_container_width=True, hide_index=True)
            
        else:
            st.warning(f"⚠️ Berkas keuangan {pilihan_emiten} sedang sibuk di sisi bursa. Silakan klik ulang tombol di atas.")

else:
    st.info("💡 Masukkan kode emiten di kolom Cyber Panel (Kiri), lalu klik 'TARIK DATA MARKET' untuk memulai sistem.")
