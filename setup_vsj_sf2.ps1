# Instal·lació al PC per VSJ SF2: clona/actualitza repo, crea venv, deps i tasca programada
param(
  [string]$RepoURL   = "https://github.com/Detersolin/rfevb-classificacio-vsj-sf2.git",
  [string]$InstallDir= "C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2\rfevb-classificacio-vsj-sf2"
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Cal Git instal·lat (git-scm.com)" }
if (-not (Get-Command py  -ErrorAction SilentlyContinue)) { throw "Cal Python instal·lat (python.org). Marca 'Add Python to PATH'." }

# Clona o actualitza
if (Test-Path $InstallDir) {
  Set-Location $InstallDir
  git pull
} else {
  git clone $RepoURL $InstallDir
  Set-Location $InstallDir
}

# Crea venv i instal·la deps
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Crea la carpeta d’output (la que usarà l’OBS)
New-Item -ItemType Directory -Force -Path "C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2" | Out-Null

# Crea la tasca programada que arrenca el scraper a l'inici de sessió
$taskName = "VSJ_SF2_Classificacio"
$ps1 = Join-Path $InstallDir "run_vsj_sf2.ps1"
$action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ps1`" -RepoDir `"$InstallDir`""
schtasks /Create /TN $taskName /TR $action /SC ONLOGON /RL HIGHEST /F

Write-Host "✔ Instal·lació VSJ SF2 completada. Reinicia sessió o executa ara: $action"
