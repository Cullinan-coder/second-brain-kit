# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: Second Brain (hafif başlatıcı; Windows: tek dosya .exe, macOS: .app). Derleme: python packaging/build.py
# Yalnız standart kütüphane: kurulu kasanın .venv Python'unda `-m app.desktop` açar (pywebview orada kurulu).
import sys
from pathlib import Path

HERE = Path(SPECPATH)                                         # noqa: F821  (PyInstaller verir)
IS_MAC = sys.platform == "darwin"
NAME = "Second Brain"
ICON = str(HERE / ("icon.icns" if IS_MAC else "icon.ico"))

a = Analysis(                                                 # noqa: F821
    [str(HERE / "app_entry.py")],
    pathex=[str(HERE)],
    datas=[],
    hiddenimports=["ctypes", "json", "subprocess"],
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "pytest", "yaml", "webview", "unittest", "email", "http", "xml", "pydoc"],
    noarchive=False,
)
pyz = PYZ(a.pure)                                             # noqa: F821
exe = EXE(                                                    # noqa: F821
    pyz, a.scripts, a.binaries, a.datas, [],
    name=NAME,
    console=False,
    icon=ICON if Path(ICON).exists() else None,
    upx=False,
    runtime_tmpdir=None,
)
if IS_MAC:
    app = BUNDLE(                                             # noqa: F821
        exe,
        name=NAME + ".app",
        icon=ICON if Path(ICON).exists() else None,
        bundle_identifier="com.secondbrain.app",
        info_plist={"CFBundleDisplayName": NAME, "NSHighResolutionCapable": True, "LSMinimumSystemVersion": "11.0"},
    )
