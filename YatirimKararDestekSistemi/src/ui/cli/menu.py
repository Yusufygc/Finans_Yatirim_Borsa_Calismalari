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
        print("      YATIRIM KARAR DESTEK SİSTEMİ - KONSOL ARAYÜZÜ      ")
        print("="*65 + Colors.ENDC)

    # --- YARDIMCI METOTLAR ---
    
    def get_input(self, prompt_text):
        """Temel input alma, 'q' kontrolü yapar."""
        val = input(Colors.BOLD + prompt_text + Colors.ENDC).strip()
        if val.lower() in ['q', 'iptal', 'exit']:
            print(Colors.WARNING + "\nİşlem iptal edildi." + Colors.ENDC)
            sleep(0.5)
            return None
        return val

    def get_valid_number(self, prompt, allow_empty=False, default_val=None):
        """
        Sayısal veri alana kadar döngüde sorar.
        Virgül/Nokta dönüşümünü otomatik yapar.
        """
        while True:
            val = self.get_input(prompt)
            
            # Kullanıcı iptal ettiyse (q)
            if val is None: 
                return None
            
            # Boş geçişe izin varsa (Örn: Fiyat için varsayılan değer)
            if allow_empty and val == "":
                return default_val

            try:
                # Virgülü noktaya çevir ve float yap
                num = float(val.replace(',', '.'))
                if num <= 0:
                    print(Colors.FAIL + "  -> Lütfen 0'dan büyük bir değer giriniz." + Colors.ENDC)
                    continue
                return num
            except ValueError:
                print(Colors.FAIL + "  -> Hatalı format! Lütfen sayısal bir değer giriniz." + Colors.ENDC)

    def get_valid_date(self, prompt):
        """
        Geçerli tarih formatı (YYYY-AA-GG) alana kadar döngüde sorar.
        """
        while True:
            date_str = self.get_input(prompt)
            if date_str is None: return None

            try:
                # Tarih formatı kontrolü
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print(Colors.FAIL + "  -> Hatalı format! Lütfen YYYY-AA-GG şeklinde giriniz (Örn: 2023-12-25)." + Colors.ENDC)

    def check_market_status(self):
        """Piyasa kapalıysa tarih girmeye zorlar, hatalı tarihte tekrar sorar."""
        now = datetime.now()
        is_weekend = now.weekday() >= 5 
        
        current_time = now.time()
        market_open = time(10, 0)
        market_close = time(18, 5) 
        is_off_hours = not (market_open <= current_time <= market_close)

        if is_weekend or is_off_hours:
            print(Colors.FAIL + "\n[UYARI] Şu an piyasalar KAPALI." + Colors.ENDC)
            
            while True:
                choice = self.get_input("Bu geçmiş tarihli bir işlem mi? (E/H): ")
                if choice is None: return "CANCEL" # q ile çıkış
                
                if choice.upper() == 'E':
                    # Tarih alma döngüsü (Hata yaparsa tekrar sorar)
                    custom_date = self.get_valid_date("İşlem Tarihi (YYYY-AA-GG): ")
                    if custom_date is None: return "CANCEL" # q ile çıkış
                    return custom_date
                
                elif choice.upper() == 'H':
                    print(Colors.WARNING + "Piyasa kapalıyken canlı işlem yapılamaz." + Colors.ENDC)
                    return "CANCEL"
                else:
                    print("Lütfen 'E' veya 'H' giriniz.")
        
        return None # Piyasa açık, None dönmesi "ŞİMDİ" demektir.

    def print_mini_portfolio(self):
        """İşlem yaparken üstte özet portföyü gösterir."""
        report = self.analysis_service.calculate_portfolio_performance(self.user_id)
        print(Colors.CYAN + "\n--- GÜNCEL PORTFÖYÜNÜZ ---" + Colors.ENDC)
        if not report["positions"]:
            print("Portföyünüz boş.")
        else:
            for pos in report["positions"]:
                pl_color = Colors.GREEN if pos['pl'] >= 0 else Colors.FAIL
                print(f"• {pos['symbol']:<6}: {pos['quantity']:<6} Adet | Mal: {pos['avg_cost']:<8.2f} | Fiyat: {pos['current_price']:<8.2f} | K/Z: {pl_color}{pos['pl']:<8.2f}{Colors.ENDC}")
        print("-" * 65 + "\n")

    # --- MENÜ FONKSİYONLARI ---

    def trade_flow(self, side="BUY"):
        """Alım ve Satım akışı - Sembol Doğrulamalı"""
        self.show_header()
        action_name = "ALIM" if side == "BUY" else "SATIŞ"
        print(Colors.BLUE + f">> HİSSE {action_name} İŞLEMİ" + Colors.ENDC)
        print(Colors.WARNING + "(Ana menüye dönmek için 'q' yazın)" + Colors.ENDC)

        # 1. Portföyü Göster
        self.print_mini_portfolio()

        # --- GÜNCELLEME: SEMBOL DOĞRULAMA DÖNGÜSÜ ---
        # Geçerli bir hisse bulana kadar döngüden çıkmaz.
        valid_ticker_info = None
        symbol = ""
        
        while True:
            symbol = self.get_input("Hisse Sembolü (Örn: ASELS): ")
            if not symbol: return # q ile çıkış

            symbol = symbol.upper()
            
            print("Kontrol ediliyor...", end="\r") # Satır başı yapar
            ticker_info = self.market_service.get_ticker_info(symbol)
            
            if ticker_info:
                # Başarılı ise döngüden çık ve bilgiyi sakla
                valid_ticker_info = ticker_info
                current_price = ticker_info['close']
                print(Colors.GREEN + f"✅ {symbol} Bulundu: {current_price:.2f} TL ({ticker_info['date']})" + Colors.ENDC)
                break 
            else:
                # Başarısız ise uyarı ver ve döngü başa döner
                print(Colors.FAIL + f"❌ '{symbol}' bulunamadı veya veri çekilemedi. Tekrar deneyin." + Colors.ENDC)
        # ----------------------------------------------

        # 3. Piyasa Kontrolü (Tarih için)
        trade_date = self.check_market_status()
        if trade_date == "CANCEL": return

        # 4. Miktar Girişi
        qty = self.get_valid_number("Adet: ")
        if qty is None: return 

        # 5. Fiyat Girişi
        current_price = valid_ticker_info['close']
        default_price_str = f" ({current_price:.2f})"
        
        price = self.get_valid_number(
            f"İşlem Fiyatı{default_price_str}: ", 
            allow_empty=True, 
            default_val=current_price
        )
        if price is None: return

        # Onay İste
        print(Colors.WARNING + f"\nÖZET: {symbol} - {qty} Adet x {price} TL" + Colors.ENDC)
        if trade_date:
            print(f"Tarih: {trade_date.strftime('%Y-%m-%d')}")
        
        confirm = self.get_input("Onaylıyor musunuz? (E/H): ")
        if not confirm or confirm.upper() != 'E': return

        # 6. İşlemi Gerçekleştir
        if side == "BUY":
            result = self.trade_service.execute_buy(self.user_id, symbol, qty, price, custom_date=trade_date)
        else:
            result = self.trade_service.execute_sell(self.user_id, symbol, qty, price, custom_date=trade_date)

        if result["status"] == "success":
            print(Colors.GREEN + f"\n[BAŞARILI] {result['message']}" + Colors.ENDC)
            # Eğer geçmiş tarihli değilse hemen güncelle
            if not trade_date:
                print(f"[SİSTEM] {symbol} verileri güncelleniyor...")
                self.market_service.update_price_history(symbol)
        else:
            print(Colors.FAIL + f"\n[HATA] {result['message']}" + Colors.ENDC)
        
        input("\nDevam etmek için Enter...")

    def show_portfolio(self):
        self.show_header()
        print(Colors.BLUE + ">> DETAYLI PORTFÖY RAPORU" + Colors.ENDC)
        
        print("Piyasa verileri güncelleniyor, lütfen bekleyin...")
        self.market_service.update_all_tickers() 

        report = self.analysis_service.calculate_portfolio_performance(self.user_id)
        
        print(f"\nToplam Değer : {report['total_value']:.2f} TL")
        print(f"Toplam Maliyet: {report['total_cost']:.2f} TL")
        
        pl_color = Colors.GREEN if report['total_pl'] >= 0 else Colors.FAIL
        print(f"Kar/Zarar    : {pl_color}{report['total_pl']:.2f} TL (%{report['pl_percentage']:.2f}){Colors.ENDC}\n")
        
        print("-" * 85)
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