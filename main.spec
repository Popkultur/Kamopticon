# -*- mode: python -*-

block_cipher = None


added_files = [ ( 'db/*.*', 'db' ),
         ( 'templates/*.*', 'templates' ),
         ( 'RECORD', 'RECORD' ),
         ( 'uploads', 'uploads' )
        ]
		
a = Analysis(['main.py'],
             pathex=['C:\Kamopticon'],
             binaries=[],
             datas=added_files,
             hiddenimports=['engineio.async_eventlet'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries + [('msvcp120.dll', 'C:\\Windows\\System32\\msvcp120.dll', 'BINARY'),
                        ('msvcr120.dll', 'C:\\Windows\\System32\\msvcr120.dll', 'BINARY')],
          a.zipfiles,
          a.datas,
		  Tree('static/', 'static'),
          name='main',
          debug=False,
          strip=False,
          upx=True,
          console=True )

