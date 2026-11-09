"""
🎵 MC Editor Pro - Interfaz Completa con Animaciones y Backend
"""

import sys
import os
import threading
import time
import requests
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QGroupBox,
    QTabWidget, QProgressBar, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
import numpy as np

# API Backend
API_URL = "http://127.0.0.1:5000/api"


class AudioVisualizer(QWidget):
    """Visualizador animado de audio"""
    def __init__(self, mode="waveform"):
        super().__init__()
        self.mode = mode
        self.animation_frame = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self.audio_data = None
        
    def animate(self):
        self.animation_frame = (self.animation_frame + 1) % 360
        self.update()
    
    def set_audio_data(self, data):
        self.audio_data = data
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(15, 15, 24))
        
        width = self.width()
        height = self.height()
        
        if self.mode == "waveform":
            self.draw_waveform(painter, width, height)
        elif self.mode == "spectrum":
            self.draw_spectrum(painter, width, height)
        elif self.mode == "spectrogram":
            self.draw_spectrogram(painter, width, height)
    
    def draw_waveform(self, painter, width, height):
        """Dibujar forma de onda animada"""
        painter.setPen(QPen(QColor(0, 170, 255), 2))
        
        for x in range(0, width, 2):
            # Oscilación animada
            t = (x / width) + (self.animation_frame / 100.0)
            y1 = height // 2 + int(np.sin(t * 3) * 30 + np.sin(t * 1.5) * 20)
            y2 = height // 2 + int(np.sin((x + 2) / width * 3 + self.animation_frame / 100.0) * 30 + np.sin((x + 2) / width * 1.5 + self.animation_frame / 100.0) * 20)
            
            painter.drawLine(x, int(np.clip(y1, 0, height)), x + 2, int(np.clip(y2, 0, height)))
        
        # Línea central
        painter.setPen(QPen(QColor(180, 0, 255, 50), 1))
        painter.drawLine(0, height // 2, width, height // 2)
    
    def draw_spectrum(self, painter, width, height):
        """Dibujar espectro animado"""
        painter.setPen(QPen(QColor(0, 255, 200), 1))
        
        num_bars = 64
        bar_width = width // num_bars
        
        for i in range(num_bars):
            # Altura dinámica del bar
            freq = i / num_bars
            magnitude = 0.3 + 0.7 * (np.sin(freq + self.animation_frame / 30.0) ** 2)
            bar_height = int(magnitude * (height - 20))
            
            # Color gradiente
            hue = int(180 + (i / num_bars) * 180)
            color = QColor.fromHsv(hue, 200, 255)
            painter.fillRect(i * bar_width + 2, height - bar_height, bar_width - 4, bar_height, color)
    
    def draw_spectrogram(self, painter, width, height):
        """Dibujar espectrograma"""
        # Grid de células coloreadas
        cell_width = width // 32
        cell_height = height // 16
        
        for y in range(16):
            for x in range(32):
                freq = (y / 16.0)
                time_pos = (x / 32.0)
                
                # Valor de intensidad basado en animación
                intensity = np.abs(np.sin(freq * 5 + self.animation_frame / 50.0) * np.cos(time_pos * 3 + self.animation_frame / 100.0))
                
                # Colorear celda
                color_val = int(intensity * 255)
                color = QColor(color_val, color_val // 2, 255 - color_val)
                painter.fillRect(x * cell_width, y * cell_height, cell_width, cell_height, color)


class BackendWorker(QThread):
    """Worker para comunicarse con el backend"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, endpoint, file_path=None, params=None):
        super().__init__()
        self.endpoint = endpoint
        self.file_path = file_path
        self.params = params or {}
    
    def run(self):
        try:
            if self.endpoint == "upload":
                self.upload_audio()
            elif self.endpoint == "separate":
                self.separate_stems()
            elif self.endpoint == "analyze":
                self.analyze_audio()
            elif self.endpoint == "export":
                self.export_audio()
        except Exception as e:
            self.error.emit(str(e))
    
    def upload_audio(self):
        """Subir archivo de audio"""
        try:
            with open(self.file_path, 'rb') as f:
                files = {'audio': f}
                response = requests.post(f"{API_URL}/upload-audio", files=files, timeout=60)
            
            if response.status_code == 200:
                self.progress.emit(100)
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Error al subir: {response.text}")
        except Exception as e:
            self.error.emit(f"Error: {e}")
    
    def separate_stems(self):
        """Separar stems"""
        try:
            response = requests.post(
                f"{API_URL}/separate-stems", 
                json=self.params,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            if response.status_code == 200:
                self.progress.emit(100)
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Error: {response.text}")
        except Exception as e:
            self.error.emit(f"Error: {e}")
    
    def analyze_audio(self):
        """Analizar audio"""
        try:
            response = requests.post(
                f"{API_URL}/analyze",
                json=self.params,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Error: {response.text}")
        except Exception as e:
            self.error.emit(f"Error: {e}")
    
    def export_audio(self):
        """Exportar audio"""
        try:
            self.progress.emit(50)
            response = requests.post(f"{API_URL}/export", json=self.params)
            
            if response.status_code == 200:
                self.progress.emit(100)
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Error: {response.text}")
        except Exception as e:
            self.error.emit(f"Error: {e}")


class MCEditorDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 MC Editor de Audio Pro")
        self.setGeometry(50, 50, 1600, 1000)
        self.setStyleSheet(self.get_style())
        
        # Estado
        self.current_file = None
        self.audio_id = None  # GUARDAR AUDIO_ID
        self.stems_data = None
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)
        
        # Panel izquierdo (controles)
        left = self.create_left_panel()
        main_layout.addWidget(left, 1)
        
        # Panel central (visualizador)
        center = self.create_center_panel()
        main_layout.addWidget(center, 3)
        
        # Panel derecho (stems)
        right = self.create_right_panel()
        main_layout.addWidget(right, 1)
    
    def get_style(self):
        return """
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
            padding: 10px;
            font-weight: bold;
            min-height: 32px;
        }
        QPushButton:hover {
            background-color: #00aaff;
        }
        QPushButton:pressed {
            background-color: #005bb8;
        }
        QPushButton.secondary {
            background-color: #b400ff;
            border: 2px solid #d600ff;
        }
        QPushButton.secondary:hover {
            background-color: #d600ff;
        }
        QPushButton.success {
            background-color: #00aa00;
        }
        QPushButton.success:hover {
            background-color: #00dd00;
            box-shadow: 0 0 15px #00dd00;
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
        QSlider::handle:horizontal:hover {
            background-color: #00ffff;
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
        QTabWidget::pane {
            border: 2px solid #0077ff;
            border-radius: 6px;
        }
        QTabBar::tab {
            background-color: #1a1a22;
            color: #aaa;
            padding: 8px 20px;
            border: 1px solid #333;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background-color: #0077ff;
            color: #fff;
            font-weight: bold;
        }
        """
    
    def create_left_panel(self):
        """Panel de controles izquierdo"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # ===== ARCHIVO =====
        file_group = QGroupBox("📂 ARCHIVO")
        file_layout = QVBoxLayout()
        btn_load = QPushButton("📂 Cargar Audio")
        btn_load.clicked.connect(self.load_audio)
        file_layout.addWidget(btn_load)
        self.label_file = QLabel("⏳ Sin archivo")
        self.label_file.setStyleSheet("color: #aaa; font-size: 9px;")
        file_layout.addWidget(self.label_file)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # ===== REPRODUCCIÓN =====
        play_group = QGroupBox("▶️ REPRODUCCIÓN")
        play_layout = QVBoxLayout()
        play_btns = QHBoxLayout()
        
        for text in ["▶ Play", "⏸ Pause", "⏹ Stop"]:
            btn = QPushButton(text)
            btn.setMaximumWidth(80)
            btn.clicked.connect(lambda checked, t=text: print(f"Acción: {t}"))
            play_btns.addWidget(btn)
        
        play_layout.addLayout(play_btns)
        
        # Timeline
        play_layout.addWidget(QLabel("Tiempo: 00:00 / 00:00"))
        timeline = QSlider(Qt.Orientation.Horizontal)
        timeline.setRange(0, 100)
        play_layout.addWidget(timeline)
        
        play_group.setLayout(play_layout)
        layout.addWidget(play_group)
        
        # ===== EFECTOS =====
        effects_group = QGroupBox("🎛️ EFECTOS")
        effects_layout = QVBoxLayout()
        
        # Volumen
        effects_layout.addWidget(QLabel("🔊 Volumen: 0 dB"))
        vol = QSlider(Qt.Orientation.Horizontal)
        vol.setRange(-30, 10)
        vol.setValue(0)
        effects_layout.addWidget(vol)
        
        # Pitch
        effects_layout.addWidget(QLabel("🎼 Pitch: 0"))
        pitch = QSlider(Qt.Orientation.Horizontal)
        pitch.setRange(-12, 12)
        pitch.setValue(0)
        effects_layout.addWidget(pitch)
        
        # Speed
        effects_layout.addWidget(QLabel("⚡ Speed: 1.0x"))
        speed = QSlider(Qt.Orientation.Horizontal)
        speed.setRange(50, 200)
        speed.setValue(100)
        effects_layout.addWidget(speed)
        
        effects_group.setLayout(effects_layout)
        layout.addWidget(effects_group)
        
        # ===== PROCESAMIENTO =====
        proc_group = QGroupBox("🎯 PROCESAMIENTO")
        proc_layout = QVBoxLayout()
        
        btn_stems = QPushButton("🎼 Separar Stems (IA)")
        btn_stems.setStyleSheet("QPushButton { background-color: #b400ff } QPushButton:hover { background-color: #d600ff }")
        btn_stems.clicked.connect(self.separate_stems)
        proc_layout.addWidget(btn_stems)
        
        btn_analyze = QPushButton("🔍 Analizar Audio")
        btn_analyze.clicked.connect(self.analyze_audio)
        proc_layout.addWidget(btn_analyze)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        proc_layout.addWidget(self.progress)
        
        proc_group.setLayout(proc_layout)
        layout.addWidget(proc_group)
        
        # ===== EXPORTAR =====
        export_group = QGroupBox("💾 EXPORTAR")
        export_layout = QVBoxLayout()
        
        export_format = QComboBox()
        export_format.addItems(["MP3", "WAV", "FLAC", "OGG", "M4A"])
        export_layout.addWidget(export_format)
        
        btn_export = QPushButton("💾 Exportar")
        btn_export.setStyleSheet("QPushButton { background-color: #00aa00 } QPushButton:hover { background-color: #00dd00 }")
        btn_export.clicked.connect(lambda: print("Exportando..."))
        export_layout.addWidget(btn_export)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def create_center_panel(self):
        """Panel central con visualización"""
        group = QGroupBox("📊 VISUALIZACIÓN EN TIEMPO REAL")
        layout = QVBoxLayout()
        
        # Tabs de vista
        tabs = QTabWidget()
        
        # Canvas para cada visualización
        self.canvas_wave = AudioVisualizer("waveform")
        tabs.addTab(self.canvas_wave, "🌊 Forma de Onda")
        
        self.canvas_spec = AudioVisualizer("spectrum")
        tabs.addTab(self.canvas_spec, "📈 Espectro")
        
        self.canvas_spectro = AudioVisualizer("spectrogram")
        tabs.addTab(self.canvas_spectro, "🔥 Spectrograma")
        
        layout.addWidget(tabs)
        
        # Info de audio
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("📊 SR: 44100 Hz"))
        info_layout.addWidget(QLabel("⏱ Duración: 00:00"))
        info_layout.addWidget(QLabel("♪ BPM: --"))
        info_layout.addWidget(QLabel("🎼 Tonalidad: --"))
        layout.addLayout(info_layout)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self):
        """Panel de stems derecho"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        group = QGroupBox("🎼 STEMS (Voces Separadas)")
        stems_layout = QVBoxLayout()
        
        self.stem_controls = {}
        
        stems = [
            ("🎙 Voz", "#ff6b9d"),
            ("🎸 Bajo", "#00d9ff"),
            ("🥁 Batería", "#ffd93d"),
            ("✨ Otros", "#00ffcc")
        ]
        
        for name, color in stems:
            # Subgrupo para cada stem
            stem_group = QGroupBox(name)
            stem_layout = QVBoxLayout()
            
            # Volumen
            vol_label = QLabel("Volumen: 50%")
            vol_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            stem_layout.addWidget(vol_label)
            
            vol_slider = QSlider(Qt.Orientation.Horizontal)
            vol_slider.setRange(0, 100)
            vol_slider.setValue(50)
            stem_layout.addWidget(vol_slider)
            
            # Botones
            btn_layout = QHBoxLayout()
            btn_solo = QPushButton("🎧 Solo")
            btn_solo.setMaximumWidth(85)
            btn_solo.clicked.connect(lambda checked, s=name: print(f"Solo: {s}"))
            btn_layout.addWidget(btn_solo)
            
            btn_mute = QPushButton("🔇 Mute")
            btn_mute.setMaximumWidth(85)
            btn_mute.clicked.connect(lambda checked, s=name: print(f"Mute: {s}"))
            btn_layout.addWidget(btn_mute)
            
            stem_layout.addLayout(btn_layout)
            stem_group.setLayout(stem_layout)
            stems_layout.addWidget(stem_group)
            
            self.stem_controls[name] = {
                'slider': vol_slider,
                'group': stem_group
            }
        
        group.setLayout(stems_layout)
        layout.addWidget(group)
        layout.addStretch()
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def load_audio(self):
        """Cargar archivo de audio"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo de audio",
            "",
            "Todos los formatos (*.mp3 *.wav *.flac *.ogg *.m4a *.mpeg *.mp2 *.wma *.aac *.opus *.aiff *.au *.raw *.voc);;MP3 (*.mp3);;WAV (*.wav);;FLAC (*.flac);;OGG (*.ogg);;M4A (*.m4a);;MPEG (*.mpeg *.mp2);;WMA (*.wma);;AAC (*.aac);;OPUS (*.opus);;AIFF (*.aiff);;Todos (*.*)"
        )
        
        if file_path:
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.label_file.setText(f"✓ {filename}")
            
            # Subir al backend
            self.progress.setVisible(True)
            self.progress.setValue(50)
            
            self.worker = BackendWorker("upload", file_path)
            self.worker.finished.connect(self.on_audio_loaded)
            self.worker.error.connect(lambda e: print(f"Error: {e}"))
            self.worker.start()
    
    def on_audio_loaded(self, result):
        """Audio cargado exitosamente"""
        self.progress.setValue(100)
        self.progress.setVisible(False)
        # GUARDAR audio_id
        self.audio_id = result.get('audio_id')
        print(f"✓ Audio cargado: {result.get('filename')} - ID: {self.audio_id}")

    
    def separate_stems(self):
        """Separar stems"""
        if not self.audio_id:
            print("❌ Primero carga un archivo")
            return
        
        self.progress.setVisible(True)
        self.progress.setValue(0)
        print("🔄 Separando stems (esto puede tardar unos segundos)...")
        
        self.worker = BackendWorker("separate", params={"audio_id": self.audio_id})
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.on_stems_separated)
        self.worker.error.connect(lambda e: print(f"❌ Error: {e}"))
        self.worker.start()
    
    def on_stems_separated(self, result):
        """Stems separados"""
        self.stems_data = result
        self.progress.setVisible(False)
        print(f"✓ Stems separados: {result.get('stems_id')}")
    
    def analyze_audio(self):
        """Analizar audio"""
        if not self.audio_id:
            print("❌ Primero carga un archivo")
            return
        
        self.worker = BackendWorker("analyze", params={"audio_id": self.audio_id})
        self.worker.finished.connect(lambda r: print(f"✓ Análisis: {r}"))
        self.worker.error.connect(lambda e: print(f"❌ Error: {e}"))
        self.worker.start()


def main():
    app = QApplication(sys.argv)
    window = MCEditorDesktop()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
