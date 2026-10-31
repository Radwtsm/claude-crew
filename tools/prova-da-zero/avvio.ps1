# Dentro Windows Sandbox (un Windows nuovo, cancellato alla chiusura): fa ciò che fa un collega con la riga di
# INSTALLA.md e scrive tutto in C:\prova\esito. Lo lancia tools/prova_da_zero.py; a mano: doppio clic su prova.wsb.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$esito = 'C:\prova\esito'
New-Item -ItemType Directory -Force -Path $esito | Out-Null
function Passo($nome) { "$(Get-Date -Format HH:mm:ss) $nome" | Add-Content -Encoding UTF8 "$esito\passi.txt" }

# La Sandbox non ha winget, un PC vero sì: lo si mette come su un PC appena comprato (modulo ufficiale Microsoft)
Passo 'winget'
try {
    Install-PackageProvider -Name NuGet -Force -Scope CurrentUser | Out-Null
    Install-Module Microsoft.WinGet.Client -Force -Scope CurrentUser -Repository PSGallery | Out-Null
    Repair-WinGetPackageManager -Latest -Force | Out-Null
} catch { Passo "winget: $_" }
$env:Path += ";$env:LOCALAPPDATA\Microsoft\WindowsApps"
Passo "winget $(winget --version 2>&1)"

# Ogni 20 s i processi vivi (con la riga di comando): se un passo si blocca si vede su cosa aspetta
Start-Job -ArgumentList $esito {
    param($esito)
    while ($true) {
        "== $(Get-Date -Format HH:mm:ss)" | Add-Content -Encoding UTF8 "$esito\processi.txt"
        Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'winget|msiexec|setup|install|git|python|consent|tmp' } |
            ForEach-Object { "$($_.Name) · $("$($_.CommandLine)".Substring(0, [Math]::Min(150, "$($_.CommandLine)".Length)))" } |
            Add-Content -Encoding UTF8 "$esito\processi.txt"
        Start-Sleep 20
    }
} | Out-Null

# La riga del collega (`irm …installa.ps1 | iex`), con la copia di installa.ps1 da provare prima del push e le
# risposte di chi non sa nulla: «Mio», «senza account GitHub», poi Invio a tutto
Passo 'installa.ps1'
$risposte = "1`n2`n`n`n`n`n`n`n`n`n"
$risposte | powershell -NoProfile -ExecutionPolicy Bypass -Command `
    "Get-Content -Raw -Encoding UTF8 C:\prova\installa.ps1 | iex" 2>&1 | Out-File -Encoding utf8 "$esito\guida.txt"

# Cosa resta da fare secondo la CLI stessa
Passo 'controlla'
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
            [Environment]::GetEnvironmentVariable('Path', 'User') + ";$HOME\.local\bin"
$crew = Join-Path $HOME '.crew\crew.py'
if (Test-Path $crew) {
    '' | python $crew controlla 2>&1 | Out-File -Encoding utf8 "$esito\controlla.txt"
    python $crew passi --json 2>&1 | Out-File -Encoding utf8 "$esito\passi.json"
} else { 'crew.py non scaricato' | Set-Content "$esito\controlla.txt" }
foreach ($p in 'git', 'python', 'claude', 'pleyades-cli') {
    "$p = $((Get-Command $p -ErrorAction SilentlyContinue).Source)" | Add-Content -Encoding UTF8 "$esito\programmi.txt"
}
Passo 'fine'
if (Test-Path 'C:\prova\chiudi') { Stop-Computer -Force }  # automatica: chiude; a mano resta aperta da guardare
