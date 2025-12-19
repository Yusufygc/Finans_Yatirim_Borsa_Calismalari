import sys
import os
from sqlalchemy import text

# Proje kök dizini ayarı
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from src.data.database import engine, Base, SessionLocal
from src.data.models import User, Security, PriceHistory, AiPrediction, PortfolioHolding, Transaction

def reset_database():
    print("UYARI: Bu işlem veritabanındaki TÜM VERİLERİ SİLECEK ve tabloları yeniden oluşturacak.")
    confirm = input("Devam etmek istiyor musunuz? (E/H): ")
    
    if confirm.upper() != 'E':
        print("İşlem iptal edildi.")
        return

    print("\n1. Temizlik Başlıyor...")
    
    # Veritabanı bağlantısı açıyoruz
    with engine.connect() as connection:
        # Transaction başlat
        trans = connection.begin()
        try:
            # 1. Foreign Key Kontrollerini Kapat (Kilitlenmeyi önler)
            print("   -> Yabancı anahtar kontrolleri devre dışı bırakılıyor...")
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            # 2. Sorun çıkaran hayalet tabloları manuel sil (Eski SQL'den kalanlar)
            print("   -> Eski tablolar temizleniyor (sim_trades vb.)...")
            connection.execute(text("DROP TABLE IF EXISTS sim_trades;"))
            
            # 3. SQLAlchemy tarafından bilinen tüm tabloları sil
            print("   -> Ana tablolar siliniyor...")
            Base.metadata.drop_all(bind=connection)
            
            # 4. Foreign Key Kontrollerini Tekrar Aç
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            
            # 5. Yeni Tabloları Oluştur
            print("2. Tablolar yeniden oluşturuluyor...")
            Base.metadata.create_all(bind=connection)
            
            trans.commit()
        except Exception as e:
            trans.rollback()
            print(f"HATA OLUŞTU: {e}")
            return

    print("3. Başlangıç verileri yükleniyor...")
    db = SessionLocal()
    
    # Demo Kullanıcıyı Tekrar Oluştur
    try:
        user = User(username="demo_user", email="demo@fintech.com", risk_profile="orta")
        db.add(user)
        db.commit()
        print(f"   -> Demo kullanıcı oluşturuldu (ID: {user.id})")
    except Exception as e:
        print(f"   -> Kullanıcı oluşturulurken hata (zaten var olabilir): {e}")
    finally:
        db.close()
    
    print("-" * 50)
    print("BAŞARILI: Veritabanı tamamen sıfırlandı ve şema güncellendi.")
    print("Lütfen 'python src/main.py' komutunu çalıştırarak analizi tekrar deneyin.")
    print("-" * 50)

if __name__ == "__main__":
    reset_database()