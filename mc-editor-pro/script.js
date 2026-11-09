// ===== CONFIG =====
function apiBase() {
  const { protocol, hostname, port } = window.location;
  if (hostname === '127.0.0.1' || hostname === 'localhost') {
    const p = port && port !== '' ? port : '5000';
    return `${protocol}//${hostname}:${p}/api`;
  }
  return `${protocol}//${hostname}${port ? `:${port}` : ''}/api`;
}
const API_URL = apiBase();
let audioContext;
let audioBuffer;
let source;
let isPlaying = false;
let currentTime = 0;
let currentViz = 'waveform';

// ===== ELEMENTOS DEL DOM =====
const audioFileInput = document.getElementById('audioFile');
const loadBtn = document.getElementById('loadBtn');
const playBtn = document.getElementById('playBtn');
const pauseBtn = document.getElementById('pauseBtn');
const stopBtn = document.getElementById('stopBtn');
const separateStemsBtn = document.getElementById('separateStemsBtn');
const waveformCanvas = document.getElementById('waveformCanvas');
const waveformCtx = waveformCanvas.getContext('2d');
const statusBox = document.getElementById('statusBox');
const stemsGrid = document.getElementById('stemsGrid');
const volumeSlider = document.getElementById('volumeSlider');
const volumeValue = document.getElementById('volValue');
const timeDisplay = document.getElementById('timeDisplay');
const timeline = document.getElementById('timeline');
const loadingModal = document.getElementById('loadingModal');
const vizBtns = document.querySelectorAll('.viz-btn');
const pitchSlider = document.getElementById('pitchSlider');
const speedSlider = document.getElementById('speedSlider');
const pitchValue = document.getElementById('pitchValue');
const speedValue = document.getElementById('speedValue');

// ===== INICIALIZACIÓN =====
function init() {
  audioContext = new (window.AudioContext || window.webkitAudioContext)();
  
  loadBtn.addEventListener('click', () => {
    if (!audioFileInput.files || !audioFileInput.files[0]) {
      audioFileInput.click();
      return;
    }
    loadAudio();
  });
  audioFileInput.addEventListener('change', () => {
    if (audioFileInput.files && audioFileInput.files[0]) {
      loadAudio();
    }
  });

  playBtn.addEventListener('click', play);
  pauseBtn.addEventListener('click', pause);
  stopBtn.addEventListener('click', stop);
  separateStemsBtn.addEventListener('click', separateStems);
  volumeSlider.addEventListener('input', (e) => {
    volumeValue.textContent = e.target.value;
  });
  if (pitchSlider && pitchValue) {
    pitchSlider.addEventListener('input', (e) => {
      pitchValue.textContent = e.target.value;
    });
  }
  if (speedSlider && speedValue) {
    speedSlider.addEventListener('input', (e) => {
      speedValue.textContent = parseFloat(e.target.value).toFixed(1);
    });
  }
  
  vizBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const t = e.target.closest('.viz-btn');
      if (!t || !t.dataset.viz) return;
      vizBtns.forEach(b => b.classList.remove('active'));
      t.classList.add('active');
      currentViz = t.dataset.viz;
      drawVisualization(currentViz);
    });
  });
  
  timeline.addEventListener('input', (e) => {
    if (audioBuffer) {
      currentTime = (e.target.value / 1000) * audioBuffer.duration;
    }
  });
  
  // Resize canvas
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  
  // Draw inicial
  drawWaveform();
  
  updateStatus('✓ App inicializada | Cargue un archivo de audio');
}

// ===== CANVAS =====
function resizeCanvas() {
  const container = waveformCanvas.parentElement;
  if (!container) return;
  const w = Math.max(240, container.clientWidth - 16);
  const h = Math.max(200, container.clientHeight - 12);
  waveformCanvas.width = w;
  waveformCanvas.height = h;
}

