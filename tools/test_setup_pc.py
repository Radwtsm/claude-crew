#!/usr/bin/env python3
"""Il setup tocca il PC solo dove serve (owner 02/11, A88 dell'agenzia): il terminale fuori dal setup, `auto` non
rimette un'app disinstallata né l'attività tolta con `pianifica --togli`. In una casa finta, niente tocca il PC vero.
Uso: python3 tools/test_setup_pc.py"""
import importlib.util, os, sys, tempfile

os.environ["HOME"] = os.environ["USERPROFILE"] = tempfile.mkdtemp(prefix="casa-")  # Windows: ~ è USERPROFILE
spec = importlib.util.spec_from_file_location("crew", os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)
male = []


def vietato(*a, **k):
    raise AssertionError("terminale toccato")


crew.ha = lambda x: False  # niente `claude plugin` veri
crew.casa_di_prova = lambda: True  # Windows non ha pwd: senza, `pianifica` creerebbe l'attività vera
crew.run = vietato  # nessun programma vero
crew.tema_windows = crew.tema_terminale = crew.tema_iterm = crew.tema_prompt = crew.tema_salvaschermo = vietato
crew.terminale_messo = lambda: False
for t in (False, None):
    try:
        crew.tema(terminale=t)
    except AssertionError as e:
        male.append(f"tema(terminale={t}): {e}")

installate = []
crew.installa_app_mac = crew.installa_app_windows = lambda app: installate.append(app["nome"]) or crew.Esito("x", True)
app = {"nome": "Prova", "mac": {"app": "Prova.app"}, "windows": {"app": "Prova"}}
crew.installa_app(None, None, app, auto=True, presente=lambda a: True)
if "Prova" not in crew.stato().get("app_viste", []):
    male.append("app presente non ricordata")
installate.clear()
e = crew.installa_app(None, None, app, auto=True, presente=lambda a: False)
if installate or not e.saltato:
    male.append("auto ha rimesso un'app disinstallata")
crew.installa_app(None, None, app, presente=lambda a: False)
if (crew.MAC or crew.WIN) and installate != ["Prova"]:
    male.append("`pleyades-cli app` non la rimette")

crew.pianifica(togli=True)
if "tolta da te" not in crew.pianifica()[1]:
    male.append("auto rimette l'attività tolta")
crew.pianifica(rimetti=True)
if crew.stato().get("pianifica_tolta"):
    male.append("`pianifica` non la riattiva")

if male:
    sys.exit("test_setup_pc: " + "; ".join(male))
print("test_setup_pc: ok")
