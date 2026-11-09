# MC Audio Pro Studio v2.4.1 — Interfaz Desktop

## Iniciar
Abre `index.html` en Chrome, Edge o Firefox. No requiere instalación.

## Atajos de teclado
| Tecla | Acción |
|-------|--------|
| Espacio | Play / Pausa |
| Home / End | Ir a inicio / fin |
| ← → | Navegar ±5s |
| Shift + ← → | Navegar ±1s |
| Ctrl+Z / Y | Deshacer / Rehacer |
| Ctrl+O | Abrir archivo |
| Ctrl+S | Guardar proyecto |
| + / - | Zoom in / out |

## Estructura
```
mc-audio-pro/
├── index.html   ← Punto de entrada
├── js/app.js    ← Lógica completa
└── README.md
```

## Modelos IA integrados
- **MDX-Net UVR5** — Separación espectral de alta precisión
- **Demucs v4 htdemucs_ft** — 4 stems en dominio de tiempo  
- **UVR-MDX-NET Vocal** — Limpieza vocal + dereverb
- **Demucs 6-Stem** — Guitar · Piano · Bass · Drums · Vocals · Other