function drawWaveform() {
  waveformCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  
  // Fondo
  waveformCtx.fillStyle = 'rgba(11, 12, 16, 0.8)';
  waveformCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  
  // Línea central
  waveformCtx.strokeStyle = 'rgba(0, 170, 255, 0.2)';
  waveformCtx.beginPath();
  waveformCtx.moveTo(0, waveformCanvas.height / 2);
  waveformCtx.lineTo(waveformCanvas.width, waveformCanvas.height / 2);
  waveformCtx.stroke();
  
  // Onda demo si no hay audio
  if (!audioBuffer) {
    waveformCtx.strokeStyle = '#b400ff';
    waveformCtx.lineWidth = 2;
    waveformCtx.beginPath();
    
    for (let x = 0; x < waveformCanvas.width; x++) {
      const y = waveformCanvas.height / 2 + Math.sin((x + Date.now() / 20) * 0.02) * 40;
      if (x === 0) waveformCtx.moveTo(x, y);
      else waveformCtx.lineTo(x, y);
    }
    
    waveformCtx.stroke();
    
    // Grid
    waveformCtx.strokeStyle = 'rgba(180, 0, 255, 0.1)';
    waveformCtx.lineWidth = 1;
    for (let i = 0; i < 10; i++) {
      waveformCtx.beginPath();
      waveformCtx.moveTo((waveformCanvas.width / 10) * i, 0);
      waveformCtx.lineTo((waveformCanvas.width / 10) * i, waveformCanvas.height);
      waveformCtx.stroke();
    }
  } else if (currentViz === 'waveform') {
    drawRealWaveform();
  } else {
    drawVisualization(currentViz);
  }
  
  requestAnimationFrame(drawWaveform);
}

function drawRealWaveform() {
  const data = audioBuffer.getChannelData(0);
  const step = Math.ceil(data.length / waveformCanvas.width);
  const amp = waveformCanvas.height / 2;
  
  // Gradiente
  const gradient = waveformCtx.createLinearGradient(0, 0, waveformCanvas.width, 0);
  gradient.addColorStop(0, 'rgba(0, 170, 255, 0.5)');
  gradient.addColorStop(0.5, 'rgba(180, 0, 255, 0.7)');
  gradient.addColorStop(1, 'rgba(0, 255, 204, 0.5)');
  
  waveformCtx.strokeStyle = gradient;
  waveformCtx.lineWidth = 2;
  waveformCtx.beginPath();
  
  for (let i = 0; i < waveformCanvas.width; i++) {
    let min = 1.0;
    let max = -1.0;
    
    for (let j = 0; j < step; j++) {
      const datum = data[(i * step) + j];
      if (datum < min) min = datum;
      if (datum > max) max = datum;
    }
    
    const y = (1 + max) * amp;
    if (i === 0) waveformCtx.moveTo(i, y);
    else waveformCtx.lineTo(i, y);
  }
  
  waveformCtx.stroke();
  
  // Rellenar
  waveformCtx.fillStyle = 'rgba(180, 0, 255, 0.1)';
  waveformCtx.lineTo(waveformCanvas.width, waveformCanvas.height / 2);
  waveformCtx.lineTo(0, waveformCanvas.height / 2);
  waveformCtx.fill();
  
  // Indicador de tiempo actual
  if (source && isPlaying) {
    const progress = (audioContext.currentTime / audioBuffer.duration) * waveformCanvas.width;
    waveformCtx.strokeStyle = '#ffcc00';
    waveformCtx.lineWidth = 2;
    waveformCtx.beginPath();
    waveformCtx.moveTo(progress, 0);
    waveformCtx.lineTo(progress, waveformCanvas.height);
    waveformCtx.stroke();
  }
}

function drawVisualization(type) {
  if (!audioBuffer) return;
  
  waveformCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  
  const data = audioBuffer.getChannelData(0);
  const amp = waveformCanvas.height / 2;
  
  switch (type) {
    case 'spectrum':
      drawSpectrum(data, amp);
      break;
    case 'spectrogram':
      drawSpectrogram(data, amp);
      break;
    case 'frequency':
      drawFrequency(data, amp);
      break;
    default:
      drawRealWaveform();
  }
}

function drawSpectrum(data, amp) {
  const fft = simpleFFT(data);
  const barWidth = (waveformCanvas.width / fft.length) * 5;
  
  waveformCtx.fillStyle = '#0b0c10';
  waveformCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  
  const gradient = waveformCtx.createLinearGradient(0, 0, waveformCanvas.width, 0);
  gradient.addColorStop(0, '#00aaff');
  gradient.addColorStop(0.5, '#b400ff');
  gradient.addColorStop(1, '#00ffcc');
  
  for (let i = 0; i < fft.length; i++) {
    const barHeight = (fft[i] / 255) * (waveformCanvas.height * 0.8);
    waveformCtx.fillStyle = gradient;
    waveformCtx.fillRect(i * barWidth, waveformCanvas.height - barHeight, barWidth - 1, barHeight);
  }
}

