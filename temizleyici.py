import re
import pandas as pd

def temizle(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = text.replace("ç", "c").replace("ğ", "g").replace("ı", "i").replace("ö", "o").replace("ş", "s").replace("ü", "u")
    text = re.sub(r"[^\w\s]", "", text)  # noktalama temizle
    text = re.sub(r"\s+", " ", text)     # fazla boşlukları teke indir
    return text.strip()
