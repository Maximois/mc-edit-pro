"""
🎵 MC Editor Pro - Backend Flask para Interfaz Web
Conecta la interfaz web con funcionalidades de audio
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import librosa
import numpy as np
import soundfile as sf
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from io import BytesIO
from pydub import AudioSegment
from werkzeug.utils import secure_filename
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Configuración
UPLOAD_FOLDER = tempfile.gettempdir()
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Variables globales para cache
audio_cache = {}
stems_cache = {}

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UVR_DIR = os.path.join(PROJECT_DIR, 'mc-editor-pro', 'musia', 'ultimatevocalremover_gui')
UVR_MODEL_DIR = os.path.join(UVR_DIR, 'models')
UVR_MODEL_FILENAME = 'UVR-MDX-NET-Inst_full_292.onnx'
UVR_EXECUTABLE = os.path.join(UVR_DIR, 'uvr_env', 'Scripts', 'audio-separator.exe')
UVR_DEVICE_CACHE = None
SEPARATION_MODELS = {
    'mdx': {
        'name': 'UVR5 MDX-Net · Inst full 292',
        'filename': UVR_MODEL_FILENAME,
        'stems': {'vocals', 'instrumental'},
        'architecture': 'mdx',
    },
    'demucs': {
        'name': 'Demucs v4 · 4 stems',
        'filename': 'htdemucs.yaml',
        'stems': {'vocals', 'bass', 'drums', 'other'},
        'architecture': 'demucs',
    },
    'd6': {
        'name': 'Demucs v4 · 6 stems',
        'filename': 'htdemucs_6s.yaml',
        'stems': {'vocals', 'bass', 'drums', 'other', 'guitar', 'piano'},
        'architecture': 'demucs',
    },
}
STEM_NAMES = {
    'vocals': 'Vocals',
    'instrumental': 'Instrumental',
    'bass': 'Bass',
    'drums': 'Drums',
    'other': 'Other',
    'guitar': 'Guitar',
    'piano': 'Piano',
}


def _waveform_peaks(audio, point_count=1000):
    """Return a compact real waveform envelope for display."""
    audio = np.asarray(audio).reshape(-1)
    if audio.size == 0:
        return []

    edges = np.linspace(0, audio.size, point_count + 1, dtype=int)
    return [
        float(np.max(np.abs(audio[edges[i]:edges[i + 1]])))
        if edges[i] < edges[i + 1] else 0.0
        for i in range(point_count)
    ]


def _remove_output_dir(output_dir):
    try:
        shutil.rmtree(output_dir)
    except FileNotFoundError:
        pass
    except OSError as error:
        app.logger.warning('Could not remove temporary UVR output %s: %s', output_dir, error)


def _uvr_execution_device():
    global UVR_DEVICE_CACHE
    if UVR_DEVICE_CACHE:
        return UVR_DEVICE_CACHE

    try:
        result = subprocess.run(
            [UVR_EXECUTABLE, '--env_info'],
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        app.logger.warning('Could not query the UVR5 execution device: %s', error)
        return None

    if result.returncode != 0:
        app.logger.warning('UVR5 device query failed: %s', (result.stderr or '')[-1000:])
        return None

    logs = (result.stdout or '') + (result.stderr or '')
    lowered = logs.lower()
    if 'running in cpu mode' in lowered:
        UVR_DEVICE_CACHE = 'CPU'
    elif 'cudaexecutionprovider available, enabling acceleration' in lowered:
        UVR_DEVICE_CACHE = 'CUDA'
    elif 'dmlexecutionprovider available, enabling acceleration' in lowered:
        UVR_DEVICE_CACHE = 'DirectML'
    elif 'coremlexecutionprovider available, enabling acceleration' in lowered:
        UVR_DEVICE_CACHE = 'CoreML'
    return UVR_DEVICE_CACHE


# ===== HEALTH CHECK =====
@app.route('/')
def health():
    return jsonify({'status': 'ok', 'message': '🎵 MC Editor Pro Backend Online'}), 200

@app.route('/api/health')
def api_health():
    model_availability = {
        model_id: os.path.isfile(os.path.join(UVR_MODEL_DIR, config['filename']))
        for model_id, config in SEPARATION_MODELS.items()
    }
    return jsonify({
        'status': 'ok',
        'version': '1.0',
        'features': ['audio-upload', 'uvr5-separation', 'demucs-4-stem', 'demucs-6-stem', 'stem-download'],
        'uvr5_available': os.path.isfile(UVR_EXECUTABLE) and model_availability['mdx'],
        'models_available': model_availability,
    }), 200

# ===== SERVIR ARCHIVOS ESTÁTICOS (PARA DESKTOP) =====
@app.route('/app')
def serve_app():
    """Servir interfaz principal"""
    try:
        web_dir = os.path.join(os.path.dirname(__file__), 'mc-editor-pro')
        index_path = os.path.join(web_dir, 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"❌ Error: {e}", 500

@app.route('/app/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos CSS, JS, etc"""
    try:
        web_dir = os.path.join(os.path.dirname(__file__), 'mc-editor-pro')
        file_path = os.path.join(web_dir, filename)
        
        # Validar ruta
        if not os.path.exists(file_path) or not os.path.abspath(file_path).startswith(os.path.abspath(web_dir)):
            return "❌ File not found", 404
        
        return send_from_directory(web_dir, filename)
    except Exception as e:
        return f"❌ Error: {e}", 500

