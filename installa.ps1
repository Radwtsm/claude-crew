# La riga unica su Windows (PowerShell): per prima cosa la voce «Pleyades tools» in Impostazioni → App (toglie tutto,
# anche da un'installazione a metà: disinstalla.ps1), poi Git e Python se mancano (chiede prima; PLEYADES_SI=1 non chiede), scarica la guida `pleyades-cli` (Pleyades tools) e la lancia.
#   irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Con un progetto a cui sei stato invitato:
#   $env:PROGETTO='PROPRIETARIO/REPO'; $env:STUDIO='studio.nome.org'; irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex
# Con un invito dell'app Pleiadi (la riga del messaggio): il codice in una variabile, mai negli argomenti
#   $env:INVITO='XXXXX-XXXXX-XXXXX-XXXXX'; $env:STUDIO='studio.nome.org'; irm …/installa.ps1 | iex
#   installa solo l'app Pleiadi e la apre col codice (A117, come Mac A90): niente Git, Python, voce in Impostazioni
#   né domande; $env:PLEYADES_COMPLETO='1' fa anche il resto (la guida)
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

# La firma degli aggiornamenti dell'app (minisign di Tauri, Ed25519 su BLAKE2b-512), la stessa che l'app controlla a ogni
# aggiornamento e crew.py in firma_aggiornamenti. In C# compilato da PowerShell (Add-Type, nessun programma in più):
# in PowerShell puro BLAKE2b su un installer di 10 MB richiederebbe minuti.
# più chiavi = rotazione (A127): basta una
$ChiaviSquadra = @('dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDA5RDYyOERGMTU1RTM0OUMKUldTY05GNFYzeWpXQ2FJQU1TT1gwQ2xvV0w3ZVNzUVlYVEZLQnZMMHNIRWtFQ3dGelV4Mm84Mk0K',
    'dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IEU4MjFERURBRDdGQTQ5M0EKUldRNlNmclgydDRoNkFnVmcrRkFUa1AwMDQwSmJFMUtpb2NOR21pWndMYzNjSnZiTlg4SlA3eDYK')
