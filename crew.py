#!/usr/bin/env python3
"""pleyades-cli (Pleyades tools): la guida unica per entrare nei progetti, anche per chi non programma.

    pleyades-cli (o pley)           la prima volta la guida; poi un menu
    pleyades-cli guida [OWNER/REPO …] [--studio=INDIRIZZO]   dall'inizio a tutto pronto: Claude Code, GitHub (con o senza
                            account), plugin, progetti, Nextcloud e la stanza Talk; si può rilanciare: salta il fatto.
                            Con --studio: accesso allo studio Nextcloud dal browser («Concedi accesso», la password
                            per app si salva da sola) e i progetti condivisi lì, anche senza GitHub
    pleyades-cli entra OWNER/REPO   entra in un progetto (clone, plugin, stanza, cartelle)
    pleyades-cli controlla [--talk] solo i controlli, senza installare niente (--talk: riassunto e versioni in ogni stanza)
    pleyades-cli squadra [PROGETTO] chi del progetto è allineato: l'ultimo `controlla --talk` di ognuno nella stanza
                            contro l'ultima versione (comando, commit del progetto, plugin); rosso = da aggiornare
    pleyades-cli aggiorna           pleyades-cli, plugin e progetti all'ultima versione
    pleyades-cli diagnosi           perché questo computer non è allineato: versioni contro le ultime, ultimo `auto` e il
                                    suo log, modifiche non pubblicate; ogni ✗ con il comando che lo sistema (non cambia niente)
    pleyades-cli progetti           i tuoi progetti e a che punto sono
    pleyades-cli link               i link giusti (studio, Talk, Dashboard, cartelle)
    pleyades-cli kit                il tuo kit in base al ruolo: skill, cosa leggere, a chi chiedere
    pleyades-cli auto [--subito]    (hook d'avvio di regole e «📦 Push» nella stanza, in background) aggiorna tutto, poi
                                    `controlla --talk` solo se il riassunto è cambiato o ha più di 3 giorni
    pleyades-cli pianifica [--togli]   l'attività del sistema che lancia `auto` all'accesso e ogni 5 minuti, anche a
                                    Claude chiuso (launchd, Utilità di pianificazione, cron); `auto` la rimette da sola
    pleyades-cli intro [--256] [--resta]   le 7 Pleiadi in pixel art con forme 3D, titolo, frase e nome del tuo
                                    aspetto (un tasto la salta); la prima volta poi chiede l'aspetto; --resta: le
                                    forme girano finché premi un tasto; --256: colori per i terminali vecchi
    pleyades-cli finestre [--togli] (Windows) i colori dell'aspetto su tutto Windows: modo scuro, la tinta su barre del
                                    titolo e bordi (Start e barra delle applicazioni scure); --togli rimette quelli di prima
    pleyades-cli salvaschermo       la scena che fluttua finché premi un tasto, poi lo schermo com'era (parte da sola
                                    dopo i minuti scelti in `aspetto` senza scrivere al prompt)
    pleyades-cli aspetto            il tuo aspetto (nome, titolo, frase, colori, forme 3D) con anteprima, poi
                                    uguale ovunque: Claude, terminale (Mac, iTerm2, Windows Terminal), prompt Starship
    pleyades-cli tema               parole Pleyades nella rotella di Claude + terminale «Pleiad Fire Red» nero con
                                    l'intro (Mac: profilo del Terminale; Windows: Windows Terminal e PowerShell)
    pleyades-cli hook               (per un hook SessionStart) installa i plugin che il progetto aperto chiede e mancano
    pleyades-cli profilo casa|lavoro   che computer è: «lavoro» = solo le regole comuni, niente progetti, Talk o Nextcloud
    pleyades-cli prendi NOME ["perché"] / pleyades-cli togli NOME   un plugin di Pleyades tools solo su questo computer (per il lavoro),
                            segnato in locale con data e motivo; `pleyades-cli aggiorna` non ne aggiunge mai altri

Un progetto dice cosa gli serve in `.claude/progetto.json` del suo repo (stanza, talk, cartelle, plugin,
marketplace, passi, dopo, primo_prompt, moduli, marchio, comando, tipo); i plugin di `.claude/settings.json` con valore true contano anche loro.
`tipo`: «squadra» (l'agenzia: workflow unificati, regole personali, kit) o «progetto» (solo comunicare su quel
progetto, in automatico); senza `tipo` è squadra chi ha `ruolo` o `cartelle`.
L'indirizzo di Nextcloud viene dal `talk.py` del progetto, l'aspetto dal suo `marchio` (se c'è) e `comando` dà un
secondo nome allo stesso programma (es. il nome dello studio): questo file è pubblico e non ne contiene.
Progetti dallo studio: ogni cartella condivisa che contiene `.claude/progetto.json` (copia di sola lettura del repo,
con `.claude-plugin/` e `plugins/`) è un progetto: chi non ha accesso al repo GitHub (`repo` in progetto.json) la
riceve in ~/.crew/studio/ e i suoi plugin come marketplace locale; le proposte vanno nella cartella `proposte`.
Il profilo e i plugin presi stanno solo in ~/.config/crew/stato.json di questo computer: mai inviati a nessuno.
Mac, Linux e Windows (python3 o python). Solo libreria standard. Le funzioni non stampano: la stampa è in
`Terminale`, così un'app con finestra può riusare le stesse funzioni con un'altra interfaccia.
"""
import hashlib, importlib.util, io, json, os, platform, plistlib, re, shutil, subprocess, sys, tarfile, tempfile
import textwrap, threading, time, urllib.error, urllib.parse, urllib.request, uuid, webbrowser
import xml.etree.ElementTree as ET, zipfile
from concurrent.futures import ThreadPoolExecutor

CREW = "Radwtsm/claude-crew"
ALIAS = "pley"  # il nome corto dello stesso comando
NOME_CLI = "pleyades-cli"  # il nome che si vede (owner 28/10: tutto Pleyades tools, niente «crew»)
CREW_PY = "https://raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py"
GH_RELEASE = "https://api.github.com/repos/cli/cli/releases/latest"
CASA = os.path.expanduser("~")
CARTELLA = os.path.join(CASA, ".crew")  # crew.py installato
LOG_AUTO = os.path.join(CARTELLA, "auto.log")  # l'output dell'ultimo `auto` (hook d'avvio di regole)
LOG_PIANO = os.path.join(CARTELLA, "pianificato.log")  # l'output dell'ultimo `auto` lanciato dall'attività del sistema
PIANO = "studio.pleyades.auto"  # nome dell'attività pianificata (launchd; su Windows «Pleyades tools»)
STATO = os.path.join(CASA, ".config", "crew", "stato.json")  # scelte della persona, mai segreti
BIN = os.path.join(CASA, ".local", "bin")
CODICE = os.path.join(CASA, "code")
WIN, MAC = os.name == "nt", sys.platform == "darwin"
# Windows: da `auto` in background (hook staccato, attività pianificata con pythonw) ogni git/claude aprirebbe una
# finestra nera per un attimo
SENZA_FINESTRA: dict = {"creationflags": 0x08000000} if WIN else {}
# senza schermo: collegati via ssh, o Linux senza grafica (es. un server): niente browser da aprire qui
SENZA_SCHERMO = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY")) or \
    (not WIN and not MAC and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")))
SPIEGA_APP_E_CLI = """Claude ha due porte, con le stesse regole, skill e progetti:
  · nel terminale: `claude` nella cartella del progetto (comandi, file, i tool del progetto)
  · nell'app Claude (claude.ai/download), scheda «Code»: scegli la stessa cartella; comoda per leggere e guardare
  Una conversazione per argomento, in tutte e due."""


REGOLE_USO = """Regole d'uso (1 minuto):
  1. Un argomento per conversazione; finito, scrivi /clear.
  2. Frasi brevi: cosa vuoi ottenere. «sì» o «1» bastano per rispondere.
  3. Mai password o codici in chat: Claude te li fa scrivere in un comando.
  4. Di un errore solo la parte che conta, o una foto dello schermo.
  5. Lavora sempre nella cartella del progetto.
  6. Quando Claude chiede prima di cancellare o inviare, rispondi pensandoci."""


class Esito:
    """cosa = cosa fare se non va (mostrato solo con ❌); nota = dettaglio mostrato con ✅ o ⏭."""
    def __init__(self, nome, ok, cosa="", saltato=False, nota="", riprova=None):
        """riprova = funzione che rifà il passo e torna True se ora va: la guida la offre sul posto (owner 28/10:
        tutto in una volta, non rilanciare il comando)."""
        self.nome, self.ok, self.cosa, self.saltato, self.nota, self.riprova = nome, ok, cosa, saltato, nota, riprova


# ───────────────────────────── logica (niente stampa) ─────────────────────────────

def run(*cmd, cwd=None, timeout=300, vivo=False):
    """(codice, output). vivo=True: la persona vede e risponde (gh auth login, talk.py collega)."""
    try:
        if vivo:
            tty = None
            if not WIN and sys.stdout.isatty():  # l'input dal terminale vero (/dev/ttys…), non da /dev/tty: Claude
                tty = open(os.ttyname(sys.stdout.fileno()), "rb")  # Code (Bun) su macOS si ferma con «kqueue EINVAL»
            schermo = SCHERMI[-1] if SCHERMI else None
            if schermo:
                schermo.sospendi()
            try:
                return subprocess.run(list(cmd), cwd=cwd, stdin=tty).returncode, ""
            finally:
                if tty:
                    tty.close()
                if schermo:
                    schermo.riprendi()
        r = subprocess.run(list(cmd), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                           timeout=timeout, **SENZA_FINESTRA)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)


LIVE = []  # la riga di stato aperta (ui.attesa): le funzioni lunghe ci scrivono senza stampare


def live(frazione=None, dettaglio=None):
    if LIVE:
        LIVE[-1].avanza(frazione, dettaglio)


def run_live(*cmd, cwd=None, timeout=900):
    """Come run, ma ogni riga del programma (anche quelle con \\r delle barre) va nella riga di stato live, con la
    percentuale se la riga ne ha una. Torna (codice, output)."""
    try:
        p = subprocess.Popen(list(cmd), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as e:
        return 1, str(e)
    out, resto, fine = [], b"", time.time() + timeout
    while True:
        pezzo = p.stdout.read1(4096)
        if not pezzo:
            break
        righe = re.split(rb"[\r\n]", resto + pezzo)
        resto = righe.pop()
        for r in righe:
            t = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", r.decode("utf-8", "replace")).strip()
            if t:
                out.append(t)
                pc = re.search(r"(\d{1,3})(?:[.,]\d+)?\s?%", t)
                live(int(pc.group(1)) / 100 if pc and int(pc.group(1)) <= 100 else None, t)
        if time.time() > fine:
            p.kill()
            out.append("tempo scaduto")
            break
    return p.wait(), "\n".join(out)


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
    req = urllib.request.Request(url, headers={"User-Agent": "pleyades-cli/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        tot, dati = int(r.headers.get("Content-Length") or 0), bytearray()
        while True:
            pezzo = r.read(65536)
            if not pezzo:
                return bytes(dati)
            dati += pezzo
            if tot > 1_000_000:  # solo i file grossi: la barra con i MB
                live(len(dati) / tot, f"{len(dati) // 1_000_000}/{tot // 1_000_000} MB")


# Claude Code

def installa_claude():
    if WIN:
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
               "irm https://claude.ai/install.ps1 | iex"]
    else:
        cmd = ["bash", "-c", "curl -fsSL https://claude.ai/install.sh | bash"]
    out = run_live(*cmd, timeout=900)[1]
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
    for i, x in enumerate(plugin):
        if x not in inst:
            live(i / len(plugin), x)
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
        codice, out = run_live("gh", "repo", "clone", repo, d, "--", "--progress")
    else:
        codice, out = run_live("git", "clone", "--progress", f"https://github.com/{repo}.git", d)
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


def di_squadra(c):
    """Progetto di squadra (l'agenzia: ruolo, cartelle dello studio) = workflow unificati; altrimenti progetto
    singolo = solo la comunicazione su quel progetto, niente configurazione personale. `tipo` lo dice esplicito."""
    return c.get("tipo") == "squadra" if c.get("tipo") else bool(c.get("ruolo") or c.get("cartelle"))


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
    sys.dont_write_bytecode = True  # niente __pycache__ nel repo del progetto
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
            "Authorization": "Basic " + auth, "Depth": "0", "User-Agent": getattr(t, "AGENTE", "pleyades-cli/1.0")})
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


NEXTCLOUD_RELEASE = "https://api.github.com/repos/nextcloud-releases/desktop/releases/latest"
NEXTCLOUD_TEAM = "Developer ID Installer: Nextcloud GmbH (NKUJUXUJ3B)"  # dalla firma del pacchetto ufficiale, 28/10


def installa_nextcloud():
    """L'app Nextcloud ufficiale: Mac = .pkg delle release di Nextcloud, aperto solo se firmato dal team di Nextcloud e
    notarizzato da Apple (l'installer chiede «Continua/Installa»); Windows = winget. (ok, cosa fare)."""
    if WIN:
        ok = run("winget", "install", "-e", "--id", "Nextcloud.NextcloudDesktop", "--accept-package-agreements",
                 "--accept-source-agreements", timeout=900)[0] == 0
        return ok, "" if ok else "scaricala da nextcloud.com/install («Desktop»)"
    if not MAC:
        return False, "installala con il gestore pacchetti (es. sudo apt install nextcloud-desktop)"
    try:
        rel = json.loads(scarica(NEXTCLOUD_RELEASE))
        url = next(a["browser_download_url"] for a in rel["assets"] if re.fullmatch(r"Nextcloud-[\d.]+\.pkg", a["name"]))
        pkg = os.path.join(CARTELLA, "Nextcloud.pkg")
        os.makedirs(CARTELLA, exist_ok=True)
        with open(pkg, "wb") as f:
            f.write(scarica(url, timeout=900))
    except (OSError, ValueError, StopIteration) as e:
        return False, f"download non riuscito ({e}): controlla internet"
    firma = run("pkgutil", "--check-signature", pkg)[1]
    if NEXTCLOUD_TEAM not in firma or "trusted by the Apple notary service" not in firma:
        os.remove(pkg)
        return False, "il pacchetto scaricato non ha la firma di Nextcloud: non lo apro (scaricala da nextcloud.com/install)"
    run("open", pkg)
    return True, ""


# Le altre app native della suite (29/10, owner: «app native per tutti»): Talk sul computer, Calendario e Contatti
# del sistema (CalDAV/CardDAV), le app ufficiali sul telefono
TALK_RELEASE = "https://api.github.com/repos/nextcloud-releases/talk-desktop/releases/latest"
TALK_MAC = "/Applications/Nextcloud Talk.app"
DAV_PROFILO = "org.pleyades.studio.dav"
APP_TELEFONO = [  # verificati 29/10: App Store (Nextcloud GmbH) e Google Play
    ("Nextcloud (file)", "https://apps.apple.com/app/id1125420102", "com.nextcloud.client"),
    ("Nextcloud Talk", "https://apps.apple.com/app/id1296825574", "com.nextcloud.talk2"),
    ("Nextcloud Notes", "https://apps.apple.com/app/id813973264", "it.niedermann.owncloud.notes"),
    ("Deck (solo Android)", None, "it.niedermann.nextcloud.deck.play"),
    ("DAVx⁵ (calendario, Android)", None, "at.bitfire.davdroid"),
]


def app_talk():
    if MAC:
        return os.path.isdir(TALK_MAC)
    if WIN:
        return run("winget", "list", "-e", "--id", "Nextcloud.Talk", "--accept-source-agreements")[0] == 0
    return True  # Linux: flatpak a mano, la guida non la propone


def installa_talk():
    """Nextcloud Talk per il computer: Mac = .dmg delle release, copiato in Applicazioni solo se firmato dal team di
    Nextcloud e notarizzato da Apple; Windows = winget. (ok, cosa fare)."""
    if WIN:
        ok = run("winget", "install", "-e", "--id", "Nextcloud.Talk", "--accept-package-agreements",
                 "--accept-source-agreements", timeout=900)[0] == 0
        return ok, "" if ok else "scaricala da nextcloud.com/talk («Desktop»)"
    dmg = os.path.join(CARTELLA, "Talk.dmg")
    try:
        rel = json.loads(scarica(TALK_RELEASE))
        url = next(a["browser_download_url"] for a in rel["assets"] if a["name"] == "Nextcloud.Talk-macos-universal.dmg")
        os.makedirs(CARTELLA, exist_ok=True)
        with open(dmg, "wb") as f:
            f.write(scarica(url, timeout=900))
    except (OSError, ValueError, StopIteration) as e:
        return False, f"download non riuscito ({e}): controlla internet"
    disco = tempfile.mkdtemp(prefix="talk-")
    try:
        if run("hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", disco, dmg)[0] != 0:
            return False, "il .dmg non si apre: scaricala da nextcloud.com/talk"
        app = os.path.join(disco, "Nextcloud Talk.app")
        firma = run("codesign", "-dv", app)[1] + run("spctl", "-a", "-vv", "-t", "exec", app)[1]
        if "TeamIdentifier=NKUJUXUJ3B" not in firma or "Notarized Developer ID" not in firma:
            return False, "l'app scaricata non ha la firma di Nextcloud: non la installo (scaricala da nextcloud.com/talk)"
        if run("ditto", app, TALK_MAC)[0] != 0:
            return False, "non riesco a copiarla in Applicazioni: apri ~/.crew/Talk.dmg e trascinala tu"
    finally:
        run("hdiutil", "detach", disco)
        if os.path.isdir(TALK_MAC) and os.path.isfile(dmg):
            os.remove(dmg)
    return True, ""


def profilo_dav_installato():
    return DAV_PROFILO in run("profiles", "list")[1]


def apri_profilo_dav(server, utente):
    """Calendario e Contatti del Mac collegati allo studio: profilo CalDAV + CardDAV SENZA password (la chiede
    Impostazioni di Sistema quando lo installi: una password per app nuova, mai scritta in un file)."""
    host = server.split("//")[-1].rstrip("/")
    principal = f"https://{host}/remote.php/dav/principals/users/{urllib.parse.quote(utente)}/"
    comune = {"PayloadVersion": 1, "PayloadOrganization": "Pleyades Studio"}

    def uid(x):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{x}.{utente}.{host}")).upper()

    dav = [dict(comune, PayloadType="com.apple.caldav.account", PayloadIdentifier=DAV_PROFILO + ".caldav",
                PayloadUUID=uid("caldav"), PayloadDisplayName="Calendario dello studio",
                CalDAVAccountDescription="Pleyades Studio", CalDAVHostName=host, CalDAVPort=443, CalDAVUseSSL=True,
                CalDAVUsername=utente, CalDAVPrincipalURL=principal),
           dict(comune, PayloadType="com.apple.carddav.account", PayloadIdentifier=DAV_PROFILO + ".carddav",
                PayloadUUID=uid("carddav"), PayloadDisplayName="Contatti dello studio",
                CardDAVAccountDescription="Pleyades Studio", CardDAVHostName=host, CardDAVPort=443,
                CardDAVUseSSL=True, CardDAVUsername=utente, CardDAVPrincipalURL=principal)]
    profilo = dict(comune, PayloadType="Configuration", PayloadIdentifier=DAV_PROFILO, PayloadContent=dav,
                   PayloadUUID=uid("profilo"), PayloadDisplayName="Pleyades Studio: calendario e contatti",
                   PayloadScope="User")
    p = os.path.join(CARTELLA, "studio-calendario.mobileconfig")
    os.makedirs(CARTELLA, exist_ok=True)
    with open(p, "wb") as f:
        plistlib.dump(profilo, f)
    run("open", p)
    return p


def app_native(ui, t, conf):
    """Talk, Calendario/Contatti e app del telefono: ognuno chiesto una volta, saltato se c'è già."""
    if (MAC or WIN) and not app_talk() and ui.conferma("Installo l'app Nextcloud Talk (chat e chiamate del team)?",
                                                         "Sì, installala", "Dopo"):
        with ui.attesa("scarico Nextcloud Talk ufficiale (circa 250 MB)"):
            ok, perche = installa_talk()
        ui.esito(Esito("app Nextcloud Talk", ok, perche, riprova=app_talk))
    elif MAC or WIN:
        ui.esito(Esito("app Nextcloud Talk", app_talk(), "pleyades-cli guida (la installa)"))
    if MAC and not profilo_dav_installato() and ui.conferma(
            "Collego Calendario e Contatti del Mac allo studio?", "Sì, collegali", "Dopo"):
        apri_profilo_dav(t.SERVER, conf["utente"])
        ui.fai("Impostazioni di Sistema → Generali → Gestione dispositivi → «Pleyades Studio: calendario e contatti» "
               "→ «Installa»; quando chiede la password, crea una password per app nuova (Nextcloud → Impostazioni "
               "personali → Sicurezza, nome: Calendario Mac)")
        ui.esito(Esito("Calendario e Contatti del Mac", profilo_dav_installato(), "installa il profilo come sopra",
                       riprova=profilo_dav_installato))
    elif MAC:
        ui.esito(Esito("Calendario e Contatti del Mac", True))
    if WIN:
        ui.info("Calendario su Windows: Outlook non legge CalDAV da solo; usa Thunderbird o il calendario nel browser.")
    ui.info(ui.c("2", "sul telefono (cerca il nome nello store o apri il link):"))
    for nome, ios, android in APP_TELEFONO:
        if ios:
            ui.link(nome + " · iPhone", ios)
        ui.link(nome + " · Android", f"https://play.google.com/store/apps/details?id={android}")
    ui.fai(f"iPhone, calendario e contatti: Impostazioni → App → Calendario → Account calendario → Aggiungi account → "
           f"Altro → «Aggiungi account CalDAV»: server {t.SERVER.split('//')[-1]}, utente {conf['utente']}, password "
           f"per app nuova; poi lo stesso con «Aggiungi account CardDAV» (Contatti). Android: DAVx⁵, stesso server.")


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


