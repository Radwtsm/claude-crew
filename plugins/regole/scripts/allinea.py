#!/usr/bin/env python3
"""Hook SessionStart: prima di lavorare, tutti gli strumenti di Pleyades all'ultima versione su ogni computer.

  allinea.py          lancia `pleyades-cli auto` staccato (aggiorna comando, marketplace e plugin, poi `controlla --talk`
                      se il riassunto è cambiato: `pleyades-cli squadra` vede tutti allineati senza chiederlo); una CLI
                      troppo vecchia per `auto` prima si aggiorna da sola; dice a Claude in una riga se l'ultimo
                      allineamento ha trovato qualcosa da sistemare o se qualcuno della squadra è indietro
  allinea.py --turno  (UserPromptSubmit) a sessione aperta: se intanto `auto` (anche dall'attività pianificata) ha
                      installato plugin nuovi, lo dice a Claude una volta: questa sessione usa ancora i vecchi

Senza pleyades-cli non fa niente. Mac, Linux e Windows (python o python3); solo libreria standard.
"""
import json, os, shutil, subprocess, sys

CASA = os.path.expanduser("~")
STATO = os.path.join(CASA, ".config", "crew", "stato.json")
LOG = os.path.join(CASA, ".crew", "auto.log")
CREW = os.path.join(CASA, ".crew", "crew.py")
INSTALLATI = os.path.join(CASA, ".claude", "plugins", "installed_plugins.json")
SESSIONI = os.path.join(CASA, ".crew", "sessioni.json")  # i plugin con cui è partita ogni sessione aperta


def leggi(p, base):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return base


def versioni_plugin():
    return {p: (i[0].get("gitCommitSha") or i[0].get("version") or "")[:7]
            for p, i in leggi(INSTALLATI, {}).get("plugins", {}).items() if i}


def sessione():
    """L'id della sessione dall'input dell'hook (JSON su stdin)."""
    try:
        return "" if sys.stdin is None or sys.stdin.isatty() else json.load(sys.stdin).get("session_id", "")
    except (OSError, ValueError, AttributeError):
        return ""


def turno():
    sid = sessione()
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
