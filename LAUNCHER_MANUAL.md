# Lanzadores de interfaces

`Iniciar.bat` abre por defecto `mc-editor-pro/` dentro de una ventana PyQt6
WebEngine. Los demás lanzadores permanecen disponibles:

| Archivo | Implementación |
|---|---|
| `Iniciar.bat` | Predeterminada: `mc-editor-pro/` dentro de una ventana PyQt6 |
| `Iniciar_Tkinter.bat` | `audio_editor_full.py` |
| `Iniciar_PyQt_Pro.bat` | `audio_editor_pro.py` |
| `Iniciar_PyQt_Desktop.bat` | `audio_editor_desktop.py` |
| `Iniciar_PyQt_Desktop_v2.bat` | `audio_editor_desktop_v2.py` |
| `Iniciar_Web_PyQt.bat` | `mc-editor-pro/` dentro de una ventana PyQt6 |
| `Iniciar_WebView.bat` | `mc-editor-pro/` dentro de una ventana pywebview |

Haz doble clic en `Iniciar.bat` para abrir la interfaz predeterminada o en
cualquier otro lanzador para probar una alternativa. Las interfaces WebView
se muestran en ventanas integradas y no abren un navegador externo.

## Entorno Python

Todos los lanzadores usan Python 3.11. En el primer arranque crean
`.venv311`, comprueban los módulos y, si falta alguno, instalan
[`requirements.txt`](./requirements.txt). El `.venv` anterior apunta a
`C:\Python314`, que no existe; no se modifica ni se usa.

Las interfaces cliente de API inician el backend Flask cuando es necesario.
Si el puerto 5000 pertenece a otro servicio, el lanzador muestra un error y
no detiene ese proceso.
