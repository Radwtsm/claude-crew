# Toglie da Windows tutto ciò che Pleyades tools e l'app Pleiadi hanno messo, anche da un'installazione a metà:
# non serve Python né pleyades-cli funzionante. Si lancia da Impostazioni → App → «Pleyades tools» → Disinstalla
# (la voce la scrive installa.ps1 per prima cosa) oppure con la riga in PowerShell:
#   irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/disinstalla.ps1 | iex
# PLEYADES_SI=1 non chiede; PLEYADES_PROVA=1 elenca soltanto. Restano Git, Python, Claude Code, gh e i progetti
# clonati (programmi generici, forse usati anche per altro): alla fine come toglierli a mano.
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$ErrorActionPreference = 'SilentlyContinue'

$Crew = Join-Path $HOME '.crew'
$Bin = Join-Path $HOME '.local\bin'
$Voce = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\PleyadesTools'
$Copia = Join-Path $env:LOCALAPPDATA 'Pleyades'  # dove installa.ps1 mette questo file per la voce in Impostazioni
$Prova = $env:PLEYADES_PROVA -eq '1'

function App-Pleiadi {  # la voce «Uninstall» dell'installer NSIS dell'app (per l'utente)
    Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' |
        Get-ItemProperty | Where-Object { $_.DisplayName -eq 'Pleiadi' } | Select-Object -First 1
}
function Credenziali {  # solo le voci di Pleyades: pleyades-studio:<utente> (CLI, talk.py), <utente>.Pleiadi Studio (app)
    cmdkey /list | ForEach-Object { if ("$_" -match ':\s*(?:target=)?(\S.*\S)\s*$') { $Matches[1] } } |
        Where-Object { $_ -match '^(LegacyGeneric:target=)?(pleyades-studio:|Pleyades tools: studio)|\.Pleiadi Studio$' }
}
function Comandi {  # i lanciatori di ~/.local/bin che aprono ~/.crew/crew.py (pleyades-cli, pley, comandi dei progetti)
    Get-ChildItem $Bin -Filter *.cmd | Where-Object { $_.Length -lt 2000 -and (Get-Content $_.FullName -Raw) -like "*$Crew\crew.py*" }
}
function Avvio-Pleiadi {  # l'avvio automatico dell'app (plugin autostart di Tauri: valore in HKCU\...\Run)
    $k = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    (Get-ItemProperty $k).PSObject.Properties | Where-Object { "$($_.Value)" -like '*pleiadi.exe*' } | ForEach-Object { $_.Name }
}
function Icone {
    @([Environment]::GetFolderPath('Desktop'), "$HOME\Desktop", "$HOME\OneDrive\Desktop",
      [Environment]::GetFolderPath('Programs')) | Select-Object -Unique |
        ForEach-Object { Join-Path $_ 'Pleyades tools.lnk' } | Where-Object { Test-Path $_ }
}
function Cartelle {
    @($Crew, "$HOME\.config\crew", "$HOME\.config\agenzia", "$env:APPDATA\Pleiadi", "$env:APPDATA\studio.pleiadi.app",
      "$env:LOCALAPPDATA\studio.pleiadi.app") | Where-Object { Test-Path $_ }
}

function Elenco {
    $v = @()
    if (schtasks /Query /TN 'Pleyades tools' 2>$null) { $v += 'attività pianificata «Pleyades tools» (ogni 5 minuti)' }
    if (App-Pleiadi) { $v += "app Pleiadi $((App-Pleiadi).DisplayVersion)" }
    if (Avvio-Pleiadi) { $v += 'avvio automatico di Pleiadi' }
    $c = @(Credenziali); if ($c) { $v += "$($c.Count) voci in Gestione credenziali (accesso allo studio)" }
    $m = @(Comandi); if ($m) { $v += "comandi $(($m | ForEach-Object { $_.BaseName }) -join ', ')" }
    if (Get-Command claude) { $v += 'plugin e cataloghi di Pleyades in Claude Code' }
    $i = @(Icone); if ($i) { $v += 'icona «Pleyades tools»' }
    Cartelle | ForEach-Object { $v += $_.Replace($HOME, '~') }
    if (Test-Path $Voce) { $v += 'la voce «Pleyades tools» in Impostazioni → App' }
    return $v
}

