# La riga unica su Windows (PowerShell): per prima cosa la voce «Pleyades tools» in Impostazioni → App (toglie tutto,
# anche da un'installazione a metà: disinstalla.ps1), poi Git e Python se mancano (chiede prima; PLEYADES_SI=1 non chiede), scarica la guida `pleyades-cli` (Pleyades tools) e la lancia.
#   irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Con un progetto a cui sei stato invitato:
#   $env:PROGETTO='PROPRIETARIO/REPO'; $env:STUDIO='studio.nome.org'; irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Con un invito dell'app Pleiadi (la riga del messaggio): il codice in una variabile, mai negli argomenti
#   $env:INVITO='XXXXX-XXXXX-XXXXX-XXXXX'; $env:STUDIO='studio.nome.org'; irm …/installa.ps1 | iex
#   installa solo l'app Pleiadi e la apre col codice (Solo-App); $env:PLEYADES_COMPLETO='1' fa anche il resto (Avvia)
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

function Installa($id) {  # winget's own message if it fails: the colleague can tell us why, not just "missing"
    # --source winget: on a new PC msstore matches too and winget stops asking which one (-1978335173);
    # --scope user first: no admin rights, no UAC prompt (the all-users Python installer hangs waiting for it)
    $w = @('install', '--id', $id, '-e', '--source', 'winget', '--silent', '--accept-package-agreements', '--accept-source-agreements')
    # @() |: stdin vuoto, winget e l'installer non leggono le risposte destinate alla guida (né aspettano un tasto)
    $out = @() | winget @w --scope user 2>&1
    if ($LASTEXITCODE -ne 0) { $out = @() | winget @w 2>&1 }
    if ($LASTEXITCODE -ne 0) {
        $motivo = ($out | ForEach-Object { "$_".Trim() } | Where-Object { $_ -match '\w{3}' } | Select-Object -Last 1)
        Write-Host "⚠️ winget: $id non installato (codice $LASTEXITCODE)" -ForegroundColor Yellow
        if ($motivo) { Write-Host "   $("$motivo".Substring(0, [Math]::Min(75, "$motivo".Length)))" -ForegroundColor Yellow }
    }
}

function Voce-Disinstalla {  # per prima cosa: un'installazione che si blocca a metà si toglie da Impostazioni → App
    $dir = Join-Path $env:LOCALAPPDATA 'Pleyades'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $f = Join-Path $dir 'disinstalla.ps1'
    try { Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/Radwtsm/claude-crew/main/disinstalla.ps1 -OutFile $f }
    catch { return }
    $k = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\PleyadesTools'
    New-Item -Force -Path $k | Out-Null
    $cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command `"`$env:PLEYADES_PAUSA='1'; iex ([IO.File]::ReadAllText('$f'))`""  # UTF-8: con & file PowerShell 5.1 legge ANSI
    @{ DisplayName = 'Pleyades tools'; Publisher = 'Pleyades Studio'; UninstallString = $cmd; NoModify = 1; NoRepair = 1
       DisplayIcon = 'powershell.exe'; InstallLocation = (Join-Path $HOME '.crew') }.GetEnumerator() |
        ForEach-Object { Set-ItemProperty -Path $k -Name $_.Key -Value $_.Value }
}

function Bloccato {
    Write-Host "`nSi è fermato? Rilancia la stessa riga: riparte da dove era.`nPer togliere tutto: Impostazioni → App → «Pleyades tools» → Disinstalla, oppure`n   irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/disinstalla.ps1 | iex" -ForegroundColor Yellow
}

