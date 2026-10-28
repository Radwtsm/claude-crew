#!/usr/bin/env python3
"""crew: la guida unica per entrare nella crew e nei suoi progetti, anche per chi non programma.

    crew                    la prima volta la guida; poi un menu
    crew guida [OWNER/REPO …]   dall'inizio a tutto pronto: Claude Code, GitHub (con o senza account), plugin,
                            progetti, Nextcloud e la stanza Talk; si può rilanciare: salta ciò che c'è già
    crew entra OWNER/REPO   entra in un progetto (clone, plugin, stanza, cartelle)
    crew controlla          solo i controlli, senza installare niente
    crew aggiorna           crew, plugin e progetti all'ultima versione
    crew progetti           i tuoi progetti e a che punto sono
    crew link               i link giusti (studio, Talk, Dashboard, cartelle)
    crew hook               (per un hook SessionStart) installa i plugin che il progetto aperto chiede e mancano

Un progetto dice cosa gli serve in `.claude/progetto.json` del suo repo (stanza, talk, cartelle, plugin,
marketplace, passi, dopo, moduli); i plugin di `.claude/settings.json` con valore true contano anche loro.
L'indirizzo di Nextcloud viene dal `talk.py` del progetto: questo file è pubblico e non ne contiene.
Mac, Linux e Windows (python3 o python). Solo libreria standard. Le funzioni non stampano: la stampa è in
`Terminale`, così un'app con finestra può riusare le stesse funzioni con un'altra interfaccia.
"""
import hashlib, importlib.util, io, json, os, platform, re, shutil, subprocess, sys, tarfile, threading, time
import urllib.error, urllib.parse, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor

CREW = "Radwtsm/claude-crew"
CREW_PY = "https://raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py"
GH_RELEASE = "https://api.github.com/repos/cli/cli/releases/latest"
CASA = os.path.expanduser("~")
CARTELLA = os.path.join(CASA, ".crew")  # crew.py installato
STATO = os.path.join(CASA, ".config", "crew", "stato.json")  # scelte della persona, mai segreti
BIN = os.path.join(CASA, ".local", "bin")
CODICE = os.path.join(CASA, "code")
WIN, MAC = os.name == "nt", sys.platform == "darwin"
REGOLE_USO = """Regole d'uso (1 minuto):
  1. Un argomento per conversazione; finito, scrivi /clear.
  2. Frasi brevi: cosa vuoi ottenere. «sì» o «1» bastano per rispondere.
  3. Mai password o codici in chat: Claude te li fa scrivere in un comando.
  4. Di un errore solo la parte che conta, o una foto dello schermo.
  5. Lavora sempre nella cartella del progetto.
  6. Quando Claude chiede prima di cancellare o inviare, rispondi pensandoci."""


class Esito:
    """cosa = cosa fare se non va (mostrato solo con ❌); nota = dettaglio mostrato con ✅ o ⏭."""
    def __init__(self, nome, ok, cosa="", saltato=False, nota=""):
        self.nome, self.ok, self.cosa, self.saltato, self.nota = nome, ok, cosa, saltato, nota


# ───────────────────────────── logica (niente stampa) ─────────────────────────────

