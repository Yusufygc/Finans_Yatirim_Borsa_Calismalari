import sys
import os
from time import sleep
from datetime import datetime, time, date

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
        
        # Servisleri Dahil Et
        from src.services.trade_engine import TradeService
        from src.services.market_data import MarketDataService
        from src.services.analysis_service import AnalysisService
        from src.services.portfolio_analytics import PortfolioAnalyticsService  # <-- YENİ
        from src.services.visualization import PortfolioVisualizationService
        
        self.trade_service = TradeService(self.db)
        self.market_service = MarketDataService(self.db)
        self.analysis_service = AnalysisService(self.db)
        self.analytics_service = PortfolioAnalyticsService(self.db) # <-- YENİ
        self.viz_service = PortfolioVisualizationService(self.db)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_header(self):
        self.clear_screen()
        print(Colors.HEADER + "="*70)
        print("      YATIRIM KARAR DESTEK SİSTEMİ (v2.4 - Pro Analytics)")
        print("="*70 + Colors.ENDC)

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
        while True:
            val = self.get_input(prompt)
            if val is None: return None
            
            if allow_empty and val == "":
                return default_val

            try:
                num = float(val.replace(',', '.'))
                if num <= 0:
                    print(Colors.FAIL + "  -> Lütfen 0'dan büyük bir değer giriniz." + Colors.ENDC)
                    continue
                return num
            except ValueError:
                print(Colors.FAIL + "  -> Hatalı format! Sayısal değer giriniz." + Colors.ENDC)

    def check_market_status(self):
        """
        Piyasa kontrolü yapar. 
        Geçmiş tarih girilirse Hafta Sonu ve Gelecek Tarih kontrolü de yapar.
        """
        now = datetime.now()
        is_weekend = now.weekday() >= 5 
        
        current_time = now.time()
        market_open = time(10, 0)
        market_close = time(18, 5) 
        is_off_hours = not (market_open <= current_time <= market_close)

        # Eğer şu an piyasa kapalıysa veya hafta sonuysa
        if is_weekend or is_off_hours:
            print(Colors.FAIL + "\n[UYARI] Şu an piyasalar KAPALI." + Colors.ENDC)
            
            while True:
                choice = self.get_input("Bu geçmiş tarihli bir işlem mi? (E/H): ")
                if choice is None: return "CANCEL"
                
                if choice.upper() == 'E':
                    while True:
                        date_str = self.get_input("İşlem Tarihi (YYYY-AA-GG): ")
                        if date_str is None: return "CANCEL"
                        try:
                            custom_date = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            # KONTROL 1: GELECEK TARİH ENGELLİ
                            if custom_date.date() > date.today():
                                print(Colors.FAIL + "  -> Hata: Geleceğe işlem giremezsiniz!" + Colors.ENDC)
                                continue

                            # KONTROL 2: HAFTA SONU ENGELLİ
                            # weekday(): 0=Pzt ... 5=Cmt, 6=Paz
                            if custom_date.weekday() >= 5:
                                day_name = "Cumartesi" if custom_date.weekday() == 5 else "Pazar"
                                print(Colors.FAIL + f"  -> Hata: {day_name} günü borsa kapalıdır. İşlem girilemez." + Colors.ENDC)
                                continue
                            
                            return custom_date

                        except ValueError:
                            print(Colors.FAIL + "  -> Hatalı tarih formatı! YYYY-AA-GG (Örn: 2023-12-25)" + Colors.ENDC)
                
                elif choice.upper() == 'H':
                    return "CANCEL"
                else:
                    print("Lütfen 'E' veya 'H' giriniz.")
        
        return None
    
    def print_mini_portfolio(self):
        """İşlem ekranında özet bilgi."""
        # Portföy verisini çek
        report = self.analysis_service.calculate_portfolio_performance(self.user_id)
        
        print(Colors.CYAN + "\n--- GÜNCEL VARLIKLAR ---" + Colors.ENDC)
        if not report["positions"]:
            print("Portföyünüz boş.")
        else:
            for pos in report["positions"]:
                pl_color = Colors.GREEN if pos['pl'] >= 0 else Colors.FAIL
                print(f"• {pos['symbol']:<6}: {pos['quantity']:<6} Adet | Mal: {pos['avg_cost']:<8.2f} | K/Z: {pl_color}{pos['pl']:<8.2f}{Colors.ENDC}")
        print("-" * 65 + "\n")
        
        # --- KRİTİK DÜZELTME BURADA ---
        # Portföydeki hisseleri ve adetlerini bir sözlük olarak döndür
        # Örnek Çıktı: {'ASELS': 100.0, 'THYAO': 50.0}
        owned_stocks = {pos['symbol']: float(pos['quantity']) for pos in report["positions"]}
        return owned_stocks

    # --- YENİLENEN PORTFÖY EKRANI ---

    def show_portfolio(self):
        self.show_header()
        print(Colors.BLUE + ">> DETAYLI PORTFÖY ANALİZİ" + Colors.ENDC)
        
        print("Piyasa verileri güncelleniyor ve analiz yapılıyor...")
        self.market_service.update_all_tickers() 

        # Yeni Analytics Servisini Çağırıyoruz
        dashboard = self.analytics_service.generate_dashboard(self.user_id)
        
        if "error" in dashboard:
            print(Colors.FAIL + f"\n[HATA] {dashboard['error']}" + Colors.ENDC)
            input("\nDevam...")
            return

        summ = dashboard["summary"]
        stats = dashboard["performance_stats"]

        # 1. ÖZET KART
        print("\n" + Colors.HEADER + "┌" + "─"*68 + "┐" + Colors.ENDC)
        print(f"{Colors.HEADER}│{Colors.ENDC} TOPLAM VARLIK: {Colors.BOLD}{summ['total_value']:>15,.2f} TL{Colors.ENDC} {Colors.HEADER}│{Colors.ENDC}")
        
        # Renklendirme Fonksiyonu
        def color_pct(val):
            c = Colors.GREEN if val >= 0 else Colors.FAIL
            return f"{c}%{val:.2f}{Colors.ENDC}"

        print(f"{Colors.HEADER}│{Colors.ENDC} Günlük: {color_pct(summ['daily_return']):<15} Haftalık: {color_pct(summ['weekly_return']):<15} Aylık: {color_pct(summ['monthly_return']):<10} {Colors.HEADER}│{Colors.ENDC}")
        print(Colors.HEADER + "└" + "─"*68 + "┘" + Colors.ENDC)

        # 2. EN İYİ / EN KÖTÜ (Güncellendi)
        if stats:
            # Servisten gelen etiketi ve durumu al
            w_label = stats.get("worst_label", "Kaybettiren")
            w_is_loss = stats.get("worst_is_loss", True)
            
            # Eğer zararsa KIRMIZI, karsa (ama azsa) SARI renk kullan
            w_color = Colors.FAIL if w_is_loss else Colors.WARNING
            
            print(f"\n🏆 Şampiyon: {Colors.GREEN}{stats['best_performer']}{Colors.ENDC} | 📉 {w_label}: {w_color}{stats['worst_performer']}{Colors.ENDC}")
        
        # 3. VARLIK DAĞILIMI
        print(f"\n{Colors.CYAN}[VARLIK DAĞILIMI]{Colors.ENDC}")
        for item in dashboard["allocation"]:
            bar_len = int(item['weight'] / 5) # Basit bir bar grafiği
            bar = "█" * bar_len
            print(f" {item['symbol']:<6} : {bar} %{item['weight']:.1f} ({item['value']:,.2f} TL)")

        # 4. DETAYLI LOT ANALİZİ (Parçalı Maliyet)
        print(f"\n{Colors.CYAN}[PARÇALI MALİYET VE KAR/ZARAR ANALİZİ]{Colors.ENDC}")
        print("-" * 70)
        
        for lot in dashboard["lot_breakdown"]:
            # Hisse Başlığı
            pl_color = Colors.GREEN if lot['avg_pl_percent'] >= 0 else Colors.FAIL
            print(f"{Colors.BOLD}{lot['symbol']}{Colors.ENDC} | Ort. Mal: {lot['avg_cost']:.2f} | Güncel: {lot['current_price']:.2f} | Genel P/L: {pl_color}%{lot['avg_pl_percent']:.2f}{Colors.ENDC}")
            
            # İşlem Detayları
            print(f"   {'TARİH':<12} {'ADET':<8} {'ALIŞ F.':<10} {'DURUM':<10} {'KAR/ZARAR'}")
            for tx in lot["transactions"]:
                tx_color = Colors.GREEN if tx['pl_percent'] >= 0 else Colors.FAIL
                icon = "✅" if tx['pl_percent'] >= 0 else "🔻"
                print(f"   {tx['date']:<12} {tx['quantity']:<8} {tx['buy_price']:<10.2f} {icon:<10} {tx_color}%{tx['pl_percent']:.2f}{Colors.ENDC}")
            print("-" * 70)

        input("\nAna menüye dönmek için Enter...")

    def trade_flow(self, side="BUY"):
        """Alım ve Satım akışı - Gelişmiş Validasyonlu"""
        self.show_header()
        action_name = "ALIM" if side == "BUY" else "SATIŞ"
        print(Colors.BLUE + f">> HİSSE {action_name} İŞLEMİ" + Colors.ENDC)
        print(Colors.WARNING + "(Ana menüye dönmek için 'q' yazın)" + Colors.ENDC)

        # 1. Portföyü Göster ve Sahip Olunanları Al
        owned_stocks = self.print_mini_portfolio()

        valid_ticker_info = None
        symbol = ""
        
        # --- SEMBOL DÖNGÜSÜ ---
        while True:
            symbol = self.get_input("Hisse Sembolü (Örn: ASELS): ")
            if not symbol: return 

            symbol = symbol.upper()
            
            # KONTROL 1: Satış yapılacaksa, hisse elde var mı?
            if side == "SELL" and symbol not in owned_stocks:
                print(Colors.FAIL + f"❌ HATA: Portföyünüzde '{symbol}' hissesi bulunmuyor. Satış yapılamaz." + Colors.ENDC)
                continue # Tekrar sembol sor
            
            print("Kontrol ediliyor...", end="\r")
            ticker_info = self.market_service.get_ticker_info(symbol)
            
            if ticker_info:
                valid_ticker_info = ticker_info
                current_price = ticker_info['close']
                print(Colors.GREEN + f"✅ {symbol} Bulundu: {current_price:.2f} TL ({ticker_info['date']})" + Colors.ENDC)
                break 
            else:
                print(Colors.FAIL + f"❌ '{symbol}' bulunamadı. Tekrar deneyin." + Colors.ENDC)

        # --- TARİH KONTROLÜ ---
        trade_date = self.check_market_status()
        if trade_date == "CANCEL": return

        # --- ADET DÖNGÜSÜ (Stok Kontrollü) ---
        while True:
            qty = self.get_valid_number("Adet: ")
            if qty is None: return 
            
            # KONTROL 2: Satış miktar kontrolü
            if side == "SELL":
                owned_qty = owned_stocks[symbol]
                if qty > owned_qty:
                    print(Colors.FAIL + f"❌ HATA: Yetersiz bakiye! Mevcut: {owned_qty}, Satılmak istenen: {qty}" + Colors.ENDC)
                    continue # Tekrar adet sor
            
            break # Sorun yoksa döngüden çık

        # 4. Fiyat Girişi
        current_price = valid_ticker_info['close']
        default_price_str = f" ({current_price:.2f})"
        
        price = self.get_valid_number(
            f"İşlem Fiyatı{default_price_str}: ", 
            allow_empty=True, 
            default_val=current_price
        )
        if price is None: return

        print(Colors.WARNING + f"\nÖZET: {symbol} - {qty} Adet x {price} TL" + Colors.ENDC)
        if trade_date:
            print(f"Tarih: {trade_date.strftime('%Y-%m-%d')}")
        
        confirm = self.get_input("Onaylıyor musunuz? (E/H): ")
        if not confirm or confirm.upper() != 'E': return

        if side == "BUY":
            result = self.trade_service.execute_buy(self.user_id, symbol, qty, price, custom_date=trade_date)
        else:
            result = self.trade_service.execute_sell(self.user_id, symbol, qty, price, custom_date=trade_date)

        if result["status"] == "success":
            print(Colors.GREEN + f"\n[BAŞARILI] {result['message']}" + Colors.ENDC)
            if not trade_date:
                print(f"[SİSTEM] {symbol} verileri güncelleniyor...")
                self.market_service.update_price_history(symbol)
        else:
            print(Colors.FAIL + f"\n[HATA] {result['message']}" + Colors.ENDC)
        
        input("\nDevam etmek için Enter...")

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
            print(f"Hedef Fiyat   : {prediction.predicted_price:.2f} TL (T+1)")
            print(f"Model Sinyali : {prediction.signal}")
            print(f"Güven Skoru   : %{float(prediction.confidence_score)*100:.1f}")
            print("*"*40 + Colors.ENDC)
        else:
            print(Colors.FAIL + "\nAnaliz başarısız oldu." + Colors.ENDC)
        
        input("\nDevam...")

    def visualization_menu(self):
        self.show_header()
        print(Colors.BLUE + ">> GÖRSEL RAPORLAMA MERKEZİ" + Colors.ENDC)
        print("Bu işlem portföy verilerinizi analiz ederek grafik dosyaları oluşturur.\n")
        
        print("1. Tüm Grafikleri Oluştur (Toplu Rapor)")
        print("2. Sadece Portföy Dağılımı (Pasta)")
        print("3. Kar/Zarar Analizi")
        print("4. Karşılaştırmalı Performans")
        print("q. Geri Dön")
        
        choice = input("\nSeçiminiz: ").strip()
        
        if choice.lower() == 'q': return

        print("\nGrafikler hazırlanıyor, lütfen bekleyin...")
        generated_files = []

        try:
            if choice == '1' or choice == '2':
                path = self.viz_service.plot_portfolio_allocation(self.user_id)
                if path: generated_files.append(f"Varlık Dağılımı: {path}")

            if choice == '1' or choice == '3':
                path = self.viz_service.plot_profit_loss_breakdown(self.user_id)
                if path: generated_files.append(f"Kar/Zarar: {path}")

            if choice == '1' or choice == '4':
                path = self.viz_service.plot_combined_performance(self.user_id)
                if path: generated_files.append(f"Performans: {path}")
                
                # Ekstraları da toplu raporda basalım
                path2 = self.viz_service.plot_individual_stocks(self.user_id)
                if path2: generated_files.append(f"Tekil Grafikler: {path2}")
                
                path3 = self.viz_service.plot_correlation_matrix(self.user_id)
                if path3: generated_files.append(f"Risk Matrisi: {path3}")

            print(Colors.GREEN + "\n✅ GRAFİKLER BAŞARIYLA OLUŞTURULDU!" + Colors.ENDC)
            print("Dosyalar şu klasörde: " + Colors.BOLD + "reports/graphs/" + Colors.ENDC)
            for f in generated_files:
                print(f"  -> {f}")
                
        except Exception as e:
            print(Colors.FAIL + f"\nHata oluştu: {e}" + Colors.ENDC)

        input("\nMenüye dönmek için Enter...")

    def main_loop(self):
        while True:
            self.show_header()
            print("1. Detaylı Portföy Analizi (PRO)")
            print("2. Hisse Al")
            print("3. Hisse Sat")
            print("4. AI Analiz (Tahmin)")
            print("5. Piyasa Verilerini Güncelle (Manuel)")
            print("6. Görsel Raporlar (Grafik Oluştur)")
            print("7. Çıkış")
            
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
                self.visualization_menu()
            elif choice == '7':
                print("Çıkış yapılıyor...")
                break
            else:
                pass