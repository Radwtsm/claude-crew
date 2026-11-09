"""Windows: niente finestre cmd che lampeggiano (owner 09/11, #53). Un processo lanciato con DETACHED_PROCESS
(0x00000008) non ha console: ogni git/python/.cmd figlio ne apre una visibile. In background si usa
CREATE_NO_WINDOW (0x08000000) | CREATE_NEW_PROCESS_GROUP (0x00000200).
Uso: python3 tools/test_finestre.py  (su ogni sistema: legge solo i sorgenti)"""
import os, re, sys

RADICE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MALE = re.compile(r"DETACHED_PROCESS|creationflags[^\n]*0x0*8\b|creationflags[^\n]*0x0800_?0008")
male = []
for d, _, fs in os.walk(RADICE):
    if "/." in d.replace("\\", "/") or "__pycache__" in d:
        continue
    for f in fs:
        if f.endswith(".py") and f != "test_finestre.py":
            p = os.path.join(d, f)
            for n, r in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if MALE.search(r):
                    male.append(f"{os.path.relpath(p, RADICE)}:{n}: DETACHED_PROCESS → usa 0x08000000 | 0x00000200")
sys.path.insert(0, RADICE)
import crew  # noqa: E402
crew.figli_senza_finestra()  # fuori da Windows non fa niente, su Windows non deve rompersi
print("\n".join(male) or "✓ nessun lancio staccato con finestra")
sys.exit(1 if male else 0)
