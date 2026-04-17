# push_videos.ps1
# Copia todos los videos de jugadores al dispositivo Android.
# Ejecutar con: .\push_videos.ps1

$VIDEOS_DIR = "$PSScriptRoot\videos"
$DEVICE_DIR = "/sdcard/stadiumv2/videos"

Write-Host "=== Stadium v2 - Push Videos ===" -ForegroundColor Cyan
Write-Host ""

# Verificar que adb esta disponible
$adb = "adb"
if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
    $adbFallback = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
    if (Test-Path $adbFallback) {
        $adb = $adbFallback
        Write-Host "[INFO] Usando adb desde: $adb" -ForegroundColor DarkCyan
    } else {
        Write-Host "[ERROR] 'adb' no encontrado. Agrega Android SDK platform-tools al PATH." -ForegroundColor Red
        exit 1
    }
}

# Verificar dispositivo conectado
$devices = & $adb devices | Select-String "device$"
if (-not $devices) {
    Write-Host "[ERROR] No hay dispositivo Android conectado. Conecta el tablet y habilita depuracion USB." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Dispositivo detectado." -ForegroundColor Green

# Crear directorio en el dispositivo
Write-Host "Creando directorio en el dispositivo: $DEVICE_DIR"
& $adb shell "mkdir -p $DEVICE_DIR"

# Copiar cada video
$videos = Get-ChildItem -Path $VIDEOS_DIR -Filter "*.mov"
if ($videos.Count -eq 0) {
    Write-Host "[AVISO] No se encontraron archivos .mov en $VIDEOS_DIR" -ForegroundColor Yellow
    exit 0
}

foreach ($video in $videos) {
    $sizeMB = [math]::Round($video.Length / 1MB, 1)
    Write-Host "Copiando $($video.Name) ($sizeMB MB)..." -ForegroundColor Yellow
    & $adb push "$($video.FullName)" "$DEVICE_DIR/$($video.Name)"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $($video.Name)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Fallo al copiar $($video.Name)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Videos en el dispositivo ===" -ForegroundColor Cyan
& $adb shell "ls -lh $DEVICE_DIR"

Write-Host ""
Write-Host "Listo! Los videos estan disponibles en el dispositivo." -ForegroundColor Green
