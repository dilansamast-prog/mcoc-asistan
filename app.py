import streamlit as st
import pandas as pd
import json
import os

# --- AYARLAR ---
EXCEL_DOSYASI = "marvel_data.xlsx"  # Yeni, basit isim
SAYFA_ANA = "Marvel 2026"
SAYFA_TAKTIK = "nasıl dövüşülür"
KADRO_DOSYASI = "kadrom.json"

# Sayfa Yapılandırması (Mobil uyumlu görünüm için)
st.set_page_config(
    page_title="MCoC Savaş Asistanı",
    page_icon="⚔️",
    layout="centered"
)

# Sınıf Avantajları
SINIF_AVANTAJI = {
    "Mutant": "Beceri",
    "Beceri": "Bilim",
    "Bilim": "Mistik",
    "Mistik": "Kozmik",
    "Kozmik": "Teknoloji",
    "Teknoloji": "Mutant"
}

# --- FONKSİYONLAR ---

@st.cache_data # Excel'i her seferinde tekrar okumasın diye önbelleğe alıyoruz
def excel_yukle():
    if not os.path.exists(EXCEL_DOSYASI):
        return None
    
    try:
        # 1. Ana Sayfayı Oku
        df_main = pd.read_excel(EXCEL_DOSYASI, sheet_name=SAYFA_ANA)
        df_main.columns = df_main.columns.str.strip()
        
        # 2. Taktik Sayfasını Oku
        try:
            df_tactic = pd.read_excel(EXCEL_DOSYASI, sheet_name=SAYFA_TAKTIK)
            df_tactic.columns = df_tactic.columns.str.strip()
        except:
            df_tactic = pd.DataFrame()

        db = {}
        for _, row in df_main.iterrows():
            isim = str(row['İsim']).strip()
            db[isim] = row.to_dict()
            db[isim]['SP Tercihi (Bait)'] = "-"
            db[isim]['Kritik Uyarı (Yasaklar)'] = "-"
            db[isim]['Nasıl Dövülür (Taktik)'] = "-"

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
        st.error(f"Excel Okuma Hatası: {e}")
        return None

