from pathlib import Path
import shutil
import subprocess


APP_NAME: str = "StartupAppLauncher"
ROOT: Path = Path(__file__).parent.resolve()
ICO_FILE: Path = ROOT / "logo.ico"
MAIN_FILE: Path = ROOT.parent / "main.py"
BIN: Path = ROOT / "bin"
TMP: Path = ROOT / "tmp"
TEMP_MAIN_FILE: Path = TMP / "main.py"


def main() -> None:
    print("[INFO] Checking PyInstaller...")
    if not pyinstaller_installed():
        print(f"\n[ERROR] PyInstaller not found!")
        print("Please install PyInstaller and try again")
        return
    
    print("[INFO] Preparing files...")
    if BIN.exists():
        shutil.rmtree(BIN)
    TMP.mkdir(parents=True, exist_ok=True)
    shutil.copy(MAIN_FILE, TEMP_MAIN_FILE)

    print("[INFO] Running PyInstaller...")
    command = [
        "pyinstaller", str(TEMP_MAIN_FILE),
        f'--distpath={str(BIN)}',
        f'--workpath={str(TMP)}',
        f'--specpath={str(TMP)}',
        f'--icon={str(ICO_FILE)}',
        "--onefile", "--noconsole",
        f'--name={APP_NAME}'
    ]
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"\n[ERROR] Error while running PyInstaller!")
        return
    
    print("[INFO] Removing temporary files...")
    if TMP.exists(): shutil.rmtree(TMP)


def pyinstaller_installed() -> bool:
    try:
        subprocess.run(["pyinstaller", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
    input("Press Enter to exit...")