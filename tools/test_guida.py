#!/usr/bin/env python3
"""La guida di un collega nuovo, provata da capo in una casa finta (owner 30/10: «devi testare da solo il processo di
onboarding + setup, ui ux compresa»). Niente tocca il computer vero: HOME in una cartella temporanea, i programmi con
effetti (claude, gh, launchctl, open, osascript, defaults, profiles, …) sostituiti da finti che scrivono cosa è stato
chiesto, rete solo verso GitHub pubblico. Controlla il percorso (ogni passo obbligatorio c'è, rilanciare salta il
fatto) e la forma (nessun errore Python, ogni ✗ dice cosa fare, nessuna riga oltre lo schermo).
Uso: python3 tools/test_guida.py [--tieni]   (--tieni: lascia la casa finta per guardarla)"""
import http.server, os, re, shutil, stat, subprocess, sys, tempfile, threading, time, urllib.parse

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREW = os.path.join(QUI, "crew.py")
# Problemi noti, ancora da sistemare: segnalati ma non bloccano; la lista può solo calare (togli la riga quando passa)
NOTI = {
    # credenziali dello studio tenute solo da talk.py del progetto: un progetto senza stanza le perde (A67)
    "guida (studio, rilancio): chiede di nuovo l'accesso allo studio (non l'ha tenuto)",
}
LOCALE = "localhost"  # lo studio finto: solo su questo computer
LARGO = 80  # il Terminale del Mac apre a 80 colonne

# claude finto: marketplace e plugin in un file della casa finta, accesso già fatto
CLAUDE = r'''#!/usr/bin/env python3
import json, os, sys
f = os.path.join(os.environ["HOME"], ".claude-finto.json")
s = json.load(open(f)) if os.path.exists(f) else {"mk": [], "plugin": []}
a = sys.argv[1:]
open(os.path.join(os.environ["HOME"], ".chiamate.log"), "a").write("claude " + " ".join(a) + "\n")
if a[:1] == ["--version"]: print("2.1.0 (Claude Code)")
elif a[:2] == ["auth", "status"]: print('{"loggedIn": true}')
elif a[:3] == ["plugin", "marketplace", "list"]: print("\n".join("  ❯ " + m for m in s["mk"]))
elif a[:3] == ["plugin", "marketplace", "add"]:
    n = a[3].rstrip("/").split("/")[-1].removesuffix(".git")
    s["mk"] += [n] if n not in s["mk"] else []
    st = os.path.join(os.environ["HOME"], ".claude", "settings.json")  # come il vero: add toglie autoUpdate
    os.makedirs(os.path.dirname(st), exist_ok=True)
    x = json.load(open(st)) if os.path.exists(st) else {}
    x.setdefault("extraKnownMarketplaces", {})[n] = {"source": {"source": "github", "repo": a[3]}}
    json.dump(x, open(st, "w"))
elif a[:2] == ["plugin", "install"]: s["plugin"] += [a[2]] if a[2] not in s["plugin"] else []
elif a[:2] == ["plugin", "list"]: print("\n".join("  ❯ " + p for p in s["plugin"]))
json.dump(s, open(f, "w"))
p = os.path.join(os.environ["HOME"], ".claude", "plugins")
os.makedirs(p, exist_ok=True)
json.dump({"plugins": {x: [{"gitCommitSha": "0000000"}] for x in s["plugin"]}}, open(os.path.join(p, "installed_plugins.json"), "w"))
json.dump({m: {"installLocation": "", "autoUpdate": True} for m in s["mk"]}, open(os.path.join(p, "known_marketplaces.json"), "w"))
'''
# ogni altro programma con effetti: scrive cosa gli è stato chiesto e risponde «non c'è / non fatto»
FINTO = '''#!/bin/sh
echo "$(basename "$0") $*" >> "$HOME/.chiamate.log"
case "$(basename "$0") $1" in "xcode-select -p") echo /Library/Developer/CommandLineTools; exit 0;; esac
[ "$(basename "$0")" = open ] && exit 0  # «aperto»: webbrowser non ripiega sul browser vero
exit 1
'''
FINTI = ["gh", "launchctl", "open", "osascript", "defaults", "profiles", "security", "codesign", "spctl", "hdiutil",
         "ditto", "pkgutil", "crontab", "schtasks", "powershell", "winget", "brew", "xcode-select", "curl", "sudo"]


# Lo studio Nextcloud finto: Login Flow v2 che concede subito, WebDAV con un progetto condiviso («Progetto Prova»)
FILE_STUDIO = {"Progetto Prova/.claude/progetto.json": b'{"nome": "Progetto Prova", "tipo": "progetto"}',
               "Progetto Prova/LEGGIMI.md": b"# Progetto Prova\n"}