def kadro_yukle():
    if os.path.exists(KADRO_DOSYASI):
        with open(KADRO_DOSYASI, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def kadro_kaydet(kadro):
    with open(KADRO_DOSYASI, 'w', encoding='utf-8') as f:
        json.dump(kadro, f, indent=4, ensure_ascii=False)

# --- ARAYÜZ BAŞLANGICI ---

st.title("⚔️ MCoC Savaş Asistanı")

# Verileri Yükle
db = excel_yukle()

if db is None:
    st.error(f"'{EXCEL_DOSYASI}' dosyası bulunamadı! Lütfen dosyanın proje klasöründe olduğundan emin olun.")
    st.stop()

tum_isimler = sorted(list(db.keys()))

# Mevcut kadroyu session state'e yükle (Anlık yenileme için)
if 'kadro' not in st.session_state:
    st.session_state['kadro'] = kadro_yukle()

# Sekmeleri Oluştur
tab1, tab2 = st.tabs(["🔥 Savaş Analizi", "🛡️ Kadro Yönetimi"])

# --- TAB 1: SAVAŞ ANALİZİ ---
with tab1:
    st.header("Rakip Analizi")
    
    # Akıllı Arama Kutusu (Streamlit'te native olarak var)
    secilen_rakip = st.selectbox("Rakip Şampiyonu Seçin:", tum_isimler, index=None, placeholder="Şampiyon adı yazın...")

    if secilen_rakip:
        rakip_data = db[secilen_rakip]
        r_sinif = rakip_data.get('Sınıf', 'Bilinmiyor')
        
        # Rakip Bilgileri Kartı
        with st.expander("📊 Rakip Detayları ve Taktikler (Tıkla)", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Sınıf:** {r_sinif}")
                st.markdown(f"**🚫 Yasaklar:** :red[{rakip_data.get('Kritik Uyarı (Yasaklar)', '-')}]")
            with col2:
                st.markdown(f"**🎯 Bait (Attır):** {rakip_data.get('SP Tercihi (Bait)', '-')}")
            
            st.info(f"**🥊 Dövüş Taktiği:**\n{rakip_data.get('Nasıl Dövülür (Taktik)', '-')}")

        st.divider()
        st.subheader("✅ Senin Kadron İçin Öneriler")

        # HESAPLAMA MOTORU
        uygun_adaylar = []
        antiler_text = str(rakip_data.get('En İyi 5 Anti (Counter)', ''))

        for hero in st.session_state['kadro']:
            puan = 0
            nedenler = []
            
            h_isim = hero['isim']
            h_sinif = hero['sinif']
            
            # 1. Anti Kontrol
            if h_isim in antiler_text:
                puan += 50
                nedenler.append("⭐ TAM ANTİ")
            
            # 2. Sınıf Avantajı
            if SINIF_AVANTAJI.get(h_sinif) == r_sinif:
                puan += 20
                nedenler.append(f"✅ Sınıf Avantajı")
            elif SINIF_AVANTAJI.get(r_sinif) == h_sinif:
                puan -= 15
                nedenler.append(f"❌ Sınıf Dezavantajı")
            
            # 3. Rütbe Puanı
            if hero['yildiz'] == "7 Yıldız": puan += 10
            elif hero['yildiz'] == "6 Yıldız": puan += 5
            
            if hero['rank'] == "R5": puan += 5
            elif hero['rank'] == "R4": puan += 4
            
            if puan > 0:
                uygun_adaylar.append({
                    "isim": h_isim,
                    "detay": f"{hero['yildiz']} {hero['rank']}",
                    "puan": puan,
                    "nedenler": ", ".join(nedenler)
                })
        
        # Sıralama
        uygun_adaylar.sort(key=lambda x: x['puan'], reverse=True)

        if not uygun_adaylar:
            st.warning("Kadronuzda bu rakibe özel bir counter bulunamadı.")
            st.markdown(f"**💡 Genel Oyun İçi Öneriler:** {antiler_text}")
        else:
            for i, aday in enumerate(uygun_adaylar):
                # Kart Görünümü
                with st.container():
                    st.success(f"**{i+1}. {aday['isim']}** ({aday['detay']}) - Puan: {aday['puan']}")
                    st.caption(f"└-> {aday['nedenler']}")

# --- TAB 2: KADRO YÖNETİMİ ---
with tab2:
    st.header("Kadro Düzenle")
    
    col_k1, col_k2, col_k3 = st.columns(3)
    
    with col_k1:
        yeni_isim = st.selectbox("Şampiyon Ekle:", tum_isimler, index=None, placeholder="Seçiniz...")
    with col_k2:
        yeni_yildiz = st.selectbox("Yıldız:", ["7 Yıldız", "6 Yıldız", "5 Yıldız"], index=1)
    with col_k3:
        yeni_rank = st.selectbox("Rank:", ["R5", "R4", "R3", "R2", "R1"], index=0)
        
    if st.button("Kadroya Ekle", type="primary"):
        if yeni_isim:
            # Mükerrer Kontrol
            var_mi = any(k['isim'] == yeni_isim and k['yildiz'] == yeni_yildiz for k in st.session_state['kadro'])
            if var_mi:
                st.toast("Bu karakter zaten ekli!", icon="⚠️")
            else:
                sinif = db[yeni_isim].get('Sınıf', 'Bilinmiyor')
                yeni_kayit = {"isim": yeni_isim, "yildiz": yeni_yildiz, "rank": yeni_rank, "sinif": sinif}
                st.session_state['kadro'].append(yeni_kayit)
                kadro_kaydet(st.session_state['kadro'])
                st.toast(f"{yeni_isim} eklendi!", icon="✅")
                st.rerun() # Sayfayı yenile
        else:
            st.toast("Lütfen bir isim seçin.", icon="❌")

    st.divider()
    st.subheader("Mevcut Kadrom")
    
    if st.session_state['kadro']:
        # DataFrame olarak göster (Daha şık tablo)
        df_kadro = pd.DataFrame(st.session_state['kadro'])
        st.dataframe(df_kadro, use_container_width=True, hide_index=True)
        
        # Silme İşlemi
        silinecek = st.selectbox("Kadrodan Silmek İçin Seç:", 
                                 [f"{k['isim']} ({k['yildiz']})" for k in st.session_state['kadro']],
                                 index=None)
        
        if silinecek and st.button("Seçileni Sil"):
            isim_sil, yildiz_sil = silinecek.split(" (")
            yildiz_sil = yildiz_sil.replace(")", "")
            
            st.session_state['kadro'] = [k for k in st.session_state['kadro'] 
                                         if not (k['isim'] == isim_sil and k['yildiz'] == yildiz_sil)]
            kadro_kaydet(st.session_state['kadro'])
            st.success("Silindi!")
            st.rerun()
    else:

        st.info("Henüz kadrona şampiyon eklemedin.")
