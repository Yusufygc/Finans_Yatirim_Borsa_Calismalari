import sys
import os
from time import sleep
from datetime import datetime, time

# Konsol Renkleri
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ConsoleMenu:
    def __init__(self, db_session, user_id):
        self.db = db_session
        self.user_id = user_id
        
        from src.services.trade_engine import TradeService
        from src.services.market_data import MarketDataService
        from src.services.analysis_service import AnalysisService
        
        self.trade_service = TradeService(self.db)
        self.market_service = MarketDataService(self.db)
        self.analysis_service = AnalysisService(self.db)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_header(self):
        self.clear_screen()
        print(Colors.HEADER + "="*65)
        print("      YATIRIM KARAR DESTEK SİSTEMİ (v2.2 - Live Update)")
        print("="*65 + Colors.ENDC)

    # --- YARDIMCI METOTLAR ---
    
    def get_input(self, prompt_text):
        """Kullanıcıdan veri alır, 'q' veya 'iptal' girerse None döner."""
        val = input(Colors.BOLD + prompt_text + Colors.ENDC).strip()
        if val.lower() in ['q', 'iptal', 'exit']:
            print(Colors.WARNING + "\nİşlem iptal edildi." + Colors.ENDC)
            sleep(0.8)
            return None
        return val

    def check_market_status(self):
        """Piyasa açık mı kontrol eder? Değilse tarih girmesini ister."""
        now = datetime.now()
        is_weekend = now.weekday() >= 5 # 5=Cmt, 6=Paz
        
        # Basit saat kontrolü (10:00 - 18:05 arası açık varsayalım)
        current_time = now.time()
        market_open = time(10, 0)
        market_close = time(18, 5) 
        is_off_hours = not (market_open <= current_time <= market_close)

        if is_weekend or is_off_hours:
            print(Colors.FAIL + "\n[UYARI] Şu an piyasalar KAPALI." + Colors.ENDC)
            print("Bu işlemi şu an canlı yapamazsınız.")
            choice = self.get_input("Bu geçmiş tarihli bir işlem mi? (E/H): ")
            
            if choice and choice.upper() == 'E':
                date_str = self.get_input("İşlem Tarihi (YYYY-AA-GG): ")
                if not date_str: return "CANCEL"
                try:
                    custom_date = datetime.strptime(date_str, "%Y-%m-%d")
                    return custom_date
                except ValueError:
                    print("Hatalı tarih formatı!")
                    return "CANCEL"
            else:
                return "CANCEL"
        
        return None # Piyasa açık, None dönmesi "ŞİMDİ" demektir.

    def print_mini_portfolio(self):
        """İşlem yaparken üstte özet portföyü gösterir."""
        # Burada update yapmıyoruz ki işlem ekranı hızlı açılsın
        report = self.analysis_service.calculate_portfolio_performance(self.user_id)
        print(Colors.CYAN + "\n--- GÜNCEL PORTFÖYÜNÜZ ---" + Colors.ENDC)
        if not report["positions"]:
            print("Portföyünüz boş.")
        else:
            for pos in report["positions"]:
                # Kar/Zarar Renklendirme
                pl_color = Colors.GREEN if pos['pl'] >= 0 else Colors.FAIL
                print(f"• {pos['symbol']:<6}: {pos['quantity']:<6} Adet | Mal: {pos['avg_cost']:<8.2f} | Fiyat: {pos['current_price']:<8.2f} | K/Z: {pl_color}{pos['pl']:<8.2f}{Colors.ENDC}")
        print("-" * 65 + "\n")

    # --- MENÜ FONKSİYONLARI ---

    def trade_flow(self, side="BUY"):
        """Alım ve Satım için ortak akış"""
        self.show_header()
        action_name = "ALIM" if side == "BUY" else "SATIŞ"
        print(Colors.BLUE + f">> HİSSE {action_name} İŞLEMİ" + Colors.ENDC)
        print(Colors.WARNING + "(Ana menüye dönmek için 'q' yazın)" + Colors.ENDC)

        # 1. Portföyü Göster
        self.print_mini_portfolio()

        # 2. Hisse Sembolü İste & Fiyat Göster
        symbol = self.get_input("Hisse Sembolü (Örn: ASELS): ")
        if not symbol: return

        symbol = symbol.upper()
        
        print("\nFiyat bilgisi alınıyor...")
        ticker_info = self.market_service.get_ticker_info(symbol)
        
        current_price = 0.0
        if ticker_info:
            current_price = ticker_info['close']
            print(Colors.GREEN + f"✅ {symbol} Son Fiyat: {current_price:.2f} TL (Tarih: {ticker_info['date']})" + Colors.ENDC)
        else:
            print(Colors.FAIL + "⚠️ Fiyat bilgisi çekilemedi veya sembol hatalı." + Colors.ENDC)

        # 3. Piyasa Kontrolü (Haftasonu/Gece Engeli)
        trade_date = self.check_market_status()
        if trade_date == "CANCEL": return

        # 4. Miktar ve Fiyat Girişi
        try:
            qty_str = self.get_input("Adet: ")
            if not qty_str: return
            
            # --- DÜZELTME BURADA: Virgülü noktaya çeviriyoruz ---
            qty = float(qty_str.replace(',', '.')) 

            default_price_str = f" ({current_price:.2f})" if current_price > 0 else ""
            price_str = self.get_input(f"İşlem Fiyatı{default_price_str}: ")
            
            if not price_str and current_price > 0:
                price = current_price
            elif not price_str:
                 print("Fiyat girmelisiniz!")
                 return
            else:
                # --- DÜZELTME BURADA: Virgülü noktaya çeviriyoruz ---
                price = float(price_str.replace(',', '.'))

            # Onay İste
            print(Colors.WARNING + f"\nÖZET: {symbol} - {qty} Adet x {price} TL" + Colors.ENDC)
            if trade_date:
                print(f"Tarih: {trade_date.strftime('%Y-%m-%d')}")
            
            confirm = self.get_input("Onaylıyor musunuz? (E/H): ")
            if not confirm or confirm.upper() != 'E': return

            # 5. İşlemi Gerçekleştir
            if side == "BUY":
                result = self.trade_service.execute_buy(self.user_id, symbol, qty, price, custom_date=trade_date)
            else:
                result = self.trade_service.execute_sell(self.user_id, symbol, qty, price, custom_date=trade_date)

            if result["status"] == "success":
                print(Colors.GREEN + f"\n[BAŞARILI] {result['message']}" + Colors.ENDC)
                
                print(f"[SİSTEM] {symbol} için güncel veriler indiriliyor...")
                self.market_service.update_price_history(symbol)
                
            else:
                print(Colors.FAIL + f"\n[HATA] {result['message']}" + Colors.ENDC)

        except ValueError:
            print(Colors.FAIL + "Hatalı sayısal değer girdiniz! (Lütfen sadece rakam kullanın)" + Colors.ENDC)
        
        input("\nDevam etmek için Enter...")

    def show_portfolio(self):
        self.show_header()
        print(Colors.BLUE + ">> DETAYLI PORTFÖY RAPORU" + Colors.ENDC)
        
        # --- DÜZELTME: Bu satırı aktifleştirdik ---
        print("Piyasa verileri güncelleniyor, lütfen bekleyin...")
        self.market_service.update_all_tickers() 
        # ------------------------------------------

        report = self.analysis_service.calculate_portfolio_performance(self.user_id)
        
        print(f"\nToplam Değer  : {report['total_value']:.2f} TL")
        print(f"Toplam Maliyet  : {report['total_cost']:.2f} TL")
        
        pl_color = Colors.GREEN if report['total_pl'] >= 0 else Colors.FAIL
        print(f"Kar/Zarar       : {pl_color}{report['total_pl']:.2f} TL (%{report['pl_percentage']:.2f}){Colors.ENDC}\n")
        
        print("-" * 85)
        # Tablo başlıklarını hizaladık
        print(f"{'HİSSE':<10} {'ADET':<10} {'MALİYET':<12} {'GÜNCEL':<12} {'DEĞER':<15} {'K/Z':<12}")
        print("-" * 85)
        
        for pos in report["positions"]:
            p_color = Colors.GREEN if pos['pl'] >= 0 else Colors.FAIL
            print(f"{pos['symbol']:<10} {pos['quantity']:<10.1f} {pos['avg_cost']:<12.2f} {pos['current_price']:<12.2f} {pos['market_value']:<15.2f} {p_color}{pos['pl']:<12.2f}{Colors.ENDC}")
        
        input("\nAna menüye dönmek için Enter...")

    def ai_analysis_menu(self):
        self.show_header()
        print(Colors.BLUE + ">> AI ANALİZ & TAHMİN" + Colors.ENDC)
        print(Colors.WARNING + "(Çıkış için 'q')" + Colors.ENDC)

        symbol = self.get_input("Analiz edilecek hisse (Örn: THYAO): ")
        if not symbol: return
        symbol = symbol.upper()

        # Veri kontrolü ve güncelleme
        self.market_service.update_price_history(symbol)
        
        print("\nAnaliz yapılıyor, modeller çalıştırılıyor...")
        prediction = self.analysis_service.run_prediction(symbol)
        
        if prediction:
            print(Colors.GREEN + "\n" + "*"*40)
            print(f" TAHMİN RAPORU: {symbol}")
            print("*"*40)
            print(f"Mevcut Fiyat  : ...") 
            print(f"Hedef Fiyat   : {prediction.predicted_price:.2f} TL (T+1)")
            print(f"Model Sinyali : {prediction.signal}")
            print(f"Güven Skoru   : %{float(prediction.confidence_score)*100:.1f}")
            print("*"*40 + Colors.ENDC)
        else:
            print(Colors.FAIL + "\nAnaliz başarısız oldu." + Colors.ENDC)
        
        input("\nDevam...")

    def main_loop(self):
        while True:
            self.show_header()
            print("1. Portföyümü Göster")
            print("2. Hisse Al")
            print("3. Hisse Sat")
            print("4. AI Analiz (Tahmin)")
            print("5. Piyasa Verilerini Güncelle (Manuel)")
            print("6. Çıkış")
            
            choice = input("\nSeçiminiz: ").strip()
            
            if choice == '1':
                self.show_portfolio()
            elif choice == '2':
                self.trade_flow(side="BUY")
            elif choice == '3':
                self.trade_flow(side="SELL")
            elif choice == '4':
                self.ai_analysis_menu()
            elif choice == '5':
                 print("Tüm hisseler güncelleniyor...")
                 self.market_service.update_all_tickers()
                 input("\nTamamlandı. Enter...")
            elif choice == '6':
                print("Çıkış yapılıyor...")
                break
            else:
                pass