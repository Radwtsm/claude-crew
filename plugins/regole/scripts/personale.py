#!/usr/bin/env python3
"""Il Claude di ognuno configurato come quello del manutentore (skill configura-claude): regole personali in un repo
privato, una sola memoria per tutti i progetti, sincronizzazione automatica, barra di stato, avviso di uso alto.

  personale.py setup        crea o clona ~/claude-personale (GitHub privato, con gh), collega regole, memoria,
                            barra di stato e aggiornamento automatico dei marketplace
  personale.py controlla    stampa cosa manca (exit 1 se qualcosa non è a posto), con i byte fissi
  personale.py misura       byte che Claude carica a ogni sessione (regole, memoria, descrizioni delle skill)
  personale.py inizio       hook SessionStart: pull, memoria collegata anche per il progetto aperto, limiti
  personale.py fine         hook Stop: commit + push di regole e memoria cambiate
  personale.py mappa        la mappa di questo computer in ~/claude-personale/mappa-<computer>.md (md che Claude
                            legge, skill, plugin, progetti, cartelle condivise, scarti dalla struttura comune);
                            rifatta a ogni avvio, va nel repo col sync: ogni Claude sa dove sta cosa su ogni PC
  personale.py statusline   barra di stato: modello · contesto · uso 5h/7g con reset · durata
  personale.py avviso       hook UserPromptSubmit: una riga a Claude quando l'uso 5h o 7g passa il 50% (risposte
                            corte) o SOGLIA (chiudi e salva); solo al cambio di livello. Suggerisce anche un plugin
                            non installato quando le parole della richiesta corrispondono ai suoi `keywords`

Senza ~/claude-personale gli hook non fanno niente. Mac, Linux e Windows (python o python3); solo libreria standard.
"""
import glob, hashlib, json, os, platform, re, shutil, socket, subprocess, sys, time

HOME = os.path.expanduser("~")
REPO = os.path.join(HOME, "claude-personale")
MEMORIA = os.path.join(REPO, "memoria")
CONFIG = os.path.expanduser(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(HOME, ".claude"))
CACHE = os.path.join(CONFIG, "uso-cache.json")
IMPORT = "@~/claude-personale/regole.md"
SOGLIA = 85
AVVISO = os.path.join(CONFIG, "uso-avviso.json")
SUGGERITI = os.path.join(CONFIG, "plugin-suggeriti.json")
PRATICHE = os.path.join(CONFIG, "pratiche-avvisate.json")
# Cattive pratiche che uno script riconosce senza dubbi (buone-pratiche.md): tema → (giorni di silenzio, consiglio).
# Il segreto ogni volta: va cambiato comunque.
CONSIGLI = {
    "segreto": (0, "sembra esserci un segreto (chiave, token, password) nel messaggio: NON ripeterlo, digli che va "
                   "cambiato e che la prossima volta lo scrive in un comando che lo chiede"),
    "log": (1, "ha incollato un log o un output lungo: usa solo le righe che contano e digli che basta l'errore (o "
               "il percorso del file)"),
    "lungo": (1, "messaggio molto lungo: se dentro ci sono più argomenti, fai il primo e proponi gli altri dopo /clear; "
                 "digli che funziona meglio un argomento per messaggio, scopo in una riga"),
    "salta": (1, "chiede di saltare un controllo: spiega cosa segnala e correggi la causa invece di aggirarlo"),
}
RE_SEGRETO = re.compile(r"\b(sk-(ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
                        r"AKIA[0-9A-Z]{16}|xox[abp]-[A-Za-z0-9-]{20,}|AIza[0-9A-Za-z_-]{30,})|-{5}BEGIN [A-Z ]*PRIVATE KEY|"
                        r"\b(password|passwd|token|api[_-]?key|secret)\s*[:=]\s*\S{8,}", re.I)
RE_LOG = re.compile(r"^\s*(\d{4}-\d\d-\d\d[ T]\d\d:\d\d|\[?\d\d:\d\d:\d\d|at [\w.$]+\(|File \".*\", line \d+|"
                    r"(ERROR|WARN|INFO|DEBUG)\b|Traceback)", re.M)
