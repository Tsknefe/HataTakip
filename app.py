import streamlit as st
import pandas as pd
from temizleyici import temizle
import veritabani
from datetime import datetime, timedelta

st.set_page_config(page_title="Hata Takip Paneli", layout="wide")
st.title(" Hata Takip ve Raporlama")

# NaN ve anlamsız değerleri temizleyen yardımcı fonksiyon
def temizle_nan(series):
    temiz = (
        series.astype(str)
        .str.strip()
        .replace(["", "nan", "NaN", "None", "NONE", "NAN"], pd.NA)
        .dropna()
    )
    return temiz

# Excel Yükleme
uploaded_file = st.file_uploader("Excel Dosyası Yükle (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, header=5)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df.dropna(how="all")  # Tüm satırı boş olanları sil

    if "Tarih\nDate" in df.columns:
        df["Tarih\nDate"] = pd.to_datetime(df["Tarih\nDate"], errors="coerce")

        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str)

        if "Ana Konu\nKeyword" in df.columns:
            df["Hata Açıklaması Temiz"] = df["Ana Konu\nKeyword"].apply(temizle)
        else:
            df["Hata Açıklaması Temiz"] = ""

        veritabani.kaydet(df)
        st.success(" Veri başarıyla kaydedildi!")
        st.subheader(" Yüklenen Veriler")
        st.dataframe(df)
    else:
        st.error(" Excel dosyasında 'Tarih\\nDate' sütunu bulunamadı.")

# Veritabanından veri çek
df_kontrol = veritabani.oku(limit=5)
df_tum = veritabani.oku()

st.subheader(" Son 5 Kayıt")
st.dataframe(df_kontrol)

# Hata Türü Dağılımı
st.subheader(" Hata Türü Dağılımı")
if not df_tum.empty and "hata_turu" in df_tum.columns:
    sayim = temizle_nan(df_tum["hata_turu"]).value_counts()
    st.bar_chart(sayim)

# Model Bazlı Hata
st.subheader(" Model Bazlı Hata Sayıları")
if "model_no" in df_tum.columns:
    model_sayim = temizle_nan(df_tum["model_no"]).value_counts()
    st.bar_chart(model_sayim)

# Platform Bazlı Hata
st.subheader(" Platform Bazlı Hata Dağılımı")
if "platform" in df_tum.columns:
    platform_sayim = temizle_nan(df_tum["platform"]).value_counts()
    st.bar_chart(platform_sayim)

# En Sık Görülen Hata Açıklamaları
st.subheader(" En Sık Görülen Hata Açıklamaları")
if "hata_aciklama_temiz" in df_tum.columns:
    aciklama_sayim = temizle_nan(df_tum["hata_aciklama_temiz"]).value_counts().head(10)
    st.table(aciklama_sayim)

# Aksiyon Önerileri
st.subheader(" Aksiyon Önerileri")
df_tum["tarih"] = pd.to_datetime(df_tum.get("tarih", pd.NaT), errors="coerce")

if not df_tum.empty and "hata_turu" in df_tum.columns:
    bugun = datetime.now()
    son_30_gun = bugun - timedelta(days=30)
    onceki_30_gun = bugun - timedelta(days=60)

    df_son30 = df_tum[df_tum["tarih"] >= son_30_gun]
    df_onceki30 = df_tum[(df_tum["tarih"] >= onceki_30_gun) & (df_tum["tarih"] < son_30_gun)]

    son30_sayim = temizle_nan(df_son30["hata_turu"]).value_counts()
    onceki30_sayim = temizle_nan(df_onceki30["hata_turu"]).value_counts()

    aksiyon_listesi = []

    for hata_turu in son30_sayim.index:
        yeni_adet = son30_sayim[hata_turu]
        eski_adet = onceki30_sayim.get(hata_turu, 0)

        artis_oran = 100 if eski_adet == 0 else ((yeni_adet - eski_adet) / eski_adet) * 100

        if artis_oran >= 30:
            aksiyon_listesi.append(
                f" **{hata_turu}** hata tipi son 30 günde %{artis_oran:.1f} artmış. Kontrol sıklığını artırın."
            )

    if aksiyon_listesi:
        for öneri in aksiyon_listesi:
            st.warning(öneri)
    else:
        st.success(" Son 30 günde belirgin bir artış tespit edilmedi.")

# Basit Tahmin
st.subheader(" Basit Hata Tahmini (Sonraki 30 Gün)")
if not df_tum.empty and "tarih" in df_tum.columns:
    gunluk = df_tum.groupby("tarih").size().reset_index(name="adet")
    gunluk = gunluk.sort_values("tarih")

    if len(gunluk) >= 2:
        gunluk["fark"] = gunluk["adet"].diff()
        ortalama_artis = gunluk["fark"].mean()

        son_tarih = gunluk["tarih"].max()
        son_adet = gunluk["adet"].iloc[-1]

        tahminler = []
        for i in range(1, 31):
            yeni_tarih = son_tarih + timedelta(days=i)
            yeni_adet = max(son_adet + ortalama_artis * i, 0)
            tahminler.append({"tarih": yeni_tarih, "tahmini_adet": yeni_adet})

        df_tahmin = pd.DataFrame(tahminler)

        grafik_df = pd.concat([
            gunluk[["tarih", "adet"]].rename(columns={"adet": "gercek"}),
            df_tahmin.rename(columns={"tahmini_adet": "gercek"})
        ])

        st.line_chart(grafik_df.set_index("tarih"))
        st.info(" Gerçek kayıtlar —  Tahmin edilen değerler")
    else:
        st.warning(" Tahmin yapabilmek için yeterli veri yok.")
