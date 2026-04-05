import streamlit as st
import yfinance as yf
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import time

# Sayfa Konfigürasyonu
st.set_page_config(page_title="Canlı Portföy & Borsa", layout="wide", page_icon="📈")

# --- OTOMATİK YENİLEME AYARI ---
# Saatin akması için uygulamayı her 1 saniyede bir tetikler (Sadece arayüzü tazeler)
# Not: Borsa verileri sadece 300 saniyede bir çekilecek şekilde aşağıda kurgulandı.
if "last_update" not in st.session_state:
    st.session_state.last_update = 0

# Türkiye Saat Dilimi
def guncel_saat_getir():
    tr_tz = pytz.timezone('Europe/Istanbul')
    now = datetime.now(tr_tz)
    return now.strftime("%H:%M:%S"), now.timestamp()

# TL Formatlama
def format_tl(deger):
    return f"{deger:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

# Veriyi Oku
def veri_yukle():
    if os.path.exists("deneme2.json"):
        with open("deneme2.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- ARAYÜZ ---
su_an_saat, su_an_ts = guncel_saat_getir()

col_baslik, col_saat = st.columns([3, 1])
with col_baslik:
    st.title("📊 Canlı Portföy Merkezi")
    # Veri güncelleme periyodunu kullanıcıya bildiriyoruz
    st.caption(f"🕒 Saat saniyelik akar. | 🔄 Borsa verileri 5 dakikada bir (300s) otomatik yenilenir.")

with col_saat:
    st.markdown(f"""
        <div style="background-color: #0f172a; color: #fbbf24; padding: 10px; 
        border-radius: 12px; text-align: center; font-size: 32px; font-weight: bold;
        border: 2px solid #fbbf24; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
            {su_an_saat}
        </div>
    """, unsafe_allow_html=True)

# --- VERİ ÇEKME MANTIĞI (ÖNBELLEKLEME) ---
# st.cache_data kullanarak verileri 300 saniye (5 dk) boyunca hafızada tutuyoruz.
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

    # Hisseler
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

# Verileri çek (Önbellekten veya 5 dk dolduysa piyasadan)
portfoy = veri_yukle()
hisse_data, toplam_maliyet, toplam_guncel_deger, bist_fiyat, bist_degisim = piyasa_verilerini_getir(portfoy)

if hisse_data:
    df = pd.DataFrame(hisse_data)
    toplam_kz = toplam_guncel_deger - toplam_maliyet
    kz_yuzde = (toplam_kz / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
    
    # Kartlar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portföy Değeri", format_tl(toplam_guncel_deger))
    c2.metric("Net Kâr/Zarar", format_tl(toplam_kz), delta=f"{kz_yuzde:.2f}%")
    c3.metric("Hisse Sayısı", len(hisse_data))
    c4.metric("BIST 100", f"{bist_fiyat:,.2f}", delta=f"{bist_degisim:.2f}%")

    st.divider()

    # Görselleştirme
    col_past, col_tablo = st.columns([1, 2])
    with col_past:
        fig = px.pie(df, values='TUTAR', names='HİSSE', hole=0.4, title="Dağılım")
        st.plotly_chart(fig, use_container_width=True)

    with col_tablo:
        def renk_ayari(val):
            return f'color: {"#27ae60" if val > 0 else "#c0392b"}; font-weight: bold'

        df_styled = df.sort_values(by="TUTAR", ascending=False).style\
            .map(renk_ayari, subset=['K/Z (TL)', 'YÜZDE (%)'])\
            .format({'ADET': '{:,.0f}', 'ALIŞ': '{:,.2f}', 'GÜNCEL': '{:,.2f}',
                     'TUTAR': '{:,.2f}', 'K/Z (TL)': '{:,.2f}', 'YÜZDE (%)': '%{:.2f}'})
        st.dataframe(df_styled, use_container_width=True, hide_index=True)

# --- SÜREKLİ AKIŞ SİHİRİ ---
# Bu komut sayfanın her 1 saniyede bir kendini yenilemesini sağlar.
# Saat her saniye güncellenir, ama 'piyasa_verilerini_getir' fonksiyonu 
# 'ttl=300' sayesinde sadece 5 dakikada bir gerçek veri çeker.
time.sleep(1)
st.rerun()
