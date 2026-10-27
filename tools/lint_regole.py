#!/usr/bin/env python3
"""Controllo comune di regole e skill (crew, repo personali, repo di progetto): stesso formato ovunque, poche parole.

  python3 lint_regole.py [cartella]           controlla e fallisce solo sui problemi NUOVI (exit 1)
  python3 lint_regole.py [cartella] --baseline  riscrive lint-regole-baseline.txt con i problemi di oggi

Cosa controlla (README della crew → Formato):
- SKILL.md: frontmatter con `name` uguale alla cartella e `description` di 80-1024 caratteri che dice quando usarla
  ("Usala…" o "Use when…"); un titolo `# …` nel corpo.
- Righe sotto un titolo "Insidie"/"Trappole": `sintomo → causa → cosa fare` (almeno una freccia).
- Ogni .md di regole o skill: righe ≤ 120 caratteri (fuori dai blocchi di codice e dalle tabelle), niente spazi in
  fondo, a capo finale.
I problemi già presenti stanno in `lint-regole-baseline.txt` nella cartella controllata: possono solo calare.
Solo libreria standard.
"""
import os, re, sys

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
            if not 80 <= len(desc) <= 1024:
                out.append(f"description di {len(desc)} caratteri (80-1024)")
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


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = os.path.abspath(args[0] if args else ".")
    base_path = os.path.join(root, "lint-regole-baseline.txt")
    trovati = sorted(p for f in da_controllare(root) for p in problemi(f, os.path.relpath(f, root)))
    # i numeri di riga cambiano a ogni modifica: la baseline confronta il problema senza la riga
    chiave = lambda p: re.sub(r": riga \d+:", ":", p)
    if "--baseline" in sys.argv:
        open(base_path, "w", encoding="utf-8").write(
            "# Problemi già presenti (lint_regole.py --baseline): possono solo calare.\n"
            + "".join(chiave(p) + "\n" for p in trovati))
        print(f"baseline: {len(trovati)} problemi")
        return 0
    noti = []
    if os.path.exists(base_path):
        noti = [r.rstrip("\n") for r in open(base_path, encoding="utf-8") if r.strip() and not r.startswith("#")]
    nuovi = []
    for p in trovati:
        k = chiave(p)
        if k in noti:
            noti.remove(k)
        else:
            nuovi.append(p)
    for p in nuovi:
        print(p)
    if nuovi:
        print(f"lint_regole: {len(nuovi)} problemi nuovi (formato: README della crew → Formato)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