def scrivi_in_stanza(d, c, testo, stato=None):
    """stato=False/True: il messaggio di stato del computer (`talk.py stato`), modificato sul posto senza notifiche;
    True = è cambiato l'esito, se ne scrive uno nuovo. Un talk.py vecchio senza `stato` → messaggio normale."""
    dove = [f"--stanza={c['stanza']}"] if c.get("stanza") else []
    talk = os.path.join(d, c["talk"])
    if stato is not None and run(sys.executable, talk, "stato", testo, *dove, *(["--nuovo"] if stato else []), cwd=d)[0] == 0:
        return True
    return run(sys.executable, talk, "scrivi", testo, *dove, cwd=d)[0] == 0


# Versioni: `controlla --talk` le scrive in ogni stanza, `squadra` le confronta con l'ultima pubblicata

RE_CONTROLLO = re.compile(r"🔎 pleyades-cli controlla \((?P<sis>[^)]*)\): (?P<ok>\d+)/(?P<tot>\d+) a posto"
                          r"(?: · versioni: (?P<ver>[^·]*))?")


def sha7(dati):
    return hashlib.sha1(dati).hexdigest()[:7]


def versioni(d, c):
    """Questo computer per il progetto: comando (hash di crew.py), progetto (commit; * = modifiche o commit non
    pushati, «studio» = copia dallo studio), marketplace (commit dei plugin installati del progetto)."""
    f = os.path.join(CARTELLA, "crew.py")
    v = {"cli": sha7(open(f if os.path.isfile(f) else __file__, "rb").read())}
    if os.path.isdir(os.path.join(d, ".git")):
        testa = run("git", "-C", d, "rev-parse", "--short=7", "HEAD")[1].strip()
        sporco = run("git", "-C", d, "status", "--porcelain", "-uno")[1].strip() or \
            run("git", "-C", d, "rev-list", "@{u}..HEAD")[1].strip()
        v["progetto"] = testa + ("*" if sporco else "")
    else:
        v["progetto"] = "studio"
    inst = leggi_json(os.path.join(CASA, ".claude", "plugins", "installed_plugins.json"), {}).get("plugins", {})
    for mk in marketplace_del_progetto(c):
        x = [i[0].get("gitCommitSha", "")[:7] for p, i in inst.items() if p in c["plugin"] and p.endswith("@" + mk) and i]
        v[mk] = x[0] if x else "manca"
    return v


def riferimento(d, c, cli):
    """L'ultima versione pubblicata: crew.py su GitHub, il main del progetto, il main di ogni marketplace."""
    def remoto(*a):
        r = run("git", "ls-remote", *a, "HEAD", timeout=30)[1].split()
        return r[0][:7] if r else "?"
    v = {"cli": cli or "?"}
    v["progetto"] = remoto("--", run("git", "-C", d, "remote", "get-url", "origin")[1].strip()) \
        if os.path.isdir(os.path.join(d, ".git")) else "studio"
    for mk, repo in marketplace_del_progetto(c).items():
        v[mk] = remoto(f"https://github.com/{repo}.git")
    return v


# Studio (Nextcloud) senza GitHub: Login Flow v2 e WebDAV

AGENTE_STUDIO = f"pleyades-cli ({platform.system()})"  # il nome del dispositivo nella pagina «Sicurezza» di Nextcloud
STUDIO_DIR = os.path.join(CARTELLA, "studio")


def studio_url(x):
    x = (x or "").strip().rstrip("/")
    return x if not x or "://" in x else urllib.parse.urlunsplit(("https", x, "", "", ""))


def chiama(url, metodo="GET", dati=None, cred=None, intestazioni=None, timeout=30):
    h = {"User-Agent": AGENTE_STUDIO}  # Cloudflare blocca l'agente predefinito di Python (errore 1010)
    if cred:
        import base64
        h["Authorization"] = "Basic " + base64.b64encode(f"{cred['utente']}:{cred['password']}".encode()).decode()
    h.update(intestazioni or {})
    req = urllib.request.Request(url, data=dati, method=metodo, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def inizia_accesso(server):
    """Login Flow v2: (pagina da aprire nel browser, dati per aspettare la risposta)."""
    r = json.loads(chiama(server + "/index.php/login/v2", "POST"))
    return r["login"], r["poll"]


def aspetta_accesso(poll, minuti=15):
    """{utente, password per app} quando la persona preme «Concedi accesso»; None se non arriva in tempo."""
    corpo = urllib.parse.urlencode({"token": poll["token"]}).encode()
    fine = time.time() + minuti * 60
    while time.time() < fine:
        try:
            d = json.loads(chiama(poll["endpoint"], "POST", corpo,
                                  intestazioni={"Content-Type": "application/x-www-form-urlencoded"}))
            return {"utente": d["loginName"], "password": d["appPassword"]}
        except urllib.error.HTTPError as e:
            if e.code != 404:  # 404 = non ancora concesso
                raise
        except (OSError, ValueError):
            pass
        time.sleep(2)
    return None


def _dav(server, cred, percorso=""):
    base = f"/remote.php/dav/files/{urllib.parse.quote(cred['utente'])}/"
    return server + base + urllib.parse.quote(percorso.strip("/")), urllib.parse.unquote(base)


def dav_elenco(server, cred, percorso=""):
    """[(nome, è_cartella)] del contenuto di `percorso` nei file dell'utente."""
    url, base = _dav(server, cred, percorso)
    xml = chiama(url.rstrip("/") + "/", "PROPFIND", b'<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop>'
                 b'<d:resourcetype/></d:prop></d:propfind>', cred, {"Depth": "1", "Content-Type": "application/xml"})
    out, io_stesso = [], percorso.strip("/")
    for r in ET.fromstring(xml).findall("{DAV:}response"):
        rel = urllib.parse.unquote(r.findtext("{DAV:}href", "")).split(base, 1)[-1].strip("/")
        if rel == io_stesso:
            continue
        cartella = r.find(".//{DAV:}resourcetype/{DAV:}collection") is not None
        out.append((rel.rsplit("/", 1)[-1], cartella))
    return out


def dav_leggi(server, cred, percorso):
    return chiama(_dav(server, cred, percorso)[0], cred=cred, timeout=120)


def progetti_studio(server, cred):
    """[(cartella, progetto.json)]: le cartelle condivise con te che sono progetti."""
    out = []
    for nome, cartella in dav_elenco(server, cred):
        if not cartella:
            continue
        try:
            out.append((nome, json.loads(dav_leggi(server, cred, f"{nome}/.claude/progetto.json"))))
        except (OSError, ValueError):
            pass
    return out


def dir_studio(cartella):
    return os.path.join(STUDIO_DIR, re.sub(r"[^a-z0-9]+", "-", cartella.lower()).strip("-"))


def scarica_cartella(server, cred, cartella, dest):
    """Copia locale di una cartella dello studio (sostituita tutta solo quando il download è completo)."""
    nuovo, file = dest + ".nuovo", []

    def giro(rel):
        for nome, sotto in dav_elenco(server, cred, f"{cartella}/{rel}"):
            (giro if sotto else file.append)(f"{rel}/{nome}".strip("/"))
    giro("")
    shutil.rmtree(nuovo, ignore_errors=True)
    for i, f in enumerate(file):
        live(i / max(1, len(file)), f"{i + 1}/{len(file)} file · {f.rsplit('/', 1)[-1]}")
        p = os.path.join(nuovo, *f.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as h:
            h.write(dav_leggi(server, cred, f"{cartella}/{f}"))
    if os.path.isdir(dest):
        shutil.rmtree(dest)  # solo la copia gestita da crew in ~/.crew/studio, mai file della persona
    os.replace(nuovo, dest)
    return len(file)


def salva_credenziali(t, cred):
    """Dove le salva `talk.py collega` (con il suo codice: file solo tuo, permessi 600)."""
    if t.credenziali() != {"utente": cred["utente"], "password": cred["password"]}:  # anche una scaduta va sostituita
        t.scrivi_json(t.CONF, {**(t.leggi_json(t.CONF) or {}), "utente": cred["utente"], "password": cred["password"]})


def cartelle_progetti():
    """(etichetta, cartella) di ogni progetto su questo computer: repo clonati e copie dallo studio."""
    out = [(r, cartella_progetto(r)) for r in stato().get("progetti", [])]
    out += [(c, dir_studio(c)) for c in stato().get("studio_progetti", [])]
    return [(e, d) for e, d in out if os.path.isdir(d)]


def credenziali_note():
    for _, d in cartelle_progetti():
        t = modulo_talk(d, config_progetto(d))
        if t and t.credenziali():
            return t.credenziali()
    return None


# Il comando pleyades-cli stesso

def installa_comando(nome=NOME_CLI, alias=False):
    """~/.crew/crew.py + il comando `nome` in ~/.local/bin (nome.cmd su Windows), nel PATH."""
    os.makedirs(CARTELLA, exist_ok=True)
    qui, dest = os.path.abspath(__file__), os.path.join(CARTELLA, "crew.py")
    if os.path.normcase(qui) != os.path.normcase(dest):
        shutil.copy(qui, dest)
    os.makedirs(BIN, exist_ok=True)
    if WIN:
        with open(os.path.join(BIN, nome + ".cmd"), "w", encoding="utf-8") as f:
            f.write(f'@"{sys.executable}" "{dest}" %*\n')
        run("powershell", "-NoProfile", "-Command",
            "$p=[Environment]::GetEnvironmentVariable('Path','User'); $b=\"$HOME\\.local\\bin\"; "
            "if (($p -split ';') -notcontains $b) { [Environment]::SetEnvironmentVariable('Path', \"$p;$b\", 'User') }")
    else:
        lanc = os.path.join(BIN, nome)
        with open(lanc, "w", encoding="utf-8") as f:
            f.write(f'#!/bin/sh\nexec "{sys.executable}" "{dest}" "$@"\n')
        os.chmod(lanc, 0o755)
        riga = 'export PATH="$HOME/.local/bin:$PATH"'
        for rc in (".zshrc", ".bashrc") if MAC else (".bashrc",):
            p = os.path.join(CASA, rc)
            testo = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
            if ".local/bin" not in testo:
                with open(p, "a", encoding="utf-8") as f:
                    f.write(f"\n# pleyades-cli: i comandi in ~/.local/bin (pleyades-cli, claude, gh)\n{riga}\n")
    if nome == NOME_CLI and not alias:
        installa_comando(ALIAS, alias=True)  # il nome corto, per chi lo usa spesso
    path_aggiornato()
    return ha(nome)


def icona_desktop(nome, png=None):
    """Un'icona «Pleyades tools» sul desktop che apre il comando nel terminale con un doppio clic (per chi non usa
    mai il terminale). Mac: .command (con l'immagine del marchio se c'è), Windows: collegamento, Linux: .desktop."""
    titolo = "Pleyades tools"
    if WIN:
        desk = run("powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')")[1].strip()
        cmd = os.path.join(BIN, nome + ".cmd")
        lnk = os.path.join(desk, titolo + ".lnk")
        ok = run("powershell", "-NoProfile", "-Command",
                 f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); $s.TargetPath='cmd.exe'; "
                 f"$s.Arguments='/k \"{cmd}\"'; $s.WorkingDirectory='{CASA}'; $s.Save()")[0] == 0
        return lnk if ok else None
    desk = os.path.join(CASA, "Desktop")
    if not os.path.isdir(desk):
        return None
    if MAC:
        f = os.path.join(desk, titolo + ".command")
        with open(f, "w", encoding="utf-8") as h:
            h.write(f'#!/bin/sh\nclear\nexec "{os.path.join(BIN, nome)}"\n')
        os.chmod(f, 0o755)
        if png:
            img = os.path.join(CARTELLA, "icona.png")
            os.makedirs(CARTELLA, exist_ok=True)
            with open(img, "wb") as h:
                h.write(png)
            run("osascript", "-l", "JavaScript", "-e", "ObjC.import('AppKit'); $.NSWorkspace.sharedWorkspace."
                f"setIconForFileOptions($.NSImage.alloc.initWithContentsOfFile('{img}'), '{f}', 0)")
        return f
    f = os.path.join(desk, "pleyades-tools.desktop")
    with open(f, "w", encoding="utf-8") as h:
        h.write(f"[Desktop Entry]\nType=Application\nName={titolo}\nExec={os.path.join(BIN, nome)}\nTerminal=true\n")
    os.chmod(f, 0o755)
    return f


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


# Profilo del computer e plugin presi uno per volta (solo locale)

def lavoro():
    return stato().get("profilo") == "lavoro"


def kit_ruolo(d, c, *opz):
    """Lo script `ruolo` del progetto (progetto.json): il kit della persona in base al suo ruolo. (codice, testo)."""
    s = c.get("ruolo") and os.path.join(d, c["ruolo"])
    if not s or not os.path.isfile(s):
        return 1, ""
    return run(sys.executable, s, *opz, cwd=d, timeout=30)


def plugin_del_ruolo(d, c):
    """I plugin della crew che il ruolo chiede e che esistono davvero nel catalogo (mai altro)."""
    codice, out = kit_ruolo(d, c, "--plugin")
    cat = catalogo_crew()
    return [x for x in out.split() if codice == 0 and x.endswith("@claude-crew") and x.split("@")[0] in cat]


def mio_kit(ui):
    ui.intestazione("il mio kit")
    for etichetta, d in cartelle_progetti():
        codice, out = kit_ruolo(d, config_progetto(d))
        if codice == 0 and out:
            print()
            for r in out.splitlines():
                ui.info(r)
    return 0


def catalogo_crew():
    """I plugin della crew (repo pubblico, controllato da check.sh: niente segreti né servizi privati)."""
    m = leggi_json(os.path.join(CASA, ".claude", "plugins", "marketplaces", "claude-crew", ".claude-plugin",
                                "marketplace.json"), {})
    return {p["name"]: p.get("description", "") for p in m.get("plugins", []) if "source" in p
            and str(p["source"]).startswith("./")}  # esclusi i plugin di terzi (esterni.json)


def prendi(nome, perche=""):
    if nome not in catalogo_crew():
        return False, "non è un plugin di Pleyades tools (elenco: `pleyades-cli prendi` senza nome)"
    codice, out = run("claude", "plugin", "install", f"{nome}@claude-crew")
    if codice != 0 and f"{nome}@claude-crew" not in plugin_installati():
        return False, out[-200:]
    presi = [x for x in stato().get("presi", []) if x["cosa"] != nome]
    presi.append({"cosa": nome, "quando": time.strftime("%Y-%m-%d"), "perche": perche})
    salva_stato(presi=presi)
    return True, ""


def togli(nome):
    presi = stato().get("presi", [])
    if not any(x["cosa"] == nome for x in presi):
        return False, "non l'hai preso con `pleyades-cli prendi` (quelli presi: `pleyades-cli controlla`)"
    codice, out = run("claude", "plugin", "uninstall", f"{nome}@claude-crew")
    salva_stato(presi=[x for x in presi if x["cosa"] != nome])
    return codice == 0 or f"{nome}@claude-crew" not in plugin_installati(), out[-200:]


def cantieri_aperti():
    """Le righe di `talk.py cantieri` del primo progetto collegato (operazioni in corso su risorse condivise)."""
    for _, d in cartelle_progetti():
        c = config_progetto(d)
        if c.get("talk") and os.path.isfile(os.path.join(d, c["talk"])):
            codice, out = run(sys.executable, os.path.join(d, c["talk"]), "cantieri", cwd=d, timeout=20)
            return out if codice == 0 else ""
    return ""


def file_marchio():
    if lavoro():
        return None
    for _, d in cartelle_progetti():
        c = config_progetto(d)
        if c.get("marchio") and os.path.isfile(os.path.join(d, c["marchio"])):
            return os.path.join(d, c["marchio"]), c.get("comando") or NOME_CLI
    return None


# ───────────────────────────── terminale (la sola parte che stampa) ─────────────────────────────

def tasto():
    """Un tasto senza Invio: "su", "giu", "invio" o il carattere. Ctrl+C esce come sempre."""
    if WIN:
        import msvcrt
        k = msvcrt.getwch()
        if k in ("\x00", "\xe0"):
            return {"H": "su", "P": "giu"}.get(msvcrt.getwch(), "")
    else:
        import termios, tty
        fd = sys.stdin.fileno()
        prima = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            b = os.read(fd, 1)
            if b == b"\x1b":
                b += os.read(fd, 2)
            elif b and b[0] >= 0xC0:  # una lettera accentata è più byte (UTF-8)
                b += os.read(fd, 1 if b[0] < 0xE0 else 2 if b[0] < 0xF0 else 3)
            k = b.decode(errors="ignore")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, prima)
        k = {"\x1b[A": "su", "\x1bOA": "su", "\x1b[B": "giu", "\x1bOB": "giu"}.get(k, k)
    if k == "\x03":
        raise KeyboardInterrupt
    if k in ("\x7f", "\x08"):
        return "indietro"
    return "invio" if k in ("\r", "\n") else k


SCHERMI = []  # lo schermo intero aperto (uno): run(vivo) lo sospende per i programmi che parlano da sé


def taglia(r, w):
    """Una riga colorata tagliata a w colonne visibili (i codici di colore non contano), mai a capo."""
    out, n, i = [], 0, 0
    while i < len(r):
        m = re.match(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\]8;;[^\x1b]*\x1b\\", r[i:])
        if m:
            out.append(m.group(0))
            i += len(m.group(0))
            continue
        if n >= w - 1 and i < len(r) - 1:
            out.append("…")
            break
        out.append(r[i])
        n += 1
        i += 1
    return "".join(out) + ("\x1b[0m" if "\x1b[" in r else "")


ACCENTO = "38;5;153"  # un solo colore, l'azzurro stella di Pleyades; il resto testo normale o grigio


