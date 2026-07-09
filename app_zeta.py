import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="AI Stock Dashboard Interactive", page_icon="📈", layout="wide")

st.title("📈 AI AUTOMATED STOCK SCANNER DASHBOARD (INTERACTIVE)")
st.markdown("*Fitur Baru: Dropdown Bandarmologi Per Saham + Perbaikan Akurasi Data Fundamental*")
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
            
            # Ambil Data Fundamental & Perbaikan Bug Satuan Yahoo Finance
            ticker = yf.Ticker(emiten)
            info = ticker.info
            
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            
            # Proteksi jika PBV ngawur/minus dari Yahoo Finance
            if pbv and (pbv > 50 or pbv < 0): 
                pbv = 1.0 # default aman jika data rusak
                
            div_yield = info.get('dividendYield', 0)
            if div_yield:
                # Koreksi Bug Perkalian Ratusan Persen
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
    with st.spinner("⏳ Mengunduh data 20 saham dari Yahoo Finance..."):
        st.session_state.raw_stocks = fetch_raw_data(daftar_saham)

if st.session_state.raw_stocks:
    # Buat DataFrame Awal untuk diedit User
    df_base = pd.DataFrame(st.session_state.raw_stocks)
    
    # Tambahkan Kolom Bandarmologi Default jika belum ada di memori
    df_base["BANDARMOLOGI"] = "NEUTRAL"
    
    st.subheader("📥 STEP 1: Isi Analisis Bandarmologi Anda di Sini")
    st.markdown("👇 *Klik pada kolom **BANDARMOLOGI** di bawah untuk mengubah status tiap saham secara manual.*")
    
    # TABEL INTERAKTIF UNTUK DROPDOWN
    df_edited = st.data_editor(
        df_base[["TICKER", "HARGA", "PER", "PBV", "DIV_YIELD", "RSI", "BANDARMOLOGI"]],
        column_config={
            "BANDARMOLOGI": st.column_config.SelectboxColumn(
                "BANDARMOLOGI (Pilihan)",
                help="Tentukan kondisi akumulasi/distribusi asing saat ini",
                options=["AKUMULASI", "NEUTRAL", "DISTRIBUSI"],
                required=True,
            ),
            # Kunci kolom lain agar tidak bisa diedit sembarangan
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
    
    # 5. PROSES KALKULASI OTOMATIS OLEH PYTHON (REAL-TIME)
    st.markdown("---")
    st.subheader("📊 STEP 2: Dashboard Hasil Rekomendasi Akhir AI Pro")
    
    hasil_rekomendasi = []
    
    # Gabungkan data teknikal tersembunyi dengan pilihan bandarmologi user
    for idx, row in df_edited.iterrows():
        ticker = row["TICKER"]
        raw_info = next(item for item in st.session_state.raw_stocks if item["TICKER"] == ticker)
        
        # Logika Pembobotan AI Skor (Maksimal 100)
        skor = 0
        if raw_info["UP_EMA20"]: skor += 15
        if raw_info["MACD_GOLDEN"]: skor += 15
        if 30 <= row["RSI"] <= 70: skor += 10 # RSI Sehat
        
        if row["PER"] != 0 and row["PER"] < 15: skor += 15
        if row["PBV"] != 0 and row["PBV"] < 2: skor += 15
        if row["DIV_YIELD"] > 3: skor += 10
            
        # Bobot Pengaruh Tombol Dropdown Pilihan Anda
        if row["BANDARMOLOGI"] == "AKUMULASI": skor += 20
        elif row["BANDARMOLOGI"] == "DISTRIBUSI": skor -= 10
        else: skor += 5 # Neutral
        
        # Batasi skor antara 0 - 100
        skor = max(0, min(100, skor))
        
        # Penentuan Keputusan Akhir & Sinyal AI
        if skor >= 70:
            keputusan = "🟩 CICIL BELI"
            sinyal = "BUY / ACCUMULATE"
        elif skor >= 45:
            keputusan = "🟨 HOLD / WATCHING"
            sinyal = "NEUTRAL"
        else:
            keputusan = "🟥 STRONG SELL"
            sinyal = "TAKE PROFIT / SELL"
            
        hasil_rekomendasi.append({
            "TICKER": row["TICKER"],
            "HARGA TERAKHIR": f"Rp {int(row['HARGA']):,}".replace(",", "."),
            "PER (x)": row["PER"] if row["PER"] > 0 else "-",
            "PBV (x)": row["PBV"] if row["PBV"] > 0 else "-",
            "DIV YIELD": f"{row['DIV_YIELD']}%",
            "RSI": row["RSI"],
            "BANDARMOLOGI": row["BANDARMOLOGI"],
            "SKOR AI": skor,
            "SINYAL TEKNIKAL": sinyal,
            "KEPUTUSAN AKHIR": keputusan
        })
        
    df_final = pd.DataFrame(hasil_rekomendasi)
    
    # FUNGSI STYLING WARNA SEPERTI EXCEL
    def styling_excel(val):
        val_str = str(val)
        if 'CICIL BELI' in val_str or 'BUY' in val_str:
            return 'background-color: #c6efce; color: #006100; font-weight: bold;'
        elif 'HOLD' in val_str or 'NEUTRAL' in val_str:
            return 'background-color: #ffeb9c; color: #9c5700; font-weight: bold;'
        elif 'STRONG SELL' in val_str or 'TAKE PROFIT' in val_str:
            return 'background-color: #ffc7ce; color: #9c0006; font-weight: bold;'
        return ''

    df_styled = df_final.style.map(styling_excel, subset=['KEPUTUSAN AKHIR', 'SINYAL TEKNIKAL'])
    
    # Tampilkan Tabel Hasil Akhir yang Sudah Diwarnai
    st.dataframe(df_styled, use_container_width=True, hide_index=True, height=550)
    st.caption("💡 *Tips: Jika ingin menyegarkan harga saham terbaru dari bursa, silakan klik tombol **TARIK DATA MARKET** di sidebar kiri.*")
else:
    st.info("Silakan klik tombol di sidebar kiri untuk memuat data saham.")
