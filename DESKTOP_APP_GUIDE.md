# Interfaces de escritorio

`Iniciar.bat` abre por defecto `mc-editor-pro/` en una ventana PyQt6 WebEngine.
Los demás lanzadores siguen disponibles:

- `Iniciar.bat` -> predeterminada: `mc-editor-pro/` embebida en PyQt6 WebEngine
- `Iniciar_Tkinter.bat` -> `audio_editor_full.py`
- `Iniciar_PyQt_Pro.bat` -> `audio_editor_pro.py`
- `Iniciar_PyQt_Desktop.bat` -> `audio_editor_desktop.py`
- `Iniciar_PyQt_Desktop_v2.bat` -> `audio_editor_desktop_v2.py`
- `Iniciar_Web_PyQt.bat` -> `mc-editor-pro/` embebida en PyQt6 WebEngine
- `Iniciar_WebView.bat` -> `mc-editor-pro/` embebida en pywebview

Cada ventana se ejecuta en escritorio; no hace falta iniciar un navegador
externo. Las interfaces web embebidas usan el backend Flask local.

## Python 3.11

Los lanzadores crean y usan `.venv311` con Python 3.11, comprueban las
dependencias e instalan `requirements.txt` si hace falta. Se conserva el
`.venv` viejo, que apunta a `C:\Python314` y no se utiliza.

## Separación de audio

En `mc-editor-pro` se puede elegir uno de estos modelos locales:

- UVR5 MDX-Net `Inst full 292`: genera `Vocals` e `Instrumental`.
- Demucs v4 `htdemucs`: genera `Vocals`, `Bass`, `Drums` y `Other`.
- Demucs v4 `htdemucs_6s`: genera `Vocals`, `Bass`, `Drums`, `Other`,
  `Guitar` y `Piano`.

Los tres modelos reproducen, exportan individualmente y permiten exportar todos
los resultados como ZIP. Las pistas y botones se muestran según los stems
generados por el modelo elegido. El botón `Config` abre el selector de carpeta
de exportación y guarda la elección entre ejecuciones.

El modelo Demucs de cuatro stems se descarga en la carpeta `models`; los
modelos de seis stems y MDX-Net ya estaban disponibles en el entorno local. En
este equipo Demucs se ejecuta en CPU; el progreso es indeterminado y no se
muestra un SDR ficticio.

La aplicación principal sigue usando Python 3.11. Para no mezclar dependencias,
el proceso de separación se ejecuta mediante el entorno local aislado `uvr_env`
de Python 3.10. El modelo UVR instalado está etiquetado como VIP; úsalo solo
con la autorización/licencia correspondiente. El guardado de proyectos
`.mcproj`, los otros modos de edición y las capturas de espectrograma siguen
pendientes; la interfaz ya no muestra confirmaciones simuladas para esas
acciones.
