import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

# 1. KONFIGURASI HALAMAN UTAMA
st.set_page_config(page_title="Scanner Saham", page_icon="📊", layout="wide")

# LOGO DAN JUDUL BARU APLIKASI
st.title("📊 Scanner Saham")
st.write("Sistem Analisis Multi-Pilar: Teknikal (40%), Fundamental (40%), dan Sentimen Pasar (20%)")
st.markdown("---")

# 2. SIDEBAR - INPUT USER & DATA MAKRO
st.sidebar.header("⚙️ 1. Daftar Saham")
saham_input = st.sidebar.text_area(
    "Masukkan kode emiten (pisahkan dengan koma):", 
    "BBCA, BBRI, TLKM, ASII, BREN, AMMN, UNVR"
)
daftar_saham = [s.strip().upper() + ".JK" for s in saham_input.split(",") if s.strip()]

st.sidebar.markdown("---")
st.sidebar.header("🌍 2. Sentimen Pasar & Bandar")
bi_rate = st.sidebar.number_input("Suku Bunga BI (%)", value=6.25, step=0.25)
bandarmologi = st.sidebar.selectbox(
    "Status Bandarmologi / Asing:", 
    ["Akumulasi (Net Buy)", "Netral", "Distribusi (Net Sell)"]
)

# Informasi Aturan Pembobotan di Sidebar agar Transparan
with st.sidebar.expander("ℹ️ Lihat Aturan Pembobotan AI"):
    st.markdown("""
    **Teknikal (Max 40 Pts):**
    * Di atas EMA20: +20 Pts
    * MACD Bullish: +10 Pts
    * RSI Aman (<60): +10 Pts
    
    **Fundamental (Max 40 Pts):**
    * PER<15 & PBV<2: +20 Pts
    * ROE > 10%: +20 Pts
    
    **Sentimen (Max 20 Pts):**
    * Akumulasi Bandar: +20 Pts
    * Netral: +10 Pts
    """)

mulai_scan = st.sidebar.button("🚀 JALANKAN SCANNER")

