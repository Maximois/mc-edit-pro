#!/usr/bin/env python
"""
Verificar e instalar dependencias de audio
"""

import subprocess
import sys

print("\n" + "="*70)
print("🔧 MC Editor Pro - Verificación de Dependencias")
print("="*70 + "\n")

deps = {
    'PyQt6': 'PyQt6',
    'PyQt6.QtWebEngineWidgets': 'PyQt6-WebEngine',
    'webview': 'pywebview',
    'librosa': 'librosa',
    'numpy': 'numpy',
    'scipy': 'scipy',
    'sklearn': 'scikit-learn',
    'flask': 'flask',
    'flask_cors': 'flask-cors',
    'requests': 'requests',
    'soundfile': 'soundfile',
    'pydub': 'pydub',
    'sounddevice': 'sounddevice',
    'tkinter': 'tkinter (incluido con Python)',
}

missing = []

print("Verificando dependencias:\n")
for name, package in deps.items():
    try:
        __import__(name)
        print(f"✓ {package}")
    except ImportError:
        print(f"✗ {package}")
        missing.append(package)

if not missing:
    print(f"\n✅ Todas las dependencias están instaladas!")
    
    # Verificar pyaudio (especial)
    try:
        import pyaudio
        print("✓ pyaudio - OK")
    except:
        print("⚠️  pyaudio no detectado (reproducción puede no funcionar)")
        print("   Intenta: pip install pyaudio")
else:
    print(f"\n⚠️  Faltan dependencias: {', '.join(missing)}")
    print("\nInstalando...")
    
    for package in missing:
        print(f"\n📦 Instalando {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   ✓ {package} instalado")
        else:
            print(f"   ✗ Error instalando {package}")
            print(f"   {result.stderr}")

print("\n" + "="*70)
print("✓ Listo!")
print("="*70 + "\n")
