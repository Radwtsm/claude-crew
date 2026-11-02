#!/usr/bin/env python3
"""`pleyades-cli disinstalla` (owner 02/11): in una casa finta preparata come la lascia il setup, --prova e «No» non
cambiano niente; dopo «Sì» i file tornano com'erano e le cose della persona restano. Nessun programma vero (run finto).
Uso: python3 tools/test_disinstalla.py"""
import importlib.util, json, os, shutil, sys, tempfile

CASA = tempfile.mkdtemp(prefix="casa-")
os.environ["HOME"] = os.environ["USERPROFILE"] = CASA  # Windows: ~ è USERPROFILE
os.environ["LOCALAPPDATA"] = os.path.join(CASA, "AppData", "Local")  # Windows Terminal finto
os.environ["SHELL"] = "/bin/zsh"
spec = importlib.util.spec_from_file_location("crew", os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)
male, chiamate = [], []


def finto(*cmd, **k):
    chiamate.append(cmd)
    if cmd[:2] == ("defaults", "read"):
        return 0, {"com.apple.Terminal": "Pleiad Fire Red"}.get(cmd[2]) or (
            crew.ITERM_GUID if cmd[3] == "Default Bookmark Guid" else "5")
    return (1, "") if cmd[0] == "pgrep" else (0, "")


crew.run = finto
crew.ha = lambda x: False
crew.casa_di_prova = lambda: True
if crew.WIN:  # CredDeleteW non passa da run: senza, cancellerebbe la voce vera
    crew.togli_segreto = lambda *a, **k: chiamate.append(("segreto",)) or True
crew.tema_finestre = lambda togli=False: chiamate.append(("finestre", togli)) or (True, "rimessi")  # registro vero
crew.pianifica = lambda togli=False, rimetti=False: chiamate.append(("pianifica", togli)) or (True, "tolta")


