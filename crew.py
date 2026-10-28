#!/usr/bin/env python3
"""pleyades-cli (Pleyades tools): la guida unica per entrare nei progetti, anche per chi non programma.

    pleyades-cli                    la prima volta la guida; poi un menu
    pleyades-cli guida [OWNER/REPO …] [--studio=INDIRIZZO]   dall'inizio a tutto pronto: Claude Code, GitHub (con o senza
                            account), plugin, progetti, Nextcloud e la stanza Talk; si può rilanciare: salta il fatto.
                            Con --studio: accesso allo studio Nextcloud dal browser («Concedi accesso», la password
                            per app si salva da sola) e i progetti condivisi lì, anche senza GitHub
    pleyades-cli entra OWNER/REPO   entra in un progetto (clone, plugin, stanza, cartelle)
    pleyades-cli controlla          solo i controlli, senza installare niente
    pleyades-cli aggiorna           pleyades-cli, plugin e progetti all'ultima versione
    pleyades-cli progetti           i tuoi progetti e a che punto sono
    pleyades-cli link               i link giusti (studio, Talk, Dashboard, cartelle)
    pleyades-cli hook               (per un hook SessionStart) installa i plugin che il progetto aperto chiede e mancano
    pleyades-cli profilo casa|lavoro   che computer è: «lavoro» = solo le regole comuni, niente progetti, Talk o Nextcloud
    pleyades-cli prendi NOME ["perché"] / pleyades-cli togli NOME   un plugin di Pleyades tools solo su questo computer (per il lavoro),
                            segnato in locale con data e motivo; `pleyades-cli aggiorna` non ne aggiunge mai altri

Un progetto dice cosa gli serve in `.claude/progetto.json` del suo repo (stanza, talk, cartelle, plugin,
marketplace, passi, dopo, primo_prompt, moduli, marchio, comando); i plugin di `.claude/settings.json` con valore true contano anche loro.
L'indirizzo di Nextcloud viene dal `talk.py` del progetto, l'aspetto dal suo `marchio` (se c'è) e `comando` dà un
secondo nome allo stesso programma (es. il nome dello studio): questo file è pubblico e non ne contiene.
Progetti dallo studio: ogni cartella condivisa che contiene `.claude/progetto.json` (copia di sola lettura del repo,
con `.claude-plugin/` e `plugins/`) è un progetto: chi non ha accesso al repo GitHub (`repo` in progetto.json) la
riceve in ~/.crew/studio/ e i suoi plugin come marketplace locale; le proposte vanno nella cartella `proposte`.
Il profilo e i plugin presi stanno solo in ~/.config/crew/stato.json di questo computer: mai inviati a nessuno.
Mac, Linux e Windows (python3 o python). Solo libreria standard. Le funzioni non stampano: la stampa è in
`Terminale`, così un'app con finestra può riusare le stesse funzioni con un'altra interfaccia.
"""
import hashlib, importlib.util, io, json, os, platform, re, shutil, subprocess, sys, tarfile, threading, time
import urllib.error, urllib.parse, urllib.request, webbrowser, xml.etree.ElementTree as ET, zipfile
from concurrent.futures import ThreadPoolExecutor

CREW = "Radwtsm/claude-crew"
NOME_CLI = "pleyades-cli"  # il nome che si vede (owner 28/10: tutto Pleyades tools, niente «crew»)
CREW_PY = "https://raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py"
GH_RELEASE = "https://api.github.com/repos/cli/cli/releases/latest"
CASA = os.path.expanduser("~")
CARTELLA = os.path.join(CASA, ".crew")  # crew.py installato
STATO = os.path.join(CASA, ".config", "crew", "stato.json")  # scelte della persona, mai segreti
BIN = os.path.join(CASA, ".local", "bin")
CODICE = os.path.join(CASA, "code")
WIN, MAC = os.name == "nt", sys.platform == "darwin"
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
            return subprocess.run(list(cmd), cwd=cwd).returncode, ""
        r = subprocess.run(list(cmd), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd,
                           timeout=timeout)
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
    if not t.credenziali():
        t.scrivi_json(t.CONF, {"utente": cred["utente"], "password": cred["password"]})


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

