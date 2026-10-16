# -*- mode: python ; coding: utf-8 -*-
import sys
import platform
from PyInstaller.utils.hooks import collect_all, copy_metadata

# Determine platform-specific target binary name
if sys.platform.startswith("win"):
    target_name = "DocuMind-windows"
elif sys.platform == "darwin":
    target_name = "DocuMind-macos"
else:
    target_name = "DocuMind-linux"

datas = [('app.py', '.'), ('pages', 'pages'), ('src', 'src')]
binaries = []
hiddenimports = ['streamlit', 'piper', 'engineio.async_drivers.threading']

# Collect all Streamlit submodules, static web assets (HTML/JS/CSS), and metadata
st_datas, st_binaries, st_hiddenimports = collect_all('streamlit')
datas += st_datas
binaries += st_binaries
hiddenimports += st_hiddenimports

# Collect Piper TTS package data, binaries, and metadata
p_datas, p_binaries, p_hiddenimports = collect_all('piper')
datas += p_datas
binaries += p_binaries
hiddenimports += p_hiddenimports

# Collect package distribution metadata
datas += copy_metadata('streamlit')
datas += copy_metadata('piper-tts')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=target_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=target_name,
)
