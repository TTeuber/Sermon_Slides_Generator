# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the directory containing this spec file
spec_root = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(spec_root)],
    binaries=[],
    datas=[
        # Include HTML template
        ('templates/index.html', 'templates'),
        # Include font files
        ('JosefinSans-Medium.ttf', '.'),
        # Include static assets
        ('static/qr_code.png', 'static'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.cocoa',  # macOS platform
        'webview.js',
        'sermon_slides_generator',
        'PIL._tkinter_finder',  # PIL requirement
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary GUI frameworks to reduce size
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        # Exclude unused libraries
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'notebook',
        # Exclude testing frameworks
        'pytest',
        'unittest',
        'test',
        # Exclude development tools
        'black',
        'flake8',
        'mypy',
        'pylint',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SermonSlidesGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SermonSlidesGenerator',
)

# For macOS, create an app bundle
if os.name == 'posix' and os.uname().sysname == 'Darwin':
    app = BUNDLE(
        coll,
        name='Sermon Slides Generator.app',
        icon=None,  # Add icon file here if you have one
        bundle_identifier='com.csbtext.sermonslides',
        version='1.0.0',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Text files',
                    'CFBundleTypeRole': 'Viewer',
                    'LSItemContentTypes': ['public.plain-text'],
                    'LSHandlerRank': 'Alternate'
                }
            ]
        }
    )