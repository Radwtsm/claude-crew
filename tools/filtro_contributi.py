#!/usr/bin/env python3
"""Filtro delle pull request: etichetta `solo-skill` o `da-rileggere` e un commento con i motivi.

Gira con pull_request_target: il codice è quello di main, la PR non può cambiarlo, e i suoi file si leggono via API
come DATI (mai eseguiti). Aiuta chi rilegge, non approva: una PR entra solo col merge del manutentore.
Una skill "di solo testo" può comunque eseguire comandi (`!` + comando fra apici inversi, hook nel frontmatter) e
plugin.json può dichiarare hook e MCP: per questo guarda il contenuto, non solo i percorsi.

Uso (dal workflow): PR=<numero> REPO=<owner/nome> GH_TOKEN=… python3 tools/filtro_contributi.py
"""
import base64, json, os, re, subprocess, sys

SEGNO = "<!-- filtro-contributi -->"
TESTO = re.compile(r"plugins/[a-z0-9-]+/skills/[a-z0-9-]+/[\w./-]+\.md")
CHIAVI_PLUGIN = {"name", "description", "author", "keywords"}
CHIAVI_SKILL = {"name", "description"}
COMANDI = re.compile(r"!`|^\s*!\s*\w", re.M)  # esecuzione inline delle skill
INVISIBILI = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿\U000e0000-\U000e007f]")


def controlla_testo(percorso, testo):
    motivi = []
    if COMANDI.search(testo):
        motivi.append(f"`{percorso}`: comando eseguibile dentro il testo")
    if INVISIBILI.search(testo):
        motivi.append(f"`{percorso}`: caratteri invisibili")
    m = re.match(r"---\n(.*?)\n---\n", testo, re.S)
    if percorso.endswith("/SKILL.md"):
        chiavi = set(re.findall(r"^([\w-]+):", m.group(1), re.M)) if m else set()
        if chiavi - CHIAVI_SKILL:
            motivi.append(f"`{percorso}`: frontmatter con {', '.join(sorted(chiavi - CHIAVI_SKILL))}")
    return motivi


def controlla_plugin(percorso, testo):
    try:
        chiavi = set(json.loads(testo))
    except (ValueError, TypeError):
        return [f"`{percorso}`: json non valido"]
    return [f"`{percorso}`: campi {', '.join(sorted(chiavi - CHIAVI_PLUGIN))}"] if chiavi - CHIAVI_PLUGIN else []


def controlla_catalogo(testo):
    try:
        voci = json.loads(testo)["plugins"]
        sorgenti = [(v["name"], v["source"]) for v in voci]
    except (ValueError, KeyError, TypeError):
        return ["`.claude-plugin/marketplace.json`: formato non valido"]
    return [f"catalogo: `{n}` non punta a `./plugins/{n}`" for n, s in sorgenti if s != f"./plugins/{n}"]


def esamina(file):
    """file = [(percorso, stato, testo)]; torna i motivi per rileggere con attenzione (vuoto = solo testo di skill)."""
    motivi = []
    for percorso, stato, testo in file:
        percorso = percorso.replace("`", "'")
        if stato not in ("added", "modified"):
            motivi.append(f"`{percorso}`: {stato}")
        elif percorso == ".claude-plugin/marketplace.json":
            motivi += controlla_catalogo(testo)
        elif re.fullmatch(r"plugins/[a-z0-9-]+/\.claude-plugin/plugin\.json", percorso):
            motivi += controlla_plugin(percorso, testo)
        elif TESTO.fullmatch(percorso) and ".." not in percorso:
            motivi += controlla_testo(percorso, testo)
            if percorso.startswith("plugins/regole/"):
                motivi.append(f"`{percorso}`: regole comuni, arrivano a tutti in ogni sessione")
        else:
            motivi.append(f"`{percorso}`: fuori dalle skill")
    return motivi


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def contenuto(repo, percorso, sha):
    r = json.loads(gh("api", f"repos/{repo}/contents/{percorso}?ref={sha}"))
    return base64.b64decode(r["content"]).decode("utf-8", "replace")


def main():
    repo, pr = os.environ["REPO"], os.environ["PR"]
    sha = json.loads(gh("api", f"repos/{repo}/pulls/{pr}"))["head"]["sha"]
    righe = gh("api", "--paginate", f"repos/{repo}/pulls/{pr}/files", "--jq", ".[] | [.filename, .status] | @json")
    file = []
    for r in righe.splitlines():
        p, stato = json.loads(r)
        file.append((p, stato, contenuto(repo, p, sha) if stato in ("added", "modified") else ""))
    motivi = esamina(file)
    tieni, togli = ("da-rileggere", "solo-skill") if motivi else ("solo-skill", "da-rileggere")
    corpo = SEGNO + ("\n⚠️ **Da rileggere con attenzione**\n" + "\n".join(f"- {m}" for m in motivi) if motivi
                     else "\n✅ Solo testo di skill. Va letto comunque: arriva al Claude di tutti.")
    gh("api", "-X", "POST", f"repos/{repo}/issues/{pr}/labels", "-f", f"labels[]={tieni}")
    subprocess.run(["gh", "api", "-X", "DELETE", f"repos/{repo}/issues/{pr}/labels/{togli}"], capture_output=True)
    vecchi = gh("api", "--paginate", f"repos/{repo}/issues/{pr}/comments", "--jq",
                f'.[] | select(.body | startswith("{SEGNO}")) | .id').split()
    if vecchi:
        gh("api", "-X", "PATCH", f"repos/{repo}/issues/comments/{vecchi[0]}", "-f", f"body={corpo}")
    else:
        gh("api", "-X", "POST", f"repos/{repo}/issues/{pr}/comments", "-f", f"body={corpo}")


if __name__ == "__main__":
    sys.exit(main())
