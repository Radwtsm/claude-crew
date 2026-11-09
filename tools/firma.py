"""Firma della squadra su crew.py e disinstalla.ps1 (A115): i PC si aggiornano solo con una firma valida.
  python3 tools/firma.py            controlla che le firme (*.sig) valgano per i file nel commit (staged)
  python3 tools/firma.py --firma    in più rifirma quelli cambiati e aggiunge i .sig al commit (serve la chiave):
                                    mostra cosa cambia dall'ultima versione firmata e chiede conferma a una persona
                                    (dialogo sul Mac o terminale), alza `# versione-firmata` se serve (A128).
Il pre-commit solo controlla: un merge non riletto o un processo che fa `git commit` non firma niente da solo.
Chiave privata: solo sul computer del manutentore (TAURI_SIGNING_PRIVATE_KEY_PATH o `git config crew.chiave-firma <percorso>`), mai nel repo;
firma con la CLI di Tauri, la stessa degli aggiornamenti dell'app. Una PR unita da GitHub senza firma: i PC restano
alla versione di prima finché il manutentore non rifirma."""
import os, re, shutil, subprocess, sys, tempfile

RADICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RADICE)
import crew  # noqa: E402

FIRMATI = ("crew.py", "disinstalla.ps1")
CHIAVE = os.path.expanduser(os.environ.get("TAURI_SIGNING_PRIVATE_KEY_PATH") or subprocess.run(
    ["git", "-C", RADICE, "config", "--get", "crew.chiave-firma"], capture_output=True, text=True).stdout.strip() or "-")


def git(*a, binario=False):
    r = subprocess.run(["git", "-C", RADICE, *a], capture_output=True)
    return r.stdout if binario else r.stdout.decode().strip()


def tauri():
    for c in (shutil.which("tauri"), os.path.expanduser("~/code/agenzia-crew/app/pleiadi-tauri/node_modules/.bin/tauri")):
        if c and os.path.exists(c):
            return [c]
    return ["npx", "--yes", "@tauri-apps/cli@2", ] if shutil.which("npx") else None


def firma(dati):
    t = tauri()
    if not t or not os.path.isfile(CHIAVE):
        return None
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "f")
        open(f, "wb").write(dati)
        subprocess.run([*t, "signer", "sign", "-f", CHIAVE, "-p", "", f], capture_output=True, stdin=subprocess.DEVNULL)
        return open(f + ".sig").read().strip() if os.path.exists(f + ".sig") else None


def ultima_firmata(nome):
    """(commit, contenuto) dell'ultima versione di `nome` con firma valida nella storia, o (None, b"")."""
    for c in git("log", "--format=%H", "--", nome + ".sig").split():
        dati = git("show", f"{c}:{nome}", binario=True)
        if crew.firma_aggiornamenti(crew.CHIAVE_SQUADRA, git("show", f"{c}:{nome}.sig"), dati):
            return c, dati
    return None, b""


def alza_versione(nome, dati, minima):
    """`# versione-firmata` almeno `minima`, nel file e nel commit; None se il file ha modifiche non in staging."""
    if open(os.path.join(RADICE, nome), "rb").read() != dati:
        return None
    vecchia = crew.versione_firmata(dati)
    riga = f"# versione-firmata: {minima}".encode()
    if vecchia:
        dati = re.sub(rb"^# versione-firmata: \d+", riga, dati, count=1, flags=re.M)
    else:
        a_capo = dati.find(b"\n") + 1 if dati.startswith(b"#!") else 0
        dati = dati[:a_capo] + riga + b"\n" + dati[a_capo:]
    open(os.path.join(RADICE, nome), "wb").write(dati)
    git("add", nome)
    return dati


def conferma(testo):
    """Sì solo da una persona: dialogo sul Mac, altrimenti il terminale (/dev/tty), mai da variabili o stdin."""
    if sys.platform == "darwin":
        s = testo.replace("\\", "\\\\").replace('"', '\\"')
        r = subprocess.run(["osascript", "-e", f'display dialog "{s}" buttons {{"No", "Firma"}} default button "No" '
                            'with title "Firma della squadra" with icon caution'], capture_output=True, text=True)
        return "Firma" in r.stdout
    try:
        with open("/dev/tty", "r+") as t:
            t.write(testo + "\nFirmo? [s/N] ")
            t.flush()
            return t.readline().strip().lower() in ("s", "si", "sì")
    except OSError:
        return False


male = []
for nome in FIRMATI:
    dati = git("show", f":{nome}", binario=True)
    sig = git("show", f":{nome}.sig")
    if crew.firma_aggiornamenti(crew.CHIAVE_SQUADRA, sig, dati):
        continue
    nuova = None
    if "--firma" in sys.argv and os.path.isfile(CHIAVE):
        prima, vecchi = ultima_firmata(nome)
        if crew.versione_firmata(dati) <= crew.versione_firmata(vecchi):
            dati = alza_versione(nome, dati, crew.versione_firmata(vecchi) + 1)
            if dati is None:
                male.append(f"✗ {nome}: metti in staging tutte le modifiche (git add {nome}) e rilancia")
                continue
        stat = git("diff", "--cached", "--stat", prima or "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "--", nome)
        autori = git("log", "--format=%an", f"{prima}..HEAD" if prima else "HEAD", "--", nome).split("\n")
        testo = (f"Firmare {nome} versione {crew.versione_firmata(dati)}? Arriva su tutti i PC.\n\n"
                 f"Dall'ultima firmata ({(prima or 'nessuna')[:7]}): {stat.splitlines()[-1].strip() if stat else 'nessuna differenza'}\n"
                 f"Autori dei commit in mezzo: {', '.join(sorted(set(a for a in autori if a))) or 'solo modifiche in staging'}\n\n"
                 "Firma solo se hai riletto il diff (git diff --cached).")
        nuova = firma(dati) if conferma(testo) else None
        if not nuova:
            male.append(f"✗ {nome}: non firmato (risposta no o firma fallita)")
            continue
    if nuova and crew.firma_aggiornamenti(crew.CHIAVE_SQUADRA, nuova, dati):
        open(os.path.join(RADICE, nome + ".sig"), "w").write(nuova + "\n")
        git("add", nome + ".sig")
        print(f"✓ {nome} firmato")
    elif not os.path.isfile(CHIAVE):  # chi contribuisce senza chiave: i PC tengono la versione firmata di prima
        print(f"⚠️ {nome}: da rifirmare dal manutentore prima che arrivi ai PC")
    else:
        male.append(f"✗ {nome}: firma mancante o vecchia; la mette `python3 tools/firma.py --firma` (chiave del manutentore)")
print("\n".join(male) or "✓ firme di crew.py e disinstalla.ps1")
sys.exit(1 if male else 0)
