#!/usr/bin/env python3
"""Aggiunge una skill alla libreria come plugin suo (una skill = un plugin).

Uso: python3 tools/aggiungi.py <skill.zip | cartella-skill> <categoria>
Poi: leggi per intero i file aggiunti (script compresi), sh check.sh, PR.
"""
import json, os, re, shutil, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, categoria = sys.argv[1], sys.argv[2]
    tmp = None
    if src.endswith(".zip"):
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if n.startswith("/") or ".." in n.split("/"):
                    sys.exit(f"percorso non sicuro nello zip: {n}")
            z.extractall(tmp)
        found = [d for d, _, f in os.walk(tmp) if "SKILL.md" in f and "__MACOSX" not in d]
        if len(found) != 1:
            sys.exit("lo zip deve contenere una sola cartella con SKILL.md")
        src = found[0]
    text = open(os.path.join(src, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    meta = dict(re.findall(r"^(\w+): (.*)$", m.group(1), re.M)) if m else {}
    name, desc = meta.get("name", ""), meta.get("description", "")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or not desc:
        sys.exit("SKILL.md senza 'name' (minuscole e trattini) o 'description' nel frontmatter")
    pdir = os.path.join(ROOT, "plugins", name)
    if os.path.exists(pdir):
        sys.exit(f"esiste già plugins/{name}: aggiorna quella cartella")
    shutil.copytree(src, os.path.join(pdir, "skills", name), ignore=shutil.ignore_patterns(".DS_Store", "__MACOSX"))
    os.makedirs(os.path.join(pdir, ".claude-plugin"))
    short = desc.split(" - ")[0].split(". Usala")[0][:120]
    with open(os.path.join(pdir, ".claude-plugin", "plugin.json"), "w", encoding="utf-8") as f:
        json.dump({"name": name, "description": short, "author": {"name": "crew"}}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    mpath = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    market = json.load(open(mpath, encoding="utf-8"))
    market["plugins"].append({"name": name, "source": f"./plugins/{name}", "category": categoria,
                              "description": short})
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(market, f, ensure_ascii=False, indent=2)
        f.write("\n")
    if tmp:
        shutil.rmtree(tmp)
    print(f"aggiunto plugins/{name} ({categoria}); rileggi per intero:")
    for d, _, files in os.walk(pdir):
        for f in files:
            print("  " + os.path.relpath(os.path.join(d, f), ROOT))


if __name__ == "__main__":
    main()
