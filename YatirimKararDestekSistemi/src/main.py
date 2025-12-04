from app.database import init_db, SessionLocal, User
from app.portfolio_manager import PortfolioManager

def main():
    # 1. Tabloları oluştur (İlk çalışmada gereklidir)
    init_db()
    
    # 2. Örnek Kullanıcı Oluştur (Yoksa)
    db = SessionLocal()
    user = db.query(User).filter_by(username="demo_user").first()
    if not user:
        user = User(username="demo_user", email="demo@test.com", risk_profile="agresif")
        db.add(user)
        db.commit()
        print("Demo kullanıcı oluşturuldu.")
    
    # 3. Portföy Yöneticisini Başlat
    pm = PortfolioManager(user_id=user.id)
    
    while True:
        print("\n--- YATIRIM KARAR DESTEK SİSTEMİ ---")
        print("1. Hisse Al")
        print("2. Portföyümü Göster")
        print("3. AI Analizi Yap (Tavsiye Al)")
        print("4. Çıkış")
        
        choice = input("Seçiminiz: ")
        
        if choice == '1':
            sembol = input("Hisse Sembolü (Örn: ASELS): ").upper()
            adet = float(input("Adet: "))
            girilen_fiyat = input("Birim Fiyat: ").replace(',', '.')
            fiyat = float(girilen_fiyat)
            pm.buy_stock(sembol, adet, fiyat)
        
        elif choice == '2':
            pm.get_portfolio_summary()
            
        elif choice == '3':
            pm.run_daily_ai_analysis()
            
        elif choice == '4':
            print("Çıkış yapılıyor...")
            break
        else:
            print("Geçersiz seçim.")

if __name__ == "__main__":
    main()