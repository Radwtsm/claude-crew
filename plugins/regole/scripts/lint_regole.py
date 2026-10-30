#!/usr/bin/env python3
"""Controllo comune di regole e skill (crew, repo personali, repo di progetto): stesso formato ovunque, poche parole.

  python3 lint_regole.py [cartella]           controlla e fallisce solo sui problemi NUOVI (exit 1)
  python3 lint_regole.py [cartella] --baseline  riscrive lint-regole-baseline.txt con i problemi di oggi
  python3 lint_regole.py [cartella] --limiti=FILE  limiti di byte da FILE (di base limiti-contesto.txt, se c'è)
  python3 lint_regole.py --hook                 hook PostToolUse: controlla il file appena scritto (JSON su stdin);
                                                un .md fuori da ogni casa (repo, cloud, ~/.claude) → avviso a Claude

Cosa controlla (README di Pleyades tools → Formato):
- SKILL.md: frontmatter con `name` uguale alla cartella e `description` di 80-300 caratteri che dice quando usarla (si paga a ogni risposta: corta)
  ("Usala…" o "Use when…"); un titolo `# …` nel corpo.
- Righe sotto un titolo "Insidie"/"Trappole": `sintomo → causa → cosa fare` (almeno una freccia).
- Ogni .md di regole o skill: righe ≤ 120 caratteri (fuori dai blocchi di codice e dalle tabelle), niente spazi in
  fondo, a capo finale.
- Contesto snello: i file elencati nei limiti (`byte glob…` per riga, `#` commento) non superano i loro byte,
  contati senza CR (un checkout Windows pesa come su Mac). Questi non vanno in baseline: si sistemano subito.
I problemi già presenti stanno in `lint-regole-baseline.txt` nella cartella controllata: possono solo calare.
Solo libreria standard.
"""
import fnmatch, glob, json, os, re, subprocess, sys

MAX_RIGA = 120
FILE = ("SKILL.md", "CLAUDE.md", "AGENTS.md")
SALTA = {".git", "node_modules", "dist", "__pycache__", ".claude"}


def da_controllare(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SALTA]
        for f in files:
            if f in FILE or (f.endswith(".md") and os.sep + "skills" + os.sep in d + os.sep):
                yield os.path.join(d, f)


def frontmatter(testo):
    m = re.match(r"---\n(.*?)\n---\n", testo, re.S)
    if not m:
        return None, testo
    campi = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
    return campi, testo[m.end():]


def problemi(path, rel):
    testo = open(path, encoding="utf-8").read()
    out = []
    if path.endswith("SKILL.md"):
        campi, corpo = frontmatter(testo)
        if campi is None:
            out.append("manca il frontmatter (--- name/description ---)")
        else:
            cartella = os.path.basename(os.path.dirname(path))
            if campi.get("name") != cartella:
                out.append(f"name '{campi.get('name')}' diverso dalla cartella '{cartella}'")
            desc = campi.get("description", "")
            if not 80 <= len(desc) <= 300:  # 2026-10-28: was 1024; every description is in context at every turn
                out.append(f"description di {len(desc)} caratteri (80-300)")
            if not re.search(r"\b(Usala|Usalo|Use (it )?when|Use this)\b", desc):
                out.append("description senza 'Usala quando/prima di…'")
            if not re.search(r"^# ", corpo, re.M):
                out.append("manca il titolo '# …'")
    in_codice, in_insidie = False, False
    fm = re.match(r"---\n.*?\n---\n", testo, re.S)
    salta_fino = fm.group(0).count("\n") if fm else 0  # il frontmatter ha la description su una riga sola
    voce = None  # (riga d'inizio, testo) dell'insidia in corso: una voce può andare a capo su più righe

    def chiudi():
        if voce and "→" not in voce[1] and "->" not in voce[1]:
            out.append(f"riga {voce[0]}: insidia senza 'sintomo → causa → cosa fare'")

    for n, riga in enumerate(testo.split("\n"), 1):
        if n <= salta_fino:
            continue
        if riga.startswith("```"):
            in_codice = not in_codice
            continue
        if in_codice:
            continue
        if riga.startswith("#"):
            chiudi()
            voce = None
            in_insidie = bool(re.search(r"(?i)insidie|trappole|pitfalls|gotchas", riga))
            continue
        if riga != riga.rstrip():
            out.append(f"riga {n}: spazi in fondo")
        if len(riga) > MAX_RIGA and not riga.lstrip().startswith("|") and "http" not in riga:
            out.append(f"riga {n}: {len(riga)} caratteri (> {MAX_RIGA})")
        if in_insidie and riga.startswith("- "):
            chiudi()
            voce = (n, riga)
        elif voce and riga.startswith("  ") and riga.strip():
            voce = (voce[0], voce[1] + " " + riga.strip())
        else:
            chiudi()
            voce = None
    chiudi()
    if testo and not testo.endswith("\n"):
        out.append("manca l'a capo finale")
    return [f"{rel}: {p}" for p in out]


def chiave(p):
    """i numeri di riga cambiano a ogni modifica: la baseline confronta il problema senza la riga"""
    return re.sub(r": riga \d+:", ":", p)


def nuovi(root, trovati):
    base_path = os.path.join(root, "lint-regole-baseline.txt")
    noti = []
    if os.path.exists(base_path):
        noti = [r.rstrip("\n") for r in open(base_path, encoding="utf-8") if r.strip() and not r.startswith("#")]
    out = []
    for p in trovati:
        if chiave(p) in noti:
            noti.remove(chiave(p))
        else:
            out.append(p)
    return out


