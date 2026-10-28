# Installa tutto con una riga su Windows (PowerShell). Si può rilanciare: salta ciò che c'è già.
#   irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Con un progetto privato a cui sei stato invitato (lo clona e lancia il suo onboarding.py, se c'è):
#   $env:PROGETTO='PROPRIETARIO/REPO'; irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Fa: Git, Python, GitHub CLI (winget) → Claude Code (installer ufficiale) → crew (solo regole + aggiornamento
# automatico) → progetto. Stessi passi di installa.sh (Mac e Linux).
[Console]::OutputEncoding = [Text.Encoding]::UTF8

function Ok($t) { Write-Host "✅ $t" }
function Ferma($t) { Write-Host "❌ $t"; Write-Host "   Poi rilancia la stessa riga." }
function Ha($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Aggiorna-Path {  # what winget just installed, without opening a new window
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User') + ";$HOME\.local\bin"
}
function Python-Vero {  # 'python' of the Microsoft Store is only a stub that opens the Store
    $p = (Get-Command python -ErrorAction SilentlyContinue).Source
    return ($p -and $p -notlike '*WindowsApps*')
}

function Installa {
    if (-not (Ha winget)) { Ferma "manca winget: Microsoft Store → aggiorna 'Programma di installazione app'"; return }
    foreach ($p in @(@('git', 'Git.Git'), @('gh', 'GitHub.cli'))) {
        if (-not (Ha $p[0])) { winget install --id $p[1] -e --silent --accept-package-agreements --accept-source-agreements | Out-Null }
    }
    if (-not (Python-Vero)) {
        winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
    }
    Aggiorna-Path
    if (-not ((Ha git) -and (Python-Vero))) { Ferma "Git o Python non installati: chiudi e riapri PowerShell"; return }
    Ok "Git e Python"

    if (-not (Ha claude)) { Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression; Aggiorna-Path }
    if (-not (Ha claude)) { Ferma "Claude Code installato ma non trovato: chiudi e riapri PowerShell"; return }
    Ok "Claude Code"

    # HTTPS for the plugins (no GitHub SSH key) and crew auto-update, without touching the rest
    $imp = Join-Path $env:TEMP 'crew-impostazioni.py'
    @'
import json, os, sys
p = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
try:
    s = json.load(open(p, encoding="utf-8"))
except (OSError, ValueError):
    s = {}
s.setdefault("env", {})["CLAUDE_CODE_PLUGIN_PREFER_HTTPS"] = "1"
for nome in sys.argv[1:]:
    m = s.get("extraKnownMarketplaces", {}).get(nome)
    if isinstance(m, dict):
        m["autoUpdate"] = True
json.dump(s, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
'@ | Set-Content -Encoding UTF8 $imp
    python $imp
    if (-not ((claude plugin marketplace list 2>$null) -match 'claude-crew')) { claude plugin marketplace add Radwtsm/claude-crew | Out-Null }
    if (-not ((claude plugin list 2>$null) -match 'regole@claude-crew')) { claude plugin install regole@claude-crew | Out-Null }
    python $imp claude-crew  # `marketplace add` removes autoUpdate: put it back
    if (-not ((claude plugin list 2>$null) -match 'regole@claude-crew')) { Ferma "plugin della crew non installati"; return }
    Ok "crew (regole) con aggiornamento automatico; gli strumenti del tuo mestiere: in Claude «aggiorna la crew»"

    $progetto = $env:PROGETTO
    if (-not $progetto) { Ok "fatto: apri Claude Code (claude) e scrivi «configura il mio Claude»"; return }

    gh auth status 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Accesso a GitHub: premi Invio, si apre il browser. Senza account: nella pagina premi «Create an account»,"
        Write-Host "crealo (gratis), poi torna qui e rilancia la stessa riga."
        gh auth login --web --git-protocol https
        if ($LASTEXITCODE -ne 0) { Ferma "accesso a GitHub non riuscito"; return }
    }
    Ok "GitHub"

    $dir = Join-Path $HOME ($progetto.Split('/')[1])
    if (-not (Test-Path (Join-Path $dir '.git'))) {
        gh repo clone $progetto $dir 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $io = gh api user -q .login 2>$null
            if ($io -and $io.ToLower() -eq $progetto.Split('/')[0].ToLower()) { Ferma "il repo $progetto non esiste: controlla il nome (è tuo)"; return }
            Ferma "non vedo $progetto. Manda il tuo nome GitHub «$io» a chi ti ha invitato, poi accetta l'invito per mail"
            return
        }
    }
    Ok "progetto in $dir"
    $onb = Get-ChildItem -Path $dir -Recurse -Depth 3 -Filter onboarding.py -ErrorAction SilentlyContinue |
           Where-Object { $_.FullName -notmatch '\\\.git\\' } | Select-Object -First 1
    if ($onb) { python $onb.FullName } else { Ok "fatto: apri Claude Code nella cartella $dir e scrivi «controlla il mio setup»" }
}

Installa
