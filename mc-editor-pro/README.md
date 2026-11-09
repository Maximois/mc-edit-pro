# 🎵 MC Editor de Audio Pro - Interfaz Web

## 🚀 Guía de Uso con Live Server

### Requerimientos:
1. **VS Code** con extensión **Live Server** instalada
2. **Python Backend** corriendo en `http://localhost:5000`
3. **Node.js** (opcional, para alternativas a Live Server)

---

## 📋 Pasos para Ejecutar

### 1️⃣ Iniciar el Backend Flask
```bash
cd .
.\.venv311\Scripts\activate
python audio_editor_full.py
```

El backend debe estar accesible en `http://localhost:5000`

### 2️⃣ Abrir Live Server (Opción A - VS Code)

1. Abre VS Code
2. Abre esta carpeta (`mc-editor-pro`)
3. Click derecho en `index.html` → **"Open with Live Server"**
4. Se abrirá automáticamente en `http://127.0.0.1:5500`

### 3️⃣ O usar Python HTTP Server (Opción B)
```bash
cd .\mc-editor-pro
python -m http.server 8000
```

Luego abre en navegador: `http://localhost:8000`

### 4️⃣ O instalar Live Server global (Opción C)
```bash
npm install -g live-server
cd .\mc-editor-pro
live-server
```

---

## 🎵 Funcionalidades

### Panel de Control (Izquierda)
- ✅ Cargar archivos de audio (MP3, WAV, FLAC, OGG)
- ✅ Controles de reproducción: Play, Pause, Stop
- ✅ Ajustes: Volumen, Pitch, Velocidad
- ✅ **Separación de Stems** (4 componentes)
- ✅ Estado en tiempo real

### Panel Principal (Centro)
- ✅ Visualización en tiempo real
- ✅ 4 modos de visualización:
  - 🌊 Waveform
  - 📊 Espectro
  - 📈 Mel Espectrograma
  - 🎯 Frecuencia
- ✅ Indicador de progreso

### Panel de Stems (Abajo)
- ✅ Tarjetas individuales para cada stem:
  - 🎤 Voz
  - 🥁 Bajos
  - 🎸 Batería
  - 🎺 Otros
- ✅ Controles por stem:
  - Volumen individual
  - Ver waveform
  - Reproducción en solo
  - Exportar

---

## 🔌 API Backend (Endpoints requeridos)

El backend Flask debe implementar estos endpoints:

```python
# Separación de stems
POST /api/separate-stems
- Input: archivo WAV en multipart/form-data
- Output: JSON con stems separados en base64

# Exportación
POST /api/export
- Input: audioBuffer + formato (mp3, wav, flac, etc)
- Output: archivo descargable
```

---

## 🎨 Personalización

### Colores (style.css)
```css
--bg-dark: #0a0a0f;
--accent-blue: #00aaff;
--accent-purple: #b400ff;
--accent-cyan: #00ffcc;
--accent-gold: #ffcc00;
```

### Tema RGB Musical
- 🔵 Cyan: Controles principales
- 🟣 Purple: Acentos y énfasis
- 🟢 Verde: Alternativas
- 🟡 Oro: Información en tiempo real

---

## 🐛 Troubleshooting

### "CORS Error"
Asegura que el backend esté respondiendo a peticiones desde:
```python
from flask_cors import CORS
CORS(app)  # En app_premium_desktop.py
```

### "AudioContext not allowed"
Algunos navegadores requieren interacción del usuario antes de reproducir audio. 
Solución: Click en Play → AudioContext se crea automáticamente

### "Live Server no actualiza cambios"
1. Hard refresh: `Ctrl + Shift + R`
2. Limpia caché del navegador
3. Cierra y reabre Live Server

---

## 📦 Estructura de Archivos
```
mc-editor-pro/
├── index.html          # Interfaz principal
├── style.css           # Estilos profesionales
├── script.js           # Lógica de audio
├── assets/
│   ├── logo_mc.svg     # Logo (futuro)
│   └── icons/          # Iconos (futuro)
└── README.md           # Este archivo
```

---

## 🎯 Próximos Pasos

1. ✅ Conectar API de separation_stems con backend
2. ✅ Implementar exportación multi-formato
3. ⏳ Agregar efectos en tiempo real (EQ, Compresión, etc)
4. ⏳ Historial de ediciones (undo/redo)
5. ⏳ Grabación de audio en vivo

---

## 📝 Notas

- La interfaz web es más rápida y responsive que Tkinter
- Compatible con todos los navegadores modernos
- Ciencias del asincronismo con AudioContext Web API
- Renders a 60fps en canvas

**¡Disfruta editando!** 🎵