RE_SALTA = re.compile(r"--no-verify|salta (i |il )?(test|controll|hook)|disattiva (i |il )?(test|controll|hook)|"
                      r"skip (the )?(tests?|checks?|hooks?)", re.I)
LIVELLI = ((SOGLIA, "niente lavori nuovi grandi: chiudi il passo in corso, salva lo stato (commit, backlog, prompt per "
                    "ripartire) e dillo all'utente."),
           (50, "risposte corte, letture mirate (grep, sezioni), niente subagent né ricerche larghe; a fine argomento "
                "proponi /clear con un prompt per ripartire."))
WIN = os.name == "nt"
GIORNI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]

REGOLE = """# Regole personali

Le mie regole per Claude, uguali su ogni computer (repo privato `claude-personale`). Vincono su quelle della crew.
Struttura e dove va una cosa nuova: skill `organizza-claude`.

## Chi sono e cosa faccio

## Come rispondermi

## Come lavoriamo

## I miei strumenti

## Da non fare mai
"""
LIMITI = """# Byte massimi dei file letti a ogni sessione (personale.py li controlla all'avvio). Sforato: i dettagli in un
# file per tema, letto quando serve (organizza-claude).
6000   regole.md
6000   memoria/MEMORY.md
"""


def run(cmd, cwd=None, timeout=60):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def git(*args, timeout=60):
    return run(["git", "-C", REPO, *args], timeout=timeout)


def leggi_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def scrivi_json(p, dati):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, p)


def scrivi_se_manca(nome, testo):
    p = os.path.join(REPO, nome)
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)


# ---- memoria unica

def cartella_progetto(cwd):
    """Come Claude Code chiama la cartella di un progetto in ~/.claude/projects (ogni carattere non alfanumerico → -)."""
    return os.path.join(CONFIG, "projects", re.sub(r"[^A-Za-z0-9]", "-", cwd))


def collegata(d):
    return os.path.exists(d) and os.path.realpath(d) == os.path.realpath(MEMORIA)


def collega(d):
    """Unisce una memoria locale a quella unica (copia, niente sovrascritto) e la sostituisce con un collegamento."""
    if collegata(d):
        return None
    os.makedirs(os.path.dirname(d), exist_ok=True)
    if os.path.islink(d):
        os.unlink(d)
    elif os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            src, dst = os.path.join(d, f), os.path.join(MEMORIA, f)
            if not os.path.isfile(src):
                continue
            if f == "MEMORY.md":
                vecchie = open(dst, encoding="utf-8").read().splitlines() if os.path.exists(dst) else []
                nuove = [r for r in open(src, encoding="utf-8").read().splitlines() if r.strip() and r not in vecchie]
                with open(dst, "a", encoding="utf-8", newline="\n") as out:
                    out.writelines(r + "\n" for r in nuove)
            elif not os.path.exists(dst):
                shutil.copy2(src, dst)
            elif open(src, "rb").read() != open(dst, "rb").read():
                shutil.copy2(src, os.path.join(MEMORIA, f[:-3] + "-" + os.path.basename(os.path.dirname(d)).strip("-")[-20:] + ".md"))
        os.rename(d, d + ".prima-di-unire-" + time.strftime("%Y%m%d%H%M%S"))  # copia di sicurezza, niente perso
    if WIN:  # giunzione: non chiede i permessi da amministratore come un collegamento simbolico
        r = run(["cmd", "/c", "mklink", "/J", d, MEMORIA])
        if r.returncode:
            return f"memoria: collegamento non creato per {d}: {(r.stderr or r.stdout).strip()}"
    else:
        os.symlink(MEMORIA, d)
    return f"memoria: {d} ora è la memoria unica"


def collega_tutte(cwd=None):
    if not os.path.isdir(MEMORIA):
        return []
    dirs = {os.path.join(p, "memory") for p in glob.glob(os.path.join(CONFIG, "projects", "*")) if os.path.isdir(p)}
    if cwd:
        dirs.add(os.path.join(cartella_progetto(cwd), "memory"))
    return [m for m in (collega(d) for d in sorted(dirs)) if m]


# ---- limiti e formato

