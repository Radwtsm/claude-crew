#!/usr/bin/env python3
"""Prova da zero su Windows: un Windows nuovo (Windows Sandbox) fa la riga d'installazione di un collega.

    python3 tools/prova_da_zero.py windows      # «windows» = host ssh del PC di prova (Windows Pro, Sandbox attiva)
    python3 tools/prova_da_zero.py mac-utente   # Mac: utente nuovo «pleyades-prova» (sudo), stessa riga e stesse regole

Copia `prova-da-zero/avvio.ps1` sul PC, apre la Sandbox nella sessione di chi è collegato al PC (la si vede sullo
schermo), aspetta la fine (max 20 min) e controlla l'esito con le stesse regole di test_guida. La Sandbox si cancella
alla chiusura: ogni prova parte da zero. Installer fermo da 2 min → si ferma subito col suo log.
Per iterare: `--a-mano` (resta aperta) poi `--esegui "<powershell>"` gira dentro la Sandbox e stampa l'output.
Con un invito vero: `--invito <file>` (riga 1 il codice, riga 2 lo studio): come la riga del messaggio d'invito; il
file arriva nella Sandbox e avvio.ps1 lo cancella appena letto. Il codice mai negli argomenti né nell'output.
Solo libreria standard; serve ssh senza password verso il PC."""
import base64, os, re, shutil, subprocess, sys, tempfile, time

QUI = os.path.dirname(os.path.abspath(__file__))
CARTELLA = "prova-da-zero"  # in C:\Users\Public: la vede anche l'utente sullo schermo, se è un altro
COMPITO = "PleyadesProvaDaZero"
MINUTI = 20  # una prova buona ne dura ~10
CHIUDI = ("schtasks /end /tn " + COMPITO + " 2>&1 | Out-Null; Get-Process WindowsSandbox* -EA SilentlyContinue | Stop-Process -Force; "
          "Restart-Service CmService -Force")  # finestra, VM rimasta e servizio: la prossima riparte pulita
WSB = """<Configuration>
  <MappedFolders><MappedFolder><HostFolder>{dir}</HostFolder><SandboxFolder>C:\\prova</SandboxFolder>
    <ReadOnly>false</ReadOnly></MappedFolder>
    <MappedFolder><HostFolder>{dir}-cache</HostFolder><SandboxFolder>C:\\cache</SandboxFolder>
    <ReadOnly>false</ReadOnly></MappedFolder></MappedFolders>
  <LogonCommand><Command>powershell -ExecutionPolicy Bypass -File C:\\prova\\avvio.ps1</Command></LogonCommand>
</Configuration>"""


def ps(host, comando, check=True):
    # -EncodedCommand: niente virgolette da far passare per cmd; output in code page Windows → errors="replace"
    cod = base64.b64encode(("[Console]::OutputEncoding=[Text.Encoding]::UTF8; " + comando).encode("utf-16-le")).decode()
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", host,
                            "powershell", "-NoProfile", "-EncodedCommand", cod],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    except subprocess.TimeoutExpired:
        # la chiave c'è ma ssh non finisce: di solito aspetta il Touch ID (Secretive) o il PC dorme
        sys.exit(f"prova_da_zero: {host} non risponde in 2 min: Touch ID sul Mac? (non compare: riavvia SecretAgent, trappole-tecniche → mac) PC sveglio?")
    if check and r.returncode:
        sys.exit(f"prova_da_zero: sul PC «{comando[:60]}» non va:\n{r.stderr.strip()[-600:]}")
    return r.stdout.strip()


def sveglia(host, schermo, dir_pc, argomenti=""):
    tr = f"powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File {dir_pc}\\sveglia.ps1 {argomenti}"
    ps(host, f"schtasks /create /f /tn {COMPITO} /sc once /st 23:59 /ru '{schermo}' /it /tr '{tr}' | Out-Null; "
             f"schtasks /run /tn {COMPITO} | Out-Null")