$FirmaCs = @'
using System; using System.Numerics; using System.Security.Cryptography;
public static class PleiadiFirma {
  static readonly ulong[] IV = {0x6a09e667f3bcc908UL,0xbb67ae8584caa73bUL,0x3c6ef372fe94f82bUL,0xa54ff53a5f1d36f1UL,
    0x510e527fade682d1UL,0x9b05688c2b3e6c1fUL,0x1f83d9abfb41bd6bUL,0x5be0cd19137e2179UL};
  static readonly byte[][] S = {
    new byte[]{0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}, new byte[]{14,10,4,8,9,15,13,6,1,12,0,2,11,7,5,3},
    new byte[]{11,8,12,0,5,2,15,13,10,14,3,6,7,1,9,4}, new byte[]{7,9,3,1,13,12,11,14,2,6,5,10,4,0,15,8},
    new byte[]{9,0,5,7,2,4,10,15,14,1,11,12,6,8,3,13}, new byte[]{2,12,6,10,0,11,8,3,4,13,7,5,15,14,1,9},
    new byte[]{12,5,1,15,14,13,4,10,0,7,6,3,9,2,8,11}, new byte[]{13,11,7,14,12,1,3,9,5,0,15,4,8,6,2,10},
    new byte[]{6,15,14,9,11,3,0,8,12,2,13,7,1,4,10,5}, new byte[]{10,2,8,4,7,6,1,5,15,11,9,14,3,12,13,0}};
  static ulong R(ulong x, int n) { return (x >> n) | (x << (64 - n)); }
  static void G(ulong[] v, int a, int b, int c, int d, ulong x, ulong y) {
    v[a] += v[b] + x; v[d] = R(v[d] ^ v[a], 32); v[c] += v[d]; v[b] = R(v[b] ^ v[c], 24);
    v[a] += v[b] + y; v[d] = R(v[d] ^ v[a], 16); v[c] += v[d]; v[b] = R(v[b] ^ v[c], 63); }
  public static byte[] Blake2b(byte[] d) {
    ulong[] h = (ulong[])IV.Clone(), m = new ulong[16], v = new ulong[16]; h[0] ^= 0x01010040UL;
    int off = 0; ulong t = 0; byte[] b = new byte[128];
    while (true) {
      int len = Math.Min(128, d.Length - off); bool ultimo = d.Length - off <= 128;
      Array.Clear(b, 0, 128); Buffer.BlockCopy(d, off, b, 0, len); t += (ulong)len;
      for (int i = 0; i < 16; i++) m[i] = BitConverter.ToUInt64(b, i * 8);
      for (int i = 0; i < 8; i++) { v[i] = h[i]; v[i + 8] = IV[i]; }
      v[12] ^= t; if (ultimo) v[14] = ~v[14];
      for (int r = 0; r < 12; r++) { byte[] s = S[r % 10];
        G(v,0,4,8,12,m[s[0]],m[s[1]]); G(v,1,5,9,13,m[s[2]],m[s[3]]); G(v,2,6,10,14,m[s[4]],m[s[5]]); G(v,3,7,11,15,m[s[6]],m[s[7]]);
        G(v,0,5,10,15,m[s[8]],m[s[9]]); G(v,1,6,11,12,m[s[10]],m[s[11]]); G(v,2,7,8,13,m[s[12]],m[s[13]]); G(v,3,4,9,14,m[s[14]],m[s[15]]); }
      for (int i = 0; i < 8; i++) h[i] ^= v[i] ^ v[i + 8];
      if (ultimo) break; off += 128; }
    byte[] o = new byte[64]; for (int i = 0; i < 8; i++) BitConverter.GetBytes(h[i]).CopyTo(o, i * 8); return o; }
  static readonly BigInteger Q = BigInteger.Pow(2, 255) - 19;
  static readonly BigInteger L = BigInteger.Pow(2, 252) + BigInteger.Parse("27742317777372353535851937790883648493");
  static BigInteger M(BigInteger x) { x %= Q; return x.Sign < 0 ? x + Q : x; }
  static BigInteger Inv(BigInteger x) { return BigInteger.ModPow(M(x), Q - 2, Q); }
  static readonly BigInteger D = M(-121665 * Inv(121666)), I = BigInteger.ModPow(2, (Q - 1) / 4, Q);
  static BigInteger Num(byte[] b, int da, int n) { byte[] x = new byte[n + 1]; Array.Copy(b, da, x, 0, n); return new BigInteger(x); }
  static BigInteger[] Piu(BigInteger[] p, BigInteger[] q) {
    BigInteger a = M((p[1] - p[0]) * (q[1] - q[0])), b = M((p[1] + p[0]) * (q[1] + q[0])),
               c = M(2 * p[3] * q[3] * D), e = M(2 * p[2] * q[2]);
    return new[] { M((b - a) * (e - c)), M((e + c) * (b + a)), M((e - c) * (e + c)), M((b - a) * (b + a)) }; }
  static BigInteger[] Per(BigInteger[] p, BigInteger n) {
    BigInteger[] r = { 0, 1, 1, 0 };
    while (n > 0) { if (!n.IsEven) r = Piu(r, p); p = Piu(p, p); n >>= 1; } return r; }
  static BigInteger[] Punto(byte[] b, int da) {
    BigInteger y = Num(b, da, 32); int s = (int)(y >> 255); y &= (BigInteger.One << 255) - 1;
    BigInteger x2 = M((y * y - 1) * Inv(D * y * y + 1)), x = BigInteger.ModPow(x2, (Q + 3) / 8, Q);
    if (M(x * x - x2) != 0) x = M(x * I);
    if (y >= Q || M(x * x - x2) != 0 || (x == 0 && s == 1)) return null;
    if ((int)(x & 1) != s) x = Q - x;
    return new[] { x, y, BigInteger.One, M(x * y) }; }
  public static bool Ed25519(byte[] pk, byte[] firma, byte[] msg) {
    if (pk.Length != 32 || firma.Length != 64) return false;
    BigInteger[] A = Punto(pk, 0), Rp = Punto(firma, 0); BigInteger s = Num(firma, 32, 32);
    if (A == null || Rp == null || s >= L) return false;
    byte[] g = (M(4 * Inv(5))).ToByteArray(); byte[] g32 = new byte[32]; Array.Copy(g, g32, Math.Min(32, g.Length));
    byte[] dati = new byte[64 + msg.Length]; Array.Copy(firma, dati, 32); Array.Copy(pk, 0, dati, 32, 32); Array.Copy(msg, 0, dati, 64, msg.Length);
    BigInteger h = BigInteger.Remainder(Num(SHA512.Create().ComputeHash(dati), 0, 64), L);
    BigInteger[] P = Per(Punto(g32, 0), s), Qp = Piu(Rp, Per(A, h));
    return M(P[0] * Qp[2] - Qp[0] * P[2]) == 0 && M(P[1] * Qp[2] - Qp[1] * P[2]) == 0; }
  static byte[] Riga2(string b64) {  // minisign: base64 di un testo di due righe, la seconda è base64 dei byte
    string[] r = System.Text.Encoding.UTF8.GetString(Convert.FromBase64String(b64.Trim())).Split('\n');
    return Convert.FromBase64String(r[1].Trim()); }
  public static bool Firmato(string chiave, string firma, byte[] dati) {
    byte[] pk, s;
    try { pk = Riga2(chiave); s = Riga2(firma); } catch { return false; }
    if (pk.Length != 42 || s.Length != 74 || pk[0] != 'E' || pk[1] != 'd' || s[0] != 'E' || (s[1] != 'D' && s[1] != 'd')) return false;
    for (int i = 2; i < 10; i++) if (s[i] != pk[i]) return false;
    byte[] p = new byte[32], f = new byte[64]; Array.Copy(pk, 10, p, 0, 32); Array.Copy(s, 10, f, 0, 64);
    return Ed25519(p, f, s[1] == 'D' ? Blake2b(dati) : dati); }
}
'@

