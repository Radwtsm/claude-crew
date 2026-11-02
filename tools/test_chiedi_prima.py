#!/usr/bin/env python3
"""Chiedere prima di installare e di cancellare (owner 02/11): senza terminale `togli_copia_vecchia` lascia la copia
vecchia e lo dice; col terminale cancella solo col sì. installa.ps1/installa.sh chiedono prima di installare programmi.
In una casa finta, niente tocca il PC vero. Uso: python3 tools/test_chiedi_prima.py"""
import importlib.util, io, os, re, sys, tempfile

os.environ["HOME"] = os.environ["USERPROFILE"] = casa = tempfile.mkdtemp(prefix="casa-")  # Windows: ~ è USERPROFILE
os.environ["LOCALAPPDATA"] = os.path.join(casa, "AppData", "Local")
os.environ["APPDATA"] = os.path.join(casa, "AppData", "Roaming")
radice = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("crew", os.path.join(radice, "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)
male = []


def vietato(*a, **k):
    raise AssertionError("programma vero lanciato")


crew.casa_di_prova = lambda: True
crew.run = vietato
app = {"nome": "Prova", "windows": {"app": "Prova"}}
vecchia = os.path.join(os.environ["LOCALAPPDATA"], "Programs", "Prova")
start = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs")
lnk = [os.path.join(start, "Prova.lnk"), os.path.join(casa, "Desktop", "Prova.lnk")]


def prepara():
    os.makedirs(vecchia, exist_ok=True)
    open(os.path.join(vecchia, "Prova.exe"), "wb").close()
    for x in lnk:
        os.makedirs(os.path.dirname(x), exist_ok=True)
        with open(x, "wb") as f:
            f.write(b"\0L\0" + os.path.join(vecchia, "Prova.exe").lower().encode("utf-16-le"))


def rimasto():
    return os.path.isdir(vecchia) and all(os.path.exists(x) for x in lnk)


class Tty(io.StringIO):
    def isatty(self):
        return True


vero = sys.stdin
try:
    prepara()
    crew.sys.stdin = io.StringIO("")  # `auto`: in background, senza terminale
    nota = crew.togli_copia_vecchia(app)
    if not rimasto():
        male.append("senza terminale ha cancellato la copia vecchia")
    elif not nota or "rimasta" not in str(nota):
        male.append("senza terminale non dice che la copia vecchia è rimasta")
    crew.sys.stdin = Tty("")
    domande = []
    crew.togli_copia_vecchia(app, chiedi=lambda d: domande.append(d) or False)
    if not domande or not rimasto():
        male.append("col terminale non chiede, o cancella col no")
    crew.togli_copia_vecchia(app, chiedi=lambda d: True)
    if os.path.isdir(vecchia) or any(os.path.exists(x) for x in lnk):
        male.append("col sì non cancella")
    domande.clear()
    if crew.togli_copia_vecchia(app, chiedi=lambda d: domande.append(d) or True) != "" or domande:
        male.append("chiede anche quando non c'è niente da cancellare")
except TypeError as e:
    male.append(f"togli_copia_vecchia non chiede ({e})")
finally:
    crew.sys.stdin = vero

# installa.ps1: prima di `Installa Git.Git` / Python la domanda S/N, saltabile con PLEYADES_SI
ps = open(os.path.join(radice, "installa.ps1"), encoding="utf-8").read()
avvia = ps[ps.find("function Avvia"):]
primo = min((avvia.find(x) for x in ("Installa Git.Git", "Installa Python.") if x in avvia), default=-1)
prima = avvia[:primo]
if primo < 0 or "Read-Host" not in prima or "PLEYADES_SI" not in prima:
    male.append("installa.ps1: winget parte senza chiedere (Read-Host e PLEYADES_SI prima di Installa)")
# installa.sh: softwareupdate (strumenti di Apple) solo dopo la domanda, saltabile con PLEYADES_SI
sh = open(os.path.join(radice, "installa.sh"), encoding="utf-8").read()
su = sh.find("softwareupdate -l")
if su >= 0 and not re.search(r"PLEYADES_SI[\s\S]*read [^\n]*/dev/tty", sh[:su]):
    male.append("installa.sh: strumenti di Apple installati senza chiedere (read da /dev/tty e PLEYADES_SI prima)")

if male:
    sys.exit("test_chiedi_prima: " + "; ".join(male))
print("test_chiedi_prima: ok")
