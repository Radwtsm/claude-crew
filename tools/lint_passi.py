#!/usr/bin/env python3
"""Ogni Esito di crew.py appartiene a un passo di PASSI e ogni passo ha ancora i suoi Esiti (owner 30/10: una funzione
o un passo di setup nuovo arriva sempre col suo passo di onboarding). Lo lancia check.sh. Uso: python3 tools/lint_passi.py"""
import ast, os, sys

LIVELLI = {"obbligatorio", "facoltativo", "stato", "azione"}
SISTEMI = {"mac", "windows", "linux"}
CAMPI = {"id", "nome", "livello", "sistemi", "fa", "esiti"}


def nome(n):
    """Il primo argomento di Esito come lo scrive il registro: testo fisso, {} per ogni parte variabile; None se non si sa."""
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        return n.value
    if isinstance(n, ast.JoinedStr):
        return "".join(x.value if isinstance(x, ast.Constant) else "{}" for x in n.values)
    if isinstance(n, ast.Name):  # una variabile (es. repo): tutto variabile
        return "{}"
    return None


def main(radice="."):
    f = os.path.join(radice, "crew.py")
    albero = ast.parse(open(f, encoding="utf-8").read(), f)
    passi = next(ast.literal_eval(n.value) for n in albero.body
                 if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "PASSI")
    errori, noti, ids = [], {}, set()
    for p in passi:
        if set(p) != CAMPI:
            errori.append(f"passo {p.get('id')}: campi {sorted(set(p) ^ CAMPI)} (servono {sorted(CAMPI)})")
        if p.get("id") in ids:
            errori.append(f"passo {p['id']} doppio")
        ids.add(p.get("id"))
        if p.get("livello") not in LIVELLI:
            errori.append(f"passo {p.get('id')}: livello «{p.get('livello')}» (uno di {sorted(LIVELLI)})")
        if not set(p.get("sistemi", "").split()) or not set(p.get("sistemi", "").split()) <= SISTEMI:
            errori.append(f"passo {p.get('id')}: sistemi «{p.get('sistemi')}» (fra {sorted(SISTEMI)})")
        for t in p.get("esiti", []):
            if t in noti:
                errori.append(f"«{t}» in due passi: {noti[t]} e {p['id']}")
            noti[t] = p.get("id")
    usati = set()
    for n in ast.walk(albero):
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "Esito" and n.args:
            t = nome(n.args[0])
            if t is None:
                errori.append(f"crew.py:{n.lineno}: nome dell'Esito non leggibile (scrivilo come testo o f-string)")
            elif t not in noti:
                errori.append(f"crew.py:{n.lineno}: Esito «{t}» senza passo: aggiungilo agli `esiti` di un passo di "
                              "PASSI (o un passo nuovo, con livello e sistemi)")
            else:
                usati.add(t)
    errori += [f"passo {noti[t]}: «{t}» non è più un Esito di crew.py: toglilo" for t in sorted(set(noti) - usati)]
    for e in errori:
        print("lint_passi: " + e, file=sys.stderr)
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
