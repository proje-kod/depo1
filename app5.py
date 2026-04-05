import streamlit as st
import yfinance as yf
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import time
# Sayfanın en üstüne ekleyin
from streamlit_autorefresh import st_autorefresh

# Her 60.000 milisaniyede (1 dakika) sayfayı yenile
# Bu komut 'time.sleep' ve 'st.rerun' yerine geçer.
# Bisiklet sadece bu 60 saniye dolduğunda 1 kez görünür ve kaybolur.
st_autorefresh(interval=60000, key="datarefresh")
# Sayfa Ayarları
st.set_page_config(page_title="Borsa Takip Paneli", layout="wide", page_icon="📈")

# Türkiye Saat Dilimi (Saniyesiz Format: SS:DD)
def guncel_saat_getir():
    tr_tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(tr_tz).strftime("%H:%M")

# TL Formatlama
def format_tl(deger):
    return f"{deger:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

# GitHub'daki JSON dosyasını OKU
def veri_yukle():
    if os.path.exists("deneme2.json"):
        with open("deneme2.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- PİYASA VERİLERİ (5 DAKİKADA BİR GÜNCELLENİR) ---
@st.cache_data(ttl=300)
def piyasa_verilerini_getir(portfoy_dict):
    h_data = []
    t_maliyet = 0.0
    t_guncel = 0.0
    
    # BIST 100
    try:
        bist = yf.Ticker("XU100.IS").history(period="2d")
        b_fiyat = bist['Close'].iloc[-1]
        b_onceki = bist['Close'].iloc[-2]
        b_degisim = ((b_fiyat - b_onceki) / b_onceki) * 100
    except:
        b_fiyat, b_degisim = 0.0, 0.0

    # Portföy Hisseleri
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

# --- ARAYÜZ OLUŞTURMA ---
col_baslik, col_saat = st.columns([3, 1])

with col_baslik:
    st.title("📊 Portföy Analiz Merkezi")
    st.caption("🕒 Saat dakikada bir, borsa verileri 5 dakikada bir otomatik güncellenir.")

with col_saat:
    # Şık, saniyesiz saat kutusu
    st.markdown(f"""
        <div style="background-color: #0f172a; color: #fbbf24; padding: 15px; 
        border-radius: 12px; text-align: center; font-size: 36px; font-weight: bold;
        border: 2px solid #fbbf24;">
            {guncel_saat_getir()}
        </div>
    """, unsafe_allow_html=True)

# Verileri İşle
portfoy = veri_yukle()
hisse_data, toplam_maliyet, toplam_guncel_deger, bist_fiyat, bist_degisim = piyasa_verilerini_getir(portfoy)

if hisse_data:
    df = pd.DataFrame(hisse_data)
    toplam_kz = toplam_guncel_deger - toplam_maliyet
    kz_yuzde = (toplam_kz / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
    
    # Üst Bilgi Kartları
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Değer", format_tl(toplam_guncel_deger))
    c2.metric("Toplam K/Z", format_tl(toplam_kz), delta=f"{kz_yuzde:.2f}%")
    c3.metric("Hisse Sayısı", len(hisse_data))
    c4.metric("BIST 100", f"{bist_fiyat:,.2f}", delta=f"{bist_degisim:.2f}%")

    st.divider()

    # Grafik ve Tablo
    col_past, col_tablo = st.columns([1, 2])
    with col_past:
        fig = px.pie(df, values='TUTAR', names='HİSSE', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with col_tablo:
        def renk(val):
            return f'color: {"#27ae60" if val > 0 else "#c0392b"}; font-weight: bold'

        df_sorted = df.sort_values(by="TUTAR", ascending=False).style\
            .map(renk, subset=['K/Z (TL)', 'YÜZDE (%)'])\
            .format({'ADET': '{:,.0f}', 'ALIŞ': '{:,.2f}', 'GÜNCEL': '{:,.2f}',
                     'TUTAR': '{:,.2f}', 'K/Z (TL)': '{:,.2f}', 'YÜZDE (%)': '%{:.2f}'})
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)

# --- DAKİKALIK DÖNGÜ ---
time.sleep(60) # 60 saniye boyunca bekle
st.rerun()    # Sayfayı ve saati güncelle