function Avvia {
    Voce-Disinstalla
    if (-not ((Ha git) -and (Python-Vero))) {
        if (-not (Ha winget)) {
            Write-Host "❌ manca winget: Microsoft Store → cerca «Programma di installazione app»`n   → «Aggiorna», poi rilancia la stessa riga" -ForegroundColor Red
            return
        }
        $manca = @(); if (-not (Ha git)) { $manca += 'Git' }; if (-not (Python-Vero)) { $manca += 'Python 3.12' }
        if ($env:PLEYADES_SI -ne '1') {  # PLEYADES_SI=1: chi lancia da script, senza domanda
            Write-Host "→ Mancano $($manca -join ' e '). Li installo con winget (il programma di Microsoft),`n   dai siti ufficiali (Git for Windows, python.org), solo per il tuo utente." -ForegroundColor Cyan
            $r = Read-Host "   Installo? [S/N]"
            if ("$r".Trim() -notmatch '^(s|si|sì|y|yes)$') {
                Write-Host "Niente installato. A mano: git-scm.com e python.org (spunta «Add python.exe to PATH»),`n   poi incolla di nuovo la stessa riga." -ForegroundColor Yellow
                return
            }
        }
        Write-Host "… installo $($manca -join ' e ') (winget), qualche minuto" -ForegroundColor Cyan
        if (-not (Ha git)) { Installa Git.Git }
        if (-not (Python-Vero)) { Installa Python.Python.3.12 }
        Aggiorna-Path
    }
    if (-not ((Ha git) -and (Python-Vero))) {
        Write-Host "❌ Git o Python non trovati: chiudi PowerShell, riaprilo`n   e incolla di nuovo la stessa riga" -ForegroundColor Red
        Bloccato; return
    }
    $dir = Join-Path $HOME '.crew'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $crew = Join-Path $dir 'crew.py'
    try {
        Invoke-WebRequest -UseBasicParsing https://raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py -OutFile "$crew.tmp"
        Move-Item -Force "$crew.tmp" $crew
    } catch {
        Write-Host "❌ non riesco a scaricare la guida: controlla internet e rilancia la stessa riga" -ForegroundColor Red
        Bloccato; return
    }
    $argomenti = @('guida')
    if ($env:PROGETTO) { $argomenti += $env:PROGETTO }
    if ($env:STUDIO) { $argomenti += "--studio=$env:STUDIO" }
    python $crew @argomenti
    if ($LASTEXITCODE -ne 0) { Bloccato }
}