def scrivi(rel, testo):
    p = os.path.join(CASA, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(testo)
    return p


def foto():
    tutto = {}
    for r, _, fs in os.walk(CASA):
        for f in fs:
            p = os.path.join(r, f)
            tutto[os.path.relpath(p, CASA)] = open(p, "rb").read()
    return tutto


class UI:
    def __init__(self, si):
        self.si, self.esiti, self.domande = si, [], 0

    def titolo(self, t): pass

    def info(self, t): pass

    def esito(self, e):
        self.esiti.append(e)

    def conferma(self, *a):
        self.domande += 1
        return self.si


# la casa della persona prima del setup
PERSONA = {".zshrc": "alias ll='ls -l'\n", ".bashrc": 'export A=1\neval "$(starship init bash)"\n',
           ".gitconfig": "[user]\n\tname = Prova\n", os.path.join(".claude", "CLAUDE.md"): "le mie regole\n",
           os.path.join("code", "progetto", "LEGGIMI"): "mio\n", os.path.join("claude-personale", "x.md"): "mio\n"}
for rel, t in PERSONA.items():
    scrivi(rel, t)
impostazioni = {"model": "opus", "enabledPlugins": {"mio@altro": True}}
scrivi(os.path.join(".claude", "settings.json"), json.dumps(impostazioni))
os.makedirs(os.path.join(CASA, "Desktop"))
wt = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows Terminal", "settings.json")
if crew.WIN:
    scrivi(wt, '{"theme": "mio"}')

# il setup: comando e PATH, chiavi di Claude, prompt, salvaschermo, icona, terminale, portachiavi
crew.installa_comando()
crew.impostazioni_utente()
crew.tema(terminale=False)
s = crew.leggi_json(os.path.join(CASA, ".claude", "settings.json"))
s["enabledPlugins"]["nuovo@altro"] = True  # un plugin preso dalla persona dopo il setup: deve restare
crew.scrivi_json(os.path.join(CASA, ".claude", "settings.json"), s)
impostazioni["enabledPlugins"]["nuovo@altro"] = True
if not crew.WIN:
    finta = os.path.join(CASA, "finta-bin")
    scrivi(os.path.join("finta-bin", "starship"), "#!/bin/sh\n")
    os.chmod(os.path.join(finta, "starship"), 0o755)
    os.environ["PATH"] = finta + os.pathsep + os.environ.get("PATH", "")
    crew.tema_prompt()
    shutil.rmtree(finta)
    crew.tema_salvaschermo({"salvaschermo": 5})
    if "salvaschermo" not in open(os.path.join(CASA, ".zshrc"), encoding="utf-8").read() and crew.MAC:
        male.append("preparazione: blocco del salvaschermo mancante")
    crew.icona_desktop(crew.NOME_CLI)
else:
    scrivi(os.path.join("Desktop", "Pleyades tools.lnk"), "lnk")
    shutil.copy(wt, wt + ".prima-di-crew")
    scrivi(wt, '{"theme": "Pleiad Fire Red"}')
if crew.MAC:
    scrivi(os.path.join("Library", "LaunchAgents", crew.PIANO + ".plist"), "plist")
    scrivi(os.path.join("Library", "Application Support", "iTerm2", "DynamicProfiles", "pleyades.json"), "{}")
crew.salva_stato(studio_utente="prova", terminale_messo=True)
if not os.path.isfile(os.path.join(crew.CARTELLA, "crew.py")) or not crew.comandi_crew():
    male.append("preparazione: ~/.crew o i comandi mancanti")

# --prova e «No»: niente cambia
prima = foto()
chiamate.clear()
crew.disinstalla(UI(True), prova=True)
if foto() != prima:
    male.append("--prova ha cambiato dei file")
if any(c[0] == "pianifica" or (c[0] == "powershell" and "GetFolderPath" not in c[-1]) or c[:2] in (("defaults", "write"), ("defaults", "delete"))
       or c[:2] == ("security", "delete-generic-password") or c[0] == "segreto" for c in chiamate):
    male.append(f"--prova ha lanciato dei comandi: {chiamate}")
ui = UI(False)
crew.disinstalla(ui)
if ui.domande != 1 or foto() != prima:
    male.append("«No» ha cambiato dei file (o nessuna domanda)")

# «Sì»: tutto via, le cose della persona come prima
chiamate.clear()
ui = UI(True)
codice = crew.disinstalla(ui)
dopo = foto()
for rel, t in PERSONA.items():
    if dopo.get(rel, b"").decode("utf-8") != t:
        male.append(f"{rel} non torna com'era: {dopo.get(rel)!r}")
s = crew.leggi_json(os.path.join(CASA, ".claude", "settings.json"))
if s != impostazioni:
    male.append(f"settings.json: {s}")
for rel in (".crew", os.path.join(".config", "crew"), os.path.join(".config", "starship.toml"),
            os.path.join(".local", "bin"), os.path.join(".claude", "settings.json.prima-di-crew"),
            os.path.join("Desktop", "Pleyades tools.command"), os.path.join("Desktop", "Pleyades tools.lnk"),
            os.path.join("Desktop", "pleyades-tools.desktop"),
            os.path.join("Library", "Application Support", "iTerm2", "DynamicProfiles", "pleyades.json")):
    if os.path.lexists(os.path.join(CASA, rel)):
        male.append(f"{rel} resta")
if crew.WIN and (open(wt, encoding="utf-8").read() != '{"theme": "mio"}' or os.path.exists(wt + ".prima-di-crew")):
    male.append("Windows Terminal non torna com'era")
attese = [("pianifica", True)] if crew.MAC or crew.WIN else []
if crew.MAC:
    attese += [("security", "delete-generic-password", "-s", "pleyades-studio", "-a", "prova"),
               ("defaults", "delete", "com.googlecode.iterm2", "Default Bookmark Guid"),
               ("defaults", "write", "com.apple.Terminal", "Default Window Settings", "Basic")]
if crew.WIN:
    attese += [c for c in chiamate if c[0] == "powershell" and "SetEnvironmentVariable" in c[-1]][:1] or [("PATH",)]
for c in attese:
    if c not in chiamate:
        male.append(f"non fatto: {' '.join(c)}")
if codice or not all(e.ok for e in ui.esiti):
    male.append(f"esito {codice}: {[(e.nome, e.cosa) for e in ui.esiti if not e.ok]}")

# lo starship.toml della persona (senza il segno) e ~/.local/bin con altri programmi restano
scrivi(os.path.join(".config", "starship.toml"), "format = '$all'\n")
crew.installa_comando()
scrivi(os.path.join(".local", "bin", "claude"), "#!/bin/sh\n")
crew.disinstalla(UI(True))
if not os.path.isfile(os.path.join(CASA, ".config", "starship.toml")):
    male.append("starship.toml della persona cancellato")
if not os.path.isfile(os.path.join(CASA, ".local", "bin", "claude")) or crew.comandi_crew():
    male.append("~/.local/bin: claude tolto o comandi di crew rimasti")
if not crew.WIN and ".local/bin" not in open(os.path.join(CASA, ".zshrc"), encoding="utf-8").read():
    male.append("PATH tolta da .zshrc con claude ancora in ~/.local/bin")

shutil.rmtree(CASA, ignore_errors=True)
if male:
    sys.exit("test_disinstalla: " + "; ".join(male))
print("test_disinstalla: ok")
