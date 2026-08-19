# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for OrderbookAutomation (PRODUCTION, --onedir).
#
# Packages the EXISTING, already-tested application (main.py) into a
# standalone Windows executable. No business logic is defined or altered
# here -- this file only controls bundling.
#
# Build:   pyinstaller OrderbookAutomation.spec --noconfirm
# Wrapper: build_exe.bat
#
# DELIBERATELY NOT BUNDLED:
#   * client input Excel workbooks  -> stay external in input/
#   * generated output workbooks    -> written externally to output/
#   * tests/, build/, __pycache__/, .git/, venv/, dev scripts
# The application resolves input/, output/ and logs/ RELATIVE TO THE EXE
# at runtime (see modules.utils.get_application_base_dir), so those
# folders must remain external and writable.

from pathlib import Path

block_cipher = None

# No bundled data files: no icons, no templates, no sample workbooks.
# Daily inputs are always discovered dynamically at runtime from input/.
datas = []

# pandas/openpyxl import some submodules lazily/dynamically, which
# PyInstaller's static analyzer cannot always see. Safety-net hints.
hiddenimports = [
    "pandas._libs.tslibs.base",
    "pandas._libs.tslibs.timedeltas",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.window.aggregations",
    "openpyxl.cell._writer",
]

# Development-only packages must never be pulled into the client build.
excludes = [
    "pytest",
    "_pytest",
    "tests",
    "matplotlib",
    "notebook",
    "IPython",
    "tkinter",
]

a = Analysis(
    ["main.py"],
    pathex=[str(Path(SPECPATH))],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OrderbookAutomation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # business users run this from a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OrderbookAutomation",
)
