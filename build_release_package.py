from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
ZIP_PATH = DIST / "gmail-sender-deployment.zip"

FILES = [
    "app.py",
    "requirements.txt",
    "README.md",
    "DEPLOYMENT.md",
    "settings.json",
    "config.json.example",
    "profiles.txt.example",
    "dolphin.json",
    "install.sh",
    "install.bat",
]

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for file_name in FILES:
        file_path = ROOT / file_name
        if file_path.exists():
            zf.write(file_path, arcname=file_name)

print(ZIP_PATH)