# Con l'invito (A90, owner 02/11): solo l'app, niente Git/Python/winget/domande; il resto (Claude, regole, progetti) si
# prepara dopo, se serve (`PLEYADES_COMPLETO=1` = la guida completa di prima). L'installer ha la firma della squadra (la
# stessa chiave degli aggiornamenti dell'app; minisign «ED» = Ed25519 sul BLAKE2b-512 del file), verificata qui senza
# Python: PowerShell 5.1 non ha né BLAKE2b né Ed25519, quindi poche righe di C# compilate al volo (come crew.py).
$RELEASE_APP = 'https://github.com/Radwtsm/claude-crew' -replace '/claude-crew$', '/pleiadi-app/releases/latest/download'  # come crew.py APP_RELEASE
$CHIAVE_APP = 'RWQ6SfrX2t4h6AgVg+FATkP0040JbE1KiocNGmiZwLc3cJvbNX8JP7x6'  # tauri.conf.json → plugins.updater.pubkey
$FIRMA_CS = @'
using System; using System.Numerics; using System.Security.Cryptography;
public static class FirmaSquadra {
  static readonly ulong[] IV = {0x6a09e667f3bcc908UL,0xbb67ae8584caa73bUL,0x3c6ef372fe94f82bUL,0xa54ff53a5f1d36f1UL,
    0x510e527fade682d1UL,0x9b05688c2b3e6c1fUL,0x1f83d9abfb41bd6bUL,0x5be0cd19137e2179UL};
  static readonly byte[] S = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15, 14,10,4,8,9,15,13,6,1,12,0,2,11,7,5,3,
    11,8,12,0,5,2,15,13,10,14,3,6,7,1,9,4, 7,9,3,1,13,12,11,14,2,6,5,10,4,0,15,8, 9,0,5,7,2,4,10,15,14,1,11,12,6,8,3,13,
    2,12,6,10,0,11,8,3,4,13,7,5,15,14,1,9, 12,5,1,15,14,13,4,10,0,7,6,3,9,2,8,11, 13,11,7,14,12,1,3,9,5,0,15,4,8,6,2,10,
    6,15,14,9,11,3,0,8,12,2,13,7,1,4,10,5, 10,2,8,4,7,6,1,5,15,11,9,14,3,12,13,0};
  static ulong R(ulong x, int n) { return (x >> n) | (x << (64 - n)); }
  static void G(ulong[] v, int a, int b, int c, int d, ulong x, ulong y) {
    v[a] += v[b] + x; v[d] = R(v[d] ^ v[a], 32); v[c] += v[d]; v[b] = R(v[b] ^ v[c], 24);
    v[a] += v[b] + y; v[d] = R(v[d] ^ v[a], 16); v[c] += v[d]; v[b] = R(v[b] ^ v[c], 63); }
  static void F(ulong[] h, byte[] k, ulong t, bool ultimo) {
    var m = new ulong[16]; var v = new ulong[16];
    for (int i = 0; i < 16; i++) m[i] = BitConverter.ToUInt64(k, i * 8);
    for (int i = 0; i < 8; i++) { v[i] = h[i]; v[i + 8] = IV[i]; }
    v[12] ^= t; if (ultimo) v[14] = ~v[14];
    for (int r = 0; r < 12; r++) { int s = (r % 10) * 16;
      G(v,0,4,8,12,m[S[s]],m[S[s+1]]); G(v,1,5,9,13,m[S[s+2]],m[S[s+3]]); G(v,2,6,10,14,m[S[s+4]],m[S[s+5]]);
      G(v,3,7,11,15,m[S[s+6]],m[S[s+7]]); G(v,0,5,10,15,m[S[s+8]],m[S[s+9]]); G(v,1,6,11,12,m[S[s+10]],m[S[s+11]]);
      G(v,2,7,8,13,m[S[s+12]],m[S[s+13]]); G(v,3,4,9,14,m[S[s+14]],m[S[s+15]]); }
    for (int i = 0; i < 8; i++) h[i] ^= v[i] ^ v[i + 8]; }
  public static byte[] Blake2b(byte[] d) {
    var h = (ulong[])IV.Clone(); h[0] ^= 0x01010040UL; var k = new byte[128]; int o = 0;
    while (d.Length - o > 128) { Buffer.BlockCopy(d, o, k, 0, 128); o += 128; F(h, k, (ulong)o, false); }
    Array.Clear(k, 0, 128); Buffer.BlockCopy(d, o, k, 0, d.Length - o); F(h, k, (ulong)d.Length, true);
    var r = new byte[64]; for (int i = 0; i < 8; i++) Buffer.BlockCopy(BitConverter.GetBytes(h[i]), 0, r, i * 8, 8);
    return r; }
  static readonly BigInteger Q = BigInteger.Pow(2, 255) - 19;
  static readonly BigInteger L = BigInteger.Pow(2, 252) + BigInteger.Parse("27742317777372353535851937790883648493");
  static BigInteger M(BigInteger a) { a %= Q; return a.Sign < 0 ? a + Q : a; }
  static BigInteger Inv(BigInteger a) { return BigInteger.ModPow(M(a), Q - 2, Q); }
  static readonly BigInteger D = M(-121665 * Inv(121666));
  static readonly BigInteger I = BigInteger.ModPow(2, (Q - 1) / 4, Q);
  static BigInteger[] Piu(BigInteger[] p, BigInteger[] q) {
    var a = M((p[1] - p[0]) * (q[1] - q[0])); var b = M((p[1] + p[0]) * (q[1] + q[0]));
    var c = M(2 * p[3] * q[3] * D); var e = M(2 * p[2] * q[2]);
    return new[] { M((b - a) * (e - c)), M((e + c) * (b + a)), M((e - c) * (e + c)), M((b - a) * (b + a)) }; }
  static BigInteger[] Per(BigInteger[] p, BigInteger n) {
    var r = new BigInteger[] { 0, 1, 1, 0 };
    while (n > 0) { if (!n.IsEven) r = Piu(r, p); p = Piu(p, p); n >>= 1; } return r; }
  static BigInteger Num(byte[] b, int da, int n) { var x = new byte[n + 1]; Buffer.BlockCopy(b, da, x, 0, n); return new BigInteger(x); }
  static BigInteger[] Punto(BigInteger y) {
    int s = (int)(y >> 255); y &= (BigInteger.One << 255) - 1;
    if (y >= Q) return null;
    var x2 = M((y * y - 1) * Inv(D * y * y + 1)); var x = BigInteger.ModPow(x2, (Q + 3) / 8, Q);
    if (M(x * x - x2) != 0) x = M(x * I);
    if (M(x * x - x2) != 0 || (x.IsZero && s == 1)) return null;
    if ((int)(x & 1) != s) x = Q - x;
    return new[] { x, y, BigInteger.One, M(x * y) }; }
  public static bool Ed25519(byte[] pk, byte[] firma, byte[] msg) {
    if (pk.Length != 32 || firma.Length != 64) return false;
    var A = Punto(Num(pk, 0, 32)); var Rp = Punto(Num(firma, 0, 32)); var s = Num(firma, 32, 32);
    if (A == null || Rp == null || s >= L) return false;
    var B = Punto(M(4 * Inv(5)));
    var dati = new byte[64 + msg.Length];
    Buffer.BlockCopy(firma, 0, dati, 0, 32); Buffer.BlockCopy(pk, 0, dati, 32, 32); Buffer.BlockCopy(msg, 0, dati, 64, msg.Length);
    var h = Num(SHA512.Create().ComputeHash(dati), 0, 64) % L;
    var P = Per(B, s); var X = Piu(Rp, Per(A, h));
    return M(P[0] * X[2] - X[0] * P[2]) == 0 && M(P[1] * X[2] - X[1] * P[2]) == 0; }
  // minisign: chiave «Ed»+id(8)+pk(32); firma «ED»+id(8)+firma(64), «ED» = firma del BLAKE2b-512 del file
  public static bool Minisign(byte[] chiave, byte[] firma, byte[] file) {
    if (chiave.Length != 42 || firma.Length != 74 || chiave[0] != 'E' || chiave[1] != 'd' || firma[0] != 'E') return false;
    for (int i = 2; i < 10; i++) if (chiave[i] != firma[i]) return false;
    var pk = new byte[32]; Buffer.BlockCopy(chiave, 10, pk, 0, 32); var f = new byte[64]; Buffer.BlockCopy(firma, 10, f, 0, 64);
    if (firma[1] == 'D') return Ed25519(pk, f, Blake2b(file));
    return firma[1] == 'd' && Ed25519(pk, f, file); }
}
'@

