# ============================================
#  INSTALADOR UVR5-UI DESDE ZIP (FUNCIONAL)
#  MC SERVICES
# ============================================

$base = $PSScriptRoot
$repo = "$base\ultimatevocalremover_gui"
$zipPath = "$base\UVR5-UI-main.zip"
$tempExtract = "$base\uvr5_ui_temp"

Write-Host "=== Instalando UVR5-UI desde ZIP ==="

# 1) Verificar ZIP
if (!(Test-Path $zipPath)) {
    Write-Host "ERROR: No se encontró UVR5-UI-main.zip junto a este instalador."
    exit
}

# 2) Extraer ZIP
Write-Host "Extrayendo ZIP..."
if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
Expand-Archive -Path $zipPath -DestinationPath $tempExtract -Force

# 3) Copiar archivos al proyecto
Write-Host "Copiando archivos..."
if (!(Test-Path $repo)) { New-Item -ItemType Directory -Path $repo | Out-Null }
Copy-Item "$tempExtract\*" $repo -Recurse -Force

# 4) Borrar carpeta temporal
Remove-Item $tempExtract -Recurse -Force

# 5) Activar entorno
Write-Host "Activando entorno..."
& "$repo\uvr_env\Scripts\activate.ps1"

# 6) Instalar dependencias
Write-Host "Instalando dependencias..."
pip install -r "$repo\requirements.txt"

# 7) Ejecutar UVR5-UI
Write-Host "=== UVR5-UI listo ==="
python "$repo\app.py"
