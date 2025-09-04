import sys
from cx_Freeze import setup, Executable

# --- UYGULAMA BİLGİLERİ ---
# Bu değerleri projenin ana betiği (MaliyetV4.py) ile uyumlu tutun.
APP_NAME = "3D Baskı Maliyet & Kar Hesaplayıcı Pro"
APP_VERSION = "4.0"
SCRIPT_FILE = "MaliyetV4.py"
EXECUTABLE_NAME = "Maliyet Hesaplayıcı"

# --- cx_Freeze AYARLARI ---

# Derleme sırasında dahil edilecek veya hariç tutulacak paketleri belirtir.
# Otomatik algılanamayan veya sorun çıkaran kütüphaneleri 'packages' listesine ekleyebilirsiniz.
build_exe_options = {
    "packages": [
        "os",
        "tkinter",
        "ttkbootstrap",
        "matplotlib.pyplot",
        "matplotlib.backends.backend_tkagg"
    ],
    "excludes": [
        "unittest", # Test kütüphanelerini dahil etme
        "pydoc",
        "pydoc_data"
    ],
    # Uygulamanızın yanında bulunması gereken ek dosyalar (örneğin ikonlar, resimler).
    # "include_files": ["icon.ico", "images/"]
}

# Windows'ta GUI uygulamaları için konsol penceresini gizler.
# Diğer işletim sistemleri için 'base' None olarak kalır.
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Oluşturulacak çalıştırılabilir dosyanın özelliklerini tanımlar.
executable = Executable(
    script=SCRIPT_FILE,          # Ana Python betiğiniz
    base=base,                   # GUI uygulaması için konsolu gizler
    target_name=f"{EXECUTABLE_NAME}.exe", # Oluşturulacak .exe dosyasının adı
    # icon="icon.ico"            # Opsiyonel: Uygulama ikonu eklemek için bu satırı aktifleştirin
)

# cx_Freeze kurulumunu yapılandırır ve başlatır.
setup(
    name=APP_NAME,
    version=APP_VERSION,
    description="3D baskı maliyet, kar ve envanter yönetimi uygulaması.",
    options={"build_exe": build_exe_options},
    executables=[executable]
)
