#!/usr/bin/env python3
"""Aggiornamenti firmati solo in avanti e firma solo voluta (A128): aggiorna_comando rifiuta una crew.py firmata ma
più vecchia (anche dalla storia pubblica) e prende la più nuova; il pre-commit (firma.py senza --firma) non firma mai.
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
print("\n".join("❌ " + m for m in male) or "✅ firma solo voluta, aggiornamenti solo in avanti")
sys.exit(1 if male else 0)
