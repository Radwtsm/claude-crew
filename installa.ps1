# La riga unica su Windows (PowerShell): installa Git e Python se mancano, scarica la guida `pleyades-cli` (Pleyades tools) e la lancia.
#   irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Con un progetto a cui sei stato invitato:
#   $env:PROGETTO='PROPRIETARIO/REPO'; $env:STUDIO='studio.nome.org'; irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Tutto il resto (Claude Code, GitHub, plugin, progetti, Nextcloud) lo fa crew.py, uguale su Mac, Linux e Windows.
[Console]::OutputEncoding = [Text.Encoding]::UTF8

function Ha($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Aggiorna-Path {  # what winget just installed, without opening a new window
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User') + ";$HOME\.local\bin"
}
function Python-Vero {  # 'python' of the Microsoft Store is only a stub that opens the Store
    $p = (Get-Command python -ErrorAction SilentlyContinue).Source
    return ($p -and $p -notlike '*WindowsApps*')
}

function Avvia {
    if (-not ((Ha git) -and (Python-Vero))) {
        if (-not (Ha winget)) {
            Write-Host "❌ manca winget: Microsoft Store → cerca «Programma di installazione app» → «Aggiorna», poi rilancia" -ForegroundColor Red
            return
        }
        Write-Host "… installo Git e Python (winget), qualche minuto" -ForegroundColor Cyan
        if (-not (Ha git)) { winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements | Out-Null }
        if (-not (Python-Vero)) { winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements | Out-Null }
        Aggiorna-Path
    }
    if (-not ((Ha git) -and (Python-Vero))) {
        Write-Host "❌ Git o Python non trovati: chiudi PowerShell, riaprilo e incolla di nuovo la stessa riga" -ForegroundColor Red
        return
    }
    $dir = Join-Path $HOME '.crew'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $crew = Join-Path $dir 'crew.py'
    try {
        Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py -OutFile "$crew.tmp"
        Move-Item -Force "$crew.tmp" $crew
    } catch {
        Write-Host "❌ non riesco a scaricare la guida: controlla internet e rilancia la stessa riga" -ForegroundColor Red
        return
    }
    $argomenti = @('guida')
    if ($env:PROGETTO) { $argomenti += $env:PROGETTO }
    if ($env:STUDIO) { $argomenti += "--studio=$env:STUDIO" }
    python $crew @argomenti
}

Avvia