# Mac: un utente nuovo al posto della Sandbox. Senza password (non entra dalla schermata di accesso, nascosto): lo si
# usa solo con sudo da qui. Ricreato a ogni prova; vede gli strumenti di Apple e /opt/homebrew già sul Mac
UTENTE = "pleyades-prova"
CASA_PROVA = "/Users/" + UTENTE


def sudo(*cmd, **kw):
    return subprocess.run(["sudo", *cmd], **kw)


def utente_nuovo():
    """Toglie l'utente di prova (casa compresa) e lo ricrea vuoto, col suo Portachiavi «login» aperto."""
    if sudo("dscl", ".", "-read", CASA_PROVA, capture_output=True).returncode == 0:
        sudo("dscl", ".", "-delete", CASA_PROVA, check=True)
    if os.path.isdir(CASA_PROVA):
        sudo("rm", "-rf", "--", CASA_PROVA, check=True)  # sempre e solo /Users/pleyades-prova
    usati = {int(x.split()[-1]) for x in subprocess.run(["dscl", ".", "-list", "/Users", "UniqueID"],
                                                       capture_output=True, text=True).stdout.splitlines()}
    uid = str(next(u for u in range(601, 700) if u not in usati))
    for k, v in (("UserShell", "/bin/zsh"), ("RealName", "Prova Pleyades"), ("UniqueID", uid),
                 ("PrimaryGroupID", "20"), ("NFSHomeDirectory", CASA_PROVA), ("Password", "*"), ("IsHidden", "1")):
        sudo("dscl", ".", "-create", CASA_PROVA, k, v, check=True)
    if sudo("createhomedir", "-c", "-u", UTENTE, capture_output=True).returncode or not os.path.isdir(CASA_PROVA):
        sudo("mkdir", "-p", CASA_PROVA + "/Library/Keychains", check=True)
        sudo("chown", "-R", f"{UTENTE}:staff", CASA_PROVA, check=True)
    sudo("-u", UTENTE, "mkdir", "-p", CASA_PROVA + "/Library/Keychains", check=True)
    # Il Portachiavi «login» lo crea il primo accesso grafico, che qui non c'è: lo si crea come farebbe quello.
    # Password a caso, solo in memoria e via stdin (mai negli argomenti); serve solo ad aprirlo
    pw = __import__("secrets").token_hex(16)
    kc = f"{CASA_PROVA}/Library/Keychains/login.keychain-db"
    r = sudo("-u", UTENTE, "-H", "security", "-i", input=f"create-keychain -p {pw} {kc}\ndefault-keychain -s {kc}\n"
             f"login-keychain -s {kc}\nlist-keychains -d user -s {kc}\nunlock-keychain -p {pw} {kc}\nset-keychain-settings {kc}\n",
             capture_output=True, text=True, cwd="/")
    if r.returncode or "error" in (r.stdout + r.stderr).lower():
        sys.exit(f"prova_da_zero: Portachiavi dell'utente di prova non creato:\n{(r.stdout + r.stderr)[-400:]}")


