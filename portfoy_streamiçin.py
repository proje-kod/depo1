import streamlit as st
import yfinance as yf
import json
import os
import pandas as pd
from datetime import datetime
import plotly.express as px  # Grafik için yeni kütüphane

# Dosya Ayarları
DATA_FILE = "portfoyum.json"

# Sayfa Konfigürasyonu
st.set_page_config(page_title="Borsa Portföy Analizi", layout="wide")

# Veri Yükleme/Kaydetme
def yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"XU100": {"adet": "1", "alis": "0.00"}}

def kaydet(portfoy):
    with open(DATA_FILE, "w") as f:
        json.dump(portfoy, f)

# TL Formatlama
def format_tl(deger):
    return f"{deger:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

# Başlık
st.title("📊 Gelişmiş Portföy Yönetimi")

portfoy = yukle()

# --- YAN PANEL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Portföy İşlemleri")
    yeni_hisse = st.text_input("Hisse Kodu (Örn: THYAO)").upper().strip()
    yeni_adet = st.number_input("Adet", min_value=0.0, step=1.0)
    yeni_alis = st.number_input("Alış Fiyatı", min_value=0.0, step=0.01)
    
    if st.button("HİSSE EKLE / GÜNCELLE"):
        if yeni_hisse:
            portfoy[yeni_hisse] = {"adet": str(yeni_adet), "alis": str(yeni_alis)}
            kaydet(portfoy)
            st.success(f"{yeni_hisse} kaydedildi!")
            st.rerun()

    st.divider()
    hisse_listesi = [h for h in portfoy.keys() if h != "XU100"]
    if hisse_listesi:
        silinecek = st.selectbox("Silinecek Hisse", hisse_listesi)
        if st.button("HİSSEYİ SİL"):
            del portfoy[silinecek]
            kaydet(portfoy)
            st.warning(f"{silinecek} silindi.")
            st.rerun()

# --- VERİ HESAPLAMA ---
hisse_data = []
toplam_maliyet = 0.0
toplam_guncel_deger = 0.0

with st.spinner('Veriler güncelleniyor...'):
    for h, info in portfoy.items():
        if h == "XU100": continue
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

# --- GÖRSELLEŞTİRME VE TABLO ---
if hisse_data:
    df = pd.DataFrame(hisse_data)
    
    # Üst Özet Kartları
    toplam_kz = toplam_guncel_deger - toplam_maliyet
    kz_yuzde = (toplam_kz / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Portföy", format_tl(toplam_guncel_deger))
    c2.metric("Toplam K/Z (TL)", format_tl(toplam_kz), delta=f"{format_tl(toplam_kz)}")
    c3.metric("Portföy Başarısı", f"%{kz_yuzde:.2f}", delta=f"{kz_yuzde:.2f}%")

    st.divider()

    # Pasta Grafiği ve Tablo Yan Yana
    col_graph, col_table = st.columns([1, 2])

    with col_graph:
        st.subheader("🎯 Hisse Dağılımı")
        fig = px.pie(df, values='TUTAR', names='HİSSE', hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("📋 Detaylı Liste")
        
        # Renklendirme Fonksiyonu
        def color_kz(val):
            color = '#27ae60' if val > 0 else '#c0392b' if val < 0 else '#7f8c8d'
            return f'color: {color}; font-weight: bold'

        # Tabloyu formatla ve renklendir
        df_styled = df.sort_values(by="TUTAR", ascending=False).style\
            .applymap(color_kz, subset=['K/Z (TL)', 'YÜZDE (%)'])\
            .format({
                'ALIŞ': '{:,.2f}',
                'GÜNCEL': '{:,.2f}',
                'TUTAR': '{:,.2f}',
                'K/Z (TL)': '{:,.2f}',
                'YÜZDE (%)': '%{:.2f}'
            })
        
        st.dataframe(df_styled, use_container_width=True, hide_index=True)

else:
    st.info("Henüz hisse eklenmemiş. Yan panelden giriş yapabilirsiniz.")
