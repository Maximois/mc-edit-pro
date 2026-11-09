#!/usr/bin/env python
"""Launch one named desktop interface using the project's Python 3.11 env."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
ENV_DIR = ROOT / ".venv311"
VENV_PYTHON = ENV_DIR / "Scripts" / "python.exe"
REQUIREMENTS = ROOT / "requirements.txt"
HEALTH_URL = "http://127.0.0.1:5000/api/health"
DEFAULT_INTERFACE = "app_desktop_window"
DEPENDENCY_CHECK = (
    "import flask, flask_cors, librosa, numpy, matplotlib, pandas, soundfile, "
    "scipy, sklearn, pydub, sounddevice, webview, tkinter, requests; "
    "from PyQt6.QtWebEngineWidgets import QWebEngineView"
)

INTERFACES = {
    "app_desktop_window": ("app_desktop_window.py", False),
    "app_desktop_lite": ("app_desktop_lite.py", False),
    "audio_editor_pro": ("audio_editor_pro.py", True),
    "audio_editor_desktop": ("audio_editor_desktop.py", False),
    "audio_editor_desktop_v2": ("audio_editor_desktop_v2.py", True),
    "audio_editor_full": ("audio_editor_full.py", False),
}


def _run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=capture,
        check=False,
    )


def _prepare_environment() -> None:
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(
            f"Este lanzador requiere Python 3.11; se inició con {sys.version.split()[0]}."
        )

    if not VENV_PYTHON.exists():
        print("Creando entorno local .venv311 con Python 3.11...")
        result = _run(
            [sys.executable, "-m", "venv", "--system-site-packages", str(ENV_DIR)]
        )
        if result.returncode:
            raise RuntimeError("No se pudo crear el entorno virtual .venv311.")

    check = _run([str(VENV_PYTHON), "-c", DEPENDENCY_CHECK], capture=True)
    if check.returncode:
        print("Instalando las dependencias de requirements.txt...")
        install = _run(
            [str(VENV_PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS)]
        )
        if install.returncode:
            raise RuntimeError("Falló la instalación de requirements.txt.")
        check = _run([str(VENV_PYTHON), "-c", DEPENDENCY_CHECK], capture=True)
        if check.returncode:
            raise RuntimeError(
                "Las dependencias siguen incompletas:\n"
                + (check.stderr or check.stdout).strip()
            )


def _backend_is_healthy() -> bool:
    try:
        with urlopen(HEALTH_URL, timeout=1) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status == 200 and payload.get("status") == "ok"
    except (OSError, URLError, ValueError):
        return False


def _port_is_open() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 5000), timeout=0.3):
            return True
    except OSError:
        return False


def _start_backend() -> subprocess.Popen | None:
    if _backend_is_healthy():
        print("Backend MC existente detectado en el puerto 5000.")
        return None
    if _port_is_open():
        raise RuntimeError(
            "El puerto 5000 está ocupado por un servicio que no es el backend MC."
        )

    print("Iniciando backend local para esta interfaz...")
    process = subprocess.Popen(
        [str(VENV_PYTHON), str(ROOT / "audio_editor_web.py")],
        cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if _backend_is_healthy():
            return process
        if process.poll() is not None:
            raise RuntimeError(
                f"El backend se cerró antes de iniciar (código {process.returncode})."
            )
        time.sleep(0.25)

    process.terminate()
    process.wait(timeout=5)
    raise RuntimeError("El backend no respondió en el puerto 5000 en 20 segundos.")


def _run_interface(interface: str) -> int:
    filename, needs_backend = INTERFACES[interface]
    script = ROOT / filename
    if not script.is_file():
        raise FileNotFoundError(f"No se encontró la interfaz: {filename}")

    backend = _start_backend() if needs_backend else None
    try:
        print(f"Interfaz seleccionada: {filename}")
        return _run([str(VENV_PYTHON), str(script)]).returncode
    finally:
        if backend is not None and backend.poll() is None:
            backend.terminate()
            try:
                backend.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend.kill()
                backend.wait()


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--prepare":
        _prepare_environment()
        print(f"Entorno listo: {VENV_PYTHON}")
        return 0

    if len(sys.argv) == 3 and sys.argv[1] == "--run":
        interface = sys.argv[2]
        if interface not in INTERFACES:
            raise ValueError(f"Interfaz desconocida: {interface}")
        return _run_interface(interface)

    if len(sys.argv) == 1:
        interface = DEFAULT_INTERFACE
    elif len(sys.argv) == 2 and sys.argv[1] in INTERFACES:
        interface = sys.argv[1]
    else:
        choices = "\n".join(f"  {name}" for name in INTERFACES)
        print(
            f"Indica una interfaz válida o --prepare:\n{choices}",
            file=sys.stderr,
        )
        return 2

    _prepare_environment()
    os.environ["PYTHONIOENCODING"] = "utf-8"
    return _run(
        [
            str(VENV_PYTHON),
            str(Path(__file__).resolve()),
            "--run",
            interface,
        ]
    ).returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        raise SystemExit(1)
