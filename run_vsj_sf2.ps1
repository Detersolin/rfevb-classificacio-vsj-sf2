# Executa el scraper amb un entorn virtual al mateix repo i actualitza dependències
param(
  [string]$RepoDir = "C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2\rfevb-classificacio-vsj-sf2"
)

$ErrorActionPreference = "SilentlyContinue"

if (Test-Path $RepoDir) {
  Set-Location $RepoDir
  git pull
} else {
  Write-Host "Repo no trobat a $RepoDir"
  exit 1
}

if (-not (Test-Path ".\.venv")) {
  py -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Assegura la carpeta d'output (on llegirà l'OBS)
New-Item -ItemType Directory -Force -Path "C:\Guillem\Temporada 25-26\Overlay\VSJ\SF2" | Out-Null

# Arrenca el scraper (bucle continu)
.\.venv\Scripts\python.exe .\scrape_vsj_sf2.py
