# NO añadir @app.route aquí: las rutas /app viven solo en audio_editor_web.py.

"""
MC Editor Pro — interfaz de escritorio embebida (sin abrir navegadores externos).

Motor principal: PyQt6 + QWebEngineView (Chromium dentro de la ventana de la app).
Opcional: pywebview si tiene pythonnet compatible (p. ej. Python < 3.14).

Requisito: pip install PyQt6-WebEngine
"""

import os
import socket
import sys
import threading
import time

BACKEND_PORT = 5000
BACKEND_URL = f'http://127.0.0.1:{BACKEND_PORT}/app'


def _port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        r = sock.connect_ex((host, port))
        sock.close()
        return r == 0
    except OSError:
        return False


def _run_flask():
    from audio_editor_web import app as flask_app

    flask_app.run(
        host='127.0.0.1',
        port=BACKEND_PORT,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


def _run_pyqt_desktop(url: str) -> int:
    """Ventana nativa con vista web embebida (no es un proceso de Edge/Chrome aparte)."""
    from PyQt6.QtCore import QObject, QSettings, QStandardPaths, QUrl, pyqtSlot
    from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    # Mejor renderizado HiDPI
    os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '1')

    app = QApplication(sys.argv)
    app.setApplicationName('MC Editor de Audio Pro')
    app.setOrganizationName('MC')

    win = QMainWindow()
    win.setWindowTitle('MC Editor de Audio Pro')
    win.resize(1600, 900)
    win.setMinimumSize(1024, 600)

    view = QWebEngineView()
    page = view.page()
    if page is None:
        raise RuntimeError('PyQt no pudo crear la página de la ventana de escritorio.')
    profile = page.profile()
    if profile is None:
        raise RuntimeError('PyQt no pudo crear el perfil de descargas de la ventana.')
    download_directory = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DownloadLocation
    )
    settings = QSettings()
    saved_directory = settings.value('download_directory', download_directory, type=str)
    if os.path.isdir(saved_directory):
        download_directory = saved_directory
    os.makedirs(download_directory, exist_ok=True)

    class DesktopBridge(QObject):
        @pyqtSlot(result='QString')
        def getDownloadDirectory(self):
            return download_directory_holder[0]

        @pyqtSlot(str, result='QString')
        def chooseDownloadDirectory(self, current_directory):
            selected_directory = QFileDialog.getExistingDirectory(
                win,
                'Elegir carpeta para guardar exportaciones',
                current_directory if os.path.isdir(current_directory) else download_directory,
                QFileDialog.Option.ShowDirsOnly,
            )
            if selected_directory:
                selected_directory = os.path.abspath(selected_directory)
                os.makedirs(selected_directory, exist_ok=True)
                settings.setValue('download_directory', selected_directory)
                settings.sync()
                download_directory_holder[0] = selected_directory
                return selected_directory
            return ''

    download_directory_holder = [download_directory]
    bridge = DesktopBridge()
    channel = QWebChannel(page)
    channel.registerObject('desktopBridge', bridge)
    page.setWebChannel(channel)

    def accept_download(download):
        filename = download.downloadFileName()
        download.setDownloadFileName(filename)
        download.setDownloadDirectory(download_directory_holder[0])
        download.accept()
        print(f'Descarga aceptada: {os.path.join(download_directory_holder[0], filename)}', flush=True)

    profile.downloadRequested.connect(accept_download)
    view.setUrl(QUrl(url))
    win.setCentralWidget(view)
    win.show()

    return app.exec()


def _try_pywebview(url: str) -> bool:
    """Opcional: solo si pythonnet / backend WinForms está disponible."""
    if sys.platform == 'win32':
        os.environ.setdefault('PYWEBVIEW_GUI', 'edgechromium')
    try:
        import webview
    except ImportError:
        return False
    try:
        w = webview.create_window(
            title='MC Editor de Audio Pro',
            url=url,
            width=1600,
            height=900,
            min_size=(1024, 600),
            background_color='#0a0a0f',
            resizable=True,
        )
        if w:
            w.events.closed += lambda: sys.exit(0)
        webview.start(debug=False, gui='edgechromium')
        return True
    except Exception:
        return False


class MCEditorDesktop:
    def __init__(self):
        self._backend_thread = None

    def start(self, backend_already_running: bool = False):
        if not backend_already_running:
            print('Iniciando backend Flask…')
            self._backend_thread = threading.Thread(target=_run_flask, daemon=True)
            self._backend_thread.start()
            for _ in range(60):
                if _port_open('127.0.0.1', BACKEND_PORT):
                    print(f'Backend listo: {BACKEND_URL}\n')
                    break
                time.sleep(0.25)
            else:
                print('Advertencia: puerto 5000 no respondió a tiempo.')

        # 1) Interfaz de escritorio PyQt6 (recomendada; funciona en Python 3.14)
        try:
            print('Abriendo interfaz de escritorio (PyQt6 WebEngine)…')
            code = _run_pyqt_desktop(BACKEND_URL)
            raise SystemExit(code)
        except ImportError as e:
            print(f'PyQt6 WebEngine no disponible: {e}')
            print('Instale: pip install PyQt6-WebEngine')
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as e:
            print(f'PyQt6 falló: {e}')

        # 2) pywebview (solo si el entorno lo soporta)
        print('Intentando pywebview…')
        if _try_pywebview(BACKEND_URL):
            return

        print(
            'No se pudo abrir la ventana de escritorio.\n'
            '  pip install PyQt6-WebEngine\n'
            '  (y en algunos sistemas: pip install pywebview pythonnet — Python 3.11–3.13)\n'
            f'API local: {BACKEND_URL}'
        )
        sys.exit(1)

    def run(self):
        self.start(backend_already_running=False)


def main():
    MCEditorDesktop().start(backend_already_running=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
