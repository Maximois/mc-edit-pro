# MC Editor de Audio Pro v2.4.1

Editor de audio profesional con separación de stems mediante IA (UVR5 MDX-Net, Demucs v4).

## Estructura del proyecto

```
mc-audio-pro/
├── index.html          ← Aplicación principal (abrir este archivo)
├── css/
│   └── style.css       ← Estilos de la interfaz
├── js/
│   └── app.js          ← Lógica de la aplicación
└── README.md
```

## Cómo usar

1. Abre `index.html` en tu navegador (Chrome, Edge o Firefox recomendado).
2. Arrastra un archivo de audio al área central, o haz clic en **Explorar Archivo**.
3. Selecciona el modelo de IA en el panel izquierdo:
   - **MDX-Net** (UVR5) — separación espectral de alta precisión
   - **Demucs v4** (htdemucs_ft) — 4 stems en dominio de tiempo
   - **UVR-MDX-NET** — limpieza vocal + eliminación de reverb
   - **Demucs 6-Stem** — separación completa (guitar, piano, etc.)
4. Ajusta los parámetros (Segment Size, Overlap, Batch Size, formato de salida).
5. Presiona **▶ PROCESAR** y observa el progreso en el log.
6. Exporta los stems desde el panel derecho.

## Atajos de teclado

| Tecla              | Acción               |
|--------------------|----------------------|
| `Espacio`          | Play / Pausa         |
| `Home`             | Ir al inicio         |
| `End`              | Ir al final          |
| `← →`             | Retroceder/Avanzar 5s|
| `Ctrl+Z`           | Deshacer             |
| `Ctrl+O`           | Abrir archivo        |
| `Ctrl+S`           | Guardar proyecto     |
| `Escape`           | Cerrar modal         |

## Formatos compatibles

**Entrada:** MP3, WAV, FLAC, AIFF, OGG, M4A, AAC  
**Salida:** WAV 32-bit Float, WAV 16-bit, FLAC, MP3 320kbps, AAC 256kbps

## Modelos de IA

Esta interfaz está diseñada para integrarse con los backends reales de:
- **UVR5** (Ultimate Vocal Remover) — https://github.com/Anjok07/ultimatevocalremovergui
- **Demucs** — https://github.com/facebookresearch/demucs
- **MDX-Net** — integrado en UVR5

Para conectar con el backend real, modifica la función `startProcess()` en `js/app.js`
para que realice llamadas HTTP a tu servidor Python/FastAPI con los modelos instalados.

## Requisitos técnicos (backend real)

```
Python >= 3.8
PyTorch >= 2.0 (con CUDA para GPU)
pip install demucs onnxruntime-gpu librosa soundfile
```

---
MC Editor de Audio Pro © 2024