def fuori_limite():
    out = []
    try:
        righe = open(os.path.join(REPO, "limiti-contesto.txt"), encoding="utf-8").read().splitlines()
    except OSError:
        return out
    for r in righe:
        if not r.strip() or r.startswith("#"):
            continue
        massimo, schema = r.split(None, 1)
        for p in glob.glob(os.path.join(REPO, schema.strip())):
            if os.path.getsize(p) > int(massimo):
                out.append(f"{os.path.relpath(p, REPO)} {os.path.getsize(p)} byte > {massimo}")
    return out


# ---- comandi

def setup():
    if not shutil.which("git") or not shutil.which("gh"):
        print("Servono git e gh (GitHub CLI) installati dalle fonti ufficiali, poi `gh auth login`.")
        return 2
    if run(["gh", "auth", "status"]).returncode:
        print("GitHub non collegato: lancia `gh auth login` (poi rilancia setup).")
        return 2
    if not os.path.isdir(os.path.join(REPO, ".git")):
        utente = run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
        if run(["gh", "repo", "view", f"{utente}/claude-personale"]).returncode == 0:
            r = run(["gh", "repo", "clone", f"{utente}/claude-personale", REPO], timeout=180)
        else:
            r = run(["gh", "repo", "create", "claude-personale", "--private", "--clone",
                     "--description", "Regole personali e memoria di Claude"], cwd=HOME, timeout=180)
        if r.returncode:
            print(f"Repo claude-personale non creato: {(r.stderr or r.stdout).strip()}")
            return 1
    else:
        git("pull", "-q", "--ff-only")
    scrivi_se_manca("regole.md", REGOLE)
    scrivi_se_manca("memoria/MEMORY.md", "")
    scrivi_se_manca("limiti-contesto.txt", LIMITI)
    scrivi_se_manca(".gitignore", ".DS_Store\n*.tmp\n")
    fatti = ["repo ~/claude-personale (privato su GitHub)"]

    cm = os.path.join(CONFIG, "CLAUDE.md")
    testo = open(cm, encoding="utf-8").read() if os.path.exists(cm) else ""
    if IMPORT not in testo:
        if testo.strip():
            shutil.copy2(cm, cm + ".prima-di-configura")
        with open(cm, "w", encoding="utf-8", newline="\n") as f:
            f.write(IMPORT + "\n" + ("\n" + testo if testo.strip() else ""))
        fatti.append(f"{cm}: importa le regole personali" + (" (copia: CLAUDE.md.prima-di-configura)" if testo.strip() else ""))

    sp = os.path.join(CONFIG, "settings.json")
    s = leggi_json(sp)
    prima = json.dumps(s, sort_keys=True)
    script = os.path.join(CONFIG, "plugins", "marketplaces", "claude-crew", "plugins", "regole", "scripts", "personale.py")
    py = shutil.which("python" if WIN else "python3") or sys.executable  # il comando, non la versione: regge gli aggiornamenti
    comando = f'"{py}" "{script}" statusline'.replace("\\", "/")
    if "personale.py" in json.dumps(s.get("statusLine", {})) or not s.get("statusLine"):
        s["statusLine"] = {"type": "command", "command": comando}
    else:
        fatti.append("barra di stato: ne hai già una, lasciata com'è (chiedi a Claude se vuoi quella della crew)")
    noti = leggi_json(os.path.join(CONFIG, "plugins", "known_marketplaces.json"))
    extra = s.setdefault("extraKnownMarketplaces", {})
    for nome, m in noti.items():
        src = (m or {}).get("source") or {}
        if src.get("source") == "github" and nome != "claude-plugins-official":
            extra.setdefault(nome, {"source": {"source": "github", "repo": src.get("repo")}})["autoUpdate"] = True
    if json.dumps(s, sort_keys=True) != prima:
        if os.path.exists(sp):
            shutil.copy2(sp, sp + ".prima-di-configura")
        scrivi_json(sp, s)
        fatti.append("barra di stato + aggiornamento automatico dei marketplace in settings.json")

    fatti += collega_tutte(os.getcwd())
    git("add", "-A")
    if git("diff", "--cached", "--quiet").returncode:
        git("commit", "-q", "-m", "configura-claude: struttura iniziale")
        git("branch", "-M", "main")
        git("push", "-q", "-u", "origin", "main", timeout=120)
    print("\n".join("- " + f for f in fatti))
    return 0


