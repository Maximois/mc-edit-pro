"""
🎵 MC Editor Pro - Editor Profesional de Audio
Separación inteligente de stems + Edición completa tipo Audacity/Reaper
"""

import sys
import os
import threading
import time
import requests
import json
import numpy as np
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QScrollArea, QGroupBox,
    QTabWidget, QProgressBar, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QSplitter, QDockWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QSize, QRect
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QIcon, QPixmap

# Pyaudio es optional
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("PyAudio no instalado - reproducción deshabilitada")


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

API_URL = "http://127.0.0.1:5000/api"
CHUNK = 2048
CHANNELS = 2
RATE = 44100

# Colores por stem
STEM_COLORS = {
    'voz': QColor(255, 107, 157),      # Rosa
    'bajo': QColor(0, 217, 255),       # Cyan
    'bateria': QColor(255, 217, 61),   # Amarillo
    'otros': QColor(0, 255, 204)       # Verde agua
}

# ============================================================================
# AUDIO PLAYER - Reproductor en tiempo real (OPCIONAL)
# ============================================================================

class AudioPlayer(QThread):
    """Thread para reproducción de audio sin bloquear UI"""
    position_changed = pyqtSignal(int)
    finished = pyqtSignal()
    
    def __init__(self, audio_data, sr):
        super().__init__()
        self.audio_data = audio_data
        self.sr = sr
        self.is_playing = False
        self.position = 0
        self.daemon = True
    
    def run(self):
        if not PYAUDIO_AVAILABLE:
            print("⚠️  PyAudio no disponible")
            return
        
        if self.audio_data is None or len(self.audio_data) == 0:
            return
        
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paFloat32, channels=1, rate=self.sr, output=True)
            
            self.is_playing = True
            chunk_size = self.sr // 30  # ~30 FPS updates
            
            for i in range(0, len(self.audio_data), chunk_size):
                if not self.is_playing:
                    break
                
                chunk = self.audio_data[i:i+chunk_size]
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
                
                # Normalizar a float32
                chunk = np.clip(chunk, -1.0, 1.0).astype(np.float32)
                stream.write(chunk.tobytes())
                
                self.position = i
                self.position_changed.emit(i)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            self.is_playing = False
            self.finished.emit()
            
        except Exception as e:
            print(f"Error en reproducción: {e}")
    
    def stop(self):
        self.is_playing = False

# ============================================================================
# BACKEND WORKER - Comunicación con Flask
# ============================================================================

