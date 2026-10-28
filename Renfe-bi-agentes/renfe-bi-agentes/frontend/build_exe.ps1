# Empaqueta el frontend en un .exe de Windows con PyInstaller.
# Uso (desde la raíz de renfe-bi-agentes, con el venv creado):
#   powershell -ExecutionPolicy Bypass -File frontend\build_exe.ps1
#
# Resultado: ..\..\App\RadarCompetitivoAV.exe y, si el .env del proyecto tiene
# SUPABASE_DB_URL, un .env junto al .exe solo con esa variable (sin la clave de Anthropic).

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$py = Join-Path $raiz ".venv\Scripts\python.exe"
$salida = Resolve-Path (Join-Path $raiz "..\..") | ForEach-Object { Join-Path $_ "App" }
$trabajo = Join-Path $env:TEMP "renfe-bi-build"

Push-Location $raiz
try {
    & $py -m pip install -q pyinstaller pywebview "psycopg[binary]" python-dotenv
    & $py -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name RadarCompetitivoAV `
        --distpath $salida --workpath $trabajo --specpath $trabajo `
        --paths $raiz `
        --add-data "$raiz\frontend\static;frontend\static" `
        --add-data "$raiz\data;data" `
        --hidden-import psycopg_binary --collect-all psycopg_binary `
        --collect-all webview `
        frontend\app.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falló" }

    # .env mínimo junto al .exe: solo la conexión a Supabase
    & $py -c @"
from dotenv import dotenv_values
url = dotenv_values(r'$raiz\.env').get('SUPABASE_DB_URL')
if url:
    open(r'$salida\.env', 'w', encoding='utf-8').write('SUPABASE_DB_URL=' + url + '\n')
    print('Creado .env con SUPABASE_DB_URL junto al .exe')
else:
    print('Sin SUPABASE_DB_URL: el .exe usará los CSV incluidos')
"@
    Write-Host "`nListo: $salida\RadarCompetitivoAV.exe"
} finally {
    Pop-Location
}
