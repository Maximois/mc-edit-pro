"""
🎵 MC Editor Pro - Desktop Window (Ventana Nativa de Escritorio)
Con pywebview - NO abre navegador, es una ventana de aplicación nativa
"""

import threading
import time
import sys
import os
from pathlib import Path

# Importar Flask
try:
    from audio_editor_web import app
except ImportError as e:
    print("❌ Error al cargar backend: {}".format(e))
    sys.exit(1)

# Importar pywebview
try:
    import webview
except ImportError:
    print("❌ pywebview no está instalado")
    print("Instala: pip install pywebview")
    sys.exit(1)

BACKEND_PORT = 5000

class MCEditor:
    def __init__(self):
        self.backend_thread = None
        self.window = None
        
    def run_backend(self):
        """Ejecutar Flask backend en thread separado"""
        try:
            app.run(
                host='127.0.0.1',
                port=BACKEND_PORT,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            print("ERROR en backend: {}".format(e))

    def start(self):
        """Iniciar la aplicación"""
        print("")
        print("=" * 50)
        print("MC Editor de Audio Pro")
        print("=" * 50)
        
        # Lanzar backend en thread
        print("Iniciando servidor backend...")
        self.backend_thread = threading.Thread(target=self.run_backend, daemon=True)
        self.backend_thread.start()
        
        # Esperar a que Flask se inicie
        time.sleep(2)
        
        # URL
        url = 'http://127.0.0.1:{}/app'.format(BACKEND_PORT)
        
        print("Servidor iniciado")
        print("Abriendo ventana de aplicacion...")
        
        try:
            # Crear ventana nativa con pywebview
            self.window = webview.create_window(
                title='MC Editor de Audio Pro',
                url=url,
                width=1400,
                height=900,
                resizable=True,
                fullscreen=False
            )
            
            print("OK - Ventana abierta")
            print("=" * 50)
            
            # Mostrar ventana (bloqueante)
            webview.start()
            
        except Exception as e:
            print("ERROR: {}".format(e))
            sys.exit(1)

if __name__ == '__main__':
    try:
        editor = MCEditor()
        editor.start()
    except KeyboardInterrupt:
        print("\nAplicacion cerrada")
        sys.exit(0)
    except Exception as e:
        print("ERROR: {}".format(e))
        sys.exit(1)
