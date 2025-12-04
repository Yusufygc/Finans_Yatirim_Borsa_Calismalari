import time

class RiskAssessment:
    """
    Yatırımcı Risk Profilini belirlemek için anket tabanlı değerlendirme sınıfı.
    Single Responsibility: Sadece kullanıcının risk algısını ölçer ve profili döndürür.
    """
    
    def __init__(self):
        # Soruları ve puanlama mantığını yapılandırıcıda tanımlıyoruz
        self.questions = self._load_questions()
        self.profiles = {
            "temkinli": (0, 14),
            "orta": (15, 24),
            "agresif": (25, 100)
        }

    def _load_questions(self):
        """
        Anket sorularını ve her şıkkın puan değerini döndürür.
        İleride bu veriler bir JSON veya veritabanından da çekilebilir.
        """
        return [
            {
                "id": 1,
                "text": "Yatırım yaparken ana hedefiniz nedir?",
                "options": {
                    1: ("Enflasyona karşı paramı korumak (Düşük Risk)", 3),
                    2: ("Dengeli bir büyüme sağlamak (Orta Risk)", 6),
                    3: ("Maksimum getiri elde etmek (Yüksek Risk)", 10)
                }
            },
            {
                "id": 2,
                "text": "Bu yatırıma ne kadar süre dokunmamayı planlıyorsunuz?",
                "options": {
                    1: ("1 yıldan az (Kısa Vade)", 2),
                    2: ("1 - 3 yıl (Orta Vade)", 6),
                    3: ("3 yıldan fazla (Uzun Vade)", 10)
                }
            },
            {
                "id": 3,
                "text": "Piyasalar kötüye gitti ve portföyünüz %20 değer kaybetti. Tepkiniz ne olur?",
                "options": {
                    1: ("Panik yapıp kalan paramı kurtarmak için satarım.", 0),
                    2: ("Endişelenirim ama satmam, beklerim.", 5),
                    3: ("Bu düşüşü alım fırsatı olarak görür, ekleme yaparım.", 10)
                }
            },
            {
                "id": 4,
                "text": "Finansal piyasalar hakkındaki bilgi seviyeniz nedir?",
                "options": {
                    1: ("Çok az / Hiç yok", 2),
                    2: ("Temel seviyede bilgim var", 5),
                    3: ("İleri seviyede bilgim ve tecrübem var", 8)
                }
            }
        ]

    def run_assessment(self):
        """
        Anketi konsol üzerinden başlatır ve sonuç profilini döndürür.
        """
        print("\n" + "="*50)
        print("   YATIRIMCI RİSK PROFİLİ ANALİZİ")
        print("="*50)
        print("Lütfen size en uygun seçeneğin numarasını giriniz.\n")

        total_score = 0

        for q in self.questions:
            print(f"Soru {q['id']}: {q['text']}")
            for key, (desc, _) in q['options'].items():
                print(f"  [{key}] {desc}")
            
            choice = self._get_valid_input(list(q['options'].keys()))
            
            # Seçilen şıkkın puanını ekle
            score = q['options'][choice][1]
            total_score += score
            print("-" * 30)
            time.sleep(0.5) # Kullanıcı deneyimi için kısa bekleme

        return self._calculate_profile(total_score)

    def _get_valid_input(self, valid_options):
        """
        Kullanıcıdan geçerli bir giriş alana kadar döngü kurar.
        """
        while True:
            try:
                selection = int(input("Seçiminiz: "))
                if selection in valid_options:
                    return selection
                else:
                    print(f"[HATA] Lütfen sadece {valid_options} değerlerinden birini giriniz.")
            except ValueError:
                print("[HATA] Lütfen sayısal bir değer giriniz.")

    def _calculate_profile(self, score):
        """
        Toplam puana göre profili belirler.
        """
        print(f"\n[SONUÇ] Toplam Risk Puanınız: {score}")
        
        for profile, (min_score, max_score) in self.profiles.items():
            if min_score <= score <= max_score:
                print(f"[PROFİL] Tespit Edilen Yatırımcı Profili: {profile.upper()}")
                return profile
        
        return "orta" # Fallback (Hata durumunda varsayılan)

if __name__ == "__main__":
    # Test amaçlı doğrudan çalıştırıldığında
    assessor = RiskAssessment()
    assessor.run_assessment()