# 🧾 3D Baskı Maliyet & Kar Hesaplayıcı v2.4 💰

## 🚀 İndirme / Download

Bu bölümden uygulamanın çalıştırılabilir Windows sürümünü veya Python kaynak kodunu indirebilirsiniz.
* **Virüs Total**
    * **[Kontrol](https://www.virustotal.com/gui/file/0be81eaf54d8d3da8fccf03fa8a26742d73ecc4b2b8c322c74ead100020c44d5?nocache=1)**
        
* **Çalıştırılabilir Program (`.exe` - Windows):**
    * **[➡️ En Son Sürüm İndirme](https://github.com/potovzuc/3D-Printer-Cost-Calculator/raw/refs/heads/V2.4/Maliyet%20V2.exe)**
        * *Önerilen yöntem budur.*

* **Kaynak Kod (`.py`):**
    * **[🐍 Ana Kod Dosyası (Maliyet V2.py)](https://raw.githubusercontent.com/potovzuc/3D-Printer-Cost-Calculator/refs/heads/V2.4/Maliyet%20V2.py)**
        * *Python kurulu ise doğrudan kodu görüntüleyip çalıştırmak veya indirmek için. İndirmek için "Raw" butonuna sağ tıklayıp "Farklı Kaydet" seçeneğini kullanabilirsiniz.*

---

*(README dosyasının geri kalan içeriği bu çizginin altına gelecek... Örneğin: Açıklama, Özellikler, Nasıl Kullanılır vb.)*

Bu masaüstü uygulaması, 3D baskı ile ürettiğiniz ürünlerin maliyetlerini detaylı bir şekilde hesaplamanıza ve karlı satış fiyatları belirlemenize yardımcı olmak için tasarlanmıştır. Özellikle filament, elektrik tüketimi, kargo ücretleri, pazaryeri komisyonları ve diğer ek giderleri göz önünde bulundurarak kapsamlı bir analiz sunar.

## Temel Özellikler

* **Filament Yönetimi:** Farklı filament türlerini ve kilogram başına maliyetlerini ekleyebilir, silebilir ve listeleyebilirsiniz.
* **Kargo Ücretleri:** Anlaşmalı olduğunuz kargo firmalarını (PTT, MNG, Yurtiçi Kargo vb.) ve farklı desi/ağırlık aralıkları için ücretlerini kaydedebilirsiniz.
* **Pazaryeri Komisyonları:** Satış yaptığınız pazaryerlerini (Trendyol, Hepsiburada, Etsy, Kendi Siteniz vb.) ve bu platformların komisyon oranlarını (yüzdesel + sabit ücret) tanımlayabilirsiniz. "Komisyonsuz" satışlar için "Other/None" seçeneği mevcuttur.
* **Detaylı Maliyet Hesaplama:**
    * Kullanılan filament miktarı (gram) ve türü.
    * Baskı süresi (saat) ve yazıcının gücü (Watt).
    * Ticari veya mesken elektrik tarifesi üzerinden elektrik maliyeti.
    * Seçilen kargo firması ve desiye göre kargo maliyeti.
    * Girebileceğiniz diğer ek giderler (örn. zımpara, boya, amortisman payı).
* **Kar ve Satış Fiyatı:**
    * Seçilen pazaryerine göre *tahmini* komisyon tutarı.
    * Komisyon dahil *tahmini* toplam maliyet.
    * Belirlenen elektrik tarifesine göre (Ticari/Mesken) %50 ve %100 kar marjları ile *önerilen* satış fiyatları (komisyon düşülerek hesaplanır).
* **Veri Saklama:** Tüm ayarlarınız (filamentler, kargo, pazaryerleri, elektrik fiyatları) uygulamanın yanındaki `app_data_v2.4.json` dosyasında otomatik olarak saklanır ve uygulama açıldığında geri yüklenir.
* **Kullanıcı Arayüzü:** Sekmeli yapısı sayesinde ayarlar ve hesaplama ekranı arasında kolay geçiş sağlar. `ttk` tema desteği ile daha modern bir görünüm sunar (sistem destekliyorsa).
* **Kaydırılabilir Hesaplama:** Hesaplama sekmesinde dikey kaydırma çubuğu ile küçük ekranlarda daha iyi kullanılabilirlik.

## v2.4 Değişiklikleri

* **Hesaplama Sekmesi Kaydırma:** "Maliyet & Kar Hesaplama" sekmesi içeriği artık dikey olarak kaydırılabilir, böylece tüm alanlar daha küçük pencerelerde bile görülebilir.
* **Kararlılık İyileştirmeleri:** Önceki sürümlerde tespit edilen bazı iç söz dizimi (syntax) hataları giderildi (özellikle kargo ve pazaryeri ayarlarını kaydederken). Uygulamanın genel kararlılığı artırıldı.

## Nasıl Kullanılır?

* **`.exe` Kullanımı (Windows):** Eğer bir `.exe` dosyası indirildiyse, dosyayı çalıştırın. Ayarlar (`app_data_v2.4.json`) `.exe` ile aynı klasörde oluşturulacaktır. Yazma izniniz olduğundan emin olun.
* **Kaynak Koddan Çalıştırma:**
    1.  Sisteminizde Python 3 kurulu olduğundan emin olun. (Tkinter genellikle Python ile birlikte gelir).
    2.  Depoyu klonlayın veya dosyaları indirin.
    3.  Komut istemcisi veya terminali açıp kodun bulunduğu klasöre gidin.
    4.  `python run.py` komutunu çalıştırın (`run.py` yerine ana dosyanızın adını yazın).

## Veri Depolama

Uygulama, tüm ayarlarınızı ve listelerinizi, çalıştırıldığı dizinde `app_data_v2.4.json` adında bir dosyada saklar. Bu dosyayı yedekleyebilir veya farklı bir bilgisayara taşıyarak ayarlarınızı koruyabilirsiniz.

## Dil

Bu sürüm (v2.4) sadece **Türkçe** arayüz sunmaktadır.