def installa_comando(nome=NOME_CLI):
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
    path_aggiornato()
    return ha(nome)


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
            k = os.read(fd, 1).decode(errors="ignore")
            if k == "\x1b":
                k += os.read(fd, 2).decode(errors="ignore")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, prima)
        k = {"\x1b[A": "su", "\x1bOA": "su", "\x1b[B": "giu", "\x1bOB": "giu"}.get(k, k)
    if k == "\x03":
        raise KeyboardInterrupt
    if k in ("j", "k"):
        return {"k": "su", "j": "giu"}[k]
    return "invio" if k in ("\r", "\n") else k


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

    def intestazione(self, t):
        """Il riquadro d'apertura, come quello di Claude Code."""
        self.riquadro([self.acc("✦ ") + self.c("1", "Pleyades tools") + self.c("2", f"  {self.nome}"), "  " + t,
                       self.c("2", "  ↑↓ scegli · Invio conferma · Ctrl+C esci (riprende da dove eri)")])

    def riquadro(self, righe):
        vis = [len(re.sub(r"\x1b\[[0-9;]*m", "", r)) for r in righe]
        w = max(vis) + 2
        print("\n" + self.c("2", "╭" + "─" * w + "╮"))
        for r, n in zip(righe, vis):
            print(self.c("2", "│") + " " + r + " " * (w - n - 1) + self.c("2", "│"))
        print(self.c("2", "╰" + "─" * w + "╯"))

    def c(self, codice, t):
        return f"\033[{codice}m{t}\033[0m" if self.colori else t

    def acc(self, t):
        return self.c(ACCENTO, t)

    def titolo(self, t):
        print("\n" + self.acc("✦") + " " + self.c("1", t))
        self.attacco = True

    def passo(self, n, tot, t, spiega=""):
        """⏺ Passo  n/tot · spiegazione, poi i risultati attaccati sotto con ⎿ (come le azioni di Claude Code)."""
        print("\n" + self.acc("⏺") + " " + self.c("1", t) + self.c("2", f"  {n}/{tot}" + (f" · {spiega}" if spiega else "")))
        self.attacco = True

    def rientro(self):
        r = "  ⎿ " if getattr(self, "attacco", False) else "    "
        self.attacco = False
        return self.c("2", r)

    def info(self, t):
        print("    " + t)

    def fai(self, t):
        """Cosa deve fare la persona: in giallo, con il nome esatto di pulsanti e menu."""
        for r in t.split("\n"):
            print("    " + self.acc("→") + " " + r)

    def esito(self, e):
        self.esiti.append(e)
        if e.saltato:
            print(self.rientro() + self.c("2", f"✓ {e.nome}" + (f" · {e.nota}" if e.nota else "")))
        elif e.ok:
            print(self.rientro() + self.c("32", "✓") + f" {e.nome}" + (self.c("2", f" · {e.nota}") if e.nota else ""))
        else:
            print(self.rientro() + self.c("31", "✗") + f" {e.nome}")
            if e.cosa:
                self.fai(e.cosa)
            while e.riprova and sys.stdin.isatty() and self.conferma("Fatto?", "Riprova adesso", "Salta per ora"):
                try:
                    e.ok = bool(e.riprova())
                except Exception as x:  # un errore nel riprovare non ferma la guida
                    self.fai(f"non ancora: {x}")
                if e.ok:
                    print("    " + self.c("32", "✓") + f" {e.nome}")
                    break
                print("    " + self.c("31", "✗") + f" {e.nome} · ancora no")
        return e.ok

    def link(self, nome, url):
        print("    " + self.c("2", f"{nome:<26}") + " " + (self.c("4", url) if url.startswith("http") else url))

    def chiedi(self, domanda, base=""):
        try:
            r = input("\n  " + self.acc("?") + " " + self.c("1", domanda) + self.c("2", f" [{base}]" if base else "")
                      + "\n  " + self.acc("❯") + " ").strip()
        except EOFError:
            r = ""
        return r or base

    def scegli(self, domanda, opzioni):
        """opzioni = [testo]; la prima è la consigliata. Torna l'indice. Frecce ↑↓ e Invio, come in Claude Code
        (o il numero); senza un terminale vero: scrivi il numero."""
        print("\n  " + self.acc("?") + " " + self.c("1", domanda))
        if self.colori and sys.stdin.isatty():
            try:
                return self._menu(opzioni)
            except (OSError, ImportError):
                pass  # niente tasti singoli (es. console strana): si ripiega sul numero
        for i, o in enumerate(opzioni, 1):
            print(f"    {i}. {o}" + (self.c("2", "  (consigliata)") if i == 1 else ""))
        while True:
            r = self.chiedi("Scrivi il numero e premi Invio:", "1")
            if r.isdigit() and 1 <= int(r) <= len(opzioni):
                return int(r) - 1

    def _menu(self, opzioni):
        def riga(i, o):
            nota = self.c("2", "  (consigliata)") if i == 0 else ""
            return (self.acc(f"  ❯ {i + 1}. {o}") if i == sel else f"    {i + 1}. {o}") + nota
        sel, n = 0, len(opzioni)
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
        if self.ui.colori:
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
        if self.ui.colori:
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
        self.m.intestazione(t)

    def titolo(self, t):
        print("\n" + self.m.c("✦ " + t, "brillio", forte=True) if self.colori else "\n✦ " + t)


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


