# 3D Baskı Maliyet & Kar Hesaplayıcı Pro

Bu proje, 3D baskı ile üretim yapanlar için geliştirilmiş, kapsamlı bir maliyet ve kar hesaplama uygulamasıdır. Kullanıcı dostu arayüzü sayesinde filament, elektrik, kargo ve pazaryeri komisyonları gibi tüm giderleri kolayca hesaplayabilir ve satışlarınızı bir Excel dosyasında takip edebilirsiniz.

### ⚠️ Önemli Uyarı: Lütfen Okuyun

> **Merhaba!** Bu uygulama **taşınabilir (portable)** olarak paketlenmiştir ve bilgisayarınıza herhangi bir kurulum yapmaz.
>
> - **Çalıştırma:** Uygulamanın düzgün çalışabilmesi için, indirdiğiniz `.zip` dosyasını bir klasöre çıkartın. `Maliyet Hesaplayıcı.exe`'nin çalışması için klasördeki diğer dosyaları **silmeyin** veya yerini **değiştirmeyin**.
> - **Kısayol Oluşturma:** Uygulamaya kolayca erişmek için `Maliyet Hesaplayıcı.exe` dosyasına sağ tıklayıp "Kısayol Oluştur" seçeneğini kullanabilirsiniz. Bu kısayolu Masaüstü'ne taşıyabilirsiniz.
> - **Excel Dosyası:** Satış kayıtlarınız (`satislar.xlsx`) da bu klasörün içinde oluşacaktır. Bu dosyaya da kolayca erişmek için bir kısayol oluşturabilirsiniz.

---

## ✅ Güvenlik ve İndirme

| Dosya | İndirme Linki | VirusTotal (ZIP Arşivi) | VirusTotal (EXE Dosyası) |
| :--- | :---: | :---: | :---: |
| **Maliyet Hesaplayıcı (ZIP)** | [**► Son Sürümü İndir**](https://github.com/0xPotovzuc/3D-Printer-Cost-Calculator/releases/download/latest-build/Maliyet-Hesaplayici-Windows.zip) | [Sonuçları Gör](https://www.virustotal.com/gui/file/b2984bdec689139cf5bfa888aa5a88562162049bbb1ef9e0ed21e5765c41ef7c/detection) | [Sonuçları Gör](https://www.virustotal.com/gui/file/830e64f1e0fa1598a82c845ca2d4e857083f207197599aa070d9c39d83a536b2) |

> **Not:** Yukarıdaki indirme linki sizi her zaman uygulamanın en güncel sürümüne yönlendirir. Güvenliğiniz için hem indirilen `.zip` arşivinin hem de içindeki `.exe` dosyasının VirusTotal sonuçlarını kontrol edebilirsiniz.

---

## ✨ Özellikler

- **Detaylı Maliyet Analizi:** Filament (gramaj bazında), elektrik (kWh ve tarifeye göre), kargo ve diğer ek giderleri hesaplama.
- **Pazaryeri Entegrasyonu:** Farklı pazaryerleri için değişken komisyon oranları ve sabit ücretleri tanımlayabilme.
- **Kar Hesaplama:** Belirlediğiniz kar marjına göre otomatik satış fiyatı önerme.
- **Excel'e Satış Kaydı:** Her bir satışı, tüm maliyet ve kar detaylarıyla birlikte tek bir tuşla `satislar.xlsx` dosyasına kaydetme.
- **Otomatik Özet Raporu:** Excel dosyasında, her yeni satışta otomatik olarak güncellenen ayrı bir "Özet" sayfası.
- **Esnek Ayarlar:** Filament türleri, kargo firmaları, elektrik tarifeleri ve pazaryerlerini kolayca ekleyip düzenleyebilme.

---

## ⚙️ Hesaplama Detayları

### Elektrik Maliyeti Nasıl Hesaplanır?

Uygulama, elektrik maliyetini adil ve doğru bir şekilde hesaplamak için standart formülleri kullanır. Hesaplama için üç temel bilgiye ihtiyaç vardır:

1.  **Cihaz Gücü (Watt):** 3D yazıcınızın ve bağlı diğer ekipmanların (örneğin Raspberry Pi) ortalama güç tüketimi. Bu değeri uygulamanın ayarlar bölümünden varsayılan olarak belirleyebilirsiniz.
2.  **Baskı Süresi (Saat):** Baskının toplam ne kadar sürdüğü.
3.  **Elektrik Birim Fiyatı (TL/kWh):** Ayarlar bölümünde belirlediğiniz "Ticari" veya "Mesken" tarifesine ait 1 kilowatt-saat (kWh) elektrik bedeli.

#### Adım 1: Toplam Enerji Tüketimini Hesaplama (kWh)

İlk olarak, cihazın baskı süresince ne kadar enerji tükettiği kilowatt-saat (kWh) cinsinden bulunur.

```latex
$$\text{Toplam Tüketim (kWh)} = \frac{\text{Cihaz Gücü (Watt)} \times \text{Baskı Süresi (Saat)}}{1000}$$
```

#### Adım 2: Toplam Elektrik Maliyetini Hesaplama (TL)

Bulunan toplam tüketim değeri, belirlediğiniz tarifenin birim fiyatı ile çarpılarak toplam maliyet hesaplanır.

```latex
$$\text{Elektrik Maliyeti (TL)} = \text{Toplam Tüketim (kWh)} \times \text{Birim Fiyat (TL/kWh)}$$
```

#### Örnek Hesaplama:

- **Cihaz Gücü:** `130 Watt`
- **Baskı Süresi:** `10 Saat`
- **Elektrik Birim Fiyatı (Ticari):** `5.54 TL/kWh`

1.  **Toplam Tüketim:**
    ```latex
    $$
    \frac{130 \text{ Watt} \times 10 \text{ Saat}}{1000} = 1.3 \text{ kWh}
    $$
    ```

2.  **Toplam Maliyet:**
    ```latex
    $$
    1.3 \text{ kWh} \times 5.54 \text{ TL/kWh} = 7.20 \text{ TL}
    $$
    ```
Bu hesaplama sonucunda, 10 saatlik baskının elektrik maliyeti `7.20 TL` olarak bulunur.

---

## ❤️ Projeyi Destekleyin

Bu uygulamayı faydalı bulduysanız ve geliştirilmesine katkıda bulunmak isterseniz, aşağıdaki yöntemlerle destek olabilirsiniz. Desteğiniz, projenin güncel kalmasına ve yeni özellikler eklenmesine yardımcı olacaktır.

### Kripto Para ile Bağış

- **Ethereum (ETH) ve ERC20 Token'ları:**
  `0xfd74638d98fdda416c2d84c0a1714a7684d11213`

---

## ⚙️ Otomatik ve Güvenilir Derleme

Bu proje, antivirüs programlarının yanlış alarm vermemesi için en güvenilir yöntemlerden biri olan **cx_Freeze** paketleyicisini kullanır. Her kod güncellemesi, temiz bir sanal ortamda GitHub Actions tarafından otomatik olarak derlenir ve yayınlanır. Bu sayede size her zaman en güncel ve güvenli uygulama sunulur.

---

## 💻 Geliştiriciler İçin

Eğer kodu kendiniz çalıştırmak veya geliştirmek isterseniz:

1.  Projeyi klonlayın:
    ```bash
    git clone [https://github.com/0xPotovzuc/3D-Printer-Cost-Calculator.git](https://github.com/0xPotovzuc/3D-Printer-Cost-Calculator.git)
    ```

2.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install -r requirements.txt
    ```

3.  Uygulamayı çalıştırın:
    ```bash
    python MaliyetV3.py
