<#
  Crea los accesos directos de OpenJarvis en el escritorio y en el menú Inicio.
  Uso:  powershell -ExecutionPolicy Bypass -File extras\windows\instalar-accesos-directos.ps1
#>
$app = Join-Path $PSScriptRoot 'app'
$sh  = New-Object -ComObject WScript.Shell
$destinos = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop'))  'OpenJarvis.lnk'),
    (Join-Path ([Environment]::GetFolderPath('Programs')) 'OpenJarvis.lnk')
)
foreach ($d in $destinos) {
    $l = $sh.CreateShortcut($d)
    $l.TargetPath       = Join-Path $env:WINDIR 'System32\wscript.exe'
    $l.Arguments        = '"' + (Join-Path $app 'OpenJarvis.vbs') + '"'
    $l.WorkingDirectory = $app
    $l.IconLocation     = (Join-Path $app 'OpenJarvis.ico') + ',0'
    $l.Description      = 'OpenJarvis · asistente personal de IA'
    $l.Save()
    Write-Host "Creado: $d"
}
