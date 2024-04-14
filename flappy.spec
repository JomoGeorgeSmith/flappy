# pyinstaller_spec.spec

# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = collect_submodules('pathlib')

a = Analysis(['flappy.py'],  
             pathex=['/Users/jomosmith/Desktop/Distributed Operating Systems/project/flappy/flappy/Game Container'], 
             binaries=[],
             datas=[('imgs', 'imgs'), ('neat_config.txt', '.')],  
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='jefferey',  
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='jefferey')  