class Terminale:
    GIRO = "✦✧⋆·⋆✧"  # la stella che pulsa

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
        self.nome = NOME_CLI
        # a schermo intero come Claude Code: in alto il riquadro fermo, in basso la riga di stato ferma, in mezzo il
        # contenuto che scorre; si ridisegna da solo quando la finestra cambia misura (owner 28/10: niente pezzi che
        # si spostano). PLEYADES_SEMPLICE=1 o niente terminale vero = righe normali, come prima.
        self.pieno = self.colori and sys.stdin.isatty() and sys.stdout.isatty() and not os.environ.get("PLEYADES_SEMPLICE")
        self.testa, self.corpo, self.piede, self.ultimo = [], [], "", []
        self.aperto, self.blocco, self.misura = False, threading.RLock(), None

    # ── lo schermo ──
    def apri(self):
        if not self.pieno or self.aperto:
            return
        self.aperto = True
        sys.stdout.write("\033[?1049h\033[?25l")
        SCHERMI.append(self)
        import atexit
        atexit.register(self.chiudi)  # qualunque uscita riporta il terminale normale
        if not WIN:
            try:
                import signal
                signal.signal(signal.SIGWINCH, lambda *_: self.disegna())
            except (ValueError, OSError, AttributeError):
                pass

        def guarda():  # anche su Windows (niente SIGWINCH): controlla la misura 5 volte al secondo
            while self.aperto:
                if shutil.get_terminal_size((80, 24)) != self.misura:
                    self.disegna()
                time.sleep(0.2)
        threading.Thread(target=guarda, daemon=True).start()
        self.disegna()

    def chiudi(self):
        """Torna allo schermo normale e lascia lì il riepilogo, così resta dopo l'uscita."""
        if not self.aperto:
            return
        self.aperto = False
        if self in SCHERMI:
            SCHERMI.remove(self)
        sys.stdout.write("\033[?25h\033[?1049l")
        resta = self.ultimo or "\n".join(self.corpo).strip("\n").split("\n")  # senza riepilogo (squadra, link…):
        resta = [r for r in resta if r]  # resta il resoconto intero, se no il comando sembra non dire niente
        sys.stdout.write("\n".join(resta) + ("\n" if resta else ""))
        sys.stdout.flush()

    def sospendi(self):
        """Per un programma che parla da sé con la persona (accesso a Claude, GitHub…): schermo normale."""
        if self.aperto:
            sys.stdout.write("\033[?25h\033[?1049l")
            sys.stdout.flush()

    def riprendi(self):
        if self.aperto:
            sys.stdout.write("\033[?1049h\033[?25l")
            self.misura = None
            self.disegna()

    def out(self, riga=""):
        if not self.pieno:
            print(riga)
            return
        self.apri()
        with self.blocco:
            self.corpo += riga.split("\n")
            del self.corpo[:-500]
        self.disegna()

    def disegna(self):
        if not self.aperto:
            return
        with self.blocco:
            self.misura = shutil.get_terminal_size((80, 24))
            w, h = self.misura.columns, self.misura.lines
            testa = [taglia(r, w) for r in self.testa] if h >= len(self.testa) + 8 else []
            piede = [self.c("2", "─" * w), taglia(self.piede or self.c("2", "  ↑↓ scegli · Invio conferma · Ctrl+C esci"), w)]
            spazio = max(1, h - len(testa) - len(piede))
            corpo = [taglia(r, w) for r in self.corpo[-spazio:]]
            corpo += [""] * (spazio - len(corpo))
            righe = testa + corpo + piede
            sys.stdout.write("\033[H" + "\r\n".join(r + "\033[K" for r in righe[:h]) + "\033[J")
            sys.stdout.flush()

    def intestazione(self, t):
        """Il riquadro d'apertura, come quello di Claude Code: fermo in alto per tutta la sessione."""
        righe = [self.acc("✦ ") + self.c("1", "Pleyades tools") + self.c("2", f"  {self.nome}"), "  " + t]
        if self.pieno:
            self.testa = self.cornice(righe)
            self.apri()
            self.disegna()
        else:
            self.riquadro(righe + [self.c("2", "  ↑↓ scegli · Invio conferma · Ctrl+C esci (riprende da dove eri)")])

    def cornice(self, righe):
        vis = [len(re.sub(r"\x1b\[[0-9;]*m", "", r)) for r in righe]
        w = self.largo = max(max(vis) + 2, getattr(self, "largo", 0))  # tutti i riquadri larghi uguali
        return ([self.c("2", "╭" + "─" * w + "╮")] + [self.c("2", "│") + " " + r + " " * (w - n - 1) + self.c("2", "│")
                for r, n in zip(righe, vis)] + [self.c("2", "╰" + "─" * w + "╯")])

    def riquadro(self, righe):
        self.out("")
        for r in self.cornice(righe):
            self.out(r)

    def c(self, codice, t):
        return f"\033[{codice}m{t}\033[0m" if self.colori else t

    def acc(self, t):
        return self.c(ACCENTO, t)

    def titolo(self, t):
        self.out("")
        self.out(self.acc("✦") + " " + self.c("1", t))
        self.attacco = True

    def passo(self, n, tot, t, spiega=""):
        """⏺ Passo  n/tot · spiegazione, poi i risultati attaccati sotto con ⎿ (come le azioni di Claude Code)."""
        self.out("")
        self.out(self.acc("⏺") + " " + self.c("1", t) + self.c("2", f"  {n}/{tot}" + (f" · {spiega}" if spiega else "")))
        self.attacco = True

    def rientro(self):
        r = "  ⎿ " if getattr(self, "attacco", False) else "    "
        self.attacco = False
        return self.c("2", r)

    def largo_testo(self):
        return max(40, min(shutil.get_terminal_size((80, 24)).columns - 1, 100))

    def pulisci(self):
        """Schermo pulito, come Claude Code (solo in un terminale vero)."""
        if self.pieno:
            with self.blocco:
                self.corpo = []
            self.disegna()
        elif self.colori and sys.stdout.isatty():
            sys.stdout.write("\033[2J\033[3J\033[H")
            sys.stdout.flush()

    def info(self, t):
        if "\033" in t:  # già colorato: niente a capo calcolati sui codici
            self.out("    " + t)
            return
        self.out(textwrap.fill(t, self.largo_testo(), initial_indent="    ", subsequent_indent="    ",
                               break_on_hyphens=False, break_long_words=False))

    def fai(self, t):
        """Cosa deve fare la persona: in giallo, con il nome esatto di pulsanti e menu."""
        for r in t.split("\n"):
            righe = textwrap.wrap(r, self.largo_testo() - 6, break_on_hyphens=False, break_long_words=False) or [""]
            self.out("    " + self.acc("→") + " " + righe[0])
            for x in righe[1:]:
                self.out("      " + x)

    def esito(self, e):
        self.esiti.append(e)
        if e.saltato:
            self.out(self.rientro() + self.c("2", f"✓ {e.nome}" + (f" · {e.nota}" if e.nota else "")))
        elif e.ok:
            self.out(self.rientro() + self.c("32", "✓") + f" {e.nome}" + (self.c("2", f" · {e.nota}") if e.nota else ""))
        else:
            self.out(self.rientro() + self.c("31", "✗") + f" {e.nome}")
            if e.cosa:
                self.fai(e.cosa)
            tentativi = 0  # mai all'infinito: al massimo 3, e nessuno se non c'è chi risponde (28/10, Windows via Claude)
            while (e.riprova and sys.stdin.isatty() and not getattr(self, "eof", False) and tentativi < 3
                   and self.conferma("Fatto?", "Riprova adesso", "Salta per ora")):
                tentativi += 1
                try:
                    e.ok = bool(e.riprova())
                except Exception as x:  # un errore nel riprovare non ferma la guida
                    self.fai(f"non ancora: {x}")
                if e.ok:
                    self.out("    " + self.c("32", "✓") + f" {e.nome}")
                    break
                self.out("    " + self.c("31", "✗") + f" {e.nome} · ancora no")
        return e.ok

    def link(self, nome, url):
        self.out("    " + self.c("2", f"{nome:<26}") + " " + (self.c("4", url) if url.startswith("http") else url))

    def chiedi(self, domanda, base=""):
        if self.pieno:
            return self._scrivi(domanda, base)
        try:
            r = input("\n  " + self.acc("?") + " " + self.c("1", domanda) + self.c("2", f" [{base}]" if base else "")
                      + "\n  " + self.acc("❯") + " ").strip()
        except EOFError:  # nessuno risponde (lanciato da Claude o da uno script): si va avanti con la scelta base
            self.eof, r = True, ""
        return r or base

    def scegli(self, domanda, opzioni):
        """opzioni = [testo]; la prima è la consigliata. Torna l'indice. Frecce ↑↓ e Invio, come in Claude Code
        (o il numero); senza un terminale vero: scrivi il numero."""
        self.out("")
        self.out("  " + self.acc("?") + " " + self.c("1", domanda))
        if self.colori and sys.stdin.isatty():
            try:
                return self._menu(opzioni)
            except (OSError, ImportError):
                pass  # niente tasti singoli (es. console strana): si ripiega sul numero
        for i, o in enumerate(opzioni, 1):
            self.out(f"    {i}. {o}" + (self.c("2", "  (consigliata)") if i == 1 else ""))
        while True:
            r = self.chiedi("Scrivi il numero e premi Invio:", "1")
            if r.isdigit() and 1 <= int(r) <= len(opzioni):
                return int(r) - 1

    def _menu(self, opzioni):
        def riga(i, o):
            w = self.largo_testo() - 8
            o = o if len(o) <= w else o[:w - 1] + "…"  # una riga per scelta, anche su uno schermo stretto
            nota = self.c("2", "  (consigliata)") if i == 0 and len(o) + 15 <= w else ""
            return (self.acc(f"  ❯ {i + 1}. {o}") if i == sel else f"    {i + 1}. {o}") + nota
        sel, n = 0, len(opzioni)
        if self.pieno:  # le scelte restano ferme al loro posto; dopo, una riga sola con la risposta
            with self.blocco:
                inizio = len(self.corpo)
                self.corpo += [riga(i, o) for i, o in enumerate(opzioni)]
            self.piede = self.c("2", "  ↑↓ per scegliere · Invio per confermare · Ctrl+C esci")
            self.disegna()
            try:
                while True:
                    k = tasto()
                    if k == "invio":
                        break
                    sel = ((sel - 1) % n if k == "su" else (sel + 1) % n if k == "giu" else
                           int(k) - 1 if k.isdigit() and 1 <= int(k) <= n else sel)
                    with self.blocco:
                        self.corpo[inizio:inizio + n] = [riga(i, o) for i, o in enumerate(opzioni)]
                    self.disegna()
            finally:
                self.piede = ""
            with self.blocco:
                self.corpo[inizio:] = ["    " + self.acc("❯ ") + opzioni[sel]]
            self.disegna()
            return sel
        sys.stdout.write("\033[?25l")  # cursore nascosto mentre si sceglie
        try:
            for i, o in enumerate(opzioni):
                print(riga(i, o))
            print(self.c("2", "    ↑↓ per scegliere · Invio per confermare"))
            while True:
                k = tasto()
                if k == "su":
                    sel = (sel - 1) % n
                elif k == "giu":
                    sel = (sel + 1) % n
                elif k.isdigit() and 1 <= int(k) <= n:
                    sel = int(k) - 1
                elif k == "invio":
                    return sel
                else:
                    continue
                sys.stdout.write(f"\033[{n + 1}F")  # torna su e riscrive le opzioni
                for i, o in enumerate(opzioni):
                    sys.stdout.write("\033[2K" + riga(i, o) + "\n")
                sys.stdout.write("\n")
                sys.stdout.flush()
        finally:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

    def _scrivi(self, domanda, base):
        """Una risposta scritta, a schermo intero: si scrive nella riga di stato in basso, ferma."""
        self.out("")
        self.out("  " + self.acc("?") + " " + self.c("1", domanda) + self.c("2", f" [{base}]" if base else ""))
        testo = ""
        sys.stdout.write("\033[?25h")
        try:
            while True:
                self.piede = "  " + self.acc("❯ ") + testo
                self.disegna()
                k = tasto()
                if k == "invio":
                    break
                if k == "indietro":
                    testo = testo[:-1]
                elif len(k) == 1 and k.isprintable():
                    testo += k
        finally:
            self.piede = ""
            sys.stdout.write("\033[?25l")
        self.out("    " + self.acc("❯ ") + (testo.strip() or self.c("2", base or "—")))
        return testo.strip() or base

    def conferma(self, domanda, si="Sì", no="No"):
        """Sì/no con le frecce; la prima (sì) è la consigliata."""
        return self.scegli(domanda, [si, no]) == 0

    def attesa(self, testo):
        return _Attesa(self, testo)

    def riepilogo(self, minuti):
        fatti = [e for e in self.esiti if e.ok or e.saltato]
        tutto = len(fatti) == len(self.esiti)
        righe = [(self.c("32", "✓ ") if tutto else self.acc("✦ ")) + self.c("1", f"{len(fatti)}/{len(self.esiti)} a posto")
                 + self.c("2", f" · {minuti} min")]
        righe += ["  " + self.c("31", "✗") + f" {e.nome}" for e in self.esiti if not (e.ok or e.saltato)]
        if not tutto:
            righe.append(self.c("2", f"  rilancia `{self.nome}`: salta ciò che è già fatto"))
        self.riquadro(righe)
        self.ultimo = self.cornice(righe)  # resta sullo schermo normale dopo l'uscita


class _Attesa:
    """La riga di stato live mentre un passo lungo lavora (solo in un terminale vero): rotellina, testo, barra con
    percentuale quando si sa quanto manca, l'ultima riga del programma che lavora e il tempo passato.
        with ui.attesa("scarico") as a:  a.avanza(0.4, "12/30 file")"""
    def __init__(self, ui, testo):
        self.ui, self.testo, self.fine = ui, testo, threading.Event()
        self.frazione, self.dettaglio, self.inizio = None, "", time.time()

    def avanza(self, frazione=None, dettaglio=None):
        if frazione is not None:
            self.frazione = max(0.0, min(1.0, frazione))
        if dettaglio is not None:
            self.dettaglio = " ".join(str(dettaglio).split())

    def luccica(self, testo):
        """Una luce che scorre sul testo, come quando Claude Code pensa."""
        if not self.ui.colori:
            return testo
        self.k = getattr(self, "k", -1) + 1
        pos = self.k % (len(testo) + 12) - 3
        return "".join(self.ui.c("1", x) if abs(i - pos) <= 1 else self.ui.c("2", x) if abs(i - pos) > 4 else x
                       for i, x in enumerate(testo))

    def riga(self, giro):
        """Sempre dentro la larghezza della finestra (una riga che va a capo sporca lo schermo a ogni giro): si
        accorcia prima il dettaglio, poi la barra, poi il testo."""
        ui, sec = self.ui, int(time.time() - self.inizio)
        tempo = f"{sec // 60}:{sec % 60:02d}" if sec >= 60 else f"{sec} s"
        if self.frazione is not None and 0.03 < self.frazione < 1 and sec >= 5:  # quanto manca, dal ritmo finora
            resta = int(sec * (1 - self.frazione) / self.frazione)
            tempo += f" · ~{resta // 60} min" if resta >= 90 else f" · ~{resta} s"
        w = shutil.get_terminal_size((80, 24)).columns - 1
        lb = 20 if self.frazione is not None else 0
        testo = self.testo
        libero = w - 6 - len(testo) - (lb + 7 if lb else 0) - len(tempo) - 2
        if libero < 0 and lb:
            lb = max(6, lb + libero)
            libero = w - 6 - len(testo) - lb - 7 - len(tempo) - 2
        if libero < 0:
            testo = testo[:max(8, len(testo) + libero - 1)] + "…"
            libero = 0
        dett = self.dettaglio if len(self.dettaglio) + 2 <= libero else ""
        barra = ""
        if lb:
            n = round(self.frazione * lb)
            barra = "  " + ui.acc("━" * n) + ui.c("2", "─" * (lb - n)) + f" {round(self.frazione * 100):3d}%"
        return ("\r    " + ui.acc(giro) + " " + self.luccica(testo) + barra
                + ui.c("2", ("  " + dett if dett else "") + f"  {tempo}") + "\033[K")

    def __enter__(self):
        LIVE.append(self)
        if self.ui.pieno:
            self.ui.apri()

            def gira():
                i = 0
                while not self.fine.wait(0.12):
                    self.ui.piede = self.riga(self.ui.GIRO[i % len(self.ui.GIRO)]).lstrip("\r").replace("\033[K", "")
                    self.ui.disegna()
                    i += 1
            self.t = threading.Thread(target=gira, daemon=True)
            self.t.start()
        elif self.ui.colori:
            def gira():
                i = 0
                while not self.fine.wait(0.12):
                    sys.stdout.write(self.riga(self.ui.GIRO[i % len(self.ui.GIRO)]))
                    sys.stdout.flush()
                    i += 1
            self.t = threading.Thread(target=gira, daemon=True)
            self.t.start()
        else:
            print("    … " + self.testo)
        return self

    def __exit__(self, *a):
        self.fine.set()
        if self in LIVE:
            LIVE.remove(self)
        if self.ui.pieno:
            self.t.join()
            self.ui.piede = ""
            self.ui.disegna()
        elif self.ui.colori:
            self.t.join()
            sys.stdout.write("\r\033[K")


class Marchio(Terminale):
    """Lo stesso Terminale (stessa disposizione) con i colori e l'intestazione del marchio del progetto (`marchio.py`)."""
    TEMA = {"1": ("stella", True), "2": ("fioco", False), "32": ("ok", False), "31": ("errore", False),
            "33": ("avviso", False), ACCENTO: ("brillio", False)}

    def __init__(self, m, nome):
        super().__init__()
        self.m, self.nome = m, nome

    def c(self, codice, t):
        if not self.colori:
            return t
        if codice in self.TEMA:
            colore, forte = self.TEMA[codice]
            return self.m.c(t, colore, forte=forte)
        return super().c(codice, t)

    def intestazione(self, t):
        if not self.pieno:
            return self.m.intestazione(t)
        alto = shutil.get_terminal_size((80, 24)).lines
        if alto >= 32 and hasattr(self.m, "_intestazione"):  # il cielo grande, fermo, se la finestra è alta
            self.testa = self.m._intestazione(t)
            self.apri()
            self.disegna()
        else:
            super().intestazione(t)

    def titolo(self, t):
        self.out("")
        self.out(self.m.c("✦ " + t, "brillio", forte=True) if self.colori else "✦ " + t)


def interfaccia():
    """Il Terminale semplice, o quello col marchio del progetto se ce n'è uno (mai sul computer di lavoro)."""
    f = file_marchio()
    if f:
        sys.dont_write_bytecode = True
        try:
            spec = importlib.util.spec_from_file_location("marchio", f[0])
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return Marchio(m, f[1])
        except Exception:
            pass
    return Terminale()


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


def passo_profilo(ui):
    if "profilo" not in stato():
        i = ui.scegli("Di chi è questo computer?",
                      ["Mio: preparo tutto ciò che serve ai miei progetti",
                       "Dell'azienda (lavoro): solo le regole comuni; il resto lo prendi tu, uno per volta"])
        salva_stato(profilo="lavoro" if i == 1 else "casa")
    if lavoro():
        ui.fai("Computer di lavoro: prima di installare qualcosa controlla le regole della tua azienda (policy IT)\n"
               "su programmi e servizi esterni. Qui installo solo Claude Code e le regole comuni;\n"
               "niente progetti, Talk o Nextcloud. Un plugin in più: `pleyades-cli prendi NOME`.")
        if ui.conferma("Le regole dell'azienda lo permettono?", "No, mi fermo qui", "Sì, continua"):
            return ui.esito(Esito("profilo lavoro", False, "rilancia `pleyades-cli` quando hai controllato"))
        return ui.esito(Esito("profilo: lavoro", True, nota="solo il minimo"))
    return ui.esito(Esito("profilo: casa", True, saltato=True, nota="cambia con `pleyades-cli profilo lavoro`"))


def passo_sistema(ui):
    if MAC and run("xcode-select", "-p")[0] != 0:
        run("xcode-select", "--install")
        return ui.esito(Esito("strumenti di Apple (git)", False, "si è aperta la finestra «Strumenti da riga di "
                              "comando»: premi «Installa» e aspetta la fine",
                              riprova=lambda: run("xcode-select", "-p")[0] == 0))
    if not ha("git"):
        cosa = ("in un'altra finestra di PowerShell: winget install --id Git.Git -e" if WIN
                else "in un altro terminale: sudo apt install git")
        return ui.esito(Esito("git", False, cosa, riprova=lambda: path_aggiornato() or ha("git")))
    return ui.esito(Esito(f"Python {platform.python_version()} e git", True))


def casa_di_prova():
    """HOME spostata (es. una prova in /tmp): diversa dalla casa vera dell'utente del sistema."""
    try:
        import pwd
        return os.path.realpath(CASA) != os.path.realpath(pwd.getpwuid(os.getuid()).pw_dir)
    except (ImportError, KeyError):
        return False


def claude_collegato():
    """Avvisi o righe in più prima del JSON (versione nuova, Windows lento al primo avvio) non vogliono dire «non
    collegato» (owner 28/10: login riuscito ma il controllo diceva di no): si cerca il JSON nell'output."""
    for _ in range(2):
        out = run("claude", "auth", "status", "--json", timeout=90)[1]
        m = re.search(r'"loggedIn"\s*:\s*(true|false)', out)
        if m:
            return m.group(1) == "true"
        if re.search(r"(?i)logged in|signed in", out) and not re.search(r"(?i)not (logged|signed) in", out):
            return True  # versione senza --json
    return False


SPIEGA_CLAUDE = """Accesso a Claude: serve un account Claude (claude.ai) con un abbonamento Pro o Max.
Si apre il browser: accedi (o crea l'account) e premi «Autorizza», poi torna qui."""


def passo_claude(ui):
    path_aggiornato()
    if ha("claude"):
        ui.esito(Esito("Claude Code", True, saltato=True, nota="già installato"))
    else:
        with ui.attesa("installo Claude Code dal sito ufficiale (claude.ai), 1-3 minuti"):
            ok, out = installa_claude()
        if not ui.esito(Esito("Claude Code", ok, "" if ok else "controlla internet"
                              + (f" (ultime righe: {out[-150:]})" if out else ""), riprova=lambda: installa_claude()[0])):
            return False
    if claude_collegato():
        return ui.esito(Esito("accesso a Claude", True, saltato=True, nota="già fatto"))
    if MAC and casa_di_prova():  # il Portachiavi sta nella casa vera: l'accesso non si salverebbe (login all'infinito)
        return ui.esito(Esito("accesso a Claude", True, saltato=True, nota="cartella di casa di prova: lo salto"))
    if SENZA_SCHERMO:  # niente browser qui: il link lungo non si apre né si copia bene da un terminale remoto
        return ui.esito(Esito("accesso a Claude", True, saltato=True,
                              nota="dopo: apri `claude` e scrivi /login (computer senza schermo)"))
    ui.fai(SPIEGA_CLAUDE)

    tentativi = [0]

    def accedi():
        tentativi[0] += 1
        if tentativi[0] > 2:  # accesso fatto ma non salvato: non farlo rifare all'infinito
            raise RuntimeError("l'accesso non si salva su questo computer: salta, poi apri `claude` e scrivi /login")
        run("claude", "auth", "login", vivo=True)
        return claude_collegato()
    ui.esito(Esito("accesso a Claude", ui.conferma("Accediamo a Claude?", "Sì, apri il browser", "Dopo") and
                   accedi(), "accedi con il tuo account Claude", riprova=accedi))
    return True  # senza accesso la guida va avanti: lo chiede Claude la prima volta che si apre


def passo_github(ui):
    if gh_collegato():
        salva_stato(github=True)
        return ui.esito(Esito(f"GitHub come {gh_utente()}", True, saltato=True, nota="già collegato"))
    # chiesto a ogni guida finché non sei collegato: si può cambiare idea
    i = ui.scegli("Hai (o vuoi creare) un account GitHub? Serve per i progetti privati e per mandare modifiche.",
                  ["Sì, ho un account o lo creo adesso (gratis)",
                   "No, per ora senza: solo le cose pubbliche (puoi cambiare idea con `pleyades-cli guida`)"])
    salva_stato(github=(i == 0))
    if i != 0:
        return ui.esito(Esito("GitHub", True, saltato=True, nota="senza account: solo repo pubblici"))
    if not ha("gh"):
        with ui.attesa("installo GitHub CLI (cli.github.com), controllato col checksum ufficiale"):
            ok, out = installa_gh()
        if not ok:
            return ui.esito(Esito("GitHub CLI", False, f"{out}: scaricalo da cli.github.com e rilancia"))
    ui.fai(SPIEGA_GH)
    if ui.conferma("Colleghiamo GitHub?", "Sì, apri il browser", "Salta per ora"):
        run("gh", "auth", "login", "--hostname", "github.com", "--web", "--git-protocol", "https", vivo=True)
    def accedi():
        run("gh", "auth", "login", "--hostname", "github.com", "--web", "--git-protocol", "https", vivo=True)
        return gh_collegato()
    if not ui.esito(Esito("GitHub", gh_collegato(), "accesso non completato: rifai i passi qui sopra", riprova=accedi)):
        return False
    run("gh", "auth", "setup-git")  # git usa lo stesso accesso: repo privati e marketplace privati
    return ui.esito(Esito(f"GitHub come {gh_utente()}", True))


def passo_crew(ui):
    impostazioni_utente()
    with ui.attesa("aggiungo le regole comuni a Claude Code"):
        manca, auto = assicura_plugin({"claude-crew": CREW}, ["regole@claude-crew"])
    ui.esito(Esito("regole comuni", not manca, "in Claude Code: /plugin install regole@claude-crew"))
    ui.esito(Esito("aggiornamento automatico delle regole comuni", auto,
                   "in Claude Code: /plugin → «Marketplaces» → claude-crew → «Enable auto-update»"))
    ok = installa_comando()
    return ui.esito(Esito("comando `pleyades-cli` (per la prossima volta)", ok,
                          "chiudi e riapri il terminale: poi `pleyades-cli` funziona da ogni cartella"))


