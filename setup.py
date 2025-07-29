import sys
from cx_Freeze import setup, Executable

# Uygulamanızın bir arayüzü olduğunu ve arkada siyah konsol ekranı çıkmamasını sağlar
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="MaliyetHesaplayici",
    version="3.0",
    description="3D Baskı Maliyet & Kar Hesaplayıcı Pro",
    executables=[Executable("MaliyetV3.py", base=base, target_name="Maliyet Hesaplayıcı.exe")]
)
