import streamlit as st
import yfinance as yf
import json
import os
import pandas as pd
from datetime import datetime

# Dosya Ayarları
DATA_FILE = "deneme1.json"

# Sayfa Konfigürasyonu
st.set_page_config(page_title="Borsa Portföy Takip", layout="wide")

# Veri Yükleme Fonksiyonları
def yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"XU100": {"adet": "1", "alis": "0.00"}}

def kaydet(portfoy):
    with open(DATA_FILE, "w") as f:
        json.dump(portfoy, f)

# TL Formatlama Fonksiyonu
def format_tl(deger):
    return f"{deger:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")

# Uygulama Başlığı ve Canlı Bilgiler
st.title("📈 Portföy Takip Sistemi (BIST)")
col_info1, col_info2 = st.columns(2)

portfoy = yukle()

# BIST 100 Verisi Çekme
try:
    bist_data = yf.Ticker("XU100.IS").history(period="1d")
    bist_fiyat = bist_data['Close'].iloc[-1]
    col_info1.metric("BIST 100 GÜNCEL", f"{bist_fiyat:,.2f}")
except:
    col_info1.error("BIST 100 verisi çekilemedi.")

col_info2.write(f"**Son Güncelleme:** {datetime.now().strftime('%H:%M:%S')}")

# Yan Panel - Hisse Ekleme/Düzenleme
with st.sidebar:
    st.header("⚙️ İşlemler")
    yeni_hisse = st.text_input("Hisse Kodu (Örn: SISE)").upper().strip()
    yeni_adet = st.number_input("Adet", min_value=0.0, step=1.0)
    yeni_alis = st.number_input("Alış Fiyatı", min_value=0.0, step=0.01)
    
    if st.button("HİSSE EKLE / GÜNCELLE"):
        if yeni_hisse:
            portfoy[yeni_hisse] = {"adet": str(yeni_adet), "alis": str(yeni_alis)}
            kaydet(portfoy)
            st.success(f"{yeni_hisse} eklendi!")
            st.rerun()

    st.divider()
    silinecek_hisse = st.selectbox("Silinecek Hisse", [h for h in portfoy.keys() if h != "XU100"])
    if st.button("HİSSEYİ SİL"):
        del portfoy[silinecek_hisse]
        kaydet(portfoy)
        st.warning(f"{silinecek_hisse} silindi.")
        st.rerun()

# Portföy Hesaplama ve Tablo Oluşturma
hisse_data = []
toplam_deger = 0.0

for h, info in portfoy.items():
    if h == "XU100": continue
    try:
        ticker = yf.Ticker(f"{h}.IS")
        data = ticker.history(period="1d")
        if data.empty: continue
        
        guncel_fiyat = data['Close'].iloc[-1]
        adet = float(info['adet'])
        alis_fiyati = float(info['alis'])
        
        tutar = guncel_fiyat * adet
        kar_zarar = (guncel_fiyat - alis_fiyati) * adet
        yuzde = ((guncel_fiyat - alis_fiyati) / alis_fiyati * 100) if alis_fiyati > 0 else 0
        
        toplam_deger += tutar
        hisse_data.append({
            "HİSSE": h,
            "ADET": adet,
            "ALIŞ FİYATI": format_tl(alis_fiyati),
            "GÜNCEL": format_tl(guncel_fiyat),
            "TUTAR": tutar,
            "K/Z (TL)": kar_zarar,
            "YÜZDE (%)": f"%{yuzde:+.2f}"
        })
    except:
        continue

# Tabloyu Görüntüle
if hisse_data:
    df = pd.DataFrame(hisse_data)
    # Tutara göre büyükten küçüğe sırala
    df = df.sort_values(by="TUTAR", ascending=False)
    
    # Görselleştirme için formatla
    df["TUTAR"] = df["TUTAR"].apply(format_tl)
    df["K/Z (TL)"] = df["K/Z (TL)"].apply(format_tl)
    
    st.table(df)
    st.subheader(f"💰 TOPLAM PORTFÖY DEĞERİ: {format_tl(toplam_deger)}")
else:
    st.info("Henüz portföyünüzde hisse bulunmuyor. Yan panelden ekleyebilirsiniz.")

