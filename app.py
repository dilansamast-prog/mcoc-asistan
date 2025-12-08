import streamlit as st
import pandas as pd
import extra_streamlit_components as stx
import json
import os
import datetime
import time
import openai  # Yeni eklenen kütüphane

# --- AYARLAR ---
EXCEL_DOSYASI = "marvel_data.xlsx"
SAYFA_ANA = "Marvel 2026"
SAYFA_TAKTIK = "nasıl dövüşülür"

# Sayfa Yapılandırması
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

@st.cache_data
def excel_yukle():
    if not os.path.exists(EXCEL_DOSYASI):
        return None
    
    try:
        df_main = pd.read_excel(EXCEL_DOSYASI, sheet_name=SAYFA_ANA)
        df_main.columns = df_main.columns.str.strip()
        
        try:
            df_tactic = pd.read_excel(EXCEL_DOSYASI, sheet_name=SAYFA_TAKTIK)
            df_tactic.columns = df_tactic.columns.str.strip()
        except:
            df_tactic = pd.DataFrame()

        db = {}
        for _, row in df_main.iterrows():
            isim = str(row['İsim']).strip()
            db[isim] = row.to_dict()
            for key in ['SP Tercihi (Bait)', 'Kritik Uyarı (Yasaklar)', 'Nasıl Dövülür (Taktik)']:
                db[isim][key] = "-"

        if not df_tactic.empty:
            for _, row in df_tactic.iterrows():
                isim = str(row['İsim']).strip()
                if isim in db:
                    db[isim].update({
                        'SP Tercihi (Bait)': row.get('SP Tercihi (Bait)', '-'),
                        'Kritik Uyarı (Yasaklar)': row.get('Kritik Uyarı (Yasaklar)', '-'),
                        'Nasıl Dövülür (Taktik)': row.get('Nasıl Dövülür (Taktik)', '-'),
                        'En İyi 5 Anti (Counter)': row.get('En İyi 5 Anti (Counter)', '-')
                    })
                    if 'En İyi 5 Anti (Counter)' in row and pd.notna(row['En İyi 5 Anti (Counter)']):
                         db[isim]['En İyi 5 Anti (Counter)'] = row['En İyi 5 Anti (Counter)']

        return db
    except Exception as e:
        st.error(f"Excel Hatası: {e}")
        return None

def get_manager():
    return stx.CookieManager(key="mcoc_manager")

cookie_manager = get_manager()

# --- ARAYÜZ BAŞLANGICI ---

# Yan Menü (API Key Girişi)
with st.sidebar:
    st.header("⚙️ Ayarlar")
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", help="ChatGPT özelliğini kullanmak için API anahtarınızı buraya girin.")
    st.info("API Key'iniz tarayıcı oturumu boyunca saklanır, sunucuya kaydedilmez.")

st.title("⚔️ MCoC Savaş Asistanı")

if 'kadro' not in st.session_state:
    st.session_state['kadro'] = []

cookies = cookie_manager.get_all()

if not st.session_state['kadro'] and cookies:
    raw_cookie = cookies.get("my_mcoc_squad")
    if raw_cookie:
        try:
            st.session_state['kadro'] = json.loads(raw_cookie)
        except:
            pass

db = excel_yukle()
if db is None:
    st.error(f"'{EXCEL_DOSYASI}' bulunamadı!")
    st.stop()

tum_isimler = sorted(list(db.keys()))

def kadroyu_cereze_kaydet():
    kadro_str = json.dumps(st.session_state['kadro'], ensure_ascii=False)
    expires = datetime.datetime.now() + datetime.timedelta(days=30)
    cookie_manager.set("my_mcoc_squad", kadro_str, expires_at=expires)

tab1, tab2 = st.tabs(["🔥 Savaş Analizi & AI", "🛡️ Kadro Yönetimi"])