def scegli_progetti(ui, richiesti):
    noti = list(dict.fromkeys(list(richiesti) + stato().get("progetti", [])))
    if not richiesti and gh_collegato():
        with ui.attesa("cerco su GitHub i progetti di cui fai parte"):
            trovati = progetti_github()
        nuovi = [r for r in trovati if r not in noti]
        for r in nuovi:
            if ui.conferma(f"Fai parte di {r}: lo preparo su questo computer?"):
                noti.append(r)
    if not noti and not richiesti:
        r = ui.chiedi("Ti hanno dato il nome di un progetto (es. PROPRIETARIO/NOME)? Scrivilo, o Invio per nessuno:")
        if "/" in r:
            noti.append(r.strip())
    return noti


SPIEGA_ACCESSO = """Accesso allo studio: si apre il browser su Nextcloud.
  1. se chiede un codice: scrivi la tua mail, poi incolla il codice che ti arriva
  2. «Accedi» con il tuo utente e la tua password (e il codice dell'app di verifica, se ce l'hai)
  3. premi «Concedi accesso»: la password per questo computer si salva da sola, non la vedi mai
  Se chiede di «confermare la password»: è la tua password di Nextcloud, non il codice della mail; non la ricordi →
  apri il link in una finestra in incognito e accedi da capo"""


def accedi_studio(ui, server):
    ui.fai(SPIEGA_ACCESSO)
    if not ui.conferma("Entriamo nello studio?", "Sì, apri il browser", "Salta per ora"):
        return None
    try:
        pagina, poll = inizia_accesso(server)
    except (OSError, ValueError, KeyError) as e:
        ui.esito(Esito("accesso allo studio", False, f"lo studio non risponde ({e}): controlla internet e rilancia"))
        return None
    webbrowser.open(pagina)
    ui.info("Se il browser non si è aperto, apri tu questo link:")
    ui.link("Accesso allo studio", pagina)
    with ui.attesa("aspetto che premi «Concedi accesso» nel browser (fino a 15 min)"):
        cred = aspetta_accesso(poll)
    return cred


def passo_studio(ui):
    """I progetti condivisi nello studio. Torna [(etichetta, risultato di prepara)]."""
    if lavoro():
        return []
    s = stato()
    if "studio" not in s:
        x = ui.chiedi("Ti hanno dato l'indirizzo di uno studio Nextcloud (es. studio.nome.org)? Scrivilo, o Invio se no:")
        salva_stato(studio=studio_url(x))
    server = stato().get("studio")
    if not server:
        return []
    ui.titolo(f"Studio {server.split('//')[-1]}")
    cred = credenziali_note()
    if cred:  # password cambiata o accesso revocato = 401: si rifà «Concedi accesso», non a mano (28/10, luco)
        try:
            dav_elenco(server, cred)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                ui.info("L'accesso salvato allo studio non vale più (password cambiata?): lo rifacciamo.")
                cred = None
        except (OSError, ValueError):
            pass
    tieni = [cred or accedi_studio(ui, server)]

    def di_nuovo():
        tieni[0] = accedi_studio(ui, server)
        return tieni[0]
    if not ui.esito(Esito("accesso allo studio", bool(tieni[0]), "premi «Concedi accesso» nel browser; senza utente: "
                          "chiedilo a chi ti ha invitato", riprova=di_nuovo)):
        return []
    cred = tieni[0]
    try:
        with ui.attesa("cerco i progetti condivisi con te"):
            trovati = progetti_studio(server, cred)
    except urllib.error.HTTPError as e:
        ui.esito(Esito("progetti dello studio", False, f"lo studio ha risposto {e.code}: rilancia `pleyades-cli`; se si ripete, "
                       "dillo a chi ti ha invitato"))
        return []
    if not trovati:
        ui.esito(Esito("progetti dello studio", True, saltato=True, nota="nessuno condiviso con te per ora"))
    out, copie = [], []
    for cartella, cfg in trovati:
        repo = cfg.get("repo")
        if repo and (os.path.isdir(os.path.join(cartella_progetto(repo), ".git")) or
                     (gh_collegato() and repo_accessibile(repo) == "si")):
            r = passo_progetto(ui, repo, cred)  # con GitHub: il repo vero, come sempre
            if r:
                out.append((repo, r))
                salva_stato(progetti=list(dict.fromkeys(stato().get("progetti", []) + [repo])))
            continue
        ui.titolo(f"Progetto {cfg.get('nome', cartella)} (dallo studio)")
        d = dir_studio(cartella)
        def scarica(cartella=cartella, d=d):
            with ui.attesa(f"scarico «{cartella}» dallo studio"):
                return scarica_cartella(server, cred, cartella, d)
        try:
            n = scarica()
        except (OSError, ValueError) as e:
            if not ui.esito(Esito(f"copia di «{cartella}»", False, f"download interrotto ({e}): controlla internet",
                                  riprova=scarica)):
                continue
            n = sum(len(f) for _, _, f in os.walk(d))
        ui.esito(Esito(f"copia di «{cartella}» in {d.replace(CASA, '~')}", True, nota=f"{n} file, sola lettura"))
        copie.append(cartella)
        out.append((cartella, prepara(ui, d, config_progetto(d), cartella, cred, studio=True)))
    if copie:
        salva_stato(studio_progetti=list(dict.fromkeys(stato().get("studio_progetti", []) + copie)))
    return out


def passo_progetto(ui, repo, cred=None):
    """Clone, plugin, hook, Talk, cartelle: un progetto dall'inizio a pronto. Torna (cartella, config, talk)."""
    ui.titolo(f"Progetto {repo}")
    acc = repo_accessibile(repo)
    if acc != "si" and not os.path.isdir(os.path.join(cartella_progetto(repo), ".git")):
        if acc == "rete":
            ui.esito(Esito(repo, False, "GitHub non risponde: controlla internet e rilancia `pleyades-cli`"))
        elif not gh_collegato():
            ui.esito(Esito(repo, False, "è privato: serve un account GitHub. Rilancia `pleyades-cli guida`, scegli «Sì», poi "
                           "manda il tuo nome GitHub a chi ti ha invitato"))
        else:
            ui.esito(Esito(repo, False, f"non hai accesso: manda il tuo nome GitHub «{gh_utente()}» a chi ti ha "
                           "invitato, accetta l'invito che arriva per mail (o su github.com → «Notifications»), "
                           "poi rilancia `pleyades-cli`"))
        return None
    with ui.attesa("scarico il progetto"):
        ok, d, out = clona(repo)
    if not ui.esito(Esito(f"repo in {d.replace(CASA, '~')}", ok, out, nota=out)):
        return None
    return prepara(ui, d, config_progetto(d), repo, cred)


def prepara(ui, d, c, etichetta, cred=None, studio=False):
    """Plugin, hook, Talk, cartelle e passi di un progetto già su questo computer (repo o copia dallo studio)."""
    mk = marketplace_del_progetto(c)
    locale = (leggi_json(os.path.join(d, ".claude-plugin", "marketplace.json"), {}) or {}).get("name")
    if studio and locale:
        mk[locale] = d  # marketplace locale: la copia dello studio al posto del repo GitHub
    if c["plugin"]:
        with ui.attesa("installo i plugin che il progetto chiede"):
            manca, auto = assicura_plugin(mk, c["plugin"])
        ui.esito(Esito(f"plugin del progetto ({len(c['plugin'])})", not manca,
                       "in Claude Code: /plugin install " + " ".join(manca)))
    ruolo = plugin_del_ruolo(d, c)
    if ruolo:
        with ui.attesa("installo le skill del tuo ruolo") as a:
            manca, _ = assicura_plugin({"claude-crew": CREW}, ruolo)
        ui.esito(Esito(f"skill del tuo ruolo ({len(ruolo)})", not manca, "pleyades-cli aggiorna",
                       nota=", ".join(x.split("@")[0] for x in ruolo)))
    if hook_git(d):
        ui.esito(Esito("controlli prima del commit (hook git)", True))
    moduli_del_progetto(c)
    t = modulo_talk(d, c)
    conf = None
    if t:
        if cred:  # dallo studio, appena controllate: sostituiscono una password per app scaduta (Talk 401)
            salva_credenziali(t, cred)
        conf = stanza_collegata(t, c.get("stanza"))
        nome = c.get("stanza") or t.STANZA
        if not conf:
            if not t.credenziali():
                cred = cred or credenziali_note() or accedi_studio(ui, t.SERVER)
                if cred:
                    salva_credenziali(t, cred)
            if t.credenziali():
                collega_stanza(d, c)  # le credenziali ci sono: non chiede niente
            else:
                ui.fai(SPIEGA_APP.format(s=t.SERVER) + "\nNon hai ancora un utente Nextcloud? Chiedilo a chi ti ha "
                       "invitato e rilancia `pleyades-cli` quando ce l'hai.")
                if ui.conferma("Ti colleghi a mano?", "Sì, collegami", "Salta per ora"):
                    collega_stanza(d, c)
            conf = stanza_collegata(t, c.get("stanza"))
        ui.esito(Esito(f"stanza Talk «{nome}»", bool(conf), "ti richiede utente e password per app",
                       riprova=lambda: collega_stanza(d, c) or stanza_collegata(t, c.get("stanza"))))
        conf = stanza_collegata(t, c.get("stanza"))
        if conf and c.get("cartelle"):
            manca = cartelle_mancanti(t, conf, c["cartelle"])
            if manca is not None:
                ui.esito(Esito("cartelle condivise del progetto", not manca,
                               f"non vedi {', '.join(manca)}: chiedi a chi ti ha invitato di condividerle col tuo utente"))
            spunta = ", ".join(f"«{x}»" for x in c["cartelle"])
            cosa = f"apri Nextcloud, accedi con il tuo utente ({t.SERVER.split('//')[-1]}), poi spunta {spunta}"
            if not app_nextcloud() and ui.conferma("Installo l'app Nextcloud (sincronizza le cartelle del progetto)?",
                                                   "Sì, installala", "Dopo"):
                with ui.attesa("scarico l'app Nextcloud ufficiale (circa 150 MB)"):
                    ok, perche = installa_nextcloud()
                if ok and MAC:
                    ui.fai("Si è aperto l'installer di Apple: premi «Continua» e «Installa» (chiede la password del Mac)")
                cosa = perche or cosa
            ui.esito(Esito("app Nextcloud sul computer", app_nextcloud(), cosa, riprova=app_nextcloud))
        if conf:
            app_native(ui, t, conf)
    if studio and c.get("proposte"):
        ui.fai(f"Questa è una copia di sola lettura: le tue proposte (skill, processi, modifiche) vanno nella cartella "
               f"«{c['proposte']}» dello studio; Claude le porta con la skill porta-proposte.")
    if not studio and c.get("passi") and os.path.isfile(os.path.join(d, c["passi"])):
        ui.info(ui.c("2", f"passi propri del progetto ({c['passi']}):"))
        args = [sys.executable, os.path.join(d, c["passi"]), "--da-crew"]
        if conf:
            args.append(conf["utente"])
        ui.esito(Esito("passi del progetto", run(*args, cwd=d, vivo=True)[0] == 0, "fai ciò che chiede qui sopra",
                       riprova=lambda: run(*args, cwd=d, vivo=True)[0] == 0))
    return d, c, t, conf


def guida(ui, richiesti, solo_progetti=False):
    inizio = time.time()
    ui.pulisci()
    ui.intestazione("la guida da zero a pronto")
    ui.info("Faccio io quello che posso; quando serve te, te lo dico con →.")
    if solo_progetti and lavoro():
        ui.esito(Esito("progetti", False, "computer di lavoro: i progetti non si installano qui "
                       "(se è davvero tuo: `pleyades-cli profilo casa`)"))
        return 1
    if not solo_progetti:
        passi = [("Questo computer", "tuo o dell'azienda: decide cosa installo", passo_profilo),
                 ("Sistema", "controllo che ci siano Python e git", passo_sistema),
                 ("Claude Code", "il programma di Claude nel terminale", passo_claude),
                 ("GitHub", "dove stanno i progetti: con o senza account", passo_github),
                 ("Pleyades tools", "le regole comuni e il comando `pleyades-cli`", passo_crew)]
        for n, (t, spiega, f) in enumerate(passi, 1):
            ui.passo(n, len(passi) + 1, t, spiega)
            if not f(ui) and f in (passo_profilo, passo_sistema, passo_claude):
                ui.riepilogo(round((time.time() - inizio) / 60, 1))
                return 1
        if not lavoro():
            ui.passo(len(passi) + 1, len(passi) + 1, "Progetti", "i progetti di cui fai parte, con stanza e cartelle")
    pronti = []  # (etichetta, (cartella, config, talk, conf))
    if not solo_progetti:
        pronti += passo_studio(ui)
    fatti = {e for e, _ in pronti} | {r[1].get("repo") for _, r in pronti}  # copia dallo studio = quel repo
    scelti = richiesti if solo_progetti else scegli_progetti(ui, richiesti)  # entra X = solo X
    for repo in ([] if lavoro() else [x for x in scelti if x not in fatti]):
        r = passo_progetto(ui, repo)
        if r:
            pronti.append((repo, r))
            salva_stato(progetti=list(dict.fromkeys(stato().get("progetti", []) + [repo])))
    for _, r in pronti:
        if r[1].get("comando"):
            installa_comando(r[1]["comando"])
    if pronti and type(ui) is Terminale and file_marchio():  # il progetto ha un marchio: da qui in poi il suo aspetto
        nuova = interfaccia()
        if isinstance(nuova, Marchio):  # stesso schermo, stessi esiti: cambia solo l'aspetto
            ui.__class__, ui.m, ui.nome = Marchio, nuova.m, nuova.nome
    if pronti and file_marchio():
        m = getattr(ui, "m", None)
        f = icona_desktop(file_marchio()[1], m.png_sfondo(512, 512) if m and hasattr(m, "png_sfondo") else None)
        ui.esito(Esito("icona «Pleyades tools» sul desktop", bool(f), "", saltato=f is None and not WIN,
                       nota="doppio clic per aprire la guida" if f else "niente cartella Scrivania"))
    for _, r in pronti:
        mostra_link(ui, *r)
        for x in r[1].get("dopo", []):
            ui.fai(x)
    if not lavoro():  # da subito si allinea da solo, senza aspettare il primo avvio di Claude
        ok, cosa = pianifica()
        ui.esito(Esito("aggiornamento automatico pianificato", ok, f"{cosa} → `{NOME_CLI} pianifica`", nota=cosa))
        if not stato().get("tema_proposto") and sys.stdin.isatty():
            salva_stato(tema_proposto=True)
            if ui.conferma("Metto il look Pleyades? Terminale nero con l'intro delle Pleiadi e Claude dello stesso colore",
                           "Sì, mettilo", "No, grazie"):
                voce_tema(ui)
    minuti = round((time.time() - inizio) / 60, 1)
    ui.riepilogo(minuti)
    ui.titolo("Regole d'uso")
    for r in REGOLE_USO.split("\n")[1:]:
        ui.info(r.strip())
    verdi = sum(e.ok or e.saltato for e in ui.esiti)
    manca = [e.nome for e in ui.esiti if not (e.ok or e.saltato)]  # chi aiuta vede subito cosa, senza chiederlo
    for etichetta, (d, c, t, conf) in pronti:
        if t and stanza_collegata(t, c.get("stanza")):
            scrivi_in_stanza(d, c, (f"🆕 pleyades-cli guida su {platform.system()}: {verdi}/{len(ui.esiti)} a posto in "
                                    f"{minuti} min ({etichetta.split('/')[-1]})"
                                    + (" · manca: " + ", ".join(manca) if manca else ""))[:390])
    if pronti and not lavoro():  # il primo 🔎 con le versioni: `squadra` lo vede subito (28/10: luco «senza controllo»)
        subprocess.Popen([sys.executable, os.path.join(CARTELLA, "crew.py"), "auto", "--subito"], cwd=CASA,
                         stdin=subprocess.DEVNULL, stdout=open(LOG_AUTO, "w", encoding="utf-8"), stderr=subprocess.STDOUT,
                         env={**os.environ, "NO_COLOR": "1"}, **({"creationflags": 0x00000008 | 0x00000200} if WIN
                                                              else {"start_new_session": True}))
    primo = pronti[0][1][0] if pronti else CASA
    for _, (d, c, t, conf) in pronti:  # il kit del ruolo a portata di mano, prima di cominciare
        codice, out = kit_ruolo(d, c)
        if codice == 0 and out:
            ui.titolo("Il tuo kit")
            for r in out.splitlines()[1:]:
                ui.info(r.strip())
    ui.titolo("E adesso")
    ui.info(f"Nel terminale, nella cartella {primo.replace(CASA, '~')}: scrivi {ui.c('1', 'claude')} e premi Invio.")
    ui.info(f"Per rivedere tutto: {ui.c('1', file_marchio()[1] if pronti and file_marchio() else ui.nome)}")
    for r in SPIEGA_APP_E_CLI.split("\n"):
        ui.info(r.strip())
    prima = not stato().get("guida_fatta")
    salva_stato(guida_fatta=True)
    primo_prompt = pronti[0][1][1].get("primo_prompt") if pronti else None
    if prima and primo_prompt and ha("claude") and ui.conferma(
            "Apro Claude qui? Finisce lui: le tue regole, il CLAUDE.md, la tua scheda", "Sì, apri Claude", "Dopo"):
        run("claude", primo_prompt, cwd=primo, vivo=True)  # la prima conversazione, già nella cartella giusta
    return 0 if verdi == len(ui.esiti) else 1


def mostra_link(ui, d, c, t, conf):
    ui.info(ui.c("1", "Link (Cmd+clic su Mac, Ctrl+clic su Windows):"))
    for nome, url in link_progetto(t, conf, c, d):
        ui.link(nome, url)


def controlla(ui):
    path_aggiornato()
    ui.titolo(f"{ui.nome} · controllo (non installo niente)")
    ui.info(f"Profilo di questo computer: {stato().get('profilo', 'non scelto')}")
    ui.esito(Esito("git", ha("git"), "rilancia la riga di installazione"))
    ui.esito(Esito("Claude Code", ha("claude"), "rilancia `pleyades-cli guida`"))
    ui.esito(Esito("GitHub", gh_collegato(), "rilancia `pleyades-cli guida` (o va bene così se lavori senza account)",
                   saltato=not stato().get("github") and not gh_collegato()))
    inst = plugin_installati() if ha("claude") else ""
    if inst:
        ui.esito(Esito("regole comuni", "regole@claude-crew" in inst, "rilancia `pleyades-cli guida`"))
        for x in stato().get("presi", []):
            ui.esito(Esito(f"preso: {x['cosa']}", f"{x['cosa']}@claude-crew" in inst, f"crew prendi {x['cosa']}",
                           nota=f"dal {x['quando']}" + (f", {x['perche']}" if x.get("perche") else "")))
    for repo in stato().get("progetti", []):
        if not os.path.isdir(os.path.join(cartella_progetto(repo), ".git")):
            ui.esito(Esito(repo, False, f"rilancia `pleyades-cli entra {repo}`"))
    in_squadra = False
    for repo, d in cartelle_progetti():
        c = config_progetto(d)
        in_squadra = in_squadra or di_squadra(c)
        manca = [p for p in c["plugin"] if ha("claude") and p not in inst]
        ui.esito(Esito(f"{repo}: plugin", not manca, "pleyades-cli aggiorna"))
        t = modulo_talk(d, c)
        if t:
            ui.esito(Esito(f"{repo}: stanza Talk", bool(stanza_collegata(t, c.get("stanza"))), f"pleyades-cli entra {repo}"))
        ruolo = plugin_del_ruolo(d, c)
        if ruolo:
            manca = [p for p in ruolo if p not in inst]
            ui.esito(Esito(f"{repo}: skill del ruolo", not manca, "pleyades-cli aggiorna", nota=", ".join(manca)))
        codice, kit = kit_ruolo(d, c)
        if codice == 0 and kit:
            ui.esito(Esito(f"{repo}: scheda con Ambiti", "Nessuna scheda" not in kit and "da scegliere" not in kit,
                           "apri Claude nella cartella del progetto e chiedi «prepara la mia scheda»"))
        if c.get("cartelle"):
            ui.esito(Esito("app Nextcloud", app_nextcloud(), "pleyades-cli guida (la installa)"))
        if t and (MAC or WIN):
            ui.esito(Esito("app Nextcloud Talk", app_talk(), "pleyades-cli guida (la installa)"))
        if t and MAC:
            ui.esito(Esito("Calendario e Contatti del Mac", profilo_dav_installato(), "pleyades-cli guida (li collega)"))
    if ha("claude") and not lavoro():
        ui.esito(Esito("accesso a Claude", claude_collegato(), "apri `claude` e scrivi /login; se il login è già "
                       "riuscito: `claude auth status` nello stesso terminale e manda la risposta (senza email)"))
    if ha("claude") and not lavoro() and in_squadra:  # solo l'agenzia unifica i workflow; un progetto singolo no
        cm = os.path.join(CASA, ".claude", "CLAUDE.md")
        eccezione = "@~/claude-rules/" in (open(cm, encoding="utf-8").read() if os.path.isfile(cm) else "")
        ui.esito(Esito("regole personali (claude-personale)", os.path.isdir(os.path.join(CASA, "claude-personale")),
                       "in Claude Code: «configura il mio Claude»", saltato=eccezione,  # lo standard è claude-personale;
                       nota="claude-rules del manutentore" if eccezione else ""))  # claude-rules = il setup del manutentore
    eta = (time.time() - os.path.getmtime(os.path.join(CARTELLA, "crew.py"))) / 86400 \
        if os.path.isfile(os.path.join(CARTELLA, "crew.py")) else 99
    if not lavoro():
        ok, cosa = pianifica()
        ui.esito(Esito("aggiornamento automatico pianificato", ok, f"{cosa} → `{NOME_CLI} pianifica`", nota=cosa))
    ui.esito(Esito("pleyades-cli aggiornato", eta < 2, "pleyades-cli aggiorna", nota=f"{eta:.0f} giorni fa"))
    ui.riepilogo(0)
    if "--talk" in sys.argv:  # il riassunto in ogni stanza; `pleyades-cli squadra` confronta le versioni di tutti
        manca = [e.nome for e in ui.esiti if not (e.ok or e.saltato)]
        testo = f"🔎 pleyades-cli controlla ({platform.system()}): {len(ui.esiti) - len(manca)}/{len(ui.esiti)} a posto"
        dove = [d for _, d in cartelle_progetti()]
        qui = run("git", "rev-parse", "--show-toplevel")[1].strip()  # un progetto non ancora «entra»: quello aperto
        if not dove and qui and os.path.isfile(os.path.join(qui, ".claude", "progetto.json")):
            dove = [qui]
        scritti, uguali, inviati = 0, 0, stato().get("talk_inviati", {})
        for d in dove:
            c = config_progetto(d)
            if c.get("talk"):
                v = " ".join(f"{k}={x}" for k, x in versioni(d, c).items())
                msg = (f"{testo} · versioni: {v}" + (" · manca: " + ", ".join(manca) if manca else ""))[:390]
                prima = inviati.get(d, {})
                if "--se-cambiato" in sys.argv and prima.get("msg") == msg and time.time() - prima.get("t", 0) < 3 * 86400:
                    uguali += 1  # già nella stanza e recente: squadra lo vede ancora
                    continue
                # cambiano solo le versioni (un push qualunque) → si modifica il messaggio di prima, senza notifiche
                esito = msg.split(" · versioni:")[0] + (" · manca: " + ", ".join(manca) if manca else "")
                if scrivi_in_stanza(d, c, msg, stato=prima.get("esito") != esito):
                    scritti += 1
                    inviati[d] = {"msg": msg, "esito": esito, "t": time.time()}
        salva_stato(talk_inviati=inviati)
        nota = (f"riassunto in {scritti} stanze" if scritti else "riassunto invariato, già nella stanza" if uguali else
                "nessuna stanza: `pleyades-cli entra PROPRIETARIO/REPO` o lancialo dalla cartella del progetto")
        ui.info(nota)
        ui.ultimo = ui.ultimo + [ui.c("2", "  " + nota)] if getattr(ui, "ultimo", None) else []  # resta dopo l'uscita
    return 0 if all(e.ok or e.saltato for e in ui.esiti) else 1


