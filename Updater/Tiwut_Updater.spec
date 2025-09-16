# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# --- Direct method to find and bundle Tcl/Tk data files ---
# This is more robust than using PyInstaller hooks. It locates the tcl/tk
# directories within the current Python environment and bundles them.

# Construct the path to the tcl and tk folders from the base Python directory
tcl_dir = os.path.join(sys.prefix, 'tcl', 'tcl8.6')
tk_dir = os.path.join(sys.prefix, 'tcl', 'tk8.6')

# The 'datas' format is a list of tuples: (source_path, destination_folder_in_bundle)
# This will copy the contents of tcl_dir into a 'tcl' folder in the bundle,
# and the contents of tk_dir into a 'tk' folder.
bundled_datas = [
    (tcl_dir, 'tcl'),
    (tk_dir, 'tk')
]
# ---

a = Analysis(
    ['Tiwut_Updater.py'],
    pathex=[],
    binaries=[],
    datas=bundled_datas,  # Use our custom-found data files
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Tiwut_Updater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,         # This creates a windowed application (.exe)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)