class Studio(http.server.BaseHTTPRequestHandler):
    accessi = 0

    def log_message(self, *a):
        pass

    def manda(self, codice, corpo, tipo="application/json"):
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        base = f"http://{LOCALE}:{self.server.server_address[1]}"
        if self.path == "/index.php/login/v2":
            Studio.accessi += 1
            return self.manda(200, f'{{"login": "{base}/accedi", "poll": {{"token": "t", "endpoint": "{base}/poll"}}}}'.encode())
        if self.path == "/poll":
            return self.manda(200, f'{{"server": "{base}", "loginName": "nuovo", "appPassword": "finta"}}'.encode())
        self.manda(404, b"")

    def do_PROPFIND(self):
        base = "/remote.php/dav/files/nuovo/"
        rel = urllib.parse.unquote(self.path)[len(base):].strip("/")
        figli = sorted({k[len(rel) + 1 if rel else 0:].split("/")[0] for k in FILE_STUDIO if k.startswith(rel)})
        voci = [(rel, True)] + [((rel + "/" if rel else "") + f, not any(k == (rel + "/" if rel else "") + f
                                  for k in FILE_STUDIO)) for f in figli if f]
        xml = "".join(f"<d:response><d:href>{urllib.parse.quote(base + v)}</d:href><d:propstat><d:prop><d:resourcetype>"
                      f"{'<d:collection/>' if c else ''}</d:resourcetype></d:prop></d:propstat></d:response>" for v, c in voci)
        self.manda(207, f'<?xml version="1.0"?><d:multistatus xmlns:d="DAV:">{xml}</d:multistatus>'.encode(), "application/xml")

    def do_GET(self):
        rel = urllib.parse.unquote(self.path)[len("/remote.php/dav/files/nuovo/"):]
        self.manda(200, FILE_STUDIO[rel], "application/octet-stream") if rel in FILE_STUDIO else self.manda(404, b"")