class BackendWorker(QThread):
    """Worker para llamadas async al backend"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, task, params=None):
        super().__init__()
        self.task = task
        self.params = params or {}
    
    def run(self):
        try:
            if self.task == "upload":
                self.upload()
            elif self.task == "separate":
                self.separate()
            elif self.task == "analyze":
                self.analyze()
            elif self.task == "export":
                self.export()
        except Exception as e:
            self.error.emit(str(e))
    
    def upload(self):
        """Subir archivo"""
        filepath = self.params.get('filepath')
        with open(filepath, 'rb') as f:
            r = requests.post(f"{API_URL}/upload-audio", files={'audio': f}, timeout=60)
        
        if r.status_code == 200:
            self.finished.emit(r.json())
        else:
            self.error.emit(r.text)
    
    def separate(self):
        """Separar stems"""
        audio_id = self.params.get('audio_id')
        r = requests.post(
            f"{API_URL}/separate-stems",
            json={'audio_id': audio_id},
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        if r.status_code == 200:
            self.finished.emit(r.json())
        else:
            self.error.emit(r.text)
    
    def analyze(self):
        """Analizar audio"""
        audio_id = self.params.get('audio_id')
        r = requests.post(
            f"{API_URL}/analyze",
            json={'audio_id': audio_id},
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if r.status_code == 200:
            self.finished.emit(r.json())
        else:
            self.error.emit(r.text)
    
    def export(self):
        """Exportar stems"""
        audio_id = self.params.get('audio_id')
        stem_name = self.params.get('stem')
        output_path = self.params.get('output')
        format_type = self.params.get('format', 'wav')
        
        r = requests.post(
            f"{API_URL}/export",
            json={'audio_id': audio_id, 'format': format_type},
            timeout=60
        )
        
        if r.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(r.content)
            self.finished.emit({'status': 'ok', 'path': output_path})
        else:
            self.error.emit(r.text)

# ============================================================================
# WAVEFORM DISPLAY - Visualización de audio
# ============================================================================

class WaveformDisplay(QWidget):
    """Display interactivo de waveforms multi-track"""
    
    def __init__(self):
        super().__init__()
        self.stems = {}  # {'voz': numpy_array, ...}
        self.zoom = 1.0
        self.scroll_pos = 0
        self.sr = 44100
        self.selected_stem = None
        self.setMinimumHeight(400)
    
    def set_stems(self, stems_data):
        """Cargar stems (dict base64 codificados)"""
        import base64
        self.stems = {}
        for name, encoded in stems_data.items():
            try:
                audio_bytes = base64.b64decode(encoded)
                audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                self.stems[name] = audio
            except:
                pass
        self.update()
    
    def paintEvent(self, event):
        """Dibujar waveforms"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(20, 20, 30))
        
        if not self.stems:
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Carga un archivo de audio")
            return
        
        # Dibujar cada stem
        height = self.height()
        track_height = height // len(self.stems)
        
        for i, (name, audio) in enumerate(self.stems.items()):
            y_offset = i * track_height
            
            # Fondo de track
            is_selected = name == self.selected_stem
            bg_color = QColor(40, 40, 60) if is_selected else QColor(30, 30, 45)
            painter.fillRect(0, y_offset, self.width(), track_height, bg_color)
            
            # Nombre del stem
            painter.setPen(QPen(STEM_COLORS[name]))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(5, y_offset + 15, name.upper())
            
            # Waveform
            self.draw_waveform(painter, audio, y_offset, track_height, STEM_COLORS[name])
    
    def draw_waveform(self, painter, audio, y_offset, height, color):
        """Dibujar forma de onda"""
        painter.setPen(QPen(color, 1))
        
        width = self.width()
        
        # Calcular cuántos samples por pixel
        samples_per_pixel = max(1, len(audio) // width)
        
        # Dibujar línea central
        painter.setPen(QPen(QColor(80, 80, 100)))
        center_y = y_offset + height // 2
        painter.drawLine(0, center_y, width, center_y)
        
        # Dibujar waveform
        painter.setPen(QPen(color, 1))
        for x in range(width):
            start_idx = x * samples_per_pixel
            end_idx = min((x + 1) * samples_per_pixel, len(audio))
            
            if end_idx > start_idx:
                chunk = audio[start_idx:end_idx]
                max_val = np.max(np.abs(chunk)) if len(chunk) > 0 else 0
                y = center_y - int(max_val * (height // 2 - 5))
                painter.drawLine(x, center_y, x, y)
    
    def mousePressEvent(self, event):
        """Seleccionar stem al hacer click"""
        height = self.height()
        track_height = height // len(self.stems)
        track_idx = event.position().y() // track_height
        
        if 0 <= track_idx < len(self.stems):
            self.selected_stem = list(self.stems.keys())[int(track_idx)]
            self.update()

# ============================================================================
# MIXER TRACK - Panel individual por stem
# ============================================================================

class MixerTrack(QGroupBox):
    """Panel de control para un stem individual"""
    
    def __init__(self, name, color):
        super().__init__(name.upper())
        self.name = name
        self.color = color
        self.setStyleSheet(f"""
            QGroupBox {{
                color: rgb({color.red()}, {color.green()}, {color.blue()});
                border: 2px solid rgb({color.red()}, {color.green()}, {color.blue()});
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Volumen
        vol_label = QLabel("Volumen: 0 dB")
        layout.addWidget(vol_label)
        
        self.vol_slider = QSlider(Qt.Orientation.Vertical)
        self.vol_slider.setRange(-60, 12)
        self.vol_slider.setValue(0)
        self.vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"Volumen: {v} dB"))
        layout.addWidget(self.vol_slider)
        
        # Pan
        pan_label = QLabel("Pan: C")
        layout.addWidget(pan_label)
        
        self.pan_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_slider.setRange(-100, 100)
        self.pan_slider.setValue(0)
        self.pan_slider.valueChanged.connect(lambda v: pan_label.setText(
            f"Pan: {'L' if v < -5 else 'C' if abs(v) <= 5 else 'R'} ({v})"
        ))
        layout.addWidget(self.pan_slider)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_mute = QPushButton("🔇 Mute")
        self.btn_mute.setCheckable(True)
        self.btn_mute.setStyleSheet("QPushButton:checked { background-color: #ff3333; }")
        btn_layout.addWidget(self.btn_mute)
        
        self.btn_solo = QPushButton("🎧 Solo")
        self.btn_solo.setCheckable(True)
        self.btn_solo.setStyleSheet("QPushButton:checked { background-color: #33ff33; }")
        btn_layout.addWidget(self.btn_solo)
        
        layout.addLayout(btn_layout)
        
        # Exportar
        self.btn_export = QPushButton("💾 Exportar")
        self.btn_export.setStyleSheet("background-color: #0077ff;")
        layout.addWidget(self.btn_export)
        
        # Peakometer
        layout.addWidget(QLabel("Pico: 0.0"))
        
        layout.addStretch()
        self.setLayout(layout)

# ============================================================================
# MAIN EDITOR WINDOW
# ============================================================================

class MCProAudioEditor(QMainWindow):
    """Editor profesional de audio - Aplicación principal"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 MC Editor Pro - Editor Profesional")
        self.setGeometry(50, 50, 1920, 1080)
        
        # Estado
        self.audio_id = None
        self.stems_data = {}
        self.analysis_data = {}
        self.players = {}  # {stem_name: AudioPlayer}
        
        # UI Principal
        self.init_ui()
        self.apply_style()
    
    def init_ui(self):
        """Inicializar interfaz"""
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)
        
        # ===== PANEL IZQUIERDO - Mixer =====
        mixer_group = QGroupBox("🎛️ MIXER")
        mixer_layout = QVBoxLayout()
        
        # Transport controls
        transport = QHBoxLayout()
        self.btn_load = QPushButton("📁 Cargar Audio")
        self.btn_load.clicked.connect(self.load_audio)
        transport.addWidget(self.btn_load)
        
        self.btn_play = QPushButton("▶️ Play")
        self.btn_play.clicked.connect(self.play_audio)
        transport.addWidget(self.btn_play)
        
        self.btn_pause = QPushButton("⏸️ Pause")
        self.btn_pause.clicked.connect(self.pause_audio)
        transport.addWidget(self.btn_pause)
        
        self.btn_stop = QPushButton("⏹️ Stop")
        self.btn_stop.clicked.connect(self.stop_audio)
        transport.addWidget(self.btn_stop)
        
        mixer_layout.addLayout(transport)
        
        # Info
        self.label_file = QLabel("📁 Sin archivo cargado")
        mixer_layout.addWidget(self.label_file)
        
        # Botones principales
        self.btn_separate = QPushButton("🎼 Separar Stems")
        self.btn_separate.setStyleSheet("background-color: #b400ff; font-weight: bold; padding: 10px;")
        self.btn_separate.clicked.connect(self.separate_stems)
        mixer_layout.addWidget(self.btn_separate)
        
        self.btn_analyze = QPushButton("🔍 Analizar")
        self.btn_analyze.clicked.connect(self.analyze_audio)
        mixer_layout.addWidget(self.btn_analyze)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        mixer_layout.addWidget(self.progress)
        
        # Tracks del mixer
        scroll_mixer = QScrollArea()
        scroll_mixer.setWidgetResizable(True)
        mixer_widget = QWidget()
        self.mixer_tracks_layout = QVBoxLayout()
        mixer_widget.setLayout(self.mixer_tracks_layout)
        scroll_mixer.setWidget(mixer_widget)
        mixer_layout.addWidget(scroll_mixer)
        
        mixer_group.setLayout(mixer_layout)
        main_layout.addWidget(mixer_group, 0)
        
        # ===== PANEL CENTRAL - Waveforms =====
        center_group = QGroupBox("📊 TIMELINE & WAVEFORMS")
        center_layout = QVBoxLayout()
        
        # Timeline
        timeline_layout = QHBoxLayout()
        timeline_layout.addWidget(QLabel("Tiempo:"))
        self.label_time = QLabel("00:00 / 00:00")
        timeline_layout.addWidget(self.label_time)
        timeline_layout.addStretch()
        center_layout.addLayout(timeline_layout)
        
        # Display
        self.waveform = WaveformDisplay()
        center_layout.addWidget(self.waveform)
        
        # Zoom
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(1, 10)
        self.zoom_slider.setValue(1)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addStretch()
        center_layout.addLayout(zoom_layout)
        
        center_group.setLayout(center_layout)
        main_layout.addWidget(center_group, 2)
        
        # ===== PANEL DERECHO - Análisis & Efectos =====
        right_group = QGroupBox("🔧 ANÁLISIS & EFFECTS")
        right_layout = QVBoxLayout()
        
        # Tabs
        self.tab_analysis = QTabWidget()
        
        # Tab: Analysis
        analysis_w = QWidget()
        analysis_l = QVBoxLayout()
        
        self.label_bpm = QLabel("BPM: --")
        analysis_l.addWidget(self.label_bpm)
        
        self.label_key = QLabel("Tonalidad: --")
        analysis_l.addWidget(self.label_key)
        
        self.label_instruments = QLabel("Instrumentos: --")
        analysis_l.addWidget(self.label_instruments)
        
        analysis_w.setLayout(analysis_l)
        self.tab_analysis.addTab(analysis_w, "📈 Análisis")
        
        # Tab: Export
        export_w = QWidget()
        export_l = QVBoxLayout()
        
        export_l.addWidget(QLabel("Exportar:"))
        
        self.combo_format = QComboBox()
        self.combo_format.addItems(["WAV", "MP3", "FLAC", "OGG"])
        export_l.addWidget(self.combo_format)
        
        self.btn_export_all = QPushButton("💾 Exportar Mezcla")
        self.btn_export_all.clicked.connect(self.export_all)
        export_l.addWidget(self.btn_export_all)
        
        export_w.setLayout(export_l)
        self.tab_analysis.addTab(export_w, "💾 Exportar")
        
        right_layout.addWidget(self.tab_analysis)
        right_group.setLayout(right_layout)
        main_layout.addWidget(right_group, 1)
    
    def apply_style(self):
        """Aplicar estilo oscuro profesional"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0f;
                color: #f5f5f5;
            }
            QGroupBox {
                color: #f5f5f5;
                border: 2px solid #0077ff;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0077ff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00aaff;
            }
            QPushButton:pressed {
                background-color: #005bb8;
            }
            QSlider::groove:horizontal {
                background-color: #222;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #00aaff;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QLabel {
                color: #f5f5f5;
            }
            QComboBox {
                background-color: #1a1a22;
                color: #f5f5f5;
                border: 1px solid #0077ff;
                border-radius: 4px;
                padding: 6px;
            }
            QProgressBar {
                background-color: #1a1a22;
                border: 1px solid #0077ff;
                border-radius: 4px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #b400ff;
                border-radius: 3px;
            }
            QScrollArea {
                background-color: #0a0a0f;
                border: none;
            }
            QTabWidget QTabBar::tab {
                background-color: #1a1a22;
                color: #f5f5f5;
                padding: 8px 20px;
                border: 1px solid #0077ff;
            }
            QTabWidget QTabBar::tab:selected {
                background-color: #0077ff;
            }
        """)
    
    def load_audio(self):
        """Cargar archivo"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir audio", "",
            "Audio (*.mp3 *.wav *.flac *.ogg *.m4a *.mpeg);;Todos (*.*)"
        )
        
        if not path:
            return
        
        self.label_file.setText(f"📁 {Path(path).name}")
        self.progress.setVisible(True)
        self.progress.setValue(50)
        
        worker = BackendWorker("upload", {"filepath": path})
        worker.finished.connect(self.on_audio_loaded)
        worker.error.connect(lambda e: print(f"Error: {e}"))
        worker.start()
    
    def on_audio_loaded(self, result):
        """Audio cargado"""
        self.progress.setValue(100)
        self.progress.setVisible(False)
        self.audio_id = result.get('audio_id')
        print(f"✓ Audio: {result.get('filename')} - ID: {self.audio_id}")
    
    def separate_stems(self):
        """Separar stems"""
        if not self.audio_id:
            print("❌ Carga un archivo primero")
            return
        
        self.progress.setVisible(True)
        self.progress.setValue(0)
        print("🔄 Separando stems...")
        
        worker = BackendWorker("separate", {"audio_id": self.audio_id})
        worker.finished.connect(self.on_stems_separated)
        worker.error.connect(lambda e: print(f"Error: {e}"))
        worker.start()
    
    def on_stems_separated(self, result):
        """Stems listos"""
        self.progress.setValue(100)
        self.progress.setVisible(False)
        self.stems_data = result.get('stems', {})
        print(f"✓ Stems: {list(self.stems_data.keys())}")
        
        # Cargar en waveform
        self.waveform.set_stems(self.stems_data)
        
        # Crear tracks en mixer
        self.create_mixer_tracks()
    
    def create_mixer_tracks(self):
        """Crear paneles en mixer"""
        # Limpiar antiguos
        while self.mixer_tracks_layout.count():
            self.mixer_tracks_layout.takeAt(0).widget().deleteLater()
        
        # Crear nuevos
        for stem_name in ['voz', 'bajo', 'bateria', 'otros']:
            track = MixerTrack(stem_name, STEM_COLORS[stem_name])
            track.btn_export.clicked.connect(lambda checked, n=stem_name: self.export_stem(n))
            self.mixer_tracks_layout.addWidget(track)
        
        self.mixer_tracks_layout.addStretch()
    
    def analyze_audio(self):
        """Analizar"""
        if not self.audio_id:
            return
        
        worker = BackendWorker("analyze", {"audio_id": self.audio_id})
        worker.finished.connect(self.on_analysis_done)
        worker.error.connect(lambda e: print(f"Error: {e}"))
        worker.start()
    
    def on_analysis_done(self, result):
        """Mostrar análisis"""
        analysis = result.get('analysis', {})
        self.label_bpm.setText(f"BPM: {analysis.get('bpm', '--'):.1f}")
        self.label_key.setText(f"Tonalidad: {analysis.get('key', '--')}")
        self.label_instruments.setText(f"Instrumentos: {', '.join(analysis.get('instruments', []))}")
        print(f"✓ Análisis: {analysis}")
    
    def play_audio(self):
        if not PYAUDIO_AVAILABLE:
            print("⚠️  PyAudio no instalado - reproducción no disponible")
            print("   Instala: pip install pyaudio")
            return
        print("▶️ Play")
    
    def pause_audio(self):
        print("⏸️ Pause")
    
    def stop_audio(self):
        print("⏹️ Stop")
    
    def export_stem(self, stem_name):
        """Exportar stem individual"""
        path, _ = QFileDialog.getSaveFileName(self, f"Exportar {stem_name}", stem_name, "WAV (*.wav)")
        if path:
            print(f"💾 Exportando {stem_name} a {path}")
    
    def export_all(self):
        """Exportar mezcla"""
        path, _ = QFileDialog.getSaveFileName(self, "Exportar mezcla", "mezcla", "WAV (*.wav)")
        if path:
            print(f"💾 Exportando mezcla a {path}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    editor = MCProAudioEditor()
    editor.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
