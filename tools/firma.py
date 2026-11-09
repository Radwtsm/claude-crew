"""Firma della squadra su crew.py e disinstalla.ps1 (A115): i PC si aggiornano solo con una firma valida.
  python3 tools/firma.py            controlla che le firme (*.sig) valgano per i file nel commit (staged)
  python3 tools/firma.py --firma    in più rifirma quelli cambiati e aggiunge i .sig al commit (serve la chiave)
Chiave privata: solo sul computer del manutentore (TAURI_SIGNING_PRIVATE_KEY_PATH o `git config crew.chiave-firma <percorso>`), mai nel repo;
firma con la CLI di Tauri, la stessa degli aggiornamenti dell'app. Una PR unita da GitHub senza firma: i PC restano
alla versione di prima finché il manutentore non rifirma."""
import os, shutil, subprocess, sys, tempfile

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


male = []
for nome in FIRMATI:
    dati = git("show", f":{nome}", binario=True)
    sig = git("show", f":{nome}.sig")
    if crew.firma_aggiornamenti(crew.CHIAVE_SQUADRA, sig, dati):
        continue
    nuova = firma(dati) if "--firma" in sys.argv else None
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