NUCLEO, INDICE, SKILL_MAX = 4500, 6000, 12000  # byte: regole sempre caricate, indice della memoria, descrizioni


def misura(stampa=True):
    """What is in context at every session, in bytes (1 token ≈ 4 byte): CLAUDE.md + its @imports, the memory index,
    the descriptions of the skills of the enabled plugins. Returns the lines over the limits."""
    righe, troppo = [], []
    cm = os.path.join(CONFIG, "CLAUDE.md")
    regole = 0
    if os.path.exists(cm):
        t = open(cm, encoding="utf-8").read()
        regole = len(t.encode())
        for imp in re.findall(r"^@(\S+)", t, re.M):
            p = os.path.expanduser(imp)
            if os.path.isfile(p):
                regole += os.path.getsize(p)
    righe.append(("regole sempre caricate (CLAUDE.md + @import)", regole, NUCLEO))
    mem = os.path.join(MEMORIA, "MEMORY.md")
    righe.append(("indice della memoria", os.path.getsize(mem) if os.path.exists(mem) else 0, INDICE))
    attivi = {k for k, v in leggi_json(os.path.join(CONFIG, "settings.json")).get("enabledPlugins", {}).items() if v}
    desc = 0
    for k in attivi:
        nome, mk = k.split("@", 1)
        vers = sorted(glob.glob(os.path.join(CONFIG, "plugins", "cache", mk, nome, "*")), key=os.path.getmtime)
        for f in glob.glob(os.path.join(vers[-1], "skills", "*", "SKILL.md")) if vers else []:
            d = re.search(r"^description:\s*(.+)$", open(f, encoding="utf-8").read(), re.M)
            desc += len(d.group(1).encode()) if d else 0
    righe.append((f"descrizioni delle skill ({len(attivi)} plugin accesi)", desc, SKILL_MAX))
    for nome, n, lim in righe:
        if n > lim:
            troppo.append(f"{nome}: {n} byte > {lim} (organizza-claude → contesto snello)")
    if stampa:
        print("\n".join(f"{n:>7} byte  {nome}" + ("  ⚠️" if n > lim else "") for nome, n, lim in righe))
        print(f"{sum(n for _, n, _ in righe):>7} byte  totale (≈ {sum(n for _, n, _ in righe) // 4} token a ogni risposta)")
    return troppo


def controlla():
    manca = []
    cm = os.path.join(CONFIG, "CLAUDE.md")
    testo = open(cm, encoding="utf-8").read() if os.path.exists(cm) else ""
    # il setup del manutentore (claude-rules + memoria nel suo repo, decisione 28/10) vale come quello standard,
    # come in `pleyades-cli controlla`: si chiede solo che ci siano regole, una memoria sola e una barra di stato
    eccezione = "@~/claude-rules/" in testo and not os.path.isdir(os.path.join(REPO, ".git"))
    linea = leggi_json(os.path.join(CONFIG, "settings.json")).get("statusLine", {})
    memorie = glob.glob(os.path.join(CONFIG, "projects", "*", "memory"))
    if eccezione:
        print("setup del manutentore (claude-rules): controllo l'equivalente")
        if not linea.get("command"):
            manca.append("barra di stato")
        mete = {os.path.realpath(p) for p in memorie}
        if len(mete) > 1:
            manca += [f"memoria non unita: {p}" for p in memorie if os.path.realpath(p) != os.path.realpath(memorie[0])]
    else:
        if not os.path.isdir(os.path.join(REPO, ".git")):
            manca.append("repo ~/claude-personale")
        if IMPORT not in testo:
            manca.append(f"{IMPORT} in {cm}")
        if "personale.py" not in json.dumps(linea):
            manca.append("barra di stato della crew")
        manca += [f"memoria non unita: {p}" for p in memorie if not collegata(p)]
    manca += fuori_limite()
    manca += misura(stampa=False)
    print("\n".join("- " + m for m in manca) or "tutto a posto")
    return 1 if manca else 0


def hook_input():
    try:
        return json.load(sys.stdin)
    except ValueError:
        return {}