def squadra(ui):
    """Chi del progetto è allineato: l'ultimo «🔎 controlla --talk» di ognuno nella stanza contro l'ultima versione."""
    filtro = ([x for x in sys.argv[2:] if not x.startswith("-")] or [""])[0]
    indietro, senza = [], []
    try:
        cli = sha7(scarica(CREW_PY))
    except (OSError, ValueError):
        cli = None
    for repo, d in cartelle_progetti():
        if filtro not in repo:
            continue
        c = config_progetto(d)
        t = modulo_talk(d, c)
        conf = t and stanza_collegata(t, c.get("stanza"))
        ui.titolo(f"{ui.nome} · squadra · {c['nome']}")
        if not conf:
            ui.esito(Esito("stanza Talk", False, f"pleyades-cli entra {repo}"))
            continue
        with ui.attesa("leggo la stanza e l'ultima versione"):
            rif = riferimento(d, c, cli)
            try:
                ultimi = {}
                for m in t.messaggi(conf, 200):
                    r = RE_CONTROLLO.search(m.get("message", ""))
                    if r:
                        ultimi[(m.get("actorDisplayName") or "?", r.group("sis"))] = (m, r)
                persone = {p.get("displayName") for p in t.api(conf, "GET", f"/v4/room/{conf['stanza']}/participants")
                           if p.get("actorType") == "users"}
            except Exception as e:  # rete giù o accesso scaduto: lo dice e passa al progetto dopo
                ultimi, persone = None, str(e)[:120]
        if ultimi is None:
            ui.esito(Esito("stanza Talk", False, f"rete o accesso: {persone}"))
            continue
        ui.info("ultima versione: " + " ".join(f"{k}={x}" for k, x in rif.items()))
        for (nome, sis), (m, r) in sorted(ultimi.items()):
            v = dict(x.split("=", 1) for x in (r.group("ver") or "").split() if "=" in x)
            diverso = [f"{k}={v.get(k, '?')}" for k, x in rif.items() if v.get(k) != x]
            ora = m.get("lastEditTimestamp") or m["timestamp"]  # lo stato si aggiorna modificando il messaggio
            giorni = (time.time() - ora) / 86400
            ui.esito(Esito(f"{nome} ({sis})", not diverso and r.group("ok") == r.group("tot") and giorni < 7,
                           f"lì: pleyades-cli aggiorna, poi pleyades-cli controlla --talk · "
                           + (f"diverso: {' '.join(diverso)}" if diverso else f"{r.group('ok')}/{r.group('tot')}")
                           + (f" · controllo di {giorni:.0f} giorni fa" if giorni >= 7 else ""),
                           nota=f"{r.group('ok')}/{r.group('tot')} · {time.strftime('%d/%m %H:%M', time.localtime(ora))}"))
        fatti = {n for n, _ in ultimi}
        mai = sorted(persone - fatti - {n[len("claude-"):] for n in fatti if n.startswith("claude-")})  # il suo Claude
        indietro += [e.nome for e in ui.esiti if not e.ok and e.nome != "stanza Talk"]
        senza += mai
        if mai:
            ui.info("nella stanza, senza controllo: " + ", ".join(mai) + " (`pleyades-cli controlla --talk`)")
    if not filtro:  # l'hook d'avvio di regole lo dice al Claude di ognuno (allineamento = priorità assoluta)
        salva_stato(squadra={"t": time.time(), "indietro": sorted(set(indietro)), "senza": sorted(set(senza))})
    return 0 if all(e.ok or e.saltato for e in ui.esiti) else 1


def aggiorna(ui):
    ui.titolo(f"{ui.nome} · aggiorno ciò che c'è già")
    ok, cosa = aggiorna_comando()
    ui.esito(Esito("comando pleyades-cli", ok, cosa, nota=cosa))
    server, cred = stato().get("studio"), credenziali_note()
    for cartella in ([] if lavoro() or not (server and cred) else stato().get("studio_progetti", [])):
        try:
            with ui.attesa(f"riallineo «{cartella}» dallo studio"):
                n = scarica_cartella(server, cred, cartella, dir_studio(cartella))
            ui.esito(Esito(f"copia di «{cartella}»", True, nota=f"{n} file"))
        except (OSError, ValueError) as e:
            ui.esito(Esito(f"copia di «{cartella}»", False, f"{e}: rilancia `pleyades-cli aggiorna`"))
    if ha("claude"):
        with ui.attesa("aggiorno i plugin"):
            codice, _ = run("claude", "plugin", "marketplace", "update")
        ui.esito(Esito("plugin (marketplace)", codice == 0, "in Claude Code: /plugin → «Marketplaces» → «Update»"))
        mk = {"claude-crew"} | {m for _, d in cartelle_progetti() for m in marketplace_del_progetto(config_progetto(d))}
        inst = leggi_json(os.path.join(CASA, ".claude", "plugins", "installed_plugins.json"), {}).get("plugins", {})
        tutti = [p for p in inst if p.split("@")[-1] in mk]
        ko = []
        with ui.attesa("porto i plugin all'ultima versione"):  # il catalogo da solo non li cambia (squadra)
            for i, p in enumerate(tutti):
                live(i / len(tutti), p)
                if run("claude", "plugin", "update", p)[0] != 0:
                    ko.append(p)
        ui.esito(Esito(f"plugin installati ({len(tutti)})", not ko, "/plugin update " + " ".join(ko),
                       nota="valgono dalla prossima sessione di Claude Code"))
    for repo in ([] if lavoro() else stato().get("progetti", [])):
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
    ui.titolo(f"{ui.nome} · i tuoi progetti")
    elenco = cartelle_progetti()
    if not elenco:
        ui.info("Nessuno ancora: `pleyades-cli entra PROPRIETARIO/NOME` o `pleyades-cli guida`.")
    for repo, d in elenco:
        ui.info(f"{ui.c('1', repo)}  {config_progetto(d).get('nome', '')}  ·  {d.replace(CASA, '~')}")
    return 0


def link(ui):
    ui.titolo(f"{ui.nome} · link")
    for repo, d in cartelle_progetti():
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
            print(f"pleyades-cli: installati i plugin del progetto {', '.join(fatti)} (validi dalla prossima sessione)")
    return 0


def teste_remote():
    """L'ultimo commit di ogni repo da cui arriva qualcosa (crew.py, progetti, marketplace): pochi `git ls-remote`."""
    url, nomi = set(), {CREW}
    for _, d in cartelle_progetti():
        c = config_progetto(d)
        if os.path.isdir(os.path.join(d, ".git")):
            url.add(run("git", "-C", d, "remote", "get-url", "origin")[1].strip())
        nomi |= set(marketplace_del_progetto(c).values())
    url |= {f"https://github.com/{repo}.git" for repo in nomi}
    with ThreadPoolExecutor(8) as ex:
        teste = ex.map(lambda r: (run("git", "ls-remote", "--", r, "HEAD", timeout=30)[1].split() or ["?"])[0][:7],
                       sorted(x for x in url if x))
    return " ".join(teste)


