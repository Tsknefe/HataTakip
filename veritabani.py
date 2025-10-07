from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("sqlite:///hata_kayitlari.db")

def kaydet(df):
    veri = df[[
        "Tarih\nDate",
        "Vardiya\nShift",
        "Model No\nModel  No",
        "Seri No\nSerial No",
        "Hata Türü\nFault Type",
        "Ana Konu\nKeyword",
        "Hata Açıklaması Temiz",
        "Platform\nPlatform"
    ]].copy()

    veri.columns = [
        "tarih",
        "vardiya",
        "model_no",
        "seri_no",
        "hata_turu",
        "hata_aciklama",
        "hata_aciklama_temiz",
        "platform"
    ]

    veri.to_sql("hata_kayitlari", engine, if_exists="replace", index=False)
    print("✅ Veritabanına veri kaydedildi.")

def oku(limit=None):
    if limit:
        query = f"SELECT * FROM hata_kayitlari LIMIT {limit}"
    else:
        query = "SELECT * FROM hata_kayitlari"
    return pd.read_sql(query, engine)