def inizio():
    dati = hook_input()
    if not os.path.isdir(os.path.join(REPO, ".git")):
        return 0
    righe = []
    r = git("pull", "-q", "--ff-only", timeout=15)
    if r.returncode and "Could not resolve" not in r.stderr and "unable to access" not in r.stderr:
        righe.append("claude-personale: pull non riuscito (modifiche da unire a mano): sistemalo prima di altro.")
    righe += collega_tutte(dati.get("cwd"))
    try:
        mappa(stampa=False)  # la commit la fa `fine`, col resto
    except OSError:
        pass
    righe += [f"claude-personale: {x}: proponi di spostare i dettagli in un file per tema (organizza-claude)."
              for x in fuori_limite()]
    if righe:
        print("\n".join(righe))
    return 0


def fine():
    hook_input()
    if not os.path.isdir(os.path.join(REPO, ".git")):
        return 0
    if git("status", "--porcelain").stdout.strip():
        git("add", "-A")
        git("commit", "-q", "-m", "aggiornamento automatico")
    if git("rev-list", "--count", "@{u}..HEAD").stdout.strip() not in ("", "0"):
        git("push", "-q", timeout=30)
    return 0


CARTELLE_PROGETTI = ("code", "Progetti", "progetti", "Developer", os.path.join(".crew", "studio"))  # dove cercarli
CLAUDE_MD_MAX = 12000  # byte di un CLAUDE.md di progetto oltre i quali va diviso (organizza-claude)


def computer():
    """Il nome di questo computer nella mappa: sistema + 4 cifre (il nome vero può contenere quello di una persona)."""
    h = hashlib.sha1(socket.gethostname().lower().encode()).hexdigest()[:4]
    return f"{platform.system().replace('Darwin', 'Mac').lower()}-{h}"


def corto(p):
    return "~" + p[len(HOME):] if p.startswith(HOME) else p


def byte(p):
    return os.path.getsize(p) if os.path.isfile(p) else 0


def progetti():
    """Le cartelle che sono progetti per Claude (CLAUDE.md o .claude/) nelle cartelle dei progetti, un livello sotto."""
    out = []
    for base in CARTELLE_PROGETTI:
        for d in sorted(glob.glob(os.path.join(HOME, base, "*"))):
            if os.path.isdir(d) and (os.path.isfile(os.path.join(d, "CLAUDE.md")) or os.path.isdir(os.path.join(d, ".claude"))):
                out.append(d)
    return out


