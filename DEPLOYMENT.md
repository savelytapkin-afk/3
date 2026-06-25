# Deployment Quick Start

## Package contents
- `app.py`
- `requirements.txt`
- `settings.json`
- `config.json.example`
- `profiles.txt.example`
- `install.sh` / `install.bat`

## Quick start
### Linux / macOS
```bash
chmod +x install.sh
./install.sh
source .venv/bin/activate
python app.py
```

### Windows
```bat
install.bat
.venv\Scripts\activate
python app.py
```

## Dependencies
All runtime dependencies are listed in `requirements.txt`.

## Automated release package
GitHub Actions workflow `.github/workflows/release-package.yml` validates the project and builds `gmail-sender-deployment.zip` on every push/PR and release.
On release events, the zip is attached to the GitHub Release assets automatically.
