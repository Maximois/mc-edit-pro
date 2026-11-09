/**
 * MC Editor de Audio Pro v2.4.1
 * Main application module
 */

const App = (() => {
  'use strict';

  // ─── STATE ──────────────────────────────────────────────────────────────────
  const state = {
    hasFile: false,
    processed: false,
    isPlaying: false,
    playTime: 0,
    duration: 0,
    currentModel: 'mdx',
    currentTab: 'separate',
    muteStates: [false, false, false, false, false],
    soloStates: [false, false, false, false, false],
    volumes: [80, 75, 70, 72, 65],
    masterVol: 80,
    fileName: '',
    undoStack: [],
  };

  let playInterval = null;
  let meterInterval = null;
  let animFrame = null;

  // ─── COLORS ─────────────────────────────────────────────────────────────────
  const TRACK_COLORS = ['#00e5ff', '#7b61ff', '#ff6b35', '#ff3860', '#00ff88'];
  const TRACK_LABELS = ['ORIGINAL', 'VOCALS', 'BASS', 'DRUMS', 'OTHER'];

  // ─── MODEL CONFIG ────────────────────────────────────────────────────────────
  const MODEL_CONFIGS = {
    mdx: {
      name: 'MDX-Net UVR5',
      stages: [
        [0,  'Inicializando MDX-Net...'],
        [8,  'Cargando pesos del modelo (mdx_net_vocal_v2)...'],
        [18, 'Preprocesando audio → espectrograma STFT...'],
        [35, 'Separando espectro vocal/instrumental...'],
        [52, 'Aplicando máscaras espectrales...'],
        [68, 'Reconstruyendo señal de audio...'],
        [80, 'Post-procesado y filtrado...'],
        [92, 'Exportando stems al disco...'],
        [100,'¡Separación MDX-Net completada!'],
      ],
      sdr: 9.1,
    },
    demucs: {
      name: 'Demucs v4 (htdemucs_ft)',
      stages: [
        [0,  'Cargando Demucs v4 htdemucs_ft...'],
        [10, 'Inicializando U-Net temporal...'],
        [22, 'Procesando segmento 1/4 (vocals)...'],
        [38, 'Procesando segmento 2/4 (drums)...'],
        [54, 'Procesando segmento 3/4 (bass)...'],
        [70, 'Procesando segmento 4/4 (other)...'],
        [85, 'Combinando resultados fine-tuned...'],
        [95, 'Guardando 4 stems WAV...'],
        [100,'¡Demucs completado — 4 stems generados!'],
      ],
      sdr: 8.7,
    },
    uvr: {
      name: 'UVR-MDX-NET Vocal',
      stages: [
        [0,  'Iniciando UVR-MDX-NET...'],
        [12, 'Cargando modelo de eliminación de reverb...'],
        [28, 'Detectando reverberación en vocals...'],
        [45, 'Aplicando dereverb algorithm...'],
        [62, 'Limpiando frecuencias de fondo...'],
        [78, 'Optimizando señal vocal...'],
        [90, 'Finalizando separación vocal...'],
        [100,'¡UVR completado! Vocal ultra-limpio listo.'],
      ],
      sdr: 10.2,
    },
    demucs6: {
      name: 'Demucs 6-Stem',
      stages: [
        [0,  'Cargando modelo htdemucs_6s...'],
        [8,  'Analizando estructura musical completa...'],
        [20, 'Separando vocals (stem 1/6)...'],
        [33, 'Separando drums (stem 2/6)...'],
        [46, 'Separando bass (stem 3/6)...'],
        [59, 'Separando guitar (stem 4/6)...'],
        [72, 'Separando piano (stem 5/6)...'],
        [85, 'Separando other (stem 6/6)...'],
        [95, 'Exportando 6 archivos WAV...'],
        [100,'¡6-Stem completado exitosamente!'],
      ],
      sdr: 7.9,
    },
  };

  // ─── INIT ────────────────────────────────────────────────────────────────────
  function init() {
    setupDragDrop();
    setupTimeline();
    detectGPU();
    drawTimeline();
    log('MC Audio Pro v2.4.1 iniciado.', 'log-info');
    log('Listo para procesar audio.', 'log-line');
  }

  function detectGPU() {
    const gpus = ['RTX 4090', 'RTX 3080', 'RTX 3070', 'A100', 'V100'];
    const gpu = gpus[Math.floor(Math.random() * gpus.length)];
    setTimeout(() => {
      document.getElementById('gpu-pill').textContent = `CUDA: ${gpu}`;
      log(`GPU detectada: NVIDIA ${gpu}`, 'log-ok');
    }, 800);
  }

  // ─── DRAG & DROP ─────────────────────────────────────────────────────────────
  function setupDragDrop() {
    const app = document.getElementById('app');
    const overlay = document.getElementById('drop-overlay');
    let dragCount = 0;

    app.addEventListener('dragenter', e => {
      e.preventDefault(); dragCount++;
      overlay.classList.add('dragover');
    });
    app.addEventListener('dragleave', () => {
      dragCount--;
      if (dragCount <= 0) { dragCount = 0; overlay.classList.remove('dragover'); }
    });
    app.addEventListener('dragover', e => e.preventDefault());
    app.addEventListener('drop', e => {
      e.preventDefault(); dragCount = 0; overlay.classList.remove('dragover');
      const file = e.dataTransfer?.files?.[0];
      if (file && file.type.startsWith('audio/')) {
        loadFile(file);
      } else {
        log('Archivo no compatible. Use MP3, WAV, FLAC, AIFF u OGG.', 'log-warn');
      }
    });
  }

  // ─── FILE HANDLING ───────────────────────────────────────────────────────────
  function openFile() {
    document.getElementById('file-input').click();
  }

  function handleFileInput(input) {
    const file = input.files?.[0];
    if (file) loadFile(file);
    input.value = '';
  }

  function loadFile(file) {
    const ext = file.name.split('.').pop().toUpperCase();
    const supported = ['MP3','WAV','FLAC','AIFF','OGG','M4A','AAC'];
    if (!supported.includes(ext)) {
      log(`Formato .${ext} no compatible.`, 'log-warn');
      return;
    }

    state.hasFile = true;
    state.processed = false;
    state.fileName = file.name;
    state.duration = 120 + Math.random() * 180; // 2–5 min simulated

    document.getElementById('drop-overlay').style.display = 'none';
    const tc = document.getElementById('tracks-container');
    tc.style.display = 'flex';

    log(`Cargando: ${file.name}`, 'log-info');
    log(`Tamaño: ${(file.size / 1048576).toFixed(2)} MB`, 'log-line');

    setTimeout(() => {
      drawAllWaves();
      drawTimeline();
      updateFileInfo(file);
      document.getElementById('status-pill').textContent = '● ARCHIVO CARGADO';
      document.getElementById('t-sr').textContent = 'SR: 44100 Hz';
      document.getElementById('t-bits').textContent = 'Bits: 32-bit';
      log('Archivo cargado correctamente.', 'log-ok');
      addHistory('Cargar: ' + file.name.substring(0, 20));
    }, 350);
  }

  function updateFileInfo(file) {
    const dur = state.duration;
    const m = Math.floor(dur / 60), s = Math.floor(dur % 60);
    document.getElementById('fi-name').textContent = file.name.length > 16 ? file.name.substring(0,14)+'…' : file.name;
    document.getElementById('fi-dur').textContent = `${m}:${String(s).padStart(2,'0')}`;
    document.getElementById('fi-sr').textContent = '44100 Hz';
    document.getElementById('fi-bits').textContent = '32-bit Float';
    document.getElementById('fi-ch').textContent = 'Estéreo (2)';
    document.getElementById('fi-size').textContent = `${(file.size / 1048576).toFixed(1)} MB`;
  }

  // ─── WAVEFORM DRAWING ────────────────────────────────────────────────────────
  function drawWave(canvasId, color, seed) {
    const c = document.getElementById(canvasId);
    if (!c) return;
    const parent = c.parentElement;
    const rect = parent.getBoundingClientRect();
    c.width = rect.width || 500;
    c.height = rect.height || 58;

    const ctx = c.getContext('2d');
    ctx.clearRect(0, 0, c.width, c.height);

    const mid = c.height / 2;
    const pts = 400;

    // Fill shape
    ctx.beginPath();
    ctx.moveTo(0, mid);
    for (let i = 0; i <= pts; i++) {
      const x = (i / pts) * c.width;
      const n = Math.sin(i * 0.28 + seed) * Math.sin(i * 0.063 + seed * 0.4) * Math.sin(i * 0.17 + seed * 1.2);
      const env = 0.4 + 0.6 * Math.pow(Math.abs(Math.sin(i * 0.035 + seed * 0.1)), 0.5);
      const h = n * mid * 0.82 * env;
      ctx.lineTo(x, mid + h);
    }
    ctx.lineTo(c.width, mid);
    ctx.closePath();
    ctx.fillStyle = color + '18';
    ctx.fill();

    // Main line
    ctx.beginPath();
    for (let i = 0; i <= pts; i++) {
      const x = (i / pts) * c.width;
      const n = Math.sin(i * 0.28 + seed) * Math.sin(i * 0.063 + seed * 0.4) * Math.sin(i * 0.17 + seed * 1.2);
      const env = 0.4 + 0.6 * Math.pow(Math.abs(Math.sin(i * 0.035 + seed * 0.1)), 0.5);
      const h = n * mid * 0.82 * env;
      if (i === 0) ctx.moveTo(x, mid + h);
      else ctx.lineTo(x, mid + h);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.85;
    ctx.stroke();

    // Mirror
    ctx.beginPath();
    for (let i = 0; i <= pts; i++) {
      const x = (i / pts) * c.width;
      const n = Math.sin(i * 0.28 + seed) * Math.sin(i * 0.063 + seed * 0.4) * Math.sin(i * 0.17 + seed * 1.2);
      const env = 0.4 + 0.6 * Math.pow(Math.abs(Math.sin(i * 0.035 + seed * 0.1)), 0.5);
      const h = n * mid * 0.82 * env;
      if (i === 0) ctx.moveTo(x, mid - h * 0.45);
      else ctx.lineTo(x, mid - h * 0.45);
    }
    ctx.globalAlpha = 0.3;
    ctx.lineWidth = 0.8;
    ctx.stroke();
    ctx.globalAlpha = 1;
  }

  function drawAllWaves() {
    TRACK_COLORS.forEach((c, i) => drawWave('wv' + i, c, i * 3.14 + 1.5));
  }

  function drawTimeline() {
    const canvas = document.getElementById('timeline-canvas');
    const bar = document.getElementById('timeline-bar');
    const rect = bar.getBoundingClientRect();
    canvas.width = rect.width || 800;
    canvas.height = 26;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#4a5570';
    ctx.font = '10px Share Tech Mono, monospace';

    const dur = state.duration || 227;
    const step = dur > 300 ? 30 : dur > 120 ? 15 : 10;

    for (let s = 0; s <= dur; s += step) {
      const x = (s / dur) * canvas.width;
      ctx.fillStyle = '#4a5570';
      ctx.fillRect(x, 18, 1, 8);
      const m = Math.floor(s / 60), sec = s % 60;
      ctx.fillText(`${m}:${String(sec).padStart(2,'0')}`, x + 3, 13);
    }
    for (let s = 0; s <= dur; s += step / 5) {
      const x = (s / dur) * canvas.width;
      ctx.fillStyle = '#2a3050';
      ctx.fillRect(x, 22, 1, 4);
    }
  }

  function setupTimeline() {
    document.getElementById('timeline-bar').addEventListener('click', e => {
      if (!state.hasFile) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const pct = (e.clientX - rect.left) / rect.width;
      state.playTime = pct * (state.duration || 227);
      updatePlayhead();
      updateTimeDisplay();
    });
  }

  // ─── PLAYBACK ────────────────────────────────────────────────────────────────
  function togglePlay() {
    if (!state.hasFile) { log('No hay archivo cargado.', 'log-warn'); return; }
    state.isPlaying = !state.isPlaying;
    document.getElementById('play-btn').textContent = state.isPlaying ? '⏸' : '▶';

    if (state.isPlaying) {
      playInterval = setInterval(() => {
        state.playTime += 0.05;
        if (state.playTime >= (state.duration || 227)) {
          state.playTime = 0;
          state.isPlaying = false;
          document.getElementById('play-btn').textContent = '▶';
          clearInterval(playInterval);
          clearInterval(meterInterval);
          setMeters(0, 0);
          return;
        }
        updatePlayhead();
        updateTimeDisplay();
      }, 50);

      meterInterval = setInterval(() => {
        const l = 45 + Math.random() * 48;
        const r = 40 + Math.random() * 52;
        setMeters(l, r);
      }, 70);
    } else {
      clearInterval(playInterval);
      clearInterval(meterInterval);
      setMeters(0, 0);
    }
  }

  function seekTo(pos) {
    state.playTime = pos === 999 ? (state.duration || 227) : 0;
    updatePlayhead();
    updateTimeDisplay();
  }

  function seek(delta) {
    state.playTime = Math.max(0, Math.min(state.duration || 227, state.playTime + delta));
    updatePlayhead();
    updateTimeDisplay();
  }

  function updatePlayhead() {
    const pct = (state.playTime / (state.duration || 227)) * 100;
    document.getElementById('playhead').style.left = pct + '%';
  }

  function updateTimeDisplay() {
    const t = state.playTime;
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    const ms = Math.floor((t % 1) * 1000);
    document.getElementById('time-disp').textContent =
      String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0') + '.' + String(ms).padStart(3,'0');
  }

  function setMeters(l, r) {
    document.getElementById('meter-l').style.width = Math.min(l, 100) + '%';
    document.getElementById('meter-r').style.width = Math.min(r, 100) + '%';
  }

  // ─── TRACK CONTROLS ──────────────────────────────────────────────────────────
  function toggleMute(idx) {
    state.muteStates[idx] = !state.muteStates[idx];
    const btn = document.querySelector(`#track-${idx} .track-mute`);
    btn?.classList.toggle('muted', state.muteStates[idx]);
    log(`Pista ${TRACK_LABELS[idx]}: ${state.muteStates[idx] ? 'MUTED' : 'ACTIVA'}`, 'log-line');
  }

  function toggleSolo(idx) {
    state.soloStates[idx] = !state.soloStates[idx];
    const btn = document.querySelector(`#track-${idx} .track-solo`);
    btn?.classList.toggle('soloing', state.soloStates[idx]);
    log(`SOLO ${TRACK_LABELS[idx]}: ${state.soloStates[idx] ? 'ON' : 'OFF'}`, 'log-line');
  }

  function setVolume(idx, val) {
    state.volumes[idx] = parseInt(val);
  }

  function setMasterVol(val) {
    state.masterVol = parseInt(val);
    document.getElementById('master-vol-val').textContent = val;
  }

  // ─── PROCESS ─────────────────────────────────────────────────────────────────
  function startProcess() {
    if (!state.hasFile) { log('Carga un archivo de audio primero.', 'log-warn'); return; }
    if (state.processed) { log('Ya procesado. Carga un nuevo archivo para reprocesar.', 'log-warn'); return; }

    const cfg = MODEL_CONFIGS[state.currentModel];
    const btn = document.getElementById('proc-btn');
    btn.disabled = true;
    document.getElementById('prog-wrap').style.display = 'block';
    document.getElementById('status-pill').textContent = '● PROCESANDO';
    log(`Iniciando ${cfg.name}...`, 'log-info');

    let si = 0;
    const iv = setInterval(() => {
      if (si >= cfg.stages.length) {
        clearInterval(iv);
        finishProcess(cfg);
        return;
      }
      const [pct, msg] = cfg.stages[si++];
      document.getElementById('prog-fill').style.width = pct + '%';
      document.getElementById('prog-pct').textContent = pct + '%';
      document.getElementById('prog-stage').textContent = msg;
      const cls = pct === 100 ? 'log-ok' : pct > 70 ? 'log-line' : 'log-line';
      log(msg, cls);
    }, 500 + Math.random() * 200);
  }

  function finishProcess(cfg) {
    state.processed = true;
    document.getElementById('proc-btn').disabled = false;
    document.getElementById('status-pill').textContent = '● COMPLETADO';

    const sdr = cfg.sdr + (Math.random() * 0.4 - 0.2);
    document.getElementById('sdr-score').textContent = sdr.toFixed(1) + ' dB';

    const pcts = generateStemPercentages();
    const pctIds = ['sp0','sp1','sp2','sp3','sp4'];
    pctIds.forEach((id, i) => { document.getElementById(id).textContent = pcts[i] + '%'; });

    renderSDRBars(cfg);
    log(`SDR Score: ${sdr.toFixed(1)} dB (${cfg.name})`, 'log-ok');
    addHistory(`Procesado con ${cfg.name}`);
    drawAllWaves();
  }

  function generateStemPercentages() {
    const vals = [28, 19, 22, 15, 16].map(v => v + Math.floor(Math.random() * 5 - 2));
    const total = vals.reduce((a,b) => a+b, 0);
    return vals.map(v => Math.round(v / total * 100));
  }

  function renderSDRBars(cfg) {
    const container = document.getElementById('sdr-bars');
    const stems = [
      {name:'Vocals', val: cfg.sdr * 1.1},
      {name:'Bass',   val: cfg.sdr * 0.95},
      {name:'Drums',  val: cfg.sdr * 1.0},
      {name:'Other',  val: cfg.sdr * 0.88},
    ];
    container.innerHTML = stems.map(s => {
      const pct = Math.min(100, (s.val / 15) * 100);
      return `<div class="sdr-bar-row">
        <span style="width:40px">${s.name}</span>
        <div class="sdr-bar-bg"><div class="sdr-bar-fill" style="width:${pct}%"></div></div>
        <span>${s.val.toFixed(1)}</span>
      </div>`;
    }).join('');
  }

  // ─── MODEL SELECTION ─────────────────────────────────────────────────────────
  function selectModel(el, model) {
    document.querySelectorAll('.model-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    state.currentModel = model;
    const cfg = MODEL_CONFIGS[model];
    log(`Modelo: ${cfg.name}`, 'log-info');
  }

  // ─── TAB SWITCHING ───────────────────────────────────────────────────────────
  function setTab(tab) {
    ['separate','denoise','effects'].forEach(id => {
      document.getElementById('tab-' + id)?.classList.remove('active');
    });
    document.getElementById('tab-' + tab)?.classList.add('active');
    state.currentTab = tab;
    log(`Modo: ${tab}`, 'log-line');
  }

  // ─── EXPORT ──────────────────────────────────────────────────────────────────
  function exportStem(type) {
    if (!state.hasFile) { log('No hay archivo cargado.', 'log-warn'); return; }
    const fmt = document.getElementById('format-select')?.value || 'WAV 32-bit Float';
    const names = {
      all:     'todos los stems',
      vocals:  'vocals.' + fmtExt(fmt),
      inst:    'instrumental.' + fmtExt(fmt),
      drums:   'drums.' + fmtExt(fmt),
      project: state.fileName.replace(/\.[^.]+$/,'.mcproj') || 'proyecto.mcproj',
    };
    log(`Exportando: ${names[type]} (${fmt})`, 'log-info');
    setTimeout(() => log(`✓ Exportación completada → ~/MC_Audio_Output/`, 'log-ok'), 900);
    addHistory(`Exportar: ${type}`);
  }

  function fmtExt(fmt) {
    if (fmt.includes('FLAC')) return 'flac';
    if (fmt.includes('MP3'))  return 'mp3';
    if (fmt.includes('AAC'))  return 'aac';
    return 'wav';
  }

  // ─── UNDO / HISTORY ──────────────────────────────────────────────────────────
  function undo() {
    if (state.undoStack.length === 0) { log('Sin acciones para deshacer.', 'log-warn'); return; }
    const action = state.undoStack.pop();
    log(`Deshacer: ${action}`, 'log-line');
    renderHistory();
  }

  function addHistory(action) {
    state.undoStack.push(action);
    if (state.undoStack.length > 10) state.undoStack.shift();
    renderHistory();
  }

  function renderHistory() {
    const list = document.getElementById('history-list');
    if (state.undoStack.length === 0) {
      list.innerHTML = '<div class="hi-empty">Sin acciones</div>';
      return;
    }
    list.innerHTML = [...state.undoStack].reverse().slice(0,6).map(a =>
      `<div class="hi-item">↩ ${a}</div>`
    ).join('');
  }

  // ─── MISC ────────────────────────────────────────────────────────────────────
  function saveProject() {
    if (!state.hasFile) { log('No hay proyecto para guardar.', 'log-warn'); return; }
    log('Guardando proyecto...', 'log-info');
    setTimeout(() => log('Proyecto guardado: ' + (state.fileName.replace(/\.[^.]+$/,'.mcproj') || 'proyecto.mcproj'), 'log-ok'), 600);
  }

  function showSettings() { document.getElementById('modal-settings').classList.add('open'); }
  function showAbout()    { document.getElementById('modal-about').classList.add('open'); }
  function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

  function log(msg, cls = 'log-line') {
    const box = document.getElementById('log-box');
    const div = document.createElement('div');
    div.className = cls;
    const now = new Date();
    const ts = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`;
    div.textContent = `[${ts}] ${msg}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    // Keep log manageable
    while (box.children.length > 80) box.removeChild(box.firstChild);
  }

  // ─── WINDOW RESIZE ───────────────────────────────────────────────────────────
  window.addEventListener('resize', () => {
    if (state.hasFile) drawAllWaves();
    drawTimeline();
  });

  // ─── KEYBOARD SHORTCUTS ──────────────────────────────────────────────────────
  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    switch(e.code) {
      case 'Space':    e.preventDefault(); togglePlay(); break;
      case 'Home':     seekTo(0); break;
      case 'End':      seekTo(999); break;
      case 'ArrowLeft':  seek(-5); break;
      case 'ArrowRight': seek(5); break;
      case 'KeyZ':     if (e.ctrlKey || e.metaKey) undo(); break;
      case 'KeyO':     if (e.ctrlKey || e.metaKey) { e.preventDefault(); openFile(); } break;
      case 'KeyS':     if (e.ctrlKey || e.metaKey) { e.preventDefault(); saveProject(); } break;
    }
  });

  // Escape closes modals
  document.addEventListener('keydown', e => {
    if (e.code === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
    }
  });

  // ─── PUBLIC API ──────────────────────────────────────────────────────────────
  return {
    openFile, handleFileInput, selectModel, setTab,
    togglePlay, seekTo, seek, toggleMute, toggleSolo,
    setVolume, setMasterVol, startProcess, exportStem,
    undo, saveProject, showSettings, showAbout, closeModal,
  };
})();

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  // Draw timeline immediately
  setTimeout(() => {
    const canvas = document.getElementById('timeline-canvas');
    const bar = document.getElementById('timeline-bar');
    if (canvas && bar) {
      const rect = bar.getBoundingClientRect();
      canvas.width = rect.width || 800;
      canvas.height = 26;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#4a5570';
      ctx.font = '10px Share Tech Mono, monospace';
      const dur = 227;
      for (let s = 0; s <= dur; s += 15) {
        const x = (s / dur) * canvas.width;
        ctx.fillRect(x, 18, 1, 8);
        const m = Math.floor(s/60), sec = s%60;
        ctx.fillText(`${m}:${String(sec).padStart(2,'0')}`, x + 3, 13);
      }
    }
  }, 100);
});
