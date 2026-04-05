import streamlit as st
import yfinance as yf
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import time

# Sayfa Ayarları
st.set_page_config(page_title="Borsa Takip", layout="wide", page_icon="📈")

# Türkiye Saat Dilimi
def guncel_saat_getir():
    tr_tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(tr_tz).strftime("%H:%M")

# Veri Yükleme
def veri_yukle():
    if os.path.exists("portfoyum.json"):
        with open("portfoyum.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 5 Dakikalık Önbellek (TTL=300 saniye)
@st.cache_data(ttl=300)
def verileri_cek(portfoy_dict):
    h_list = []
    t_m = 0.0
    t_g = 0.0
    try:
        bist = yf.Ticker("XU100.IS").history(period="2d")
        b_f, b_d = bist['Close'].iloc[-1], ((bist['Close'].iloc[-1]-bist['Close'].iloc[-2])/bist['Close'].iloc[-2])*100
    except: b_f, b_d = 0, 0

    for h, info in portfoy_dict.items():
        try:
            t = yf.Ticker(f"{h}.IS").history(period="1d")
            f = t['Close'].iloc[-1]
            a, ad = float(info['alis']), float(info['adet'])
            h_list.append({"HİSSE": h, "ADET": ad, "ALIŞ": a, "GÜNCEL": f, "TUTAR": f*ad, "K/Z": (f-a)*ad, "YÜZDE": (f-a)/a*100})
            t_m += a*ad; t_g += f*ad
        except: continue
    return h_list, t_m, t_g, b_f, b_d

# --- ARAYÜZ ---
c_baslik, c_saat = st.columns([3, 1])
with c_baslik:
    st.title("📊 Portföy Analizi")
    st.caption("Otomatik Güncelleme: 1 Dakika")

with c_saat:
    st.markdown(f"""<div style="background-color:#0f172a;color:#fbbf24;padding:15px;border-radius:12px;text-align:center;font-size:36px;font-weight:bold;border:2px solid #fbbf24;">{guncel_saat_getir()}</div>""", unsafe_allow_html=True)

p = veri_yukle()
h_data, t_maliyet, t_guncel, b_f, b_d = verileri_cek(p)

if h_data:
    df = pd.DataFrame(h_data)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Değer", f"{t_guncel:,.0f} TL")
    m2.metric("Kâr/Zarar", f"{t_guncel-t_maliyet:,.0f} TL", delta=f"{(t_guncel-t_maliyet)/t_maliyet*100:.2f}%")
    m3.metric("Hisse", len(h_data))
    m4.metric("BIST 100", f"{b_f:,.0f}", delta=f"{b_d:.2f}%")
    
    st.divider()
    col_p, col_t = st.columns([1, 2])
    with col_p:
        st.plotly_chart(px.pie(df, values='TUTAR', names='HİSSE', hole=0.4), use_container_width=True)
    with col_t:
        st.dataframe(df.sort_values("TUTAR", ascending=False), use_container_width=True, hide_index=True)

# --- BİSİKLETİ DURDURAN DÖNGÜ ---
# time.sleep burada 'bloklayıcı' çalışır, yani 60 saniye boyunca hiçbir işlem yapılmaz.
# Bu süreçte sağ üstteki bisiklet (loading ikonu) DURMALIDIR.
time.sleep(60)
st.rerun()