def auto(ui):
    """Hook d'avvio e attività pianificata (in background): tutti gli strumenti all'ultima versione prima di lavorare,
    poi il controllo nella stanza se è cambiato; l'esito resta in stato.json e l'hook lo dice a Claude al prossimo
    avvio. L'attività gira ogni 5 minuti: senza commit nuovi da nessuna parte esce dopo pochi `ls-remote`."""
    ultimo = stato().get("auto", {})
    fa = time.time() - ultimo.get("t", 0)
    if "--leggero" in sys.argv and fa < 6 * 3600:
        t = teste_remote()
        if "?" not in t and t == ultimo.get("teste") and (ultimo.get("esito") == "ok" or fa < 1800):
            return 0  # niente di nuovo pubblicato (owner 28/10: allineamento in pochi minuti); un ✗ si riprova ogni 30'
    if "--leggero" not in sys.argv and time.time() - ultimo.get("t", 0) < (60 if "--subito" in sys.argv else 1800):
        return 0  # più sessioni aperte di seguito: una volta ogni mezz'ora basta; --subito = un push nella stanza
    blocco = os.path.join(CARTELLA, "auto.lock")  # attività + avvio di Claude insieme: i due `claude plugin` si pestano
    try:
        os.close(os.open(blocco, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        if time.time() - os.path.getmtime(blocco) < 900:
            return 0
        os.utime(blocco)  # rimasto da un giro interrotto
    try:
        return giro_auto(ui)
    finally:
        os.remove(blocco)


def giro_auto(ui):
    teste = teste_remote()  # prima del giro: un push arrivato durante il giro lo rifà quello dopo
    salva_stato(auto={"t": time.time(), "esito": "in corso"})
    aggiorna(ui)
    ko = [e.nome for e in ui.esiti if not (e.ok or e.saltato)]
    ui.esiti = []
    sys.argv += ["--talk", "--se-cambiato"]
    controlla(ui)
    ko += [e.nome for e in ui.esiti if not (e.ok or e.saltato)]
    ok, cosa = pianifica()
    if not ok:
        ko.append(f"attività pianificata ({cosa})")
    salva_stato(auto={"t": time.time(), "esito": "ok" if not ko else "da sistemare: " + ", ".join(dict.fromkeys(ko)),
                      "teste": teste})
    ui.esiti = []
    squadra(ui)
    return 0


def pianifica(togli=False):
    """L'allineamento anche a Claude chiuso (owner 28/10: imposto, non affidato a chi riapre Claude): un'attività del
    sistema lancia `auto` all'accesso e ogni 5 minuti. Si rimette da sola a ogni `auto`. Torna (ok, cosa)."""
    if lavoro():
        return True, "computer di lavoro: niente attività pianificate"
    crew = os.path.join(CARTELLA, "crew.py")
    if WIN:
        pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")  # senza finestra
        tr = f'"{pyw if os.path.isfile(pyw) else sys.executable}" "{crew}" auto --leggero'
        if togli:
            return run("schtasks", "/Delete", "/TN", "Pleyades tools", "/F")[0] == 0, "tolta"
        if tr in run("schtasks", "/Query", "/TN", "Pleyades tools", "/V", "/FO", "LIST")[1]:
            return True, "attiva (Utilità di pianificazione, ogni 5 minuti)"
        c, out = run("schtasks", "/Create", "/TN", "Pleyades tools", "/SC", "MINUTE", "/MO", "5", "/TR", tr, "/F")
        return c == 0, "attivata (Utilità di pianificazione, ogni 5 minuti)" if c == 0 else out[:200]
    if MAC:
        p = os.path.join(CASA, "Library", "LaunchAgents", PIANO + ".plist")
        dominio = f"gui/{os.getuid()}"
        dati = plistlib.dumps({
            "Label": PIANO, "ProgramArguments": [sys.executable, crew, "auto", "--leggero"], "RunAtLoad": True,
            "StartInterval": 300, "ProcessType": "Background", "StandardOutPath": LOG_PIANO,
            "StandardErrorPath": LOG_PIANO, "EnvironmentVariables": {
                "PATH": f"{BIN}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin", "NO_COLOR": "1"}})
        uguale = os.path.isfile(p) and open(p, "rb").read() == dati
        if uguale and not togli and run("launchctl", "print", f"{dominio}/{PIANO}")[0] == 0:
            return True, "attiva (launchd, ogni 5 minuti)"
        run("launchctl", "bootout", f"{dominio}/{PIANO}")
        if togli:
            if os.path.isfile(p):
                os.remove(p)
            return True, "tolta"
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(dati)
        c, out = run("launchctl", "bootstrap", dominio, p)
        return c == 0, "attivata (launchd, ogni 5 minuti)" if c == 0 else out[:200]
    if not ha("crontab"):
        return False, f"manca crontab: fai partire `{NOME_CLI} auto` all'accesso"
    attuale = run("crontab", "-l")[1]
    riga = f'*/5 * * * * NO_COLOR=1 "{sys.executable}" "{crew}" auto --leggero >"{LOG_PIANO}" 2>&1'
    if not togli and riga in attuale:
        return True, "attiva (cron, ogni 5 minuti)"
    resto = [r for r in attuale.splitlines() if r.strip() and f'"{crew}" auto' not in r and not r.startswith("no crontab")]
    r = subprocess.run(["crontab", "-"], input="\n".join(resto + ([] if togli else [riga])) + "\n", text=True,
                       capture_output=True)
    return r.returncode == 0, ("tolta" if togli else "attivata (cron, ogni 5 minuti)") if r.returncode == 0 else r.stderr[:200]


def diagnosi(ui):
    """Per il Claude di chi è indietro (skill `ripara-allineamento`): tutto in una volta, senza cambiare niente; ogni ✗
    dice la causa probabile e il comando che la sistema."""
    ui.titolo(f"{ui.nome} · diagnosi dell'allineamento (non cambio niente)")
    ui.info(f"{platform.system()} {platform.release()} · python {platform.python_version()} · "
            f"comando: {shutil.which(NOME_CLI) or 'non nel PATH'} · claude: {shutil.which('claude') or 'non trovato'}")
    try:
        cli = sha7(scarica(CREW_PY))
    except (OSError, ValueError) as e:
        cli = None
        ui.esito(Esito("GitHub raggiungibile", False, f"rete, proxy o antivirus: {str(e)[:120]}"))
    f = os.path.join(CARTELLA, "crew.py")
    mio = sha7(open(f, "rb").read()) if os.path.isfile(f) else "manca"
    ui.esito(Esito("pleyades-cli", cli is None or mio == cli, f"`{NOME_CLI} aggiorna`; se resta uguale e il push è "
                   "di pochi minuti fa, GitHub serve ancora la versione vecchia (cache ~5 min): riprova fra poco",
                   nota=mio + (f", ultima {cli}" if cli and cli != mio else "")))
    a = stato().get("auto", {})
    esito, quando = a.get("esito", "mai partito"), a.get("t", 0)
    if esito == "in corso" and time.time() - quando > 900:
        esito = "interrotto (in corso da più di 15 minuti)"
    ui.esito(Esito("aggiornamento automatico (auto)", esito == "ok",
                   f"{esito} → righe di auto.log sotto; si rifà a mano con `{NOME_CLI} auto --subito`; «mai partito» = "
                   "manca il plugin regole o il suo hook (Windows: serve python o python3 nel PATH)",
                   nota=time.strftime("%d/%m %H:%M", time.localtime(quando)) if quando else ""))
    if esito != "ok" and os.path.isfile(LOG_AUTO):
        for r in open(LOG_AUTO, encoding="utf-8", errors="replace").read().strip().splitlines()[-8:]:
            ui.info("auto.log │ " + r[:150])
    noti = leggi_json(os.path.join(CASA, ".claude", "plugins", "known_marketplaces.json"), {})
    for repo, d in cartelle_progetti():
        c = config_progetto(d)
        ui.titolo(repo)
        v, rif = versioni(d, c), riferimento(d, c, cli)
        p, r = v.get("progetto", ""), rif.get("progetto", "")
        if p.endswith("*"):
            n = len(run("git", "-C", d, "status", "--short", "-uno")[1].strip().splitlines())
            avanti = run("git", "-C", d, "rev-list", "--count", "@{u}..HEAD")[1].strip()
            ui.esito(Esito("progetto: modifiche non pubblicate", False,
                           f"{n} file modificati, {avanti or '?'} commit non pushati: commit + push (prima "
                           "`git pull --rebase`); push rifiutato da check.sh → leggi il suo messaggio, non saltarlo"))
        elif p not in ("studio", r) and r != "?":
            ui.esito(Esito("progetto: dietro", False, f"`git -C {d} pull --ff-only` (o `{NOME_CLI} aggiorna`)",
                           nota=f"{p} → {r}"))
        else:
            ui.esito(Esito("progetto", True, nota=p))
        for mk in marketplace_del_progetto(c):
            loc = noti.get(mk, {}).get("installLocation", "")
            testa = run("git", "-C", loc, "rev-parse", "--short=7", "HEAD")[1].strip() if loc else ""
            mio_mk, ult = v.get(mk, "manca"), rif.get(mk, "?")
            if mio_mk == "manca":
                cosa = f"plugin di {mk} non installati: `{NOME_CLI} aggiorna` (o /plugin install …@{mk})"
            elif testa and testa != ult:
                cosa = f"catalogo fermo a {testa}: `claude plugin marketplace update {mk}`, poi `{NOME_CLI} aggiorna`"
            else:
                cosa = f"catalogo aggiornato, plugin no: `{NOME_CLI} aggiorna` (fa `claude plugin update` di ognuno)"
            ui.esito(Esito(f"plugin {mk}", ult in (mio_mk, "?"), cosa + "; poi riavvia Claude",
                           nota=mio_mk + ("" if noti.get(mk, {}).get("autoUpdate") else " · autoUpdate spento")))
        t = modulo_talk(d, c)
        if t:
            ui.esito(Esito("stanza Talk", bool(stanza_collegata(t, c.get("stanza"))), f"`{NOME_CLI} entra {repo}`"))
    sq = stato().get("squadra", {})
    if sq.get("t"):
        ui.info(f"squadra al {time.strftime('%d/%m %H:%M', time.localtime(sq['t']))}: indietro "
                f"{', '.join(sq.get('indietro', [])) or 'nessuno'}; senza controllo {', '.join(sq.get('senza', [])) or 'nessuno'}")
    ui.info("Plugin aggiornati = validi dalla prossima sessione: chiudi e riapri Claude. Tutto ✓ ma la squadra ti vede "
            f"indietro → `{NOME_CLI} controlla --talk` (il resoconto nella stanza è vecchio).")
    ui.riepilogo(0)
    return 0 if all(e.ok or e.saltato for e in ui.esiti) else 1


def menu(ui):
    ui.pulisci()
    voci = [("Controlla che sia tutto a posto", controlla), ("Aggiorna pleyades-cli, plugin e progetti", aggiorna),
            ("Il mio kit: skill, cosa leggere, a chi chiedere", mio_kit),
            ("I miei progetti", progetti), ("Entra in un nuovo progetto", None), ("I link", link),
            ("Look Pleyades: terminale nero con l'intro, Claude dello stesso colore", voce_tema),
            ("Il tuo aspetto: nome, titolo, frase, colori e forme 3D", voce_aspetto),
            ("Rifai la guida da capo", lambda u: guida(u, []))]
    ui.intestazione("cosa c'è e cosa manca")
    if not lavoro():
        aperti = cantieri_aperti()
        if aperti and "nessun" not in aperti.lower():
            ui.titolo("Cantieri aperti (operazioni in corso)")
            for r in aperti.splitlines()[:6]:
                ui.info(r)
    codice = 0
    while True:  # si torna al menu dopo ogni cosa, finché non si sceglie «Esci»
        i = ui.scegli("Cosa vuoi fare?", [v[0] for v in voci] + ["Esci"])
        if i == len(voci):
            return codice
        if voci[i][1] is None:
            r = ui.chiedi("Nome del progetto (PROPRIETARIO/NOME, te lo dà chi ti ha invitato):")
            codice = guida(ui, [r], solo_progetti=True) if "/" in r else 1
        else:
            codice = voci[i][1](ui) or 0
        ui.esiti = []  # il riepilogo di ogni voce conta solo i suoi passi
        if not sys.stdin.isatty():
            return codice
        ui.chiedi(ui.c("2", "Invio per tornare al menu"))
        ui.pulisci()
        ui.intestazione("cosa c'è e cosa manca")


# --- Intro e profilo del Terminale (tema «Pleiad Fire Red») -------------------------------------------------------
# Le Pleiadi vere: (nome, ascensione retta in minuti, declinazione in gradi, magnitudine)
PLEIADI = [("Alcyone", 227.48, 24.100, 2.9), ("Atlas", 229.15, 24.050, 3.6), ("Electra", 224.87, 24.100, 3.7),
           ("Maia", 225.82, 24.367, 3.9), ("Merope", 226.32, 23.950, 4.2), ("Taygeta", 225.20, 24.467, 4.3),
           ("Celaeno", 224.80, 24.283, 5.4)]
# lettere 3×5: 15 cifre per riga, da sinistra a destra e dall'alto in basso
FONT_PIXEL = {"A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110",
              "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
              "I": "111010010010111", "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
              "M": "101111111101101", "N": "110101101101101", "O": "010101101101010", "P": "111101111100100",
              "Q": "010101101110011", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010",
              "U": "101101101101111", "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
              "Y": "101101010010010", "Z": "111001010100111", "0": "111101101101111", "1": "010110010010111",
              "2": "110001010100111", "3": "110001010001110", "4": "101101111001001", "5": "111100110001110",
              "6": "011100111101111", "7": "111001010010010", "8": "111101111101111", "9": "111101111001110",
              "-": "000000111000000", ".": "000000000000010", "!": "010010010000010", "&": "010101010101011",
              "'": "010010000000000", " ": "000000000000000"}
ACCENTI = str.maketrans("ÀÁÈÉÌÍÒÓÙÚ", "AAEEIIOOUU")
# colori dell'intro (base, chiaro, luce): il primo è il rosso del tema «Pleiad Fire Red», il secondo il blu dello studio
TINTE = {"rosso": ("#e8253f", "#ff8a96", "#fff4f0"), "blu": ("#4a6cf7", "#a9c4ff", "#f0f4ff"),
         "viola": ("#8a5cf0", "#c9b8ff", "#f6f0ff"), "verde": ("#1fae6a", "#8af0bf", "#effff6"),
         "oro": ("#e09a1a", "#ffd98a", "#fffaf0"), "ciano": ("#16a9c2", "#94eef8", "#f0feff")}
FORME_3D = ("stella", "sfera", "ciambella", "cubo", "cono", "ottaedro", "cuore", "cilindro", "merkaba")
ASPETTO_BASE = {"titolo": "PLEIADI STUDIO", "frase": "Sette stelle, una rotta", "nome": "", "tinta": "rosso",
                "colori": None, "forme": ["stella", "sfera"], "salvaschermo": 5}


def aspetto():
    """L'aspetto della persona (stato.json di questo computer): titolo in pixel, frase, nome, colori, forme 3D.
    Ogni campo mancante o sbagliato torna a quello dello studio."""
    a = {**ASPETTO_BASE, **(stato().get("aspetto") or {})}
    esa = re.compile(r"^#[0-9a-fA-F]{6}$")
    c = a.get("colori")
    if not (isinstance(c, list) and len(c) == 3 and all(isinstance(x, str) and esa.match(x) for x in c)):
        c = list(TINTE.get(a.get("tinta"), TINTE["rosso"]))
    a["colori"] = [tuple(int(x[i:i + 2], 16) for i in (1, 3, 5)) for x in c]
    forme = [x for x in (a.get("forme") or []) if x in FORME_3D][:2]
    a["forme"] = (forme + ASPETTO_BASE["forme"])[:2] if len(forme) < 2 else forme
    a["titolo"] = "".join(ch for ch in str(a.get("titolo") or "").upper().translate(ACCENTI) if ch in FONT_PIXEL)[:24].strip()
    a["titolo"] = a["titolo"] or ASPETTO_BASE["titolo"]
    a["frase"], a["nome"] = str(a.get("frase") or "")[:80], str(a.get("nome") or "")[:30]
    a["salvaschermo"] = a["salvaschermo"] if a.get("salvaschermo") in (0, 2, 5, 10, 20) else ASPETTO_BASE["salvaschermo"]
    return a


def distanza_forma(nome, x, y, z):
    """Distanza (con segno) dalla superficie di una forma grande circa 1, y in alto: negativa dentro."""
    import math
    if nome == "sfera":
        return math.sqrt(x * x + y * y + z * z) - 0.8
    if nome == "ciambella":
        return math.hypot(math.hypot(x, z) - 0.56, y) - 0.26
    if nome == "cubo":
        dx, dy, dz = abs(x) - 0.5, abs(y) - 0.5, abs(z) - 0.5
        return math.sqrt(max(dx, 0) ** 2 + max(dy, 0) ** 2 + max(dz, 0) ** 2) + min(max(dx, dy, dz), 0) - 0.08
    if nome == "ottaedro":
        return (abs(x) + abs(y) + abs(z) - 0.95) * 0.577
    if nome == "cilindro":
        dx, dy = math.hypot(x, z) - 0.55, abs(y) - 0.5
        return min(max(dx, dy), 0) + math.hypot(max(dx, 0), max(dy, 0)) - 0.04
    if nome == "cono":  # punta in alto
        y -= 0.55
        qx, qy = 1.15 * 0.62, -1.15
        wx, wy = math.hypot(x, z), y
        k = max(0.0, min(1.0, (wx * qx + wy * qy) / (qx * qx + qy * qy)))
        ax, ay = wx - qx * k, wy - qy * k
        k2 = max(0.0, min(1.0, wx / qx))
        bx, by = wx - qx * k2, wy - qy
        s = max(-(wx * qy - wy * qx), -(wy - qy))
        return math.sqrt(min(ax * ax + ay * ay, bx * bx + by * by)) * (1 if s > 0 else -1)
    if nome == "merkaba":  # due tetraedri incrociati
        t1 = (max(abs(x + y) - z, abs(x - y) + z) - 0.62) / 3 ** 0.5
        t2 = (max(abs(x + y) + z, abs(x - y) - z) - 0.62) / 3 ** 0.5
        return min(t1, t2)
    def estrudi(d, h):
        wx, wy = d, abs(z) - h
        return min(max(wx, wy), 0) + math.hypot(max(wx, 0), max(wy, 0))
    if nome == "cuore":
        px, py = abs(x) * 1.05, (y + 0.55) * 1.05
        if px + py > 1:
            d = math.hypot(px - 0.25, py - 0.75) - 2 ** 0.5 / 4
        else:
            m = 0.5 * max(px + py, 0)
            d = math.sqrt(min(px * px + (py - 1) ** 2, (px - m) ** 2 + (py - m) ** 2)) * (1 if px > py else -1)
        return estrudi(d, 0.1) - 0.2
    # stella a cinque punte, spessa (stella di iq: le punte per riflessione)
    k1x, k1y, k2x = 0.809016994375, -0.587785252292, -0.809016994375
    px, py, rr, rf = abs(x), y, 0.95, 0.45
    d = max(k1x * px + k1y * py, 0); px, py = px - 2 * d * k1x, py - 2 * d * k1y
    d = max(k2x * px + k1y * py, 0); px, py = px - 2 * d * k2x, py - 2 * d * k1y
    px, py = abs(px), py - rr
    bax, bay = rf * -k1y, rf * k1x - 1
    h = max(0.0, min(rr, (px * bax + py * bay) / (bax * bax + bay * bay)))
    d = math.hypot(px - bax * h, py - bay * h) * (1 if py * bax - px * bay > 0 else -1)
    return estrudi(d, 0.16) - 0.06


NUVOLE = {}


def nuvola(nome, n):
    """La superficie di una forma come n punti con la normale: lo stesso punto i, in ogni forma, sta nella stessa
    direzione dal centro (spirale di Fibonacci), così una forma si deforma nell'altra spostando ogni punto."""
    import math
    if (nome, n) in NUVOLE:
        return NUVOLE[(nome, n)]
    f = lambda x, y, z: distanza_forma(nome, x, y, z)
    pts, oro = [], math.pi * (3 - 5 ** 0.5)
    for i in range(n):
        uy = 1 - 2 * (i + 0.5) / n
        ur = math.sqrt(max(0.0, 1 - uy * uy))
        ux, uz = math.cos(i * oro) * ur, math.sin(i * oro) * ur
        if nome == "ciambella":  # ha il buco: la direzione dà i due angoli dell'anello
            th, ph = math.atan2(uz, ux), math.asin(max(-1.0, min(1.0, uy))) * 2
            rr = 0.56 + 0.26 * math.cos(ph)
            pts.append((rr * math.cos(th), 0.26 * math.sin(ph), rr * math.sin(th),
                        math.cos(ph) * math.cos(th), math.sin(ph), math.cos(ph) * math.sin(th)))
            continue
        lo, hi = 0.0, 1.8  # dal centro (dentro) verso fuori: dove la distanza cambia segno
        for _ in range(22):
            mid = (lo + hi) / 2
            if f(ux * mid, uy * mid, uz * mid) < 0:
                lo = mid
            else:
                hi = mid
        x, y, z = ux * lo, uy * lo, uz * lo
        e = 0.003
        gx = f(x + e, y, z) - f(x - e, y, z)
        gy = f(x, y + e, z) - f(x, y - e, z)
        gz = f(x, y, z + e) - f(x, y, z - e)
        m = math.sqrt(gx * gx + gy * gy + gz * gz) or 1
        pts.append((x, y, z, gx / m, gy / m, gz / m))
    NUVOLE[(nome, n)] = pts
    return pts


def intro(durata=3.2, resta=False, domanda=True, sfuma=False, salvaschermo=False):
    """`pleyades-cli intro`: a tutto schermo, su nero pieno in ogni cella (uguale in ogni terminale, anche col fondo
    chiaro): sale dal nero, volo fra le stelle, le 7 Pleiadi, due forme 3D che ruotano, il titolo, la frase, il nome
    e lo stato, con l'aspetto della persona (`aspetto()`). Pixel = mezza cella (▀/▄); un tasto salta alla fine.
    `resta`: le forme continuano a girare finché non premi un tasto. La prima volta (`domanda`) poi chiede l'aspetto
    e da dove partire. Transizioni sempre graduali: un tasto accelera fino alla fine (non salta), `sfuma` (quando dopo
    viene altro a schermo) dissolve tutto nel nero prima di lasciare lo schermo. `salvaschermo`: sullo schermo di
    riserva del terminale, la scena finale entra in dissolvenza e fluttua finché premi un tasto, poi sfuma e torna lo
    schermo di prima com'era. Fuori da un terminale non fa niente."""
    import math, random
    asp = aspetto()
    if salvaschermo:
        resta, sfuma, domanda = True, True, False
    sfuma = sfuma or (domanda and not stato().get("intro_vista"))  # dopo vengono le domande: niente schermo che salta
    ROSSO, ROSA, BIANCO = asp["colori"]
    FRASE_INTRO = asp["frase"]
    if not sys.stdout.isatty():
        return 0
    cols, righe_t = shutil.get_terminal_size((80, 24))
    C, A = cols, righe_t - 4  # celle; sotto: frase, stato, comandi, poi il prompt
    if C < 40 or A < 10:
        print(FRASE_INTRO)
        return 0
    # la scena si disegna in pixel quadrati: Q=2 → 2×4 per cella, poi 2×2 per cella (blocchi a quadranti, ▘▝▖▗);
    # PLEYADES_PIXEL=2 → 1×2 per cella (▀/▄), più leggero per i computer lenti
    Q = 1 if os.environ.get("PLEYADES_PIXEL") == "2" else 2
    W, PH = C * Q, A * 2 * Q
    if WIN:
        os.system("")  # sequenze ANSI nella console di Windows
    tp = os.environ.get("TERM_PROGRAM", "")
    vero = (os.environ.get("COLORTERM", "") in ("truecolor", "24bit") or bool(os.environ.get("WT_SESSION"))
            or tp in ("iTerm.app", "WezTerm", "ghostty", "vscode")
            or (tp == "Apple_Terminal" and int((platform.mac_ver()[0] or "0").split(".")[0]) >= 26))

    forza = os.environ.get("PLEYADES_COLORI", "")
    vero = forza != "256" and (forza == "24" or vero)
    LIV = (0, 95, 135, 175, 215, 255)  # i livelli veri del cubo a 256 colori (non a passi uguali)
    def livello(v, soglia):
        i = next(k for k in range(5) if v <= LIV[k + 1])  # fra LIV[i] e LIV[i+1]
        return i + ((v - LIV[i]) / (LIV[i + 1] - LIV[i]) > soglia)

    def col(c, sfondo, x=0, y=0):
        r, g, b = (min(255, max(0, int(v))) for v in c)
        if vero:
            return f"\033[{48 if sfondo else 38};2;{r};{g};{b}m"
        ir, ig, ib = livello(r, 0.5), livello(g, 0.5), livello(b, 0.5)  # il più vicino (un retino fa scacchiera)
        cubo = 16 + 36 * ir + 6 * ig + ib
        grigio = (r + g + b) / 3
        gi = min(23, max(0, round((grigio - 8) / 10)))
        if max(r, g, b) - min(r, g, b) < 14 and abs(8 + 10 * gi - grigio) < abs(LIV[ir] - r) + 6:
            cubo = 232 + gi if grigio > 4 else 16  # quasi grigio: la rampa dei grigi è più fine del cubo
        return f"\033[{48 if sfondo else 38};5;{cubo}m"

    rnd = random.Random(7)
    cx, cy = W / 2, PH * 0.4
    s = min(W * 0.46, PH * 0.42 / 0.52)  # pixel per grado: l'ammasso occupa metà larghezza o poco più di un terzo d'altezza
    g = s / 34  # 1 = la misura per cui sono pensate stelle e solidi
    stelle = [(-(ra - 227.48) * 0.25 * 0.9135 * s, -(de - 24.1) * s, m) for _, ra, de, m in PLEIADI]
    mx = (max(x for x, _, _ in stelle) + min(x for x, _, _ in stelle)) / 2
    my = (max(y for _, y, _ in stelle) + min(y for _, y, _ in stelle)) / 2
    stelle = [(cx + x - mx, cy + y - my, m) for x, y, m in stelle]
    volo = [[rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.1, 1)] for _ in range(int(60 + W * PH / 40))]
    fondo = [(rnd.uniform(0, W), rnd.uniform(0, PH), rnd.uniform(0.15, 0.6), rnd.uniform(0, 6.3))
             for _ in range(int(W * PH / 55))]
    # nebulosa calcolata una volta: ogni fotogramma la scala soltanto
    toni = [tuple(v * k + d for v, d in zip(ROSSO, sp)) for k, sp in ((0.3, (0, 0, 4)), (0.24, (0, 0, 32)), (0.38, (0, 0, 0)))]
    nubi = [(sx + rnd.uniform(-5, 5) * g, sy + rnd.uniform(-3, 3) * g, rnd.uniform(7, 13) * g, rnd.uniform(4, 7) * g,
             rnd.choice(toni)) for sx, sy, _ in stelle for _ in range(2)]
    nebbia = [[[0.0, 0.0, 0.0] for _ in range(W)] for _ in range(PH)]
    for bx, by, rx, ry, c in nubi:
        for y in range(max(0, int(by - 2.5 * ry)), min(PH, int(by + 2.5 * ry) + 1)):
            for x in range(max(0, int(bx - 2.5 * rx)), min(W, int(bx + 2.5 * rx) + 1)):
                d = ((x - bx) / rx) ** 2 + ((y - by) / ry) ** 2
                if d < 6:
                    a = 0.42 * math.exp(-d) * rnd.uniform(0.55, 1.0)
                    p = nebbia[y][x]
                    p[0] += c[0] * a; p[1] += c[1] * a; p[2] += c[2] * a
    r3 = 7 * g
    lato = 0.5 * s + 2.2 * r3
    posa = lambda f, k: (0.0, 0.0) if f in ("stella", "cuore") else (0.6 * k, 0.45)  # stella e cuore finiscono di fronte
    npunti = int(max(1500, min(9000, 4 * math.pi * r3 * r3 / 1.4)))  # abbastanza punti da coprire la superficie
    solidi = [(asp["forme"][0], asp["forme"][1], max(r3 + 1, cx - lato), cy - 0.12 * s, r3, 1, *posa(asp["forme"][0], -1)),
              (asp["forme"][1], asp["forme"][0], min(W - r3 * 1.15 - 2, cx + lato), cy + 0.18 * s, r3, -1, *posa(asp["forme"][1], 1))]
    for f_ in asp["forme"]:
        nuvola(f_, npunti)
    # il retino: 5 toni della tinta (nero, scuro, base, chiaro, luce), scelti per luminosità con la matrice di Bayer
    TONI = [(0, 0, 0), tuple(v * 0.42 for v in ROSSO), ROSSO, ROSA, BIANCO]
    YT = [0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2] for c in TONI]
    BAYER4 = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]

    def retino(c, bx, by):
        y_ = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
        if y_ <= 1:
            return TONI[0]
        for i in range(4):
            if y_ < YT[i + 1] or i == 3:
                fr = min(1.0, (y_ - YT[i]) / ((YT[i + 1] - YT[i]) or 1))
                # i toni più scuri (la nebulosa) a punti sparsi: il retino regolare lì fa righe
                soglia = ((bx * 92837111) ^ (by * 689287499)) % 16 if i == 0 else BAYER4[(by & 3) * 4 + (bx & 3)]
                return TONI[i + 1] if fr * 16 > soglia + 0.5 else TONI[i]

    def tono_luce(l):
        """Una luminosità 0..1 come colore della tavolozza (poi il retino la rende a punti)."""
        y_ = max(0.0, min(1.0, l)) * YT[4]
        for i in range(4):
            if y_ <= YT[i + 1]:
                fr = (y_ - YT[i]) / ((YT[i + 1] - YT[i]) or 1)
                return tuple(TONI[i][q] + (TONI[i + 1][q] - TONI[i][q]) * fr for q in range(3))
        return BIANCO
    LX, LY, LZ = -0.5 / 0.987, 0.62 / 0.987, -0.6 / 0.987  # luce in alto a sinistra, davanti
    HX, HY, HZ = LX, LY, LZ - 1
    hm = math.sqrt(HX * HX + HY * HY + HZ * HZ)
    HX, HY, HZ = HX / hm, HY / hm, HZ / hm

    def deforma(giro):
        """0 → 1 → 0: ogni ~12 s le due forme si scambiano, deformandosi (solo quando la scena resta)."""
        k = giro % 12.4
        if k < 5:
            return 0.0
        if k < 6.4:
            return 0.5 - 0.5 * math.cos(math.pi * (k - 5) / 1.4)
        if k < 11:
            return 1.0
        return 0.5 + 0.5 * math.cos(math.pi * (k - 11) / 1.4)
    nome = asp["titolo"]
    if len(nome) * 4 - 1 > W * 0.9:  # non ci sta neanche a pixel di una cella: la prima parola
        nome = nome.split()[0][:max(1, int(W * 0.9 + 1) // 4)]
    f = max(1, min(int(W * 0.8 / (len(nome) * 4 - 1)), int(PH * 0.16 / 5)))  # grandezza del pixel del nome
    if Q == 2:
        f = max(2, f - f % 2)  # pari: ogni pixel del nome copre righe intere di quadranti (niente righe a metà)
    tx0 = int(cx - (len(nome) * 4 - 1) * f / 2)
    ty0 = int(PH * 0.8) - 5 * f // 2
    ty0 += (ty0 % 2 == 0) if f == 1 else (ty0 % 2)  # f=1: riga dispari (▀/▄ del Mac); f pari: celle intere

    def disegna(buf, x, y, c, a):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < PH and a > 0:
            p = buf[y][x]
            p[0] += c[0] * a; p[1] += c[1] * a; p[2] += c[2] * a

    volo_t = [0.0]

    def fotogramma(t, giro=0.0):
        neb = max(0.0, min(1.0, (t - 0.35) / 0.4)) if vero else 0.0  # a 256 colori il rosso scuro più tenue è già acceso
        buf = [[[p[0] * neb, p[1] * neb, p[2] * neb] for p in riga] for riga in nebbia]
        passo = max(0.0, t - volo_t[0]) * passi  # quanti fotogrammi «giusti» da quello prima (computer lenti: più di 1)
        volo_t[0] = t
        v = max(0.0, 1 - t / 0.5) ** 2 * passo  # volo fra le stelle: veloce all'inizio, si ferma a metà
        for st in volo:
            z0 = st[2]
            st[2] -= v * 0.13
            if st[2] < 0.06:
                st[0], st[1], st[2] = rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1.0
                continue
            a = min(1.0, (1 - st[2]) * 1.7 + 0.15) * max(0.0, 1 - t / 0.55) * min(1.0, t / 0.1)  # sale dal nero
            k = W * 0.24
            x1, y1, x0, y0 = cx + st[0] / st[2] * k, cy + st[1] / st[2] * k * 0.5, cx + st[0] / z0 * k, cy + st[1] / z0 * k * 0.5
            n = max(1, int(abs(x1 - x0) + abs(y1 - y0)))
            for q in range(n + 1):
                fr = q / n
                disegna(buf, x0 + (x1 - x0) * fr, y0 + (y1 - y0) * fr, BIANCO if fr > 0.8 else ROSA, a * (0.25 + 0.75 * fr))
        fa = max(0.0, min(1.0, (t - 0.3) / 0.3))
        for x, y, b, ph in fondo:
            for dx in range(Q):  # a quadranti un pixel solo è alto il doppio che largo: il punto è largo 2
                disegna(buf, x + dx, y, BIANCO, fa * b * (0.6 + 0.4 * math.sin((t + giro / 3) * 9 + ph)))
        sa = max(0.0, min(1.0, (t - 0.25) / 0.25))
        mf = deforma(giro) if giro else 0.0
        mf = mf * mf * (3 - 2 * mf)
        for nome_a, nome_b, ox, oy, r, verso, fy, fx in solidi if sa else []:
            ay, ax = verso * (t * 2 * math.pi + giro * 0.9) + fy, (1 - t) * 3.5 + fx + 0.25 * math.sin(giro * 0.5)
            cy_, sy_, cx_, sx_ = math.cos(ay), math.sin(ay), math.cos(ax), math.sin(ax)
            oy2 = oy + math.sin(giro * 0.7 + ox) * r * 0.08  # fluttua piano
            ra = r * (1 - 0.2 * math.sin(math.pi * mf))  # respira mentre cambia forma
            pa, pb = NUVOLE[(nome_a, npunti)], NUVOLE[(nome_b, npunti)]
            zb = {}
            for i in range(npunti):
                x, y, z, nx, ny, nz = pa[i]
                if mf:
                    b_ = pb[i]
                    x, y, z = x + (b_[0] - x) * mf, y + (b_[1] - y) * mf, z + (b_[2] - z) * mf
                    nx, ny, nz = nx + (b_[3] - nx) * mf, ny + (b_[4] - ny) * mf, nz + (b_[5] - nz) * mf
                    m_ = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
                    nx, ny, nz = nx / m_, ny / m_, nz / m_
                x, z = x * cy_ + z * sy_, -x * sy_ + z * cy_
                y, z = y * cx_ - z * sx_, y * sx_ + z * cx_
                nx, nz = nx * cy_ + nz * sy_, -nx * sy_ + nz * cy_
                ny, nz = ny * cx_ - nz * sx_, ny * sx_ + nz * cx_
                if nz > 0.2:  # guarda indietro: non si vede
                    continue
                ix, iy = int(ox + x * ra), int(oy2 - y * ra)
                dif = max(0.0, nx * LX + ny * LY + nz * LZ)
                spe = max(0.0, nx * HX + ny * HY + nz * HZ) ** 26
                lum = 0.07 + 0.58 * dif + 0.62 * spe + 0.1 * (1 - abs(nz)) ** 3
                for px_, py_ in ((ix, iy), (ix + 1, iy), (ix, iy + 1), (ix + 1, iy + 1)):
                    v = zb.get((px_, py_))
                    if v is None or z < v[0]:
                        zb[(px_, py_)] = (z, lum)
            for (px_, py_), (_, lum) in zb.items():
                if 0 <= px_ < W and 0 <= py_ < PH:
                    c = tono_luce(lum)
                    q = buf[py_][px_]
                    q[0] += (c[0] - q[0]) * sa; q[1] += (c[1] - q[1]) * sa; q[2] += (c[2] - q[2]) * sa
        for i, (x, y, m) in enumerate(sorted(stelle, key=lambda st: st[2])):  # le sette, dalla più luminosa
            a = max(0.0, min(1.0, (t - 0.42 - i * 0.045) / 0.12))
            if not a:
                continue
            r = (6.2 - m) * g
            e = int(4 * g) + 1
            for dy in range(-e, e + 1):
                for dx in range(-e, e + 1):
                    disegna(buf, x + dx, y + dy, ROSSO, a * 0.5 * math.exp(-(dx * dx + dy * dy) / (r * 0.9 * g)))
            for k in range(1, int(r) + 2):
                for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                    disegna(buf, x + dx, y + dy, ROSA, a * 0.9 / (k / g))
            disegna(buf, x, y, BIANCO, a * 1.2)
        na = max(0.0, min(1.0, (t - 0.72) / 0.15))  # il nome, con un riflesso che passa
        lampo = tx0 + (t - 0.8) / 0.2 * (len(nome) * 4 + 8) * f
        for j, ch in enumerate(nome):
            for k, b in enumerate(FONT_PIXEL.get(ch, FONT_PIXEL[" "])):
                if b == "1":
                    for qy in range(f):
                        for qx in range(f):
                            x, y = tx0 + (j * 4 + k % 3) * f + qx, ty0 + (k // 3) * f + qy
                            c = ROSSO  # tinta piena: a retino le lettere verrebbero rigate
                            luce = max(0.0, 1 - abs(x - lampo) / (4 * f))
                            disegna(buf, x, y, tuple(c[q] + (BIANCO[q] - c[q]) * luce for q in range(3)), na)
        return buf

    nero = col((0, 0, 0), True)

    prima = {}  # cella → cosa c'era: si riscrivono solo le celle cambiate (meno byte, meglio sui computer lenti)

    QUADRANTI = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"  # indice = pixel accesi: 1 alto-sx, 2 alto-dx, 4 basso-sx, 8 basso-dx

    memo = {}

    def cella_quadranti(px):
        """4 pixel (alto-sx, alto-dx, basso-sx, basso-dx) → (colore davanti, colore dietro, carattere): i due gruppi
        di pixel che sbagliano meno; un carattere ha solo due colori. Le celle già viste (la nebulosa ferma, il
        nero) vengono dalla memoria: è il calcolo più caro di ogni fotogramma."""
        chiave = tuple(int(v) >> 2 for p in px for v in p)
        if chiave in memo:
            return memo[chiave]
        if max(sum(p) for p in px) <= 9:
            memo[chiave] = None, None, " "
            return memo[chiave]
        if max(px[i][q] for i in range(4) for q in range(3)) - min(px[i][q] for i in range(4) for q in range(3)) < 6:
            memo[chiave] = None, px[0], " "
            return memo[chiave]
        meglio = None
        for m in range(1, 8):  # il pixel basso-dx sempre nel gruppo «dietro»: ogni divisione una volta sola
            a = [px[i] for i in range(4) if m >> i & 1]
            b = [px[i] for i in range(4) if not m >> i & 1]
            ma = [sum(p[q] for p in a) / len(a) for q in range(3)]
            mb = [sum(p[q] for p in b) / len(b) for q in range(3)]
            err = sum((p[q] - ma[q]) ** 2 for p in a for q in range(3)) + sum((p[q] - mb[q]) ** 2 for p in b for q in range(3))
            if meglio is None or err < meglio[0]:
                meglio = (err, m, ma, mb)
        _, m, ma, mb = meglio
        memo[chiave] = (None, ma, " ") if max(abs(ma[q] - mb[q]) for q in range(3)) < 6 else (ma, mb, QUADRANTI[m])
        if len(memo) > 200000:
            memo.clear()
        return memo[chiave]

    def schermo(buf, t, luce=1.0):
        out = []
        for r in range(A):
            s_, ultimo, salto = [], None, True
            for x in range(C):
                if Q == 2:  # 2×4 pixel quadrati → 2×2 (le coppie di righe in media)
                    y = 4 * r
                    px = [retino([(buf[y + dy][2 * x + dx][q] + buf[y + dy + 1][2 * x + dx][q]) / 2 for q in range(3)],
                                 2 * x + dx, 2 * r + dy // 2)
                          for dy, dx in ((0, 0), (0, 1), (2, 0), (2, 1))]
                    dav, die, ch = cella_quadranti(px)
                    if ch == " ":
                        cod = (col(die, True) if die and sum(die) > 9 else nero, " ")
                    else:
                        cod = (col(dav, False) + (col(die, True) if sum(die) > 9 else nero), ch)
                else:
                    a, b = retino(buf[2 * r][x], x, 2 * r), retino(buf[2 * r + 1][x], x, 2 * r + 1)
                    sa, sb = sum(a) > 9, sum(b) > 9
                    if sa and sb and max(abs(a[q] - b[q]) for q in range(3)) < 6:
                        cod = (col(a, True, x, 2 * r), " ")  # cella intera dallo sfondo: nessun bordo del glifo
                    elif sa and sb:
                        cod = (col(a, False, x, 2 * r) + col(b, True, x, 2 * r + 1), "▀")
                    elif sa:
                        cod = (col(a, False, x, 2 * r) + nero, "▀")
                    elif sb:
                        cod = (col(b, False, x, 2 * r + 1) + nero, "▄")
                    else:
                        cod = (nero, " ")
                if prima.get((r, x)) == cod:
                    salto = True
                    continue
                prima[(r, x)] = cod
                if salto:
                    s_.append(f"\033[{r + 1};{x + 1}H")
                    salto, ultimo = False, None
                s_.append(("" if cod[0] == ultimo else cod[0]) + cod[1])
                ultimo = cod[0]
            out.append("".join(s_))
        n = int(max(0.0, min(1.0, (t - 0.85) / 0.15)) * len(FRASE_INTRO) + 0.999) if t > 0.85 else 0
        sotto = "  ·  ".join(x for x in ((f"ciao, {asp['nome']}" if asp["nome"] else ""), stato_in_parole()) if x)
        testi = [(FRASE_INTRO[:n], ROSA, "\033[3m"), (sotto if t >= 1 else "", (150, 150, 160), ""),
                 ("claude  parla con Claude  ·  pley  menu Pleiadi Studio" if t >= 1 else "", (110, 110, 120), "")]
        for i, (testo, c, stile) in enumerate(testi):
            testo, c = testo[:C], tuple(v * luce for v in c)
            pieno = len(FRASE_INTRO) if i == 0 else len(testo)
            out.append(f"\033[{A + 1 + i};1H" + nero + " " * C + f"\033[{A + 1 + i};{max(1, (C - pieno) // 2 + 1)}H"
                       + nero + col(c, False) + stile + testo + "\033[0m")
        return "".join(out)

    passi = int(durata * 20)
    tasto, vecchio = (lambda: False), None
    if WIN:
        import msvcrt
        tasto = msvcrt.kbhit
    else:
        import select, termios, tty
        try:
            vecchio = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            tasto = lambda: bool(select.select([sys.stdin], [], [], 0)[0])
        except Exception:
            vecchio = None
    sys.stdout.write(("\033[?1049h" if salvaschermo else "") + "\033[?25l" + nero + "\033[2J")
    try:
        t0, svelto = time.time(), None
        while not salvaschermo:  # t dal tempo vero: su un computer lento meno fotogrammi, stessa durata
            inizio = time.time()
            if svelto is None and tasto():
                svelto = (min(1.0, (inizio - t0) / durata), inizio)  # un tasto: fino alla fine in 0,35 s, senza salto
            t = (min(1.0, (inizio - t0) / durata) if svelto is None else
                 min(1.0, svelto[0] + (1 - svelto[0]) * (inizio - svelto[1]) / 0.35))
            sys.stdout.write(schermo(fotogramma(t), t))
            sys.stdout.flush()
            if t >= 1.0:
                break
            time.sleep(max(0.0, durata / passi - (time.time() - inizio)))
        prima_t = time.time()
        while resta and not tasto():  # le forme continuano a girare, piano (il salvaschermo entra in dissolvenza)
            giro = time.time() - prima_t
            luce = min(1.0, giro / 0.8) ** 2 if salvaschermo else 1.0
            buf = fotogramma(1.0, giro)
            if luce < 1:
                buf = [[[v * luce for v in p] for p in riga] for riga in buf]
            sys.stdout.write(schermo(buf, 1.0, luce))
            sys.stdout.flush()
            time.sleep(0.06)
        if sfuma:  # dissolve nel nero (0,4 s), poi lo schermo pulito per quello che viene dopo
            giro, inizio = time.time() - prima_t, time.time()
            while (k := (time.time() - inizio) / 0.4) < 1:
                luce = (1 - k) ** 2
                buf = [[[v * luce for v in p] for p in riga] for riga in fotogramma(1.0, giro + k * 0.4)]
                sys.stdout.write(schermo(buf, 1.0, luce))
                sys.stdout.flush()
                time.sleep(0.03)
            sys.stdout.write(nero + "\033[2J\033[H")
    finally:
        sys.stdout.write("\033[0m\033[?25h\033[?1049l" if salvaschermo else f"\033[0m\033[{A + 4};1H\033[?25h")
        sys.stdout.flush()
        if vecchio is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, vecchio)
            while select.select([sys.stdin], [], [], 0)[0]:
                os.read(sys.stdin.fileno(), 64)  # il tasto che ha saltato non finisce nel prompt
    if domanda and not stato().get("intro_vista"):  # primo avvio: l'aspetto, poi tre strade; poi mai più
        salva_stato(intro_vista=time.strftime("%Y-%m-%d"))
        ui = interfaccia()
        if not stato().get("aspetto"):
            voce_aspetto(ui, primo=True)
        i = ui.scegli("Da dove parti?", ["Parla con Claude", "Menu Pleyades: progetti, aggiornamenti, aiuto",
                                         "Niente, uso il terminale"])
        if i == 0 and shutil.which("claude"):
            os.execvp("claude", ["claude"])
        if i == 1:
            return menu(ui)
    return 0


def voce_aspetto(ui, primo=False):
    """`pleyades-cli aspetto` (e la prima intro): nome, titolo, frase, colori e forme 3D, anteprima, poi lo stesso
    aspetto ovunque: Claude, terminale, prompt. Invio su ogni domanda = la scelta dello studio."""
    import getpass
    prima = stato().get("aspetto")
    a = {**ASPETTO_BASE, **(prima or {})}
    ui.pulisci()
    ui.titolo("Benvenuto: scegli il tuo aspetto" if primo else "Il tuo aspetto")
    ui.info("Vale per l'intro, per Claude e per il terminale. Invio = la scelta dello studio; si cambia quando vuoi "
            f"con `{NOME_CLI} aspetto`.")
    a["nome"] = ui.chiedi("Come ti chiamo nell'intro? (spazio = niente)", a.get("nome") or getpass.getuser()).strip()
    a["titolo"] = ui.chiedi("Titolo in pixel (lettere, numeri, - . ! &)", a.get("titolo") or ASPETTO_BASE["titolo"])
    a["frase"] = ui.chiedi("Frase sotto il titolo", a.get("frase") or ASPETTO_BASE["frase"])
    tinte = list(TINTE)
    attuale = a.get("tinta") if a.get("tinta") in tinte else "rosso"
    ordine = [attuale] + [x for x in tinte if x != attuale]  # la prima = la consigliata: quella che hai
    i = ui.scegli("Colori", [x.capitalize() for x in ordine] + ["I miei: tre colori #rrggbb"])
    if i < len(ordine):
        a["tinta"], a["colori"] = ordine[i], None
    else:
        a["colori"] = [ui.chiedi(f"Colore {q} (#rrggbb)", c) for q, c in zip(("base", "chiaro", "luce"), TINTE[attuale])]
    forme = list(FORME_3D)
    a["forme"] = list(a.get("forme") or ASPETTO_BASE["forme"])[:2]
    for k, q in enumerate(("a sinistra", "a destra")):
        ora = a["forme"][k] if len(a["forme"]) > k and a["forme"][k] in forme else ASPETTO_BASE["forme"][k]
        scelte = [ora] + [x for x in forme if x != ora]
        a["forme"][k:k + 1] = [scelte[ui.scegli(f"Forma 3D {q}", [x.capitalize() for x in scelte])]]
    durate = [5, 2, 10, 20, 0]
    ora_ss = a.get("salvaschermo", 5) if a.get("salvaschermo") in durate else 5
    durate = [ora_ss] + [x for x in durate if x != ora_ss]
    a["salvaschermo"] = durate[ui.scegli("Salvaschermo: dopo quanto senza scrivere nel terminale?",
                                         [f"{x} minuti" if x else "Mai" for x in durate])]
    salva_stato(aspetto=a)  # aspetto() legge da qui: l'anteprima è l'intro vera
    while True:
        intro(domanda=False, sfuma=True)
        i = ui.scegli("Ti piace?", ["Sì, mettilo ovunque (Claude, terminale, prompt)", "Rivedi l'anteprima",
                                    "No, torna a prima"])
        if i != 1:
            break
    if i == 2:
        salva_stato(aspetto=prima)
        ui.info("Rimesso com'era.")
        return 0
    ok, cosa = tema(forza=True, terminale_mac=primo)
    if WIN and (stato().get("finestre_prima") or ui.scegli(
            "Anche i colori di tutto Windows? (modo scuro, la tua tinta su barre del titolo e bordi)",
            ["Sì", "No, solo il terminale"]) == 0):
        ok2, cosa2 = tema_finestre()
        ok, cosa = ok and ok2, f"{cosa}; {cosa2}"
    ui.esito(Esito("aspetto messo ovunque", ok, cosa, nota="Claude: dalla prossima sessione (o /theme)"))
    return 0 if ok else 1


def stato_in_parole():
    """Una riga per chi non programma: questo computer e la squadra, dall'ultimo giro automatico (niente rete)."""
    st = stato()
    a, sq = st.get("auto") or {}, st.get("squadra") or {}
    if not a.get("t") or time.time() - a["t"] > 86400:
        return ""
    io = "✓ computer aggiornato" if a.get("esito") == "ok" else f"✗ da sistemare: {NOME_CLI} diagnosi"
    indietro = [x.split(" (")[0] for x in sq.get("indietro", [])]
    gruppo = ("✓ squadra allineata" if not indietro else
              "squadra: " + ", ".join(indietro) + " in aggiornamento") if sq.get("t") else ""
    return "  ·  ".join(x for x in (io, gruppo) if x)


def colore_ns(esa):
    """Un colore come lo salva il Terminale del Mac (NSColor archiviato)."""
    r, g, b = (int(esa[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return plistlib.dumps({"$version": 100000, "$archiver": "NSKeyedArchiver", "$top": {"root": plistlib.UID(1)},
                           "$objects": ["$null", {"NSRGB": f"{r:.4f} {g:.4f} {b:.4f}\0".encode(), "NSColorSpace": 2,
                                                  "$class": plistlib.UID(2)},
                                        {"$classname": "NSColor", "$classes": ["NSColor", "NSObject"]}]},
                          fmt=plistlib.FMT_BINARY)


TEMA_CLAUDE = "custom:tema-studio:pleyades-studio-rosso"  # l'id viene dal nome del file: «Pleiad Fire Red»
TEMI_CLAUDE = {"rosso": "pleyades-studio-rosso", "blu": "pleyades-studio", "viola": "pleiadi-viola",
               "verde": "pleiadi-verde", "oro": "pleiadi-oro", "ciano": "pleiadi-ciano"}  # tinta → themes/ di tema-studio
PAROLE_ROTELLA = ["Allineo le stelle", "Consulto le Pleiadi", "Accendo la nebulosa", "Traccio la rotta",
                  "Lucido le costellazioni"]
COLORI_ANSI = ["#000000", "#e8253f", "#5fd4a0", "#f5c26b", "#6c8cff", "#ff6b7d", "#7fd6e0", "#d8d8d8",
               "#555555", "#ff4d5e", "#7fe8b8", "#ffd98a", "#93abff", "#ff9aa5", "#a6eef5", "#ffffff"]


def tinta_claude(asp):
    """Il tema di Claude per l'aspetto: quello della tinta; con colori propri, la tinta di tonalità più vicina."""
    import colorsys
    if not (stato().get("aspetto") or {}).get("colori"):
        return TEMI_CLAUDE.get(asp.get("tinta"), TEMI_CLAUDE["rosso"])
    ton = lambda c: colorsys.rgb_to_hsv(*(v / 255 for v in c))[0]
    h = ton(asp["colori"][0])
    vicina = min(TINTE, key=lambda k: min(abs(h - ton(int(TINTE[k][0][i:i + 2], 16) for i in (1, 3, 5))) % 1,
                                          1 - abs(h - ton(int(TINTE[k][0][i:i + 2], 16) for i in (1, 3, 5))) % 1))
    return TEMI_CLAUDE[vicina]


def colori_terminale(asp=None):
    """Colori del terminale per l'aspetto: nero pieno, i rossi della tavolozza (ANSI 1, 5, 9, 13) con la tinta
    scelta, cursore e selezione dello stesso colore; gli altri ANSI restano (verde, giallo, blu si devono distinguere)."""
    asp = asp or aspetto()
    base, chiaro, _ = asp["colori"]
    esa = lambda c, k=1.0: "#%02x%02x%02x" % tuple(max(0, min(255, round(v * k))) for v in c)
    mix = lambda a, b, k: tuple(a[i] + (b[i] - a[i]) * k for i in range(3))
    ansi = list(COLORI_ANSI)
    ansi[1], ansi[5], ansi[9], ansi[13] = esa(base), esa(mix(base, chiaro, 0.55)), esa(mix(base, chiaro, 0.25)), esa(chiaro)
    return {"ansi": ansi, "cursore": esa(base), "selezione": esa(base, 0.39)}


def tema_prompt(asp=None):
    """Il prompt colorato (Starship, uguale su Mac e Windows) con i colori dell'aspetto. Scrive
    ~/.config/starship.toml solo se non c'è o l'ha scritto pleyades-cli; senza Starship non fa niente."""
    if not shutil.which("starship"):
        return "prompt: Starship non installato (Mac: brew install starship; Windows: winget install Starship.Starship)"
    asp = asp or aspetto()
    f = os.path.join(CASA, ".config", "starship.toml")
    segno = "# scritto da pleyades-cli aspetto"
    if os.path.exists(f) and segno not in open(f, encoding="utf-8").read():
        return "prompt: ~/.config/starship.toml è tuo, non lo tocco"
    esa = lambda c, k=1.0: "#%02x%02x%02x" % tuple(max(0, min(255, round(v * k))) for v in c)
    base, chiaro, _ = asp["colori"]
    medio = tuple((base[i] + chiaro[i]) / 2 for i in range(3))
    os.makedirs(os.path.dirname(f), exist_ok=True)
    with open(f, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"""{segno} (si rifà a ogni cambio di aspetto: per tenerne uno tuo, togli questa riga)
palette = "pleiadi"
add_newline = true
scan_timeout = 100
format = \"\"\"
[◆](base)[ $username](medio)$directory$git_branch$git_status$python$nodejs$cmd_duration
$character\"\"\"

[palettes.pleiadi]
base = "{esa(base)}"
medio = "{esa(medio)}"
chiaro = "{esa(chiaro)}"
scuro = "{esa(base, 0.52)}"
cenere = "#8a8a8a"

[username]
show_always = true
format = "[$user]($style) "
style_user = "bold medio"
style_root = "bold base"

[directory]
format = "[in ](cenere)[$path]($style)[$read_only]($read_only_style) "
style = "bold chiaro"
truncation_length = 3
read_only = " ⊘"

[git_branch]
format = "[on ](cenere)[⎇ $branch]($style) "
style = "bold base"

[git_status]
format = "([\\[$all_status$ahead_behind\\]]($style) )"
style = "medio"

[python]
format = "[py $version]($style) "
style = "scuro"

[nodejs]
format = "[node $version]($style) "
style = "scuro"

[cmd_duration]
format = "[⧗ $duration]($style) "
style = "cenere"

[character]
success_symbol = "[❯](bold base)"
error_symbol = "[❯](bold #ff5f3a)"
""")
    if MAC or not WIN:
        rc = os.path.join(CASA, ".zshrc" if "zsh" in os.environ.get("SHELL", "zsh") else ".bashrc")
        riga = f'eval "$(starship init {"zsh" if rc.endswith("zshrc") else "bash"})"'
        if riga not in (open(rc, encoding="utf-8").read() if os.path.exists(rc) else ""):
            with open(rc, "a", encoding="utf-8") as fh:
                fh.write(f"\n# prompt Pleiadi Studio (colori: {NOME_CLI} aspetto)\n{riga}\n")
    return "prompt Starship con i tuoi colori"


def tema_salvaschermo(asp=None):
    """Il salvaschermo della shell: dopo N minuti senza scrivere al prompt parte `salvaschermo` (un tasto torna com'era).
    zsh: TMOUT + TRAPALRM in un blocco segnato di ~/.zshrc, tolto con 0 minuti. Windows: nel profilo di Terminale
    (`tema_windows`). Mai mentre gira un programma (Claude Code compreso): solo al prompt."""
    asp = asp or aspetto()
    rc = os.path.join(CASA, ".zshrc")
    if WIN or "zsh" not in os.environ.get("SHELL", "zsh"):
        return ""
    inizio, fine = "# >>> salvaschermo Pleiadi (pleyades-cli aspetto)", "# <<< salvaschermo Pleiadi"
    testo = open(rc, encoding="utf-8").read() if os.path.exists(rc) else ""
    testo = re.sub(rf"\n?{re.escape(inizio)}.*?{re.escape(fine)}\n?", "\n", testo, flags=re.S).rstrip("\n") + "\n"
    minuti = asp["salvaschermo"]
    if minuti:
        cli = os.path.join(BIN, NOME_CLI)
        testo += (f"\n{inizio}\nTMOUT={minuti * 60}\n"
                  f"TRAPALRM() {{ [[ -t 1 ]] && \"{cli}\" salvaschermo; zle && zle reset-prompt }}\n{fine}\n")
    with open(rc, "w", encoding="utf-8") as f:
        f.write(testo)
    return f"salvaschermo dopo {minuti} min" if minuti else "salvaschermo spento"


def tema(forza=False, terminale_mac=True):
    """`pleyades-cli tema`: tema di Claude con la tinta dell'aspetto e parole della rotella in Claude Code + il
    terminale nero con l'intro (Mac: profilo del Terminale e iTerm2; Windows: schema di Windows Terminal + intro) +
    il prompt Starship. `forza`: il tema di Claude cambia anche se ne avevi già uno dello studio (scelta dell'aspetto).
    `terminale_mac=False`: non reimporta il profilo del Terminale (aprirlo apre una finestra)."""
    asp = aspetto()
    p = os.path.join(CASA, ".claude", "settings.json")
    s = leggi_json(p, {})
    prima = json.dumps(s, sort_keys=True)
    s.setdefault("spinnerVerbs", {"mode": "append", "verbs": PAROLE_ROTELLA})  # mai sopra a quelle della persona
    if forza or not str(s.get("theme", "")).startswith("custom:tema-studio:"):  # Claude uguale al terminale
        s["theme"] = "custom:tema-studio:" + tinta_claude(asp)
    s.setdefault("enabledPlugins", {})["tema-studio@claude-crew"] = True  # installato ma spento = Claude arancione
    if json.dumps(s, sort_keys=True) != prima:
        if os.path.exists(p):
            shutil.copy(p, p + ".prima-di-crew")
        scrivi_json(p, s)
    if ha("claude"):  # il tema sta nel plugin tema-studio: senza il marketplace Claude torna al tema di base, zitto
        mancanti, _ = assicura_plugin({"claude-crew": CREW}, ["tema-studio@claude-crew"])
        if mancanti:
            return False, "plugin tema-studio non installato: `claude plugin marketplace add Radwtsm/claude-crew`, poi rilancia"
    pr = tema_prompt(asp)
    ss = tema_salvaschermo(asp)
    pr = f"{pr}; {ss}" if ss else pr
    if MAC:
        ok, cosa = (tema_terminale() if terminale_mac or os.environ.get("TERM_PROGRAM") == "Apple_Terminal"
                    else (True, "Terminale: invariato"))
        if app_iterm():
            ok2, cosa2 = tema_iterm()
            ok, cosa = ok and ok2, f"{cosa}; {cosa2}"
        return ok, f"{cosa}; {pr}"
    if WIN:
        ok, cosa = tema_windows()
        return ok, f"{cosa}; {pr}"
    return True, f"parole della rotella messe; {pr}; nel tuo terminale scegli uno sfondo nero pieno"


ITERM_GUID = "pleyades-pleiad-fire-red"


def app_iterm():
    return any(os.path.isdir(os.path.join(d, "iTerm.app")) for d in ("/Applications", os.path.join(CASA, "Applications")))


def tema_iterm():
    """Mac con iTerm2: profilo dinamico «Pleiad Fire Red» (nero pieno, niente trasparenza, colori del tema, intro e poi
    la shell di sempre) predefinito, barra delle schede «Minimal» (prende il nero del profilo)."""
    def c(h):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        return {"Red Component": r, "Green Component": g, "Blue Component": b, "Alpha Component": 1, "Color Space": "sRGB"}

    ct = colori_terminale()
    shell = os.environ.get("SHELL") or "/bin/zsh"
    cli = shutil.which(NOME_CLI) or os.path.join(CASA, ".local", "bin", NOME_CLI)  # ~/.local/bin non è nel PATH di -l -c
    p = {"Name": "Pleiad Fire Red", "Guid": ITERM_GUID, "Background Color": c("#000000"),
         "Foreground Color": c("#f2f2f2"), "Bold Color": c("#ffffff"), "Cursor Color": c(ct["cursore"]),
         "Cursor Text Color": c("#000000"), "Selection Color": c(ct["selezione"]), "Selected Text Color": c("#ffffff"),
         "Transparency": 0, "Blur": False, "Use Separate Colors for Light and Dark Mode": False,
         "Custom Command": "Yes", "Command": f"{shell} -l -c '\"{cli}\" intro; exec {shell} -l'"}
    for i, x in enumerate(ct["ansi"]):
        p[f"Ansi {i} Color"] = c(x)
    d = os.path.join(CASA, "Library", "Application Support", "iTerm2", "DynamicProfiles")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "pleyades.json"), "w", encoding="utf-8") as f:
        json.dump({"Profiles": [p]}, f, indent=1)
    time.sleep(1)  # iTerm2 carica i profili dinamici da solo; predefinito solo dopo che lo conosce
    dom = "com.googlecode.iterm2"
    run("defaults", "write", dom, "Default Bookmark Guid", ITERM_GUID)
    run("defaults", "write", dom, "TabStyleWithAutomaticOption", "-int", "5")
    if run("defaults", "read", dom, "Default Bookmark Guid")[1].strip() != ITERM_GUID:
        return False, "profilo iTerm2 creato ma non predefinito: iTerm2 → Settings → Profiles → «Pleiad Fire Red» → Other Actions → Set as Default"
    return True, "iTerm2: profilo «Pleiad Fire Red» predefinito (nero, intro all'apertura)"


def voce_tema(ui):
    ok, cosa = tema()
    ui.esito(Esito("look Pleyades (terminale + Claude)", ok, f"{cosa} → `{NOME_CLI} tema`", nota=cosa))
    return 0 if ok else 1


def jsonc(testo):
    """JSON con commenti (Windows Terminal): toglie // e /* */ fuori dalle stringhe."""
    out, i, n, dentro = [], 0, len(testo), False
    while i < n:
        ch = testo[i]
        if dentro:
            out.append(ch)
            if ch == "\\":
                out.append(testo[i + 1]); i += 1
            elif ch == '"':
                dentro = False
        elif ch == '"':
            dentro = True; out.append(ch)
        elif testo.startswith("//", i):
            i = testo.find("\n", i)
            i = n if i < 0 else i
            continue
        elif testo.startswith("/*", i):
            i = testo.find("*/", i) + 2 or n
            continue
        else:
            out.append(ch)
        i += 1
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", "".join(out)))


FINESTRE_CHIAVI = (r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", r"Software\Microsoft\Windows\DWM",
                   r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent", r"Control Panel\Desktop")


def valori_finestre(asp=None):
    """I colori di Windows per l'aspetto (solo impostazioni di Windows, niente programmi): modo scuro, colore
    principale = la tinta sulle barre del titolo e sui bordi; Start e barra delle applicazioni scure (rosse: owner no).
    [(chiave sotto HKCU, nome, "dword"|"binary", valore)]"""
    asp = asp or aspetto()
    base, chiaro, _ = asp["colori"]
    scala = [tuple(c[i] + (chiaro[i] - c[i]) * k for i in range(3)) for c, k in ((base, 0.8), (base, 0.55), (base, 0.28))]
    scala += [base] + [tuple(v * k for v in base) for k in (0.78, 0.56, 0.36, 0.22)]  # chiari, la tinta, scuri
    abgr = lambda c: (0xFF << 24) | (round(c[2]) << 16) | (round(c[1]) << 8) | round(c[0])
    argb = lambda c, a=0xC4: (a << 24) | (round(c[0]) << 16) | (round(c[1]) << 8) | round(c[2])
    pers, dwm, acc, desk = FINESTRE_CHIAVI
    return [(pers, "AppsUseLightTheme", "dword", 0), (pers, "SystemUsesLightTheme", "dword", 0),
            (pers, "ColorPrevalence", "dword", 0), (pers, "EnableTransparency", "dword", 0),
            (dwm, "ColorPrevalence", "dword", 1), (dwm, "AccentColor", "dword", abgr(base)),
            (dwm, "ColorizationColor", "dword", argb(base)), (dwm, "ColorizationAfterglow", "dword", argb(base)),
            (dwm, "AccentColorInactive", "dword", abgr(scala[5])),
            (acc, "AccentColorMenu", "dword", abgr(base)), (acc, "StartColorMenu", "dword", abgr(scala[5])),
            (acc, "AccentPalette", "binary", b"".join(bytes([round(c[0]), round(c[1]), round(c[2]), 0]) for c in scala)),
            (desk, "AutoColorization", "dword", 0)]


def tema_finestre(togli=False):
    """`pleyades-cli finestre [--togli]` (Windows): i colori dell'aspetto su tutto Windows. La prima volta salva i
    valori di prima in stato.json; --togli li rimette. Avvisa le app subito (niente riavvio)."""
    if not WIN:
        return False, "solo su Windows"
    import ctypes, winreg
    prima = stato().get("finestre_prima")
    if togli:
        if not prima:
            return False, "niente da rimettere: i colori di Windows non li ha cambiati pleyades-cli"
        for chiave, nome, tipo, val in prima:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, chiave) as k:
                if val is None:
                    try:
                        winreg.DeleteValue(k, nome)
                    except OSError:
                        pass
                else:
                    winreg.SetValueEx(k, nome, 0, winreg.REG_BINARY if tipo == "binary" else winreg.REG_DWORD,
                                      bytes.fromhex(val) if tipo == "binary" else val)
        salva_stato(finestre_prima=None)
    else:
        nuovi = valori_finestre()
        if not prima:  # i valori di prima, una volta sola: --togli torna lì anche dopo più cambi di tinta
            vecchi = []
            for chiave, nome, tipo, _ in nuovi:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chiave) as k:
                        v = winreg.QueryValueEx(k, nome)[0]
                    vecchi.append([chiave, nome, tipo, v.hex() if isinstance(v, bytes) else v])
                except OSError:
                    vecchi.append([chiave, nome, tipo, None])
            salva_stato(finestre_prima=vecchi)
        for chiave, nome, tipo, val in nuovi:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, chiave) as k:
                winreg.SetValueEx(k, nome, 0, winreg.REG_BINARY if tipo == "binary" else winreg.REG_DWORD, val)
    for parola in ("ImmersiveColorSet", "WindowsThemeElement"):  # WM_SETTINGCHANGE a tutte le finestre
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, parola, 2, 3000, None)
    return True, ("colori di Windows rimessi come prima" if togli else
                  f"Windows scuro con la tua tinta su barre del titolo e bordi (`{NOME_CLI} finestre --togli` per tornare indietro)")


def tema_windows():
    nome = "Pleiad Fire Red"
    loc = os.environ.get("LOCALAPPDATA", "")
    cand = [os.path.join(loc, "Packages", f"Microsoft.WindowsTerminal{x}_8wekyb3d8bbwe", "LocalState", "settings.json")
            for x in ("", "Preview")] + [os.path.join(loc, "Microsoft", "Windows Terminal", "settings.json")]
    f = next((c for c in cand if os.path.isfile(c)), None)
    if not f:
        return False, "Windows Terminal non trovato: installalo dal Microsoft Store e rilancia"
    try:
        with open(f, encoding="utf-8-sig") as fh:
            w = jsonc(fh.read())
    except (OSError, ValueError) as e:
        return False, f"impostazioni di Windows Terminal illeggibili ({e}): non le tocco"
    nomi = ["black", "red", "green", "yellow", "blue", "purple", "cyan", "white"]
    ct = colori_terminale()
    schema = {"name": nome, "background": "#000000", "foreground": "#F2F2F2", "cursorColor": ct["cursore"].upper(),
              "selectionBackground": ct["selezione"].upper()}
    for i, c in enumerate(ct["ansi"]):
        k = nomi[i % 8]
        schema[("bright" + k.capitalize()) if i > 7 else k] = c.upper()
    w["schemes"] = [x for x in w.get("schemes", []) if x.get("name") != nome] + [schema]
    prof = w.setdefault("profiles", {})
    if isinstance(prof, list):
        prof = w["profiles"] = {"list": prof}
    prof.setdefault("defaults", {}).update(colorScheme=nome, opacity=100, useAcrylic=False)
    # la barra in alto (schede e titolo) nera come lo sfondo, non il grigio del tema di Windows
    w["themes"] = [x for x in w.get("themes", []) if x.get("name") != nome] + [{
        "name": nome, "window": {"applicationTheme": "dark", "useMica": False},
        "tabRow": {"background": "#000000FF", "unfocusedBackground": "#000000FF"},
        "tab": {"background": "terminalBackground", "unfocusedBackground": "#000000FF", "showCloseButton": "hover"}}]
    w["theme"] = nome
    if not os.path.exists(f + ".prima-di-crew"):  # la copia resta quella di prima del primo giro
        shutil.copy(f, f + ".prima-di-crew")
    # l'intro a ogni scheda nuova di PowerShell: dalla riga di comando del profilo di Windows Terminal ($PROFILE
    # no: su Windows Home la policy Restricted non lo esegue, sanghez 28/10)
    cli = os.path.join(BIN, f"{NOME_CLI}.cmd")
    for x in prof.get("list", []):
        c, sorg = str(x.get("commandline", "")).lower(), str(x.get("source", ""))
        if "intro" in c and "starship" in c:
            continue
        if sorg == "Windows.Terminal.PowershellCore" or "pwsh" in c:
            exe = "pwsh.exe"
        elif "powershell" in c or "powershell" in str(x.get("name", "")).lower():
            exe = "powershell.exe"
        else:
            continue
        # Starship dalla riga di comando, non da $PROFILE (Restricted, vedi sopra)
        x["commandline"] = (f"{exe} -NoLogo -NoExit -Command \"& '{cli}' intro; if (Get-Command starship -EA 0) "
                            "{ Invoke-Expression (&starship init powershell) }\"")
    scrivi_json(f, w)
    ps = shutil.which("powershell") and subprocess.run(["powershell", "-NoProfile", "-Command", "$PROFILE"],
                                                       capture_output=True, text=True).stdout.strip()
    if ps and os.path.isfile(ps):  # la riga della versione di prima, che con Restricted dà errore a ogni scheda
        testo = open(ps, encoding="utf-8-sig").read()
        if "# Pleyades tools" in testo:
            with open(ps, "w", encoding="utf-8") as fh:
                fh.write("".join(r for r in testo.splitlines(True) if "# Pleyades tools" not in r))
    return True, f"schema «{nome}» predefinito in Windows Terminal (copia: settings.json.prima-di-crew), intro nelle schede nuove"


def tema_terminale():
    """Mac: il profilo «Pleiad Fire Red» del Terminale (nero pieno, colori del tema, intro all'apertura),
    predefinito per le finestre nuove. Solo Mac: altrove lo sfondo nero si sceglie nelle impostazioni del terminale."""
    nome = "Pleiad Fire Red"
    ct = colori_terminale()
    ansi = ct["ansi"]
    nomi = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]
    p = {"name": nome, "type": "Window Settings", "ProfileCurrentVersion": 2.07, "columnCount": 110, "rowCount": 32,
         "BackgroundColor": colore_ns("#000000"), "TextColor": colore_ns("#f2f2f2"), "TextBoldColor": colore_ns("#ffffff"),
         "CursorColor": colore_ns(ct["cursore"]), "SelectionColor": colore_ns(ct["selezione"]), "BackgroundBlur": 0.0,
         "CommandString": "pleyades-cli intro", "RunCommandAsShell": False, "shellExitAction": 1}
    for i, c in enumerate(ansi):
        p[f"ANSI{'Bright' if i > 7 else ''}{nomi[i % 8]}Color"] = colore_ns(c)
    f = os.path.join(CARTELLA, f"{nome}.terminal")
    with open(f, "wb") as fh:
        plistlib.dump(p, fh)
    # aprire il file lo importa (e apre una finestra con l'intro); poi diventa il profilo delle finestre nuove
    subprocess.run(["open", f], check=False)
    time.sleep(1.5)
    r = subprocess.run(["osascript", "-e", f'tell application "Terminal" to set default settings to settings set "{nome}"',
                        "-e", f'tell application "Terminal" to set startup settings to settings set "{nome}"'],
                       capture_output=True, text=True)
    if r.returncode:
        return False, f"profilo importato ma non predefinito: Terminale → Impostazioni → Profili → «{nome}» → Predefinito"
    return True, f"profilo «{nome}» predefinito: le finestre nuove del Terminale sono nere, con l'intro"