def mappa(stampa=True):
    """mappa-<computer>.md nel repo personale: dove sta ogni cosa che Claude usa su questo PC e cosa non segue la
    struttura comune (organizza-claude). Solo nomi, percorsi e byte: mai il contenuto dei file."""
    s = [f"# Mappa di {computer()} ({platform.system()} {platform.release()})", "",
         "Generata da `personale.py mappa` a ogni avvio di Claude Code: non modificarla a mano. Percorsi con ~ = la "
         "cartella di casa.", ""]
    scarti = []
    cm = os.path.join(CONFIG, "CLAUDE.md")
    t = open(cm, encoding="utf-8").read() if os.path.isfile(cm) else ""
    s += ["## Personale (sempre caricato)", "| File | Byte |", "|---|---|", f"| {corto(cm)} | {byte(cm)} |"]
    for imp in re.findall(r"^@(\S+)", t, re.M):
        s.append(f"| {imp} (import) | {byte(os.path.expanduser(imp))} |")
    s.append(f"| {corto(MEMORIA)}/ | {len(glob.glob(os.path.join(MEMORIA, '*.md')))} memorie |")
    if [r for r in t.splitlines() if r.strip() and not r.startswith(("@", "#", "<!--"))]:
        scarti.append(f"{corto(cm)} ha regole scritte dentro: spostale in regole.md (solo import lì)")
    if IMPORT not in t:
        scarti.append(f"{corto(cm)} non importa {IMPORT}")
    skill = sorted(glob.glob(os.path.join(CONFIG, "skills", "*", "SKILL.md")))
    comandi = sorted(glob.glob(os.path.join(CONFIG, "commands", "*.md")))
    s += ["", "## Skill e comandi solo miei", "| Cosa | Byte |", "|---|---|"]
    s += [f"| skill `{os.path.basename(os.path.dirname(f))}` | {byte(f)} |" for f in skill]
    s += [f"| comando `/{os.path.basename(f)[:-3]}` | {byte(f)} |" for f in comandi] or ["| (nessuno) | |"]
    scarti += [f"skill {os.path.basename(os.path.dirname(f))}: SKILL.md {byte(f)} byte > 6000 (fanne un indice)"
               for f in skill if byte(f) > 6000]
    attivi = sorted(k for k, v in leggi_json(os.path.join(CONFIG, "settings.json")).get("enabledPlugins", {}).items() if v)
    s += ["", "## Plugin accesi ovunque", ", ".join(f"`{k}`" for k in attivi) or "(nessuno)"]
    s += ["", "## Progetti", "| Cartella | CLAUDE.md byte | Skill del progetto | Plugin accesi nel progetto |",
          "|---|---|---|---|"]
    for d in progetti():
        cmd = os.path.join(d, "CLAUDE.md")
        sk = len(glob.glob(os.path.join(d, ".claude", "skills", "*", "SKILL.md")))
        pl = [k for k, v in leggi_json(os.path.join(d, ".claude", "settings.json")).get("enabledPlugins", {}).items() if v]
        s.append(f"| {corto(d)} | {byte(cmd)} | {sk} | {', '.join(pl) or '—'} |")
        if byte(cmd) > CLAUDE_MD_MAX:
            scarti.append(f"{corto(cmd)}: {byte(cmd)} byte > {CLAUDE_MD_MAX}: indice corto + file per tema")
    condivise = sorted(set(glob.glob(os.path.join(HOME, "Library", "CloudStorage", "*", "Agenzia*")) +
                           glob.glob(os.path.join(HOME, "Nextcloud*", "Agenzia*"))))
    s += ["", "## Cartelle condivise (app Nextcloud)"] + [f"- {corto(c)}" for c in condivise] + (["- (nessuna)"] if not condivise else [])
    if not os.path.isdir(os.path.join(HOME, "code")):
        scarti.append("niente ~/code: i progetti stanno in ~/code/<nome> (struttura comune)")
    s += ["", "## Scarti dalla struttura comune (skill organizza-claude)"] + ([f"- {x}" for x in scarti] or ["- nessuno ✓"])
    testo = "\n".join(s) + "\n"
    if os.path.isdir(REPO):
        p = os.path.join(REPO, f"mappa-{computer()}.md")
        if (open(p, encoding="utf-8").read() if os.path.isfile(p) else "") != testo:
            with open(p, "w", encoding="utf-8") as f:
                f.write(testo)
    if stampa:
        print(testo)
    return 0


def quando(ts):
    t = time.localtime(ts)
    return time.strftime("%H:%M", t) if ts - time.time() < 86400 else GIORNI[t.tm_wday]


def finestre(rl, ora):
    out = []
    for chiave, nome in (("five_hour", "5h"), ("seven_day", "7g")):
        w = (rl or {}).get(chiave) or {}
        pct, reset = w.get("used_percentage"), w.get("resets_at") or 0
        if pct is not None and (not reset or reset > ora):
            out.append((nome, float(pct), reset))
    return out


