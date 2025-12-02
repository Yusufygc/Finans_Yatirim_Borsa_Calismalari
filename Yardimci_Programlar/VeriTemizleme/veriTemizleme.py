import pandas as pd

# --- 1. Dosyayı oku ---
df = pd.read_excel("VeriTemizleme/Sirketler_temiz.xlsx")

# --- 2. Sütun adını 'Kod' olarak belirle (bazı Excel'lerde "Unnamed: 0" olabilir) ---
df.columns = ["Kod", "Şirket Ünvanı", "Şehir", "Bağımsız Denetim Kuruluşu"]

# --- 3. Gereksiz satırları filtrele ---
df = df[df["Kod"].notna()]                     # boş olanları çıkar
df = df[df["Kod"].str.len() > 1]               # tek harfli olanları çıkar
df = df[~df["Kod"].isin(["Kod", "Şirketler Listesi"])]

# --- 4. Sadece Kod sütununu seç ---
codes = df[["Kod"]]

# --- 5. CSV olarak kaydet ---
codes.to_csv("Sirket_Kodlari.csv", index=False)

print("✅ Sadece hisse kodlarını içeren 'Sirket_Kodlari.csv' oluşturuldu!")