def main():
    a = sys.argv[1:]
    if sys.stdout is None:  # pythonw (attività pianificata su Windows): l'output nel log
        sys.stdout = sys.stderr = open(LOG_PIANO, "w", encoding="utf-8")
    if a[:1] == ["hook"]:
        try:
            return hook()
        except Exception:
            return 0
    if a[:1] == ["salvaschermo"]:
        return intro(salvaschermo=True)
    if a[:1] == ["intro"]:
        if "--256" in a:
            os.environ["PLEYADES_COLORI"] = "256"
        return intro(resta="--resta" in a)
    if a[:1] in (["-h"], ["--help"], ["aiuto"]):
        print(__doc__)
        return 0
    path_aggiornato()
    for x in a:
        if x.startswith("--studio="):
            salva_stato(studio=studio_url(x.split("=", 1)[1]))
    a = [x for x in a if not x.startswith("--studio=")]
    ui = interfaccia()
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
        if cmd == "profilo" and a[1:2] in (["casa"], ["lavoro"]):
            salva_stato(profilo=a[1])
            print(f"✅ profilo di questo computer: {a[1]}")
            return 0
        if cmd in ("prendi", "togli"):
            if len(a) < 2:
                ui.titolo("Plugin di Pleyades tools che puoi prendere su questo computer")
                for nome, descr in catalogo_crew().items():
                    ui.info(f"{ui.c('1', nome)}  {descr[:90]}")
                return 0
            ok, cosa = prendi(a[1], " ".join(a[2:])) if cmd == "prendi" else togli(a[1])
            ui.esito(Esito(f"{'preso' if cmd == 'prendi' else 'tolto'}: {a[1]}", ok, cosa,
                           nota="valido dalla prossima sessione di Claude Code"))
            return 0 if ok else 1
        if cmd == "tema":
            return voce_tema(ui)
        if cmd == "aspetto":
            return voce_aspetto(ui)
        if cmd == "finestre":
            ok, cosa = tema_finestre(togli="--togli" in a)
            ui.esito(Esito("colori di Windows", ok, cosa, nota="se una barra resta com'era: esci e rientra da Windows"))
            return 0 if ok else 1
        if cmd == "pianifica":
            ok, cosa = pianifica(togli="--togli" in a)
            ui.esito(Esito("aggiornamento automatico pianificato", ok, cosa, nota=cosa))
            return 0 if ok else 1
        f = {"controlla": controlla, "squadra": squadra, "aggiorna": aggiorna, "auto": auto, "diagnosi": diagnosi, "progetti": progetti, "link": link, "kit": mio_kit}.get(cmd)
        if f:
            return f(ui)
        print(f"pleyades-cli: comando «{cmd}» sconosciuto. `pleyades-cli --help` per l'elenco.")
        return 2
    except KeyboardInterrupt:
        for x in list(SCHERMI):
            x.chiudi()
        print("\n   Interrotto. Rilancia `pleyades-cli` quando vuoi: riparte da dove eri.")
        return 130
    finally:
        for x in list(SCHERMI):
            x.chiudi()


if __name__ == "__main__":
    sys.exit(main())
