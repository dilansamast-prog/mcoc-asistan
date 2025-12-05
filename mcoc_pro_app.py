import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import json
import os

# --- AYARLAR ---
EXCEL_DOSYASI = "MARVEL 2026 TÜM LİSTE.XLSX"
SAYFA_ANA = "Marvel 2026"
SAYFA_TAKTIK = "nasıl dövüşülür"
KADRO_DOSYASI = "kadrom.json"

# Sınıf Avantajları
SINIF_AVANTAJI = {
    "Mutant": "Beceri",
    "Beceri": "Bilim",
    "Bilim": "Mistik",
    "Mistik": "Kozmik",
    "Kozmik": "Teknoloji",
    "Teknoloji": "Mutant"
}

class MCOCAsistanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MCoC Savaş Asistanı 2026 - Pro V2")
        self.root.geometry("1000x750")

        # Verileri Yükle
        self.tum_karakterler_db = self.excel_yukle()
        self.tum_isimler = sorted(list(self.tum_karakterler_db.keys())) # Arama için tam liste
        self.benim_kadrom = self.kadro_yukle()

        # Arayüz Sekmeleri
        self.tab_control = ttk.Notebook(root)
        
        self.tab_savas = ttk.Frame(self.tab_control)
        self.tab_kadro = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_savas, text='⚔️ Savaş Asistanı')
        self.tab_control.add(self.tab_kadro, text='🛡️ Kadro Yönetimi')
        
        self.tab_control.pack(expand=1, fill="both")

        # Sekmeleri Oluştur
        self.arayuz_kadro_yonetimi()
        self.arayuz_savas_asistani()

    def excel_yukle(self):
        """Excel'deki iki sayfayı okur ve birleştirir"""
        if not os.path.exists(EXCEL_DOSYASI):
            messagebox.showerror("Hata", f"{EXCEL_DOSYASI} bulunamadı!")
            return {}
        
        try:
            # 1. Ana Sayfayı Oku (Statlar ve Antiler)
            df_main = pd.read_excel(EXCEL_DOSYASI, sheet_name=SAYFA_ANA)
            df_main.columns = df_main.columns.str.strip()
            
            # 2. Taktik Sayfasını Oku (Nasıl Dövülür)
            try:
                df_tactic = pd.read_excel(EXCEL_DOSYASI, sheet_name=SAYFA_TAKTIK)
                df_tactic.columns = df_tactic.columns.str.strip()
            except:
                messagebox.showwarning("Uyarı", f"'{SAYFA_TAKTIK}' sayfası bulunamadı, taktikler boş gelecek.")
                df_tactic = pd.DataFrame() # Boş dataframe

            # Veritabanını oluştur
            db = {}
            
            # Önce ana verileri yükle
            for _, row in df_main.iterrows():
                isim = str(row['İsim']).strip()
                db[isim] = row.to_dict()
                # Varsayılan boş değerler ata (Taktik sayfası yoksa hata vermesin)
                db[isim]['SP Tercihi (Bait)'] = "-"
                db[isim]['Kritik Uyarı (Yasaklar)'] = "-"
                db[isim]['Nasıl Dövülür (Taktik)'] = "-"

            # Sonra taktik verilerini eşleştir ve güncelle
            if not df_tactic.empty:
                for _, row in df_tactic.iterrows():
                    isim = str(row['İsim']).strip()
                    if isim in db:
                        db[isim].update({
                            'SP Tercihi (Bait)': row.get('SP Tercihi (Bait)', '-'),
                            'Kritik Uyarı (Yasaklar)': row.get('Kritik Uyarı (Yasaklar)', '-'),
                            'Nasıl Dövülür (Taktik)': row.get('Nasıl Dövülür (Taktik)', '-')
                        })
            
            return db

        except Exception as e:
            messagebox.showerror("Hata", f"Excel okuma hatası: {str(e)}")
            return {}

    def kadro_yukle(self):
        if os.path.exists(KADRO_DOSYASI):
            with open(KADRO_DOSYASI, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def kadro_kaydet(self):
        with open(KADRO_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(self.benim_kadrom, f, indent=4, ensure_ascii=False)

    def arama_filtresi(self, event, combobox):
        """Combobox'a yazılan yazıya göre listeyi filtreler"""
        yazilan = event.widget.get()
        
        if yazilan == '':
            combobox['values'] = self.tum_isimler
        else:
            # İçinde geçen kelimeleri bul (Büyük/küçük harf duyarsız)
            filtrelenmis = [x for x in self.tum_isimler if yazilan.lower() in x.lower()]
            combobox['values'] = filtrelenmis
            
        # Listeyi açmak istersen (opsiyonel, bazen rahatsız edici olabilir)
        # combobox.event_generate('<Down>')

    # --- KADRO YÖNETİMİ ---
    def arayuz_kadro_yonetimi(self):
        frame_top = ttk.Frame(self.tab_kadro, padding=10)
        frame_top.pack(fill="x")

        ttk.Label(frame_top, text="Şampiyon Ara/Seç:").grid(row=0, column=0, padx=5)
        
        # Akıllı Arama Kutusu
        self.combo_isim = ttk.Combobox(frame_top, values=self.tum_isimler, width=30)
        self.combo_isim.grid(row=0, column=1, padx=5)
        # Her tuşa basıldığında filtreleme yap
        self.combo_isim.bind('<KeyRelease>', lambda event: self.arama_filtresi(event, self.combo_isim))

        ttk.Label(frame_top, text="Yıldız:").grid(row=0, column=2, padx=5)
        self.combo_yildiz = ttk.Combobox(frame_top, values=["7 Yıldız", "6 Yıldız", "5 Yıldız"], width=10)
        self.combo_yildiz.current(1)
        self.combo_yildiz.grid(row=0, column=3, padx=5)

        ttk.Label(frame_top, text="Rütbe:").grid(row=0, column=4, padx=5)
        self.combo_rank = ttk.Combobox(frame_top, values=["R5", "R4", "R3", "R2", "R1"], width=5)
        self.combo_rank.current(0)
        self.combo_rank.grid(row=0, column=5, padx=5)

        btn_ekle = ttk.Button(frame_top, text="Kadroya Ekle", command=self.kadroya_ekle)
        btn_ekle.grid(row=0, column=6, padx=10)

        # Liste
        frame_list = ttk.Frame(self.tab_kadro, padding=10)
        frame_list.pack(fill="both", expand=True)

        columns = ('isim', 'yildiz', 'rank', 'sinif')
        self.tree_kadro = ttk.Treeview(frame_list, columns=columns, show='headings')
        
        self.tree_kadro.heading('isim', text='Şampiyon Adı')
        self.tree_kadro.heading('yildiz', text='Yıldız')
        self.tree_kadro.heading('rank', text='Rütbe')
        self.tree_kadro.heading('sinif', text='Sınıf')
        
        self.tree_kadro.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree_kadro.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree_kadro.configure(yscrollcommand=scrollbar.set)

        btn_sil = ttk.Button(self.tab_kadro, text="Seçili Olanı Sil", command=self.kadrodan_sil)
        btn_sil.pack(pady=10)

        self.kadro_listesini_guncelle()

    def kadroya_ekle(self):
        isim = self.combo_isim.get()
        yildiz = self.combo_yildiz.get()
        rank = self.combo_rank.get()

        if isim not in self.tum_karakterler_db:
            messagebox.showwarning("Uyarı", "Lütfen listeden geçerli bir karakter seçin!")
            return

        sinif = self.tum_karakterler_db[isim].get('Sınıf', 'Bilinmiyor')
        yeni_kayit = {"isim": isim, "yildiz": yildiz, "rank": rank, "sinif": sinif}
        
        for k in self.benim_kadrom:
            if k['isim'] == isim and k['yildiz'] == yildiz:
                messagebox.showinfo("Bilgi", "Bu karakter zaten kadronuzda var.")
                return

        self.benim_kadrom.append(yeni_kayit)
        self.kadro_kaydet()
        self.kadro_listesini_guncelle()
        # Kutuyu temizle
        self.combo_isim.set('') 
        self.combo_isim['values'] = self.tum_isimler # Listeyi sıfırla

    def kadrodan_sil(self):
        selected_item = self.tree_kadro.selection()
        if not selected_item: return
        
        item = self.tree_kadro.item(selected_item)
        values = item['values']
        self.benim_kadrom = [k for k in self.benim_kadrom if not (k['isim'] == values[0] and k['yildiz'] == values[1])]
        self.kadro_kaydet()
        self.kadro_listesini_guncelle()

    def kadro_listesini_guncelle(self):
        for i in self.tree_kadro.get_children():
            self.tree_kadro.delete(i)
        for k in self.benim_kadrom:
            self.tree_kadro.insert('', 'end', values=(k['isim'], k['yildiz'], k['rank'], k['sinif']))

    # --- SAVAŞ ASİSTANI ---
    def arayuz_savas_asistani(self):
        frame_top = ttk.Frame(self.tab_savas, padding=20)
        frame_top.pack(fill="x")

        ttk.Label(frame_top, text="RAKİP ŞAMPİYON:", font=("Arial", 12, "bold")).pack(side="left")
        
        # Akıllı Arama Kutusu (Rakip İçin)
        self.combo_rakip = ttk.Combobox(frame_top, values=self.tum_isimler, font=("Arial", 11), width=40)
        self.combo_rakip.pack(side="left", padx=10)
        self.combo_rakip.bind('<KeyRelease>', lambda event: self.arama_filtresi(event, self.combo_rakip))

        btn_analiz = ttk.Button(frame_top, text="ANALİZ ET", command=self.analiz_et)
        btn_analiz.pack(side="left", padx=10)

        self.text_sonuc = tk.Text(self.tab_savas, height=30, font=("Consolas", 10), padx=10, pady=10)
        self.text_sonuc.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(self.text_sonuc, command=self.text_sonuc.yview)
        self.text_sonuc['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side="right", fill="y")

        # Tag yapılandırması (Renklendirme için)
        self.text_sonuc.tag_configure("baslik", font=("Consolas", 12, "bold"), foreground="blue")
        self.text_sonuc.tag_configure("uyari", foreground="red")
        self.text_sonuc.tag_configure("basari", foreground="green")

    def analiz_et(self):
        rakip_isim = self.combo_rakip.get()
        if rakip_isim not in self.tum_karakterler_db:
            messagebox.showerror("Hata", "Lütfen listeden geçerli bir rakip seçin.")
            return

        rakip_data = self.tum_karakterler_db[rakip_isim]
        rakip_sinifi = rakip_data.get('Sınıf', 'Bilinmiyor')
        onerilen_antiler_str = str(rakip_data.get('En İyi 5 Anti (Counter)', ''))
        
        # Taktik verilerini güvenli çek
        yasaklar = rakip_data.get('Kritik Uyarı (Yasaklar)', '-')
        if pd.isna(yasaklar): yasaklar = "-" # Excel boşsa NaN gelir
        
        bait = rakip_data.get('SP Tercihi (Bait)', '-')
        if pd.isna(bait): bait = "-"

        taktik = rakip_data.get('Nasıl Dövülür (Taktik)', '-')
        if pd.isna(taktik): taktik = "-"

        self.text_sonuc.delete(1.0, tk.END)
        
        self.text_sonuc.insert(tk.END, f"🛑 RAKİP: {rakip_isim.upper()} ({rakip_sinifi})\n", "baslik")
        self.text_sonuc.insert(tk.END, "="*60 + "\n")
        self.text_sonuc.insert(tk.END, f"⚠️  YASAKLAR: {yasaklar}\n", "uyari")
        self.text_sonuc.insert(tk.END, f"🎯  BAIT (Attır): {bait}\n")
        self.text_sonuc.insert(tk.END, f"🥊  TAKTIK: {taktik}\n\n")

        uygun_adaylar = []

        for hero in self.benim_kadrom:
            puan = 0
            nedenler = []
            
            hero_isim = hero['isim']
            hero_sinif = hero['sinif']
            hero_yildiz = hero['yildiz']
            hero_rank = hero['rank']

            # 1. Anti Kontrol
            if hero_isim in onerilen_antiler_str:
                puan += 50
                nedenler.append("⭐ TAM ANTİ")

            # 2. Sınıf Avantajı
            if SINIF_AVANTAJI.get(hero_sinif) == rakip_sinifi:
                puan += 20
                nedenler.append(f"✅ Sınıf Avantajı ({hero_sinif})")
            elif SINIF_AVANTAJI.get(rakip_sinifi) == hero_sinif:
                puan -= 15
                nedenler.append(f"❌ Sınıf Dezavantajı")

            # 3. Güç Bonusu
            if hero_yildiz == "7 Yıldız": puan += 10
            elif hero_yildiz == "6 Yıldız": puan += 5
            if hero_rank == "R5": puan += 5
            elif hero_rank == "R4": puan += 4
            elif hero_rank == "R3": puan += 3

            if puan > 0:
                uygun_adaylar.append({
                    "bilgi": f"{hero_isim} ({hero_yildiz} {hero_rank})",
                    "puan": puan,
                    "nedenler": nedenler
                })

        uygun_adaylar.sort(key=lambda x: x['puan'], reverse=True)

        self.text_sonuc.insert(tk.END, "✅ SENİN KADRONDAKİ EN İYİ SEÇENEKLER:\n", "basari")
        self.text_sonuc.insert(tk.END, "-"*60 + "\n")

        if not uygun_adaylar:
            self.text_sonuc.insert(tk.END, "❌ Kadrunda özel bir counter bulunamadı.\n")
            self.text_sonuc.insert(tk.END, f"💡 Genel Öneriler: {onerilen_antiler_str}\n")
        else:
            for i, aday in enumerate(uygun_adaylar):
                self.text_sonuc.insert(tk.END, f"{i+1}. {aday['bilgi']} -- PUAN: {aday['puan']}\n")
                self.text_sonuc.insert(tk.END, f"   └-> {', '.join(aday['nedenler'])}\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = MCOCAsistanApp(root)
    root.mainloop()