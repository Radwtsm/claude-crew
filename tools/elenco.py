#!/usr/bin/env python3
"""Rigenera .claude-plugin/marketplace.json dalle cartelle plugins/*: nessuno lo modifica a mano, così due Claude
che aggiungono skill insieme non si pestano i piedi. Categoria = primo "keywords" del plugin.json.

Plugin di terzi utili a tutti: `esterni.json` (lista di voci del marketplace con sorgente git fissata a un commit,
`sha` obbligatorio), aggiunti all'elenco dopo i nostri.

Uso: python3 tools/elenco.py  (lo lanciano aggiungi.py e la sincronizzazione della cartella condivisa)
Esce con 1 e stampa i problemi se un plugin è scritto male (viene saltato, gli altri restano).
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMI = ("regole", "codice")


def genera(root=ROOT):
    mpath = os.path.join(root, ".claude-plugin", "marketplace.json")
    market = json.load(open(mpath, encoding="utf-8"))
    voci, problemi = [], []
    pdir = os.path.join(root, "plugins")
    for nome in sorted(os.listdir(pdir)):
        if not os.path.isdir(os.path.join(pdir, nome)) or nome.startswith("."):
            continue
        try:
            pj = json.load(open(os.path.join(pdir, nome, ".claude-plugin", "plugin.json"), encoding="utf-8"))
        except (OSError, ValueError) as e:
            problemi.append(f"plugins/{nome}: plugin.json mancante o non valido ({e})")
            continue
        if pj.get("name") != nome or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", nome) or not pj.get("description"):
            problemi.append(f"plugins/{nome}: 'name' deve essere uguale alla cartella (minuscole e trattini) "
                            f"e serve 'description'")
            continue
        if "version" in pj:
            problemi.append(f"plugins/{nome}: togli 'version' (chi installa non riceverebbe più gli aggiornamenti)")
            continue
        voce = {"name": nome, "source": f"./plugins/{nome}", "description": pj["description"]}
        if pj.get("keywords"):
            voce["category"] = pj["keywords"][0]
        voci.append(voce)
    voci.sort(key=lambda v: (PRIMI.index(v["name"]) if v["name"] in PRIMI else len(PRIMI),
                             v.get("category", ""), v["name"]))
    epath = os.path.join(root, "esterni.json")
    for v in json.load(open(epath, encoding="utf-8")) if os.path.isfile(epath) else []:
        src = v.get("source") if isinstance(v, dict) else None
        if not (isinstance(src, dict) and re.fullmatch(r"[0-9a-f]{40}", src.get("sha", "")) and v.get("name")
                and v.get("description") and v["name"] not in {x["name"] for x in voci}):
            problemi.append(f"esterni.json: voce {v.get('name') if isinstance(v, dict) else v!r} senza nome, "
                            f"descrizione o 'sha' di 40 caratteri (o nome già usato)")
            continue
        voci.append(v)
    market["plugins"] = voci
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(market, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return problemi


if __name__ == "__main__":
    probs = genera()
    for p in probs:
        print(p)
    sys.exit(1 if probs else 0)
