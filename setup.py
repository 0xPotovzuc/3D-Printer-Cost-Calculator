import sys
from cx_Freeze import setup, Executable
import customtkinter

# --- UYGULAMA BİLGİLERİ ---
# Bu değerleri projenin ana betiği (MaliyetV4Beta2.py) ile uyumlu tutun.
APP_NAME = "3D Baskı Maliyet & Kar Hesaplayıcı Pro"
APP_VERSION = "4.0"
SCRIPT_FILE = "MaliyetV4Beta2.py"
EXECUTABLE_NAME = "Maliyet Hesaplayıcı"

# --- cx_Freeze AYARLARI ---

# Derleme sırasında dahil edilecek veya hariç tutulacak paketleri belirtir.
# Otomatik olarak algılanamayan veya sorun çıkaran kütüphaneleri buraya ekleyin.
build_exe_options = {
    "packages": [
        "os",
        "tkinter",
        "customtkinter",  # Yeni arayüz kütüphanesi
        "matplotlib",     # Grafikler için
        "reportlab",      # PDF raporlama için
        "collections",
        "shutil"
    ],
    "excludes": [
        "unittest", # Test kütüphanelerini dahil etme
        "pydoc",
        "pydoc_data"
    ],
    # customtkinter'ın temaları ve veri dosyası gibi ek dosyaları dahil etmek için.
    # Bu bölüm, "No such file or directory" hatasını çözer.
    "include_files": [
        ("app_data.json", "app_data.json"), # (kaynak, hedef)
        (customtkinter.ThemeManager.theme_path, "lib/customtkinter")
    ]
}

# Windows'ta GUI uygulamaları için konsol penceresini gizler.
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Oluşturulacak çalıştırılabilir dosyanın özelliklerini tanımlar.
executable = Executable(
    script=SCRIPT_FILE,          # Ana Python betiğiniz
    base=base,                   # GUI uygulaması için konsolu gizler
    target_name=f"{EXECUTABLE_NAME}.exe", # Oluşturulacak .exe dosyasının adı
)

# cx_Freeze kurulumunu yapılandırır ve başlatır.
setup(
    name=APP_NAME,
    version=APP_VERSION,
    description="3D baskı maliyet, kar ve envanter yönetimi uygulaması.",
    options={"build_exe": build_exe_options},
    executables=[executable]
)

