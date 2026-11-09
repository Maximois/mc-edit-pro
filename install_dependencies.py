#!/usr/bin/env python
"""
Instalador de dependencias para MC Editor Pro
Detecta Python y pip, instala todo lo necesario
"""

import subprocess
import sys
import os

print("\n" + "="*70)
print("🔧 MC Editor Pro - Instalador de Dependencias")
print("="*70 + "\n")

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}\n")

# Dependencias principales
deps = [
    "PyQt6",
    "PyQt6-WebEngine",
    "pywebview",
    "librosa",
    "numpy",
    "scipy",
    "scikit-learn",
    "flask",
    "flask-cors",
    "requests",
    "soundfile",
    "pydub",
]

# En Windows, preferir sounddevice en lugar de pyaudio (más fácil compilación)
if sys.platform == "win32":
    print("🪟 Detectado Windows - usando sounddevice para audio\n")
    deps.append("sounddevice")
else:
    print("🐧 Sistema Unix - intentando pyaudio\n")
    deps.append("pyaudio")

print("Instalando dependencias:\n")

failed = []
for package in deps:
    print(f"📦 {package}...", end=" ", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", package],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓")
    else:
        print("✗")
        failed.append(package)
        if "--no-cache-dir" not in result.stderr:
            print(f"   Error: {result.stderr[:100]}")

print("\n" + "="*70)

if not failed:
    print("✅ TODAS LAS DEPENDENCIAS INSTALADAS")
    print("\nUsa el lanzador Iniciar_*.bat de la interfaz que quieras abrir.")
else:
    print(f"⚠️  Algunas dependencias fallaron: {', '.join(failed)}")
    print("\n🔧 Intentando workarounds...\n")
    
    # Reintentar con --no-cache-dir
    for package in failed:
        print(f"Reintentando {package} sin cache...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-q", package],
            capture_output=True
        )
        if result.returncode == 0:
            print("✓")
            failed.remove(package)
        else:
            print("✗")
    
    if failed:
        print(f"\n❌ Aún fallan: {', '.join(failed)}")
        print("\nIntenta manualmente:")
        for pkg in failed:
            print(f"  pip install {pkg}")
    else:
        print("\n✅ Todos los retry funcionaron!")

print("\n" + "="*70)
