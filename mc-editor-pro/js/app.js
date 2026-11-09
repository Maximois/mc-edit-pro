/* ═══════════════════════════════════════════════════════════════
   MC Audio Pro Studio — app.js v2.4.1
   ═══════════════════════════════════════════════════════════════ */
'use strict';

const A = (() => {

  /* ── STATE ─────────────────────────────────────────── */
  const S = {
    file: null, hasFile: false, processed: false, processing: false,
    audioId: null, audioInfo: null, uploadPromise: null, loadToken: 0, stemsId: null, stems: {},
    waveforms: [],
    playing: false, time: 0, dur: 0,
    model: 'mdx', mode: 'stems',
    mute: [false,false,false,false,false,false,false,false],
    solo: [false,false,false,false,false,false,false,false],
    vol:  [85,80,75,78,68,72,72,72],
    masterVol: 80, zoom: 1,
    history: [], histIdx: -1,
    params: { seg:256, ovl:25, batch:1 },
  };

  const audioPlayer = new Audio();
  audioPlayer.preload = 'metadata';
  let audioObjectUrl = null;
  let desktopBridge = null;
  const stemPlayers = new Map();
  let specAnim=null;

  const COLORS = ['#00d4e8','#a080ff','#f09050','#ff6060','#50e890','#e0b040','#40b8d0','#00d4e8'];
  const NAMES  = ['Original','Vocals','Bass','Drums','Other','Guitar','Piano','Instrumental'];

  const MODELS = {
    mdx:{name:'UVR5 MDX-Net · Inst full 292',stems:'Vocals / Instrumental'},
    demucs:{name:'Demucs v4 · 4 stems',stems:'Vocals / Bass / Drums / Other'},
    d6:{name:'Demucs v4 · 6 stems',stems:'Vocals / Bass / Drums / Other / Guitar / Piano'},
  };
  const STEM_TRACKS = { vocals:1, bass:2, drums:3, other:4, guitar:5, piano:6, instrumental:7 };

  /* ── INIT ───────────────────────────────────────────── */
  function init() {
    if(typeof qt!=='undefined'&&qt.webChannelTransport){
      new QWebChannel(qt.webChannelTransport,channel=>{desktopBridge=channel.objects.desktopBridge;});
    }
    setupDrag();
    setupKnob();
    setupSpectrogram();
    setupMiniSpec();
    drawRuler();
    audioPlayer.addEventListener('loadedmetadata', onAudioMetadata);
    audioPlayer.addEventListener('timeupdate', onAudioTimeUpdate);
    audioPlayer.addEventListener('play', onAudioPlay);
    audioPlayer.addEventListener('pause', onAudioPause);
    audioPlayer.addEventListener('ended', onAudioEnded);
    audioPlayer.addEventListener('error', onAudioError);
    detectGPU();
    log('MC Audio Pro Studio v2.4.1','cl-info');
    log('Modelos disponibles: UVR5 MDX-Net y Demucs v4 de 4 y 6 stems.','cl');
    log('Sistema inicializado correctamente.','cl-ok');
    startSpecAnim();
    window.addEventListener('resize', onResize);
  }

  function detectGPU() {
    set('gpu-name','Aceleración: se informa al procesar');
  }

  function onResize() {
    if (S.hasFile) drawAllWaves();
    drawRuler();
    resizeSpec();
  }

  /* ── DRAG & DROP ─────────────────────────────────────── */
  function setupDrag() {
    const app = document.getElementById('app');
    let n = 0;
    app.addEventListener('dragenter', e => { e.preventDefault(); if(++n===1) app.classList.add('drag-on'); });
    app.addEventListener('dragleave', () => { if(--n<=0){n=0;app.classList.remove('drag-on');} });
    app.addEventListener('dragover', e => e.preventDefault());
    app.addEventListener('drop', e => {
      e.preventDefault(); n=0; app.classList.remove('drag-on');
      const f = e.dataTransfer?.files?.[0];
      if (f && (f.type.startsWith('audio/') || /\.(mp3|wav|flac|aiff|ogg|m4a|aac)$/i.test(f.name))) loadFile(f);
      else warn('Formato no soportado. Usa MP3, WAV, FLAC, AIFF, OGG, M4A o AAC.');
    });
  }

  /* ── FILE ────────────────────────────────────────────── */
  function openFile() { document.getElementById('file-in').click(); }
  function fileChosen(inp) { if(inp.files?.[0]) loadFile(inp.files[0]); inp.value=''; }

  function loadFile(f) {
    if(S.processing){warn('Espera a que termine la separación antes de cargar otro archivo.');return;}
    const ext = f.name.split('.').pop().toUpperCase();
    if (!['MP3','WAV','FLAC','AIFF','OGG','M4A','AAC'].includes(ext)) {
      warn('Formato .'+ext+' no compatible.'); return;
    }
    const previousAudioId=S.audioId;
    const previousStemsId=S.stemsId;
    stopPlay();
    audioPlayer.pause();
    clearStemPlayers();
    const previousUrl=audioObjectUrl;
    audioObjectUrl=null;
    audioPlayer.removeAttribute('src');
    audioPlayer.load();
    if (previousUrl) URL.revokeObjectURL(previousUrl);
    if(previousAudioId||previousStemsId){
      cleanupBackend(previousAudioId,previousStemsId).catch(error=>warn(error.message));
    }
    audioObjectUrl = URL.createObjectURL(f);
    const loadToken=++S.loadToken;
    S.file=f; S.hasFile=false; S.processed=false; S.processing=false;
    S.audioId=null; S.audioInfo=null; S.stemsId=null; S.stems={}; S.waveforms=[];
    S.time=0; S.dur=0;
    resetStemDisplay();
    set('prog-stage','En espera');
    set('prog-pct','—');
    const progressBar=document.getElementById('prog-bar');
    progressBar.classList.remove('indeterminate');
    progressBar.style.width='0%';
    document.getElementById('drop-zone').style.display='flex';
    document.getElementById('tracks-wrap').style.display='none';
    document.getElementById('proj-name').textContent = f.name.replace(/\.[^.]+$/,'.mcproj');
    document.getElementById('sb-file').textContent = f.name.length>20 ? f.name.slice(0,18)+'…' : f.name;
    set('fi-name', f.name.length>16 ? f.name.slice(0,14)+'…' : f.name);
    set('fi-dur','Cargando…');
    set('fi-sz',(f.size/1048576).toFixed(1)+' MB');
    set('fi-codec',ext);
    log('Abriendo: '+f.name,'cl-info');
    log('Tamaño: '+(f.size/1048576).toFixed(2)+' MB | Formato: '+ext,'cl');
    audioPlayer.src = audioObjectUrl;
    audioPlayer.load();
    S.uploadPromise=uploadAudio(f,loadToken).catch(error=>{
      if(loadToken===S.loadToken)warn('No se pudo enviar el audio al backend: '+error.message);
      throw error;
    });
    S.uploadPromise.catch(()=>{});
  }

  async function uploadAudio(file, loadToken) {
    const formData=new FormData();
    formData.append('audio',file,file.name);
    const response=await fetch('/api/upload-audio',{method:'POST',body:formData});
    const result=await response.json();
    if(!response.ok) throw new Error(result.error||'No se pudo enviar el audio al backend.');
    if(loadToken!==S.loadToken){
      await cleanupBackend(result.audio_id,null);
      return null;
    }
    S.audioId=result.audio_id;
    S.audioInfo=result;
    S.waveforms[0]=result.waveform;
    updateAudioInfo();
    drawAllWaves();
    log('Audio recibido por el backend.','cl-ok');
    return result;
  }

  async function cleanupBackend(audioId,stemsId,attempt=0){
    const response=await fetch('/api/cleanup-session',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({audio_id:audioId,stems_id:stemsId}),
    });
    const result=await response.json();
    if(response.status===409&&attempt<5){
      await new Promise(resolve=>setTimeout(resolve,500));
      return cleanupBackend(audioId,stemsId,attempt+1);
    }
    if(!response.ok)throw new Error(result.error||'No se pudo limpiar el audio temporal anterior.');
  }

  function onAudioMetadata() {
    if (!Number.isFinite(audioPlayer.duration)) {
      warn('No se pudo determinar la duración del archivo.');
      return;
    }
    S.hasFile=true;
    S.dur=audioPlayer.duration;
    S.time=0;
    document.getElementById('drop-zone').style.display='none';
    document.getElementById('tracks-wrap').style.display='block';
    set('fi-dur',formatDuration(S.dur));
    updateAudioInfo();
    set('fi-bits','—');
    updatePlayhead();
    updateTimeDisplay();
    updateDurDisplay();
    drawAllWaves();
    drawRuler();
    log('Audio listo para reproducir.','cl-ok');
    addHist('Abrir: '+S.file.name.slice(0,22));
  }

  function updateAudioInfo(){
    set('fi-sr',S.audioInfo?`${S.audioInfo.sample_rate} Hz`:'—');
    set('fi-ch',S.audioInfo?String(S.audioInfo.channels):'—');
  }

  function onAudioError() {
    if (audioPlayer.error?.code===1) return;
    if (!audioObjectUrl || audioPlayer.currentSrc !== audioObjectUrl) return;
    const errors = {
      1:'carga cancelada',
      2:'error al leer el archivo',
      3:'formato o datos de audio no compatibles',
      4:'formato no compatible con el reproductor',
    };
    const code=audioPlayer.error?.code;
    URL.revokeObjectURL(audioObjectUrl);
    audioObjectUrl=null;
    S.hasFile=false;
    S.file=null;
    S.dur=0;
    document.getElementById('drop-zone').style.display='flex';
    document.getElementById('tracks-wrap').style.display='none';
    set('fi-dur','—');
    warn('No se pudo abrir el audio: '+(errors[code]||'error desconocido')+'.');
  }

  function formatDuration(seconds) {
    const minutes=Math.floor(seconds/60);
    const remainder=Math.floor(seconds%60);
    return minutes+':'+String(remainder).padStart(2,'0');
  }

  function onAudioTimeUpdate() {
    if (!S.hasFile) return;
    S.time=audioPlayer.currentTime;
    for(const player of stemPlayers.values()){
      if(!player.paused&&player.readyState>0&&Math.abs(player.currentTime-S.time)>0.2)player.currentTime=S.time;
    }
    updatePlayhead();
    updateTimeDisplay();
    document.getElementById('sb-pos').textContent=fmtPos(S.time);
  }

  function onAudioPlay() {
    S.playing=true;
    const btn=document.getElementById('btn-play');
    btn.textContent='⏸';
    btn.classList.add('playing');
  }

  function onAudioPause() {
    S.playing=false;
    const btn=document.getElementById('btn-play');
    btn.textContent='▶';
    btn.classList.remove('playing');
  }

  function onAudioEnded() {
    S.time=S.dur;
    updatePlayhead();
    updateTimeDisplay();
    pausePlayers();
    onAudioPause();
  }

  function applyPlaybackVolume() {
    const hasSolo=S.solo.some(Boolean);
    audioPlayer.volume=S.mute[0]||(hasSolo&&!S.solo[0])
      ? 0
      : (S.masterVol/100)*(S.vol[0]/100);
    for(const [key,player] of stemPlayers){
      const idx=STEM_TRACKS[key];
      player.volume=S.mute[idx]||(hasSolo&&!S.solo[idx])
        ? 0
        : (S.masterVol/100)*(S.vol[idx]/100);
    }
  }

  /* ── WAVEFORM ────────────────────────────────────────── */
  function drawWave(id, color, trackIndex) {
    const c = document.getElementById(id); if(!c) return;
    const p = c.parentElement; const r = p.getBoundingClientRect();
    c.width = r.width||600; c.height = r.height||64;
    const ctx = c.getContext('2d'), W=c.width, H=c.height, mid=H/2;
    ctx.clearRect(0,0,W,H);
    const samples=S.waveforms[trackIndex];
    if(!samples?.length){
      ctx.strokeStyle=color+'44';
      ctx.beginPath();ctx.moveTo(0,mid);ctx.lineTo(W,mid);ctx.stroke();
      return;
    }
    const grad = ctx.createLinearGradient(0,0,0,H);
    grad.addColorStop(0,color+'28');
    grad.addColorStop(0.5,color+'12');
    grad.addColorStop(1,color+'04');
    ctx.beginPath(); ctx.moveTo(0,mid);
    for(let x=0;x<W;x++){
      const amplitude=Math.min(1,samples[Math.floor(x/W*samples.length)]||0)*mid*0.9;
      ctx.lineTo(x,mid-amplitude);
    }
    for(let x=W-1;x>=0;x--){
      const amplitude=Math.min(1,samples[Math.floor(x/W*samples.length)]||0)*mid*0.9;
      ctx.lineTo(x,mid+amplitude);
    }
    ctx.lineTo(W,mid); ctx.closePath();
    ctx.fillStyle=grad; ctx.fill();
    ctx.strokeStyle=color;ctx.lineWidth=1.25;ctx.stroke();
  }

  function drawAllWaves() {
    COLORS.forEach((c,i) => drawWave('wv'+i,c,i));
  }

  /* ── RULER ───────────────────────────────────────────── */
  function drawRuler() {
    const el = document.getElementById('ruler-canvas');
    const bar = document.getElementById('ruler');
    const r = bar.getBoundingClientRect();
    el.width = r.width||800; el.height = 22;
    const ctx = el.getContext('2d'), W=el.width, dur=S.dur||240;
    ctx.clearRect(0,0,W,22);
    const step = dur>300?30:dur>120?15:10;
    for(let s=0;s<=dur;s+=step/5){
      const x=(s/dur)*W, major=(s%step===0);
      ctx.fillStyle=major?'#4a5870':'#2a3450';
      ctx.fillRect(x,major?10:16,1,major?12:6);
    }
    ctx.fillStyle='#8a9ab5'; ctx.font='9px JetBrains Mono,monospace';
    for(let s=0;s<=dur;s+=step){
      const x=(s/dur)*W;
      const m=Math.floor(s/60), sec=s%60;
      ctx.fillText(m+':'+String(sec).padStart(2,'0'), x+3, 9);
    }
  }

  function rulerClick(e) {
    if (!S.hasFile) return;
    const r = document.getElementById('ruler').getBoundingClientRect();
    seek(((e.clientX-r.left)/r.width)*S.dur);
  }

  function updatePlayhead() {
    const pct = S.dur > 0 ? (S.time/S.dur)*100 : 0;
    document.getElementById('playhead').style.left = pct+'%';
  }

  /* ── SPECTROGRAM ──────────────────────────────────────── */
  function resizeSpec() {
    const el=document.getElementById('spec-canvas');
    const p=document.getElementById('spec-area');
    const r=p.getBoundingClientRect();
    el.width=r.width||800; el.height=r.height||120;
  }

  function setupSpectrogram() {
    setTimeout(()=>{ resizeSpec(); drawSpec(); },100);
  }

  function drawSpec() {
    const el=document.getElementById('spec-canvas');
    const ctx=el.getContext('2d'); if(!el.width) return;
    const W=el.width, H=el.height;
    ctx.clearRect(0,0,W,H);
    if(!S.hasFile){ drawEmptySpec(ctx,W,H); return; }
    ctx.strokeStyle='rgba(255,255,255,0.04)';ctx.lineWidth=0.5;
    for(let y=0;y<H;y+=H/8){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
    for(let x=0;x<W;x+=W/16){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
    ctx.fillStyle='rgba(138,154,181,0.75)';
    ctx.font='11px JetBrains Mono,monospace';
    ctx.textAlign='center';
    ctx.fillText('Espectrograma real aún no integrado',W/2,H/2);
  }

  function drawEmptySpec(ctx,W,H) {
    ctx.fillStyle='#0e1118'; ctx.fillRect(0,0,W,H);
    for(let y=0;y<H;y+=H/8){
      ctx.strokeStyle='rgba(255,255,255,0.03)'; ctx.lineWidth=0.5;
      ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();
    }
  }

  function startSpecAnim() {
    function frame() {
      if(S.playing) drawSpec();
      specAnim = requestAnimationFrame(frame);
    }
    frame();
  }

  /* ── MINI SPECTRUM ────────────────────────────────────── */
  function setupMiniSpec() { setTimeout(()=>drawMiniSpec(),200); }
  function drawMiniSpec() {
    const el=document.getElementById('mini-spec');
    const p=el.parentElement;
    const r=p.getBoundingClientRect();
    el.width=r.width||300; el.height=r.height||38;
    const ctx=el.getContext('2d'), W=el.width, H=el.height;
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle='rgba(138,154,181,0.75)';
    ctx.font='10px JetBrains Mono,monospace';
    ctx.textAlign='center';
    ctx.fillText('Medidor de audio no integrado',W/2,H/2+3);
  }

  /* ── PLAYBACK ─────────────────────────────────────────── */
  async function play() {
    if(!S.hasFile){warn('Carga un archivo primero.');return;}
    if (!audioPlayer.paused) {
      pausePlayers();
      return;
    }
    if (audioPlayer.ended) seek(0);
    applyPlaybackVolume();
    try {
      for(const player of stemPlayers.values())setPlayerTime(player,S.time);
      await Promise.all([audioPlayer,...stemPlayers.values()].map(player=>player.play()));
    } catch (error) {
      pausePlayers();
      warn('No se pudo reproducir el archivo: '+error.message);
    }
  }

  function stopPlay(){
    pausePlayers();
    onAudioPause();
  }

  function seek(t){
    if(!S.hasFile)return;
    S.time=Math.max(0,Math.min(S.dur,t>=9000?S.dur:t));
    audioPlayer.currentTime=S.time;
    for(const player of stemPlayers.values())setPlayerTime(player,S.time);
    updatePlayhead();
    updateTimeDisplay();
  }

  function setPlayerTime(player,time){
    if(player.readyState>0){
      player.currentTime=Math.min(time,Math.max(0,player.duration-0.01));
      return;
    }
    player.addEventListener('loadedmetadata',()=>{
      player.currentTime=Math.min(S.time,Math.max(0,player.duration-0.01));
    },{once:true});
  }

  function pausePlayers(){
    audioPlayer.pause();
    for(const player of stemPlayers.values())player.pause();
  }
  function seekDelta(d){
    if(!S.hasFile)return;
    seek(S.time+d);
  }

  function updateTimeDisplay(){
    const t=S.time;
    const m=Math.floor(t/60),s=Math.floor(t%60),ms=Math.floor((t%1)*1000);
    const str=String(m).padStart(2,'0')+':'+String(s).padStart(2,'0')+'.'+String(ms).padStart(3,'0');
    document.getElementById('time-disp').textContent=str;
    document.getElementById('sb-pos').textContent=str;
  }

  function updateDurDisplay(){
    const t=S.dur;
    const m=Math.floor(t/60),s=Math.floor(t%60);
    document.getElementById('dur-disp').textContent=m+':'+String(s).padStart(2,'0');
  }

  /* ── PROCESSING ───────────────────────────────────────── */
  async function process(){
    if(!S.hasFile){warn('Carga un archivo de audio primero.');return;}
    if(S.processed){warn('Ya procesado. Carga un nuevo archivo.');return;}
    if(S.processing)return;
    const cfg=MODELS[S.model];
    const btn=document.getElementById('btn-proc');
    S.processing=true;
    pausePlayers();
    btn.disabled=true;
    btn.textContent='Procesando…';
    log('─'.repeat(28),'cl');
    log('Iniciando '+cfg.name,'cl-info');
    set('prog-stage','Subiendo audio al backend…');
    set('prog-pct','…');
    document.getElementById('prog-bar').classList.add('indeterminate');

    try{
      const upload=await S.uploadPromise;
      if(!S.audioId||!upload)throw new Error('El audio no llegó al backend. Vuelve a cargarlo e inténtalo de nuevo.');
      set('prog-stage',cfg.name+' separando '+cfg.stems+'…');
      log('Procesando con el modelo local; el tiempo depende de la duración del audio y del CPU.','cl');
      const response=await fetch('/api/separate-stems',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({audio_id:S.audioId,model:S.model,params:S.params}),
      });
      const result=await response.json();
      if(!response.ok)throw new Error([result.error,result.details].filter(Boolean).join(' '));
      S.stemsId=result.stems_id;
      S.stems=Object.fromEntries(result.stems.map(stem=>[stem.key,stem]));
      S.processed=true;
      renderStems(result.stems);
      set('prog-stage',cfg.name+' completado');
      set('prog-pct','100%');
      const bar=document.getElementById('prog-bar');
      bar.classList.remove('indeterminate');
      bar.style.width='100%';
      set('gpu-name','Motor: '+(result.execution_device||'listo'));
      const deviceNote=result.execution_device?` (${result.execution_device})`:'';
      log(`${result.stems.length} stems reales generados en ${result.processing_time}s${deviceNote}.`,'cl-ok');
      log('Resultados disponibles: '+result.stems.map(stem=>stem.name).join(', '),'cl-ok');
      addHist('Procesar: '+cfg.name);
    }catch(error){
      const bar=document.getElementById('prog-bar');
      bar.classList.remove('indeterminate');
      bar.style.width='0%';
      set('prog-stage','Error de procesamiento');
      set('prog-pct','—');
      warn(error.message||'Falló el procesamiento de audio.');
    }finally{
      S.processing=false;
      btn.disabled=false;
      btn.textContent='▶  Procesar';
    }
  }

  /* ── MODEL / MODE ─────────────────────────────────────── */
  function selectModel(el, m) {
    if(!MODELS[m]){warn('Este modelo todavía no está integrado.');return;}
    if(S.processing){warn('Espera a que termine el procesamiento para cambiar de modelo.');return;}
    if(m===S.model)return;
    if(S.processed&&S.stemsId){
      const previousStemsId=S.stemsId;
      pausePlayers();
      clearStemPlayers();
      S.processed=false;
      S.stemsId=null;
      S.stems={};
      S.waveforms=S.waveforms.slice(0,1);
      resetStemDisplay();
      drawAllWaves();
      set('prog-stage','En espera');
      set('prog-pct','—');
      const bar=document.getElementById('prog-bar');
      bar.classList.remove('indeterminate');
      bar.style.width='0%';
      cleanupBackend(null,previousStemsId).catch(error=>warn(error.message));
      log('Resultados anteriores limpiados para reprocesar con otro modelo.','cl');
    }
    document.querySelectorAll('.model-card').forEach(c=>{
      c.classList.remove('sel','sel-gold');
    });
    el.classList.add(m==='mdx'?'sel':'sel-gold');
    S.model=m;
    const cfg=MODELS[m];
    log('Modelo: '+cfg.name,'cl-info');
    document.getElementById('sb-model').textContent=cfg.name;
    document.querySelector('#sel-stems option').textContent=cfg.stems;
  }

  function setMode(m){
    if(m!=='stems'){warn('Este modo todavía no está integrado; el procesamiento disponible es Separación UVR5.');return;}
    ['stems','denoise','eq','pitch'].forEach(id=>{
      document.getElementById('tb-'+id)?.classList.remove('active');
    });
    document.getElementById('tb-'+m)?.classList.add('active');
    S.mode=m;
    const names={stems:'Separación de Stems',denoise:'Reducción de Ruido',eq:'Ecualizador',pitch:'Corrección de Pitch'};
    document.getElementById('sb-mode').textContent=names[m]||m;
    log('Modo: '+names[m],'cl');
  }

  /* ── SLIDER ───────────────────────────────────────────── */
  function slid(el, dispId, key, suffix='') {
    const val=parseInt(el.value);
    S.params[key]=val;
    set(dispId, val+suffix);
    const min=parseInt(el.min),max=parseInt(el.max);
    const pct=((val-min)/(max-min)*100)+'%';
    el.parentElement.style.setProperty('--pct',pct);
  }

  /* ── TRACK CONTROLS ───────────────────────────────────── */
  function mute(idx, btn){
    S.mute[idx]=!S.mute[idx];
    btn.classList.toggle('muted',S.mute[idx]);
    applyPlaybackVolume();
    log(NAMES[idx]+': '+(S.mute[idx]?'MUTED':'UNMUTED'),'cl');
  }
  function solo(idx, btn){
    S.solo[idx]=!S.solo[idx];
    btn.classList.toggle('soloed',S.solo[idx]);
    applyPlaybackVolume();
    log('SOLO '+NAMES[idx]+': '+(S.solo[idx]?'ON':'OFF'),'cl');
  }
  function vol(idx, el){
    S.vol[idx]=parseInt(el.value);
    applyPlaybackVolume();
  }

  /* ── ZOOM ─────────────────────────────────────────────── */
  function zoom(){ warn('El zoom de la línea de tiempo todavía no está integrado.'); }
  function zoomFit(){ warn('El ajuste de zoom todavía no está integrado.'); }

  /* ── EXPORT / DOWNLOAD ────────────────────────────────── */
  function exportAll(){
    if(!S.processed||!S.stemsId){warn('Procesa el audio con el modelo seleccionado antes de exportar.');return;}
    downloadFile('/api/download-stems/'+encodeURIComponent(S.stemsId),'MC_Audio_Stems.zip');
  }
  function exportStem(t){ dlStem(t==='inst'?'instrumental':t); }
  function exportProject(){ warn('La exportación de proyectos .mcproj todavía no está integrada.'); }
  function dlStem(t){
    const key=t==='inst'?'instrumental':t;
    if(!S.processed||!S.stemsId||!S.stems[key]){warn('Ese stem no está disponible en los resultados actuales.');return;}
    const query=new URLSearchParams({stems_id:S.stemsId,stem_name:key,format:'wav'});
    downloadFile('/api/export-stem?'+query.toString(),S.stems[key].filename);
  }

  function downloadFile(url,fallbackName){
    const link=document.createElement('a');
    link.href=url;
    link.download=fallbackName;
    link.style.display='none';
    document.body.appendChild(link);
    link.click();
    link.remove();
    log('Solicitando descarga: '+fallbackName,'cl');
  }

  function clearStemPlayers(){
    for(const player of stemPlayers.values()){
      player.pause();
      player.removeAttribute('src');
      player.load();
    }
    stemPlayers.clear();
  }

  function resetStemDisplay(){
    document.querySelectorAll('.stem-row[data-stem-key]').forEach(row=>{
      row.style.display='none';
      const button=row.querySelector('.stem-dl');
      if(button)button.disabled=true;
      const value=row.querySelector('.stem-pct');
      if(value)value.textContent='—';
    });
    document.querySelectorAll('.track[data-stem-key]').forEach(track=>{
      track.style.display='none';
      track.querySelectorAll('button,input').forEach(control=>{control.disabled=true;});
    });
    set('sdr-main','—');
    set('sdr-unit','SDR no calculado: se requiere una referencia limpia.');
    set('sdr-grade','');
    document.getElementById('sdr-grade').style.display='none';
  }

  function renderStems(stems){
    clearStemPlayers();
    resetStemDisplay();
    for(const stem of stems){
      const trackIndex=STEM_TRACKS[stem.key];
      if(trackIndex===undefined)continue;
      S.waveforms[trackIndex]=stem.waveform;
      const row=document.querySelector(`.stem-row[data-stem-key="${stem.key}"]`);
      if(row){
        row.style.display='';
        const value=row.querySelector('.stem-pct');
        if(value)value.textContent='WAV';
        const button=row.querySelector('.stem-dl');
        if(button)button.disabled=false;
      }
      const track=document.getElementById('tr'+trackIndex);
      if(track){
        track.style.display='';
        track.querySelectorAll('button,input').forEach(control=>{control.disabled=false;});
      }
      const player=new Audio(`/api/stem-audio/${encodeURIComponent(S.stemsId)}/${encodeURIComponent(stem.key)}`);
      player.preload='auto';
      player.addEventListener('loadedmetadata',()=>setPlayerTime(player,S.time),{once:true});
      stemPlayers.set(stem.key,player);
    }
    applyPlaybackVolume();
    drawAllWaves();
  }

  /* ── HISTORY / UNDO ───────────────────────────────────── */
  function addHist(a){
    S.history.splice(S.histIdx+1);
    S.history.push(a); S.histIdx=S.history.length-1;
    if(S.history.length>12) S.history.shift();
    renderHist();
  }
  function renderHist(){
    const el=document.getElementById('hist-list');
    if(!S.history.length){el.innerHTML='<div style="font-size:10px;color:var(--text4);padding:4px 6px;font-family:var(--mono)">Sin acciones</div>';return;}
    el.innerHTML=[...S.history].reverse().slice(0,8).map(a=>`<div class="hist-item">${a}</div>`).join('');
  }
  function undo(){ warn('Deshacer todavía no está integrado.'); }
  function redo(){ warn('Rehacer todavía no está integrado.'); }

  /* ── KNOB ─────────────────────────────────────────────── */
  function setupKnob(){
    const knob=document.getElementById('knob-master');
    let dragging=false, startY=0, startVal=S.masterVol;
    knob.addEventListener('mousedown',e=>{dragging=true;startY=e.clientY;startVal=S.masterVol;e.preventDefault();});
    document.addEventListener('mousemove',e=>{
      if(!dragging)return;
      const delta=(startY-e.clientY)*0.8;
      S.masterVol=Math.max(0,Math.min(100,startVal+delta));
      const rot=-135+(S.masterVol/100)*270;
      knob.style.setProperty('--rot',rot+'deg');
      knob.nextElementSibling.nextElementSibling.textContent=Math.round(S.masterVol)+'%';
      applyPlaybackVolume();
    });
    document.addEventListener('mouseup',()=>{dragging=false;});
  }

  /* ── VIZ CONTROLS ────────────────────────────────────── */
  function toggleVizOpt(btn){ btn.classList.toggle('on'); }
  function captureSpec(){ warn('La captura de espectrograma no está integrada.'); }

  /* ── MISC ─────────────────────────────────────────────── */
  function save(){ warn('El guardado de proyecto todavía no está integrado.'); }
  function saveAs(){ warn('Guardar como todavía no está integrado.'); }
  function showSettings(){
    if(!desktopBridge){
      warn('La selección de carpeta solo está disponible en la aplicación de escritorio PyQt.');
      return;
    }
    desktopBridge.getDownloadDirectory(currentDirectory=>{
      desktopBridge.chooseDownloadDirectory(currentDirectory,selectedDirectory=>{
        if(selectedDirectory)log('Carpeta de exportación: '+selectedDirectory,'cl-ok');
      });
    });
  }

  function log(msg, cls='cl'){
    const box=document.getElementById('console');
    const now=new Date();
    const ts=String(now.getHours()).padStart(2,'0')+':'+String(now.getMinutes()).padStart(2,'0')+':'+String(now.getSeconds()).padStart(2,'0');
    const d=document.createElement('div');
    d.className=cls; d.textContent='['+ts+'] '+msg;
    box.appendChild(d); box.scrollTop=box.scrollHeight;
    while(box.children.length>100) box.removeChild(box.firstChild);
  }
  function warn(m){ log(m,'cl-warn'); }

  function set(id,v){ const el=document.getElementById(id); if(el) el.textContent=v; }
  function fmtPos(t){ const m=Math.floor(t/60),s=Math.floor(t%60); return m+':'+String(s).padStart(2,'0'); }
  function formatTime(d){ return String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'); }

  /* ── KEYBOARD ────────────────────────────────────────── */
  document.addEventListener('keydown', e=>{
    if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT') return;
    if(e.code==='Space'){e.preventDefault();play();}
    if(e.code==='Home') seek(0);
    if(e.code==='End')  seek(9999);
    if(e.code==='ArrowLeft') seekDelta(e.shiftKey?-1:-5);
    if(e.code==='ArrowRight') seekDelta(e.shiftKey?1:5);
    if((e.ctrlKey||e.metaKey)&&e.code==='KeyZ'){e.preventDefault();undo();}
    if((e.ctrlKey||e.metaKey)&&e.code==='KeyY'){e.preventDefault();redo();}
    if((e.ctrlKey||e.metaKey)&&e.code==='KeyO'){e.preventDefault();openFile();}
    if((e.ctrlKey||e.metaKey)&&e.code==='KeyS'){e.preventDefault();save();}
    if(e.code==='Equal'||e.code==='NumpadAdd') zoom(1);
    if(e.code==='Minus'||e.code==='NumpadSubtract') zoom(-1);
  });

  document.addEventListener('DOMContentLoaded', init);
  if(document.readyState!=='loading') init();

  return { openFile, fileChosen, selectModel, setMode, slid, play, seek, seekDelta,
    rulerClick, mute, solo, vol, zoom, zoomFit, process, toggleVizOpt, captureSpec,
    exportAll, exportStem, exportProject, dlStem, undo, redo, save, saveAs, showSettings };

})();
