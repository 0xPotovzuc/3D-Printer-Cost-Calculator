import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import customtkinter as ctk
import json
import os
import sys
import traceback
import webbrowser
from typing import Dict, List, Any, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import shutil
from collections import defaultdict

# --- UYGULAMA SABİTLERİ ---
APP_NAME = "3D Baskı Maliyet & Kar Hesaplayıcı Pro"
APP_VERSION = "4.0" # Sürüm isteğiniz üzerine güncellendi
DATA_FILE_NAME = "app_data.json"

# --- YENİ: DOĞRU DOSYA YOLUNU BULMA FONKSİYONU ---
def get_resource_path(relative_path):
    """
    Uygulama verilerinin yolunu, programın çalıştırıldığı ortama
    (hem geliştirme hem de derlenmiş .exe) göre doğru bir şekilde belirler.
    Bu fonksiyon, "No such file or directory" hatasını çözer.
    """
    if getattr(sys, 'frozen', False):
        # Program derlenmişse (.exe), çalıştırılabilir dosyanın yanına bakar.
        base_path = os.path.dirname(sys.executable)
    else:
        # Program normal bir Python betiği olarak çalıştırılıyorsa,
        # betik dosyasının yanına bakar.
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# JSON veri yapısı için anahtarlar
KEY_FILAMENTS = "filament_data"
KEY_ELECTRICITY = "electricity_prices"
KEY_SHIPPING = "shipping_prices"
KEY_MARKETPLACES = "marketplaces"
KEY_SETTINGS = "settings"
KEY_SALES_HISTORY = "sales_history"
KEY_INVENTORY = "filament_inventory"

# Varsayılan değerler
DEFAULT_ELECTRICITY = {"ticari": 5.54, "mesken": 3.11}
DEFAULT_MARKETPLACES = {
    "Diğer/Yok": {"rate": 0.0, "fixed": 0.0, "vat_type": "Dahil"}
}
DEFAULT_SETTINGS = {
    "costing_electricity_type": "ticari",
    "default_device_power": 130.0,
    "general_vat_rate": 20.0,
    "withholding_tax_rate": 1.0,
    "high_precision": False,
}
DISCORD_USER_ID = "351410962336841748"

# Varsayılan temayı ayarla
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# Dil çevirileri için (sadeleştirilmiş)
_ = lambda message: message

# --- Yardımcı Sınıflar ---

class CustomSaleDialog(ctk.CTkToplevel):
    """Ürün adı, satış fiyatı ve müşteri notu girişi için özel dialog penceresi."""
    def __init__(self, parent, title, initial_price=""):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.parent = parent
        self.result = None
        self.geometry("400x300")

        ctk.CTkLabel(self, text=_("Ürün Adı:"), wraplength=350).pack(pady=(20, 5), padx=20, anchor="w")
        self.product_entry = ctk.CTkEntry(self, width=360)
        self.product_entry.pack(pady=0, padx=20, fill="x")
        self.product_entry.focus_set()

        ctk.CTkLabel(self, text=_("Nihai Satış Fiyatı (KDV Dahil):"), wraplength=350).pack(pady=(10, 5), padx=20, anchor="w")
        vcmd_numeric = (self.register(self.validate_numeric_input), '%P')
        self.price_entry = ctk.CTkEntry(self, width=360, validate='key', validatecommand=vcmd_numeric)
        self.price_entry.insert(0, initial_price)
        self.price_entry.pack(pady=0, padx=20, fill="x")
        
        ctk.CTkLabel(self, text=_("Müşteri / Not:"), wraplength=350).pack(pady=(10, 5), padx=20, anchor="w")
        self.note_entry = ctk.CTkEntry(self, width=360)
        self.note_entry.pack(pady=0, padx=20, fill="x")
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20, padx=20, fill="x", expand=True)
        
        ok_button = ctk.CTkButton(button_frame, text=_("Tamam"), command=self.on_ok)
        ok_button.pack(side="right", padx=(10, 0))
        
        cancel_button = ctk.CTkButton(button_frame, text=_("İptal"), command=self.on_cancel, fg_color="gray", hover_color="darkgray")
        cancel_button.pack(side="right")
        
        self.bind("<Return>", self.on_ok)
        self.bind("<Escape>", self.on_cancel)
        
        self.update_idletasks()
        self.center_window()
        self.grab_set()
        self.wait_window(self)

    def validate_numeric_input(self, P: str) -> bool:
        if P == "" or P == ".": return True
        try:
            float(P)
            return True
        except ValueError:
            return False

    def center_window(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"+{x}+{y}")

    def on_ok(self, event=None):
        product_name = self.product_entry.get().strip()
        sale_price = self.price_entry.get().strip()
        note = self.note_entry.get().strip()
        if not product_name or not sale_price:
            messagebox.showwarning(_("Eksik Bilgi"), _("Ürün adı ve satış fiyatı boş bırakılamaz."), parent=self)
            return
        try:
            price_float = float(sale_price)
            self.result = {"product_name": product_name, "sale_price": price_float, "note": note}
            self.destroy()
        except ValueError:
            messagebox.showerror(_("Geçersiz Fiyat"), _("Lütfen satış fiyatı için geçerli bir sayı girin."), parent=self)

    def on_cancel(self, event=None):
        self.result = None
        self.destroy()

class CostCalculatorApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self._setup_window()
        
        self.status_var = ctk.StringVar()
        self.filaments: List[Tuple[str, float]] = []
        self.electricity_prices: Dict[str, float] = DEFAULT_ELECTRICITY.copy()
        self.shipping_prices: Dict[str, List[Tuple[str, float]]] = {}
        self.marketplaces: Dict[str, Dict[str, Any]] = {}
        self.settings: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self.sales_history: List[Dict[str, Any]] = []
        self.filament_inventory: Dict[str, float] = {}  
        self.selected_marketplace_name: str | None = None
        self.last_calculation_results: Dict[str, Any] | None = None
        self.last_calculation_inputs: Dict[str, Any] | None = None

        self.frames = {}
        self.nav_buttons = {}

        self._load_data()
        self._create_widgets()
        self.update_status(_("Uygulama başarıyla başlatıldı."))
        self._populate_all_widgets()

    def _setup_window(self):
        self.root.title(f"{APP_NAME} - v{APP_VERSION}")
        self.root.geometry("1250x900")
        self.root.minsize(1150, 800)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self.root, fg_color="white")
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        nav_outer_frame = ctk.CTkFrame(main_frame, height=50, fg_color="white")
        nav_outer_frame.pack(fill="x", side="top")
        
        nav_frame = ctk.CTkFrame(nav_outer_frame, fg_color="white")
        nav_frame.pack(expand=True, padx=5, pady=5)

        separator = ctk.CTkFrame(main_frame, height=2, corner_radius=0)
        separator.pack(fill='x', pady=5)

        container = ctk.CTkFrame(main_frame, fg_color="white")
        container.pack(expand=True, fill="both")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        pages = {
            _("Hesaplayıcı"): ("🧾", self._create_cost_profit_tab),
            _("Satış Geçmişi"): ("📊", self._create_sales_history_tab),
            _("Filamentler & Envanter"): ("🧵", self._create_filament_tab),
            _("Pazaryerleri"): ("🏪", self._create_marketplace_tab),
            _("Kargo"): ("🚚", self._create_shipping_tab),
            _("Ayarlar"): ("⚙️", self._create_settings_tab)
        }

        for i, (page_name, (icon, creation_method)) in enumerate(pages.items()):
            button = ctk.CTkButton(nav_frame, text=f" {icon}  {page_name}", 
                                command=lambda p=page_name: self._show_frame(p))
            button.grid(row=0, column=i, padx=4)
            self.nav_buttons[page_name] = button

            frame = creation_method(container)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Bu satır _create_widgets'in sonuna taşındı çünkü widget'lar artık mevcut.
        # self._populate_all_widgets() 
        self._show_frame(_("Hesaplayıcı"))

        status_bar = ctk.CTkLabel(self.root, textvariable=self.status_var, height=30, anchor='w', 
                                  corner_radius=0, fg_color=("gray85", "gray25"))
        status_bar.pack(side="bottom", fill="x")

    def _show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        for name, button in self.nav_buttons.items():
            if name == page_name:
                button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])
            else:
                button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.update_status(f"{page_name} {_('sekmesi açıldı.')}")

    def _populate_all_widgets(self):
        """Tüm widget'ları başlangıç verileriyle doldurur."""
        self._refresh_filament_list()
        self._update_filament_combobox()
        self._refresh_shipping_list()
        self._update_all_shipping_comboboxes()
        self._refresh_marketplace_list()
        self._update_all_marketplace_comboboxes()
        self._clear_marketplace_fields()
        self._update_sales_summary() # Bu, refresh_history'den önce çağrılmalı ki combobox dolsun
        self._refresh_sales_history_list()
        default_power = self.settings.get("default_device_power", 130.0)
        self.cost_entries["device_power"].delete(0, tk.END)
        self.cost_entries["device_power"].insert(0, str(default_power))

    def _load_data(self):
        # DEĞİŞİKLİK: Yeni fonksiyon kullanılıyor
        data_path = get_resource_path(DATA_FILE_NAME)
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.filaments = data.get(KEY_FILAMENTS, [])
                    loaded_settings = data.get(KEY_SETTINGS, {})
                    self.settings = {**DEFAULT_SETTINGS, **loaded_settings}
                    self.electricity_prices.update(data.get(KEY_ELECTRICITY, {}))
                    self.shipping_prices = data.get(KEY_SHIPPING, {})
                    loaded_marketplaces = data.get(KEY_MARKETPLACES, {})
                    self.marketplaces = DEFAULT_MARKETPLACES.copy()
                    for name, details in loaded_marketplaces.items():
                        if isinstance(details, dict):
                            if 'vat_type' not in details: details['vat_type'] = 'Dahil'
                            self.marketplaces[name] = details
                    self.sales_history = data.get(KEY_SALES_HISTORY, [])
                    self.filament_inventory = data.get(KEY_INVENTORY, {})
            except (json.JSONDecodeError, TypeError):
                messagebox.showwarning(_("Yükleme Hatası"), f"{DATA_FILE_NAME} {_('dosyası bozuk. Varsayılanlar kullanılacak.')}")
                self.marketplaces = DEFAULT_MARKETPLACES.copy()
                self.settings = DEFAULT_SETTINGS.copy()
                self.sales_history = []
                self.filament_inventory = {}
        else:
            self.marketplaces = DEFAULT_MARKETPLACES.copy()
            self.settings = DEFAULT_SETTINGS.copy()
            self.sales_history = []
            self.filament_inventory = {}
            self._save_data()

    def _save_data(self):
        # DEĞİŞİKLİK: Yeni fonksiyon kullanılıyor
        data_path = get_resource_path(DATA_FILE_NAME)
        data_to_save = {
            KEY_FILAMENTS: self.filaments,
            KEY_ELECTRICITY: self.electricity_prices,
            KEY_SHIPPING: self.shipping_prices,
            KEY_MARKETPLACES: self.marketplaces,
            KEY_SETTINGS: self.settings,
            KEY_SALES_HISTORY: self.sales_history,
            KEY_INVENTORY: self.filament_inventory,
        }
        try:
            with open(data_path, "w", encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            self.update_status(_("Değişiklikler başarıyla kaydedildi."))
        except Exception as e:
            messagebox.showerror(_("Kaydetme Hatası"), f"{_('Veri kaydedilirken bir hata oluştu')}: {e}")

    def _on_close(self):
        self._save_data()
        self.root.destroy()

    def _validate_numeric_input(self, P: str) -> bool:
        if P == "" or P == ".": return True
        try:
            val = float(P)
            return val >= 0
        except ValueError:
            return False

    def update_status(self, message: str):
        self.status_var.set(f" {message}")

    def _create_treeview(self, parent, columns, headings):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black", rowheight=25)
        style.map("Treeview", background=[("selected", "#3470B6")], foreground=[("selected", "white")])

        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col, heading in zip(columns, headings): tree.heading(col, text=heading)
        tree.grid(row=0, column=0, sticky="nsew")

        vsb = ctk.CTkScrollbar(parent, orientation="vertical", command=tree.yview)
        hsb = ctk.CTkScrollbar(parent, orientation="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        return tree

    def _create_tab_frame(self, parent):
        tab_frame = ctk.CTkFrame(parent, corner_radius=0, fg_color="white")
        return tab_frame
        
    def _create_filament_tab(self, parent: ctk.CTkFrame):
        page = self._create_tab_frame(parent)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        page.rowconfigure(2, weight=0)

        input_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        input_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text=_("Yeni Filament Ekle"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, pady=(5,10), sticky="w")

        ctk.CTkLabel(input_frame, text=_("Filament Türü:"), text_color="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.filament_type_entry = ctk.CTkEntry(input_frame)
        self.filament_type_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text=_("Fiyat (TL/kg):"), text_color="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        vcmd_numeric = (self.root.register(self._validate_numeric_input), '%P')
        self.filament_price_entry = ctk.CTkEntry(input_frame, validate='key', validatecommand=vcmd_numeric)
        self.filament_price_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        btn_frame_add = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_frame_add.grid(row=3, column=0, columnspan=2, pady=10)
        
        ctk.CTkButton(btn_frame_add, text=_("Ekle"), command=self._add_filament).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame_add, text=_("Seçileni Sil"), command=self._delete_filament, fg_color="red").pack(side=tk.LEFT, padx=5)

        list_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 5))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("Tür", "Fiyat", "Envanter")
        headings = (_("Filament Türü"), _("Fiyat (TL/kg)"), _("Envanter (g)"))
        self.filament_tree = self._create_treeview(list_frame, columns, headings)
        self.filament_tree.column("Fiyat", width=120, anchor="e", stretch=tk.NO)
        self.filament_tree.column("Envanter", width=120, anchor="e", stretch=tk.NO)
        self.filament_tree.bind("<<TreeviewSelect>>", self._on_filament_select)
        
        inventory_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        inventory_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        inventory_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(inventory_frame, text=_("Seçili Envanteri Güncelle"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(inventory_frame, text=_("Filament:"), text_color="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.selected_filament_label = ctk.CTkLabel(inventory_frame, text=_("Lütfen listeden seçin"), text_color="black", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.selected_filament_label.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(inventory_frame, text=_("Yeni Miktar (g):"), text_color="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.inventory_amount_entry = ctk.CTkEntry(inventory_frame, validate='key', validatecommand=vcmd_numeric)
        self.inventory_amount_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkButton(inventory_frame, text=_("Güncelle"), command=self._update_selected_inventory).grid(row=2, column=2, padx=10, pady=5)
        
        return page

    def _on_filament_select(self, event=None):
        selected_items = self.filament_tree.selection()
        if not selected_items:
            self.selected_filament_label.configure(text=_("Lütfen listeden seçin"))
            self.inventory_amount_entry.delete(0, tk.END)
            return
        
        item_values = self.filament_tree.item(selected_items[0], "values")
        f_type = item_values[0]
        inventory_amount = self.filament_inventory.get(f_type, 0.0)
        
        self.selected_filament_label.configure(text=f_type)
        self.inventory_amount_entry.delete(0, tk.END)
        self.inventory_amount_entry.insert(0, f"{inventory_amount:.2f}")

    def _update_selected_inventory(self):
        f_type = self.selected_filament_label.cget("text")
        amount_str = self.inventory_amount_entry.get()
        
        if f_type == _("Lütfen listeden seçin") or not amount_str:
            messagebox.showwarning(_("Eksik Bilgi"), _("Lütfen listeden bir filament seçin ve miktar girin."))
            return
            
        try:
            amount = float(amount_str)
            self.filament_inventory[f_type] = amount
            self._save_data()
            self._refresh_filament_list()
            self.update_status(f"'{f_type}' {_('envanteri güncellendi.')}")
        except ValueError:
            messagebox.showerror(_("Hata"), _("Miktar için geçerli sayısal bir değer girin."))

    def _create_cost_profit_tab(self, parent: ctk.CTkFrame):
        page = self._create_tab_frame(parent)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=2)
        page.rowconfigure(0, weight=1)
        
        left_panel = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        
        right_panel = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        vcmd_numeric = (self.root.register(self._validate_numeric_input), '%P')
        
        input_frame = ctk.CTkFrame(left_panel, fg_color="white")
        input_frame.pack(fill="x", expand=False, padx=10, pady=10)
        input_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(input_frame, text=_("Baskı Bilgileri"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        self.cost_entries = {}
        input_fields = {
            "filament_amount": _("Filament Miktarı (g):"),
            "print_time": _("Baskı Süresi (saat):"),
            "device_power": _("Cihaz Gücü (W):")
        }
        for i, (key, text) in enumerate(input_fields.items()):
            ctk.CTkLabel(input_frame, text=text, text_color="black").grid(row=i + 1, column=0, padx=5, pady=5, sticky="w")
            entry = ctk.CTkEntry(input_frame, validate='key', validatecommand=vcmd_numeric)
            entry.grid(row=i + 1, column=1, padx=5, pady=5, sticky="ew")
            self.cost_entries[key] = entry
            
        ctk.CTkLabel(input_frame, text=_("Filament Türü:"), text_color="black").grid(row=len(input_fields) + 1, column=0, padx=5, pady=5, sticky="w")
        self.calc_filament_combo = ctk.CTkComboBox(input_frame, state="readonly", values=[])
        self.calc_filament_combo.grid(row=len(input_fields) + 1, column=1, padx=5, pady=5, sticky="ew")
        
        extra_frame = ctk.CTkFrame(left_panel, fg_color="white")
        extra_frame.pack(fill="x", expand=False, padx=10, pady=10)
        extra_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(extra_frame, text=_("Ek Maliyetler ve Kar"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        ctk.CTkLabel(extra_frame, text=_("İstenen Kar Oranı (%):"), text_color="black").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.profit_margin_entry = ctk.CTkEntry(extra_frame, validate='key', validatecommand=vcmd_numeric)
        self.profit_margin_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.profit_margin_entry.insert(0, "100.0")
        
        ctk.CTkLabel(extra_frame, text=_("Diğer Giderler (TL):"), text_color="black").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.other_costs_entry = ctk.CTkEntry(extra_frame, validate='key', validatecommand=vcmd_numeric)
        self.other_costs_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.other_costs_entry.insert(0, "0.0")

        expenses_frame = ctk.CTkFrame(left_panel, fg_color="white")
        expenses_frame.pack(fill="x", expand=False, padx=10, pady=10)
        expenses_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(expenses_frame, text=_("Giderler ve Kesintiler"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        self.apply_shipping_var = ctk.BooleanVar(value=False)
        self.apply_shipping_check = ctk.CTkCheckBox(expenses_frame, text=_("Kargo Ücreti Ekle"), variable=self.apply_shipping_var, command=self._toggle_shipping_widgets, text_color="black")
        self.apply_shipping_check.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        self.calc_shipping_company_combo = ctk.CTkComboBox(expenses_frame, state="disabled", width=150, values=[])
        self.calc_shipping_company_combo.grid(row=2, column=0, padx=(25, 5), pady=5, sticky="ew")
        self.calc_shipping_company_combo.bind("<<ComboboxSelected>>", self._update_shipping_desi_combobox)
        
        self.calc_shipping_desi_combo = ctk.CTkComboBox(expenses_frame, state="disabled", width=150, values=[])
        self.calc_shipping_desi_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        self.dynamic_commission_frame = ctk.CTkFrame(expenses_frame, fg_color="transparent")
        self.dynamic_commission_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5)
        self.dynamic_commission_frame.columnconfigure(0, weight=1)
        self.dynamic_commission_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(self.dynamic_commission_frame, text=_("Pazaryeri:"), text_color="black").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.calc_marketplace_combo = ctk.CTkComboBox(self.dynamic_commission_frame, state="readonly", values=[])
        self.calc_marketplace_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.calc_marketplace_combo.bind("<<ComboboxSelected>>", self._update_dynamic_commission_fields)

        ctk.CTkLabel(self.dynamic_commission_frame, text=_("Komisyon Oranı (%):"), text_color="black").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.dynamic_commission_entry = ctk.CTkEntry(self.dynamic_commission_frame, validate='key', validatecommand=vcmd_numeric)
        self.dynamic_commission_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.mplace_vat_type_var = ctk.StringVar(value=_("Dahil"))
        vat_type_combo = ctk.CTkComboBox(self.dynamic_commission_frame, variable=self.mplace_vat_type_var, values=[_("Dahil"), _("Hariç")], state="readonly")
        vat_type_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(self.dynamic_commission_frame, text=_("Komisyon KDV Tipi:"), text_color="black").grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.apply_vat_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(expenses_frame, text=_("Genel KDV Uygula"), variable=self.apply_vat_var, text_color="black").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.apply_withholding_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(expenses_frame, text=_("Pazaryeri Stopajı Uygula"), variable=self.apply_withholding_var, text_color="black").grid(row=4, column=1, sticky='w', padx=5, pady=2)
        
        ctk.CTkButton(left_panel, text=_("Hesapla"), command=self._calculate_and_display, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 5), padx=10, fill='x', ipady=5)
        
        note_label = ctk.CTkLabel(left_panel, 
                                  text=_('Not: "Kargo Ücreti Ekle" seçeneği sonrası desi listesi güncellenmezse,\n'
                                         'kutucuğu bir kez kapatıp açmayı deneyin.'),
                                  font=ctk.CTkFont(size=10), 
                                  text_color="gray50",
                                  justify="left")
        note_label.pack(pady=(0, 10), padx=15, fill='x', anchor='w')

        results_frame = ctk.CTkFrame(right_panel, fg_color="white")
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        results_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(results_frame, text=_("Hesaplama Sonuçları"), font=ctk.CTkFont(size=16, weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        self.result_labels: Dict[str, ctk.CTkLabel] = {}
        result_fields = {
            # --- Maliyet ve Kar ---
            "filament_cost": _("Filament Maliyeti:"),
            "elec_cost": _("Elektrik Maliyeti:"),
            "shipping_cost": _("Kargo Maliyeti:"),
            "other_costs": _("Diğer Giderler:"),
            "sep1": None,
            "total_base_cost": _("Toplam Temel Maliyet:"),
            "profit_amount": _("İstenen Kar Tutarı:"),
            "sep2": None,
            # --- Giderler ve Vergisiz Fiyat ---
            "commission": _("Platform Komisyonu:"),
            "withholding_tax": _("Pazaryeri Stopajı:"),
            "total_expenses_without_vat": _("Toplam Gider (Vergisiz):"),
            "pre_vat_price": _("Satış Fiyatı (KDV Hariç):"),
            "sep3": None,
            # --- Nihai Hesaplama ---
            "vat_on_sale": _("Eklenecek Satış KDV'si:"),
            "custom_sale_price": _("Nihai Satış Fiyatı (KDV Dahil):"),
            "net_profit": _("Ele Geçecek Net Kar:"),
        }
        row_counter = 1
        for key, text in result_fields.items():
            if text is None:
                ctk.CTkFrame(results_frame, height=2, corner_radius=0).grid(row=row_counter, column=0, columnspan=2, sticky='ew', pady=6)
            else:
                label_widget = ctk.CTkLabel(results_frame, text=text, anchor="w", font=ctk.CTkFont(size=11), text_color="black")
                label_widget.grid(row=row_counter, column=0, padx=5, pady=5, sticky="w")
                self.result_labels[f"{key}_text"] = label_widget
                value_label = ctk.CTkLabel(results_frame, text="0.00 TL", anchor="e", font=ctk.CTkFont(size=12, weight="bold"), text_color="black")
                value_label.grid(row=row_counter, column=1, padx=5, pady=5, sticky="ew")
                self.result_labels[key] = value_label
            row_counter += 1
        
        ctk.CTkFrame(results_frame, height=2, corner_radius=0).grid(row=row_counter, column=0, columnspan=2, sticky='ew', pady=10)
        row_counter += 1
        
        add_to_sales_btn = ctk.CTkButton(results_frame, text=_("Bu Satışı Geçmişe Ekle"), command=self._add_sale_to_history, 
                                          font=ctk.CTkFont(size=14, weight="bold"))
        add_to_sales_btn.grid(row=row_counter, column=0, columnspan=2, sticky='ew', ipady=4)
        
        important_results = ["total_expenses_without_vat", "custom_sale_price", "net_profit", "pre_vat_price"]
        for key in important_results:
            self.result_labels[key].configure(font=ctk.CTkFont(size=14, weight="bold"))
            self.result_labels[f"{key}_text"].configure(font=ctk.CTkFont(size=12, weight="bold"))
        self.result_labels["net_profit"].configure(text_color="green")
        
        return page

    def _update_dynamic_commission_fields(self, event=None):
        mplace_name = self.calc_marketplace_combo.get()
        if mplace_name in self.marketplaces:
            data = self.marketplaces[mplace_name]
            self.dynamic_commission_entry.delete(0, tk.END)
            self.dynamic_commission_entry.insert(0, str(data.get("rate", 0.0)))
            self.mplace_vat_type_var.set(data.get('vat_type', _("Dahil")))
        else:
            self.dynamic_commission_entry.delete(0, tk.END)
            self.dynamic_commission_entry.insert(0, "0.0")

    def _toggle_shipping_widgets(self):
        is_enabled = self.apply_shipping_var.get()
        state = "readonly" if is_enabled else "disabled"
        self.calc_shipping_company_combo.configure(state=state)
        self.calc_shipping_desi_combo.configure(state=state)
        self.root.update_idletasks() # Arayüzün güncellenmesini zorla
        if is_enabled:
            self._update_shipping_desi_combobox()

    def _update_shipping_desi_combobox(self, event=None):
        """Kargo firması seçildiğinde desi/ağırlık combobox'ını günceller."""
        company = self.calc_shipping_company_combo.get()
        if company and company in self.shipping_prices:
            # Desi listesini al (sadece desi isimleri, fiyatlar değil)
            desi_list = [item[0] for item in self.shipping_prices[company]]
            self.calc_shipping_desi_combo.configure(values=desi_list)
            # Eğer listede eleman varsa ilkini seç, yoksa boşalt
            if desi_list:
                self.calc_shipping_desi_combo.set(desi_list[0])
            else:
                self.calc_shipping_desi_combo.set("")
        else:
            # Firma seçilmemişse veya listede yoksa desi listesini boşalt
            self.calc_shipping_desi_combo.configure(values=[])
            self.calc_shipping_desi_combo.set("")

    def _create_sales_history_tab(self, parent: ctk.CTkFrame):
        page = self._create_tab_frame(parent)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(2, weight=1) # History frame row

        summary_container = ctk.CTkFrame(page, fg_color="white")
        summary_container.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        summary_container.columnconfigure(0, weight=1)
        summary_container.columnconfigure(1, weight=1)

        totals_frame = ctk.CTkFrame(summary_container, corner_radius=10, fg_color="white")
        totals_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        totals_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(totals_frame, text=_("Genel Toplamlar"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        self.summary_labels = {}
        summary_fields = {
            "total_sales": _("Toplam Satış:"), "total_cost": _("Toplam Maliyet:"),
            "total_profit": _("Toplam Net Kar:"), "sales_count": _("Toplam Satış Adedi:")
        }
        for i, (key, text) in enumerate(summary_fields.items()):
            ctk.CTkLabel(totals_frame, text=text, text_color="black").grid(row=i + 1, column=0, sticky="w", padx=10, pady=2)
            lbl = ctk.CTkLabel(totals_frame, text="-", font=ctk.CTkFont(weight="bold"), text_color="black")
            lbl.grid(row=i + 1, column=1, sticky="e", padx=10, pady=2)
            self.summary_labels[key] = lbl

        filament_frame = ctk.CTkFrame(summary_container, corner_radius=10, fg_color="white")
        filament_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ctk.CTkLabel(filament_frame, text=_("Harcanan Filament"), font=ctk.CTkFont(weight="bold"), text_color="black").pack(padx=10, pady=(10, 5), anchor="w")
        
        self.filament_summary_labels_frame = ctk.CTkFrame(filament_frame, fg_color="transparent")
        self.filament_summary_labels_frame.pack(expand=True, fill="both", padx=10, pady=5)
        self.filament_summary_labels_frame.columnconfigure(1, weight=1)
        
        ctk.CTkButton(filament_frame, text=_("Gelişmiş Raporlama"), command=self._show_analytics_window).pack(pady=5, padx=10, fill='x')

        # --- FİLTRELEME WIDGET'LARI ---
        filter_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)

        ctk.CTkLabel(filter_frame, text=_("Ara (Ürün/Not):"), text_color="black").grid(row=0, column=0, padx=(10, 5), pady=10)
        self.sales_filter_entry = ctk.CTkEntry(filter_frame, placeholder_text=_("Aramak için yazın..."))
        self.sales_filter_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        self.sales_filter_entry.bind("<KeyRelease>", lambda e: self._refresh_sales_history_list())

        ctk.CTkLabel(filter_frame, text=_("Pazaryeri Filtresi:"), text_color="black").grid(row=0, column=2, padx=(10, 5), pady=10)
        self.sales_filter_mplace_combo = ctk.CTkComboBox(filter_frame, state="readonly", values=[_("Tümü")])
        self.sales_filter_mplace_combo.grid(row=0, column=3, sticky="ew", padx=(0, 10), pady=10)
        self.sales_filter_mplace_combo.set(_("Tümü"))
        self.sales_filter_mplace_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_sales_history_list())

        history_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        history_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # --- SÜTUN GÜNCELLEMESİ ---
        columns = ("tarih", "urun", "musteri_not", "satis_fiyati", "toplam_maliyet", "net_kar", "pazaryeri", "komisyon", "stopaj", "kargo", "filament", "elektrik")
        headings = (_("Tarih"), _("Ürün Adı"), _("Müşteri/Not"), _("Satış Fiyatı"), _("Toplam Maliyet"), _("Net Kar"), _("Pazaryeri"), _("Komisyon"), _("Stopaj"), _("Kargo"), _("Filament"), _("Elektrik"))
        self.sales_history_tree = self._create_treeview(history_frame, columns, headings)
        
        # Sütun genişlikleri ve hizalamaları
        self.sales_history_tree.column("tarih", width=120, anchor='w', stretch=tk.NO)
        self.sales_history_tree.column("urun", width=150, anchor='w')
        self.sales_history_tree.column("musteri_not", width=150, anchor='w')
        self.sales_history_tree.column("satis_fiyati", width=100, anchor='e', stretch=tk.NO)
        self.sales_history_tree.column("toplam_maliyet", width=100, anchor='e', stretch=tk.NO)
        self.sales_history_tree.column("net_kar", width=100, anchor='e', stretch=tk.NO)
        self.sales_history_tree.column("pazaryeri", width=100, anchor='center', stretch=tk.NO)
        self.sales_history_tree.column("komisyon", width=80, anchor='e', stretch=tk.NO)
        self.sales_history_tree.column("stopaj", width=80, anchor='e', stretch=tk.NO)
        self.sales_history_tree.column("kargo", width=80, anchor='e', stretch=tk.NO)
        self.sales_history_tree.column("filament", width=80, anchor='e', stretch=tk.NO)
        self.sales_history_tree.column("elektrik", width=80, anchor='e', stretch=tk.NO)
        # --- SÜTUN GÜNCELLEMESİ SONU ---

        btn_frame = ctk.CTkFrame(page, fg_color="white")
        btn_frame.grid(row=3, column=0, pady=10, padx=10, sticky="e")
        ctk.CTkButton(btn_frame, text=_("Seçili Satışı Sil"), command=self._delete_sale_from_history, fg_color="red").pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text=_("Tüm Geçmişi Temizle"), command=self._clear_sales_history, fg_color="darkred").pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text=_("Rapor Oluştur (PDF)"), command=self._create_report, fg_color="green").pack(side=tk.LEFT, padx=5)
        return page

    def _show_analytics_window(self):
        if not self.sales_history:
            messagebox.showinfo(_("Bilgi"), _("Analiz yapmak için yeterli satış verisi bulunmamaktadır."))
            return

        dialog = ctk.CTkToplevel(self.root)
        dialog.title(_("Gelişmiş Raporlama"))
        dialog.geometry("900x700")
        dialog.grab_set()

        tab_view = ctk.CTkTabview(dialog)
        tab_view.pack(expand=True, fill="both", padx=10, pady=10)
        tab_view.add(_("Aylık Performans"))
        tab_view.add(_("Filament Kullanımı"))

        # Aylık Performans Grafiği
        monthly_data = defaultdict(lambda: {"sales": 0, "cost": 0, "profit": 0})
        for sale in self.sales_history:
            try:
                sale_date = datetime.strptime(sale["date"], "%d-%m-%Y %H:%M")
                month_key = sale_date.strftime("%Y-%m")
                monthly_data[month_key]["sales"] += sale.get("sale_price", 0)
                monthly_data[month_key]["cost"] += sale.get("total_cost", 0)
                monthly_data[month_key]["profit"] += sale.get("net_profit", 0)
            except (ValueError, KeyError):
                continue
        
        sorted_months = sorted(monthly_data.keys())
        sales = [monthly_data[m]["sales"] for m in sorted_months]
        costs = [monthly_data[m]["cost"] for m in sorted_months]
        profits = [monthly_data[m]["profit"] for m in sorted_months]

        fig_monthly, ax_monthly = plt.subplots(figsize=(8, 6), facecolor='#f0f0f0')
        bar_width = 0.25
        index = range(len(sorted_months))
        
        ax_monthly.bar([i - bar_width for i in index], sales, bar_width, label=_('Ciro'))
        ax_monthly.bar(index, costs, bar_width, label=_('Maliyet'))
        ax_monthly.bar([i + bar_width for i in index], profits, bar_width, label=_('Net Kar'))
        
        ax_monthly.set_ylabel('TL')
        ax_monthly.set_title(_('Aylık Performans'))
        ax_monthly.set_xticks(index)
        ax_monthly.set_xticklabels(sorted_months, rotation=45, ha="right")
        ax_monthly.legend()
        fig_monthly.tight_layout()

        canvas_monthly = FigureCanvasTkAgg(fig_monthly, master=tab_view.tab(_("Aylık Performans")))
        canvas_monthly.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Filament Kullanım Grafiği
        filament_usage = defaultdict(float)
        for sale in self.sales_history:
            inputs = sale.get("inputs", {})
            f_type = inputs.get("filament_type", _("Bilinmiyor"))
            f_amount = inputs.get("filament_amount", 0)
            filament_usage[f_type] += f_amount
        
        fig_filament, ax_filament = plt.subplots(figsize=(8, 6), facecolor='#f0f0f0')
        labels = list(filament_usage.keys())
        sizes = list(filament_usage.values())
        ax_filament.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax_filament.axis('equal')
        ax_filament.set_title(_("Filament Kullanım Oranları (gram)"))

        canvas_filament = FigureCanvasTkAgg(fig_filament, master=tab_view.tab(_("Filament Kullanımı")))
        canvas_filament.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def _create_report(self):
        if not self.sales_history:
            messagebox.showinfo(_("Bilgi"), _("Rapor oluşturmak için satış geçmişi bulunmamaktadır."))
            return
        
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            messagebox.showerror(_("Eksik Modül"), _("PDF raporu oluşturmak için 'reportlab' kütüphanesi gereklidir.\nLütfen 'pip install reportlab' komutu ile kurun."))
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Dosyaları", "*.pdf"), ("Tüm Dosyalar", "*.*")],
            title=_("PDF Raporunu Kaydet"),
            initialfile=f"Satis_Raporu_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        if not filename:
            self.update_status(_("PDF rapor oluşturma iptal edildi."))
            return

        try:
            # Türkçe karakterleri destekleyen bir font bul veya kaydet
            font_path = None
            font_paths_to_check = [
                "C:/Windows/Fonts/arial.ttf", # Windows
                "/System/Library/Fonts/Supplemental/Arial.ttf", # macOS
                "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf", # Linux
                "/usr/share/fonts/corefonts/arial.ttf" # Linux
            ]
            for path in font_paths_to_check:
                if os.path.exists(path):
                    font_path = path
                    break
            
            if not font_path:
                 messagebox.showwarning(_("Font Uyarısı"), _("Arial fontu sistemde bulunamadı. PDF'teki Türkçe karakterler hatalı görünebilir."))
                 font_name = "Helvetica" # Fallback font
            else:
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                font_name = "Arial"

            styles = getSampleStyleSheet()
            styles['Normal'].fontName = font_name
            styles['Normal'].fontSize = 8
            styles['Heading1'].fontName = font_name
            styles['Heading1'].fontSize = 16
            
            doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
            
            data = [
                [_("Tarih"), _("Ürün"), _("Müşteri/Not"), _("Satış Fiyatı"), _("Toplam Maliyet"), _("Net Kar"), _("Pazaryeri"), _("Komisyon"), _("Stopaj"), _("Kargo"), _("Filament"), _("Elektrik")]
            ]
            
            for sale in self.sales_history:
                row = [
                    sale.get("date", "-"), sale.get("product_name", "-"), sale.get("note", "-"),
                    f'{sale.get("sale_price", 0):.2f} TL', f'{sale.get("total_cost", 0):.2f} TL',
                    f'{sale.get("net_profit", 0):.2f} TL', sale.get("marketplace", "-"),
                    f'{sale.get("commission", 0):.2f} TL', f'{sale.get("withholding_tax", 0):.2f} TL',
                    f'{sale.get("shipping_cost", 0):.2f} TL', f'{sale.get("filament_cost", 0):.2f} TL',
                    f'{sale.get("electricity_cost", 0):.2f} TL'
                ]
                data.append(row)
                
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a2d2e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), font_name), # Fontu uygula
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8e8e8')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ])
            
            table = Table(data, repeatRows=1)
            table.setStyle(table_style)
            
            story = [
                Paragraph(_("3D Baskı Maliyet ve Kar Raporu"), styles['Heading1']),
                Paragraph(f"{_('Rapor Tarihi')}: {datetime.now().strftime('%d-%m-%Y %H:%M')}", styles['Normal']),
                Spacer(1, 12),
                table
            ]
            
            doc.build(story)
            messagebox.showinfo(_("Başarılı"), f"{_('PDF raporu başarıyla oluşturuldu')}: {filename}")
        except Exception as e:
            messagebox.showerror(_("Hata"), f"{_('Rapor oluşturulurken bir hata oluştu')}: {e}")

    def _create_marketplace_tab(self, parent: ctk.CTkFrame):
        page = self._create_tab_frame(parent)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        vcmd_numeric = (self.root.register(self._validate_numeric_input), '%P')
        
        input_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        input_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(input_frame, text=_("Pazaryeri Ekle/Düzenle"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(input_frame, text=_("Pazaryeri Adı:"), text_color="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.mplace_name_entry = ctk.CTkEntry(input_frame)
        self.mplace_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text=_("Komisyon Oranı (%):"), text_color="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.mplace_rate_entry = ctk.CTkEntry(input_frame, validate='key', validatecommand=vcmd_numeric)
        self.mplace_rate_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text=_("Sabit Komisyon (TL):"), text_color="black").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.mplace_fixed_entry = ctk.CTkEntry(input_frame, validate='key', validatecommand=vcmd_numeric)
        self.mplace_fixed_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(input_frame, text=_("Komisyon KDV Tipi:"), text_color="black").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.mplace_vat_type_var_tab = ctk.StringVar(value=_("Dahil"))
        vat_type_combo = ctk.CTkComboBox(input_frame, variable=self.mplace_vat_type_var_tab, values=[_("Dahil"), _("Hariç")], state="readonly")
        vat_type_combo.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        
        btn_frame = ctk.CTkFrame(input_frame, fg_color="white")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        self.mplace_save_btn = ctk.CTkButton(btn_frame, text=_("Ekle"), command=self._save_or_update_marketplace)
        self.mplace_save_btn.pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text=_("Seçileni Sil"), command=self._delete_marketplace, fg_color="red").pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text=_("Temizle/Yeni"), command=self._clear_marketplace_fields, fg_color="gray").pack(side=tk.LEFT, padx=5)
        
        list_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        columns = ("Ad", "Oran", "Sabit", "KDV Tipi")
        headings = (_("Pazaryeri Adı"), _("Komisyon (%)"), _("Sabit Komisyon (TL)"), _("KDV Tipi"))
        self.mplace_tree = self._create_treeview(list_frame, columns, headings)
        self.mplace_tree.column("Oran", width=120, anchor="e", stretch=tk.NO)
        self.mplace_tree.column("Sabit", width=140, anchor="e", stretch=tk.NO)
        self.mplace_tree.column("KDV Tipi", width=100, anchor="center", stretch=tk.NO)
        self.mplace_tree.bind("<<TreeviewSelect>>", self._load_marketplace_for_edit)
        
        return page

    def _create_shipping_tab(self, parent: ctk.CTkFrame):
        page = self._create_tab_frame(parent)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        vcmd_numeric = (self.root.register(self._validate_numeric_input), '%P')
        
        input_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        input_frame.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(input_frame, text=_("Yeni Kargo Fiyatı Ekle/Sil"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        ctk.CTkLabel(input_frame, text=_("Kargo Firması:"), text_color="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.ship_company_combo = ctk.CTkComboBox(input_frame, values=[])
        self.ship_company_combo.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text=_("Desi/Ağırlık:"), text_color="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.ship_desi_entry = ctk.CTkEntry(input_frame)
        self.ship_desi_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text=_("Fiyat (TL) (KDV Dahil):"), text_color="black").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.ship_price_entry = ctk.CTkEntry(input_frame, validate='key', validatecommand=vcmd_numeric)
        self.ship_price_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        btn_frame = ctk.CTkFrame(input_frame, fg_color="white")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ctk.CTkButton(btn_frame, text=_("Ekle/Güncelle"), command=self._add_shipping_price).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text=_("Seçileni Sil"), command=self._delete_shipping_price, fg_color="red").pack(side=tk.LEFT, padx=5)
        
        list_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        columns = ("Firma", "Desi", "Fiyat")
        headings = (_("Kargo Firması"), _("Desi/Ağırlık"), _("Fiyat (TL)"))
        self.shipping_tree = self._create_treeview(list_frame, columns, headings)
        self.shipping_tree.column("Desi", width=120, anchor="center", stretch=tk.NO)
        self.shipping_tree.column("Fiyat", width=120, anchor="e", stretch=tk.NO)
        
        return page

    def _create_settings_tab(self, parent: ctk.CTkFrame):
        page = self._create_tab_frame(parent)
        page.columnconfigure(0, weight=1)
        vcmd_numeric = (self.root.register(self._validate_numeric_input), '%P')
        
        tax_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        tax_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        tax_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(tax_frame, text=_("Vergi Ayarları"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        ctk.CTkLabel(tax_frame, text=_("Genel KDV Oranı (%):"), text_color="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.general_vat_rate_entry = ctk.CTkEntry(tax_frame, validate='key', validatecommand=vcmd_numeric)
        self.general_vat_rate_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.general_vat_rate_entry.insert(0, str(self.settings.get("general_vat_rate", 20.0)))
        
        ctk.CTkLabel(tax_frame, text=_("Pazaryeri Stopaj Oranı (%):"), text_color="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.withholding_tax_rate_entry = ctk.CTkEntry(tax_frame, validate='key', validatecommand=vcmd_numeric)
        self.withholding_tax_rate_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.withholding_tax_rate_entry.insert(0, str(self.settings.get("withholding_tax_rate", 1.0)))

        elec_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        elec_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        elec_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(elec_frame, text=_("Elektrik Fiyatları (TL/kWh)"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        ctk.CTkLabel(elec_frame, text=_("Ticari Tarife:"), text_color="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.comm_elec_entry = ctk.CTkEntry(elec_frame, validate='key', validatecommand=vcmd_numeric)
        self.comm_elec_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.comm_elec_entry.insert(0, str(self.electricity_prices.get("ticari", 0.0)))

        ctk.CTkLabel(elec_frame, text=_("Mesken Tarife:"), text_color="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.res_elec_entry = ctk.CTkEntry(elec_frame, validate='key', validatecommand=vcmd_numeric)
        self.res_elec_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.res_elec_entry.insert(0, str(self.electricity_prices.get("mesken", 0.0)))

        costing_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        costing_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        costing_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(costing_frame, text=_("Genel Hesaplama Ayarları"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        ctk.CTkLabel(costing_frame, text=_("Varsayılan Cihaz Gücü (W):"), text_color="black").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.default_power_entry = ctk.CTkEntry(costing_frame, validate='key', validatecommand=vcmd_numeric)
        self.default_power_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.default_power_entry.insert(0, str(self.settings.get("default_device_power", 130.0)))

        ctk.CTkLabel(costing_frame, text=_("Varsayılan Elektrik Tarifesi:"), text_color="black").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.costing_elec_var = ctk.StringVar(value=self.settings.get("costing_electricity_type", "ticari"))
        rb_frame = ctk.CTkFrame(costing_frame, fg_color="white")
        rb_frame.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkRadioButton(rb_frame, text=_("Ticari"), variable=self.costing_elec_var, value="ticari", text_color="black").pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(rb_frame, text=_("Mesken"), variable=self.costing_elec_var, value="mesken", text_color="black").pack(side=tk.LEFT, padx=5)

        self.high_precision_var = ctk.BooleanVar(value=self.settings.get("high_precision", False))
        ctk.CTkCheckBox(costing_frame, text=_("Hassas Hesaplama Modu (Virgülden sonra 4 hane)"), variable=self.high_precision_var, text_color="black").grid(row=3, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        
        ctk.CTkButton(page, text=_("Ayarları Kaydet"), command=self._update_settings).grid(row=3, column=0, pady=20, padx=10, sticky="ew")
        
        # --- YENİ: VERİ YÖNETİMİ ---
        data_mgmt_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        data_mgmt_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        data_mgmt_frame.columnconfigure(0, weight=1)
        data_mgmt_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(data_mgmt_frame, text=_("Veri Yönetimi"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        ctk.CTkButton(data_mgmt_frame, text=_("Verileri Yedekle"), command=self._backup_data).grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(data_mgmt_frame, text=_("Yedekten Geri Yükle"), command=self._restore_data, fg_color="gray").grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        support_frame = ctk.CTkFrame(page, corner_radius=10, fg_color="white")
        support_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=5)
        support_frame.columnconfigure(0, weight=1)
        ctk.CTkLabel(support_frame, text=_("Destek & İletişim"), font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        discord_btn = ctk.CTkButton(support_frame, text=_("Geliştiriciye Discord'dan Ulaş"), command=self._open_discord_support)
        discord_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        return page

    def _update_settings(self):
        try:
            self.electricity_prices["ticari"] = float(self.comm_elec_entry.get())
            self.electricity_prices["mesken"] = float(self.res_elec_entry.get())
            self.settings["default_device_power"] = float(self.default_power_entry.get())
            self.settings["costing_electricity_type"] = self.costing_elec_var.get()
            self.settings["general_vat_rate"] = float(self.general_vat_rate_entry.get())
            self.settings["withholding_tax_rate"] = float(self.withholding_tax_rate_entry.get())
            self.settings["high_precision"] = self.high_precision_var.get()

            self._save_data()
            self.cost_entries["device_power"].delete(0, tk.END)
            self.cost_entries["device_power"].insert(0, str(self.settings["default_device_power"]))
            messagebox.showinfo(_("Başarılı"), _("Genel ayarlar güncellendi."))
            
        except (ValueError, TypeError):
            messagebox.showerror(_("Hata"), _("Geçersiz giriş! Lütfen tüm sayısal alanları doldurun."))

    def _open_discord_support(self):
        url = f"discord://-/users/{DISCORD_USER_ID}"
        try: webbrowser.open(url); self.update_status(_("Discord uygulaması açılıyor..."))
        except Exception as e: messagebox.showerror(_("Hata"), f"{_('Discord açılamadı. Yüklü olduğundan emin olun.')}\n\n{_('Hata')}: {e}")

    def _calculate_and_display(self):
        self.last_calculation_results = None
        self.last_calculation_inputs = None
        try:
            inputs = {key: float(entry.get() or 0) for key, entry in self.cost_entries.items()}
            inputs["other_costs"] = float(self.other_costs_entry.get() or 0)
            inputs["profit_margin"] = float(self.profit_margin_entry.get() or 0)
            inputs["filament_type"] = self.calc_filament_combo.get()
            inputs["shipping_company"] = self.calc_shipping_company_combo.get()
            inputs["shipping_desi"] = self.calc_shipping_desi_combo.get()
            inputs["marketplace"] = self.calc_marketplace_combo.get()
            inputs["commission_rate"] = float(self.dynamic_commission_entry.get() or 0)
            inputs["commission_vat_type"] = self.mplace_vat_type_var.get()
            
            inputs["apply_shipping"] = self.apply_shipping_var.get()
            inputs["apply_vat"] = self.apply_vat_var.get()
            inputs["apply_withholding"] = self.apply_withholding_var.get()

            if not all([inputs["filament_type"], inputs["marketplace"]]):
                messagebox.showwarning(_("Eksik Bilgi"), _("Filament türü ve pazaryeri seçilmelidir."))
                return
            
            filament_used_g = inputs.get("filament_amount", 0)
            if self.filament_inventory: # Envanter boş değilse kontrol et
                filament_in_stock = self.filament_inventory.get(inputs["filament_type"], 0)
                if filament_used_g > filament_in_stock:
                    if not messagebox.askyesno(_("Yetersiz Envanter"), _(f"Seçilen filamentin envanteri ({filament_in_stock:.2f}g) kullanılandan ({filament_used_g:.2f}g) daha az. Yine de hesaplamak istiyor musunuz?")):
                        return
                
        except (ValueError, TypeError):
            messagebox.showerror(_("Geçersiz Giriş"), _("Tüm sayısal alanlar doldurulmalıdır."))
            return
        
        try:
            results = self._perform_calculations(inputs)
            self.last_calculation_results = results
            self.last_calculation_inputs = inputs
        except Exception as e:
            messagebox.showerror(_("Hesaplama Hatası"), f"{_('Hesaplama sırasında bir hata oluştu')}: {e}")
            traceback.print_exc()
            return

        self._update_results_display(results, inputs)
        self.update_status(_("Hesaplama tamamlandı."))

    def _perform_calculations(self, inputs: Dict[str, Any]) -> Dict[str, float]:
        results = {}
        
        general_vat_rate = self.settings.get("general_vat_rate", 20.0) / 100.0
        withholding_tax_rate = self.settings.get("withholding_tax_rate", 1.0) / 100.0 if inputs["apply_withholding"] else 0.0
        profit_margin = inputs["profit_margin"] / 100.0
        
        f_price_kg = next((price for type_, price in self.filaments if type_ == inputs["filament_type"]), 0.0)
        results["filament_cost"] = (inputs["filament_amount"] / 1000.0) * f_price_kg
        
        elec_type = self.settings.get("costing_electricity_type", "ticari")
        elec_price = self.electricity_prices.get(elec_type, 0.0)
        kwh = (inputs["device_power"] * inputs["print_time"]) / 1000.0
        results["elec_cost"] = kwh * elec_price
        
        base_production_cost = results["filament_cost"] + results["elec_cost"] + inputs["other_costs"]
        
        shipping_cost = 0.0
        if inputs["apply_shipping"] and inputs["shipping_company"] and inputs["shipping_desi"]:
            shipping_cost = next((price for d, price in self.shipping_prices.get(inputs["shipping_company"], []) if d == inputs["shipping_desi"]), 0.0)
        
        mplace_info = self.marketplaces.get(inputs["marketplace"], {"rate": 0.0, "fixed": 0.0, "vat_type": _("Dahil")})
        stated_rate = inputs.get("commission_rate", 0.0) / 100.0
        vat_type = inputs.get("commission_vat_type", _("Dahil"))
        fixed_commission = mplace_info.get("fixed", 0.0)
        
        effective_commission_rate = stated_rate * (1 + general_vat_rate) if vat_type == _("Hariç") and inputs["apply_vat"] else stated_rate
        
        denominator = 1 - effective_commission_rate - withholding_tax_rate
        if inputs["apply_vat"]:
            denominator -= (general_vat_rate / (1 + general_vat_rate))

        profit_amount = base_production_cost * profit_margin

        if denominator <= 0:
            sale_price, commission, withholding_tax, vat_on_sale, net_profit = [float('inf')] * 5
            pre_vat_price, total_expenses_without_vat = float('inf'), float('inf')
        else:
            target_revenue = base_production_cost * (1 + profit_margin) + shipping_cost + fixed_commission
            sale_price = target_revenue / denominator
            
            commission = (sale_price * effective_commission_rate) + fixed_commission
            withholding_tax = sale_price * withholding_tax_rate
            vat_on_sale = sale_price * (general_vat_rate / (1 + general_vat_rate)) if inputs["apply_vat"] else 0.0
            
            pre_vat_price = sale_price - vat_on_sale
            total_expenses_without_vat = base_production_cost + shipping_cost + commission + withholding_tax
            net_profit = pre_vat_price - total_expenses_without_vat
        
        results.update({
            "total_base_cost": base_production_cost,
            "shipping_cost": shipping_cost,
            "custom_sale_price": sale_price, "commission": commission, "withholding_tax": withholding_tax,
            "vat_on_sale": vat_on_sale, "net_profit": net_profit,
            "profit_amount": profit_amount,
            "pre_vat_price": pre_vat_price,
            "total_expenses_without_vat": total_expenses_without_vat
        })
        return results

    def _update_results_display(self, results: Dict[str, float], inputs: Dict[str, Any]):
        precision = 4 if self.settings.get("high_precision", False) else 2
        format_str = f"{{:.{precision}f}} TL"

        # Update standard labels first
        self.result_labels["filament_cost"].configure(text=format_str.format(results.get('filament_cost', 0)))
        self.result_labels["elec_cost"].configure(text=format_str.format(results.get('elec_cost', 0)))
        shipping_text = format_str.format(results.get('shipping_cost', 0))
        if not inputs['apply_shipping']: shipping_text += f" ({_('Pasif')})"
        self.result_labels["shipping_cost"].configure(text=shipping_text)
        self.result_labels["other_costs"].configure(text=format_str.format(inputs.get('other_costs', 0)))
        
        # Update dynamic text labels
        self.result_labels["total_base_cost_text"].configure(text=_("Toplam Temel Maliyet:"))
        elec_type_tr = _("Ticari") if self.settings.get("costing_electricity_type", "ticari") == "ticari" else _("Mesken")
        self.result_labels["elec_cost_text"].configure(text=f"{_('Elektrik Maliyeti')} ({elec_type_tr}):")
        mplace_name = inputs.get('marketplace')
        self.result_labels["commission_text"].configure(text=f"{_('Komisyon')} ({mplace_name}):")
        w_tax_rate = self.settings.get("withholding_tax_rate", 1.0)
        w_tax_text = f"{_('Pazaryeri Stopajı')} (%{w_tax_rate:.1f})"
        if not inputs['apply_withholding']: w_tax_text += f" ({_('Pasif')})"
        self.result_labels["withholding_tax_text"].configure(text=w_tax_text)
        vat_text = f"{_('Eklenecek Satış KDV')}si (%{self.settings.get('general_vat_rate', 20.0):.1f})"
        if not inputs['apply_vat']: vat_text += f" ({_('Pasif')})"
        self.result_labels["vat_on_sale_text"].configure(text=vat_text)
        self.result_labels["custom_sale_price_text"].configure(text=f"{_('Nihai Satış Fiyatı')} (%{inputs.get('profit_margin', 100):.1f} {_('Kar ile')}):")
        
        # Update all main result values
        main_results = [
            "total_base_cost", "profit_amount", "pre_vat_price", "commission", 
            "withholding_tax", "vat_on_sale", "total_expenses_without_vat", 
            "custom_sale_price", "net_profit"
        ]
        for key in main_results:
            if key in self.result_labels:
                value = results.get(key, 0.0)
                text = _("Hesaplanamadı") if value == float('inf') else format_str.format(value)
                self.result_labels[key].configure(text=text)
        
        # ÖNEMLİ SONUÇLARI VURGULA
        important_results = ["total_expenses_without_vat", "custom_sale_price", "net_profit", "pre_vat_price"]
        for key in important_results:
            if key in self.result_labels:
                self.result_labels[key].configure(font=ctk.CTkFont(size=14, weight="bold"))
                self.result_labels[f"{key}_text"].configure(font=ctk.CTkFont(size=12, weight="bold"))
        self.result_labels["net_profit"].configure(text_color="green")

    def _recalculate_deductions_for_sale(self, sale_price, inputs):
        """Verilen bir satış fiyatına göre kesintileri yeniden hesaplar."""
        general_vat_rate = self.settings.get("general_vat_rate", 20.0) / 100.0
        withholding_tax_rate = self.settings.get("withholding_tax_rate", 1.0) / 100.0 if inputs["apply_withholding"] else 0.0
        
        mplace_info = self.marketplaces.get(inputs["marketplace"], {"rate": 0.0, "fixed": 0.0, "vat_type": _("Dahil")})
        stated_rate = inputs.get("commission_rate", 0.0) / 100.0
        vat_type = inputs.get("commission_vat_type", _("Dahil"))
        fixed_commission = mplace_info.get("fixed", 0.0)
        
        effective_commission_rate = stated_rate * (1 + general_vat_rate) if vat_type == _("Hariç") and inputs["apply_vat"] else stated_rate
        
        commission = (sale_price * effective_commission_rate) + fixed_commission
        withholding_tax = sale_price * withholding_tax_rate
        vat_on_sale = sale_price * (general_vat_rate / (1 + general_vat_rate)) if inputs["apply_vat"] else 0.0
        
        return {"commission": commission, "withholding_tax": withholding_tax, "vat_on_sale": vat_on_sale}

    def _add_sale_to_history(self):
        if not self.last_calculation_results or not self.last_calculation_inputs:
            messagebox.showwarning(_("Hesaplama Gerekli"), _("Lütfen önce bir maliyet hesaplaması yapın."))
            return

        initial_price_str = f"{self.last_calculation_results.get('custom_sale_price', 0.0):.2f}"
        dialog = CustomSaleDialog(self.root, 
                                  title=_("Satışı Kaydet"),
                                  initial_price=initial_price_str)
        
        dialog_result = dialog.result
        if not dialog_result:
            self.update_status(_("Satış ekleme işlemi iptal edildi."))
            return

        try:
            product_name = dialog_result["product_name"]
            user_sale_price = dialog_result["sale_price"]
            note = dialog_result["note"]

            # Kullanıcının girdiği fiyata göre kesintileri ve net karı yeniden hesapla
            recalculated_deductions = self._recalculate_deductions_for_sale(user_sale_price, self.last_calculation_inputs)
            
            base_cost = self.last_calculation_results.get("total_base_cost", 0)
            shipping_cost = self.last_calculation_results.get("shipping_cost", 0)
            
            commission = recalculated_deductions["commission"]
            withholding_tax = recalculated_deductions["withholding_tax"]
            vat_on_sale = recalculated_deductions["vat_on_sale"]
            
            total_cost = base_cost + shipping_cost + commission + withholding_tax + vat_on_sale
            net_profit = user_sale_price - total_cost

            sale_record = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "date": datetime.now().strftime("%d-%m-%Y %H:%M"),
                "product_name": product_name,
                "note": note,
                "sale_price": user_sale_price,
                "total_cost": total_cost,
                "net_profit": net_profit,
                "marketplace": self.last_calculation_inputs.get("marketplace", "-"),
                "commission": commission,
                "withholding_tax": withholding_tax,
                "shipping_cost": shipping_cost,
                "filament_cost": self.last_calculation_results.get("filament_cost", 0.0),
                "electricity_cost": self.last_calculation_results.get("elec_cost", 0.0),
                "inputs": self.last_calculation_inputs
            }
            
            f_type = self.last_calculation_inputs.get("filament_type")
            f_amount_used = self.last_calculation_inputs.get("filament_amount", 0)
            if f_type in self.filament_inventory:
                self.filament_inventory[f_type] -= f_amount_used
                if self.filament_inventory[f_type] < 0:
                    self.filament_inventory[f_type] = 0.0
            else:
                self.filament_inventory[f_type] = -f_amount_used if f_amount_used > 0 else 0.0

            self.sales_history.insert(0, sale_record)
            self._save_data()
            self._refresh_sales_history_list()
            self._update_sales_summary()
            self._refresh_filament_list()
            messagebox.showinfo(_("Başarılı"), _("Satış başarıyla geçmişe eklendi."))
            self.update_status(f"'{product_name}' {_('satışı kaydedildi.')}")
        except Exception as e:
            messagebox.showerror(_("Kayıt Hatası"), f"{_('Satış kaydedilirken bir hata oluştu')}:\n\n{e}")
            traceback.print_exc()

    def _refresh_sales_history_list(self, event=None):
        """Satış geçmişi listesini mevcut filtrelere göre günceller."""
        if not hasattr(self, 'sales_history_tree'): return
        
        search_term = self.sales_filter_entry.get().lower()
        mplace_filter = self.sales_filter_mplace_combo.get()

        self.sales_history_tree.delete(*self.sales_history_tree.get_children())
        
        filtered_sales = self.sales_history
        
        if mplace_filter != _("Tümü"):
            filtered_sales = [s for s in filtered_sales if s.get("marketplace") == mplace_filter]

        if search_term:
            filtered_sales = [s for s in filtered_sales if search_term in s.get("product_name", "").lower() or search_term in s.get("note", "").lower()]

        for sale in filtered_sales:
            # --- VERİ GÜNCELLEMESİ ---
            values = (
                sale.get("date", "-"),
                sale.get("product_name", "-"),
                sale.get("note", "-"),
                f'{sale.get("sale_price", 0):.2f} TL',
                f'{sale.get("total_cost", 0):.2f} TL',
                f'{sale.get("net_profit", 0):.2f} TL',
                sale.get("marketplace", "-"),
                f'{sale.get("commission", 0):.2f} TL',
                f'{sale.get("withholding_tax", 0):.2f} TL',
                f'{sale.get("shipping_cost", 0):.2f} TL',
                f'{sale.get("filament_cost", 0):.2f} TL',
                f'{sale.get("electricity_cost", 0):.2f} TL'
            )
            # --- VERİ GÜNCELLEMESİ SONU ---
            self.sales_history_tree.insert("", tk.END, iid=sale.get("id"), values=values)

    def _update_sales_summary(self):
        if not hasattr(self, 'summary_labels'): return
        
        # Filtreleme combobox'ını güncelle
        marketplaces = sorted(list(set(s.get("marketplace") for s in self.sales_history if s.get("marketplace"))))
        if hasattr(self, 'sales_filter_mplace_combo'):
            self.sales_filter_mplace_combo.configure(values=[_("Tümü")] + marketplaces)

        if not self.sales_history:
            self.summary_labels["total_sales"].configure(text="0.00 TL")
            self.summary_labels["total_cost"].configure(text="0.00 TL")
            self.summary_labels["total_profit"].configure(text="0.00 TL")
            self.summary_labels["sales_count"].configure(text="0")
            for widget in self.filament_summary_labels_frame.winfo_children(): widget.destroy()
            return
        
        total_sales = sum(s.get("sale_price", 0) for s in self.sales_history)
        total_cost = sum(s.get("total_cost", 0) for s in self.sales_history)
        total_profit = sum(s.get("net_profit", 0) for s in self.sales_history)
        sales_count = len(self.sales_history)
        
        self.summary_labels["total_sales"].configure(text=f"{total_sales:.2f} TL")
        self.summary_labels["total_cost"].configure(text=f"{total_cost:.2f} TL")
        self.summary_labels["total_profit"].configure(text=f"{total_profit:.2f} TL")
        self.summary_labels["sales_count"].configure(text=str(sales_count))

        filament_usage = defaultdict(float)
        for sale in self.sales_history:
            inputs = sale.get("inputs", {})
            f_type = inputs.get("filament_type", _("Bilinmiyor"))
            f_amount = inputs.get("filament_amount", 0)
            filament_usage[f_type] += f_amount
        
        for widget in self.filament_summary_labels_frame.winfo_children(): widget.destroy()
        self.filament_summary_labels_frame.columnconfigure(1, weight=1)
        for i, (f_type, amount) in enumerate(sorted(filament_usage.items())):
            ctk.CTkLabel(self.filament_summary_labels_frame, text=f"{f_type}:", text_color="black").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            ctk.CTkLabel(self.filament_summary_labels_frame, text=f"{amount:.2f} {_('gr')}", font=ctk.CTkFont(weight="bold"), text_color="black").grid(row=i, column=1, sticky="e", padx=5, pady=2)

    def _delete_sale_from_history(self):
        selected_items = self.sales_history_tree.selection()
        if not selected_items:
            messagebox.showwarning(_("Seçim Yapılmadı"), _("Lütfen silmek için bir satış kaydı seçin."))
            return
        if messagebox.askyesno(_("Onay"), f"{len(selected_items)} {_('adet satışı silmek istediğinizden emin misiniz?')}"):
            ids_to_delete = set(selected_items)
            self.sales_history = [sale for sale in self.sales_history if sale.get("id") not in ids_to_delete]
            self._save_data()
            self._refresh_sales_history_list()
            self._update_sales_summary()
            self.update_status(f"{len(ids_to_delete)} {_('satış kaydı silindi.')}")

    def _clear_sales_history(self):
        if not self.sales_history:
            messagebox.showinfo(_("Bilgi"), _("Satış geçmişi zaten boş."))
            return
        if messagebox.askyesno(_("Onay"), _("Tüm satış geçmişini kalıcı olarak silmek istediğinizden emin misiniz?\nBu işlem geri alınamaz!")):
            self.sales_history = []
            self._save_data()
            self._refresh_sales_history_list()
            self._update_sales_summary()
            self.update_status(_("Tüm satış geçmişi temizlendi."))

    def _backup_data(self):
        self._save_data() # En son verilerin kaydedildiğinden emin ol
        source_path = get_resource_path(DATA_FILE_NAME)
        
        backup_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Dosyaları", "*.json"), ("Tüm Dosyalar", "*.*")],
            title=_("Veri Yedeğini Kaydet"),
            initialfile=f"app_data_backup_{datetime.now().strftime('%Y%m%d')}.json"
        )

        if backup_path:
            try:
                shutil.copy(source_path, backup_path)
                messagebox.showinfo(_("Başarılı"), f"{_('Veriler başarıyla yedeklendi')}:\n{backup_path}")
                self.update_status(_("Veriler yedeklendi."))
            except Exception as e:
                messagebox.showerror(_("Yedekleme Hatası"), f"{_('Yedekleme sırasında bir hata oluştu')}: {e}")

    def _restore_data(self):
        if not messagebox.askyesno(_("Onay"), _("Mevcut verileriniz yedek dosyasındaki verilerle değiştirilecek. Bu işlem geri alınamaz. Devam etmek istiyor musunuz?")):
            return

        backup_path = filedialog.askopenfilename(
            filetypes=[("JSON Dosyaları", "*.json"), ("Tüm Dosyalar", "*.*")],
            title=_("Yedek Dosyasını Seç")
        )

        if backup_path:
            try:
                destination_path = get_resource_path(DATA_FILE_NAME)
                shutil.copy(backup_path, destination_path)
                
                # Verileri yeniden yükle ve arayüzü güncelle
                self._load_data()
                self._populate_all_widgets()

                messagebox.showinfo(_("Başarılı"), _("Veriler başarıyla geri yüklendi. Arayüz güncellendi."))
                self.update_status(_("Veriler yedekten geri yüklendi."))
            except Exception as e:
                messagebox.showerror(_("Geri Yükleme Hatası"), f"{_('Geri yükleme sırasında bir hata oluştu')}: {e}")

    # --- TAMAMLANMIŞ FONKSİYONLAR ---
    
    def _add_filament(self):
        f_type = self.filament_type_entry.get().strip()
        f_price_str = self.filament_price_entry.get().strip()
        if not f_type or not f_price_str:
            messagebox.showwarning(_("Eksik Bilgi"), _("Filament türü ve fiyatı boş bırakılamaz."))
            return
        try:
            f_price = float(f_price_str)
            
            # Var olanı güncelleme kontrolü
            existing_filament = next((f for f in self.filaments if f[0] == f_type), None)
            if existing_filament:
                if messagebox.askyesno(_("Onay"), f"'{f_type}' zaten mevcut. Fiyatı güncellemek istiyor musunuz?"):
                    self.filaments.remove(existing_filament)
                else:
                    return
            
            self.filaments.append((f_type, f_price))
            self.filaments.sort() # Alfabetik sıralama
            self._save_data()
            self._refresh_filament_list()
            self._update_filament_combobox()
            self.filament_type_entry.delete(0, tk.END)
            self.filament_price_entry.delete(0, tk.END)
            self.update_status(f"'{f_type}' filamenti eklendi/güncellendi.")
        except ValueError:
            messagebox.showerror(_("Hata"), _("Fiyat için geçerli sayısal bir değer girin."))

    def _delete_filament(self):
        selected_items = self.filament_tree.selection()
        if not selected_items:
            messagebox.showwarning(_("Seçim Yapılmadı"), _("Lütfen silmek için bir filament seçin."))
            return
        
        f_type = self.filament_tree.item(selected_items[0], "values")[0]
        if messagebox.askyesno(_("Onay"), f"'{f_type}' filamentini silmek istediğinizden emin misiniz?"):
            self.filaments = [f for f in self.filaments if f[0] != f_type]
            if f_type in self.filament_inventory:
                del self.filament_inventory[f_type]
            
            self._save_data()
            self._refresh_filament_list()
            self._update_filament_combobox()
            self.update_status(f"'{f_type}' filamenti silindi.")

    def _refresh_filament_list(self):
        if not hasattr(self, 'filament_tree'): return
        self.filament_tree.delete(*self.filament_tree.get_children())
        for f_type, f_price in sorted(self.filaments):
            inventory = self.filament_inventory.get(f_type, 0.0)
            self.filament_tree.insert("", tk.END, values=(f_type, f"{f_price:.2f}", f"{inventory:.2f}"))

    def _update_filament_combobox(self):
        if not hasattr(self, 'calc_filament_combo'): return
        filament_names = sorted([f[0] for f in self.filaments])
        self.calc_filament_combo.configure(values=filament_names)
        if filament_names:
            self.calc_filament_combo.set(filament_names[0])

    def _refresh_shipping_list(self):
        if not hasattr(self, 'shipping_tree'): return
        self.shipping_tree.delete(*self.shipping_tree.get_children())
        for company, prices in sorted(self.shipping_prices.items()):
            for desi, price in sorted(prices):
                self.shipping_tree.insert("", tk.END, values=(company, desi, f"{price:.2f}"))

    def _update_all_shipping_comboboxes(self):
        if not hasattr(self, 'ship_company_combo'): return
        companies = sorted(list(self.shipping_prices.keys()))
        self.ship_company_combo.configure(values=companies)
        self.calc_shipping_company_combo.configure(values=companies)
        if companies:
            self.ship_company_combo.set(companies[0])
            self.calc_shipping_company_combo.set(companies[0])
        self._update_shipping_desi_combobox()

    def _refresh_marketplace_list(self):
        if not hasattr(self, 'mplace_tree'): return
        self.mplace_tree.delete(*self.mplace_tree.get_children())
        # "Diğer/Yok" pazaryerini atla, çünkü o düzenlenemez
        for name, data in sorted(self.marketplaces.items()):
            if name == "Diğer/Yok": continue
            self.mplace_tree.insert("", tk.END, values=(name, data.get("rate", 0), data.get("fixed", 0), data.get("vat_type", "Dahil")))

    def _update_all_marketplace_comboboxes(self):
        if not hasattr(self, 'calc_marketplace_combo'): return
        mplace_names = sorted(list(self.marketplaces.keys()))
        self.calc_marketplace_combo.configure(values=mplace_names)
        if mplace_names:
            self.calc_marketplace_combo.set("Diğer/Yok")

    def _clear_marketplace_fields(self):
        if not hasattr(self, 'mplace_name_entry'): return
        self.mplace_name_entry.delete(0, tk.END)
        self.mplace_rate_entry.delete(0, tk.END)
        self.mplace_fixed_entry.delete(0, tk.END)
        self.mplace_vat_type_var_tab.set(_("Dahil"))
        self.mplace_name_entry.configure(state="normal")
        self.mplace_save_btn.configure(text=_("Ekle"))
        self.mplace_tree.selection_set() # Seçimi temizle
        self.selected_marketplace_name = None
        self.update_status(_("Yeni pazaryeri girişi için alanlar temizlendi."))

    def _save_or_update_marketplace(self):
        name = self.mplace_name_entry.get().strip()
        rate_str = self.mplace_rate_entry.get().strip() or "0"
        fixed_str = self.mplace_fixed_entry.get().strip() or "0"
        vat_type = self.mplace_vat_type_var_tab.get()

        if not name:
            messagebox.showwarning(_("Eksik Bilgi"), _("Pazaryeri adı boş bırakılamaz."))
            return
        if name == "Diğer/Yok":
            messagebox.showerror(_("Hata"), _("'Diğer/Yok' adı rezerve edilmiştir ve kullanılamaz."))
            return
            
        try:
            data = {"rate": float(rate_str), "fixed": float(fixed_str), "vat_type": vat_type}
            self.marketplaces[name] = data
            self._save_data()
            self._refresh_marketplace_list()
            self._update_all_marketplace_comboboxes()
            self._clear_marketplace_fields()
            self.update_status(f"'{name}' pazaryeri kaydedildi.")
        except ValueError:
            messagebox.showerror(_("Hata"), _("Komisyon oranları için geçerli sayısal değerler girin."))

    def _delete_marketplace(self):
        selected_items = self.mplace_tree.selection()
        if not selected_items:
            messagebox.showwarning(_("Seçim Yapılmadı"), _("Lütfen silmek için bir pazaryeri seçin."))
            return
        
        name = self.mplace_tree.item(selected_items[0], "values")[0]
        if name == "Diğer/Yok":
            messagebox.showerror(_("Hata"), _("'Diğer/Yok' pazaryeri silinemez."))
            return

        if messagebox.askyesno(_("Onay"), f"'{name}' pazaryerini silmek istediğinizden emin misiniz?"):
            del self.marketplaces[name]
            self._save_data()
            self._refresh_marketplace_list()
            self._update_all_marketplace_comboboxes()
            self._clear_marketplace_fields()
            self.update_status(f"'{name}' pazaryeri silindi.")

    def _load_marketplace_for_edit(self, event=None):
        selected_items = self.mplace_tree.selection()
        if not selected_items: return
        
        name = self.mplace_tree.item(selected_items[0], "values")[0]
        self.selected_marketplace_name = name
        data = self.marketplaces[name]
        
        self.mplace_name_entry.delete(0, tk.END)
        self.mplace_name_entry.insert(0, name)
        self.mplace_name_entry.configure(state="disabled") # Ad değiştirilemez
        
        self.mplace_rate_entry.delete(0, tk.END)
        self.mplace_rate_entry.insert(0, str(data.get("rate", 0.0)))
        
        self.mplace_fixed_entry.delete(0, tk.END)
        self.mplace_fixed_entry.insert(0, str(data.get("fixed", 0.0)))
        
        self.mplace_vat_type_var_tab.set(data.get("vat_type", _("Dahil")))
        self.mplace_save_btn.configure(text=_("Güncelle"))

    def _add_shipping_price(self):
        company = self.ship_company_combo.get().strip()
        desi = self.ship_desi_entry.get().strip()
        price_str = self.ship_price_entry.get().strip()
        
        if not all([company, desi, price_str]):
            messagebox.showwarning(_("Eksik Bilgi"), _("Tüm alanlar doldurulmalıdır."))
            return
        
        try:
            price = float(price_str)
            if company not in self.shipping_prices:
                self.shipping_prices[company] = []
            
            # Var olan desi'yi güncelle
            desi_exists = False
            for i, (d, p) in enumerate(self.shipping_prices[company]):
                if d == desi:
                    self.shipping_prices[company][i] = (desi, price)
                    desi_exists = True
                    break
            
            if not desi_exists:
                self.shipping_prices[company].append((desi, price))

            self._save_data()
            self._refresh_shipping_list()
            self._update_all_shipping_comboboxes()
            self.update_status(f"'{company}' için '{desi}' desi fiyatı eklendi/güncellendi.")
        except ValueError:
            messagebox.showerror(_("Hata"), _("Fiyat için geçerli bir sayı girin."))

    def _delete_shipping_price(self):
        selected_items = self.shipping_tree.selection()
        if not selected_items:
            messagebox.showwarning(_("Seçim Yapılmadı"), _("Lütfen silmek için bir kargo fiyatı seçin."))
            return
        
        company, desi, price_str = self.shipping_tree.item(selected_items[0], "values")
        
        if messagebox.askyesno(_("Onay"), f"'{company}' firmasından '{desi}' desi fiyatını silmek istiyor musunuz?"):
            self.shipping_prices[company] = [item for item in self.shipping_prices[company] if item[0] != desi]
            if not self.shipping_prices[company]: # Firma listesi boşaldıysa firmayı sil
                del self.shipping_prices[company]
            
            self._save_data()
            self._refresh_shipping_list()
            self._update_all_shipping_comboboxes()
            self.update_status(f"'{company}' - '{desi}' fiyatı silindi.")

def main():
    try:
        root = ctk.CTk()
        CostCalculatorApp(root)
        root.mainloop()
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror(f"{APP_NAME} - {_('Kritik Hata')}", f"{_('Uygulama başlatılamadı')}:\n\n{e}")

if __name__ == "__main__":
    main()