def run(*cmd, cwd=None, timeout=300, vivo=False):
    """(codice, output). vivo=True: la persona vede e risponde (gh auth login, talk.py collega)."""
    try:
        if vivo:
            return subprocess.run(list(cmd), cwd=cwd).returncode, ""
        r = subprocess.run(list(cmd), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                           timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


def leggi_json(p, base=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return base


def scrivi_json(p, dati):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        json.dump(dati, f, indent=2, ensure_ascii=False)
    os.replace(p + ".tmp", p)


def stato():
    return leggi_json(STATO, {})


def salva_stato(**k):
    s = stato()
    s.update(k)
    scrivi_json(STATO, s)


def path_aggiornato():
    """Ciò che è appena stato installato si trova senza aprire un terminale nuovo."""
    parti = os.environ.get("PATH", "").split(os.pathsep)
    for d in (BIN, "/opt/homebrew/bin", "/usr/local/bin"):
        if os.path.isdir(d) and d not in parti:
            parti.insert(0, d)
    os.environ["PATH"] = os.pathsep.join(parti)


def ha(prog):
    return shutil.which(prog) is not None


def scarica(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "crew/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# Claude Code

def installa_claude():
    if WIN:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
               "irm https://claude.ai/install.ps1 | iex"]
    else:
        cmd = ["bash", "-c", "curl -fsSL https://claude.ai/install.sh | bash"]
    out = run(*cmd, timeout=900)[1]
    path_aggiornato()
    return ha("claude"), out[-400:]


# GitHub

def gh_collegato():
    return ha("gh") and run("gh", "auth", "status")[0] == 0


def gh_utente():
    return run("gh", "api", "user", "-q", ".login")[1].strip() if gh_collegato() else ""


def installa_gh():
    """GitHub CLI dalla pagina ufficiale delle versioni (cli/cli), controllata con il suo file di checksum."""
    sistema = {"darwin": "macOS", "win32": "windows", "linux": "linux"}.get(sys.platform)
    arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "amd64"
    fine = f"_{sistema}_{arch}" + (".tar.gz" if sistema == "linux" else ".zip")
    if not sistema:
        return False, "sistema non riconosciuto"
    try:
        rel = json.loads(scarica(GH_RELEASE))
        asset = {a["name"]: a["browser_download_url"] for a in rel["assets"]}
        nome = next(n for n in asset if n.endswith(fine))
        somme = scarica(asset[next(n for n in asset if n.endswith("_checksums.txt"))]).decode()
        dati = scarica(asset[nome], timeout=300)
    except (OSError, ValueError, KeyError, StopIteration) as e:
        return False, f"download non riuscito ({type(e).__name__} {e})"
    atteso = next((r.split()[0] for r in somme.splitlines() if r.endswith(" " + nome)), "")
    if hashlib.sha256(dati).hexdigest() != atteso:
        return False, "il file scaricato non corrisponde al checksum ufficiale: non lo installo"
    exe = "gh.exe" if WIN else "gh"
    if fine.endswith(".zip"):
        arc = zipfile.ZipFile(io.BytesIO(dati))
        membro = next(n for n in arc.namelist() if ("/" + n).endswith("/bin/" + exe))
        contenuto = arc.read(membro)
    else:
        arc = tarfile.open(fileobj=io.BytesIO(dati))
        membro = next(m for m in arc.getmembers() if ("/" + m.name).endswith("/bin/gh"))
        contenuto = arc.extractfile(membro).read()
    os.makedirs(BIN, exist_ok=True)
    dest = os.path.join(BIN, exe)
    with open(dest, "wb") as f:
        f.write(contenuto)
    os.chmod(dest, 0o755)
    path_aggiornato()
    return ha("gh"), dest


def repo_accessibile(repo):
    """'si', 'no' (privato o inesistente per te) o 'rete'."""
    if gh_collegato():
        return "si" if run("gh", "api", f"repos/{repo}", "-q", ".full_name")[0] == 0 else "no"
    codice, out = run("git", "ls-remote", f"https://github.com/{repo}.git", "HEAD", timeout=30)
    return "si" if codice == 0 else ("rete" if "resolve host" in out.lower() else "no")


def progetti_github():
    """I repo che vedi su GitHub e che hanno .claude/progetto.json (= progetti di cui fai parte)."""
    if not gh_collegato():
        return []
    codice, out = run("gh", "api", "user/repos?per_page=100&sort=pushed&affiliation=owner,collaborator,"
                      "organization_member", "-q", ".[].full_name")
    nomi = out.split()[:40] if codice == 0 else []

    def ha_progetto(r):
        return r if run("gh", "api", f"repos/{r}/contents/.claude/progetto.json", "-q", ".name",
                        timeout=30)[0] == 0 else None
    with ThreadPoolExecutor(8) as ex:
        return [r for r in ex.map(ha_progetto, nomi) if r]


# Plugin di Claude Code

def impostazioni_utente(marketplace=()):
    """HTTPS per i plugin (niente chiave SSH di GitHub) e aggiornamento automatico dei marketplace dati."""
    p = os.path.join(CASA, ".claude", "settings.json")
    s = leggi_json(p, {})
    prima = json.dumps(s, sort_keys=True)
    s.setdefault("env", {})["CLAUDE_CODE_PLUGIN_PREFER_HTTPS"] = "1"
    for nome in marketplace:
        m = s.get("extraKnownMarketplaces", {}).get(nome)
        if isinstance(m, dict):
            m["autoUpdate"] = True  # `marketplace add` lo toglie: rimesso dopo
    if json.dumps(s, sort_keys=True) != prima:
        if os.path.exists(p):
            shutil.copy(p, p + ".prima-di-crew")
        scrivi_json(p, s)
    return all(s.get("extraKnownMarketplaces", {}).get(n, {}).get("autoUpdate") for n in marketplace)


def plugin_installati():
    return run("claude", "plugin", "list")[1]


def assicura_plugin(marketplace, plugin):
    """marketplace = {nome: OWNER/REPO}; plugin = ['nome@marketplace']. Torna (mancanti, auto_update)."""
    lista = run("claude", "plugin", "marketplace", "list")[1]
    for nome, src in marketplace.items():
        if nome not in lista:
            run("claude", "plugin", "marketplace", "add", src)
    inst = plugin_installati()
    for x in plugin:
        if x not in inst:
            run("claude", "plugin", "install", x)
    auto = impostazioni_utente(marketplace)
    inst = plugin_installati()
    return [x for x in plugin if x not in inst], auto


# Progetti

def cartella_progetto(repo):
    nome = repo.split("/")[-1]
    for d in (os.path.join(CODICE, nome), os.path.join(CASA, nome)):  # ~/NOME: il vecchio installa.ps1
        if os.path.isdir(os.path.join(d, ".git")):
            return d
    return os.path.join(CODICE, nome)


def clona(repo):
    d = cartella_progetto(repo)
    if gh_collegato():
        run("gh", "auth", "setup-git")  # git usa l'accesso di gh: pull dei repo privati senza altre password
    if os.path.isdir(os.path.join(d, ".git")):
        codice, out = run("git", "-C", d, "pull", "-q", "--ff-only")
        return True, d, ("" if codice == 0 else "non aggiornato: " + out[:200])
    os.makedirs(os.path.dirname(d), exist_ok=True)
    if gh_collegato():
        codice, out = run("gh", "repo", "clone", repo, d)
    else:
        codice, out = run("git", "clone", "-q", f"https://github.com/{repo}.git", d)
    return codice == 0, d, ("" if codice == 0 else out[-300:])


def config_progetto(d):
    """progetto.json + i plugin attivi in .claude/settings.json del repo."""
    c = leggi_json(os.path.join(d, ".claude", "progetto.json"), {})
    imp = leggi_json(os.path.join(d, ".claude", "settings.json"), {})
    plugin = list(c.get("plugin", [])) + [p for p, on in imp.get("enabledPlugins", {}).items() if on is True]
    c["plugin"] = list(dict.fromkeys(plugin))
    c.setdefault("nome", os.path.basename(d))
    if not c.get("stanza"):
        c["stanza"] = (leggi_json(os.path.join(d, ".claude", "talk.json"), {}) or {}).get("stanza")
    return c


def marketplace_del_progetto(c):
    m = {"claude-crew": CREW}
    m.update(c.get("marketplace", {}))
    serve = {p.split("@", 1)[1] for p in c["plugin"] if "@" in p}
    return {k: v for k, v in m.items() if k in serve or k in c.get("marketplace", {})}


def moduli_del_progetto(c):
    """Aggancio per l'indice dei moduli di S196 (skill e documenti per appartenenza): quando esisterà, qui si
    calcola la vista della persona e si scaricano solo i moduli cambiati. Oggi: la lista dichiarata, niente sync."""
    return c.get("moduli", [])


def hook_git(d):
    if os.path.isdir(os.path.join(d, ".githooks")):
        run("git", "-C", d, "config", "core.hooksPath", ".githooks")
        return True
    return None


# Nextcloud e Talk (tramite il talk.py del progetto, mai una copia qui)

def modulo_talk(d, c):
    p = os.path.join(d, c.get("talk") or "")
    if not c.get("talk") or not os.path.isfile(p):
        return None
    spec = importlib.util.spec_from_file_location("talk_" + re.sub(r"\W", "_", os.path.basename(d)), p)
    try:
        t = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(t)
    except Exception:  # un talk.py rotto non deve fermare la guida
        return None
    return t


def stanza_collegata(t, stanza):
    try:
        return t.conf(stanza or t.STANZA)
    except Exception:
        return None


def collega_stanza(d, c):
    args = [sys.executable, os.path.join(d, c["talk"]), "collega"]
    if c.get("stanza"):
        args.append(f"--stanza={c['stanza']}")
    return run(*args, cwd=d, vivo=True)[0] == 0


def cartelle_mancanti(t, conf, cartelle):
    """Le cartelle condivise del progetto che il tuo utente Nextcloud non vede (WebDAV, password per app)."""
    import base64
    auth = base64.b64encode(f"{conf['utente']}:{conf['password']}".encode()).decode()
    manca = []
    for x in cartelle:
        url = f"{t.SERVER}/remote.php/dav/files/{urllib.parse.quote(conf['utente'])}/{urllib.parse.quote(x)}/"
        req = urllib.request.Request(url, method="PROPFIND", headers={
            "Authorization": "Basic " + auth, "Depth": "0", "User-Agent": getattr(t, "AGENTE", "crew/1.0")})
        try:
            urllib.request.urlopen(req, timeout=15).close()
        except urllib.error.HTTPError:
            manca.append(x)
        except OSError:
            return None  # rete giù: non si sa
    return manca


def app_nextcloud():
    if MAC:
        return os.path.isdir("/Applications/Nextcloud.app")
    if WIN:
        return any(os.path.isfile(os.path.join(os.environ.get(v, ""), "Nextcloud", "nextcloud.exe"))
                   for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"))
    return ha("nextcloud")


def link_progetto(t, conf, c, d):
    out = [("Cartella del progetto", d)]
    if not t:
        return out
    s = t.SERVER
    out += [("Studio (Nextcloud)", s), ("Dashboard", s + "/apps/dashboard/")]
    if conf and conf.get("stanza"):
        out.append((f"Talk · {c.get('stanza') or t.STANZA}", f"{s}/call/{conf['stanza']}"))
    for x in c.get("cartelle", []):
        out.append((f"Cartella «{x}»", f"{s}/apps/files/files?dir=" + urllib.parse.quote("/" + x)))
    return out


def scrivi_in_stanza(d, c, testo):
    args = [sys.executable, os.path.join(d, c["talk"]), "scrivi", testo]
    if c.get("stanza"):
        args.append(f"--stanza={c['stanza']}")
    return run(*args, cwd=d)[0] == 0


# Il comando crew stesso

def installa_comando():
    """~/.crew/crew.py + il comando `crew` in ~/.local/bin (crew.cmd su Windows), nel PATH."""
    os.makedirs(CARTELLA, exist_ok=True)
    qui, dest = os.path.abspath(__file__), os.path.join(CARTELLA, "crew.py")
    if os.path.normcase(qui) != os.path.normcase(dest):
        shutil.copy(qui, dest)
    os.makedirs(BIN, exist_ok=True)
    if WIN:
        with open(os.path.join(BIN, "crew.cmd"), "w", encoding="utf-8") as f:
            f.write(f'@"{sys.executable}" "{dest}" %*\n')
        run("powershell", "-NoProfile", "-Command",
            "$p=[Environment]::GetEnvironmentVariable('Path','User'); $b=\"$HOME\\.local\\bin\"; "
            "if (($p -split ';') -notcontains $b) { [Environment]::SetEnvironmentVariable('Path', \"$p;$b\", 'User') }")
    else:
        lanc = os.path.join(BIN, "crew")
        with open(lanc, "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\nexec "{sys.executable}" "{dest}" "$@"\n')
        os.chmod(lanc, 0o755)
        riga = 'export PATH="$HOME/.local/bin:$PATH"'
        for rc in (".zshrc", ".bashrc") if MAC else (".bashrc",):
            p = os.path.join(CASA, rc)
            testo = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
            if ".local/bin" not in testo:
                with open(p, "a", encoding="utf-8") as f:
                    f.write(f"\n# crew: i comandi in ~/.local/bin (crew, claude, gh)\n{riga}\n")
    path_aggiornato()
    return ha("crew")


def aggiorna_comando():
    """Scarica l'ultima crew.py; la sostituisce solo se è Python valido."""
    try:
        nuovo = scarica(CREW_PY)
        compile(nuovo, "crew.py", "exec")
    except (OSError, SyntaxError, ValueError) as e:
        return False, str(e)
    dest = os.path.join(CARTELLA, "crew.py")
    vecchio = open(dest, "rb").read() if os.path.exists(dest) else b""
    if nuovo == vecchio:
        return True, "già all'ultima versione"
    os.makedirs(CARTELLA, exist_ok=True)
    with open(dest + ".tmp", "wb") as f:
        f.write(nuovo)
    os.replace(dest + ".tmp", dest)
    return True, "aggiornato"


# ───────────────────────────── terminale (la sola parte che stampa) ─────────────────────────────

class Terminale:
    def __init__(self):
        self.colori = sys.stdout.isatty() and not os.environ.get("NO_COLOR") and os.environ.get("TERM") != "dumb"
        for s in (sys.stdout, sys.stderr):
            try:
                s.reconfigure(encoding="utf-8")
            except (AttributeError, ValueError):
                pass
        if WIN and self.colori:  # colori ANSI nella console di Windows (VT)
            try:
                import ctypes
                k = ctypes.windll.kernel32
                h, m = k.GetStdHandle(-11), ctypes.c_uint32()
                if not (k.GetConsoleMode(h, ctypes.byref(m)) and k.SetConsoleMode(h, m.value | 4)):
                    self.colori = False
            except (OSError, AttributeError):
                self.colori = False
        self.esiti = []

    def c(self, codice, t):
        return f"\033[{codice}m{t}\033[0m" if self.colori else t

    def titolo(self, t):
        print("\n" + self.c("1;36", "━━ " + t + " " + "━" * max(3, 60 - len(t))))

    def passo(self, n, tot, t, spiega=""):
        print("\n" + self.c("1;34", f"[{n}/{tot}] {t}"))
        if spiega:
            print(self.c("2", "      " + spiega))

    def info(self, t):
        print("      " + t)

    def fai(self, t):
        """Cosa deve fare la persona: in giallo, con il nome esatto di pulsanti e menu."""
        for r in t.split("\n"):
            print(self.c("33", "   👉 " + r))

    def esito(self, e):
        self.esiti.append(e)
        if e.saltato:
            print(self.c("2", f"   ⏭  {e.nome}" + (f" — {e.nota}" if e.nota else "")))
        elif e.ok:
            print(self.c("32", f"   ✅ {e.nome}") + (self.c("2", f" — {e.nota}") if e.nota else ""))
        else:
            print(self.c("31", f"   ❌ {e.nome}"))
            if e.cosa:
                self.fai(e.cosa)
        return e.ok

    def link(self, nome, url):
        if not url.startswith("http"):
            print(f"   {nome:<30} {self.c('36', url)}")
            return
        print(f"   {nome:<30} {self.c('4;36', url)}")

    def chiedi(self, domanda, base=""):
        try:
            r = input(self.c("1", "   ❓ " + domanda + (f" [{base}]" if base else "") + " ")).strip()
        except EOFError:
            r = ""
        return r or base

    def scegli(self, domanda, opzioni):
        """opzioni = [testo]; la prima è la consigliata. Torna l'indice."""
        print(self.c("1", "   ❓ " + domanda))
        for i, o in enumerate(opzioni, 1):
            print(f"      {self.c('1;36', str(i))}  {o}" + (self.c("2", "  (consigliata)") if i == 1 else ""))
        while True:
            r = self.chiedi("Scrivi il numero e premi Invio:", "1")
            if r.isdigit() and 1 <= int(r) <= len(opzioni):
                return int(r) - 1

    def attesa(self, testo):
        return _Attesa(self, testo)

    def riepilogo(self, minuti):
        fatti = [e for e in self.esiti if e.ok or e.saltato]
        self.titolo(f"Riepilogo: {len(fatti)}/{len(self.esiti)} a posto in {minuti} min")
        for e in self.esiti:
            segno = "⏭ " if e.saltato else ("✅" if e.ok else "❌")
            print(f"   {segno} {e.nome}")
        if len(fatti) < len(self.esiti):
            print(self.c("33", "\n   Fai i passi con ❌ (sopra c'è cosa fare) e rilancia `crew`: salta ciò che è già fatto."))


class _Attesa:
    """Una rotellina mentre un comando lungo lavora (solo in un terminale vero)."""
    def __init__(self, ui, testo):
        self.ui, self.testo, self.fine = ui, testo, threading.Event()

    def __enter__(self):
        if self.ui.colori:
            def gira():
                i = 0
                while not self.fine.wait(0.12):
                    sys.stdout.write("\r      " + self.ui.c("36", "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[i % 10]) + " " + self.testo + " ")
                    sys.stdout.flush()
                    i += 1
            self.t = threading.Thread(target=gira, daemon=True)
            self.t.start()
        else:
            print("      … " + self.testo)

    def __exit__(self, *a):
        self.fine.set()
        if self.ui.colori:
            self.t.join()
            sys.stdout.write("\r" + " " * (len(self.testo) + 10) + "\r")


# ───────────────────────────── i passi della guida ─────────────────────────────

SPIEGA_GH = """GitHub ti fa alcune domande; rispondi così:
  · «Authenticate Git with your GitHub credentials?» → premi Invio (Yes)
  · compare un codice di 8 caratteri (es. ABCD-1234): copialo, poi premi Invio
  · si apre il browser: accedi (o premi «Create an account»), premi «Continue», incolla il codice,
    poi premi «Authorize github» e torna qui"""
SPIEGA_APP = """Serve una «password per app» di Nextcloud (non la tua password: una a parte, solo per questo computer):
  1. apri {s} e accedi con il tuo utente
  2. in alto a destra la tua foto → «Impostazioni personali» → a sinistra «Sicurezza»
  3. in fondo, «Nome dell'app»: scrivi Claude → premi «Crea nuova password per app»
  4. copia la password che compare e incollala qui sotto quando la chiede (non si vede mentre scrivi)"""


def passo_sistema(ui):
    if MAC and run("xcode-select", "-p")[0] != 0:
        run("xcode-select", "--install")
        return ui.esito(Esito("strumenti di Apple (git)", False, "si è aperta la finestra «Strumenti da riga di "
                              "comando»: premi «Installa», aspetta la fine, poi rilancia la stessa riga"))
    if not ha("git"):
        cosa = ("PowerShell: winget install --id Git.Git -e, poi chiudi e riapri PowerShell" if WIN
                else "installa git (es. sudo apt install git) e rilancia")
        return ui.esito(Esito("git", False, cosa))
    return ui.esito(Esito(f"Python {platform.python_version()} e git", True))


def passo_claude(ui):
    path_aggiornato()
    if ha("claude"):
        return ui.esito(Esito("Claude Code", True, saltato=True, nota="già installato"))
    with ui.attesa("installo Claude Code dal sito ufficiale (claude.ai), 1-3 minuti"):
        ok, out = installa_claude()
    return ui.esito(Esito("Claude Code", ok, "" if ok else "chiudi e riapri il terminale, poi rilancia `crew`"
                          + (f" (ultime righe: {out[-150:]})" if out else "")))


def passo_github(ui):
    if gh_collegato():
        salva_stato(github=True)
        return ui.esito(Esito(f"GitHub come {gh_utente()}", True, saltato=True, nota="già collegato"))
    # chiesto a ogni guida finché non sei collegato: si può cambiare idea
    i = ui.scegli("Hai (o vuoi creare) un account GitHub? Serve per i progetti privati e per mandare modifiche.",
                  ["Sì, ho un account o lo creo adesso (gratis)",
                   "No, per ora senza: solo le cose pubbliche (puoi cambiare idea con `crew guida`)"])
    salva_stato(github=(i == 0))
    if i != 0:
        return ui.esito(Esito("GitHub", True, saltato=True, nota="senza account: solo repo pubblici"))
    if not ha("gh"):
        with ui.attesa("installo GitHub CLI (cli.github.com), controllato col checksum ufficiale"):
            ok, out = installa_gh()
        if not ok:
            return ui.esito(Esito("GitHub CLI", False, f"{out}: scaricalo da cli.github.com e rilancia"))
    ui.fai(SPIEGA_GH)
    if ui.chiedi("Premi Invio per cominciare (o scrivi «salta»):").lower() != "salta":
        run("gh", "auth", "login", "--hostname", "github.com", "--web", "--git-protocol", "https", vivo=True)
    if not gh_collegato():
        return ui.esito(Esito("GitHub", False, "accesso non completato: rilancia `crew` e rifai i passi qui sopra"))
    run("gh", "auth", "setup-git")  # git usa lo stesso accesso: repo privati e marketplace privati
    return ui.esito(Esito(f"GitHub come {gh_utente()}", True))


def passo_crew(ui):
    impostazioni_utente()
    with ui.attesa("aggiungo la crew (regole comuni) a Claude Code"):
        manca, auto = assicura_plugin({"claude-crew": CREW}, ["regole@claude-crew"])
    ui.esito(Esito("crew: regole comuni", not manca, "in Claude Code: /plugin install regole@claude-crew"))
    ui.esito(Esito("aggiornamento automatico della crew", auto,
                   "in Claude Code: /plugin → «Marketplaces» → claude-crew → «Enable auto-update»"))
    ok = installa_comando()
    return ui.esito(Esito("comando `crew` (per la prossima volta)", ok,
                          "chiudi e riapri il terminale: poi `crew` funziona da ogni cartella"))


def scegli_progetti(ui, richiesti):
    noti = list(dict.fromkeys(list(richiesti) + stato().get("progetti", [])))
    if not richiesti and gh_collegato():
        with ui.attesa("cerco su GitHub i progetti di cui fai parte"):
            trovati = progetti_github()
        nuovi = [r for r in trovati if r not in noti]
        for r in nuovi:
            if ui.chiedi(f"Fai parte di {r}: lo preparo su questo computer? [s/n]", "s").lower().startswith("s"):
                noti.append(r)
    if not noti and not richiesti:
        r = ui.chiedi("Ti hanno dato il nome di un progetto (es. PROPRIETARIO/NOME)? Scrivilo, o Invio per nessuno:")
        if "/" in r:
            noti.append(r.strip())
    return noti


def passo_progetto(ui, repo):
    """Clone, plugin, hook, Talk, cartelle: un progetto dall'inizio a pronto. Torna (cartella, config, talk)."""
    ui.titolo(f"Progetto {repo}")
    acc = repo_accessibile(repo)
    if acc != "si" and not os.path.isdir(os.path.join(cartella_progetto(repo), ".git")):
        if acc == "rete":
            ui.esito(Esito(repo, False, "GitHub non risponde: controlla internet e rilancia `crew`"))
        elif not gh_collegato():
            ui.esito(Esito(repo, False, "è privato: serve un account GitHub. Rilancia `crew guida`, scegli «Sì», poi "
                           "manda il tuo nome GitHub a chi ti ha invitato"))
        else:
            ui.esito(Esito(repo, False, f"non hai accesso: manda il tuo nome GitHub «{gh_utente()}» a chi ti ha "
                           "invitato, accetta l'invito che arriva per mail (o su github.com → «Notifications»), "
                           "poi rilancia `crew`"))
        return None
    with ui.attesa("scarico il progetto"):
        ok, d, out = clona(repo)
    if not ui.esito(Esito(f"repo in {d.replace(CASA, '~')}", ok, out, nota=out)):
        return None
    c = config_progetto(d)
    if c["plugin"]:
        with ui.attesa("installo i plugin che il progetto chiede"):
            manca, auto = assicura_plugin(marketplace_del_progetto(c), c["plugin"])
        ui.esito(Esito(f"plugin del progetto ({len(c['plugin'])})", not manca,
                       "in Claude Code: /plugin install " + " ".join(manca)))
    if hook_git(d):
        ui.esito(Esito("controlli prima del commit (hook git)", True))
    moduli_del_progetto(c)
    t = modulo_talk(d, c)
    conf = None
    if t:
        conf = stanza_collegata(t, c.get("stanza"))
        nome = c.get("stanza") or t.STANZA
        if not conf:
            ui.fai(SPIEGA_APP.format(s=t.SERVER) + "\nNon hai ancora un utente Nextcloud? Chiedilo a chi ti ha "
                   "invitato e rilancia `crew` quando ce l'hai.")
            if ui.chiedi("Premi Invio per collegarti (o scrivi «salta»):").lower() != "salta":
                collega_stanza(d, c)
            conf = stanza_collegata(t, c.get("stanza"))
        ui.esito(Esito(f"stanza Talk «{nome}»", bool(conf), "rilancia `crew`: ti richiede utente e password per app"))
        if conf and c.get("cartelle"):
            manca = cartelle_mancanti(t, conf, c["cartelle"])
            if manca is not None:
                ui.esito(Esito("cartelle condivise del progetto", not manca,
                               f"non vedi {', '.join(manca)}: chiedi a chi ti ha invitato di condividerle col tuo utente"))
            ui.esito(Esito("app Nextcloud sul computer", app_nextcloud(),
                           "scaricala da nextcloud.com/install («Desktop»), accedi con il tuo utente, poi "
                           "«⋯» → «Scegli cosa sincronizzare» → spunta " + ", ".join(f"«{x}»" for x in c["cartelle"])))
    if c.get("passi") and os.path.isfile(os.path.join(d, c["passi"])):
        ui.info(ui.c("2", f"passi propri del progetto ({c['passi']}):"))
        args = [sys.executable, os.path.join(d, c["passi"]), "--da-crew"]
        if conf:
            args.append(conf["utente"])
        ui.esito(Esito("passi del progetto", run(*args, cwd=d, vivo=True)[0] == 0,
                       f"rilancia `crew entra {repo}` dopo aver fatto ciò che chiede"))
    return d, c, t, conf


def guida(ui, richiesti, solo_progetti=False):
    inizio = time.time()
    ui.titolo("crew · la guida da zero a pronto")
    ui.info("Faccio io quello che posso; quando serve te, te lo dico in giallo con 👉.")
    ui.info("Si può interrompere (Ctrl+C) e rilanciare quando vuoi: salta ciò che è già fatto.")
    if not solo_progetti:
        passi = [("Sistema", "controllo che ci siano Python e git", passo_sistema),
                 ("Claude Code", "il programma di Claude nel terminale", passo_claude),
                 ("GitHub", "dove stanno i progetti: con o senza account", passo_github),
                 ("Crew", "le regole comuni e il comando `crew`", passo_crew)]
        for n, (t, spiega, f) in enumerate(passi, 1):
            ui.passo(n, len(passi) + 1, t, spiega)
            if not f(ui) and f in (passo_sistema, passo_claude):
                ui.riepilogo(round((time.time() - inizio) / 60, 1))
                return 1
        ui.passo(len(passi) + 1, len(passi) + 1, "Progetti", "i progetti di cui fai parte, con stanza e cartelle")
    pronti = []
    for repo in scegli_progetti(ui, richiesti):
        r = passo_progetto(ui, repo)
        if r:
            pronti.append(repo)
            mostra_link(ui, *r)
            for x in r[1].get("dopo", []):
                ui.fai(x)
    if pronti:
        salva_stato(progetti=list(dict.fromkeys(stato().get("progetti", []) + pronti)))
    minuti = round((time.time() - inizio) / 60, 1)
    ui.riepilogo(minuti)
    print("\n" + REGOLE_USO)
    verdi = sum(e.ok or e.saltato for e in ui.esiti)
    for repo in pronti:
        d, c = cartella_progetto(repo), config_progetto(cartella_progetto(repo))
        t = modulo_talk(d, c)
        if t and stanza_collegata(t, c.get("stanza")):
            scrivi_in_stanza(d, c, f"🆕 crew guida su {platform.system()}: {verdi}/{len(ui.esiti)} a posto in "
                             f"{minuti} min ({repo.split('/')[-1]})")
    primo = cartella_progetto(pronti[0]) if pronti else CASA
    ui.titolo("E adesso")
    ui.info(f"Apri il terminale nella cartella {primo.replace(CASA, '~')}, scrivi {ui.c('1', 'claude')} e premi Invio;")
    ui.info("la prima volta scrivi «configura il mio Claude». Per rivedere tutto: " + ui.c("1", "crew"))
    salva_stato(guida_fatta=True)
    return 0 if verdi == len(ui.esiti) else 1


def mostra_link(ui, d, c, t, conf):
    ui.info(ui.c("1", "Link (Cmd+clic su Mac, Ctrl+clic su Windows):"))
    for nome, url in link_progetto(t, conf, c, d):
        ui.link(nome, url)


def controlla(ui):
    path_aggiornato()
    ui.titolo("crew · controllo (non installo niente)")
    ui.esito(Esito("git", ha("git"), "rilancia la riga di installazione"))
    ui.esito(Esito("Claude Code", ha("claude"), "rilancia `crew guida`"))
    ui.esito(Esito("GitHub", gh_collegato(), "rilancia `crew guida` (o va bene così se lavori senza account)",
                   saltato=not stato().get("github") and not gh_collegato()))
    inst = plugin_installati() if ha("claude") else ""
    if inst:
        ui.esito(Esito("crew: regole comuni", "regole@claude-crew" in inst, "rilancia `crew guida`"))
    for repo in stato().get("progetti", []):
        d = cartella_progetto(repo)
        if not os.path.isdir(os.path.join(d, ".git")):
            ui.esito(Esito(repo, False, f"rilancia `crew entra {repo}`"))
            continue
        c = config_progetto(d)
        manca = [p for p in c["plugin"] if ha("claude") and p not in inst]
        ui.esito(Esito(f"{repo}: plugin", not manca, "crew aggiorna"))
        t = modulo_talk(d, c)
        if t:
            ui.esito(Esito(f"{repo}: stanza Talk", bool(stanza_collegata(t, c.get("stanza"))), f"crew entra {repo}"))
    ui.riepilogo(0)
    return 0 if all(e.ok or e.saltato for e in ui.esiti) else 1


def aggiorna(ui):
    ui.titolo("crew · aggiorno tutto")
    ok, cosa = aggiorna_comando()
    ui.esito(Esito("comando crew", ok, cosa, nota=cosa))
    if ha("claude"):
        with ui.attesa("aggiorno i plugin"):
            codice, _ = run("claude", "plugin", "marketplace", "update")
        ui.esito(Esito("plugin (marketplace)", codice == 0, "in Claude Code: /plugin → «Marketplaces» → «Update»"))
    for repo in stato().get("progetti", []):
        d = cartella_progetto(repo)
        if os.path.isdir(os.path.join(d, ".git")):
            ok, d, out = clona(repo)
            ui.esito(Esito(f"{repo}", ok and not out, f"{out[:150]} → apri Claude Code lì e scrivi «aggiorna il repo»"))
            c = config_progetto(d)
            if c["plugin"]:
                manca, _ = assicura_plugin(marketplace_del_progetto(c), c["plugin"])
                ui.esito(Esito(f"{repo}: plugin", not manca, "/plugin install " + " ".join(manca)))
    ui.riepilogo(0)
    return 0


def progetti(ui):
    ui.titolo("crew · i tuoi progetti")
    elenco = stato().get("progetti", [])
    if not elenco:
        ui.info("Nessuno ancora: `crew entra PROPRIETARIO/NOME` o `crew guida`.")
    for repo in elenco:
        d = cartella_progetto(repo)
        c = config_progetto(d) if os.path.isdir(d) else {}
        ui.info(f"{ui.c('1', repo)}  {c.get('nome', '')}  ·  {d.replace(CASA, '~')}"
                + ("" if os.path.isdir(d) else ui.c("31", "  (non scaricato)")))
    return 0


def link(ui):
    ui.titolo("crew · link")
    for repo in stato().get("progetti", []):
        d = cartella_progetto(repo)
        if os.path.isdir(d):
            c = config_progetto(d)
            t = modulo_talk(d, c)
            ui.info(ui.c("1", repo))
            mostra_link(ui, d, c, t, stanza_collegata(t, c.get("stanza")) if t else None)
    return 0


def hook():
    """SessionStart: installa i plugin che il progetto aperto chiede e mancano; una riga, mai un errore."""
    d = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isfile(os.path.join(d, ".claude", "progetto.json")) or not ha("claude"):
        return 0
    c = config_progetto(d)
    inst = plugin_installati()
    serve = [p for p in c["plugin"] if p not in inst]
    if serve:
        manca, _ = assicura_plugin(marketplace_del_progetto(c), serve)
        fatti = [p for p in serve if p not in manca]
        if fatti:
            print(f"crew: installati i plugin del progetto {', '.join(fatti)} (validi dalla prossima sessione)")
    return 0


def menu(ui):
    voci = [("Controlla che sia tutto a posto", controlla), ("Aggiorna crew, plugin e progetti", aggiorna),
            ("I miei progetti", progetti), ("Entra in un nuovo progetto", None), ("I link", link),
            ("Rifai la guida da capo", lambda u: guida(u, []))]
    ui.titolo("crew")
    i = ui.scegli("Cosa vuoi fare?", [v[0] for v in voci] + ["Esci"])
    if i == len(voci):
        return 0
    if voci[i][1] is None:
        r = ui.chiedi("Nome del progetto (PROPRIETARIO/NOME, te lo dà chi ti ha invitato):")
        return guida(ui, [r], solo_progetti=True) if "/" in r else 1
    return voci[i][1](ui)


def main():
    a = sys.argv[1:]
    if a[:1] == ["hook"]:
        try:
            return hook()
        except Exception:
            return 0
    if a[:1] in (["-h"], ["--help"], ["aiuto"]):
        print(__doc__)
        return 0
    path_aggiornato()
    ui = Terminale()
    try:
        if not a:
            return menu(ui) if stato().get("guida_fatta") else guida(ui, [])
        cmd, resto = a[0], [x for x in a[1:] if "/" in x]
        if "/" in cmd:  # come la vecchia riga: installa.sh PROPRIETARIO/REPO
            return guida(ui, a)
        if cmd == "guida":
            return guida(ui, resto)
        if cmd == "entra" and resto:
            return guida(ui, resto, solo_progetti=True)
        f = {"controlla": controlla, "aggiorna": aggiorna, "progetti": progetti, "link": link}.get(cmd)
        if f:
            return f(ui)
        print(f"crew: comando «{cmd}» sconosciuto. `crew --help` per l'elenco.")
        return 2
    except KeyboardInterrupt:
        print("\n   Interrotto. Rilancia `crew` quando vuoi: riparte da dove eri.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
