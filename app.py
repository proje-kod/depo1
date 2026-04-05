import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel
import yfinance as yf
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DATA_FILE = "portfoyum.json"

class BorsaPortfoy:
    def __init__(self, root):
        self.root = root
        self.root.title("Portföy Takip Sistemi (BIST 30)")
        self.root.geometry("800x670+0+0") # Saat için yükseklik biraz artırıldı
        
        # Üst Panel (Saat ve Başlık için)
        top_panel = tk.Frame(root)
        top_panel.pack(fill="x", padx=20, pady=5)

        self.index_label = tk.Label(top_panel, text="BIST 100: Yükleniyor...", font=("Arial", 12, "bold"), fg="#2c3e50")
        self.index_label.pack(side="left")

        # Canlı Saat Etiketi (Sağ Üst)
        self.clock_label = tk.Label(top_panel, text="", font=("Arial", 11, "italic"), fg="#7f8c8d")
        self.clock_label.pack(side="right")

        # Liste Başlıkları
        header_frame = tk.Frame(root)
        header_frame.pack(fill="x", padx=20)
        tk.Label(header_frame, text="HİSSE", font=("Arial", 9, "bold"), width=8, anchor="w").pack(side="left")
        tk.Label(header_frame, text="ADET", font=("Arial", 9, "bold"), width=8).pack(side="left")
        tk.Label(header_frame, text="ALIŞ", font=("Arial", 9, "bold"), width=12).pack(side="left", padx=(60, 0))
        tk.Label(header_frame, text="GÜNCEL", font=("Arial", 9, "bold"), width=12).pack(side="left")
        tk.Label(header_frame, text="TUTAR", font=("Arial", 9, "bold"), width=15, fg="#2980b9").pack(side="left")
        tk.Label(header_frame, text="KAR-ZARAR (TL)", font=("Arial", 9, "bold"), width=15, fg="#8e44ad").pack(side="left", padx=(40, 0))
        tk.Label(header_frame, text="YÜZDE (%)", font=("Arial", 9, "bold"), width=10, anchor="e").pack(side="left")

        self.listbox = tk.Listbox(root, font=("Courier New", 10, "bold"), height=15)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=5)

        self.total_label = tk.Label(root, text="TOPLAM PORTFÖY DEĞERİ: 0,00 TL", font=("Arial", 12, "bold"), bg="#f1c40f", pady=10)
        self.total_label.pack(fill="x", padx=20, pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="HİSSE EKLE", command=self.hisse_ekle, bg="#27ae60", fg="white", width=11, font=("Arial", 8, "bold")).grid(row=0, column=0, padx=2)
        tk.Button(btn_frame, text="DÜZELT", command=self.hisse_duzelt, bg="#f39c12", fg="white", width=11, font=("Arial", 8, "bold")).grid(row=0, column=1, padx=2)
        tk.Button(btn_frame, text="HİSSE SİL", command=self.hisse_sil, bg="#c0392b", fg="white", width=11, font=("Arial", 8, "bold")).grid(row=0, column=2, padx=2)
        # tk.Button(btn_frame, text="5 GÜNLÜK SEYİR", command=self.seyir_ekrani_ac, bg="#3498db", fg="white", width=15, font=("Arial", 8, "bold")).grid(row=0, column=3, padx=2)

        self.portfoy = self.yukle()
        if "XU100" not in self.portfoy:
            self.portfoy["XU100"] = {"adet": "1", "alis": "0.00", "gecmis": ["0.00"] * 5, "son_guncelleme": ""}
        
        # Döngüleri Başlat
        self.saati_guncelle()
        self.otomatik_guncelle_dongusu() # İlk güncelleme ve 5 dk'lık döngü
        
    def saati_guncelle(self):
        zaman_str = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=f"Saat: {zaman_str}")
        self.root.after(1000, self.saati_guncelle) # Her 1 saniyede bir saati tazele

    def otomatik_guncelle_dongusu(self):
        self.guncelle()
        # 300.000 ms = 5 dakika
        self.root.after(300000, self.otomatik_guncelle_dongusu)

    def yukle(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f: return json.load(f)
        return {}

    def kaydet(self):
        with open(DATA_FILE, "w") as f: json.dump(self.portfoy, f)

    def format_tl(self, deger):
        try:
            return f"{float(deger):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except: return "0,00"

    def hisse_ekle(self):
        hisse = simpledialog.askstring("Hisse Ekle", "Hisse kodu (Örn: SISE):", parent=self.root)
        if hisse:
            hisse = hisse.upper().strip()
            adet = simpledialog.askstring("Adet", f"{hisse} Adedi:", parent=self.root)
            alis = simpledialog.askstring("Alış Fiyatı", f"{hisse} Alış Fiyatı:", parent=self.root)
            if adet and alis:
                self.portfoy[hisse] = {"adet": adet, "alis": alis.replace(",", "."), "gecmis": ["0.00"] * 5, "son_guncelleme": ""}
                self.kaydet(); self.guncelle()

    def hisse_duzelt(self):
        secili = self.listbox.curselection()
        if not secili: return
        item = self.listbox.get(secili[0]); hisse_adi = item.split()[0]
        if hisse_adi == "XU100": return
        m = self.portfoy[hisse_adi]
        y_adet = simpledialog.askstring("Düzelt", "Yeni Adet:", initialvalue=m['adet'], parent=self.root)
        y_alis = simpledialog.askstring("Düzelt", "Yeni Alış:", initialvalue=m['alis'], parent=self.root)
        if y_adet and y_alis:
            self.portfoy[hisse_adi]['adet'] = y_adet
            self.portfoy[hisse_adi]['alis'] = y_alis.replace(",", ".")
            self.kaydet(); self.guncelle()

    def hisse_sil(self):
        secili = self.listbox.curselection()
        if not secili: return
        hisse_adi = self.listbox.get(secili[0]).split()[0]
        if hisse_adi != "XU100" and messagebox.askyesno("Onay", f"{hisse_adi} silinsin mi?", parent=self.root):
            del self.portfoy[hisse_adi]; self.kaydet(); self.guncelle()

    def guncelle(self):
        self.listbox.delete(0, tk.END)
        toplam_deger = 0.0
        
        # 1. Endeks Verisi
        try:
            bist_fiyat = yf.Ticker("XU100.IS").history(period="1d")['Close'].iloc[-1]
            self.index_label.config(text=f"BIST 100 GÜNCEL: {self.format_tl(bist_fiyat)}")
            index_satir = f"{'XU100':<8} {'-':<8} {'-':>12} {self.format_tl(bist_fiyat):>12} {'-':>15} {'-':>15} {'-':>12}"
            self.listbox.insert(tk.END, index_satir)
            self.listbox.itemconfig(tk.END, {'fg': 'blue'})
        except: pass

        # 2. Hisseleri Hesapla
        hisse_listesi = []
        for h, info in self.portfoy.items():
            if h == "XU100": continue
            try:
                # Veri çekme
                data = yf.Ticker(f"{h}.IS").history(period="1d")
                if data.empty: continue
                guncel_fiyat = data['Close'].iloc[-1]
                
                adet = float(info['adet'])
                alis_fiyati = float(info['alis'])
                
                bagli_tutar = guncel_fiyat * adet
                kar_zarar_tl = (guncel_fiyat - alis_fiyati) * adet
                yuzde_degisim = ((guncel_fiyat - alis_fiyati) / alis_fiyati) * 100 if alis_fiyati > 0 else 0
                
                toplam_deger += bagli_tutar
                hisse_listesi.append({
                    'kod': h, 'adet': info['adet'], 'alis': alis_fiyati, 
                    'guncel': guncel_fiyat, 'tutar': bagli_tutar, 
                    'kz_tl': kar_zarar_tl, 'yuzde': yuzde_degisim
                })
            except: continue

        # 3. Sırala ve Yazdır
        hisse_listesi.sort(key=lambda x: x['tutar'], reverse=True)
        for item in hisse_listesi:
            yuzde_str = f"%{item['yuzde']:+.2f}"
            kz_str = self.format_tl(item['kz_tl'])
            satir = f"{item['kod']:<8} {item['adet']:<8} {self.format_tl(item['alis']):>12} {self.format_tl(item['guncel']):>12} {self.format_tl(item['tutar']):>15} {kz_str:>15} {yuzde_str:>12}"
            self.listbox.insert(tk.END, satir)
            
            idx = self.listbox.size() - 1
            if item['yuzde'] > 0: self.listbox.itemconfig(idx, {'fg': 'green'})
            elif item['yuzde'] < 0: self.listbox.itemconfig(idx, {'fg': 'red'})

        self.total_label.config(text=f"TOPLAM PORTFÖY DEĞERİ: {self.format_tl(toplam_deger)} TL")

    def seyir_ekrani_ac(self):
        seyir_penceresi = Toplevel(self.root)
        seyir_penceresi.geometry("850x450")
        seyir_penceresi.title("5 Günlük Seyir")
        seyir_listbox = tk.Listbox(seyir_penceresi, font=("Courier New", 9))
        seyir_listbox.pack(fill="both", expand=True)
        for h, info in self.portfoy.items():
            g = info.get("gecmis", ["0.00"]*5)
            satir = f"{h:<8} {info.get('adet','-'):<8} " + " ".join([f"{self.format_tl(gf):>12}" for gf in g])
            seyir_listbox.insert(tk.END, satir)

if __name__ == "__main__":
    root = tk.Tk()
    app = BorsaPortfoy(root)
    root.mainloop()