def claude_collegato():
    try:
        return json.loads(run("claude", "auth", "status", "--json", timeout=30)[1] or "{}").get("loggedIn") is True
    except ValueError:
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
    ui.fai(SPIEGA_CLAUDE)

    def accedi():
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
  3. premi «Concedi accesso»: la password per questo computer si salva da sola, non la vedi mai"""


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
    tieni = [credenziali_note() or accedi_studio(ui, server)]

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
    if hook_git(d):
        ui.esito(Esito("controlli prima del commit (hook git)", True))
    moduli_del_progetto(c)
    t = modulo_talk(d, c)
    conf = None
    if t:
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
            ui.esito(Esito("app Nextcloud sul computer", app_nextcloud(),
                           "scaricala da nextcloud.com/install («Desktop»), accedi con il tuo utente, poi "
                           "«⋯» → «Scegli cosa sincronizzare» → spunta " + ", ".join(f"«{x}»" for x in c["cartelle"]),
                           riprova=app_nextcloud))
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
    ui.intestazione("la guida da zero a pronto")
    ui.info("Faccio io quello che posso; quando serve te, te lo dico in giallo con 👉.")
    ui.info("Si può interrompere (Ctrl+C) e rilanciare quando vuoi: salta ciò che è già fatto.")
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
        nuova.esiti = ui.esiti
        ui = nuova
    for _, r in pronti:
        mostra_link(ui, *r)
        for x in r[1].get("dopo", []):
            ui.fai(x)
    minuti = round((time.time() - inizio) / 60, 1)
    ui.riepilogo(minuti)
    ui.titolo("Regole d'uso")
    for r in REGOLE_USO.split("\n")[1:]:
        ui.info(r.strip())
    verdi = sum(e.ok or e.saltato for e in ui.esiti)
    for etichetta, (d, c, t, conf) in pronti:
        if t and stanza_collegata(t, c.get("stanza")):
            scrivi_in_stanza(d, c, f"🆕 pleyades-cli guida su {platform.system()}: {verdi}/{len(ui.esiti)} a posto in "
                             f"{minuti} min ({etichetta.split('/')[-1]})")
    primo = pronti[0][1][0] if pronti else CASA
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
    for repo, d in cartelle_progetti():
        c = config_progetto(d)
        manca = [p for p in c["plugin"] if ha("claude") and p not in inst]
        ui.esito(Esito(f"{repo}: plugin", not manca, "pleyades-cli aggiorna"))
        t = modulo_talk(d, c)
        if t:
            ui.esito(Esito(f"{repo}: stanza Talk", bool(stanza_collegata(t, c.get("stanza"))), f"pleyades-cli entra {repo}"))
    ui.riepilogo(0)
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


def menu(ui):
    voci = [("Controlla che sia tutto a posto", controlla), ("Aggiorna pleyades-cli, plugin e progetti", aggiorna),
            ("I miei progetti", progetti), ("Entra in un nuovo progetto", None), ("I link", link),
            ("Rifai la guida da capo", lambda u: guida(u, []))]
    ui.intestazione("cosa c'è e cosa manca")
    if not lavoro():
        aperti = cantieri_aperti()
        if aperti and "nessun" not in aperti.lower():
            ui.titolo("Cantieri aperti (operazioni in corso)")
            for r in aperti.splitlines()[:6]:
                ui.info(r)
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
        f = {"controlla": controlla, "aggiorna": aggiorna, "progetti": progetti, "link": link}.get(cmd)
        if f:
            return f(ui)
        print(f"pleyades-cli: comando «{cmd}» sconosciuto. `pleyades-cli --help` per l'elenco.")
        return 2
    except KeyboardInterrupt:
        print("\n   Interrotto. Rilancia `pleyades-cli` quando vuoi: riparte da dove eri.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
