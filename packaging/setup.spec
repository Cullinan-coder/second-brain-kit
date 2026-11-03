# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: Second Brain Setup (Windows: tek dosya .exe, macOS: .app). Derleme: python packaging/build.py
# Ortam (build.py verir):  SB_KIT_ROOT = içinde system/ ve vault/ olan kit klasörü (varsayılan: packaging'in üstü)
#                          SB_UV_BIN   = gömülecek uv ikilisi          SB_LAUNCHER_DIR = derlenmiş Second Brain.exe/.app klasörü
import os
import sys
from pathlib import Path

HERE = Path(SPECPATH)                                         # noqa: F821  (PyInstaller verir)
KIT = Path(os.environ.get("SB_KIT_ROOT") or HERE.parent).resolve()
SYSTEM = KIT / "system"
IS_MAC = sys.platform == "darwin"
NAME = "Second Brain Setup"
ICON = str(HERE / ("icon.icns" if IS_MAC else "icon.ico"))

datas = [
    (str(SYSTEM), "kit/system"),                              # kurulacak kod (engine.kit_dir() → _MEIPASS/kit)
    (str(KIT / "vault"), "kit/vault"),                        # şablon kasa
    (str(SYSTEM / "setup" / "ui"), "setup/ui"),               # sihirbaz arayüzü (server.UI = setup/ui)
]
uv = os.environ.get("SB_UV_BIN")
if uv and Path(uv).is_file():
    datas.append((uv, "uv"))
launcher = os.environ.get("SB_LAUNCHER_DIR")
if launcher and Path(launcher).exists():
    for item in Path(launcher).iterdir():
        if item.name.startswith("Second Brain") and "Setup" not in item.name:
            datas.append((str(item), "launcher" + ("/" + item.name if item.is_dir() else "")))

hiddenimports = [
    "setup", "setup.app", "setup.server", "setup.engine", "setup.accounts", "setup.autostart", "setup.imports", "setup.mcp",
    "webview", "yaml", "keyring", "keyring.backends", "send2trash", "imaplib", "ssl", "sqlite3",
]
hiddenimports += (["webview.platforms.cocoa"] if IS_MAC else ["webview.platforms.winforms", "webview.platforms.edgechromium", "clr"])

a = Analysis(                                                 # noqa: F821
    [str(HERE / "setup_entry.py")],
    pathex=[str(SYSTEM), str(HERE)],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "numpy", "PIL", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)                                             # noqa: F821
exe = EXE(                                                    # noqa: F821
    pyz, a.scripts, a.binaries, a.datas, [],
    name=NAME,
    console=False,                                            # pencereli: konsol açılmaz
    icon=ICON if Path(ICON).exists() else None,
    upx=False,
    runtime_tmpdir=None,
)
if IS_MAC:
    app = BUNDLE(                                             # noqa: F821
        exe,
        name=NAME + ".app",
        icon=ICON if Path(ICON).exists() else None,
        bundle_identifier="com.secondbrain.setup",
        info_plist={"CFBundleDisplayName": NAME, "NSHighResolutionCapable": True, "LSMinimumSystemVersion": "11.0"},
    )