def troppo_lungo(root, rel, path):
    """limiti-contesto.txt alla radice del repo (byte massimi per glob), se c'è"""
    lim = os.path.join(root, "limiti-contesto.txt")
    if not os.path.exists(lim):
        return []
    for r in open(lim, encoding="utf-8"):
        parti = r.split()
        if len(parti) >= 2 and parti[0].isdigit() and any(fnmatch.fnmatch(rel, g) for g in parti[1:]):
            n = os.path.getsize(path)
            if n > int(parti[0]):
                return [f"{rel}: {n} byte > {parti[0]} (dettagli in un file per tema letto quando serve)"]
    return []


def sparso(path):
    """True se il file non sta in un repo git né in una delle case note (cloud sincronizzati, ~/.claude, temporanei)."""
    import tempfile
    d = os.path.dirname(path)
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, ".git")):
            return False
        d = os.path.dirname(d)
    home = os.path.expanduser("~")
    case = [os.path.join(home, x) for x in (".claude", "Nextcloud", os.path.join("Library", "CloudStorage"),
                                            os.path.join("Library", "Mobile Documents"))]
    case += [tempfile.gettempdir(), "/tmp", "/private/tmp", "/private/var/folders", "/var/folders"]
    reale = os.path.realpath(path)
    return not any(reale.startswith(os.path.realpath(c) + os.sep) or path.startswith(c + os.sep) for c in case)


def hook():
    """PostToolUse (Edit/Write) del plugin regole: controlla subito il file appena scritto, se è una regola o una
    skill. Silenzioso se è a posto; exit 2 = Claude vede i problemi e li corregge prima di andare avanti."""
    if "--se-manca-python3" in sys.argv:  # seconda voce dell'hook, per Windows dove c'è solo `python`
        try:
            if subprocess.run(["python3", "-c", "pass"], capture_output=True, timeout=10).returncode == 0:
                return 0
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        path = json.load(sys.stdin).get("tool_input", {}).get("file_path") or ""
    except ValueError:
        return 0
    path = os.path.abspath(path)
    nome, cartella = os.path.basename(path), os.path.dirname(path)
    if nome.endswith(".md") and os.path.isfile(path) and sparso(path):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
              f"{path} è un .md fuori da ogni casa (repo, studio Nextcloud, memoria): dillo all'utente in una riga "
              "(dove sta e perché) e proponi la casa giusta, o spostalo (crew: una casa per ogni cosa)."}}))
        return 0
    if not os.path.isfile(path) or not (nome in FILE or (nome.endswith(".md") and os.sep + "skills" + os.sep in cartella + os.sep)):
        return 0
    root = cartella
    while not os.path.exists(os.path.join(root, ".git")) and os.path.dirname(root) != root:
        root = os.path.dirname(root)
    if not os.path.exists(os.path.join(root, ".git")):
        root = cartella
    rel = os.path.relpath(path, root)
    trovati = nuovi(root, problemi(path, rel)) + troppo_lungo(root, rel, path)
    if not trovati:
        return 0
    print("\n".join(trovati) + "\nlint_regole (plugin regole): sistemali ora, formato nel README di Pleyades tools → Formato",
          file=sys.stderr)
    return 2


def troppo_lunghi(root, limiti):
    """Le righe `file: N byte > MAX` dei file oltre il loro limite."""
    fuori = []
    for riga in open(limiti, encoding="utf-8"):
        parti = riga.split()
        if not parti or parti[0].startswith("#"):
            continue
        for modello in parti[1:]:
            for f in sorted(glob.glob(os.path.join(root, modello))):
                n = len(open(f, "rb").read().replace(b"\r", b""))
                if n > int(parti[0]):
                    fuori.append(f"{os.path.relpath(f, root)}: {n} byte > {parti[0]}")
    return fuori


def main():
    if "--hook" in sys.argv:
        return hook()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = os.path.abspath(args[0] if args else ".")
    trovati = sorted(p for f in da_controllare(root) for p in problemi(f, os.path.relpath(f, root)))
    if "--baseline" in sys.argv:
        open(os.path.join(root, "lint-regole-baseline.txt"), "w", encoding="utf-8").write(
            "# Problemi già presenti (lint_regole.py --baseline): possono solo calare.\n"
            + "".join(chiave(p) + "\n" for p in trovati))
        print(f"baseline: {len(trovati)} problemi")
        return 0
    da_sistemare = nuovi(root, trovati)
    for p in da_sistemare:
        print(p)
    limiti = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--limiti=")), "limiti-contesto.txt")
    limiti = os.path.join(root, limiti)
    lunghi = troppo_lunghi(root, limiti) if os.path.isfile(limiti) else []
    for p in lunghi:
        print(p)
    if da_sistemare:
        print(f"lint_regole: {len(da_sistemare)} problemi nuovi (formato: README di Pleyades tools → Formato)", file=sys.stderr)
    if lunghi:
        print("lint_regole: file letti a ogni sessione troppo lunghi; i dettagli in un file per tema letto quando serve "
              "(organizza-claude)", file=sys.stderr)
    return 1 if da_sistemare or lunghi else 0


if __name__ == "__main__":
    sys.exit(main())
