#!/usr/bin/env python
"""
Crear archivo de audio test
"""

import numpy as np
import soundfile as sf
from pathlib import Path

output_path = Path(__file__).resolve().parent / "test_audio.wav"

# Crear audio sintético simple
duration = 3  # segundos
sample_rate = 44100
t = np.linspace(0, duration, int(sample_rate * duration))

# Mix de tonos
frequency = 440  # La
audio = 0.3 * np.sin(2 * np.pi * frequency * t)
audio += 0.2 * np.sin(2 * np.pi * (frequency * 1.5) * t)

# Guardar
sf.write(str(output_path), audio, sample_rate)

print(f"✓ Audio de prueba creado: {output_path}")
print(f"  Duración: {duration}s @ {sample_rate}Hz")
