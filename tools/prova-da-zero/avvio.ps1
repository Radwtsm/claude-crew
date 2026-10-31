# Dentro Windows Sandbox (un Windows nuovo, cancellato alla chiusura): fa ciò che fa un collega con la riga di
# INSTALLA.md e scrive tutto in C:\prova\esito. Lo lancia tools/prova_da_zero.py; a mano: doppio clic su prova.wsb.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$esito = 'C:\prova\esito'
New-Item -ItemType Directory -Force -Path $esito | Out-Null
function Passo($nome) { "$(Get-Date -Format HH:mm:ss) $nome" | Add-Content -Encoding UTF8 "$esito\passi.txt" }

# Bug della Sandbox (24H2+, Windows-Sandbox#68/#85): Smart App Control acceso con Defender spento fa bloccare ogni
# MSI sulla verifica (Python, a «File will have security applied from OpCode»). Un PC vero ha Defender: non succede
Set-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy VerifiedAndReputablePolicyState 0
'' | CiTool.exe -r | Out-Null  # chiede Invio

# La Sandbox non ha winget, un PC vero sì: i pacchetti delle release Microsoft (come nella guida Microsoft per la
# Sandbox), tenuti in C:\cache sul PC per 7 giorni. Niente API di GitHub: a prove ripetute dà «rate limit exceeded»
Passo 'winget'
try {
    $rel = 'https://github.com/microsoft/winget-cli/releases/latest/download'
    foreach ($f in 'Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle', 'DesktopAppInstaller_Dependencies.zip') {
        $c = Get-Item "C:\cache\$f" -ErrorAction SilentlyContinue
        if (-not $c -or $c.LastWriteTime -lt (Get-Date).AddDays(-7)) {
            Invoke-WebRequest -UseBasicParsing "$rel/$f" -OutFile "C:\cache\$f.tmp"
            Move-Item -Force "C:\cache\$f.tmp" "C:\cache\$f"
        }
    }
    Expand-Archive -Force C:\cache\DesktopAppInstaller_Dependencies.zip "$env:TEMP\dip"
    Get-ChildItem "$env:TEMP\dip" -Recurse -Filter *.appx | Where-Object FullName -match 'x64' |
        ForEach-Object { Add-AppxPackage $_.FullName }
    Add-AppxPackage C:\cache\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle
} catch { Passo "winget: $_" }
$env:Path += ";$env:LOCALAPPDATA\Microsoft\WindowsApps"
Passo "winget $(winget --version 2>&1)"

# Ogni 10 s i processi vivi (con la riga di comando) e i log degli installer: se un passo si blocca si vede su cosa
# aspetta. Installer vivo e log fermi da 2 min = «fermo» in passi.txt: il lanciatore chiude subito, niente 20 min persi
Start-Job -ArgumentList $esito {
    param($esito)
    $peso, $da = -1, (Get-Date)
    while ($true) {
        "== $(Get-Date -Format HH:mm:ss)" | Add-Content -Encoding UTF8 "$esito\processi.txt"
        Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'winget|msiexec|setup|install|git|python|consent|tmp' } |
            ForEach-Object { "$($_.Name) · $("$($_.CommandLine)".Substring(0, [Math]::Min(400, "$($_.CommandLine)".Length)))" } |
            Add-Content -Encoding UTF8 "$esito\processi.txt"
        # log degli installer (winget fa scrivere quello di Python in DiagOutputDir): si vede dove si ferma
        $diag = "$env:LOCALAPPDATA\Packages\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\LocalState\DiagOutputDir"
        Get-ChildItem $env:TEMP, $diag -Recurse -Include *.log -ErrorAction SilentlyContinue | Where-Object Length -lt 5MB |
            ForEach-Object {
                # chi lo scrive lo tiene aperto: Copy-Item fallisce, serve lettura con condivisione ReadWrite
                New-Item -ItemType Directory -Force "$esito\log" | Out-Null
                try { $f = [IO.File]::Open($_.FullName, 'Open', 'Read', 'ReadWrite')
                      $o = [IO.File]::Create("$esito\log\$($_.Name)"); $f.CopyTo($o); $o.Close(); $f.Close() } catch {}
            }
        $vivi = @(Get-Process python-*, Git-*, *setup* -ErrorAction SilentlyContinue)  # msiexec /V resta vivo da solo
        $ora = (Get-ChildItem "$esito\log" -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
        if ($ora -ne $peso -or -not $vivi) { $peso, $da = $ora, (Get-Date) }
        elseif ((Get-Date) - $da -gt [TimeSpan]::FromMinutes(2)) {
            "$(Get-Date -Format HH:mm:ss) fermo: $(($vivi.Name | Sort-Object -Unique) -join ', ') senza log nuovi da 2 min" |
                Add-Content -Encoding UTF8 "$esito\passi.txt"
            $da = (Get-Date).AddYears(1)  # una volta sola
        }
        # comandi dal Mac mentre la Sandbox gira (prova_da_zero.py --esegui): si itera senza rifare tutto
        if (Test-Path C:\prova\esegui.ps1) {
            Move-Item -Force C:\prova\esegui.ps1 "$env:TEMP\esegui.ps1"
            & "$env:TEMP\esegui.ps1" *>&1 | Out-File -Encoding utf8 "$esito\esegui.txt"
        }
        Start-Sleep 10
    }
} | Out-Null

# La riga del collega (`irm …installa.ps1 | iex`), con le copie di installa.ps1 e crew.py da provare prima del push
# e le risposte di chi non sa nulla: «Mio», niente accesso a Claude (serve il browser), «senza account GitHub», poi
# Invio a tutto. Una domanda nuova sfasa le risposte: un Invio su «Colleghiamo GitHub?» aspetta il browser 15 min
Passo 'installa.ps1'
(Get-Content -Raw -Encoding UTF8 C:\prova\installa.ps1) -replace 'https://raw\.githubusercontent\.com/[^ ]+/crew\.py',
    'file:///C:/prova/crew.py' | Set-Content -Encoding UTF8 "$env:TEMP\installa.ps1"
$risposte = "1`n2`n2`n`n`n`n`n`n`n`n"
$risposte | powershell -NoProfile -ExecutionPolicy Bypass -Command `
    "Get-Content -Raw -Encoding UTF8 $env:TEMP\installa.ps1 | iex" 2>&1 | Out-File -Encoding utf8 "$esito\guida.txt"

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
Get-Job | Wait-Job | Out-Null  # a mano: il controllo (e --esegui) resta vivo finché la Sandbox è aperta
