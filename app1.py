import streamlit as st
import yfinance as yf
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz # Saat dilimi için

# Sayfa Ayarları
st.set_page_config(page_title="Portföy & Borsa Takip", layout="wide", page_icon="📈")

# Türkiye Saat Dilimi Ayarı
def guncel_saat_getir():
    tr_tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(tr_tz).strftime("%H:%M:%S")

# TL Formatlama Fonksiyonu
def format_tl(deger):
    return f"{deger:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

# Veriyi GitHub'daki dosyadan OKUMA
def veri_yukle():
    if os.path.exists("portfoyum.json"):
        with open("portfoyum.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- ARAYÜZ BAŞLANGICI ---
col_baslik, col_saat = st.columns([3, 1])

with col_baslik:
    st.title("📊 Portföy İzleme Paneli")
    st.caption("Veriler GitHub 'portfoyum.json' dosyasından okunmaktadır.")

with col_saat:
    # Büyük ve şık bir saat kutusu
    st.markdown(f"""
        <div style="background-color: #1e293b; color: #38bdf8; padding: 10px; 
        border-radius: 10px; text-align: center; font-size: 30px; font-weight: bold;
        border: 2px solid #38bdf8; margin-top: 10px;">
            🕒 {guncel_saat_getir()}
        </div>
    """, unsafe_allow_none=True)

portfoy = veri_yukle()

if portfoy:
    hisse_data = []
    toplam_maliyet = 0.0
    toplam_guncel_deger = 0.0

    with st.spinner('Piyasa verileri güncelleniyor...'):
        # BIST 100 Endeksini Çekme
        try:
            bist100 = yf.Ticker("XU100.IS")
            bist_hist = bist100.history(period="2d")
            bist_fiyat = bist_hist['Close'].iloc[-1]
            bist_onceki = bist_hist['Close'].iloc[-2]
            bist_degisim = ((bist_fiyat - bist_onceki) / bist_onceki) * 100
        except:
            bist_fiyat, bist_degisim = 0.0, 0.0

        # Portföydeki Hisseleri Çekme
        for h, info in portfoy.items():
            try:
                ticker = yf.Ticker(f"{h}.IS")
                data = ticker.history(period="1d")
                if data.empty: continue
                
                guncel_fiyat = data['Close'].iloc[-1]
                adet = float(info['adet'])
                alis_fiyati = float(info['alis'])
                
                maliyet = alis_fiyati * adet
                guncel_tutar = guncel_fiyat * adet
                kar_zarar = guncel_tutar - maliyet
                yuzde = ((guncel_fiyat - alis_fiyati) / alis_fiyati * 100) if alis_fiyati > 0 else 0
                
                toplam_maliyet += maliyet
                toplam_guncel_deger += guncel_tutar
                
                hisse_data.append({
                    "HİSSE": h,
                    "ADET": adet,
                    "ALIŞ": alis_fiyati,
                    "GÜNCEL": guncel_fiyat,
                    "TUTAR": guncel_tutar,
                    "K/Z (TL)": kar_zarar,
                    "YÜZDE (%)": yuzde
                })
            except: continue

    if hisse_data:
        df = pd.DataFrame(hisse_data)
        toplam_kz = toplam_guncel_deger - toplam_maliyet
        kz_yuzde = (toplam_kz / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
        
        # Özet Kartları
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Portföy", format_tl(toplam_guncel_deger))
        c2.metric("Net Kâr/Zarar", format_tl(toplam_kz), delta=f"{kz_yuzde:.2f}%")
        c3.metric("Hisse Sayısı", len(hisse_data))
        
        if bist_fiyat > 0:
            c4.metric("BIST 100", f"{bist_fiyat:,.2f}", delta=f"{bist_degisim:.2f}%")
        else:
            c4.metric("BIST 100", "Veri Alınamadı")

        st.divider()

        # Görsel Analiz
        col_past, col_tablo = st.columns([1, 2])
        
        with col_past:
            st.subheader("🎯 Dağılım")
            fig = px.pie(df, values='TUTAR', names='HİSSE', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)

        with col_tablo:
            st.subheader("📋 Hisse Detayları")
            
            def renk_ayari(val):
                color = '#27ae60' if val > 0 else '#c0392b' if val < 0 else '#7f8c8d'
                return f'color: {color}; font-weight: bold'

            df_styled = df.sort_values(by="TUTAR", ascending=False).style\
                .map(renk_ayari, subset=['K/Z (TL)', 'YÜZDE (%)'])\
                .format({
                    'ADET': '{:,.0f}', 'ALIŞ': '{:,.2f}', 'GÜNCEL': '{:,.2f}',
                    'TUTAR': '{:,.2f}', 'K/Z (TL)': '{:,.2f}', 'YÜZDE (%)': '%{:.2f}'
                })
            
            st.dataframe(df_styled, use_container_width=True, hide_index=True)
            
            if st.button("🔄 Verileri ve Saati Güncelle"):
                st.rerun()
else:
    st.warning("Henüz portföyünüzde hisse yok veya 'portfoyum.json' dosyası okunamadı.")
