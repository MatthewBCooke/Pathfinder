# Building Pathfinder Executable

This guide explains how to create a standalone Pathfinder executable for distribution.

## Quick Start

```bash
# 1. Install build dependencies
pip install -r requirements-dev.txt

# 2. Build executable
pyinstaller pathfinder.spec

# 3. Find executable in dist/ folder
# Windows: dist/Pathfinder/Pathfinder.exe
# macOS: dist/Pathfinder.app
# Linux: dist/Pathfinder/Pathfinder
```

## Detailed Instructions

### 1. Prerequisites

Ensure you have:
- Python 3.8+
- All dependencies installed (`pip install -r requirements-dev.txt`)
- PyInstaller >= 6.0.0

### 2. Build for Your Platform

#### Windows (produces .exe)

```bash
# Standard build
pyinstaller pathfinder.spec

# Result: dist/Pathfinder/Pathfinder.exe
# Copy the entire dist/Pathfinder folder for distribution
```

**To create installer (.msi):**
```bash
pip install pyinstaller-hooks-contrib
pyinstaller pathfinder.spec --onefile  # Single file
# Then use NSIS or WiX to create installer
```

#### macOS (produces .app)

```bash
# Build app bundle
pyinstaller pathfinder.spec

# Result: dist/Pathfinder.app
# To create DMG for distribution:
hdiutil create -volname Pathfinder -srcfolder dist/ -ov -format UDZO Pathfinder.dmg

# Optional: Sign the app (requires Apple developer certificate)
codesign --deep --force --verify --verbose --sign "Apple Development" dist/Pathfinder.app
```

#### Linux (produces binary)

```bash
# Build executable
pyinstaller pathfinder.spec

# Result: dist/Pathfinder/Pathfinder
# Make executable if needed:
chmod +x dist/Pathfinder/Pathfinder

# To create .deb package:
# Use checkinstall or fpm to convert to .deb
fpm -s dir -t deb -n pathfinder -v 2.0.0 \
    -C dist/Pathfinder -p pathfinder-2.0.0.deb
```

### 3. Test the Executable

**Windows:**
```bash
cd dist/Pathfinder
Pathfinder.exe
```

**macOS:**
```bash
open dist/Pathfinder.app
# Or run directly:
dist/Pathfinder.app/Contents/MacOS/Pathfinder
```

**Linux:**
```bash
./dist/Pathfinder/Pathfinder
```

### 4. Distribution

#### Option A: Direct Distribution
- Copy entire `dist/Pathfinder/` folder
- Create zip: `Pathfinder-2.0.0-win64.zip`
- Users extract and run `.exe` or binary

#### Option B: Installer
- Windows: Create .msi with WiX or NSIS
- macOS: Create .dmg with drag-and-drop install
- Linux: Create .deb or .rpm package

#### Option C: GitHub Releases
```bash
# Tag and push release
git tag -a v2.0.0 -m "Pathfinder 2.0"
git push origin v2.0.0

# Upload artifacts from dist/ to GitHub Releases
# (Can automate with .github/workflows/build.yml)
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pathfinder'"

**Solution:** Ensure pathfinder package is in project root and included in `pathfinder.spec` datas section.

```python
datas=[
    ('pathfinder', 'pathfinder'),  # This line is critical
    ('gui', 'gui'),
],
```

### "No module named PyQt6" or matplotlib errors

**Solution:** These are listed in `hiddenimports` in the spec. If still failing:

```bash
# Rebuild with verbose output
pyinstaller pathfinder.spec -v
```

### Executable is very large (>500MB)

**Normal for PyQt6 + matplotlib + scientific packages.** To reduce:
- Use `--onedir` (default, easier to debug)
- Exclude unused packages from `hiddenimports`
- Use UPX compression (already enabled in spec)

### App crashes on startup

**Common causes:**
1. Missing data files — check `datas` section in spec
2. Import errors — run with verbose: `pyinstaller pathfinder.spec -v`
3. Platform-specific Qt issues — test on target platform

**Debug:** Run from command line to see error messages:
```bash
./dist/Pathfinder/Pathfinder  # Shows traceback if error occurs
```

## Custom Configuration

### Adding Application Icon

Place `icon.ico` in project root. The spec file automatically uses it if present.

```bash
# Convert PNG to ICO (Windows only):
pip install pillow
python -c "from PIL import Image; Image.open('logo.png').save('icon.ico')"
```

### Including Sample Data

Add to `datas` section in `pathfinder.spec`:
```python
datas=[
    ('pathfinder', 'pathfinder'),
    ('gui', 'gui'),
    ('sample_data/', 'sample_data'),  # Include test files
],
```

### Creating One-File Executable

Edit `pathfinder.spec` and change EXE section:
```python
exe = EXE(
    # ... other args ...
    onefile=True,  # Single file instead of directory
)
```

**Note:** One-file executables are slower to start (~5s vs ~0.5s) because they extract to temp directory on launch.

## Build Automation (GitHub Actions)

To automatically build on each release, create `.github/workflows/build.yml`:

```yaml
name: Build Executable

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Build
        run: pyinstaller pathfinder.spec
      - name: Upload artifacts
        uses: softprops/action-gh-release@v1
        with:
          files: dist/**/*
```

## Version Updates

When updating Pathfinder version:

1. Update `__version__` in `pathfinder_gui.py`
2. Rebuild: `pyinstaller pathfinder.spec`
3. Test: `dist/Pathfinder/Pathfinder`
4. Tag: `git tag -a v2.0.1 -m "Pathfinder 2.0.1"`
5. Create release with new binary

## Support

For PyInstaller issues:
- [PyInstaller Docs](https://pyinstaller.org/)
- [PyInstaller GitHub Issues](https://github.com/pyinstaller/pyinstaller)

For Pathfinder-specific issues:
- Check that all pathfinder modules are in `hiddenimports`
- Verify `datas` paths are correct
- Test by running from extracted directory first
