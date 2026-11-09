# ⚡ SETUP: MC Editor Pro con Live Server

## ✅ Lista de Instalación

### 1. Extensión Live Server en VS Code

```
1. Abre VS Code
2. Ve a Extensiones (Ctrl+Shift+X)
3. Busca: "Live Server"
4. Instala de Ritwickdey (la más popular)
5. Reinicia VS Code
```

**Verificar instalación:**
- En VS Code, botón derecho en un archivo HTML
- Debe aparecer opción: "Open with Live Server"

---

### 2. Backend Flask (Configuración CORS)

Edita `ui/app_premium_desktop.py` y agrega:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # ← Agregar esta línea
```

Instala la dependencia:
```bash
cd .
.\.venv311\Scripts\python.exe -m pip install flask-cors
```

---

### 3. Archivo de Configuración (Opcional)

Crea `mc-editor-pro/.liveserverrc` (puerto personalizado):

```json
{
  "port": 5500,
  "host": "127.0.0.1",
  "root": "./",
  "file": "index.html",
  "wait": 1000,
  "mount": [["/components", "./node_modules"]]
}
```

---

## 🚀 Ejecución Rápida

### Opción 1: Live Server (Recomendado)
```bash
# Terminal 1: Backend
cd .
.\.venv311\Scripts\python.exe audio_editor_full.py

# Terminal 2: VS Code + Live Server
# Click derecho en index.html → "Open with Live Server"
```

### Opción 2: Python Built-in
```bash
# Terminal 1: Backend
cd .
.\.venv311\Scripts\python.exe audio_editor_full.py

# Terminal 2: Frontend
cd .\mc-editor-pro
python -m http.server 8000
# Abre: http://localhost:8000
```

### Opción 3: Node Live Server Global
```bash
# Instalar una sola vez
npm install -g live-server

# Después, en cualquier proyecto:
cd .\mc-editor-pro
live-server --port=3000
# Abre: http://localhost:3000
```

---

## 🔧 Configuración Avanzada

### Hot Reload en VS Code
Agrega a settings.json:
```json
"liveServer.settings.donotShowInfoMsg": true,
"liveServer.settings.ignoreFiles": [
    ".git/**",
    "**/*.scss",
    "**/*.sass"
]
```

### Puerto Personalizado
Por defecto: `5500`

Para cambiar (en Live Server settings):
```
Live Server Config:
- Port: 3000
- Root: ./mc-editor-pro
- Default file: index.html
```

---

## 🌊 Estructura de Carpetas (Recomendada)

```
repository-root\
├── audio_editor_full.py          (Backend Tkinter original)
├── audio_editor_web.py           (Backend Flask para web)
├── ui/
│   └── app_premium_desktop.py    (API endpoints)
└── mc-editor-pro/               (Frontend Web)
    ├── index.html
    ├── style.css
    ├── script.js
    ├── .liveserverrc             (config)
    └── assets/
```

---

## 📡 Testing de Conexión

### Verificar Backend corriendo:
```bash
curl http://localhost:5000/
# Debe retornar algo, no error 404
```

### Verificar Frontend corriendo:
```bash
curl http://localhost:5500/
# Debe retornar HTML
```

### Verificar CORS headers:
```bash
curl -H "Origin: http://localhost:5500" \
     -H "Access-Control-Request-Method: POST" \
     -v http://localhost:5000/api/separate-stems
```

---

## 🎯 Próximas Tareas

1. **Implementar API endpoints** en Flask:
   ```python
   @app.route('/api/separate-stems', methods=['POST'])
   def separate_stems():
       # Usar code de audio_editor_full.py
       pass
   ```

2. **Conectar exportación**:
   ```python
   @app.route('/api/export', methods=['POST'])
   def export_audio():
       # Multi-formato export
       pass
   ```

3. **WebSocket para progreso en tiempo real**:
   ```python
   from flask_socketio import SocketIO
   socketio = SocketIO(app, cors_allowed_origins="*")
   ```

---

## 📚 Recursos Útiles

- [Live Server Documentación](https://ritwickdey.github.io/vscode-live-server/)
- [Web Audio API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Flask CORS](https://flask-cors.readthedocs.io/)

---

## ⚠️ Notas Importantes

1. **Backend DEBE estar corriendo** antes de usar la web
2. **CORS habilitado** es obligatorio
3. **Navegador moderno** recomendado (Chrome 90+, Firefox 88+)
4. **La app es responsiva** pero optimizada para desktop
5. **No requiere instalación de dependencias Node.js** si usas Live Server de VS Code

---

## 🐛 Si algo no funciona

1. **Limpia caché**: `Ctrl + Shift + Del`
2. **Hard refresh**: `Ctrl + Shift + R`
3. **Cierra Live Server**: Click en "Go Live" para apagar
4. **Reinicia VS Code**
5. **Revisa consola**: `F12` → Pestaña Console

¡Listo! Tu interfaz web está lista. 🎵✨