def statusline():
    dati = hook_input()
    parti = [((dati.get("model") or {}).get("display_name") or "")]
    ctx = (dati.get("context_window") or {}).get("used_percentage")
    if ctx is not None:
        parti.append(f"contesto {ctx:.0f}%")
    rl = dati.get("rate_limits")
    if rl:
        try:
            scrivi_json(CACHE, {"ts": int(time.time()), "rate_limits": rl})
        except OSError:
            pass
    parti += [f"{n} {p:.0f}%" + (f" ↻{quando(r)}" if r else "") for n, p, r in finestre(rl, time.time())]
    ms = (dati.get("cost") or {}).get("total_duration_ms")
    if ms:
        m = int(ms // 60000)
        parti.append(f"{m // 60}h{m % 60:02d}" if m >= 60 else f"{m} min")
    print(" · ".join(p for p in parti if p))
    return 0


def suggerisci(prompt):
    """Plugin non installato che fa al caso della richiesta (parole `keywords` dei marketplace installati): una riga a
    Claude, una volta a settimana per plugin. Niente output se non c'è (0 token)."""
    testo = " " + re.sub(r"[^\w+-]+", " ", (prompt or "").lower()) + " "
    if len(testo) < 4:
        return
    inst = set((leggi_json(os.path.join(CONFIG, "plugins", "installed_plugins.json")) or {}).get("plugins", {}))
    stato, ora, righe = leggi_json(SUGGERITI) or {}, time.time(), []
    for mk in glob.glob(os.path.join(CONFIG, "plugins", "marketplaces", "*", ".claude-plugin", "marketplace.json")):
        nome_mk = os.path.basename(os.path.dirname(os.path.dirname(mk)))
        for p in (leggi_json(mk) or {}).get("plugins", []):
            pid = f"{p.get('name')}@{nome_mk}"
            if pid in inst or ora - stato.get(pid, 0) < 7 * 86400:
                continue
            if any(f" {k.lower()} " in testo for k in p.get("keywords", [])):
                righe.append(f"`{pid}` ({p.get('description', '')[:90]})")
                stato[pid] = ora
    if righe:
        scrivi_json(SUGGERITI, stato)
        print("Per questa richiesta c'è un plugin non installato: " + "; ".join(righe[:2]) + ". Proponilo all'utente in "
              "una riga (`claude plugin install <nome>`, vale dalla prossima sessione o con /reload-plugins); se non "
              "serve davvero al lavoro, non dirlo.")


def pratiche(prompt):
    """Una riga a Claude quando il messaggio mostra una cattiva pratica certa, una volta per tema ogni N giorni
    (buone-pratiche.md). Il testo del messaggio non viene mai ripetuto. Niente output se è tutto ok (0 token)."""
    p = prompt or ""
    temi = []
    if RE_SEGRETO.search(p):
        temi.append("segreto")
    if len(RE_LOG.findall(p)) >= 15:
        temi.append("log")
    elif len(p) > 3000:
        temi.append("lungo")
    if RE_SALTA.search(p):
        temi.append("salta")
    stato, ora = leggi_json(PRATICHE) or {}, time.time()
    temi = [t for t in temi if ora - stato.get(t, 0) >= CONSIGLI[t][0] * 86400]
    if not temi:
        return
    for t in temi:
        stato[t] = ora
    try:
        scrivi_json(PRATICHE, stato)
    except OSError:
        pass  # senza memoria dell'avviso si ripete: meglio che un hook rotto
    print("💡 buone pratiche (regole-crew → Insegnare): " + "; ".join(CONSIGLI[t][1] for t in temi) +
          ". Dillo all'utente in UNA riga «💡 Meglio: …», gentile, poi rispondi alla richiesta.")


def avviso():
    dati = hook_input()
    pratiche(dati.get("prompt"))
    suggerisci(dati.get("prompt"))
    c = leggi_json(CACHE)
    ora = time.time()
    if not c or ora - c.get("ts", 0) > 6 * 3600:
        return 0
    w = finestre(c.get("rate_limits"), ora)
    livello = next((i for i, (soglia, _) in enumerate(LIVELLI) if any(p >= soglia for _, p, _ in w)), None)
    stato, f = leggi_json(AVVISO) or {}, AVVISO
    if livello is None:
        if stato:
            os.remove(f)
        return 0
    # once per level change (and the top level again every 30 min): a line on every prompt would cost tokens
    if stato.get("livello") == livello and (livello != 0 or ora - stato.get("ts", 0) < 1800):
        return 0
    scrivi_json(f, {"livello": livello, "ts": ora})
    soglia, cosa = LIVELLI[livello]
    print(f"uso {', '.join(f'{n} {p:.0f}% (reset {quando(r)})' for n, p, r in w if p >= soglia)}: {cosa}")
    return 0


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--se-manca-python3" in sys.argv and run(["python3", "-c", "pass"], timeout=10).returncode == 0:
        sys.exit(0)  # seconda voce degli hook, per Windows dove c'è solo `python`
    comandi = {"setup": setup, "controlla": controlla, "misura": lambda: (misura(), 0)[1], "inizio": inizio, "fine": fine,
               "statusline": statusline, "avviso": avviso, "mappa": mappa}
    if not args or args[0] not in comandi:
        print(__doc__)
        sys.exit(2)
    sys.exit(comandi[args[0]]())
