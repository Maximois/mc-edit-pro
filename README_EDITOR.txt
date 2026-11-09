MC EDITOR PRO - INTERFACES DE ESCRITORIO
========================================

Elige una interfaz por su nombre de lanzador:

Iniciar_Tkinter.bat          -> audio_editor_full.py
Iniciar_PyQt_Pro.bat         -> audio_editor_pro.py
Iniciar_PyQt_Desktop.bat     -> audio_editor_desktop.py
Iniciar_PyQt_Desktop_v2.bat  -> audio_editor_desktop_v2.py
Iniciar_Web_PyQt.bat         -> mc-editor-pro dentro de PyQt6 WebEngine
Iniciar_WebView.bat          -> mc-editor-pro dentro de pywebview

Todos usan Python 3.11 y el entorno local .venv311. Se comprueban las
dependencias antes de abrir la interfaz. No se abre un navegador externo.

El antiguo .venv apunta a Python 3.14 y se conserva sin usar. Las interfaces
que dependen de la API local inician Flask automáticamente.
