# MC Editor Pro

Proyecto de editor de audio para escritorio con una interfaz web local servida
por Flask. La etapa actual se enfoca en la integración de UVR5 para separar
voces e instrumentos. La meta es evolucionar hacia un editor multipista
avanzado, ampliando sus capacidades por etapas.

La referencia de producto es el nivel de herramientas y flujo de trabajo de
editores profesionales como Sony VEGAS; MC Editor Pro es un proyecto
independiente y no está afiliado a Sony. Consulta el [plan de evolución](./ROADMAP.md).

## Requisitos

- Windows 10/11
- Python 3.11 disponible mediante el lanzador `py`
- Conexión a Internet en el primer inicio para instalar las dependencias

## Inicio rápido

1. Clona el repositorio:

   ```powershell
   git clone https://github.com/Maximois/mc-edit-pro.git
   cd mc-edit-pro
   ```

2. Ejecuta `Iniciar.bat`. En el primer inicio, el lanzador crea `.venv311`
   e instala las dependencias de [`requirements.txt`](./requirements.txt).

También puedes preparar el entorno por separado con `instalar_todo.bat`.

## Interfaces disponibles

| Lanzador | Interfaz |
|---|---|
| `Iniciar.bat` | Interfaz web en ventana PyQt6 (predeterminada) |
| `Iniciar_Tkinter.bat` | `audio_editor_full.py` |
| `Iniciar_PyQt_Pro.bat` | `audio_editor_pro.py` |
| `Iniciar_PyQt_Desktop.bat` | `audio_editor_desktop.py` |
| `Iniciar_PyQt_Desktop_v2.bat` | `audio_editor_desktop_v2.py` |
| `Iniciar_Web_PyQt.bat` | Interfaz web en ventana PyQt6 |
| `Iniciar_WebView.bat` | Interfaz web en ventana pywebview |

Las interfaces WebView se muestran en una ventana de escritorio; no hace falta
abrir un navegador externo. Las interfaces que requieren la API inician el
backend local y lo cierran al salir. Si el puerto 5000 está ocupado por otro
servicio, el lanzador informa el problema y no lo cierra.

## Estado actual: separación de stems

El backend contempla modelos UVR/MDX-Net y Demucs. Los entornos Python de UVR
y los pesos de modelos no se distribuyen en este repositorio por su tamaño.
Para usar la separación, instala UVR y descarga los modelos compatibles en
`mc-editor-pro/musia/ultimatevocalremover_gui/`. La disponibilidad se informa
en el endpoint local `/api/health`.

## Archivos excluidos del repositorio

`.gitignore` evita subir entornos virtuales, cachés, audio de prueba, salidas
generadas y pesos de modelos. Se conservan el código fuente y los archivos de
configuración necesarios para instalar el proyecto.

El código de UVR incluido en `mc-editor-pro/musia/ultimatevocalremover_gui/`
conserva su licencia original. Este repositorio no agrega una licencia global;
define una antes de publicar si quieres otorgar permisos de uso sobre el resto
del proyecto.