function Firma-Ok($firma, [byte[]]$dati) {
    if (-not ('PleiadiFirma' -as [type])) { Add-Type -TypeDefinition $FirmaCs -ReferencedAssemblies System.Numerics }
    foreach ($k in $ChiaviSquadra) { if ([PleiadiFirma]::Firmato($k, $firma, $dati)) { return $true } }
    return $false
}

function App-Installata {  # la voce «Uninstall» dell'installer NSIS (per l'utente), come crew.py app_windows_installata
    Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' -ErrorAction SilentlyContinue |
        Get-ItemProperty | Where-Object { $_.DisplayName -eq 'Pleiadi' } | Select-Object -First 1
}

function Solo-App {  # con l'invito: solo l'app, niente domande (A117; amici che non usano il terminale)
    $codice = ("$env:INVITO" -replace '\s', '').ToUpper()
    if ($codice -notmatch '^[A-HJ-NP-Z2-9]{5}(-[A-HJ-NP-Z2-9]{5}){3}$') {
        Write-Host "  ✗ Il codice dell'invito non è giusto: copia di nuovo la riga intera dal messaggio." -ForegroundColor Red
        return 1
    }
    Write-Host "`n  Pleiadi Studio · preparo il computer (circa un minuto, non devi fare niente)`n" -ForegroundColor Cyan
    if (App-Installata) {
        Write-Host "  ✓ Pleiadi c'è già (si aggiorna da sola)"
    } else {
        $manifesto = if ($env:PLEYADES_MANIFESTO) { $env:PLEYADES_MANIFESTO } else {  # PLEYADES_MANIFESTO: i test
            'https://github.com/Radwtsm/pleiadi-app/releases/latest/download/latest.json' }
        $tmp = Join-Path ([IO.Path]::GetTempPath()) ("pleiadi-" + [guid]::NewGuid())
        New-Item -ItemType Directory -Force -Path $tmp | Out-Null
        try {
            Write-Host '  … Scarico Pleiadi'
            try {
                $p = (Invoke-RestMethod -UseBasicParsing $manifesto).platforms.'windows-x86_64'
                $dati = (New-Object Net.WebClient).DownloadData($p.url)  # in memoria: firma prima, disco dopo
            } catch {
                Write-Host '  ✗ Non riesco a scaricare Pleiadi: controlla internet e incolla di nuovo la stessa riga.' -ForegroundColor Red
                return 1
            }
            Write-Host '  … Controllo che sia quella della squadra'
            if (-not (Firma-Ok $p.signature $dati)) {
                Write-Host "  ✗ Il file scaricato non ha la firma della squadra: non lo installo. Avvisa chi ti ha invitato." -ForegroundColor Red
                return 1
            }
            if ($env:PLEYADES_NON_INSTALLARE -eq '1') { Write-Host '  ✓ firma della squadra (prova: non installo)'; return 0 }
            Write-Host '  … Installo Pleiadi (solo per il tuo utente: niente password)'
            $setup = Join-Path $tmp 'Pleiadi-setup.exe'; [IO.File]::WriteAllBytes($setup, $dati)
            # scaricato qui e non dal browser: niente «Mark of the Web», SmartScreen non lo ferma
            & $setup /S | Out-Null  # avvio diretto: Start-Process (ShellExecute) dà «Accesso negato» fuori dal desktop
            if ($LASTEXITCODE -ne 0 -or -not (App-Installata)) {
                Write-Host "  ✗ L'installazione non è andata: incolla di nuovo la stessa riga." -ForegroundColor Red
                return 1
            }
            Write-Host '  ✓ Pleiadi installata'
        } finally { Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue }
    }
    if ($env:PLEYADES_NON_APRIRE -eq '1') { return 0 }  # i test: installa e controlla, senza aprire l'app
    # il link apre l'app col codice già scritto; entra solo chi preme la freccia (accesso.rs → link_aperto). Lo schema
    # pleiadi:// lo registra l'installer (deep-link in tauri.conf); senza, l'exe col link come argomento fa lo stesso
    $link = "pleiadi://invito/$codice"
    if (Test-Path 'HKCU:\Software\Classes\pleiadi\shell\open\command') { Start-Process $link }
    else { Start-Process -FilePath (Join-Path (App-Installata).InstallLocation.Trim('"') 'pleiadi.exe') -ArgumentList $link }
    Write-Host "`n  ✓ Pleiadi è aperta: premi la freccia per entrare. Puoi chiudere questa finestra.`n" -ForegroundColor Green
    return 0
}

function Avvia {
    if ($env:INVITO -and $env:PLEYADES_COMPLETO -ne '1') {  # errori suoi senza le righe di «Pleyades tools»: qui non c'è
        try { $null = Solo-App } catch { Write-Host "  ✗ $_`n  Incolla di nuovo la stessa riga." -ForegroundColor Red }
        return
    }
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

try { Avvia } catch { Write-Host "❌ $_" -ForegroundColor Red; Bloccato } finally { Remove-Item Env:INVITO -ErrorAction SilentlyContinue }  # il codice non resta nella finestra
