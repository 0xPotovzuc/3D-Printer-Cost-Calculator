import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import traceback # Hata ayıklama için

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Baskı Maliyet & Kar Hesaplayıcı v2.4 - Tam Sürüm")
        self.root.geometry("950x750")

        # Uygulama sürümü ve veri dosyası adı
        self.app_version = "v2.4"
        self.data_file = f"app_data_{self.app_version}.json"

        # --- Renkler ve Stil ---
        self.bg_color = "#f5f5f5"
        self.button_color = "#e0e0e0"
        self.text_color = "#333333"
        self.highlight_color = "#64b5f6"
        self.style = ttk.Style()
        try:
             # Denenebilecek modern temalar ('clam', 'alt', 'default', 'classic')
             # Sistemde mevcut değilse 'clam' kullanılır.
            available_themes = self.style.theme_names()
            if 'vista' in available_themes: # Windows için 'vista' genellikle daha iyi görünür
                self.style.theme_use('vista')
            elif 'aqua' in available_themes: # MacOS için
                 self.style.theme_use('aqua')
            else:
                 self.style.theme_use('clam') # Genel fallback
        except tk.TclError:
             self.style.theme_use('clam') # Hata durumunda clam kullan

        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, font=("Arial", 10), foreground=self.text_color)
        self.style.configure("TButton", font=("Arial", 10, "bold"), padding=5, background=self.button_color, foreground=self.text_color)
        self.style.map("TButton", background=[('active', self.highlight_color)])
        self.style.configure("TCombobox", font=("Arial", 10), padding=5)
        self.style.configure("TEntry", font=("Arial", 10), padding=5)
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.style.configure("TLabelframe", background=self.bg_color, padding=10)
        self.style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.text_color, font=("Arial", 11, "bold"))
        self.style.configure("TCanvas", background=self.bg_color, borderwidth=0, highlightthickness=0)


        # --- Sekmeler ---
        self.tab_control = ttk.Notebook(root)
        self.tab1 = ttk.Frame(self.tab_control, style="TFrame")
        self.tab2 = ttk.Frame(self.tab_control, style="TFrame") # Hesaplama sekmesi için dış çerçeve
        self.tab3 = ttk.Frame(self.tab_control, style="TFrame")
        self.tab4 = ttk.Frame(self.tab_control, style="TFrame")
        self.tab5 = ttk.Frame(self.tab_control, style="TFrame")
        self.tab_control.add(self.tab1, text="Filament Ayarları")
        self.tab_control.add(self.tab2, text="Maliyet & Kar Hesaplama")
        self.tab_control.add(self.tab5, text="Pazaryeri Ayarları")
        self.tab_control.add(self.tab4, text="Kargo Ücretleri")
        self.tab_control.add(self.tab3, text="Genel Ayarlar")
        self.tab_control.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Veri Saklama ---
        self.filament_data = []
        self.electricity_prices = {"ticari": 5.5411, "mesken": 3.1085}
        self.shipping_prices = {"PTT": [], "MNG": [], "Yurtiçi Kargo": []}
        self.marketplaces = {
            "Trendyol": {"rate": 15.0, "fixed": 1.50},
            "Hepsiburada": {"rate": 12.5, "fixed": 1.00},
            "Diğer/Yok": {"rate": 0.0, "fixed": 0.0} }
        self.settings = { "costing_electricity_type": "ticari" }
        self.selected_marketplace_id = None # Pazaryeri düzenleme için

        self.load_data() # Verileri yükle

        # --- Sekme İçeriklerini Oluştur ---
        self.create_filament_tab()
        self.create_cost_profit_tab()
        self.create_settings_tab()
        self.create_shipping_tab()
        self.create_marketplace_tab()

        # Pencere kapatma olayını bağla
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # --- Veri Yönetimi ---
    def load_data(self):
        """Verileri JSON dosyasından yükler."""
        default_marketplaces = {
            "Trendyol": {"rate": 15.0, "fixed": 1.50},
            "Hepsiburada": {"rate": 12.5, "fixed": 1.00},
            "Diğer/Yok": {"rate": 0.0, "fixed": 0.0} }
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding='utf-8') as file:
                    data = json.load(file)
                    # Veri tiplerini kontrol ederek yükle
                    self.filament_data = data.get("filament_data", [])
                    if not isinstance(self.filament_data, list): self.filament_data = []

                    loaded_electricity = data.get("electricity_prices", self.electricity_prices)
                    if isinstance(loaded_electricity, dict): self.electricity_prices.update(loaded_electricity)

                    loaded_shipping = data.get("shipping_prices", self.shipping_prices)
                    if isinstance(loaded_shipping, dict): self.shipping_prices.update(loaded_shipping)

                    loaded_marketplaces = data.get("marketplaces", default_marketplaces)
                    if isinstance(loaded_marketplaces, dict): self.marketplaces.update(loaded_marketplaces)
                    else: self.marketplaces = default_marketplaces

                    loaded_settings = data.get("settings", self.settings)
                    if isinstance(loaded_settings, dict): self.settings.update(loaded_settings)

            except json.JSONDecodeError:
                messagebox.showerror("Yükleme Hatası", f"{self.data_file} dosyası bozuk veya geçersiz formatta.\nVarsayılan ayarlar yüklendi.")
                self.marketplaces = default_marketplaces # Hata durumunda varsayılana dön
            except Exception as e:
                 messagebox.showerror("Yükleme Hatası", f"Veri yüklenirken beklenmedik bir hata oluştu: {e}")
                 traceback.print_exc()
                 self.marketplaces = default_marketplaces
        else:
            # Eğer veri dosyası yoksa, varsayılanlarla başlat ve ilk kez kaydet
             print(f"Veri dosyası bulunamadı ({self.data_file}). Varsayılan ayarlar kullanılıyor.")
             self.marketplaces = default_marketplaces
             self.save_data()

    def save_data(self):
        """Mevcut verileri JSON dosyasına kaydeder."""
        data = {
            "filament_data": self.filament_data,
            "electricity_prices": self.electricity_prices,
            "shipping_prices": self.shipping_prices,
            "marketplaces": self.marketplaces,
            "settings": self.settings,
        }
        try:
            with open(self.data_file, "w", encoding='utf-8') as file:
                # indent=4 ile daha okunaklı JSON, ensure_ascii=False Türkçe karakterler için
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as e:
             messagebox.showerror("Kaydetme Hatası", f"Veri kaydedilirken bir hata oluştu: {e}")
             traceback.print_exc()

    def on_close(self):
        """Pencere kapatıldığında çağrılır."""
        # Veriler artık anlık kaydedildiği için burada tekrar kaydetmeye gerek yok.
        # İstenirse burada ek bir kaydetme yapılabilir veya onay sorulabilir.
        print("Uygulama kapatılıyor.")
        self.root.destroy()

    def validate_numeric_input(self, P):
        """Tkinter Entry widget'ı için doğrulama fonksiyonu. Sadece pozitif sayılara izin verir."""
        if P == "" or P == ".": return True # Boş veya sadece nokta ise izin ver (ondalık için)
        try:
            value = float(P)
            return value >= 0 # Negatif olmayan sayılara izin ver
        except ValueError:
            return False # Sayıya dönüştürülemiyorsa izin verme

    # --- Filament Ayarları Sekmesi ---
    def create_filament_tab(self):
        """Filament ayarları sekmesinin içeriğini oluşturur."""
        frame = ttk.Frame(self.tab1, padding=(10, 10))
        frame.pack(expand=True, fill="both")
        frame.rowconfigure(1, weight=1); frame.columnconfigure(0, weight=1)

        # Giriş Alanı
        input_frame = ttk.LabelFrame(frame, text="Yeni Filament Ekle/Sil", padding=(10, 10))
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Filament Türü:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.filament_type_entry = ttk.Entry(input_frame, width=30)
        self.filament_type_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text="Fiyat (TL/kg):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        vcmd_numeric = (self.root.register(self.validate_numeric_input), '%P')
        self.filament_price_entry = ttk.Entry(input_frame, validate='key', validatecommand=vcmd_numeric, width=15)
        self.filament_price_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Ekle", command=self.add_filament, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Seçileni Sil", command=self.delete_filament, width=10).pack(side=tk.LEFT, padx=5)

        # Liste Alanı
        list_frame = ttk.LabelFrame(frame, text="Kayıtlı Filamentler", padding=(10, 10))
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.rowconfigure(0, weight=1); list_frame.columnconfigure(0, weight=1)

        self.filament_listbox = ttk.Treeview(list_frame, columns=("Tür", "Fiyat"), show="headings")
        self.filament_listbox.heading("Tür", text="Filament Türü")
        self.filament_listbox.heading("Fiyat", text="Fiyat (TL/kg)")
        self.filament_listbox.column("Tür", width=200, stretch=tk.YES)
        self.filament_listbox.column("Fiyat", width=100, anchor="e", stretch=tk.NO)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.filament_listbox.yview)
        self.filament_listbox.configure(yscrollcommand=scrollbar.set)
        self.filament_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.refresh_filament_list() # Listeyi ilk yüklemede doldur

    def add_filament(self):
        """Yeni filament ekler."""
        filament_type = self.filament_type_entry.get().strip()
        filament_price_str = self.filament_price_entry.get()
        if not filament_type: messagebox.showwarning("Eksik Bilgi", "Filament türü boş bırakılamaz."); return
        if not filament_price_str: messagebox.showwarning("Eksik Bilgi", "Filament fiyatı boş bırakılamaz."); return
        try:
            filament_price = float(filament_price_str)
            if filament_price < 0: messagebox.showwarning("Geçersiz Değer", "Fiyat negatif olamaz."); return
            # Küçük/büyük harf duyarsız kontrol
            if any(f[0].strip().lower() == filament_type.lower() for f in self.filament_data):
                messagebox.showwarning("Mevcut Filament", f"'{filament_type}' zaten listede mevcut."); return
            self.filament_data.append((filament_type, filament_price))
            self.filament_data.sort(key=lambda x: x[0].lower()) # İsme göre (küçük/büyük harf duyarsız) sırala
            self.refresh_filament_list()
            self.filament_type_entry.delete(0, tk.END)
            self.filament_price_entry.delete(0, tk.END)
            self.update_filament_combobox() # Diğer sekmedeki listeyi güncelle
            self.save_data() # Değişikliği kaydet
        except ValueError: messagebox.showerror("Hata", "Fiyat geçersiz! Lütfen sayısal bir değer girin.")

    def delete_filament(self):
        """Seçili filamenti siler."""
        selected_items = self.filament_listbox.selection()
        if not selected_items: messagebox.showwarning("Seçim Yapılmadı", "Lütfen silmek için listeden bir filament seçin."); return
        selected_item = selected_items[0]
        try:
             item_values = self.filament_listbox.item(selected_item, "values")
             filament_name_to_delete = item_values[0]
        except IndexError:
             messagebox.showerror("Hata", "Seçili öğe bilgisi alınamadı.")
             return

        confirm = messagebox.askyesno("Silme Onayı", f"'{filament_name_to_delete}' filamentini silmek istediğinizden emin misiniz?")
        if confirm:
            # İsme göre filtreleyerek sil
            original_length = len(self.filament_data)
            self.filament_data = [f for f in self.filament_data if f[0] != filament_name_to_delete]
            if len(self.filament_data) < original_length: # Silme başarılıysa
                self.refresh_filament_list()
                self.update_filament_combobox()
                self.save_data()
                print(f"'{filament_name_to_delete}' silindi.")
            else:
                print(f"Silinecek filament '{filament_name_to_delete}' listede bulunamadı.") # Nadir durum

    def refresh_filament_list(self):
        """Filament listesini (Treeview) temizler ve yeniden doldurur."""
        for item in self.filament_listbox.get_children(): self.filament_listbox.delete(item)
        # Sıralanmış veriyi ekle
        for filament in self.filament_data:
             # Fiyatı formatlayarak ekle
             self.filament_listbox.insert("", tk.END, values=(filament[0], f"{filament[1]:.2f}"))

    # --- Maliyet & Kar Hesaplama Sekmesi ---
    def create_cost_profit_tab(self):
        """Maliyet & Kar Hesaplama sekmesinin içeriğini oluşturur (Kaydırma Çubuğu ile)."""
        # === Kaydırılabilir Alan Kurulumu ===
        outer_frame = ttk.Frame(self.tab2, style="TFrame")
        outer_frame.pack(expand=True, fill="both")
        outer_frame.rowconfigure(0, weight=1); outer_frame.columnconfigure(0, weight=1)

        canvas = tk.Canvas(outer_frame, background=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky='nsew'); scrollbar.grid(row=0, column=1, sticky='ns')

        content_frame = ttk.Frame(canvas, style="TFrame")
        content_frame_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def _on_frame_configure(event): canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(event): canvas.itemconfig(content_frame_id, width=event.width)
        content_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        # === Kaydırılabilir Alan Kurulumu Sonu ===

        # === Asıl İçerik Widget'ları (content_frame içine) ===
        content_frame.columnconfigure(0, weight=1) # İçerik yatay genişlesin
        vcmd_numeric = (self.root.register(self.validate_numeric_input), '%P')

        # Baskı Girdileri
        input_frame = ttk.LabelFrame(content_frame, text="Baskı Bilgileri", padding=(15, 10))
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5)); input_frame.columnconfigure(1, weight=1)
        ttk.Label(input_frame, text="Filament Miktarı (g):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.filament_amount_entry = ttk.Entry(input_frame, validate='key', validatecommand=vcmd_numeric); self.filament_amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(input_frame, text="Filament Türü:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.filament_type_combobox = ttk.Combobox(input_frame, state="readonly", width=25); self.filament_type_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.update_filament_combobox() # Liste yüklendikten sonra doldur
        ttk.Label(input_frame, text="Baskı Süresi (saat):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.print_time_entry = ttk.Entry(input_frame, validate='key', validatecommand=vcmd_numeric); self.print_time_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(input_frame, text="Cihaz Gücü (W):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.device_power_entry = ttk.Entry(input_frame, validate='key', validatecommand=vcmd_numeric); self.device_power_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Ek Maliyetler, Kargo ve Pazaryeri
        cost_frame = ttk.LabelFrame(content_frame, text="Ek Maliyetler, Kargo ve Pazaryeri", padding=(15, 10))
        cost_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5); cost_frame.columnconfigure(1, weight=1)
        ttk.Label(cost_frame, text="Diğer Giderler (TL):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.other_costs_entry = ttk.Entry(cost_frame, validate='key', validatecommand=vcmd_numeric); self.other_costs_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew"); self.other_costs_entry.insert(0, "0.0")
        ttk.Label(cost_frame, text="Kargo Firması:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.shipping_company_combobox = ttk.Combobox(cost_frame, values=list(self.shipping_prices.keys()), state="readonly", width=25); self.shipping_company_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.shipping_company_combobox.bind("<<ComboboxSelected>>", self.update_shipping_desi_combobox)
        ttk.Label(cost_frame, text="Desi/Ağırlık:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.shipping_desi_combobox = ttk.Combobox(cost_frame, state="readonly", width=25); self.shipping_desi_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        # Başlangıçta kargo desilerini doldur (eğer kargo firması varsa)
        keys = list(self.shipping_prices.keys())
        if keys: self.shipping_company_combobox.set(keys[0]); self.update_shipping_desi_combobox()
        ttk.Label(cost_frame, text="Satış Pazaryeri:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.marketplace_selection_combobox = ttk.Combobox(cost_frame, state="readonly", width=25); self.marketplace_selection_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.update_marketplace_combobox() # Liste yüklendikten sonra doldur

        # Hesaplama Butonu
        ttk.Button(content_frame, text="Hesapla", command=self.calculate_cost_profit, style="TButton").grid(row=2, column=0, pady=15)

        # Sonuç Alanı
        results_frame = ttk.LabelFrame(content_frame, text="Sonuçlar", padding=(15, 10))
        results_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0,10)); results_frame.columnconfigure(1, weight=1)
        # Sonuç etiketleri ve anahtarları
        self.result_labels = {}
        self.result_keys = {
            "filament_cost": "Filament Maliyeti:", "elec_cost_comm": "Elektrik Maliyeti (Ticari):",
            "elec_cost_res": "Elektrik Maliyeti (Mesken):", "shipping_cost": "Kargo Maliyeti:",
            "other_costs": "Diğer Giderler:", "sep1": "---", "total_cost_comm": "Toplam Maliyet (Ticari Elektrik):",
            "total_cost_res": "Toplam Maliyet (Mesken Elektrik):", "sep2": "---",
            "commission": "Platform Komisyonu (Tahmini):", "total_cost_commissioned": "Toplam Maliyet Komisyonlu (Seçili):",
            "sep3": "---", "sale_50_profit": "%50 Kar ile Satış Fiyatı:", "sale_100_profit": "%100 Kar ile Satış Fiyatı:", }
        self.commission_label_ref, self.total_cost_commissioned_label_ref = None, None
        self.sale_50_label_ref, self.sale_100_label_ref = None, None
        for i, (key, text) in enumerate(self.result_keys.items()):
            label_widget = ttk.Label(results_frame, text=text, anchor="w")
            label_widget.grid(row=i, column=0, padx=5, pady=2, sticky="w")
            if key == "commission": self.commission_label_ref = label_widget
            elif key == "total_cost_commissioned": self.total_cost_commissioned_label_ref = label_widget
            elif key == "sale_50_profit": self.sale_50_label_ref = label_widget
            elif key == "sale_100_profit": self.sale_100_label_ref = label_widget
            if not key.startswith("sep"):
                value_label = ttk.Label(results_frame, text="0.00 TL", anchor="e", font=("Arial", 10, "bold"))
                value_label.grid(row=i, column=1, padx=5, pady=2, sticky="ew"); self.result_labels[key] = value_label

    # --- Combobox Güncelleme Fonksiyonları ---
    def update_filament_combobox(self):
        """Hesaplama sekmesindeki filament combobox'ını günceller."""
        filament_types = sorted([f[0] for f in self.filament_data], key=str.lower)
        self.filament_type_combobox["values"] = filament_types
        if filament_types: self.filament_type_combobox.set(filament_types[0])
        else: self.filament_type_combobox.set("")

    def update_shipping_desi_combobox(self, event=None):
        """Hesaplama sekmesindeki kargo desi combobox'ını günceller."""
        company = self.shipping_company_combobox.get()
        desi_options = []
        if company and company in self.shipping_prices:
            # Desi değerlerini al ve sırala (önce sayısal, sonra metinsel)
            items = self.shipping_prices[company]
            def sort_key(item):
                desi_val = item[0]
                try: return (0, float(desi_val)) # Sayısal ise (0, sayısal_değer)
                except ValueError: return (1, desi_val) # Metinsel ise (1, metin)
            items.sort(key=sort_key)
            desi_options = [item[0] for item in items]

        self.shipping_desi_combobox["values"] = desi_options
        if desi_options: self.shipping_desi_combobox.set(desi_options[0])
        else: self.shipping_desi_combobox.set("")

    def update_marketplace_combobox(self):
        """Hesaplama sekmesindeki pazaryeri combobox'ını günceller."""
        marketplace_names = sorted(list(self.marketplaces.keys()), key=str.lower)
        self.marketplace_selection_combobox["values"] = marketplace_names
        # "Diğer/Yok" varsa onu seç, yoksa ilkini seç
        default_selection = "Diğer/Yok" if "Diğer/Yok" in marketplace_names else (marketplace_names[0] if marketplace_names else "")
        self.marketplace_selection_combobox.set(default_selection)

    # --- Hesaplama Fonksiyonu ---
    def calculate_cost_profit(self):
        """Girdilere göre maliyet ve karı hesaplar, sonuçları gösterir."""
        try:
            # Girdileri al ve temel doğrulamaları yap
            filament_amount_str = self.filament_amount_entry.get(); print_time_str = self.print_time_entry.get()
            device_power_str = self.device_power_entry.get(); other_costs_str = self.other_costs_entry.get()
            if not all([filament_amount_str, print_time_str, device_power_str, other_costs_str]): messagebox.showwarning("Eksik Bilgi", "Lütfen tüm baskı bilgilerini ve ek maliyetleri girin."); return

            # Sayısal değerlere çevir
            filament_amount = float(filament_amount_str); print_time = float(print_time_str)
            device_power = float(device_power_str); other_costs = float(other_costs_str)
            if filament_amount < 0 or print_time < 0 or device_power < 0 or other_costs < 0: messagebox.showwarning("Geçersiz Değer", "Sayısal değerler negatif olamaz."); return

            # Filament Maliyeti
            filament_type = self.filament_type_combobox.get()
            if not filament_type: messagebox.showwarning("Eksik Bilgi", "Lütfen bir filament türü seçin."); return
            filament_price_kg = next((price for type_, price in self.filament_data if type_ == filament_type), None) # None dönsün ki hata kontrolü yapalım
            if filament_price_kg is None: messagebox.showerror("Hata", f"'{filament_type}' için fiyat bilgisi bulunamadı."); return
            filament_cost = (filament_amount / 1000.0) * filament_price_kg

            # Elektrik Maliyeti
            commercial_electricity_price = self.electricity_prices.get("ticari", 0.0); residential_electricity_price = self.electricity_prices.get("mesken", 0.0)
            electricity_consumption_kwh = (device_power * print_time) / 1000.0
            commercial_electricity_cost = electricity_consumption_kwh * commercial_electricity_price
            residential_electricity_cost = electricity_consumption_kwh * residential_electricity_price

            # Kargo Maliyeti
            company = self.shipping_company_combobox.get(); desi = self.shipping_desi_combobox.get(); shipping_cost = 0.0
            if company and desi and company in self.shipping_prices:
                shipping_cost = next((price for d, price in self.shipping_prices.get(company, []) if d == desi), 0.0)

            # Toplam Temel Maliyetler
            total_cost_commercial_base = filament_cost + commercial_electricity_cost + shipping_cost + other_costs
            total_cost_residential_base = filament_cost + residential_electricity_cost + shipping_cost + other_costs

            # Seçilen Pazaryeri Komisyonu
            selected_marketplace = self.marketplace_selection_combobox.get()
            if not selected_marketplace: messagebox.showwarning("Eksik Bilgi", "Lütfen bir satış pazaryeri seçin."); return
            marketplace_info = self.marketplaces.get(selected_marketplace, {"rate": 0.0, "fixed": 0.0})
            commission_rate = marketplace_info.get("rate", 0.0) / 100.0; fixed_commission = marketplace_info.get("fixed", 0.0)

            # Komisyon Hesabı İçin Temel Maliyet Belirleme
            costing_electricity_type = self.settings.get("costing_electricity_type", "ticari")
            base_cost_for_commission = total_cost_commercial_base if costing_electricity_type == "ticari" else total_cost_residential_base

            # Komisyon ve Komisyonlu Toplam Maliyet (Tahmini)
            estimated_commission = (base_cost_for_commission * commission_rate) + fixed_commission
            total_cost_with_commission = base_cost_for_commission + estimated_commission

            # Satış Fiyatı Hesaplama (Komisyonu Satış Fiyatından Düşecek Şekilde)
            base_cost_plus_fixed = base_cost_for_commission + fixed_commission
            denominator = (1 - commission_rate)
            if denominator <= 0: # %100 veya üzeri komisyon durumu (veya hata)
                 sale_price_50_profit_correct = float('inf') # Sonsuz veya çok büyük sayı
                 sale_price_100_profit_correct = float('inf')
                 if denominator == 0: print("Uyarı: Komisyon oranı %100, satış fiyatı sonsuz hesaplanıyor.")
                 else: print("Uyarı: Komisyon oranı %100'den büyük, satış fiyatı negatif olabilir veya tanımsız.")
            else:
                sale_price_50_profit_correct = (base_cost_plus_fixed + (base_cost_for_commission * 0.50)) / denominator
                sale_price_100_profit_correct = (base_cost_plus_fixed + (base_cost_for_commission * 1.00)) / denominator

            # --- Sonuçları Etiketlere Yazdır ---
            self.result_labels["filament_cost"].config(text=f"{filament_cost:.2f} TL")
            self.result_labels["elec_cost_comm"].config(text=f"{commercial_electricity_cost:.2f} TL")
            self.result_labels["elec_cost_res"].config(text=f"{residential_electricity_cost:.2f} TL")
            self.result_labels["shipping_cost"].config(text=f"{shipping_cost:.2f} TL")
            self.result_labels["other_costs"].config(text=f"{other_costs:.2f} TL")
            self.result_labels["total_cost_comm"].config(text=f"{total_cost_commercial_base:.2f} TL")
            self.result_labels["total_cost_res"].config(text=f"{total_cost_residential_base:.2f} TL")

            # Dinamik Etiketleri Güncelle
            komisyon_etiket_text = f"Komisyon ({selected_marketplace}):"; komisyonlu_maliyet_etiket_text = f"Toplam Maliyet Kom. ({selected_marketplace}, {costing_electricity_type.capitalize()} Elek.):"
            satis_50_etiket_text = f"%50 Kar ile Satış ({selected_marketplace}):"; satis_100_etiket_text = f"%100 Kar ile Satış ({selected_marketplace}):"
            if self.commission_label_ref: self.commission_label_ref.config(text=komisyon_etiket_text)
            if self.total_cost_commissioned_label_ref: self.total_cost_commissioned_label_ref.config(text=komisyonlu_maliyet_etiket_text)
            if self.sale_50_label_ref: self.sale_50_label_ref.config(text=satis_50_etiket_text)
            if self.sale_100_label_ref: self.sale_100_label_ref.config(text=satis_100_etiket_text)

            # Dinamik Değerleri Güncelle
            self.result_labels["commission"].config(text=f"{estimated_commission:.2f} TL (Tahmini)")
            self.result_labels["total_cost_commissioned"].config(text=f"{total_cost_with_commission:.2f} TL (Tahmini)")
            # Sonsuz sonuçları daha anlaşılır göster
            sale_50_text = f"{sale_price_50_profit_correct:.2f} TL" if sale_price_50_profit_correct != float('inf') else "Hesaplanamadı (%100+ Kom.)"
            sale_100_text = f"{sale_price_100_profit_correct:.2f} TL" if sale_price_100_profit_correct != float('inf') else "Hesaplanamadı (%100+ Kom.)"
            self.result_labels["sale_50_profit"].config(text=sale_50_text)
            self.result_labels["sale_100_profit"].config(text=sale_100_text)

        except ValueError: messagebox.showerror("Hata", "Geçersiz giriş! Lütfen tüm alanlara geçerli sayısal değerler girin.")
        except KeyError as e: messagebox.showerror("Kod Hatası", f"Sonuç etiketi anahtarı bulunamadı: {e}\nLütfen geliştirici ile iletişime geçin."); traceback.print_exc()
        except Exception as e:
             exc_type, exc_value, exc_traceback = traceback.sys.exc_info(); line_no = exc_traceback.tb_lineno if exc_traceback else 'Bilinmiyor'
             messagebox.showerror("Hesaplama Hatası", f"Hesaplama sırasında bir hata oluştu (Satır: {line_no}):\n{exc_value}"); traceback.print_exc()

    # --- Genel Ayarlar Sekmesi ---
    def create_settings_tab(self):
        """Genel ayarlar sekmesinin içeriğini oluşturur."""
        frame = ttk.Frame(self.tab3, padding=(10, 10)); frame.pack(expand=True, fill="both")
        vcmd_numeric = (self.root.register(self.validate_numeric_input), '%P')

        # Elektrik Ayarları
        elec_frame = ttk.LabelFrame(frame, text="Elektrik Fiyatları (TL/kWh)", padding=(15, 10)); elec_frame.pack(fill="x", pady=(0, 10)); elec_frame.columnconfigure(1, weight=1)
        ttk.Label(elec_frame, text="Ticari Tarife:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.commercial_electricity_entry = ttk.Entry(elec_frame, validate='key', validatecommand=vcmd_numeric); self.commercial_electricity_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.commercial_electricity_entry.insert(0, str(self.electricity_prices.get("ticari", 0.0)))
        ttk.Label(elec_frame, text="Mesken Tarife:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.residential_electricity_entry = ttk.Entry(elec_frame, validate='key', validatecommand=vcmd_numeric); self.residential_electricity_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.residential_electricity_entry.insert(0, str(self.electricity_prices.get("mesken", 0.0)))

        # Kar Hesaplama bazı
        costing_frame = ttk.LabelFrame(frame, text="Kar Hesaplama Ayarı", padding=(15, 10)); costing_frame.pack(fill="x", pady=10)
        ttk.Label(costing_frame, text="Kar Hesabı İçin Elektrik Tarifesi:").pack(side=tk.LEFT, padx=5, pady=5)
        self.costing_elec_var = tk.StringVar(value=self.settings.get("costing_electricity_type", "ticari"))
        ttk.Radiobutton(costing_frame, text="Ticari", variable=self.costing_elec_var, value="ticari").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(costing_frame, text="Mesken", variable=self.costing_elec_var, value="mesken").pack(side=tk.LEFT, padx=5)

        # Güncelleme Butonu
        ttk.Button(frame, text="Ayarları Kaydet", command=self.update_settings, style="TButton").pack(pady=15)

    def update_settings(self):
        """Genel ayarları günceller ve kaydeder."""
        try:
            comm_price_str = self.commercial_electricity_entry.get(); res_price_str = self.residential_electricity_entry.get()
            if not all([comm_price_str, res_price_str]): messagebox.showwarning("Eksik Bilgi", "Lütfen elektrik fiyat alanlarını doldurun."); return
            commercial_price = float(comm_price_str); residential_price = float(res_price_str); costing_type = self.costing_elec_var.get()
            if commercial_price < 0 or residential_price < 0: messagebox.showwarning("Geçersiz Değer", "Elektrik fiyatları negatif olamaz."); return
            self.electricity_prices["ticari"] = commercial_price; self.electricity_prices["mesken"] = residential_price; self.settings["costing_electricity_type"] = costing_type
            self.save_data(); messagebox.showinfo("Başarılı", "Genel ayarlar güncellendi ve kaydedildi.")
        except ValueError: messagebox.showerror("Hata", "Geçersiz giriş! Lütfen sayısal değerler girin.")
        except Exception as e: messagebox.showerror("Kaydetme Hatası", f"Ayarlar kaydedilirken bir hata oluştu: {e}"); traceback.print_exc()


    # --- Kargo Ücretleri Sekmesi ---
    def create_shipping_tab(self):
        """Kargo ücretleri sekmesinin içeriğini oluşturur."""
        frame = ttk.Frame(self.tab4, padding=(10, 10)); frame.pack(expand=True, fill="both"); frame.rowconfigure(1, weight=1); frame.columnconfigure(0, weight=1)

        # Giriş Alanı
        input_frame = ttk.LabelFrame(frame, text="Yeni Kargo Fiyatı Ekle/Sil", padding=(10, 10)); input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5); input_frame.columnconfigure(1, weight=1)
        ttk.Label(input_frame, text="Kargo Firması:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.shipping_company_combobox_tab4 = ttk.Combobox(input_frame, values=list(self.shipping_prices.keys()), state="readonly", width=25); self.shipping_company_combobox_tab4.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        keys = list(self.shipping_prices.keys());
        if keys: self.shipping_company_combobox_tab4.set(keys[0])
        ttk.Label(input_frame, text="Desi/Ağırlık:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.shipping_desi_entry_tab4 = ttk.Entry(input_frame, width=15); self.shipping_desi_entry_tab4.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(input_frame, text="Fiyat (TL):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        vcmd_numeric = (self.root.register(self.validate_numeric_input), '%P')
        self.shipping_price_entry_tab4 = ttk.Entry(input_frame, validate='key', validatecommand=vcmd_numeric, width=15); self.shipping_price_entry_tab4.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        button_frame = ttk.Frame(input_frame); button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Ekle", command=self.add_shipping_price, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Seçileni Sil", command=self.delete_shipping_price, width=10).pack(side=tk.LEFT, padx=5)

        # Liste Alanı
        list_frame = ttk.LabelFrame(frame, text="Kayıtlı Kargo Fiyatları", padding=(10, 10)); list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5); list_frame.rowconfigure(0, weight=1); list_frame.columnconfigure(0, weight=1)
        self.shipping_listbox = ttk.Treeview(list_frame, columns=("Firma", "Desi/Ağırlık", "Fiyat"), show="headings")
        self.shipping_listbox.heading("Firma", text="Kargo Firması"); self.shipping_listbox.heading("Desi/Ağırlık", text="Desi/Ağırlık"); self.shipping_listbox.heading("Fiyat", text="Fiyat (TL)")
        self.shipping_listbox.column("Firma", width=150, stretch=tk.YES); self.shipping_listbox.column("Desi/Ağırlık", width=100, anchor="center", stretch=tk.NO); self.shipping_listbox.column("Fiyat", width=100, anchor="e", stretch=tk.NO)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.shipping_listbox.yview); self.shipping_listbox.configure(yscrollcommand=scrollbar.set)
        self.shipping_listbox.grid(row=0, column=0, sticky="nsew"); scrollbar.grid(row=0, column=1, sticky="ns")
        self.refresh_shipping_list()

    def add_shipping_price(self):
        """Yeni kargo fiyatı ekler."""
        company = self.shipping_company_combobox_tab4.get(); desi = self.shipping_desi_entry_tab4.get().strip(); price_str = self.shipping_price_entry_tab4.get()
        if not company: messagebox.showwarning("Eksik Bilgi", "Lütfen bir kargo firması seçin."); return
        if not desi: messagebox.showwarning("Eksik Bilgi", "Desi/Ağırlık alanı boş bırakılamaz."); return
        if not price_str: messagebox.showwarning("Eksik Bilgi", "Fiyat alanı boş bırakılamaz."); return
        try:
            price = float(price_str)
            if price < 0: messagebox.showwarning("Geçersiz Değer", "Fiyat negatif olamaz."); return
            # Aynı firma ve desi için kontrol
            if any(item[0] == desi for item in self.shipping_prices.get(company, [])): messagebox.showwarning("Mevcut Kayıt", f"{company} için '{desi}' desi/ağırlık değeri zaten mevcut."); return
            if company not in self.shipping_prices: self.shipping_prices[company] = []
            self.shipping_prices[company].append((desi, price))
            # Ekleme sonrası sıralama (Desi'ye göre)
            def sort_key(item):
                 try: return (0, float(item[0]))
                 except ValueError: return (1, item[0])
            self.shipping_prices[company].sort(key=sort_key)
            self.refresh_shipping_list(); self.shipping_desi_entry_tab4.delete(0, tk.END); self.shipping_price_entry_tab4.delete(0, tk.END)
            self.update_shipping_comboboxes(); self.save_data()
        except ValueError: messagebox.showerror("Hata", "Fiyat geçersiz! Lütfen sayısal bir değer girin.")
        except Exception as e: messagebox.showerror("Hata", f"Kargo fiyatı eklenirken hata: {e}"); traceback.print_exc()

    def delete_shipping_price(self):
        """Seçili kargo fiyatını siler."""
        selected_items = self.shipping_listbox.selection()
        if not selected_items: messagebox.showwarning("Seçim Yapılmadı", "Lütfen silmek için listeden bir kargo fiyatı seçin."); return
        selected_item = selected_items[0]
        try:
             item_values = self.shipping_listbox.item(selected_item, "values"); company, desi, _ = item_values
        except IndexError: messagebox.showerror("Hata", "Seçili öğe bilgisi alınamadı."); return

        confirm = messagebox.askyesno("Silme Onayı", f"'{company}' firmasından '{desi}' desi/ağırlık kaydını silmek istediğinizden emin misiniz?")
        if confirm:
            if company in self.shipping_prices:
                original_len = len(self.shipping_prices[company])
                self.shipping_prices[company] = [item for item in self.shipping_prices[company] if item[0] != desi]
                if len(self.shipping_prices[company]) < original_len: # Başarılı silme
                     self.refresh_shipping_list(); self.update_shipping_comboboxes(); self.save_data()
                else:
                     print(f"Silinecek kargo kaydı ({company} - {desi}) bulunamadı.") # Nadir durum
            else:
                 print(f"Silinecek kargo firması ({company}) bulunamadı.") # Nadir durum


    def refresh_shipping_list(self):
        """Kargo listesini (Treeview) temizler ve yeniden doldurur."""
        for item in self.shipping_listbox.get_children(): self.shipping_listbox.delete(item)
        # Firmaları isme göre sırala
        for company in sorted(self.shipping_prices.keys(), key=str.lower):
             # Desileri sıralı (ekleme sırasında sıralandığı varsayılır)
            for desi, price in self.shipping_prices.get(company, []):
                self.shipping_listbox.insert("", tk.END, values=(company, desi, f"{price:.2f}"))

    def update_shipping_comboboxes(self):
        """Tüm kargo ile ilgili combobox'ları günceller."""
        companies = sorted(list(self.shipping_prices.keys()), key=str.lower)
        # Kargo sekmesindeki firma listesi
        self.shipping_company_combobox_tab4['values'] = companies
        # Hesaplama sekmesindeki firma listesi
        self.shipping_company_combobox['values'] = companies
        # Hesaplama sekmesindeki desi listesini de güncelle (eğer firma seçiliyse)
        self.update_shipping_desi_combobox()

    # --- Pazaryeri Ayarları Sekmesi ---
    def create_marketplace_tab(self):
        """Pazaryeri ayarları sekmesinin içeriğini oluşturur."""
        frame = ttk.Frame(self.tab5, padding=(10, 10)); frame.pack(expand=True, fill="both"); frame.rowconfigure(1, weight=1); frame.columnconfigure(0, weight=1)

        # Giriş Alanı
        input_frame = ttk.LabelFrame(frame, text="Pazaryeri Ekle/Düzenle", padding=(10, 10)); input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5); input_frame.columnconfigure(1, weight=1)
        ttk.Label(input_frame, text="Pazaryeri Adı:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.marketplace_name_entry = ttk.Entry(input_frame, width=30); self.marketplace_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        vcmd_numeric = (self.root.register(self.validate_numeric_input), '%P')
        ttk.Label(input_frame, text="Komisyon Oranı (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.marketplace_rate_entry = ttk.Entry(input_frame, validate='key', validatecommand=vcmd_numeric, width=15); self.marketplace_rate_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(input_frame, text="Sabit Komisyon (TL):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.marketplace_fixed_entry = ttk.Entry(input_frame, validate='key', validatecommand=vcmd_numeric, width=15); self.marketplace_fixed_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        button_frame = ttk.Frame(input_frame); button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.save_update_marketplace_button = ttk.Button(button_frame, text="Ekle", command=self.save_update_marketplace, width=12); self.save_update_marketplace_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Seçileni Sil", command=self.delete_marketplace, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Temizle/Yeni", command=self.clear_marketplace_fields, width=12).pack(side=tk.LEFT, padx=5)

        # Liste Alanı
        list_frame = ttk.LabelFrame(frame, text="Kayıtlı Pazaryerleri", padding=(10, 10)); list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5); list_frame.rowconfigure(0, weight=1); list_frame.columnconfigure(0, weight=1)
        self.marketplace_listbox = ttk.Treeview(list_frame, columns=("Ad", "Oran", "Sabit"), show="headings")
        self.marketplace_listbox.heading("Ad", text="Pazaryeri Adı"); self.marketplace_listbox.heading("Oran", text="Komisyon Oranı (%)"); self.marketplace_listbox.heading("Sabit", text="Sabit Komisyon (TL)")
        self.marketplace_listbox.column("Ad", width=200, stretch=tk.YES); self.marketplace_listbox.column("Oran", width=150, anchor="e", stretch=tk.NO); self.marketplace_listbox.column("Sabit", width=150, anchor="e", stretch=tk.NO)
        self.marketplace_listbox.bind("<<TreeviewSelect>>", self.load_marketplace_for_edit)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.marketplace_listbox.yview); self.marketplace_listbox.configure(yscrollcommand=scrollbar.set)
        self.marketplace_listbox.grid(row=0, column=0, sticky="nsew"); scrollbar.grid(row=0, column=1, sticky="ns")
        self.refresh_marketplace_list(); self.clear_marketplace_fields()

    def refresh_marketplace_list(self):
        """Pazaryeri listesini (Treeview) temizler ve yeniden doldurur."""
        for item in self.marketplace_listbox.get_children(): self.marketplace_listbox.delete(item)
        # İsimlere göre sıralanmış olarak ekle
        for name in sorted(self.marketplaces.keys(), key=str.lower):
            data = self.marketplaces[name]; rate = data.get('rate', 0.0); fixed = data.get('fixed', 0.0)
            # Item ID için basit bir yöntem (boşluk yerine _)
            item_id = name.replace(" ", "_").replace("/","_") # ID'de / olmasın
            # Aynı ID varsa sonuna ek ekle (çok nadir ama garanti)
            base_id = item_id
            count = 0
            while self.marketplace_listbox.exists(item_id):
                 count += 1
                 item_id = f"{base_id}_{count}"

            self.marketplace_listbox.insert("", tk.END, iid=item_id, values=(name, f"{rate:.2f}", f"{fixed:.2f}"))

    def clear_marketplace_fields(self):
        """Pazaryeri giriş alanlarını temizler ve Ekle moduna geçer."""
        self.selected_marketplace_id = None; self.marketplace_name_entry.config(state='normal')
        self.marketplace_name_entry.delete(0, tk.END); self.marketplace_rate_entry.delete(0, tk.END)
        self.marketplace_fixed_entry.delete(0, tk.END); self.save_update_marketplace_button.config(text="Ekle")
        # Treeview seçimini kaldır
        if self.marketplace_listbox.selection():
            self.marketplace_listbox.selection_set("")

    def load_marketplace_for_edit(self, event=None):
        """Treeview'dan seçilen pazaryerinin bilgilerini giriş alanlarına yükler."""
        selected_items = self.marketplace_listbox.selection()
        if not selected_items: self.clear_marketplace_fields(); return
        selected_item_id = selected_items[0] # Bu bizim verdiğimiz iid
        try:
            marketplace_name = self.marketplace_listbox.item(selected_item_id, "values")[0]
        except (IndexError, tk.TclError): # TclError: invalid command name ".!notebook.!frame5.!labelframe2.!treeview"
             # Bazen seçim kaldırıldığında hatalı event gelebiliyor
             self.clear_marketplace_fields()
             return

        if marketplace_name in self.marketplaces:
            self.selected_marketplace_id = marketplace_name # Düzenlenecek ismi sakla
            data = self.marketplaces[marketplace_name]; rate = data.get('rate', 0.0); fixed = data.get('fixed', 0.0)
            self.marketplace_name_entry.config(state='normal'); self.marketplace_name_entry.delete(0, tk.END); self.marketplace_name_entry.insert(0, marketplace_name)
            # İsim alanını düzenlemeye kapatmak daha güvenli olabilir:
            # self.marketplace_name_entry.config(state='disabled')
            self.marketplace_rate_entry.delete(0, tk.END); self.marketplace_rate_entry.insert(0, f"{rate:.2f}")
            self.marketplace_fixed_entry.delete(0, tk.END); self.marketplace_fixed_entry.insert(0, f"{fixed:.2f}")
            self.save_update_marketplace_button.config(text="Güncelle") # Buton metnini değiştir
        else:
             # Veri ile liste tutarsızsa (olmamalı) temizle
             self.clear_marketplace_fields()

    # --- DÜZELTİLMİŞ FONKSİYON ---
    def save_update_marketplace(self):
        """Yeni pazaryeri ekler veya mevcut olanı günceller. (Girinti Düzeltildi)"""
        name = self.marketplace_name_entry.get().strip()
        rate_str = self.marketplace_rate_entry.get()
        fixed_str = self.marketplace_fixed_entry.get()

        if not name: messagebox.showwarning("Eksik Bilgi", "Pazaryeri adı boş bırakılamaz."); return
        if not rate_str: messagebox.showwarning("Eksik Bilgi", "Komisyon oranı boş bırakılamaz."); return
        if not fixed_str: messagebox.showwarning("Eksik Bilgi", "Sabit komisyon boş bırakılamaz."); return

        try:
            rate = float(rate_str); fixed = float(fixed_str)
            if rate < 0 or fixed < 0: messagebox.showwarning("Geçersiz Değer", "Sayısal değerler negatif olamaz."); return

            action_message = ""
            # Eğer selected_marketplace_id varsa GÜNCELLEME yapılıyor
            if self.selected_marketplace_id:
                original_name = self.selected_marketplace_id
                # İsim değişikliği yapıldı mı kontrol et
                if name != original_name:
                    # Yeni isim zaten var mı?
                    if name in self.marketplaces:
                        messagebox.showwarning("Mevcut İsim", f"'{name}' adında başka bir pazaryeri zaten var.")
                        return
                    # Eski kaydı sil (güvenli kontrol ile)
                    if original_name in self.marketplaces:
                        del self.marketplaces[original_name]
                    else:
                         print(f"Uyarı: Güncellenmeye çalışılan eski isim '{original_name}' zaten mevcut değildi.")

                # Yeni veya mevcut isimle güncelle/ekle
                self.marketplaces[name] = {"rate": rate, "fixed": fixed}
                action_message = "güncellendi"

            # Yoksa YENİ EKLEME yapılıyor
            else:
                if name in self.marketplaces:
                    messagebox.showwarning("Mevcut Pazaryeri", f"'{name}' adında bir pazaryeri zaten mevcut.")
                    return
                self.marketplaces[name] = {"rate": rate, "fixed": fixed}
                action_message = "eklendi"

            # Ortak işlemler
            self.save_data()
            self.refresh_marketplace_list()
            self.update_marketplace_combobox() # Diğer combobox'ı da güncelle
            self.clear_marketplace_fields() # Alanları temizle
            messagebox.showinfo("Başarılı", f"Pazaryeri '{name}' başarıyla {action_message}.")

        except ValueError: messagebox.showerror("Hata", "Oran ve Sabit Komisyon için geçerli sayısal değerler girin.")
        except Exception as e: messagebox.showerror("Hata", f"Pazaryeri kaydedilirken/güncellenirken bir hata oluştu: {e}"); traceback.print_exc()

    def delete_marketplace(self):
        """Seçili pazaryerini siler."""
        selected_items = self.marketplace_listbox.selection()
        if not selected_items: messagebox.showwarning("Seçim Yapılmadı", "Lütfen silmek için listeden bir pazaryeri seçin."); return
        selected_item_id = selected_items[0] # Bu bizim verdiğimiz iid
        try:
            marketplace_name = self.marketplace_listbox.item(selected_item_id, "values")[0]
        except (IndexError, tk.TclError): messagebox.showerror("Hata", "Seçili öğe bilgisi alınamadı."); return

        confirm = messagebox.askyesno("Silme Onayı", f"'{marketplace_name}' pazaryerini silmek istediğinizden emin misiniz?")
        if confirm:
            if marketplace_name in self.marketplaces:
                del self.marketplaces[marketplace_name]
                self.save_data()
                self.refresh_marketplace_list()
                self.update_marketplace_combobox()
                self.clear_marketplace_fields() # Seçim kalktığı için temizle
                messagebox.showinfo("Başarılı", f"'{marketplace_name}' pazaryeri silindi.")
            else: messagebox.showerror("Hata", f"'{marketplace_name}' veritabanında bulunamadı (Bu bir iç hata olabilir).")

# --- Uygulamayı Başlat ---
if __name__ == "__main__":
    root = tk.Tk()

    # Pencereyi Ortala
    window_width = 950; window_height = 750
    screen_width = root.winfo_screenwidth(); screen_height = root.winfo_screenheight()
    center_x = max(0, int(screen_width/2 - window_width / 2))
    center_y = max(0, int(screen_height/2 - window_height / 2))
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    root.minsize(750, 650) # Uygulamanın küçülebileceği minimum boyut

    # Uygulama sınıfını başlat
    app = App(root)

    # <<< Pencerenin daha hızlı görünmesi için >>>
    # Widget'ların çizilmesi ve boyutlandırılması gibi bekleyen işlemleri yapmaya zorlar.
    root.update_idletasks()

    # Tkinter olay döngüsünü başlat (Bu satır programı çalışır tutar)
    root.mainloop()