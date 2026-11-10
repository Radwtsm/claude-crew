#!/usr/bin/env python3
"""Aggiornamenti firmati solo in avanti e firma solo voluta (A128): aggiorna_comando rifiuta una crew.py firmata ma
più vecchia (anche dalla storia pubblica) e prende la più nuova; il pre-commit (firma.py senza --firma) non firma mai.
A122: installa.sh/ps1 hanno le stesse chiavi di crew.py e installa.sh prende crew.py solo firmata.
Casa finta, niente rete. Uso: python3 tools/test_firma.py"""
import importlib.util, os, subprocess, sys, tempfile

os.environ["HOME"] = os.environ["USERPROFILE"] = casa = tempfile.mkdtemp(prefix="casa-")
radice = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("crew", os.path.join(radice, "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)
male = []


def versione(n):
    return f"#!/usr/bin/env python3\n# versione-firmata: {n}\nprint({n})\n".encode() if n else b"print(0)\n"


for dati, atteso in ((versione(7), 7), (versione(0), 0), (b"x = '# versione-firmata: 9'\n", 0)):
    if crew.versione_firmata(dati) != atteso:
        male.append(f"versione_firmata({dati[:30]!r}) != {atteso}")
dest = os.path.join(crew.CARTELLA, "crew.py")
os.makedirs(crew.CARTELLA, exist_ok=True)
for c, nuovo, ok, resta in ((5, 3, False, 5), (5, 0, False, 5), (5, 6, True, 6), (5, 5, True, 5)):
    open(dest, "wb").write(versione(c))
    crew.scarica_firmato = lambda nome, n=nuovo: versione(n)
    esito = crew.aggiorna_comando()
    if esito[0] != ok or crew.versione_firmata(open(dest, "rb").read()) != resta:
        male.append(f"da {c} a {nuovo}: {esito}, resta {crew.versione_firmata(open(dest, 'rb').read())} (atteso {resta})")
for nome in ("crew.py", "disinstalla.ps1"):
    if crew.versione_firmata(open(os.path.join(radice, nome), "rb").read()) < 1:
        male.append(f"{nome} senza `# versione-firmata`")
if any("firma.py" in r and "--firma" in r for r in open(os.path.join(radice, "check.sh")) if not r.lstrip().startswith("#")):
    male.append("check.sh firma da solo: il pre-commit deve solo controllare")
# A122: le chiavi degli installer = CHIAVE_SQUADRA; installa.sh scarica (file://) e tiene solo il file firmato
import re, shutil  # noqa: E402
sh, ps = (open(os.path.join(radice, f), encoding="utf-8").read() for f in ("installa.sh", "installa.ps1"))
chiavi = set(crew.CHIAVE_SQUADRA)
blocco = re.search(r"CHIAVI = \[(.*?)\]", sh, re.S)
if not blocco or set(re.findall(r'"([^"]+)"', blocco.group(1))) != chiavi:
    male.append("installa.sh: CHIAVI diverse da crew.CHIAVE_SQUADRA")
blocco = re.search(r"\$ChiaviSquadra = @\((.*?)\)", ps, re.S)
if not blocco or set(re.findall(r"'([^']+)'", blocco.group(1))) != chiavi:
    male.append("installa.ps1: $ChiaviSquadra diverse da crew.CHIAVE_SQUADRA")
if "raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py" in sh + ps or "main/disinstalla.ps1 -OutFile" in ps:
    male.append("installer: crew.py o disinstalla.ps1 scaricati senza firma")
if os.name != "nt":
    pezzo = sh[sh.index("CREW_RAW="):sh.index('mkdir -p "$HOME/.crew"')]
    srv = tempfile.mkdtemp(prefix="raw-")
    os.makedirs(os.path.join(srv, "main"))
    for f in ("crew.py", "crew.py.sig", "disinstalla.ps1.sig"):
        shutil.copy(os.path.join(radice, f), os.path.join(srv, "main", f))
    open(os.path.join(srv, "main", "disinstalla.ps1"), "wb").write(open(os.path.join(radice, "crew.py"), "rb").read())
    pezzo = re.sub(r"(?m)^CREW_RAW=.*$", f"CREW_RAW=file://{srv}", pezzo)
    pezzo = re.sub(r"(?m)^CREW_GIT=.*$", "CREW_GIT=", pezzo)
    for nome, ok in (("crew.py", True), ("disinstalla.ps1", False)):  # il secondo: file scambiato, firma d'altro
        dest = os.path.join(casa, "preso-" + nome)
        r = subprocess.run(["bash", "-c", pezzo + f'\nscarica_firmato {nome} "{dest}"'], capture_output=True, text=True)
        if (r.returncode == 0) != ok or os.path.exists(dest) != ok or os.path.exists(dest + ".tmp"):
            male.append(f"installa.sh {nome}: esito {r.returncode}, file {os.path.exists(dest)} (atteso {ok}) {r.stdout}{r.stderr}")
print("\n".join("❌ " + m for m in male) or "✅ firma solo voluta, aggiornamenti solo in avanti, prima installazione firmata")
sys.exit(1 if male else 0)