# --- TAB 1: SAVAŞ ANALİZİ VE AI ---
with tab1:
    st.header("Rakip Analizi")
    secilen_rakip = st.selectbox("Rakip Şampiyonu Seçin:", tum_isimler, index=None, placeholder="Yazmaya başlayın...")

    if secilen_rakip:
        rakip_data = db[secilen_rakip]
        r_sinif = rakip_data.get('Sınıf', 'Bilinmiyor')
        
        # --- EXCEL VERİLERİ ---
        with st.expander("📊 Veritabanı Bilgileri (Tıkla)", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Sınıf:** {r_sinif}")
                st.markdown(f"**🚫 Yasaklar:** :red[{rakip_data.get('Kritik Uyarı (Yasaklar)', '-')}]")
            with col2:
                st.markdown(f"**🎯 Bait:** {rakip_data.get('SP Tercihi (Bait)', '-')}")
            
            st.info(f"**🥊 Taktik:**\n{rakip_data.get('Nasıl Dövülür (Taktik)', '-')}")
            st.success(f"**🛡️ En İyi 5 Anti (Genel Öneri):**\n{rakip_data.get('En İyi 5 Anti (Counter)', '-')}")

        st.divider()
        
        # --- AI KOÇU BÖLÜMÜ ---
        st.subheader("🧠 AI Koçuna Sor")
        st.caption("Seçeceğin bir saldırı karakteri ile bu rakibi nasıl döveceğini ChatGPT'ye sor.")

        # Kullanıcının kendi kadrosundan veya tüm listeden seçim yapması
        secenekler = ["Tüm Liste"] + [h['isim'] for h in st.session_state['kadro']]
        secim_kaynagi = st.radio("Saldıran Karakteri Nereden Seçeceksin?", ["Kadromdan", "Tüm Listeden"], horizontal=True)
        
        if secim_kaynagi == "Kadromdan":
            saldıran_listesi = [h['isim'] for h in st.session_state['kadro']]
        else:
            saldıran_listesi = tum_isimler

        secilen_saldiran = st.selectbox("Saldıran Karakteri Seç:", saldıran_listesi, index=None, placeholder="Kiminle saldıracaksın?")

        if st.button("🤖 AI Analiz Başlat", type="primary"):
            if not openai_api_key:
                st.warning("Lütfen sol menüden OpenAI API Key giriniz.")
            elif not secilen_saldiran:
                st.warning("Lütfen bir saldıran karakter seçiniz.")
            else:
                with st.spinner("Yapay Zeka maçı analiz ediyor..."):
                    try:
                        # ChatGPT Bağlantısı
                        client = openai.OpenAI(api_key=openai_api_key)
                        prompt = f"""
                        Marvel Şampiyonlar Turnuvası (MCOC) oyununda bir dövüş analizi yap.
                        
                        Saldıran (Ben): {secilen_saldiran}
                        Savunan (Rakip): {secilen_rakip}
                        
                        Bu eşleşme için bana kısa ve net maddeler halinde taktik ver.
                        1. Saldıranın hangi özelliği rakibi bozar?
                        2. Rakibin hangi özelliğine dikkat etmeliyim?
                        3. Hangi özel saldırıyı (L1/L2/L3) kullanmalıyım?
                        4. Dövüşün püf noktası nedir?
                        
                        Cevabı Türkçe ver ve oyuncu diline (buff, debuff, dex, parry gibi terimlere) uygun olsun.
                        """
                        
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo", # Veya "gpt-4" kullanabilirsin
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        ai_cevabi = response.choices[0].message.content
                        st.markdown("### 💡 AI Taktikleri:")
                        st.markdown(ai_cevabi)
                        
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")

        st.divider()
        st.subheader("✅ Senin Kadron İçin Excel Önerileri")
        # ... (Eski kodun Kadro Hesaplama kısmı buraya gelecek) ...
        # Kodun geri kalanını bozmamak için burayı aşağıya ekliyorum
        
        if not st.session_state['kadro']:
            st.warning("Kadronuz boş! Lütfen 'Kadro Yönetimi' sekmesinden şampiyon ekleyin.")
        else:
            uygun_adaylar = []
            antiler_text = str(rakip_data.get('En İyi 5 Anti (Counter)', ''))

            for hero in st.session_state['kadro']:
                puan = 0
                nedenler = []
                h_isim = hero['isim']
                h_sinif = hero['sinif']
                
                if h_isim in antiler_text:
                    puan += 50
                    nedenler.append("⭐ TAM ANTİ")
                
                if SINIF_AVANTAJI.get(h_sinif) == r_sinif:
                    puan += 20
                    nedenler.append(f"✅ Sınıf Avantajı")
                elif SINIF_AVANTAJI.get(r_sinif) == h_sinif:
                    puan -= 15
                    nedenler.append(f"❌ Sınıf Dezavantajı")
                
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
            
            uygun_adaylar.sort(key=lambda x: x['puan'], reverse=True)

            if not uygun_adaylar:
                st.warning("Kadronuzda uygun counter yok.")
            else:
                for i, aday in enumerate(uygun_adaylar):
                    st.success(f"**{i+1}. {aday['isim']}** ({aday['detay']}) - Puan: {aday['puan']}")
                    st.caption(f"└-> {aday['nedenler']}")

# --- TAB 2: KADRO YÖNETİMİ ---
with tab2:
    st.header("Kadro Düzenle (Kişisel Kayıt)")
    st.caption("Veriler tarayıcınızda saklanır. Sayfayı yenileseniz de silinmez.")
    
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        yeni_isim = st.selectbox("Şampiyon Ekle:", tum_isimler, index=None, placeholder="Seçiniz...")
    with col_k2:
        yeni_yildiz = st.selectbox("Yıldız:", ["7 Yıldız", "6 Yıldız", "5 Yıldız"], index=1)
    with col_k3:
        yeni_rank = st.selectbox("Rank:", ["R5", "R4", "R3", "R2", "R1"], index=0)
        
    if st.button("Kadroya Ekle + Kaydet", type="primary"):
        if yeni_isim:
            var_mi = any(k['isim'] == yeni_isim and k['yildiz'] == yeni_yildiz for k in st.session_state['kadro'])
            if var_mi:
                st.toast("Zaten ekli!", icon="⚠️")
            else:
                sinif = db[yeni_isim].get('Sınıf', 'Bilinmiyor')
                yeni_kayit = {"isim": yeni_isim, "yildiz": yeni_yildiz, "rank": yeni_rank, "sinif": sinif}
                st.session_state['kadro'].append(yeni_kayit)
                kadroyu_cereze_kaydet()
                st.toast(f"{yeni_isim} eklendi! Kaydediliyor...", icon="✅")
                time.sleep(0.5)
                st.rerun()
        else:
            st.toast("İsim seçmediniz.", icon="❌")

    st.divider()
    st.subheader("Mevcut Kadrom")
    
    if st.session_state['kadro']:
        df_kadro = pd.DataFrame(st.session_state['kadro'])
        st.dataframe(df_kadro, use_container_width=True, hide_index=True)
        
        silinecek = st.selectbox("Silmek İçin Seç:", 
                                 [f"{k['isim']} ({k['yildiz']})" for k in st.session_state['kadro']],
                                 index=None)
        
        if silinecek and st.button("Seçileni Sil ve Kaydet"):
            isim_sil, yildiz_sil = silinecek.split(" (")
            yildiz_sil = yildiz_sil.replace(")", "")
            
            st.session_state['kadro'] = [k for k in st.session_state['kadro'] 
                                         if not (k['isim'] == isim_sil and k['yildiz'] == yildiz_sil)]
            
            kadroyu_cereze_kaydet()
            st.success("Silindi!")
            time.sleep(0.5)
            st.rerun()
            
        if st.button("🔄 Kadro Görünmüyorsa Tıkla (Yenile)"):
             st.rerun()
    else:
        st.info("Kadro boş veya yükleniyor...")
