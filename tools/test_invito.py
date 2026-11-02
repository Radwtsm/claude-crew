#!/usr/bin/env python3
"""Dopo il login GitHub, l'invito al repo del progetto si accetta da solo: solo quello, mai gli altri.
Uso: python3 tools/test_invito.py"""
import importlib.util, os, sys

spec = importlib.util.spec_from_file_location("crew", os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)

# GitHub finto: due inviti (il nostro, con il nome in maiuscolo diverso, e un altro); il repo si vede dopo l'accettazione
inviti = [{"id": 7, "repository": {"full_name": "Anna/Progetto"}}, {"id": 9, "repository": {"full_name": "x/altro"}}]
accettati, err = [], []


def run(*a, **k):
    a = list(a)
    if a[:3] == ["gh", "api", "user/repository_invitations"]:
        filtro = a[a.index("-q") + 1]
        return 0, "\n".join(str(i["id"]) for i in inviti
                            if f'"{i["repository"]["full_name"].lower()}"' in filtro)
    if a[:4] == ["gh", "api", "-X", "PATCH"]:
        accettati.append(a[4].rsplit("/", 1)[1])
        return 0, ""
    if a[:2] == ["gh", "api"] and a[2].startswith("repos/"):
        return (0, a[2][6:]) if "7" in accettati else (1, "Not Found")
    return 1, ""


crew.run, crew.gh_collegato = run, lambda: True
if crew.repo_accessibile("anna/progetto") != "si":
    err.append("con l'invito in attesa il repo non diventa accessibile")
if accettati != ["7"]:
    err.append(f"accettati {accettati}, atteso solo ['7']")
accettati.clear(); inviti.pop(0)
if crew.repo_accessibile("anna/nuovo") != "no" or accettati:
    err.append("senza invito deve restare «no» senza accettare niente")
for e in err:
    print("test_invito: " + e, file=sys.stderr)
sys.exit(1 if err else print("test_invito: ok"))
