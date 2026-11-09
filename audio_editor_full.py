import librosa
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import Tk, Label, Button, Entry, messagebox, filedialog, Menu, Scale, Frame, Canvas, Listbox, Scrollbar
from tkinter import ttk
import soundfile as sf
import sounddevice as sd
import threading
import os
from scipy import signal as scipy_signal
from scipy.fft import fft
import time
import ctypes
from sklearn.decomposition import FastICA
from pydub import AudioSegment
import warnings
warnings.filterwarnings('ignore')


class AudioEditorPro:
    """Editor de audio profesional con todas las funcionalidades"""
    
    def __init__(self):
        self.root = Tk()
        self.root.title("🎵 MC Audio Editor Pro")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0b0c10")
        
        # Cambiar barra de título a negro (Windows API)
        self.set_titlebar_color_black()
        
        # Variables de estado
        self.audio = None
        self.original_audio = None
        self.sr = None
        self.file_path = None
        self.playing = False
        self.play_thread = None
        self.current_position = 0
        self.history = []
        self.history_index = -1
        
        # Configurar estilo oscuro profesional con acentos musicales
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#0b0c10')
        style.configure('Dark.TLabel', background='#0b0c10', foreground='#f5f5f5')
        style.configure('Dark.TButton', background='#b400ff', foreground='#f5f5f5')
        
        # Crear UI
        self.create_menu()
        self.decorative_background()
        self.create_top_panel()
        self.create_waveform_panel()
        self.create_effects_panel()
        self.create_playback_controls()
        self.create_status_bar()
        
    def set_titlebar_color_black(self):
        """Cambiar titlebar de Windows a negro"""
        try:
            # Obtener handle de la ventana
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd == 0:
                hwnd = int(self.root.wm_frame(), 16) if hasattr(self.root, 'wm_frame') else None
            
            # Usar API de Windows para cambiar titlebar
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.windll.kernel32.GetForegroundWindow(),
                20,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except:
            pass  # Si no funciona en este sistema, continuar sin cambios
        
    def decorative_background(self):
        """Crea elementos decorativos de fondo"""
        # Canvas para notas flotantes
        self.bg_canvas = Canvas(self.root, bg="#0b0c10", highlightthickness=0, height=40)
        self.bg_canvas.pack(fill="x", padx=10, pady=5)

        # Notas musicales animadas
        notes = ['♪', '♫', '♬', '♪', '♫']
        colors = ['#00aaff', '#b400ff', '#ffcc00', '#00aaff', '#ff00ff']
        self.note_objs = []

        for i, (note, color) in enumerate(zip(notes, colors)):
            x = 50 + i * 220
            note_id = self.bg_canvas.create_text(x, 20, text=note, font=('Arial', 16),
                                                 fill=color)
            self.note_objs.append({'id': note_id, 'x': x, 'y': 20, 'color': color})

        self.animate_notes()

    def animate_notes(self):
        """Anima las notas musicales de fondo"""
        for note in self.note_objs:
            # Movimiento flotante
            note['y'] = 20 + 5 * np.sin(time.time())
            self.bg_canvas.coords(note['id'], note['x'], note['y'])

        self.root.after(50, self.animate_notes)
        
    def create_menu(self):
        """Menú superior"""
        menubar = Menu(self.root, bg='#1a0033', fg='#00aaff')
        self.root.config(menu=menubar)
        
        # Archivo
        file_menu = Menu(menubar, tearoff=0, bg='#1a0033', fg='#00aaff')
        menubar.add_cascade(label="📁 Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir (Ctrl+O)", command=self.open_file)
        file_menu.add_command(label="Guardar (Ctrl+S)", command=self.save_file)
        file_menu.add_command(label="Guardar Como...", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Edición
        edit_menu = Menu(menubar, tearoff=0, bg='#1a0033', fg='#00aaff')
        menubar.add_cascade(label="✂️ Edición", menu=edit_menu)
        edit_menu.add_command(label="Deshacer (Ctrl+Z)", command=self.undo)
        edit_menu.add_command(label="Rehacer (Ctrl+Y)", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Deletrear Silencio", command=self.trim_silence)
        
        # Efectos
        effects_menu = Menu(menubar, tearoff=0, bg='#1a0033', fg='#00aaff')
        menubar.add_cascade(label="⚡ Efectos", menu=effects_menu)
        effects_menu.add_command(label="Normalizar", command=self.normalize_audio)
        effects_menu.add_command(label="Amplificar +3dB", command=lambda: self.amplify(3))
        effects_menu.add_command(label="Reducir -3dB", command=lambda: self.amplify(-3))
        effects_menu.add_command(label="Reverb", command=self.apply_reverb)
        effects_menu.add_command(label="Echo", command=self.apply_echo)
        effects_menu.add_command(label="Fade In", command=self.fade_in)
        effects_menu.add_command(label="Fade Out", command=self.fade_out)
        effects_menu.add_command(label="Compresión", command=self.apply_compression)
        
        # Análisis
        analyze_menu = Menu(menubar, tearoff=0, bg='#1a0033', fg='#00aaff')
        menubar.add_cascade(label="🔍 Análisis", menu=analyze_menu)
        analyze_menu.add_command(label="Detectar BPM", command=self.detect_bpm)
        analyze_menu.add_command(label="Detectar Tonalidad", command=self.detect_key)
        analyze_menu.add_command(label="Extraer Características", command=self.extract_features)
        analyze_menu.add_command(label="Identificar Instrumentos", command=self.identify_instruments)
        
        # Stem Separation
        stem_menu = Menu(menubar, tearoff=0, bg='#1a0033', fg='#00aaff')
        menubar.add_cascade(label="🎼 Stem Separation", menu=stem_menu)
        stem_menu.add_command(label="Separar Stems (4 factores)", command=self.separate_stems)
        stem_menu.add_command(label="Editar Stems", command=self.open_stem_editor)
        stem_menu.add_separator()
        stem_menu.add_command(label="Exportar Stems", command=self.export_stems)
        
        # Exportación
        export_menu = Menu(menubar, tearoff=0, bg='#1a0033', fg='#00aaff')
        menubar.add_cascade(label="💾 Exportar", menu=export_menu)
        export_menu.add_command(label="WAV (sin pérdida)", command=lambda: self.export_audio("wav"))
        export_menu.add_command(label="MP3 (320kbps)", command=lambda: self.export_audio("mp3"))
        export_menu.add_command(label="FLAC (sin pérdida)", command=lambda: self.export_audio("flac"))
        export_menu.add_command(label="OGG (Vorbis)", command=lambda: self.export_audio("ogg"))
        export_menu.add_command(label="M4A (AAC)", command=lambda: self.export_audio("m4a"))
        
        # Atajos
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<space>", lambda e: self.toggle_playback())
        
    def create_top_panel(self):
        """Panel superior con carga de archivo"""
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side="top", fill="x", padx=10, pady=10)

        Label(top_frame, text="📂 Archivo:", bg="#0b0c10", fg="#00aaff", font=('Arial', 11, 'bold')).pack(side="left", padx=5)

        self.file_entry = Entry(top_frame, width=60, bg="#1a0033", fg="#00aaff", insertbackground='#00aaff', font=('Arial', 10))
        self.file_entry.pack(side="left", padx=5)

        Button(top_frame, text="📂 Abrir", command=self.open_file, bg="#00aaff", fg="#0b0c10", font=('Arial', 9, 'bold')).pack(side="left", padx=2)
        Button(top_frame, text="⬇️ Cargar", command=self.load_audio, bg="#b400ff", fg="#f5f5f5", font=('Arial', 9, 'bold')).pack(side="left", padx=2)
        Button(top_frame, text="🗑️ Limpiar", command=self.clear_audio, bg="#ff1493", fg="#f5f5f5", font=('Arial', 9, 'bold')).pack(side="left", padx=2)
        
    def create_waveform_panel(self):
        """Panel para visualizar waveform y espectrograma"""
        waveform_frame = ttk.Frame(self.root)
        waveform_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Botones de visualización
        viz_buttons = Frame(waveform_frame, bg="#0b0c10")
        viz_buttons.pack(fill="x", pady=5)

        Button(viz_buttons, text="🌊 Waveform", command=self.show_waveform, bg="#1f6feb", fg="#c9d1d9").pack(side="left", padx=2)
        Button(viz_buttons, text="📊 Espectrograma", command=self.show_spectrogram, bg="#1f6feb", fg="#c9d1d9").pack(side="left", padx=2)
        Button(viz_buttons, text="🎯 Frecuencia", command=self.show_frequency, bg="#1f6feb", fg="#c9d1d9").pack(side="left", padx=2)
        Button(viz_buttons, text="📈 Mel Espectro", command=self.show_3d_spectrogram, bg="#1f6feb", fg="#c9d1d9").pack(side="left", padx=2)

        # Canvas para gráficos
        self.fig = Figure(figsize=(13, 5), dpi=100, facecolor='#161b22')
        self.ax = self.fig.add_subplot(111, facecolor='#0d1117')
        self.ax.tick_params(colors='#8b949e')
        self.ax.spines['bottom'].set_color('#30363d')
        self.ax.spines['left'].set_color('#30363d')

        self.canvas = FigureCanvasTkAgg(self.fig, master=waveform_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def create_effects_panel(self):
        """Panel de controles de efectos"""
        effects_frame = ttk.LabelFrame(self.root, text="⚙️ Controles de Efectos", padding=10)
        effects_frame.pack(fill="x", padx=10, pady=5)

        # Volume
        vol_frame = Frame(effects_frame, bg="#1a0033")
        vol_frame.pack(fill="x", pady=5)
        Label(vol_frame, text="Volumen:", bg="#1a0033", fg="#00aaff", font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        self.volume_slider = Scale(vol_frame, from_=-30, to=10, orient="horizontal",
                                   bg="#2d0055", fg="#00aaff", troughcolor="#0b0c10",
                                   command=self.update_volume, highlightthickness=0)
        self.volume_slider.set(0)
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.volume_label = Label(vol_frame, text="0 dB", bg="#1a0033", fg="#ffcc00", font=('Arial', 10, 'bold'), width=8)
        self.volume_label.pack(side="left", padx=5)

        # Pitch
        pitch_frame = Frame(effects_frame, bg="#1a0033")
        pitch_frame.pack(fill="x", pady=5)
        Label(pitch_frame, text="Pitch:", bg="#1a0033", fg="#00aaff", font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        self.pitch_slider = Scale(pitch_frame, from_=-12, to=12, orient="horizontal",
                                  bg="#2d0055", fg="#00aaff", troughcolor="#0b0c10",
                                  command=self.update_pitch_label, highlightthickness=0)
        self.pitch_slider.set(0)
        self.pitch_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.pitch_label = Label(pitch_frame, text="0 st", bg="#1a0033", fg="#ffcc00", font=('Arial', 10, 'bold'), width=8)
        self.pitch_label.pack(side="left", padx=5)

        # Speed
        speed_frame = Frame(effects_frame, bg="#1a0033")
        speed_frame.pack(fill="x", pady=5)
        Label(speed_frame, text="Velocidad:", bg="#1a0033", fg="#00aaff", font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        self.speed_slider = Scale(speed_frame, from_=0.5, to=2.0, resolution=0.1, orient="horizontal",
                                  bg="#2d0055", fg="#00aaff", troughcolor="#0b0c10",
                                  command=self.update_speed_label, highlightthickness=0)
        self.speed_slider.set(1.0)
        self.speed_slider.pack(side="left", fill="x", expand=True, padx=5)
        self.speed_label = Label(speed_frame, text="1.0x", bg="#1a0033", fg="#ffcc00", font=('Arial', 10, 'bold'), width=8)
        self.speed_label.pack(side="left", padx=5)
        
    def create_playback_controls(self):
        """Controles de reproducción"""
        playback_frame = ttk.Frame(self.root)
        playback_frame.pack(fill="x", padx=10, pady=5)

        Button(playback_frame, text="▶️ Play", command=self.play_audio, bg="#00ff00", fg="#0b0c10", font=('Arial', 9, 'bold'), width=10).pack(side="left", padx=2)
        Button(playback_frame, text="⏸️ Pause", command=self.pause_audio, bg="#ffff00", fg="#0b0c10", font=('Arial', 9, 'bold'), width=10).pack(side="left", padx=2)
        Button(playback_frame, text="⏹️ Stop", command=self.stop_audio, bg="#ff1493", fg="#f5f5f5", font=('Arial', 9, 'bold'), width=10).pack(side="left", padx=2)

        Label(playback_frame, text="Tiempo:", bg="#0b0c10", fg="#00aaff", font=('Arial', 10, 'bold')).pack(side="left", padx=5)
        self.time_label = Label(playback_frame, text="00:00 / 00:00", bg="#0b0c10", fg="#ffcc00",
                               font=("Arial", 12, "bold"), width=20)
        self.time_label.pack(side="left", padx=5)

        # Timeline slider
        self.timeline_slider = Scale(playback_frame, from_=0, to=100, orient="horizontal",
                                    bg="#2d0055", fg="#00aaff", troughcolor="#0b0c10",
                                    command=self.seek_audio, highlightthickness=0)
        self.timeline_slider.pack(side="left", fill="x", expand=True, padx=5)
        
    def create_status_bar(self):
        """Barra de estado con información del audio"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = Label(status_frame, text="Listo | Cargue un archivo de audio",
                                 bg="#0b0c10", fg="#00aaff", justify="left", wraplength=1300, font=('Arial', 9))
        self.status_label.pack(fill="x")
        
    def update_status(self, message):
        """Actualizar estado"""
        self.status_label.config(text=message)
        self.root.update()
        
    def update_volume(self, value):
        """Actualizar etiqueta de volumen"""
        self.volume_label.config(text=f"{value} dB", fg="#ffcc00")
        
    def update_pitch_label(self, value):
        """Actualizar etiqueta de pitch"""
        self.pitch_label.config(text=f"{value} st", fg="#ffcc00")
        
    def update_speed_label(self, value):
        """Actualizar etiqueta de velocidad"""
        self.speed_label.config(text=f"{float(value):.1f}x", fg="#ffcc00")
        
    def open_file(self):
        """Abrir archivo"""
        path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.flac *.ogg"), ("All", "*.*")]
        )
        if path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, path)
            
    def load_audio(self):
        """Cargar audio"""
        path = self.file_entry.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Error", "Seleccione un archivo válido")
            return
            
        try:
            self.update_status(f"Cargando {os.path.basename(path)}...")
            self.audio, self.sr = librosa.load(path, sr=None)
            self.original_audio = self.audio.copy()
            self.file_path = path
            self.history = [self.audio.copy()]
            self.history_index = 0
            self.current_position = 0
            
            duration = len(self.audio) / self.sr
            info = f"✓ {os.path.basename(path)} | {duration:.1f}s | {self.sr}Hz | {len(self.audio)} muestras"
            self.update_status(info)
            self.show_waveform()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar: {str(e)}")
            
    def clear_audio(self):
        """Limpiar audio"""
        self.audio = None
        self.original_audio = None
        self.file_entry.delete(0, "end")
        self.ax.clear()
        self.canvas.draw()
        self.update_status("Audio limpiado")
        
    def save_file(self):
        """Guardar archivo"""
        if self.audio is None:
            messagebox.showerror("Error", "No hay audio para guardar")
            return
            
        if self.file_path:
            try:
                sf.write(self.file_path, self.audio, self.sr)
                messagebox.showinfo("Éxito", f"Guardado en {self.file_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            self.save_as()
            
    def save_as(self):
        """Guardar como"""
        if self.audio is None:
            messagebox.showerror("Error", "No hay audio para guardar")
            return
            
        path = filedialog.asksaveasfilename(defaultextension=".wav",
                                           filetypes=[("WAV", "*.wav"), ("All", "*.*")])
        if path:
            try:
                sf.write(path, self.audio, self.sr)
                self.file_path = path
                messagebox.showinfo("Éxito", f"Guardado en {path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                
    def show_waveform(self):
        """Mostrar forma de onda"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        self.ax.clear()
        time = np.arange(len(self.audio)) / self.sr
        self.ax.plot(time, self.audio, color='#00aaff', linewidth=0.5)
        self.ax.set_xlabel('Tiempo (s)', color='#00aaff')
        self.ax.set_ylabel('Amplitud', color='#00aaff')
        self.ax.set_title('Forma de Onda', color='#ffcc00', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.1, color='#b400ff')
        self.fig.tight_layout()
        self.canvas.draw()
        
    def show_spectrogram(self):
        """Mostrar espectrograma"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        self.ax.clear()
        D = librosa.stft(self.audio)
        S_db = librosa.power_to_db(np.abs(D)**2, ref=np.max)
        img = self.ax.imshow(S_db, aspect='auto', origin='lower', cmap='twilight_shifted', 
                            extent=[0, len(self.audio)/self.sr, 0, self.sr/2])
        self.ax.set_xlabel('Tiempo (s)', color='#8b949e')
        self.ax.set_ylabel('Frecuencia (Hz)', color='#8b949e')
        self.ax.set_title('Espectrograma', color='#c9d1d9', fontsize=14, fontweight='bold')
        self.fig.colorbar(img, ax=self.ax, label='dB')
        self.fig.colorbar(img, ax=self.ax, label='dB')
        self.fig.tight_layout()
        self.canvas.draw()
        
    def show_frequency(self):
        """Mostrar espectro de frecuencia"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        self.ax.clear()
        frequencies = np.abs(fft(self.audio))[:len(self.audio)//2]
        freqs = np.fft.fftfreq(len(self.audio), 1/self.sr)[:len(self.audio)//2]
        self.ax.semilogy(freqs, frequencies, color='#00aaff', linewidth=1)
        self.ax.set_xlabel('Frecuencia (Hz)', color='#00aaff')
        self.ax.set_ylabel('Magnitud', color='#00aaff')
        self.ax.set_title('Espectro de Frecuencia', color='#ffcc00', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.1, color='#b400ff')
        self.fig.tight_layout()
        self.canvas.draw()
        
    def show_3d_spectrogram(self):
        """Mostrar mel-espectrograma"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        self.ax.clear()
        mel_spec = librosa.feature.melspectrogram(y=self.audio, sr=self.sr, n_mels=128)
        mel_db = librosa.power_to_db(mel_spec, ref=np.max)
        img = self.ax.imshow(mel_db, aspect='auto', origin='lower', cmap='twilight',
                            extent=[0, len(self.audio)/self.sr, 0, 128])
        self.ax.set_xlabel('Tiempo (s)', color='#00aaff')
        self.ax.set_ylabel('Mel Bin', color='#00aaff')
        self.ax.set_title('Mel-Espectrograma', color='#ffcc00', fontsize=14, fontweight='bold')
        self.fig.colorbar(img, ax=self.ax, label='dB')
        self.fig.tight_layout()
        self.canvas.draw()
        self.fig.colorbar(img, ax=self.ax, label='dB')
        self.fig.tight_layout()
        self.canvas.draw()
        
    def play_audio(self):
        """Reproducir audio"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        if not self.playing:
            self.playing = True
            self.play_thread = threading.Thread(target=self._play_thread, daemon=True)
            self.play_thread.start()
            
    def _play_thread(self):
        """Hilo de reproducción"""
        try:
            start = int(self.current_position * len(self.audio) / 100)
            audio_slice = self.audio[start:]
            volume_db = float(self.volume_slider.get())
            volume_linear = 10 ** (volume_db / 20)
            audio_slice = audio_slice * volume_linear
            sd.play(audio_slice, self.sr)
            sd.wait()
            self.playing = False
        except Exception as e:
            messagebox.showerror("Error", f"Reproducción: {str(e)}")
            self.playing = False
            
    def pause_audio(self):
        """Pausar"""
        self.playing = False
        sd.stop()
        
    def stop_audio(self):
        """Detener"""
        self.playing = False
        self.current_position = 0
        self.timeline_slider.set(0)
        sd.stop()
        
    def toggle_playback(self):
        """Espacio para play/pause"""
        if self.playing:
            self.pause_audio()
        else:
            self.play_audio()
            
    def seek_audio(self, value):
        """Mover en la línea de tiempo"""
        self.current_position = float(value)
        if self.audio is not None:
            duration = len(self.audio) / self.sr
            current_time = float(value) / 100 * duration
            total_time_str = f"{int(duration//60):02d}:{int(duration%60):02d}"
            current_time_str = f"{int(current_time//60):02d}:{int(current_time%60):02d}"
            self.time_label.config(text=f"{current_time_str} / {total_time_str}")
            
    def normalize_audio(self):
        """Normalizar audio"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        self._save_history()
        max_val = np.max(np.abs(self.audio))
        if max_val > 0:
            self.audio = self.audio / max_val
        self.update_status("✓ Audio normalizado")
        self.show_waveform()
        
    def amplify(self, db):
        """Amplificar"""
        if self.audio is None:
            return
            
        self._save_history()
        linear = 10 ** (db / 20)
        self.audio = self.audio * linear
        self.audio = np.clip(self.audio, -1, 1)
        self.update_status(f"✓ Amplificado {db:+.1f} dB")
        self.show_waveform()
        
    def apply_reverb(self):
        """Aplicar reverb"""
        if self.audio is None:
            return
            
        self._save_history()
        decay = 0.5
        delay_samples = int(0.05 * self.sr)
        reverb = np.zeros_like(self.audio)
        
        for i in range(10):
            delayed = np.zeros_like(self.audio)
            offset = delay_samples * (i + 1)
            if offset < len(self.audio):
                delayed[offset:] = self.audio[:-offset] * (decay ** (i + 1))
                reverb += delayed
        
        self.audio = np.clip(self.audio + reverb * 0.3, -1, 1)
        self.update_status("✓ Reverb aplicado")
        self.show_waveform()
        
    def apply_echo(self):
        """Aplicar echo"""
        if self.audio is None:
            return
            
        self._save_history()
        delay = int(0.5 * self.sr)
        echo = np.zeros_like(self.audio)
        echo[delay:] = self.audio[:-delay] * 0.6
        self.audio = np.clip(self.audio + echo, -1, 1)
        self.update_status("✓ Echo aplicado")
        self.show_waveform()
        
    def fade_in(self):
        """Fade in"""
        if self.audio is None:
            return
            
        self._save_history()
        duration = int(2 * self.sr)
        fade = np.linspace(0, 1, min(duration, len(self.audio)))
        self.audio[:len(fade)] *= fade
        self.update_status("✓ Fade In aplicado")
        self.show_waveform()
        
    def fade_out(self):
        """Fade out"""
        if self.audio is None:
            return
            
        self._save_history()
        duration = int(2 * self.sr)
        fade = np.linspace(1, 0, min(duration, len(self.audio)))
        self.audio[-len(fade):] *= fade
        self.update_status("✓ Fade Out aplicado")
        self.show_waveform()
        
    def apply_compression(self):
        """Compresión dinámica"""
        if self.audio is None:
            return
            
        self._save_history()
        threshold = 0.5
        ratio = 4
        compressed = self.audio.copy()
        mask = np.abs(self.audio) > threshold
        compressed[mask] = (np.sign(self.audio[mask]) * 
                           (np.abs(self.audio[mask]) - threshold) / ratio + threshold)
        self.audio = compressed
        self.update_status("✓ Compresión aplicada")
        self.show_waveform()
        
    def trim_silence(self):
        """Deletrear silencio"""
        if self.audio is None:
            return
            
        self._save_history()
        threshold = np.max(np.abs(self.audio)) * 0.02
        mask = np.abs(self.audio) > threshold
        
        if np.any(mask):
            start = np.where(mask)[0][0]
            end = np.where(mask)[0][-1] + 1
            self.audio = self.audio[start:end]
        
        self.update_status("✓ Silencio deletreado")
        self.show_waveform()
        
    def detect_bpm(self):
        """Detectar BPM"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        try:
            onset_env = librosa.onset.onset_strength(y=self.audio, sr=self.sr)
            bpm_value = librosa.feature.tempo(onset_envelope=onset_env, sr=self.sr)[0]
            messagebox.showinfo("BPM", f"BPM detectado: ~{bpm_value:.0f}")
        except:
            messagebox.showinfo("BPM", "No se pudo detectar BPM con precisión")
            
    def detect_key(self):
        """Detectar tonalidad"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
            
        try:
            chroma = librosa.feature.chroma_cqt(y=self.audio, sr=self.sr)
            key_strength = np.mean(chroma, axis=1)
            key_index = np.argmax(key_strength)
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            messagebox.showinfo("Tonalidad", f"Tonalidad probable: {keys[key_index]}")
        except:
            messagebox.showinfo("Tonalidad", "No se pudo detectar tonalidad")
            
    def extract_features(self):
        """Extraer características"""
        if self.audio is None:
            return
            
        try:
            rms = librosa.feature.rms(y=self.audio)[0]
            zcr = librosa.feature.zero_crossing_rate(self.audio)[0]
            info = f"""
Características de Audio:
━━━━━━━━━━━━━━━━━━━
RMS Promedio: {np.mean(rms):.3f}
RMS Máximo: {np.max(rms):.3f}
ZCR Promedio: {np.mean(zcr):.3f}
Duración: {len(self.audio)/self.sr:.2f}s
            """
            messagebox.showinfo("Características", info)
        except:
            messagebox.showerror("Error", "No se pudieron extraer características")
            
    def identify_instruments(self):
        """Identificar instrumentos"""
        if self.audio is None:
            return
            
        try:
            mel_spec = librosa.feature.melspectrogram(y=self.audio, sr=self.sr, n_mels=128)
            mel_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            low_freq = np.mean(mel_db[:32, :])
            mid_freq = np.mean(mel_db[32:96, :])
            high_freq = np.mean(mel_db[96:, :])
            
            instruments = []
            if low_freq > mid_freq and low_freq > high_freq:
                instruments.append("🥁 Bajos / Batería")
            if mid_freq > low_freq and mid_freq > high_freq - 5:
                instruments.append("🎸 Guitarra / Voces")
            if high_freq > low_freq and high_freq > mid_freq:
                instruments.append("📯 Altos / Instrumentos agudos")
            
            if instruments:
                messagebox.showinfo("Instrumentos", "Posibles instrumentos:\n\n" + "\n".join(instruments))
            else:
                messagebox.showinfo("Instrumentos", "No se detectaron patrones claros")
        except:
            messagebox.showerror("Error", "No se pudieron identificar instrumentos")
    
    def separate_stems(self):
        """Separar audio en 4 stems: voces, bajos, batería, otros"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
        
        self.update_status("⏳ Separando stems... (esto puede tomar un tiempo)")
        self.root.update()
        
        try:
            # Convertir mono a estéreo si es necesario
            if len(self.audio.shape) == 1:
                audio_stereo = np.vstack([self.audio, self.audio])
            else:
                audio_stereo = self.audio.T
            
            # Aplicar ICA para separación
            n_components = 4
            ica = FastICA(n_components=n_components, random_state=42, max_iter=500)
            
            # Reshapear para ICA
            audio_reshaped = audio_stereo.reshape(audio_stereo.shape[0], -1)
            sources = ica.fit_transform(audio_reshaped.T).T
            
            # Guardar stems separados
            stem_names = ["Voces", "Bajos", "Batería", "Otros"]
            self.stems = {}
            
            for i, name in enumerate(stem_names):
                self.stems[name] = sources[i % len(sources)]
            
            self.update_status(f"✓ Audio separado en {n_components} stems listos para editar")
            self.open_stem_editor()
            
        except Exception as e:
            messagebox.showerror("Error", f"Separación falló: {str(e)}")
            self.update_status("Error en separación")
    
    def open_stem_editor(self):
        """Abre ventana para editar stems individuales"""
        if not hasattr(self, 'stems') or not self.stems:
            messagebox.showerror("Error", "Primero separa los stems")
            return
        
        # Crear ventana nueva
        stem_window = tk.Toplevel(self.root)
        stem_window.title("🎼 Editor de Stems")
        stem_window.geometry("900x600")
        stem_window.configure(bg="#0b0c10")
        
        # Frame para lista de stems
        list_frame = ttk.Frame(stem_window)
        list_frame.pack(side="left", fill="both", expand=False, padx=10, pady=10)
        
        Label(list_frame, text="Stems Disponibles:", bg="#0b0c10", fg="#00aaff", 
              font=('Arial', 11, 'bold')).pack()
        
        self.stem_listbox = Listbox(list_frame, bg="#1a0033", fg="#00aaff", 
                                    font=('Arial', 10), width=20, height=20)
        self.stem_listbox.pack(fill="both", expand=True, pady=5)
        
        for stem_name in self.stems.keys():
            self.stem_listbox.insert("end", f"🎵 {stem_name}")
        
        self.stem_listbox.bind("<<ListboxSelect>>", lambda e: self.highlight_stem(stem_window))
        
        # Frame para controles
        control_frame = Frame(stem_window, bg="#0b0c10")
        control_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Slider de volumen para stem seleccionado
        Label(control_frame, text="Volumen del Stem:", bg="#0b0c10", fg="#00aaff",
              font=('Arial', 10, 'bold')).pack()
        
        self.stem_volume_var = Scale(control_frame, from_=-30, to=10, orient="horizontal",
                                     bg="#2d0055", fg="#00aaff", troughcolor="#0b0c10",
                                     highlightthickness=0, length=300)
        self.stem_volume_var.set(0)
        self.stem_volume_var.pack(fill="x", pady=5)
        
        # Botones de acción
        Button(control_frame, text="▶️ Reproducir Stem", command=self.play_selected_stem,
               bg="#00ff00", fg="#0b0c10", font=('Arial', 9, 'bold')).pack(fill="x", pady=5)
        
        Button(control_frame, text="🔊 Solo", command=self.solo_stem,
               bg="#b400ff", fg="#f5f5f5", font=('Arial', 9, 'bold')).pack(fill="x", pady=5)
        
        Button(control_frame, text="📊 Visualizar", command=self.show_stem_waveform,
               bg="#00aaff", fg="#0b0c10", font=('Arial', 9, 'bold')).pack(fill="x", pady=5)
        
        Button(control_frame, text="💾 Exportar Stem", command=self.export_single_stem,
               bg="#ffcc00", fg="#0b0c10", font=('Arial', 9, 'bold')).pack(fill="x", pady=5)
        
        Button(control_frame, text="🔄 Cerrar", command=stem_window.destroy,
               bg="#ff1493", fg="#f5f5f5", font=('Arial', 9, 'bold')).pack(fill="x", pady=5)
        
        self.stem_window = stem_window
    
    def highlight_stem(self, window):
        """Resaltar stem seleccionado"""
        selection = self.stem_listbox.curselection()
        if selection:
            self.current_stem_index = selection[0]
    
    def play_selected_stem(self):
        """Reproducir stem seleccionado"""
        if not hasattr(self, 'current_stem_index'):
            messagebox.showwarning("Error", "Selecciona un stem primero")
            return
        
        stem_names = list(self.stems.keys())
        stem_name = stem_names[self.current_stem_index]
        stem_audio = self.stems[stem_name]
        
        volume_db = float(self.stem_volume_var.get())
        volume_linear = 10 ** (volume_db / 20)
        stem_audio = (stem_audio * volume_linear).astype(np.float32)
        
        try:
            sd.play(stem_audio, self.sr)
        except:
            messagebox.showerror("Error", "No se pudo reproducir")
    
    def solo_stem(self):
        """Reproducir solo un stem"""
        if not hasattr(self, 'current_stem_index'):
            messagebox.showwarning("Error", "Selecciona un stem primero")
            return
        
        stem_names = list(self.stems.keys())
        stem_name = stem_names[self.current_stem_index]
        self.audio = self.stems[stem_name]
        self.update_status(f"✓ Solo: {stem_name} cargado en editor principal")
        self.show_waveform()
    
    def show_stem_waveform(self):
        """Mostrar waveform del stem seleccionado"""
        if not hasattr(self, 'current_stem_index'):
            messagebox.showwarning("Error", "Selecciona un stem primero")
            return
        
        stem_names = list(self.stems.keys())
        stem_name = stem_names[self.current_stem_index]
        stem_audio = self.stems[stem_name]
        
        self.ax.clear()
        time_axis = np.linspace(0, len(stem_audio) / self.sr, len(stem_audio))
        self.ax.plot(time_axis, stem_audio, color='#00aaff', linewidth=0.5)
        self.ax.fill_between(time_axis, stem_audio, alpha=0.3, color='#b400ff')
        self.ax.set_xlabel('Tiempo (s)', color='#00aaff')
        self.ax.set_ylabel('Amplitud', color='#00aaff')
        self.ax.set_title(f'Waveform: {stem_name}', color='#ffcc00', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.1, color='#00aaff')
        self.ax.set_facecolor('#0d1117')
        self.fig.patch.set_facecolor('#161b22')
        self.fig.tight_layout()
        self.canvas.draw()
    
    def export_single_stem(self):
        """Exportar stem seleccionado"""
        if not hasattr(self, 'current_stem_index'):
            messagebox.showwarning("Error", "Selecciona un stem primero")
            return
        
        stem_names = list(self.stems.keys())
        stem_name = stem_names[self.current_stem_index]
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV", "*.wav"), ("MP3", "*.mp3"), ("FLAC", "*.flac"), ("All", "*.*")]
        )
        
        if filepath:
            try:
                stem_audio = self.stems[stem_name]
                sf.write(filepath, stem_audio, self.sr)
                messagebox.showinfo("Success", f"Stem '{stem_name}' exportado a:\n{filepath}")
                self.update_status(f"✓ Stem exportado: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
    
    def export_stems(self):
        """Exportar todos los stems"""
        if not hasattr(self, 'stems') or not self.stems:
            messagebox.showerror("Error", "Primero separa los stems")
            return
        
        folder = filedialog.askdirectory(title="Selecciona carpeta para exportar stems")
        if folder:
            try:
                for stem_name, stem_audio in self.stems.items():
                    filepath = os.path.join(folder, f"{stem_name}_stem.wav")
                    sf.write(filepath, stem_audio, self.sr)
                
                messagebox.showinfo("Éxito", f"✓ Todos los stems exportados a:\n{folder}")
                self.update_status(f"✓ {len(self.stems)} stems exportados")
            except Exception as e:
                messagebox.showerror("Error", f"Exportación falló: {str(e)}")
    
    def export_audio(self, format_type):
        """Exportar audio a diversos formatos"""
        if self.audio is None:
            messagebox.showerror("Error", "Cargue audio primero")
            return
        
        format_extensions = {
            "wav": ("WAV files", "*.wav"),
            "mp3": ("MP3 files", "*.mp3"),
            "flac": ("FLAC files", "*.flac"),
            "ogg": ("OGG files", "*.ogg"),
            "m4a": ("M4A files", "*.m4a")
        }
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            filetypes=[format_extensions.get(format_type, ("Audio", f"*.{format_type}")), ("All", "*.*")]
        )
        
        if filepath:
            try:
                self.update_status(f"💾 Exportando a {format_type.upper()}...")
                self.root.update()
                
                # Normalizar audio antes de exportar
                audio = self.audio.astype(np.float32)
                max_val = np.max(np.abs(audio))
                if max_val > 1:
                    audio = audio / max_val
                
                # Exportar según formato
                if format_type == "wav":
                    sf.write(filepath, audio, self.sr, subtype='PCM_16')
                elif format_type == "mp3":
                    # Convertir a wav temporal, luego a mp3 con pydub
                    temp_wav = filepath.replace(".mp3", "_temp.wav")
                    sf.write(temp_wav, audio, self.sr)
                    audio_segment = AudioSegment.from_wav(temp_wav)
                    audio_segment.export(filepath, format="mp3", bitrate="320k")
                    os.remove(temp_wav)
                elif format_type == "flac":
                    sf.write(filepath, audio, self.sr, subtype='PCM_16')
                    os.rename(filepath.replace(".flac", ".wav"), filepath)
                    sf.write(filepath, audio, self.sr)
                elif format_type in ["ogg", "m4a"]:
                    temp_wav = filepath.replace(f".{format_type}", "_temp.wav")
                    sf.write(temp_wav, audio, self.sr)
                    audio_segment = AudioSegment.from_wav(temp_wav)
                    audio_segment.export(filepath, format=format_type)
                    os.remove(temp_wav)
                
                messagebox.showinfo("Éxito", f"✓ Audio exportado a {format_type.upper()}")
                self.update_status(f"✓ Exportado: {os.path.basename(filepath)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")
                self.update_status("Error en exportación")
    
    def _save_history(self):
        """Guardar en historial"""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(self.audio.copy())
        self.history_index += 1
        
    def undo(self):
        """Deshacer"""
        if self.history_index > 0:
            self.history_index -= 1
            self.audio = self.history[self.history_index].copy()
            self.show_waveform()
            self.update_status("✓ Deshacer")
            
    def redo(self):
        """Rehacer"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.audio = self.history[self.history_index].copy()
            self.show_waveform()
            self.update_status("✓ Rehacer")
            
    def run(self):
        """Ejecutar aplicación"""
        self.root.mainloop()


if __name__ == "__main__":
    app = AudioEditorPro()
    app.run()
