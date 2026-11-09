#!/usr/bin/env python
"""
Test completo: Upload → Analyze → Separate
"""

import requests
import json
import time
import os
from pathlib import Path
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent

# Crear archivo de audio de prueba si no existe
def ensure_test_audio():
    test_file = PROJECT_DIR / "test_audio.wav"
    if os.path.exists(test_file):
        return str(test_file)
    
    print("📝 Creando archivo de audio de prueba...\n")
    try:
        import soundfile as sf
        duration = 3
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.2 * np.sin(2 * np.pi * 660 * t)
        sf.write(str(test_file), audio, sample_rate)
        print(f"✓ Audio creado: {test_file}\n")
    except Exception as e:
        print(f"❌ Error creando audio: {e}\n")
        return None
    
    return str(test_file)

print("\n" + "="*70)
print("🔧 Test Completo - Upload → Analyze → Separate")
print("="*70 + "\n")

# Asegurar que tenemos audio de prueba
test_file = ensure_test_audio()
if not test_file:
    exit(1)

API = "http://127.0.0.1:5000/api"



# Test 1: Health check
print("1️⃣  Health Check")
try:
    r = requests.get(f"{API}/health", timeout=2)
    print(f"   ✓ Status: {r.status_code}")
    print(f"   ✓ Response: {r.json()}\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    exit(1)

# Test 2: Upload
print("2️⃣  Upload Audio")
try:
    with open(test_file, 'rb') as f:
        r = requests.post(f"{API}/upload-audio", files={'audio': f}, timeout=10)
    
    if r.status_code == 200:
        data = r.json()
        audio_id = data.get('audio_id')
        print(f"   ✓ Status: {r.status_code}")
        print(f"   ✓ Audio ID: {audio_id}")
        print(f"   ✓ Duration: {data.get('duration'):.1f}s")
        print(f"   ✓ Sample Rate: {data.get('sample_rate')} Hz\n")
    else:
        print(f"   ❌ Upload failed: {r.text}\n")
        audio_id = None
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    audio_id = None

# Test 3: Analyze
if audio_id:
    print("3️⃣  Analyze Audio")
    try:
        r = requests.post(f"{API}/analyze", json={'audio_id': audio_id}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            analysis = data.get('analysis', {})
            print(f"   ✓ Status: {r.status_code}")
            print(f"   ✓ BPM: {analysis.get('bpm'):.1f}")
            print(f"   ✓ Key: {analysis.get('key')}")
            print(f"   ✓ Instruments: {analysis.get('instruments')}\n")
        else:
            print(f"   ❌ Analyze failed: {r.text}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

# Test 4: Separate Stems
if audio_id:
    print("4️⃣  Separate Stems (ICA)")
    try:
        r = requests.post(f"{API}/separate-stems", json={'audio_id': audio_id}, timeout=120)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✓ Status: {r.status_code}")
            print(f"   ✓ Stems ID: {data.get('stems_id')}")
            print(f"   ✓ Sample Rate: {data.get('sample_rate')} Hz")
            print(f"   ✓ Stems: {list(data.get('stems', {}).keys())}\n")
        else:
            print(f"   ❌ Separation failed: {r.text}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

print("="*70)
print("✅ Test completado")
print("="*70 + "\n")
