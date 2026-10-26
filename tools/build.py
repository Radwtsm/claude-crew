#!/usr/bin/env python3
"""Costruisce in dist/ la pagina della crew: catalogo dei plugin, uno zip per skill, le regole da incollare.

Uso: python3 tools/build.py  (lo lancia la CI a ogni push su main e pubblica dist/ su GitHub Pages)
"""
import html, json, os, re, shutil, subprocess, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
REPO = "Radwtsm/claude-crew"
SOLO_CLI = {"installa-crew"}
INIZIO = "<!-- regole crew: inizio (si aggiornano dalla pagina della crew, non modificare qui) -->"
FINE = "<!-- regole crew: fine -->"
INSTALLA = f"https://raw.githubusercontent.com/{REPO}/main/INSTALLA.md"
e = html.escape


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(re.findall(r"^(\w+): (.*)$", m.group(1), re.M)) if m else {}


def sezioni(text):
    return re.findall(r"^## (.+)$", text, re.M)


def aggiornata(path):
    r = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%cd", "--date=format:%d/%m/%Y", "--", path],
                       capture_output=True, text=True)
    return r.stdout.strip() or "—"


def zip_skill(src, name):
    # l'app Claude vuole uno zip con dentro la cartella della skill
    with zipfile.ZipFile(os.path.join(DIST, f"{name}.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, _, files in os.walk(src):
            for f in sorted(files):
                full = os.path.join(dirpath, f)
                z.write(full, os.path.join(name, os.path.relpath(full, src)))


def scheda(p):
    pdir = os.path.join(ROOT, p["source"])
    nome = p["name"]
    pezzi, testi, zips = [], [], []
    for md in ("regole.md", "codice.md", "architettura.md"):
        f = os.path.join(pdir, md)
        if os.path.isfile(f):
            t = open(f, encoding="utf-8").read()
            pezzi.append(f"<li><b>Regole sempre attive</b> ({e(md)}, solo Claude Code): {e(', '.join(sezioni(t)))}</li>")
            testi.append((md, t))
    sdir = os.path.join(pdir, "skills")
    for s in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
        t = open(os.path.join(sdir, s, "SKILL.md"), encoding="utf-8").read()
        fm = frontmatter(t)
        dove = "solo Claude Code" if s in SOLO_CLI else "Claude Code e app"
        sez = f"<br><span class=\"muted\">Sezioni: {e(', '.join(sezioni(t)))}</span>" if sezioni(t) else ""
        pezzi.append(f"<li><b>Skill {e(s)}</b> ({dove}): {e(fm.get('description', ''))}{sez}</li>")
        testi.append((f"{s}/SKILL.md", t))
        if s not in SOLO_CLI:
            zip_skill(os.path.join(sdir, s), s)
            zips.append(s)
    frase = (f"Installa il plugin {nome} della crew: claude plugin install {nome}@claude-crew "
             f"(se la crew non è ancora installata, prima segui {INSTALLA})")
    bottoni = [f'<button class="btn" data-testo="{e(frase)}">Copia per Claude Code</button>']
    bottoni += [f'<a class="btn alt" href="{z}.zip" download>Scarica {e(z)} per l\'app</a>' for z in zips]
    if nome == "regole":
        bottoni.append('<a class="btn alt" href="#app">Regole per l\'app: più sotto</a>')
    corpo = "".join(f"<details><summary>Leggi {e(n)}</summary><pre>{e(t)}</pre></details>" for n, t in testi)
    return (f'<li class="card"><div class="head"><span class="tag">{e(p.get("category", ""))}</span>'
            f'<span class="muted">aggiornato {aggiornata(pdir)}</span></div>'
            f'<h3>{e(nome)}</h3><p>{e(p.get("description", ""))}</p><ul class="inside">{"".join(pezzi)}</ul>'
            f'<div class="actions">{"".join(bottoni)}</div>{corpo}</li>')


def main():
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(DIST)
    market = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8"))
    cards = "\n".join(scheda(p) for p in market["plugins"])
    # i segnaposto tengono separate le regole crew da quelle personali nelle preferenze dell'app
    regole = open(os.path.join(ROOT, "plugins", "regole", "regole.md"), encoding="utf-8").read()
    regole = f"{INIZIO}\n{regole.strip()}\n{FINE}\n"
    open(os.path.join(DIST, "regole.txt"), "w", encoding="utf-8").write(regole)
    tpl = open(os.path.join(ROOT, "tools", "pagina.html"), encoding="utf-8").read()
    out = (tpl.replace("{{CATALOGO}}", cards).replace("{{REGOLE}}", e(regole))
           .replace("{{INSTALLA}}", INSTALLA).replace("{{REPO}}", REPO))
    open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(out)
    print(f"dist/: {len(market['plugins'])} plugin, regole, index.html")


if __name__ == "__main__":
    main()
