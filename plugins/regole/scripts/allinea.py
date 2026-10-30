#!/usr/bin/env python3
"""Hook SessionStart: prima di lavorare, tutti gli strumenti di Pleyades all'ultima versione su ogni computer.

  allinea.py          lancia `pleyades-cli auto` staccato (aggiorna comando, marketplace e plugin, poi `controlla --talk`
                      se il riassunto è cambiato: `pleyades-cli squadra` vede tutti allineati senza chiederlo); una CLI
                      troppo vecchia per `auto` prima si aggiorna da sola; dice a Claude in una riga se l'ultimo
                      allineamento ha trovato qualcosa da sistemare o se qualcuno della squadra è indietro
  allinea.py --turno  (UserPromptSubmit) a sessione aperta: se intanto `auto` (anche dall'attività pianificata) ha
                      installato plugin nuovi, lo dice a Claude una volta: questa sessione usa ancora i vecchi;
                      e quando il contesto della sessione passa i 150k token (poi ogni 100k in più), perché Claude lo
                      rilegge tutto a ogni risposta

Senza pleyades-cli non fa niente. Mac, Linux e Windows (python o python3); solo libreria standard.
"""
import json, os, shutil, subprocess, sys

CASA = os.path.expanduser("~")
STATO = os.path.join(CASA, ".config", "crew", "stato.json")
LOG = os.path.join(CASA, ".crew", "auto.log")
CREW = os.path.join(CASA, ".crew", "crew.py")
INSTALLATI = os.path.join(CASA, ".claude", "plugins", "installed_plugins.json")
SESSIONI = os.path.join(CASA, ".crew", "sessioni.json")  # i plugin con cui è partita ogni sessione aperta
CONTESTO = os.path.join(CASA, ".crew", "contesto.json")  # l'ultima soglia di contesto già detta, per sessione
SOGLIA, PASSO = 150_000, 100_000  # come MAX_MEDIO di crew.py; poi un avviso ogni 100k in più


def leggi(p, base):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return base


def versioni_plugin():
    return {p: (i[0].get("gitCommitSha") or i[0].get("version") or "")[:7]
            for p, i in leggi(INSTALLATI, {}).get("plugins", {}).items() if i}


def ingresso():
    """L'input dell'hook (JSON su stdin), {} se non c'è."""
    try:
        return {} if sys.stdin is None or sys.stdin.isatty() else json.load(sys.stdin)
    except (OSError, ValueError, AttributeError):
        return {}


def sessione():
    """L'id della sessione dall'input dell'hook."""
    return ingresso().get("session_id", "")


def contesto(transcript):
    """I token dell'ultima risposta principale (non dei subagent) dalla coda del transcript; 0 se non si sa."""
    try:
        with open(transcript, "rb") as f:
            f.seek(max(0, os.path.getsize(transcript) - 2_000_000))
            righe = f.read().decode("utf-8", "replace").splitlines()
    except (OSError, TypeError):
        return 0
    for r in reversed(righe):
        if '"usage"' not in r or '"assistant"' not in r:
            continue
        try:
            x = json.loads(r)
        except ValueError:
            continue
        if x.get("type") == "assistant" and not x.get("isSidechain"):
            u = (x.get("message") or {}).get("usage") or {}
            return sum(u.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return 0


def avviso_contesto(sid, transcript):
    n = contesto(transcript)
    if not sid or n < SOGLIA:
        return
    livello = SOGLIA + (n - SOGLIA) // PASSO * PASSO
    detti = leggi(CONTESTO, {})
    if detti.get(sid, 0) >= livello:
        return
    print(f"Pleyades: questa sessione ha {n // 1000}k token di contesto e Claude li rilegge tutti a ogni risposta. "
          "Dillo all'utente in una riga: finito il passo in corso, salva lo stato e fai /clear con un prompt pronto "
          "per ripartire (un argomento per sessione).")
    detti = dict(list({k: v for k, v in detti.items() if k != sid}.items())[-19:])
    detti[sid] = livello
    scrivi(CONTESTO, detti)


def turno():
    dati = ingresso()
    sid = dati.get("session_id", "")
    avviso_contesto(sid, dati.get("transcript_path"))
    sess = leggi(SESSIONI, {})
    prima = sess.get(sid)
    if not sid or not prima or prima.get("detto"):
        return
    ora = versioni_plugin()
    nuovi = sorted(p for p, v in ora.items() if prima["plugin"].get(p) not in (None, v))
    if nuovi:
        print(f"Pleyades: mentre lavoravi sono arrivate versioni nuove di {', '.join(nuovi)}; questa sessione usa "
              "ancora le vecchie. Dillo all'utente in una riga: a fine lavoro chiudi e riapri Claude.")
        prima["detto"] = True
        scrivi(SESSIONI, sess)


def scrivi(p, dati):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dati, f)


def figlio(cli):
    """Staccato dall'avvio: una pleyades-cli troppo vecchia per `auto` prima si aggiorna da sola."""
    try:
        vecchia = "\ndef auto(" not in open(CREW, encoding="utf-8").read()
    except OSError:
        vecchia = True
    if vecchia:
        subprocess.run([cli, "aggiorna"], stdin=subprocess.DEVNULL, timeout=600)
    subprocess.run([cli, "auto"], stdin=subprocess.DEVNULL, timeout=900)


def main():
    if sys.argv[1:2] == ["--figlio"]:
        return figlio(sys.argv[2])
    if "--se-manca-python3" in sys.argv and shutil.which("python3") and \
            subprocess.run(["python3", "-c", "pass"], capture_output=True, timeout=10).returncode == 0:
        return  # seconda voce degli hook, per Windows dove c'è solo `python`
    if "--turno" in sys.argv:
        return turno()
    cli = shutil.which("pleyades-cli") or shutil.which("pleyades-cli", path=os.path.join(CASA, ".local", "bin"))
    if not cli:
        return
    try:
        with open(STATO, encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, ValueError):
        st = {}
    esito, sq = st.get("auto", {}).get("esito", ""), st.get("squadra", {})
    if esito.startswith("da sistemare"):
        print(f"pleyades-cli: l'ultimo allineamento automatico ha {esito}: dillo all'utente in una riga e "
              "sistemalo con la skill `ripara-allineamento` (parte da `pleyades-cli diagnosi`).")
    fuori = sq.get("indietro", []) + [f"{n} (mai controllato)" for n in sq.get("senza", [])]
    if fuori:  # allineamento costante del team = priorità assoluta (owner 2026-10-28)
        print(f"Squadra non allineata: {', '.join(fuori)}. Priorità assoluta: dillo all'utente prima del resto. "
              "Ogni computer acceso si allinea da solo entro ~5 minuti da un push; se resta "
              "indietro, skill `ripara-allineamento`.")
    sid = sessione()
    if sid:
        sess = {k: v for k, v in leggi(SESSIONI, {}).items() if k != sid}
        sess = dict(list(sess.items())[-19:])  # le ultime 20 sessioni bastano
        sess[sid] = {"plugin": versioni_plugin()}
        scrivi(SESSIONI, sess)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    # staccato: l'avvio di Claude non aspetta (Windows: DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
    extra: dict = {"creationflags": 0x00000008 | 0x00000200} if os.name == "nt" else {"start_new_session": True}
    with open(LOG, "w", encoding="utf-8") as log:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--figlio", cli], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                         cwd=CASA, env={**os.environ, "NO_COLOR": "1"}, **extra)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # un hook d'avvio non deve mai fermare Claude
        pass