def prepara(casa):
    finti = os.path.join(casa, ".finti")
    os.makedirs(finti)
    for nome, testo in [("claude", CLAUDE)] + [(n, FINTO) for n in FINTI]:
        p = os.path.join(finti, nome)
        with open(p, "w") as f:
            f.write(testo.replace("#!/usr/bin/env python3", "#!" + sys.executable))
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    # le cartelle che path_aggiornato mette davanti stanno già dopo i finti: i finti vincono sempre
    vere = [os.path.dirname(shutil.which("git") or "/usr/bin/git"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"]
    return {"HOME": casa, "USERPROFILE": casa, "PATH": os.pathsep.join([finti, os.path.join(casa, ".local", "bin")] + vere),
            "COLUMNS": str(LARGO), "LINES": "40", "NO_COLOR": "1", "TERM": "dumb", "LANG": "it_IT.UTF-8",
            "BROWSER": os.path.join(finti, "open"), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0", "PYTHONDONTWRITEBYTECODE": "1"}


def guida(env, risposte, *a):
    t = time.time()
    try:
        r = subprocess.run([sys.executable, CREW, *a], input=risposte, env=env, cwd=env["HOME"], text=True,
                           capture_output=True, timeout=180)
    except subprocess.TimeoutExpired as e:  # una guida che aspetta per sempre è un errore di UX, non un test lento
        out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return -1, out + "\n⏳ FERMA AD ASPETTARE (3 minuti senza finire)", time.time() - t
    return r.returncode, r.stdout + r.stderr, time.time() - t


def forma(out, dove):
    """La UX del terminale: niente errori Python, ogni ✗ con il suo →, nessuna riga oltre lo schermo."""
    err, righe = [], out.splitlines()
    if "FERMA AD ASPETTARE" in out:
        err.append(f"{dove}: si ferma ad aspettare; ultime righe:\n" + "\n".join(out.splitlines()[-8:]))
    if "Traceback" in out:
        err.append(f"{dove}: errore Python\n" + out[out.index("Traceback"):][:800])
    for i, r in enumerate(righe):
        if re.match(r"\s*(?:[❯⎿]\s+)*✗ ", r) and not any("→" in x for x in righe[i + 1:i + 3]) and "│" not in r:
            err.append(f"{dove}: «{r.strip()}» senza cosa fare (→)")
        if len(r) > LARGO and " " in r.strip():  # un percorso lungo da solo non si può andare a capo
            err.append(f"{dove}: riga di {len(r)} caratteri (schermo {LARGO}): «{r[:70]}…»")
    return err


def esiti(out):
    return [m.group(2).split(" · ")[0].strip() for m in re.finditer(r"^\s*(?:[❯⎿]\s+)*(✓|✗) (.+)$", out, re.M)]


def main():
    tieni = "--tieni" in sys.argv
    casa = tempfile.mkdtemp(prefix="guida-")
    sys.path.insert(0, QUI)
    sys.argv = sys.argv[:1]
    import crew  # il registro dei passi, dallo stesso file provato
    err = []
    try:
        env = prepara(casa)
        # 1. collega nuovo, computer suo, senza GitHub, senza studio: 1 = «Mio», 2 = «senza account», Invio = no studio
        c, out, s1 = guida(env, "1\n2\n\n\n\n\n\n\n", "guida")
        open(os.path.join(casa, "guida-1.txt"), "w").write(out)
        err += forma(out, "guida")
        visti = {crew.passo_di(n)["id"] for n in esiti(out)}
        for p in crew.PASSI:
            if p["livello"] == "obbligatorio" and p["id"] in ("computer", "sistema", "claude", "crew") \
                    and p["id"] not in visti:
                err.append(f"guida: passo obbligatorio «{p['nome']}» mai mostrato")
        if "a posto" not in out:
            err.append("guida: manca il riepilogo finale («x/y a posto»)")
        chiamate = open(os.path.join(casa, ".chiamate.log")).read() if os.path.exists(os.path.join(casa, ".chiamate.log")) else ""
        for vietato in ("launchctl bootout", "launchctl bootstrap", "gh auth login", "profiles install"):
            if vietato in chiamate:  # nella casa di prova niente che tocchi l'utente vero o aspetti una persona
                err.append(f"guida: chiamato «{vietato}» in una casa di prova")
        if "plugin install regole@claude-crew" not in chiamate:
            err.append("guida: le regole comuni non sono state installate (claude plugin install regole@claude-crew)")
        # 2. rilanciare salta ciò che è fatto: nessuna installazione nuova
        prima = chiamate.count("plugin install")
        c2, out2, s2 = guida(env, "\n\n\n\n\n\n", "guida")
        open(os.path.join(casa, "guida-2.txt"), "w").write(out2)
        err += forma(out2, "guida (rilancio)")
        dopo = open(os.path.join(casa, ".chiamate.log")).read().count("plugin install")
        if dopo != prima:
            err.append(f"guida (rilancio): {dopo - prima} plugin reinstallati (doveva saltare il fatto)")
        # 3. i comandi di tutti i giorni nella stessa casa
        for cmd in (["controlla"], ["diagnosi"], ["passi"], ["kit"], ["link"]):
            c3, out3, _ = guida(env, "\n", *cmd)
            err += forma(out3, " ".join(cmd))
        # 5. chi non programma: progetti dallo studio Nextcloud, senza GitHub
        server = http.server.ThreadingHTTPServer((LOCALE, 0), Studio)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        indirizzo = f"http://{LOCALE}:{server.server_address[1]}"
        studio = tempfile.mkdtemp(prefix="guida-studio-")
        try:
            env5 = prepara(studio)
            c5, out5, _ = guida(env5, "1\n2\n1\n\n\n\n", "guida", f"--studio={indirizzo}")
            err += forma(out5, "guida (studio)")
            if not os.path.isfile(os.path.join(studio, ".crew", "studio", "progetto-prova", "LEGGIMI.md")):
                err.append("guida (studio): il progetto condiviso non è stato copiato in ~/.crew/studio/")
            for atteso in ("accesso allo studio", "copia di «Progetto Prova»"):
                if atteso not in out5:
                    err.append(f"guida (studio): manca «{atteso}»")
            accessi = Studio.accessi
            c6, out6, _ = guida(env5, "\n\n\n\n\n\n", "guida")
            err += forma(out6, "guida (studio, rilancio)")
            if Studio.accessi != accessi:
                err.append("guida (studio, rilancio): chiede di nuovo l'accesso allo studio (non l'ha tenuto)")
        finally:
            server.shutdown()
            shutil.rmtree(studio, ignore_errors=True)
        # 4. computer di lavoro: solo regole comuni, niente studio, progetti o attività pianificata
        lavoro = tempfile.mkdtemp(prefix="guida-lavoro-")
        try:
            c4, out4, _ = guida(prepara(lavoro), "2\n2\n2\n\n\n", "guida")
            err += forma(out4, "guida (lavoro)")
            for vietato in ("indirizzo di uno studio", "stanza Talk", "PROPRIETARIO/NOME"):
                if vietato in out4:
                    err.append(f"guida (lavoro): chiede o mostra «{vietato}» su un computer di lavoro")
            if "profilo: lavoro" not in out4:
                err.append("guida (lavoro): il profilo lavoro non è stato preso")
        finally:
            shutil.rmtree(lavoro, ignore_errors=True)
        print(f"guida: {s1:.0f} s la prima volta, {s2:.0f} s il rilancio · casa finta {casa}")
    finally:
        if not tieni:
            shutil.rmtree(casa, ignore_errors=True)
    for e in err:
        print("test_guida: " + ("⚠ noto: " if e in NOTI else "") + e, file=sys.stderr)
    for e in sorted(NOTI - set(err)):
        print(f"test_guida: «{e}» ora passa: toglilo da NOTI", file=sys.stderr)
    return 1 if set(err) - NOTI or NOTI - set(err) else 0


if __name__ == "__main__":
    sys.exit(main())
