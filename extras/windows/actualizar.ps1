<#
  Actualiza OpenJarvis conservando las personalizaciones de esta rama
  (castellano, tema «Aurora», motor Claude Code y lanzador de Windows).

  Uso (con OpenJarvis cerrado):
      powershell -ExecutionPolicy Bypass -File extras\windows\actualizar.ps1

  Qué hace:
    1. Descarga la última versión oficial (upstream/main u origin/main).
    2. Vuelve a aplicar tus cambios encima (git rebase).
    3. Reinstala dependencias de Python (uv sync) y de la interfaz (npm 11).
    4. Recompila la interfaz.
  Si hay un conflicto, se detiene sin perder nada y explica cómo deshacerlo.

  No uses `jarvis self-update` en esta rama: solo hace `git pull --ff-only`.
#>
param([string] $Rama = 'es-aurora')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$uvDir = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe'
if (Test-Path $uvDir) { $env:Path = "$uvDir;$env:Path" }

function Paso($t) { Write-Host "`n==> $t" -ForegroundColor Magenta }

Set-Location $repo
if (git status --porcelain --untracked-files=no) {
    throw "Hay cambios sin guardar en $repo. Haz commit antes de actualizar."
}
$antes = git rev-parse HEAD
# El repositorio oficial puede estar como 'upstream' (si clonaste tu fork) u 'origin'.
$remoto = if (git remote | Select-String -SimpleMatch 'upstream') { 'upstream' } else { 'origin' }

Paso "Descargando la última versión de OpenJarvis ($remoto/main)"
git fetch $remoto --tags
git switch main
git merge --ff-only "$remoto/main"
git switch $Rama

Paso 'Aplicando tus personalizaciones encima'
git rebase main
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nHay un conflicto entre la versión nueva y tus cambios." -ForegroundColor Yellow
    Write-Host "Para dejarlo todo como estaba:  git -C `"$repo`" rebase --abort" -ForegroundColor Yellow
    Write-Host "(Tu versión anterior era $antes.)"
    exit 1
}

Paso 'Instalando dependencias de Python'
uv sync --extra desktop --group desktop-native

Paso 'Instalando dependencias de la interfaz (npm 11)'
Set-Location (Join-Path $repo 'frontend')
npx -y npm@11 ci --no-audit --no-fund

Paso 'Compilando la interfaz'
npm run build
git -C $repo checkout -- frontend/tsconfig.tsbuildinfo 2>$null

Write-Host "`nOpenJarvis actualizado. Ábrelo desde el acceso directo." -ForegroundColor Green