function drawSpectrogram(data, amp) {
  // Dibujar espectrograma colorido
  waveformCtx.fillStyle = '#0b0c10';
  waveformCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  
  const imageData = waveformCtx.createImageData(waveformCanvas.width, waveformCanvas.height);
  const pixels = imageData.data;
  
  const step = Math.ceil(data.length / waveformCanvas.width);
  
  for (let x = 0; x < waveformCanvas.width; x++) {
    let sum = 0;
    for (let j = 0; j < step; j++) {
      const idx = (x * step + j) % data.length;
      sum += Math.abs(data[idx]);
    }
    const value = Math.floor((sum / step) * 255);
    
    for (let y = 0; y < waveformCanvas.height; y++) {
      const idx = (y * waveformCanvas.width + x) * 4;
      const hue = (value + y) % 360;
      const rgb = hslToRgb(hue / 360, 1, 0.5);
      pixels[idx] = rgb[0];
      pixels[idx + 1] = rgb[1];
      pixels[idx + 2] = rgb[2];
      pixels[idx + 3] = 255;
    }
  }
  
  waveformCtx.putImageData(imageData, 0, 0);
}

function drawFrequency(data, amp) {
  // Similar a spectrum pero más detallado
  drawSpectrum(data, amp);
}

// ===== UTILITARIOS =====
function simpleFFT(data) {
  const result = new Uint8Array(64);
  const slice = data.length / result.length;
  
  for (let i = 0; i < result.length; i++) {
    const start = Math.floor(i * slice);
    const end = Math.floor(start + slice);
    let sum = 0;
    for (let j = start; j < end; j++) {
      sum += Math.abs(data[j]);
    }
    result[i] = (sum / (end - start)) * 255;
  }
  
  return result;
}

function hslToRgb(h, s, l) {
  let r, g, b;
  
  if (s === 0) {
    r = g = b = l;
  } else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };
    
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1/3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1/3);
  }
  
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

// ===== AUDIO LOADING =====
async function loadAudio() {
  const file = audioFileInput.files[0];
  if (!file) {
    updateStatus('❌ Seleccione un archivo de audio');
    return;
  }
  
  showLoading('Cargando archivo de audio...');
  
  try {
    const arrayBuffer = await file.arrayBuffer();
    audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    updateStatus(`✓ Cargado: ${file.name} | ${(audioBuffer.duration).toFixed(2)}s`);
    hideLoading();
    
    updateTimeDisplay();
    drawWaveform();
    
  } catch (error) {
    console.error('Error al cargar:', error);
    updateStatus(`❌ Error al cargar: ${error.message}`);
    hideLoading();
  }
}

// ===== REPRODUCCIÓN =====
function play() {
  if (!audioBuffer) {
    updateStatus('❌ Cargue un archivo primero');
    return;
  }
  
  if (isPlaying) return;
  
  isPlaying = true;
  source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  if (speedSlider) {
    source.playbackRate.value = parseFloat(speedSlider.value) || 1;
  }
  if (pitchSlider) {
    source.detune.value = parseFloat(pitchSlider.value) * 100 || 0;
  }
  
  // Aplicar efectos de volumen
  const volDb = parseFloat(volumeSlider.value);
  const volLinear = Math.pow(10, volDb / 20);
  
  const gainNode = audioContext.createGain();
  gainNode.gain.value = volLinear;
  
  source.connect(gainNode);
  gainNode.connect(audioContext.destination);
  
  source.start(0, currentTime);
  playBtn.style.opacity = '0.5';
  pauseBtn.style.opacity = '1';
  
  updateStatus('▶️ Reproduciendo...');
}

function pause() {
  if (!isPlaying || !source) return;
  
  isPlaying = false;
  source.stop();
  
  currentTime = audioContext.currentTime;
  
  playBtn.style.opacity = '1';
  pauseBtn.style.opacity = '0.5';
  
  updateStatus('⏸️ Pausado');
}

function stop() {
  if (source) {
    source.stop();
    source = null;
  }
  isPlaying = false;
  currentTime = 0;
  timeline.value = 0;
  
  playBtn.style.opacity = '1';
  pauseBtn.style.opacity = '0.5';
  
  updateStatus('⏹️ Detenido');
  updateTimeDisplay();
}

