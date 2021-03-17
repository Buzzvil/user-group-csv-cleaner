# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['text_cleaner_main.py'],
             pathex=['/Users/jeseo/Works/text_cleaner'],
             binaries=[],
             datas=[],
             hiddenimports=['cmath'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
          name='Text cleaner',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='icon.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Text cleaner')
app = BUNDLE(coll,
             name='Text cleaner.app',
             icon='icon.icns',
             bundle_identifier=None)