# ===== CARGA DE AUDIO =====
@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Store an uploaded audio file for playback and UVR5 processing."""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            return jsonify({'error': 'Invalid audio filename'}), 400

        suffix = os.path.splitext(safe_filename)[1].lower()
        descriptor, filepath = tempfile.mkstemp(
            prefix='mc_editor_upload_',
            suffix=suffix,
            dir=app.config['UPLOAD_FOLDER']
        )
        os.close(descriptor)
        file.save(filepath)
        
        # Cargar con librosa
        audio_channels, sr = librosa.load(filepath, sr=None, mono=False)
        channels = 1 if audio_channels.ndim == 1 else int(audio_channels.shape[0])
        audio = audio_channels if audio_channels.ndim == 1 else np.mean(audio_channels, axis=0)
        
        # Guardar en cache
        audio_id = uuid.uuid4().hex
        audio_cache[audio_id] = {
            'audio': audio,
            'sr': sr,
            'filepath': filepath,
            'filename': safe_filename
        }
        
        return jsonify({
            'status': 'ok',
            'audio_id': audio_id,
            'duration': float(audio.shape[0] / sr),
            'sample_rate': int(sr),
            'channels': channels,
            'filename': safe_filename,
            'waveform': _waveform_peaks(audio)
        }), 200
        
    except Exception as e:
        if 'filepath' in locals() and os.path.isfile(filepath):
            try:
                os.remove(filepath)
            except OSError as cleanup_error:
                app.logger.warning('Could not remove failed audio upload %s: %s', filepath, cleanup_error)
        app.logger.exception('Audio upload failed')
        return jsonify({'error': str(e)}), 500

@app.route('/api/separate-stems', methods=['POST'])
def separate_stems():
    """Separate uploaded audio with a locally installed UVR5 or Demucs model."""
    output_dir = None
    try:
        start = time.perf_counter()
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({'error': 'The request body must be a JSON object.'}), 400
        audio_id = data.get('audio_id')
        
        if not isinstance(audio_id, str) or not audio_id:
            return jsonify({'error': 'Missing audio_id in request'}), 400
        
        audio_info = audio_cache.get(audio_id)
        if not audio_info:
            return jsonify({'error': 'Audio not found. Upload it again before processing.'}), 404

        model_id = data.get('model', 'mdx')
        if not isinstance(model_id, str):
            return jsonify({'error': 'Model id must be a string.'}), 400
        model_config = SEPARATION_MODELS.get(model_id)
        if model_config is None:
            return jsonify({'error': 'Unknown separation model.'}), 400

        if not os.path.isfile(UVR_EXECUTABLE):
            return jsonify({'error': 'The audio-separator runtime is missing. Check the bundled uvr_env installation.'}), 503
        model_path = os.path.join(UVR_MODEL_DIR, model_config['filename'])
        if not os.path.isfile(model_path):
            return jsonify({'error': f'Model file is missing: {model_config["filename"]}'}), 503

        params = data.get('params', {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return jsonify({'error': 'Model parameters must be a JSON object.'}), 400

        mdx_params = None
        if model_config['architecture'] == 'mdx':
            try:
                segment_size = int(params.get('seg', 256))
                overlap_percent = int(params.get('ovl', 25))
                batch_size = int(params.get('batch', 1))
            except (TypeError, ValueError):
                return jsonify({'error': 'Invalid UVR5 parameter values.'}), 400

            if not 32 <= segment_size <= 512:
                return jsonify({'error': 'Segment size must be between 32 and 512.'}), 400
            if not 1 <= overlap_percent <= 99:
                return jsonify({'error': 'Overlap must be between 1% and 99%.'}), 400
            if not 1 <= batch_size <= 4:
                return jsonify({'error': 'Batch size must be between 1 and 4 for this CPU-oriented setup.'}), 400
            mdx_params = (segment_size, overlap_percent, batch_size)

        stems_id = uuid.uuid4().hex
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'mc_editor_stems_{stems_id}')
        os.makedirs(output_dir, exist_ok=False)
        command = [
            UVR_EXECUTABLE,
            audio_info['filepath'],
            '--model_filename', model_config['filename'],
            '--model_file_dir', UVR_MODEL_DIR,
            '--output_dir', output_dir,
            '--output_format', 'WAV',
            '--log_level', 'INFO',
        ]
        if mdx_params:
            segment_size, overlap_percent, batch_size = mdx_params
            command.extend([
                '--mdx_segment_size', str(segment_size),
                '--mdx_overlap', str(overlap_percent / 100),
                '--mdx_batch_size', str(batch_size),
            ])
        else:
            command.extend(['--demucs_shifts', '1'])

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=4 * 60 * 60,
                check=False
            )
        except subprocess.TimeoutExpired:
            _remove_output_dir(output_dir)
            return jsonify({'error': 'Audio separation exceeded the four-hour time limit.'}), 504
        except OSError as error:
            _remove_output_dir(output_dir)
            app.logger.exception('Could not start audio-separator')
            return jsonify({'error': f'Could not start audio-separator: {error}'}), 503

        logs = '\n'.join(part for part in (result.stdout, result.stderr) if part)
        if result.returncode != 0:
            _remove_output_dir(output_dir)
            app.logger.error('%s failed (exit %s): %s', model_config['name'], result.returncode, logs[-4000:])
            return jsonify({
                'error': f'{model_config["name"]} separation failed.',
                'details': logs[-2000:] or f'Process exited with code {result.returncode}.'
            }), 500

        output_files = [
            os.path.join(output_dir, filename)
            for filename in os.listdir(output_dir)
            if filename.lower().endswith('.wav')
        ]
        found_stems = {}
        for filepath in output_files:
            filename = os.path.basename(filepath)
            match = re.search(r'\(([^()]+)\)', filename)
            if not match:
                continue
            stem_key = match.group(1).strip().lower()
            stem_name = STEM_NAMES.get(stem_key)
            if not stem_name or stem_key not in model_config['stems']:
                continue
            stem_audio, sample_rate = sf.read(filepath, dtype='float32', always_2d=True)
            found_stems[stem_key] = {
                'key': stem_key,
                'name': stem_name,
                'filename': f'{stem_name}.wav',
                'sample_rate': int(sample_rate),
                'waveform': _waveform_peaks(np.max(np.abs(stem_audio), axis=1)),
                'filepath': filepath,
                'output_dir': output_dir,
            }

        if set(found_stems) != model_config['stems']:
            _remove_output_dir(output_dir)
            app.logger.error('Unexpected UVR5 output files: %s', output_files)
            return jsonify({
                'error': f'{model_config["name"]} did not produce all expected stems.',
                'details': logs[-2000:]
            }), 500

        for stem_key, stem in found_stems.items():
            stems_cache[f'{stems_id}_{stem_key}'] = stem

        execution_device = _uvr_execution_device()
        return jsonify({
            'status': 'ok',
            'stems_id': stems_id,
            'model': model_id,
            'model_name': model_config['name'],
            'execution_device': execution_device,
            'stems': [
                {key: value for key, value in stem.items() if key != 'filepath' and key != 'output_dir'}
                for stem in found_stems.values()
            ],
            'processing_time': round(time.perf_counter() - start, 2)
        }), 200

    except Exception as error:
        if output_dir:
            _remove_output_dir(output_dir)
        app.logger.exception('Unexpected audio separation error')
        return jsonify({'error': f'Audio separation failed: {error}'}), 500

# ===== ANÁLISIS DE AUDIO =====
@app.route('/api/analyze', methods=['POST'])
def analyze_audio():
    """Analizar audio para detectar instrumentos, BPM, etc"""
    try:
        data = request.json
        audio_id = data.get('audio_id')
        
        if audio_id not in audio_cache:
            return jsonify({'error': 'Audio not found'}), 404
        
        audio = audio_cache[audio_id]['audio']
        sr = audio_cache[audio_id]['sr']
        
        # Detectar BPM
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        bpm_value = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)[0]
        
        # Detectar tonalidad
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        key_strength = np.mean(chroma, axis=1)
        key_index = np.argmax(key_strength)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Características
        rms = librosa.feature.rms(y=audio)[0]
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        
        # Detectar instrumentos por rango frecuencia
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128)
        mel_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        low_freq = np.mean(mel_db[:32, :])
        mid_freq = np.mean(mel_db[32:96, :])
        high_freq = np.mean(mel_db[96:, :])
        
        instruments = []
        if low_freq > mid_freq and low_freq > high_freq:
            instruments.append('Bajos/Batería')
        if mid_freq > low_freq and mid_freq > high_freq - 5:
            instruments.append('Guitarra/Voces')
        if high_freq > low_freq and high_freq > mid_freq:
            instruments.append('Altos/Agudos')
        
        return jsonify({
            'status': 'ok',
            'analysis': {
                'bpm': float(bpm_value),
                'key': keys[key_index],
                'instruments': instruments,
                'rms_avg': float(np.mean(rms)),
                'zcr_avg': float(np.mean(zcr))
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== EXPORTACIÓN =====
@app.route('/api/export', methods=['POST'])
def export_audio():
    """Exportar audio a diversos formatos"""
    try:
        data = request.json
        audio_id = data.get('audio_id')
        format_type = data.get('format', 'wav').lower()
        
        if audio_id not in audio_cache:
            return jsonify({'error': 'Audio not found'}), 404
        
        audio = audio_cache[audio_id]['audio']
        sr = audio_cache[audio_id]['sr']
        
        # Normalizar
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        
        # Exportar según formato
        output = BytesIO()
        
        if format_type == 'wav':
            sf.write(output, audio, sr, format='WAV', subtype='PCM_16')
            mime_type = 'audio/wav'
            
        elif format_type == 'mp3':
            temp_wav = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_export.wav')
            sf.write(temp_wav, audio, sr)
            audio_segment = AudioSegment.from_wav(temp_wav)
            audio_segment.export(output, format="mp3", bitrate="320k")
            mime_type = 'audio/mpeg'
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
                
        elif format_type == 'flac':
            sf.write(output, audio, sr, format='FLAC')
            mime_type = 'audio/flac'
            
        elif format_type in ['ogg', 'm4a']:
            temp_wav = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_export.wav')
            sf.write(temp_wav, audio, sr)
            audio_segment = AudioSegment.from_wav(temp_wav)
            audio_segment.export(output, format=format_type)
            mime_type = f'audio/{format_type}'
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        else:
            return jsonify({'error': f'Unsupported format: {format_type}'}), 400
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype=mime_type,
            as_attachment=True,
            download_name=f'audio.{format_type}'
        ), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-stem', methods=['GET', 'POST'])
def export_stem():
    """Download one WAV stem produced by UVR5."""
    try:
        if request.method == 'GET':
            data = request.args
        else:
            data = request.get_json(silent=True) or {}
            if not isinstance(data, dict):
                return jsonify({'error': 'The request body must be a JSON object.'}), 400
        stems_id = data.get('stems_id')
        stem_name = data.get('stem_name')
        if not isinstance(stems_id, str) or not isinstance(stem_name, str):
            return jsonify({'error': 'Missing stems_id or stem_name.'}), 400
        if data.get('format', 'wav').lower() != 'wav':
            return jsonify({'error': 'UVR5 stems are currently available as WAV files only.'}), 400

        stem = stems_cache.get(f'{stems_id}_{stem_name}')
        if not stem or not os.path.isfile(stem['filepath']):
            return jsonify({'error': 'Stem not found'}), 404

        return send_file(
            stem['filepath'],
            mimetype='audio/wav',
            as_attachment=True,
            download_name=stem['filename']
        ), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stem-audio/<stems_id>/<stem_name>')
def stream_stem(stems_id, stem_name):
    stem = stems_cache.get(f'{stems_id}_{stem_name}')
    if not stem or not os.path.isfile(stem['filepath']):
        return jsonify({'error': 'Stem not found'}), 404
    return send_file(stem['filepath'], mimetype='audio/wav', conditional=True)


@app.route('/api/download-stems/<stems_id>')
def download_stems(stems_id):
    stems = [
        stem for cache_key, stem in stems_cache.items()
        if cache_key.startswith(f'{stems_id}_') and os.path.isfile(stem['filepath'])
    ]
    if not stems:
        return jsonify({'error': 'No stems found'}), 404

    archive = BytesIO()
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for stem in stems:
            zip_file.write(stem['filepath'], arcname=stem['filename'])
    archive.seek(0)
    return send_file(
        archive,
        mimetype='application/zip',
        as_attachment=True,
        download_name='MC_Audio_Stems.zip'
    )


@app.route('/api/cleanup-session', methods=['POST'])
def cleanup_session():
    """Remove only the uploaded audio and generated stems named by the caller."""
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': 'The request body must be a JSON object.'}), 400
    audio_id = data.get('audio_id')
    stems_id = data.get('stems_id')
    if audio_id is not None and not isinstance(audio_id, str):
        return jsonify({'error': 'audio_id must be a string.'}), 400
    if stems_id is not None and not isinstance(stems_id, str):
        return jsonify({'error': 'stems_id must be a string.'}), 400
    removed = 0
    files_in_use = False

    if audio_id:
        audio_info = audio_cache.get(audio_id)
        if audio_info:
            filepath = audio_info.get('filepath')
            if filepath and os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                    removed += 1
                except OSError as error:
                    app.logger.warning('Could not remove temporary audio %s: %s', filepath, error)
                    files_in_use = True
            if not files_in_use:
                audio_cache.pop(audio_id, None)

    if stems_id:
        prefix = f'{stems_id}_'
        stems = [
            (cache_key, stem) for cache_key, stem in stems_cache.items()
            if cache_key.startswith(prefix)
        ]
        output_dirs = {stem.get('output_dir') for _, stem in stems if stem.get('output_dir')}
        for cache_key, stem in stems:
            filepath = stem.get('filepath')
            if filepath and os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                    removed += 1
                except OSError as error:
                    app.logger.warning('Could not remove temporary stem %s: %s', filepath, error)
                    files_in_use = True
                    continue
            stems_cache.pop(cache_key, None)
        for output_dir in output_dirs:
            if os.path.isdir(output_dir):
                try:
                    os.rmdir(output_dir)
                except OSError as error:
                    app.logger.warning('Could not remove temporary UVR output %s: %s', output_dir, error)
                    files_in_use = True

    if files_in_use:
        return jsonify({
            'error': 'Some temporary audio files are still in use. Stop playback and retry cleanup.',
            'removed_files': removed
        }), 409

    return jsonify({'status': 'ok', 'removed_files': removed}), 200


# ===== UTILIDADES =====
@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Limpiar cache"""
    try:
        output_dirs = set()
        for audio_info in audio_cache.values():
            filepath = audio_info.get('filepath')
            if filepath and os.path.isfile(filepath):
                os.remove(filepath)
        for stem in stems_cache.values():
            filepath = stem.get('filepath')
            if filepath and os.path.isfile(filepath):
                output_dirs.add(stem.get('output_dir'))
                os.remove(filepath)
        for output_dir in output_dirs:
            if output_dir and os.path.isdir(output_dir):
                os.rmdir(output_dir)
        audio_cache.clear()
        stems_cache.clear()
        return jsonify({'status': 'ok', 'message': 'Cache cleaned'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ERROR HANDLERS =====
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Max 500MB'}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

# ===== MAIN =====
if __name__ == '__main__':
    print("🎵 MC Editor Pro - Backend Server")
    print("=" * 50)
    print("🚀 Iniciando en http://localhost:5000")
    print("📡 CORS habilitado para desarrollo")
    print("=" * 50)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True,
    )