def mac_utente():
    invito = open(sys.argv[sys.argv.index("--invito") + 1]).read().split() if "--invito" in sys.argv else []
    app = "/Applications/Pleiadi.app"
    if os.path.isdir(app):  # installa_app_mac guarda anche lì: la prova la salterebbe
        print(f"prova_da_zero: {app} c'è già: il passo dell'app sarà «installata» (spostala in ~/Applications)", file=sys.stderr)
    print("→ sudo per creare l'utente di prova (Touch ID o password del Mac)", flush=True)
    sudo("-v", check=True)
    utente_nuovo()
    # le copie di installa.sh e crew.py da provare prima del push, leggibili dall'utente di prova
    lavoro = tempfile.mkdtemp(prefix="da-zero-", dir="/Users/Shared")
    esito = os.path.join(lavoro, "esito")
    os.makedirs(esito)
    crew = os.path.join(lavoro, "crew.py")
    shutil.copy(os.path.join(QUI, "..", "crew.py"), crew)
    sh = open(os.path.join(QUI, "..", "installa.sh"), encoding="utf-8").read()
    sh = re.sub(r"https://raw\.githubusercontent\.com/[^ ]+/crew\.py", "file://" + crew, sh)
    open(os.path.join(lavoro, "installa.sh"), "w", encoding="utf-8").write(sh)
    if invito:  # come la riga del messaggio: codice e studio in variabili, il file sparisce appena letto
        with os.fdopen(os.open(os.path.join(lavoro, "invito.txt"), os.O_WRONLY | os.O_CREAT, 0o600), "w") as f:
            f.write("\n".join(invito))  # 600 da subito, poi suo
    os.chmod(lavoro, 0o755)
    os.chmod(esito, 0o777)
    for f in os.listdir(lavoro):
        if f not in ("esito", "invito.txt"):
            os.chmod(os.path.join(lavoro, f), 0o644)
    if invito:
        sudo("chown", UTENTE, os.path.join(lavoro, "invito.txt"), check=True)
    # le risposte di chi non sa nulla, come in avvio.ps1: «Mio», niente accesso a Claude, senza GitHub, poi Invio
    risposte = "1\n2\n2\n" + "\n" * 7
    corpo = (f"cd ~; if [ -f {lavoro}/invito.txt ]; then set -- $(cat {lavoro}/invito.txt); "
             "export INVITO=$1 STUDIO=$2; fi; bash " + lavoro + "/installa.sh > " + esito + "/guida.txt 2>&1; unset INVITO; "
             f"export PATH=$HOME/.local/bin:$PATH; c=$HOME/.crew/crew.py; "
             f"if [ -f $c ]; then echo | python3 $c controlla > {esito}/controlla.txt 2>&1; python3 $c passi --json > {esito}/passi.json 2>&1; "
             f"else echo 'crew.py non scaricato' > {esito}/controlla.txt; fi; "
             f"for p in git python3 claude pleyades-cli; do echo \"$p = $(command -v $p)\" >> {esito}/programmi.txt; done")
    # niente terminale (nuova sessione): installa.sh legge le risposte da stdin come in avvio.ps1
    print(f"guida come {UTENTE}; aspetto la fine (max {MINUTI} min)…", flush=True)
    t = time.time()
    try:
        sudo("-u", UTENTE, "-H", "env", "-i", f"HOME={CASA_PROVA}", f"USER={UTENTE}", f"LOGNAME={UTENTE}",
             "PATH=/usr/bin:/bin:/usr/sbin:/sbin", "TERM=xterm-256color", "LANG=it_IT.UTF-8", "SHELL=/bin/zsh",
             "bash", "-c", corpo, input=risposte, text=True, timeout=MINUTI * 60, start_new_session=True, cwd="/")
        finita = True
    except subprocess.TimeoutExpired:
        print(f"prova_da_zero: {MINUTI} minuti senza finire", file=sys.stderr)
        finita = False
    finally:
        sudo("rm", "-f", os.path.join(lavoro, "invito.txt"))  # la cartella è mia: il file lo tolgo io
    print(f"{(time.time() - t) / 60:.1f} min · l'utente {UTENTE} resta per guardarci (si ricrea alla prossima prova)")
    return verifica(esito, finita, invito)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "mac-utente":
        return mac_utente()
    host, a_mano = sys.argv[1], "--a-mano" in sys.argv
    if "--sveglia" in sys.argv:  # solo riaccendere lo schermo e tenerlo sveglio per la Sandbox già aperta
        dir_pc = ps(host, "$env:PUBLIC") + "\\" + CARTELLA
        subprocess.run(["scp", "-q", "-o", "BatchMode=yes", os.path.join(QUI, CARTELLA, "sveglia.ps1"), f"{host}:{dir_pc}/".replace("\\", "/")], check=True)
        return sveglia(host, ps(host, "(Get-CimInstance Win32_ComputerSystem).UserName"), dir_pc)
    if "--esegui" in sys.argv:  # un comando dentro la Sandbox già aperta (--a-mano), output qui: si itera in secondi
        dir_pc = ps(host, "$env:PUBLIC") + "\\" + CARTELLA
        # la Sandbox scrive l'output mentre gira: il segno finale dice che è completo
        cod = (sys.argv[sys.argv.index("--esegui") + 1] + "\n'== fine'").replace("'", "''")
        ps(host, f"Remove-Item '{dir_pc}\\esito\\esegui.txt' -EA SilentlyContinue; "
                 f"Set-Content -Encoding UTF8 '{dir_pc}\\esegui.ps1' '{cod}'")
        for _ in range(60):  # il controllo dentro gira ogni 10 s
            time.sleep(4)
            out = ps(host, f"Get-Content '{dir_pc}\\esito\\esegui.txt' -Raw -EA SilentlyContinue", False)
            if out.endswith("== fine"):
                return print(out.removesuffix("== fine").rstrip())
        sys.exit("prova_da_zero: nessuna risposta dalla Sandbox in 4 min (è aperta? --a-mano)")
    if ps(host, "(Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM).State") != "Enabled":
        sys.exit("prova_da_zero: Windows Sandbox non è attiva sul PC (serve Windows Pro: Funzionalità di Windows)")
    # ne gira una alla volta: quella di una prova interrotta (o rimasta a metà) si chiude; il PC è solo di prova
    ps(host, "if (Get-Process WindowsSandbox*, vmmemWindowsSandbox -EA SilentlyContinue) { " + CHIUDI + "; Start-Sleep 5 }")
    schermo = ps(host, "(Get-CimInstance Win32_ComputerSystem).UserName", False)  # chi ha l'accesso allo schermo
    if not schermo:
        sys.exit("prova_da_zero: nessuno ha fatto l'accesso a Windows sul PC: entra (anche bloccato va bene) e rilancia")
    dir_pc = ps(host, "$env:PUBLIC") + "\\" + CARTELLA
    ps(host, f"Remove-Item -Recurse -Force '{dir_pc}' -ErrorAction SilentlyContinue; New-Item -ItemType Directory '{dir_pc}' | Out-Null; "
             f"New-Item -ItemType Directory -Force '{dir_pc}-cache' | Out-Null")  # la cache (winget) resta fra le prove
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", os.path.join(QUI, CARTELLA, "avvio.ps1"), os.path.join(QUI, CARTELLA, "sveglia.ps1"),
                    os.path.join(QUI, "..", "installa.ps1"), os.path.join(QUI, "..", "crew.py"),
                    f"{host}:{dir_pc}/".replace("\\", "/")], check=True)  # provati prima del push
    invito = open(sys.argv[sys.argv.index("--invito") + 1]).read().split() if "--invito" in sys.argv else []
    if invito:
        subprocess.run(["scp", "-q", "-o", "BatchMode=yes", sys.argv[sys.argv.index("--invito") + 1],
                        f"{host}:{dir_pc}/invito.txt".replace("\\", "/")], check=True)
    wsb = WSB.format(dir=dir_pc).replace("'", "''")
    ps(host, f"Set-Content -Encoding UTF8 '{dir_pc}\\prova.wsb' '{wsb}'" + ("" if a_mano else f"; New-Item '{dir_pc}\\chiudi' | Out-Null"))
    # da ssh la Sandbox non si apre (nessuno schermo): un compito nella sessione di chi è allo schermo, che la apre
    # e tiene sveglio il PC finché resta aperta (sveglia.ps1); standby a metà prova = prova ferma
    sveglia(host, schermo, dir_pc, f"-Wsb {dir_pc}\\prova.wsb")
    for _ in range(12):  # la Sandbox parte in pochi secondi; se no il compito non è partito
        time.sleep(5)
        if ps(host, "(Get-Process WindowsSandbox* -EA SilentlyContinue).Count", False) not in ("", "0"):
            break
    else:
        ps(host, f"schtasks /delete /f /tn {COMPITO} | Out-Null", False)
        sys.exit("prova_da_zero: la Sandbox non è partita sul PC (compito interattivo non eseguito): guarda lo schermo del PC")
    print(f"Sandbox aperta sul PC ({'resta aperta' if a_mano else 'si chiude alla fine'}); aspetto la fine…", flush=True)
    visti, t = "", time.time()
    while time.time() - t < MINUTI * 60:
        time.sleep(10)
        passi = ps(host, f"Get-Content '{dir_pc}\\esito\\passi.txt' -ErrorAction SilentlyContinue", False)
        if passi != visti:
            print("\n".join(passi.splitlines()[len(visti.splitlines()):]), flush=True)
            visti = passi
        if passi.endswith("fine"):
            break
        if " fermo: " in passi:  # installer bloccato (avvio.ps1): ultime righe del suo log, poi si chiude subito
            print(ps(host, f"$l = Get-ChildItem '{dir_pc}\\esito\\log' | Sort-Object {{ $_.Name -match 'ython' }}, Length | Select-Object -Last 1; "
                           "'== ' + $l.Name; Get-Content $l.FullName -Tail 15", False), flush=True)
            if not a_mano:
                ps(host, CHIUDI, False)
            break
    else:
        print(f"prova_da_zero: {MINUTI} minuti senza finire: chiudo la Sandbox", file=sys.stderr)
        ps(host, CHIUDI, False)
    dest = tempfile.mkdtemp(prefix="da-zero-")
    subprocess.run(["scp", "-q", "-r", "-o", "BatchMode=yes", f"{host}:{dir_pc}/esito".replace("\\", "/"), dest])
    return verifica(os.path.join(dest, "esito"), "fine" in visti, invito)


