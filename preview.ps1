$ErrorActionPreference = 'Stop'
$runtimePath = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $runtimePath)) {
    throw 'No se encuentra el Python de vista previa. Sigue la instalación del README con Python 3.10 o posterior.'
}
Push-Location $PSScriptRoot
try {
    & $runtimePath -c "import sys, runpy; sys.path.insert(0, '.deps'); runpy.run_path('app.py', run_name='__main__')"
} finally {
    Pop-Location
}