# 3. FUNGSI TEKNIKAL (MACD)
def hitung_macd(df):
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# 4. PROSES LOGIKA UTAMA SCANNER SAHAM
if mulai_scan:
    st.subheader("⚙️ Sedang Menghitung Bobot Nilai Emiten...")
    progress_bar = st.progress(0)
    
    hasil_final = []
    hasil_teknikal = []
    hasil_fundamental = []
    
    total_emiten = len(daftar_saham)
    
    for idx, saham in enumerate(daftar_saham):
        try:
            progress_bar.progress((idx + 1) / total_emiten)
            kode_saham = saham.replace(".JK", "")
            
            # --- A. AMBIL & HITUNG DATA TEKNIKAL ---
            df = yf.download(saham, period="6mo", progress=False)
            if df.empty:
                continue
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            df['MACD'], df['Signal'] = hitung_macd(df)
            
            harga_skg = float(df['Close'].iloc[-1])
            vol_skg = float(df['Volume'].iloc[-1])
            rsi_skg = float(df['RSI'].iloc[-1])
            macd_skg = float(df['MACD'].iloc[-1])
            sig_skg = float(df['Signal'].iloc[-1])
            ema20_skg = float(df['EMA20'].iloc[-1])
            
            # --- B. AMBIL DATA FUNDAMENTAL ---
            ticker = yf.Ticker(saham)
            info = ticker.info
            
            per = info.get('trailingPE', 0)
            pbv = info.get('priceToBook', 0)
            roe = info.get('returnOnEquity', 0)
            der = info.get('debtToEquity', 0)
            div_yield = info.get('dividendYield', 0)
            
            if roe is not None: roe = roe * 100
            if div_yield is not None: div_yield = div_yield * 100

            # --- C. PROSES PEMBOBOTAN TRANSFARAN (TOTAL MAKSIMAL: 100 POIN) ---
            skor_teknikal = 0
            skor_fundamental = 0
            skor_sentimen = 0
            catatan_katalis = []
            
            # 1. Hitung Nilai Teknikal (Max 40 Poin)
            if harga_skg > ema20_skg:
                skor_teknikal += 20
                catatan_katalis.append("Harga Uptrend")
            if macd_skg > sig_skg:
                skor_teknikal += 10
                catatan_katalis.append("Momentum Bullish")
            if rsi_skg < 60:
                skor_teknikal += 10
                catatan_katalis.append("RSI Wajar/Aman")
                
            # 2. Hitung Nilai Fundamental (Max 40 Poin)
            if per != 0 and per < 15 and pbv != 0 and pbv < 2:
                skor_fundamental += 20
                catatan_katalis.append("Valuasi Murah")
            if roe != 0 and roe > 10:
                skor_fundamental += 20
                catatan_katalis.append("Profitabilitas Bagus")
                
            # 3. Hitung Nilai Sentimen (Max 20 Poin)
            if bandarmologi == "Akumulasi (Net Buy)":
                skor_sentimen += 20
                catatan_katalis.append("Diakumulasi Bandar")
            elif bandarmologi == "Netral":
                skor_sentimen += 10
            
            # Total Skor Akhir
            total_skor = skor_teknikal + skor_fundamental + skor_sentimen
            
            # Menentukan Keputusan Aksi Berdasarkan Nilai Batas Pembobotan
            if total_skor >= 70:
                aksi = "🟩 BUY"
            elif total_skor >= 40:
                aksi = "🟨 WATCHLIST"
            else:
                aksi = "🟥 AVOID / SELL"
                
            # Masukkan ke list penampung tabel
            hasil_final.append({
                "Saham": kode_saham,
                "Rekomendasi Aksi": aksi,
                "Total Skor AI (Max 100)": total_skor,
                "Bobot Teknikal (40)": skor_teknikal,
                "Bobot Fundamental (40)": skor_fundamental,
                "Bobot Sentimen (20)": skor_sentimen,
                "Katalis Positif": ", ".join(catatan_katalis) if catatan_katalis else "Minim Katalis"
            })
            
            hasil_teknikal.append({
                "Saham": kode_saham, "Harga Skg": round(harga_skg), "Volume": vol_skg,
                "RSI (14)": round(rsi_skg, 1), "MACD": round(macd_skg, 2), "Tren (vs EMA20)": "Di Atas EMA20" if harga_skg > ema20_skg else "Di Bawah EMA20"
            })
            
            hasil_fundamental.append({
                "Saham": kode_saham, "PER (x)": round(per, 1) if per else "N/A", "PBV (x)": round(pbv, 1) if pbv else "N/A",
                "ROE (%)": round(roe, 1) if roe else "N/A", "DER (%)": round(der, 1) if der else "N/A", "Div Yield (%)": round(div_yield, 1) if div_yield else "0.0"
            })
            
        except Exception as e:
            st.sidebar.error(f"Gagal memproses emiten {saham}: {e}")

    # 5. BERHASIL DI-SCAN - TAMPILKAN HASIL MULTI-TAB KE LAYAR WEB
    if hasil_final:
        st.success("✅ Analisis Pembobotan Berhasil Diselesaikan!")
        
        # Membuat Layout Tab yang Sangat Rapi
        tab1, tab2, tab3 = st.tabs(["🎯 RINGKASAN BOBOT & AKSI", "📊 METRIK TEKNIKAL", "🏢 RASIO FUNDAMENTAL"])
        
        with tab1:
            st.markdown("### Hasil Skor Komprehensif (Skor Kenaikan Saham)")
            df_final = pd.DataFrame(hasil_final)
            # Urutkan berdasarkan skor tertinggi agar saham terbaik muncul paling atas
            df_final = df_final.sort_values(by="Total Skor AI (Max 100)", ascending=False)
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            
        with tab2:
            st.markdown("### Data Riwayat Harga & Indikator Tren")
            df_tech = pd.DataFrame(hasil_teknikal)
            st.dataframe(df_tech, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📈 Visualisasi Grafik Pergerakan")
            pilih_saham = st.selectbox("Pilih kode saham untuk memunculkan chart:", df_tech['Saham'].tolist())
            if pilih_saham:
                df_chart = yf.download(pilih_saham + ".JK", period="6mo", progress=False)
                df_chart.columns = [col[0] if isinstance(col, tuple) else col for col in df_chart.columns]
                df_chart['EMA20'] = df_chart['Close'].ewm(span=20, adjust=False).mean()
                st.line_chart(df_chart[['Close', 'EMA20']])
                st.write("Volume Transaksi Harian:")
                st.bar_chart(df_chart['Volume'])
                
        with tab3:
            st.markdown("### Laporan Kesehatan & Valuasi Saham")
            st.info("💡 Rasio keuangan ditarik langsung dari sistem Yahoo Finance global.")
            df_fund = pd.DataFrame(hasil_fundamental)
            st.dataframe(df_fund, use_container_width=True, hide_index=True)
            
    else:
        st.error("Gagal mendapatkan data, pastikan kode emiten benar.")
else:
    # Tampilan Selamat Datang Saat Pertama Kali Dibuka
    st.info("👈 Masukkan kode emiten di menu sebelah kiri, lalu klik **JALANKAN SCANNER** untuk memulai perhitungan pembobotan.")
