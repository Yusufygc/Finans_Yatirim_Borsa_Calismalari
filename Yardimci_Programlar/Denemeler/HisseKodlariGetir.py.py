import requests
import pandas as pd
import os
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def save_to_csv(stock_list, source_name):
    """Listeyi CSV'ye kaydeder"""
    if not stock_list:
        print(f"⚠️ {source_name} listesi boş geldi, kaydedilmedi.")
        return False

    folder_name = "Veriler"
    file_name = "KAP_Tum_Sirket_Kodlari2.csv"
    full_path = os.path.join(folder_name, file_name)

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Tekrarlananları temizle ve sırala
    stock_list = sorted(list(set(stock_list)))
    
    df = pd.DataFrame(stock_list, columns=["Symbol"])
    df.to_csv(full_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ BAŞARILI! {source_name} kaynağından {len(stock_list)} adet hisse çekildi.")
    print(f"Dosya şuraya kaydedildi: {full_path}")
    return True

def get_stocks_from_tradingview():
    """YÖNTEM 1: TradingView (Genişletilmiş Sorgu)"""
    print("1. Yöntem: TradingView deneniyor...")
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # En basit sorgu: Türkiye piyasasındaki tüm hisseleri ("stock") getir
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]},
            {"left": "exchange", "operation": "equal", "right": "BIST"} 
        ],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "close", "volume", "type"],
        "sort": {"sortBy": "name", "sortOrder": "asc"},
        "range": [0, 600] # İlk 600 hisseyi al
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        stock_list = []
        if 'data' in data:
            for item in data['data']:
                # Sembol genellikle "BIST:THYAO" formatındadır, sadece "THYAO" kısmını alalım
                symbol_raw = item['d'][0]
                if ":" in symbol_raw:
                    symbol = symbol_raw.split(":")[1]
                else:
                    symbol = symbol_raw
                
                # VARANTLARI ELEMEK İÇİN BASİT FİLTRE:
                # Genellikle hisse kodları 5 karakterden uzun olmaz ve rakam içermez (İstisnalar hariç)
                # Ancak fonlar vs. 5 karakter olabilir. Şimdilik hepsini alıyoruz.
                stock_list.append(symbol)
        
        if len(stock_list) > 10: # En az 10 hisse bulduysa başarılı say
            return save_to_csv(stock_list, "TradingView")
        else:
            print("TradingView 0 veya çok az veri döndürdü.")
            return False

    except Exception as e:
        print(f"TradingView Hatası: {e}")
        return False

def get_stocks_from_github_backup():
    """YÖNTEM 2: Github'daki Açık Kaynaklı Listelerden Çekme (En Garantisi)"""
    print("\n2. Yöntem: Github (Yedek Liste) deneniyor...")
    
    # Burası BIST hisselerini tutan popüler bir repodan ham veri (Burak Demirci'nin veya benzeri repolar)
    # Eğer bu link çalışmazsa, alternatif bir statik liste kullanılabilir.
    # Örnek olarak TradingView python kütüphanesinin kullandığı veri setine benzer bir yapı deniyoruz
    # Veya güvenilir bir BIST listesi raw url:
    
    url = "https://raw.githubusercontent.com/dursunokyay/Bist-Hisse-Kodlari/main/hisse_kodlari.txt" 
    # Not: Eğer yukarıdaki URL çalışmazsa kendi oluşturduğumuz statik listeyi devreye sokabiliriz.
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            # Satır satır ayır ve temizle
            stock_list = [line.strip() for line in content.splitlines() if line.strip()]
            
            if len(stock_list) > 50:
                return save_to_csv(stock_list, "Github Yedek")
    except Exception:
        pass
    
    print("Github yedek listesine ulaşılamadı.")
    return False

def get_stocks_from_isyatirim():
    """YÖNTEM 3: İş Yatırım (SSL Atlatmalı)"""
    print("\n3. Yöntem: İş Yatırım (Güçlendirilmiş) deneniyor...")
    url = "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/HisseTekil"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            stock_list = [item['code'] for item in data['value']]
            if len(stock_list) > 10:
                return save_to_csv(stock_list, "İş Yatırım")
    except Exception as e:
        print(f"İş Yatırım Hatası: {e}")
    
    return False

def create_emergency_list():
    """HİÇBİRİ ÇALIŞMAZSA: En bilinen 30 hisseyi manuel oluştur"""
    print("\n⚠️ Tüm yöntemler başarısız oldu. Manuel BIST30 listesi oluşturuluyor...")
    bist30 = ["AKBNK","ALARK","ARCLK","ASELS","ASTOR","BIMAS","BRSAN","DOHOL","EKGYO","ENKAI",
              "EREGL","FROTO","GARAN","GUBRF","HEKTS","ISCTR","KCHOL","KONTR","KOZAL","KRDMD",
              "ODAS","OYAKC","PETKM","PGSUS","SAHOL","SASA","SISE","TCELL","THYAO","TOASO",
              "TSKB","TTKOM","TUPRS","VESTL","YKBNK"]
    save_to_csv(bist30, "Acil Durum Listesi (BIST30)")

# --- ANA PROGRAM ---
if __name__ == "__main__":
    # Sırayla dene, biri başarılı olursa dur.
    if get_stocks_from_tradingview():
        pass
    elif get_stocks_from_github_backup():
        pass
    elif get_stocks_from_isyatirim():
        pass
    else:
        create_emergency_list()