def verifica(esito, finita, invito):
    """Stesse regole per Windows e Mac: forma dell'output (test_guida), programmi, durata, passi dell'invito."""
    leggi = lambda f: open(os.path.join(esito, f), encoding="utf-8-sig", errors="replace").read() if os.path.exists(os.path.join(esito, f)) else ""
    sys.path.insert(0, QUI)
    from test_guida import forma, esiti  # stesse regole di UX della prova in casa finta
    err = forma(leggi("guida.txt"), "guida (da zero)") + forma(leggi("controlla.txt"), "controlla (da zero)")
    if not finita:
        err.append("non è arrivata alla fine")
    for riga in leggi("programmi.txt").splitlines():  # alla fine un collega li deve avere tutti
        if riga.endswith("= "):
            err.append(f"manca {riga.split()[0]} dopo la guida")
    durata = re.search(r"a posto · ([\d.]+) min", leggi("guida.txt"))
    if durata and float(durata[1]) > 5:  # una buona ne dura 1-2: qualcosa ha aspettato (risposte sfasate, browser)
        err.append(f"guida lenta: {durata[1]} min (attesa nascosta? guarda guida.txt)")
    if "a posto" not in leggi("guida.txt"):
        err.append("guida: manca il riepilogo finale («x/y a posto»): si è fermata prima")
    if invito:  # la riga dell'invito: studio, progetto e app senza «Concedi accesso»; resta solo l'accesso a Claude
        g = leggi("guida.txt")
        if invito[0].upper() in g.upper():
            err.append("guida: il codice d'invito compare nell'output")
        for atteso in ("invito per lo studio", "accesso per l'app Pleiadi", "copia di «", "app Pleiadi"):
            if not re.search(r"✓[^\n]*" + re.escape(atteso), g):
                err.append(f"guida (invito): «{atteso}» non è riuscito")
    print(leggi("programmi.txt"))
    print("esiti:", ", ".join(esiti(leggi("controlla.txt")) or esiti(leggi("guida.txt"))) or "nessuno")
    for e in err:
        print("prova_da_zero: " + e, file=sys.stderr)
    print(f"file: {esito}")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
