# 3D Baskı Maliyet & Kar Hesaplayıcı Pro

Bu proje, 3D baskı ile üretim yapanlar için geliştirilmiş, kapsamlı bir maliyet ve kar hesaplama uygulamasıdır. Kullanıcı dostu arayüzü sayesinde filament, elektrik, kargo ve pazaryeri komisyonları gibi tüm giderleri kolayca hesaplayabilir ve satışlarınızı bir Excel dosyasında takip edebilirsiniz.

---

## 🚀 İndirme (Download)

Uygulamanın en güncel ve stabil sürümünü aşağıdaki linkten indirebilirsiniz. Bu link sizi projenin "Releases" sayfasına yönlendirecektir.

[**► Son Sürümü İndir (Windows x64)**](https://github.com/[kullanici-adiniz]/[depo-adiniz]/releases/latest)

---

## ✨ Özellikler

- **Detaylı Maliyet Analizi:** Filament (gramaj bazında), elektrik (kWh ve tarifeye göre), kargo ve diğer ek giderleri hesaplama.
- **Pazaryeri Entegrasyonu:** Farklı pazaryerleri için değişken komisyon oranları ve sabit ücretleri tanımlayabilme.
- **Kar Hesaplama:** Belirlediğiniz kar marjına göre otomatik satış fiyatı önerme.
- **Excel'e Satış Kaydı:** Her bir satışı, tüm maliyet ve kar detaylarıyla birlikte tek bir tuşla `satislar.xlsx` dosyasına kaydetme.
- **Otomatik Özet Raporu:** Excel dosyasında, her yeni satışta otomatik olarak güncellenen ayrı bir "Özet" sayfası. Bu sayfa, harcanan toplam filament miktarını (her tür için ayrı) ve genel finansal toplamları (toplam maliyet, satış, kar) gösterir.
- **Esnek Ayarlar:** Filament türleri, kargo firmaları, elektrik tarifeleri ve pazaryerlerini kolayca ekleyip düzenleyebilme.

---

## 🛠️ Kurulum ve Çalıştırma

1.  Yukarıdaki **İndirme (Download)** bölümünden en son sürümü indirin.
2.  İndirdiğiniz `.zip` dosyasını bir klasöre çıkartın.
3.  Klasörün içindeki `Maliyet Hesaplayıcı.exe` dosyasına çift tıklayarak uygulamayı başlatın.

Uygulama, ayarlarınızı (`app_data.json`) ve satış kayıtlarınızı (`satislar.xlsx`) kendi bulunduğu klasörde oluşturacak ve yönetecektir.

---

## ⚙️ Otomatik Derleme (GitHub Actions)

Bu proje, güvenilir ve temiz bir `.exe` dosyası oluşturmak için GitHub Actions kullanır. `main` branch'ine `v` harfiyle başlayan yeni bir etiket (örn: `v3.0`, `v3.1`) gönderildiğinde, derleme süreci otomatik olarak başlar ve yeni sürüm "Releases" sayfasında yayınlanır.

---

## 💻 Geliştiriciler İçin

Eğer kodu kendiniz çalıştırmak veya geliştirmek isterseniz:

1.  Projeyi klonlayın:
    ```bash
    git clone [https://github.com/](https://github.com/)[kullanici-adiniz]/[depo-adiniz].git
    ```
2.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```
3.  Uygulamayı çalıştırın:
    ```bash
    python MaliyetV3.py
    ```
