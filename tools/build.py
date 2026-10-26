#!/usr/bin/env python3
"""Costruisce in dist/ la pagina per chi usa l'app Claude: uno zip per skill + le regole da incollare.

Uso: python3 tools/build.py  (lo lancia la CI a ogni push su main e pubblica dist/ su GitHub Pages)
"""
import html, json, os, re, shutil, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
REPO = "Radwtsm/claude-crew"
SOLO_CLI = {"installa-crew"}
INIZIO = "<!-- regole crew: inizio (si aggiornano dalla pagina della crew, non modificare qui) -->"
FINE = "<!-- regole crew: fine -->"


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(re.findall(r"^(\w+): (.*)$", m.group(1), re.M)) if m else {}


def main():
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(DIST)
    market = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8"))
    skills, plugins = [], []
    for p in market["plugins"]:
        pdir = os.path.join(ROOT, p["source"])
        plugins.append(p)
        sdir = os.path.join(pdir, "skills")
        for name in sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []:
            if name in SOLO_CLI:
                continue
            src = os.path.join(sdir, name)
            fm = frontmatter(os.path.join(src, "SKILL.md"))
            # l'app Claude vuole uno zip con dentro la cartella della skill
            with zipfile.ZipFile(os.path.join(DIST, f"{name}.zip"), "w", zipfile.ZIP_DEFLATED) as z:
                for dirpath, _, files in os.walk(src):
                    for f in sorted(files):
                        full = os.path.join(dirpath, f)
                        z.write(full, os.path.join(name, os.path.relpath(full, src)))
            skills.append((p.get("category", p["name"]), name, fm.get("description", "")))
    # i segnaposto tengono separate le regole crew da quelle personali nelle preferenze dell'app
    regole = open(os.path.join(ROOT, "plugins", "regole", "regole.md"), encoding="utf-8").read()
    regole = f"{INIZIO}\n{regole.strip()}\n{FINE}\n"
    open(os.path.join(DIST, "regole.txt"), "w", encoding="utf-8").write(regole)

    tpl = open(os.path.join(ROOT, "tools", "pagina.html"), encoding="utf-8").read()
    cards = "\n".join(
        f'<li class="skill"><div><span class="tag">{html.escape(plug)}</span><h3>{html.escape(name)}</h3>'
        f'<p>{html.escape(desc.split(" - ")[0].split(". Usala")[0])}</p></div>'
        f'<a class="btn" href="{name}.zip" download>Scarica</a></li>'
        for plug, name, desc in skills)
    install = "\n".join(f"/plugin install {p['name']}@claude-crew" for p in plugins)
    out = (tpl.replace("{{SKILLS}}", cards).replace("{{REGOLE}}", html.escape(regole))
           .replace("{{INSTALL}}", html.escape(install)).replace("{{REPO}}", REPO))
    open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(out)
    print(f"dist/: {len(skills)} skill, regole, index.html")


if __name__ == "__main__":
    main()
