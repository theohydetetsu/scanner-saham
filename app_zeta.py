import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time

# 1. KONFIGURASI HALAMAN (WIDE LAYOUT)
st.set_page_config(page_title="AI Stock Dashboard Pro", page_icon="📈", layout="wide")

st.title("📈 AI AUTOMATED STOCK SCANNER DASHBOARD")
st.markdown("*Sistem Analisis Multi-Pilar Terintegrasi: Teknikal, Fundamental & Sentimen*")
st.markdown("---")

# 2. DEFAULT 20 SAHAM BLUECHIP INDONESIA
default_bluechips = "BBCA, BBRI, BMRI, BBNI, TLKM, ASII, UNTR, ICBP, INDF, AMRT, GOTO, PGAS, PTBA, ITMG, KLBF, ADRO, UNVR, BRIS, CPIN, ANTM"

st.sidebar.header("⚙️ 1. Pengaturan Saham")
saham_input = st.sidebar.text_area("Daftar Emiten (Pisahkan dengan koma):", default_bluechips, height=150)
daftar_saham = [s.strip().upper() + ".JK" for s in saham_input.split(",") if s.strip()]

st.sidebar.markdown("---")
st.sidebar.header("🌍 2. Sentimen Makro")
bandarmologi = st.sidebar.selectbox(
    "Kondisi Asing/Bandar Secara Umum:", 
    ["AKUMULASI", "NEUTRAL", "DISTRIBUSI"]
)

mulai_scan = st.sidebar.button("🚀 JALANKAN DASHBOARD PRO", use_container_width=True)

# 3. FUNGSI TEKNIKAL & CACHING (ANTI-BLOKIR YAHOO FINANCE)
def hitung_macd(df):
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# Fitur Cache: Mengingat data selama 1 jam agar tidak kena Limit "Too Many Requests"
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data_saham(saham_list, status_bandar):
    hasil = []
    for emiten in saham_list:
        try:
            kode = emiten.replace(".JK", "")
            
            # Ambil Data Harga
            df = yf.download(emiten, period="6mo", progress=False)
            if df.empty:
                continue
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            # Indikator Teknikal
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['MACD'], df['Signal'] = hitung_macd(df)
            
            harga_skg = float(df['Close'].iloc[-1])
            macd_skg = float(df['MACD'].iloc[-1])
            sig_skg = float(df['Signal'].iloc[-1])
            ema20_skg = float(df['EMA20'].iloc[-1])
            
            # Ambil Data Fundamental
            ticker = yf.Ticker(emiten)
            info = ticker.info
            
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            div_yield = info.get('dividendYield', 0)
            if div_yield: div_yield = div_yield * 100
            
            # LOGIKA PEMBOBOTAN AI PRO
            skor = 0
            if harga_skg > ema20_skg: skor += 20
            if macd_skg > sig_skg: skor += 10
            if per != 0 and per < 15: skor += 15
            if pbv != 0 and pbv < 2: skor += 15
            if div_yield and div_yield > 3: skor += 10
            
            if status_bandar == "AKUMULASI": skor += 30
            elif status_bandar == "NEUTRAL": skor += 10
            
            # KEPUTUSAN AKHIR SEPERTI DI EXCEL
            if skor >= 75:
                keputusan = "🟩 CICIL BELI"
                sinyal = "BUY / ACCUMULATE"
            elif skor >= 45:
                keputusan = "🟨 HOLD / WATCHING"
                sinyal = "NEUTRAL"
            else:
                keputusan = "🟥 STRONG SELL"
                sinyal = "TAKE PROFIT / SELL"

            hasil.append({
                "TICKER": kode,
                "HARGA TERAKHIR": f"Rp {int(harga_skg):,}".replace(",", "."),
                "PER (x)": round(per, 2) if per else "-",
                "PBV (x)": round(pbv, 2) if pbv else "-",
                "DIV YIELD (%)": f"{round(div_yield, 2)}%" if div_yield else "0.0%",
                "SKOR AI": skor,
                "SINYAL TEKNIKAL": sinyal,
                "KEPUTUSAN AKHIR": keputusan
            })
            
            time.sleep(0.1) # Jeda aman untuk server
            
        except Exception:
            continue
            
    return hasil

# 4. PROSES & TAMPILAN DASHBOARD
if mulai_scan:
    with st.spinner("⏳ Sedang memindai 20 Saham Bluechip, mohon tunggu..."):
        data_dashboard = fetch_data_saham(daftar_saham, bandarmologi)
    
    if data_dashboard:
        df_dash = pd.DataFrame(data_dashboard)
        
        # PENGATURAN WARNA OTOMATIS (STYLING) SEPERTI EXCEL
        def styling_excel(val):
            val_str = str(val)
            if 'CICIL BELI' in val_str or 'BUY' in val_str:
                return 'background-color: #c6efce; color: #006100; font-weight: bold;'
            elif 'HOLD' in val_str or 'NEUTRAL' in val_str:
                return 'background-color: #ffeb9c; color: #9c5700; font-weight: bold;'
            elif 'STRONG SELL' in val_str or 'TAKE PROFIT' in val_str:
                return 'background-color: #ffc7ce; color: #9c0006; font-weight: bold;'
            return ''

        # Terapkan warna khusus untuk kolom Keputusan dan Sinyal
        df_styled = df_dash.style.map(styling_excel, subset=['KEPUTUSAN AKHIR', 'SINYAL TEKNIKAL'])
        
        st.success(f"✅ Pemindaian selesai! Menampilkan {len(df_dash)} saham.")
        
        # Tampilkan Tabel ala Excel
        st.dataframe(
            df_styled, 
            use_container_width=True, 
            hide_index=True,
            height=600 # Tinggi tabel disesuaikan agar pas di layar
        )
        
        st.caption("💡 *Catatan: Data tersimpan di memori cache selama 1 jam untuk mencegah pemblokiran. Jika ingin data terbaru secara paksa, Anda bisa refresh halaman web ini.*")
    else:
        st.error("Gagal menarik data. Pastikan koneksi internet stabil.")
else:
    st.info("👈 Klik **JALANKAN DASHBOARD PRO** di sebelah kiri untuk melihat rekomendasi ke-20 saham Bluechip.")
