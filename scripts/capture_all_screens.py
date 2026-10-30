import subprocess
import time
import os

ADB = r"D:\Installed Software\SDK\platform-tools\adb.exe"
SERIAL = "192.168.0.141:5555"
OUT_DIR = r"C:\Users\Parvej Hossain\.gemini\antigravity\brain\986fcd24-90a3-4d1e-a0ea-e9048f439cb9"

def run_adb(args):
    cmd = [ADB, "-s", SERIAL] + args
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')

# Scroll back to top first
print("Scrolling to top...")
for _ in range(12):
    run_adb(["shell", "input", "swipe", "960", "250", "960", "900", "150"])
    time.sleep(0.3)

time.sleep(1)

# Now capture screens sequentially
screens = []
for i in range(12):
    png_path = os.path.join(OUT_DIR, f"tv_page_{i}.png")
    xml_path = os.path.join(OUT_DIR, f"tv_page_{i}.xml")
    
    print(f"Capturing page {i}...")
    # screencap
    run_adb(["shell", "screencap", "-p", "/sdcard/tv_scr.png"])
    subprocess.run([ADB, "-s", SERIAL, "pull", "/sdcard/tv_scr.png", png_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # dump UI hierarchy
    run_adb(["shell", "uiautomator", "dump", "/sdcard/tv_ui.xml"])
    subprocess.run([ADB, "-s", SERIAL, "pull", "/sdcard/tv_ui.xml", xml_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # swipe up to scroll down
    run_adb(["shell", "input", "swipe", "960", "850", "960", "280", "300"])
    time.sleep(1.2)

print("Finished capturing all pages!")