function Firma-Ok([byte[]]$dati, [string]$firma) {  # firma = campo "signature" di latest.json (base64 del file .sig)
    if (-not ('FirmaSquadra' -as [type])) { Add-Type -TypeDefinition $FIRMA_CS -ReferencedAssemblies System.Numerics }
    try {
        $riga = ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($firma)) -split "`n")[1].Trim()
        return [FirmaSquadra]::Minisign([Convert]::FromBase64String($CHIAVE_APP), [Convert]::FromBase64String($riga), $dati)
    } catch { return $false }
}

function Riga($segno, $testo, $colore = 'Gray') { Write-Host "  $segno $testo" -ForegroundColor $colore }

function App-Versione {  # versione installata (chiave Uninstall dell'utente con DisplayName Pleiadi), o $null
    Get-ChildItem HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ItemProperty $_.PSPath } | Where-Object { $_.DisplayName -eq 'Pleiadi' } |
        Select-Object -First 1 -ExpandProperty DisplayVersion
}

function Solo-App {
    $codice = ("$env:INVITO" -replace '\s', '').ToUpper()
    if ($codice -notmatch '^[A-HJ-NP-Z2-9]{5}(-[A-HJ-NP-Z2-9]{5}){3}$') {
        Riga '✗' "Il codice dell'invito non è giusto: copia di nuovo la riga intera dal messaggio." Red; return
    }
    $ProgressPreference = 'SilentlyContinue'  # la barra di Invoke-WebRequest rallenta il download di 10 volte
    Write-Host "`n  Pleiadi Studio · preparo il computer (circa un minuto, non devi fare niente)`n" -ForegroundColor Cyan
    try {
        $m = Invoke-RestMethod -UseBasicParsing "$RELEASE_APP/latest.json"
        $p = $m.platforms.'windows-x86_64'
        $ora = App-Versione
        if ($ora -and ([version]$ora -ge [version]$m.version)) {
            Riga '✓' "Pleiadi c'è già (versione $ora)" Green
        } else {
            Riga '…' "Scarico Pleiadi $($m.version)"
            $dati = (Invoke-WebRequest -UseBasicParsing $p.url).Content
            Riga '…' 'Controllo che sia quella della squadra'
            if (-not (Firma-Ok $dati $p.signature)) {
                Riga '✗' "Il file scaricato non ha la firma della squadra: non lo installo. Avvisa chi ti ha invitato." Red; return
            }
            Riga '…' 'Installo Pleiadi (solo per te: niente permessi da amministratore)'
            $setup = Join-Path ([IO.Path]::GetTempPath()) "Pleiadi-setup-$PID.exe"
            [IO.File]::WriteAllBytes($setup, $dati)
            try { Start-Process -Wait -FilePath $setup -ArgumentList '/S' } finally { Remove-Item $setup -ErrorAction SilentlyContinue }
            if (-not (App-Versione)) { Riga '✗' "L'installazione non è andata: incolla di nuovo la stessa riga." Red; return }
            Riga '✓' 'Pleiadi installata' Green
        }
    } catch {
        Riga '✗' 'Non riesco a scaricare Pleiadi: controlla internet e incolla di nuovo la stessa riga.' Red; return
    }
    if ($env:PLEYADES_NON_APRIRE -eq '1') { return }  # i test: installa e controlla, senza aprire l'app
    # il link apre l'app col codice già scritto; entra solo chi preme la freccia (accesso.rs → link_aperto)
    Start-Process "pleiadi://invito/$codice"
    Write-Host "`n  ✓ Pleiadi è aperta: premi la freccia per entrare. Puoi chiudere questa finestra.`n" -ForegroundColor Green
}

try { if ($env:INVITO -and $env:PLEYADES_COMPLETO -ne '1') { Solo-App } else { Avvia } } catch { Write-Host "❌ $_" -ForegroundColor Red; Bloccato } finally { Remove-Item Env:INVITO -ErrorAction SilentlyContinue }  # il codice non resta nella finestra
