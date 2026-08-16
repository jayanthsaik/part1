# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for OrderbookAutomation.
#
# This packages the EXISTING application (main.py) into a standalone,
# directory-based ("--onedir") Windows executable. No business logic is
# defined or altered here -- this file only controls how the already-tested
# Python application is bundled for deployment on business users' machines
# that do not have Python installed.
#
# Build with:
#   pyinstaller OrderbookAutomation.spec
#
# or via the provided build_exe.bat wrapper.

import sys
from pathlib import Path

block_cipher = None

# The application has no bundled data files of its own (no icons, no
# templates, no sample Excel workbooks are shipped inside the EXE -- daily
# input Excel files always remain external in input/, discovered dynamically
# at runtime by modules.source_discovery).
datas = []

# pandas/openpyxl occasionally require explicit hidden-import hints under
# PyInstaller because some of their submodules are imported lazily/dynamically
# rather than via static `import` statements PyInstaller's analyzer can see.
# These are safety-net entries; the application itself does not import them
# directly.
hiddenimports = [
    "pandas._libs.tslibs.base",
    "pandas._libs.tslibs.timedeltas",
    "pandas._libs.tslibs.np_datetime",
    "pandas._libs.tslibs.nattype",
    "pandas._libs.window.aggregations",
    "openpyxl.cell._writer",
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
    excludes=[],
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
    upx=False,
    # Console retained for the first production build so business users and
    # support staff can see clear success/error messages directly in the
    # window while the application is still being validated in the field.
    # A --noconsole build can be considered later once the EXE is proven
    # stable (see project deployment notes).
    console=True,
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
    upx=False,
    upx_exclude=[],
    name="OrderbookAutomation",
)