function updateTimeDisplay() {
  if (!audioBuffer) {
    timeDisplay.textContent = '00:00 / 00:00';
    return;
  }
  
  const current = Math.floor(currentTime);
  const total = Math.floor(audioBuffer.duration);
  const currentMin = Math.floor(current / 60);
  const currentSec = current % 60;
  const totalMin = Math.floor(total / 60);
  const totalSec = total % 60;
  
  timeDisplay.textContent = `${String(currentMin).padStart(2, '0')}:${String(currentSec).padStart(2, '0')} / ${String(totalMin).padStart(2, '0')}:${String(totalSec).padStart(2, '0')}`;
  
  if (audioBuffer) {
    timeline.max = 1000;
    timeline.value = (currentTime / audioBuffer.duration) * 1000;
  }
}

// Actualizar tiempo cada 100ms
setInterval(updateTimeDisplay, 100);

// ===== STEM SEPARATION =====
async function separateStems() {
  if (!audioBuffer) {
    updateStatus('❌ Cargue un archivo primero');
    return;
  }
  
  showLoading('🎼 Separando stems... Esto puede tomar un tiempo...');
  
  try {
    // Convertir audioBuffer a WAV
    const wav = encodeWAV(audioBuffer);
    const blob = new Blob([wav], { type: 'audio/wav' });
    
    const formData = new FormData();
    formData.append('audio', blob, 'audio.wav');
    
    const response = await fetch(`${API_URL}/separate-stems`, {
      method: 'POST',
      body: formData
    });
    
    if (response.ok) {
      const data = await response.json();
      
      // Mostrar stems
      showStems(data.stems);
      updateStatus('✓ Stems separados exitosamente');
      
    } else {
      throw new Error('Error en la API');
    }
    
    hideLoading();
    
  } catch (error) {
    console.error('Error:', error);
    updateStatus(`❌ Error en separación: ${error.message}`);
    hideLoading();
  }
}

function encodeWAV(audioBuffer) {
  const channel = audioBuffer.getChannelData(0);
  const sampleRate = audioBuffer.sampleRate;
  
  const buffer = new ArrayBuffer(44 + channel.length * 2);
  const view = new DataView(buffer);
  
  // WAV header
  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };
  
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + channel.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, channel.length * 2, true);
  
  // Audio data
  let off = 44;
  for (let i = 0; i < channel.length; i++, off += 2) {
    const s = Math.max(-1, Math.min(1, channel[i]));
    view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }
  
  return buffer;
}

function decodeStemBase64(b64) {
  const raw = atob(b64);
  const buf = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < raw.length; i++) view[i] = raw.charCodeAt(i);
  const dv = new DataView(buf);
  const n = raw.length / 2;
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) out[i] = dv.getInt16(i * 2, true) / 32768;
  return out;
}

function showStems(stems) {
  const stemNames = ['voz', 'bajo', 'bateria', 'otros'];
  
  stemNames.forEach((name) => {
    const card = document.querySelector(`.stem-card.${name}`);
    if (!card || stems[name] == null) return;
    let data = stems[name];
    if (typeof data === 'string') {
      try {
        data = decodeStemBase64(data);
      } catch (err) {
        console.error(err);
        return;
      }
    }
    card.classList.remove('hidden');
    const canvas = card.querySelector('.stem-canvas');
    drawSmallWaveform(canvas, data);
  });
}

function drawSmallWaveform(canvas, audioData) {
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.parentElement.clientWidth - 4;
  canvas.height = 40;
  
  ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // Dibujar miniatura de waveform
  const step = Math.ceil(audioData.length / canvas.width);
  const amp = canvas.height / 2;
  
  ctx.strokeStyle = '#00aaff';
  ctx.lineWidth = 1;
  ctx.beginPath();
  
  for (let i = 0; i < canvas.width; i++) {
    let sum = 0;
    for (let j = 0; j < step; j++) {
      const idx = (i * step + j) % audioData.length;
      sum += Math.abs(audioData[idx]);
    }
    const y = amp - (sum / step) * amp;
    if (i === 0) ctx.moveTo(i, y);
    else ctx.lineTo(i, y);
  }
  
  ctx.stroke();
}

// ===== UI UTILITIES =====
function updateStatus(message) {
  statusBox.textContent = message;
}

function showLoading(text = 'Procesando...') {
  document.getElementById('loadingText').textContent = text;
  loadingModal.classList.remove('hidden');
}

function hideLoading() {
  loadingModal.classList.add('hidden');
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', init);