function Togli {
    # 1. niente che riparta a metà: attività, giri di auto in corso, app aperta
    schtasks /End /TN 'Pleyades tools' 2>$null | Out-Null
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*\.crew\crew.py*" -and $_.ProcessId -ne $PID } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Get-Process pleiadi | Stop-Process -Force
    # 2. con pleyades-cli che funziona: le sue parti fini (terminale e colori com'erano, chiavi in settings.json di
    #    Claude), che solo lui sa rimettere; poi qui il resto, che c'è o no
    $py = (Get-Command python).Source
    if ($py -and $py -notlike '*WindowsApps*' -and (Test-Path "$Crew\crew.py")) {
        Write-Host '… pleyades-cli disinstalla' -ForegroundColor Cyan
        & $py "$Crew\crew.py" disinstalla --si | Out-Host
    }
    schtasks /Delete /TN 'Pleyades tools' /F 2>$null | Out-Null
    $app = App-Pleiadi
    if ($app) {
        Write-Host "… app Pleiadi $($app.DisplayVersion)" -ForegroundColor Cyan
        $u = "$($app.UninstallString)".Trim('"')
        if (Test-Path $u) { Start-Process $u -ArgumentList '/S' -Wait }
    }
    $k = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    Avvio-Pleiadi | ForEach-Object { Remove-ItemProperty $k -Name $_ }
    Credenziali | ForEach-Object { cmdkey "/delete:$_" | Out-Null }
    if (Get-Command claude) {  # togliere il catalogo toglie anche i suoi plugin
        Write-Host '… plugin di Pleyades in Claude Code' -ForegroundColor Cyan
        foreach ($m in 'claude-crew', 'agenzia-crew') { @() | claude plugin marketplace remove $m 2>&1 | Out-Null }
    }
    Comandi | Remove-Item -Force
    if (-not (Get-ChildItem $Bin)) {  # ~/.local/bin vuota: via anche dalla PATH utente (claude o gh dentro: resta)
        $p = [Environment]::GetEnvironmentVariable('Path', 'User')
        $n = (($p -split ';') | Where-Object { $_ -and $_ -ne $Bin }) -join ';'
        if ($n -ne $p) { [Environment]::SetEnvironmentVariable('Path', $n, 'User') }
        Remove-Item $Bin
    }
    Icone | Remove-Item -Force
    Cartelle | ForEach-Object { Remove-Item -Recurse -Force $_ }
    Remove-Item $Voce -Recurse -Force
    if (Test-Path $Copia) {  # questo stesso file può essere lì: lo toglie un cmd staccato, a script finito
        Start-Process cmd -ArgumentList '/c', "ping -n 4 localhost >nul & rmdir /s /q `"$Copia`"" -WindowStyle Hidden
    }
}

$voci = @(Elenco)
Write-Host "`n✦ Pleyades tools · disinstalla$(if ($Prova) { ' · prova: non cambio niente' })" -ForegroundColor Magenta
if (-not $voci) { Write-Host '   niente di Pleyades su questo computer' }
$voci | ForEach-Object { Write-Host "   • $_" }
$fai = $voci -and -not $Prova
if ($fai -and $env:PLEYADES_SI -ne '1') {
    $r = Read-Host "`n   Tolgo tutto questo? [S/N]"
    $fai = "$r".Trim() -match '^(s|si|sì|y|yes)$'
    if (-not $fai) { Write-Host '   Niente tolto.' -ForegroundColor Yellow }
}
if ($fai) {
    Togli
    $resta = @(Elenco) | Where-Object { $_ -notlike '*Impostazioni → App*' -and $_ -notlike '*plugin e cataloghi*' }
    if ($resta) {
        Write-Host "`n⚠️ restano (in uso? riavvia il PC e rilancia):" -ForegroundColor Yellow
        $resta | ForEach-Object { Write-Host "   • $_" }
    } else { Write-Host "`n✓ tolto tutto" -ForegroundColor Green }
}
Write-Host "`nRestano (programmi generici, non li tocco):"
Write-Host '   • Claude Code: Remove-Item ~\.local\bin\claude.exe; Remove-Item -Recurse ~\.local\share\claude, ~\.claude'
Write-Host '   • Git e Python: winget uninstall --id Git.Git, poi Python.Python.3.12; GitHub CLI: ~\.local\bin\gh.exe'
Write-Host '   • progetti clonati in ~\code: cancella le cartelle che non servono più'
if ($env:PLEYADES_PAUSA -eq '1') { Read-Host "`nInvio per chiudere" | Out-Null }  # da Impostazioni: la finestra resta
