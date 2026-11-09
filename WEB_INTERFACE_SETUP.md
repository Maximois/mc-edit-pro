# Interfaz mc-editor-pro en ventana de escritorio

Hay dos lanzadores para la interfaz `mc-editor-pro/`:

- `Iniciar_Web_PyQt.bat` la abre en una ventana PyQt6 WebEngine.
- `Iniciar_WebView.bat` la abre en una ventana pywebview.

Ambas son aplicaciones de escritorio integradas; no requieren abrir Chrome,
Edge, Live Server ni VS Code. El lanzador inicia el backend Flask local
cuando hace falta.

Los lanzadores usan Python 3.11 y el entorno local `.venv311`.
