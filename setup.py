import sys
from cx_Freeze import setup, Executable

# Uygulamanızın bir arayüzü olduğunu ve arkada siyah konsol ekranı çıkmamasını sağlar
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# MSI yükleyicisi için seçenekler
bdist_msi_options = {
    "add_to_path": False,
    "initial_target_dir": r"%ProgramFiles%\MaliyetHesaplayici",
    "all_users": True,
}

setup(
    # DEĞİŞTİRİLDİ: Türkçe karakter sorunlarını önlemek için isim basitleştirildi.
    name="MaliyetHesaplayici",
    version="3.0",
    description="3D Baskı Maliyet & Kar Hesaplayıcı Pro",
    options={"bdist_msi": bdist_msi_options},
    executables=[Executable("MaliyetV3.py", base=base, target_name="Maliyet Hesaplayıcı.exe")]
)
