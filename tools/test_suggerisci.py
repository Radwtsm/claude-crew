#!/usr/bin/env python3
"""L'hook dei messaggi propone un plugin che fa al caso della richiesta anche se è installato ma spento (enable),
non quello acceso. Casa finta in CLAUDE_CONFIG_DIR. Uso: python3 tools/test_suggerisci.py"""
import contextlib, importlib.util, io, json, os, sys, tempfile

casa = tempfile.mkdtemp(prefix="suggerisci-")
os.environ["CLAUDE_CONFIG_DIR"] = casa


def scrivi(rel, dati):
    p = os.path.join(casa, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(dati, open(p, "w", encoding="utf-8"))


scrivi("plugins/marketplaces/crew/.claude-plugin/marketplace.json", {"plugins": [
    {"name": "acceso", "keywords": ["blender"]}, {"name": "spento", "keywords": ["blender"]},
    {"name": "mancante", "keywords": ["ffmpeg"]}]})
scrivi("plugins/installed_plugins.json", {"plugins": {"acceso@crew": [], "spento@crew": []}})
scrivi("settings.json", {"enabledPlugins": {"acceso@crew": True, "spento@crew": False}})

spec = importlib.util.spec_from_file_location("personale", os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "plugins", "regole", "scripts", "personale.py"))
personale = importlib.util.module_from_spec(spec)
spec.loader.exec_module(personale)

out = io.StringIO()
with contextlib.redirect_stdout(out):
    personale.suggerisci("render in blender e video con ffmpeg")
t = out.getvalue()
for c, atteso in (("enable spento@crew", True), ("install mancante@crew", True), ("acceso@crew", False)):
    if (c in t) != atteso:
        sys.exit(f"test_suggerisci: «{c}» {'manca' if atteso else 'non deve esserci'} in: {t!r}")
out = io.StringIO()
with contextlib.redirect_stdout(out):
    personale.suggerisci("render in blender e video con ffmpeg")
if out.getvalue():
    sys.exit("test_suggerisci: lo stesso plugin riproposto prima di una settimana")
print("test_suggerisci: ok")
