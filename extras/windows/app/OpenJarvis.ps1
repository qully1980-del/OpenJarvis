<#
  Lanzador de OpenJarvis como aplicación de escritorio (Windows).

  - Arranca Ollama y el servidor de OpenJarvis en segundo plano (sin ventanas).
  - Abre la interfaz en una ventana de aplicación de Edge: sin barra de
    direcciones ni pestañas, con su propio icono en la barra de tareas.
  - Al cerrar la ventana, detiene el servidor (solo si lo arrancó este lanzador).

  Se ejecuta desde OpenJarvis.vbs para que no aparezca ninguna consola.
  Crea los accesos directos con ..\instalar-accesos-directos.ps1.
#>
$ErrorActionPreference = 'SilentlyContinue'

$appDir     = $PSScriptRoot
$repo       = (Resolve-Path (Join-Path $appDir '..\..\..')).Path
$jarvis     = Join-Path $repo '.venv\Scripts\jarvis.exe'
$port       = if ($env:OPENJARVIS_PORT) { $env:OPENJARVIS_PORT } else { '8000' }
$health     = "http://127.0.0.1:$port/health"
$appProfile = Join-Path $env:USERPROFILE '.openjarvis\app-profile'
$logDir     = Join-Path $env:USERPROFILE '.openjarvis\logs'
New-Item -ItemType Directory -Force $logDir, $appProfile | Out-Null

function Test-Url($u) {
    try { Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 2 | Out-Null; $true } catch { $false }
}

# Una sola instancia gestiona el servidor. Si ya hay otra, solo abrimos ventana.
$mutex = New-Object System.Threading.Mutex($false, 'Local\OpenJarvisLauncher')
$owner = $mutex.WaitOne(0)

$edge = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

$splash = 'file:///' + ((Join-Path $appDir 'splash.html') -replace '\\', '/') + "?port=$port"
$edgeArgs = @(
    "--app=$splash",
    "--user-data-dir=`"$appProfile`"",
    '--no-first-run', '--no-default-browser-check',
    '--window-size=1440,920',
    '--disable-features=Translate'
)

if (-not $owner) {
    Start-Process $edge -ArgumentList $edgeArgs
    exit 0
}

$startedServer = $null
try {
    # 1. Ollama (modelo local)
    if (-not (Test-Url 'http://127.0.0.1:11434/api/version')) {
        $ollamaApp = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama app.exe'
        if (Test-Path $ollamaApp) { Start-Process $ollamaApp -WindowStyle Hidden }
    }

    # 2. Servidor de OpenJarvis (si no está ya en marcha)
    if (-not (Test-Url $health)) {
        $env:PYTHONIOENCODING = 'utf-8'
        $startedServer = Start-Process -FilePath $jarvis -ArgumentList 'serve', '--port', $port `
            -WorkingDirectory $repo -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $logDir 'app-server.log') `
            -RedirectStandardError  (Join-Path $logDir 'app-server.err.log')
    }

    # 3. Ventana de la app (la pantalla de carga espera al servidor y entra sola)
    $win = Start-Process $edge -ArgumentList $edgeArgs -PassThru
    $win.WaitForExit()

    # Edge puede delegar en un proceso ya abierto con el mismo perfil: esperamos
    # a que no quede ningún Edge usando el perfil de la app.
    do {
        Start-Sleep -Seconds 2
        $alive = Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
            Where-Object { $_.CommandLine -like '*app-profile*' }
    } while ($alive)
}
finally {
    if ($startedServer) {
        & taskkill.exe /PID $startedServer.Id /T /F | Out-Null
    }
    $mutex.ReleaseMutex() | Out-Null
}
