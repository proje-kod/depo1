import streamlit as st
import yfinance as yf
import json
import os
import pandas as pd
import plotly.express as px
import time

# Sayfa Ayarları
st.set_page_config(page_title="Borsa İzleme Paneli", layout="wide", page_icon="📈")

# Veri Yükleme (GitHub'daki JSON)
def veri_yukle():
    if os.path.exists("portfoyum.json"):
        with open("portfoyum.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Piyasadan Veri Çekme Fonksiyonu
def piyasa_verilerini_getir(portfoy_dict):
    h_data = []
    t_maliyet = 0.0
    t_guncel = 0.0
    
    # BIST 100 Endeksi
    try:
        bist = yf.Ticker("XU100.IS").history(period="2d")
        b_fiyat = bist['Close'].iloc[-1]
        b_onceki = bist['Close'].iloc[-2]
        b_degisim = ((b_fiyat - b_onceki) / b_onceki) * 100
    except:
        b_fiyat, b_degisim = 0.0, 0.0

    # Portföydeki Hisseler
    for h, info in portfoy_dict.items():
        try:
            ticker = yf.Ticker(f"{h}.IS").history(period="1d")
            if ticker.empty: continue
            fiyat = ticker['Close'].iloc[-1]
            adet = float(info['adet'])
            alis = float(info['alis'])
            
            maliyet = alis * adet
            tutar = fiyat * adet
            t_maliyet += maliyet
            t_guncel += tutar
            
            h_data.append({
                "HİSSE": h, "ADET": adet, "ALIŞ": alis, "GÜNCEL": fiyat,
                "TUTAR": tutar, "K/Z (TL)": tutar - maliyet,
                "YÜZDE (%)": ((fiyat - alis) / alis * 100) if alis > 0 else 0
            })
        except: continue
    
    return h_data, t_maliyet, t_guncel, b_fiyat, b_degisim

# --- ANA EKRAN ---
st.title("📈 Portföy Analizi")
st.caption("Veriler 5 dakikada bir otomatik olarak güncellenir.")

# Verileri Çek
portfoy = veri_yukle()
hisse_data, toplam_maliyet, toplam_guncel_deger, bist_fiyat, bist_degisim = piyasa_verilerini_getir(portfoy)

if hisse_data:
    df = pd.DataFrame(hisse_data)
    toplam_kz = toplam_guncel_deger - toplam_maliyet
    kz_yuzde = (toplam_kz / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
    
    # Üst Özet Kartları
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Değer", f"{toplam_guncel_deger:,.2f} TL")
    c2.metric("Net Kâr/Zarar", f"{toplam_kz:,.2f} TL", delta=f"{kz_yuzde:.2f}%")
    c3.metric("Hisse Sayısı", len(hisse_data))
    c4.metric("BIST 100", f"{bist_fiyat:,.2f}", delta=f"{bist_degisim:.2f}%")

    st.divider()

    # Grafik ve Tablo Bölümü
    col_past, col_tablo = st.columns([1, 2])
    
    with col_past:
        fig = px.pie(df, values='TUTAR', names='HİSSE', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with col_tablo:
        def renk_format(val):
            return f'color: {"#27ae60" if val > 0 else "#c0392b"}; font-weight: bold'

        df_styled = df.sort_values(by="TUTAR", ascending=False).style\
            .map(renk_format, subset=['K/Z (TL)', 'YÜZDE (%)'])\
            .format({'ADET': '{:,.0f}', 'ALIŞ': '{:,.2f}', 'GÜNCEL': '{:,.2f}',
                     'TUTAR': '{:,.2f}', 'K/Z (TL)': '{:,.2f}', 'YÜZDE (%)': '%{:.2f}'})
        st.dataframe(df_styled, use_container_width=True, hide_index=True)

# --- 5 DAKİKALIK UYKU MODU ---
# Bisikleti durduran en kritik kısım:
time.sleep(300) # 300 saniye (5 dakika) boyunca hiçbir şey yapmadan bekle
st.rerun()      # 5 dakika dolunca sayfayı yenile
