import librosa
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, Label, Button, messagebox
import os

class InstrumentIdentifier:
    def __init__(self):
        self.root = Tk()
        self.root.title("Instrument Identifier")
        self.root.geometry("500x400")
        
        self.label = Label(self.root, text="Select a track:", wraplength=450, justify="left")
        self.label.pack(pady=10)
        
        self.button = Button(self.root, text="Analyze song.mp3", command=self.analyze)
        self.button.pack(pady=10)
        
        self.result_label = Label(self.root, text="", wraplength=450, justify="left", fg="blue")
        self.result_label.pack(pady=10, fill="both", expand=True)

    def analyze(self):
        try:
            # Verifica que el archivo existe
            if not os.path.exists('song.mp3'):
                messagebox.showerror("Error", "song.mp3 no encontrado en la carpeta actual")
                return
            
            self.label.config(text="Cargando audio...")
            self.root.update()
            
            # Carga la canción
            audio, sr = librosa.load('song.mp3')
            
            # Analiza el espectrograma Mel (retorna UN array, no dos)
            mel_spectrogram = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128)
            mel_spec_db = librosa.power_to_db(mel_spectrogram, ref=np.max)
            
            # Calcula estadísticas globales
            mean_energy = np.mean(mel_spec_db, axis=0)
            max_energy = np.max(mel_spec_db)
            
            # Detecta instrumentos basado en características de frecuencia
            instruments = {}
            
            # Voz: picos en frecuencias medias (rango 1-4 kHz)
            mid_freq = np.mean(mel_spec_db[40:80, :], axis=0)
            if np.mean(mid_freq) > np.percentile(mean_energy, 60):
                instruments['voz'] = f"✓ Detectada (energía: {np.mean(mid_freq):.1f} dB)"
            
            # Guitarra: energía en bajos (100-500 Hz)
            low_freq = np.mean(mel_spec_db[0:40, :], axis=0)
            if np.mean(low_freq) > np.percentile(mean_energy, 50):
                instruments['guitarra'] = f"✓ Detectada (energía: {np.mean(low_freq):.1f} dB)"
            
            # Batería: picos puntuales de alta energía
            high_energy_frames = np.where(mean_energy > np.percentile(mean_energy, 85))[0]
            if len(high_energy_frames) > 10:
                instruments['batería'] = f"✓ Detectada ({len(high_energy_frames)} picos)"
            
            # Piano: energía uniforme en todo el rango
            if np.std(mean_energy) < np.mean(mean_energy) * 0.3:
                instruments['piano'] = "✓ Detectada (sonido uniforme)"
            
            # Muestra resultados
            self.label.config(text="✓ Análisis completado")
            
            if instruments:
                result_text = "INSTRUMENTOS IDENTIFICADOS:\n\n" + "\n".join(
                    [f"  {inst.upper()}: {info}" for inst, info in instruments.items()]
                )
            else:
                result_text = "No se detectaron instrumentos claros.\nIntenta con otro archivo."
            
            self.result_label.config(text=result_text)
            
            # Muestra el espectrograma
            self._plot_spectrogram(mel_spec_db, sr)
            
        except Exception as e:
            messagebox.showerror("Error", f"Análisis fallido: {str(e)}")
            self.label.config(text="❌ Error durante el análisis")

    def _plot_spectrogram(self, mel_spec_db, sr):
        """Muestra el espectrograma de audio"""
        fig, ax = plt.subplots(figsize=(12, 5))
        
        # Dibuja el espectrograma
        im = ax.imshow(mel_spec_db, origin='lower', aspect='auto', cmap='magma', interpolation='bilinear')
        
        ax.set_title('Espectrograma Mel de Audio', fontsize=14, fontweight='bold')
        ax.set_xlabel('Frames de Tiempo')
        ax.set_ylabel('Banda de Frecuencia Mel')
        
        # Colorbar con escala
        cbar = plt.colorbar(im, ax=ax, label='Potencia (dB)')
        
        plt.tight_layout()
        plt.show()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = InstrumentIdentifier()
    app.run()
