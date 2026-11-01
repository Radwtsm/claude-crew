#!/usr/bin/env python3
"""`pleyades-cli squadra` conta solo chi è ancora nella stanza: chi è tolto dallo studio non resta «non allineato».
Uso: python3 tools/test_squadra.py"""
import importlib.util, os, sys

spec = importlib.util.spec_from_file_location("crew", os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)

ultimi = {("anna", "Windows"): 1, ("claude-anna", "Darwin"): 2, ("bruno", "Darwin"): 3, ("?", "Darwin"): 4,
          ("claude-bruno", "Windows"): 5}
resta = crew.solo_presenti(ultimi, {"anna"})
atteso = {("anna", "Windows"): 1, ("claude-anna", "Darwin"): 2}
if resta != atteso:
    sys.exit(f"test_squadra: atteso {atteso}, avuto {resta}")
print("test_squadra: ok")
