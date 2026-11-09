#!/usr/bin/env python3
"""Lo scarico di una cartella dello studio non scrive fuori dalla copia (A129): un file chiamato `..` o con
separatori, mandato dal server, viene scartato; un percorso che esce lo stesso ferma lo scarico. Casa finta, niente rete.
Uso: python3 tools/test_studio_percorsi.py"""
import importlib.util, os, sys, tempfile

os.environ["HOME"] = os.environ["USERPROFILE"] = casa = tempfile.mkdtemp(prefix="casa-")
radice = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("crew", os.path.join(radice, "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)
crew.live = lambda *a, **k: None
male = []
cred = {"utente": "u"}
base = "/remote.php/dav/files/u/"


def risposta(*nomi):
    r = "".join(f"<d:response><d:href>{base}Cartella/{n}</d:href><d:propstat><d:prop><d:resourcetype/></d:prop>"
                f"</d:propstat></d:response>" for n in nomi)
    return f'<?xml version="1.0"?><d:multistatus xmlns:d="DAV:">{r}</d:multistatus>'.encode()


crew.chiama = lambda *a, **k: risposta("buono.txt", "..", "%2E%2E", "a%5Cb", "c%3Ad")
nomi = [n for n, _ in crew.dav_elenco("https://{host}/", cred, "Cartella")]
if nomi != ["buono.txt"]:
    male.append(f"dav_elenco tiene nomi pericolosi: {nomi}")

dest = os.path.join(casa, ".crew", "studio", "cartella")
crew.dav_elenco = lambda s, c, p: [("..", False)] if p.strip("/") == "Cartella" else []
crew.dav_leggi = lambda *a: b"print('preso')"
try:
    crew.scarica_cartella("https://{host}/", cred, "Cartella", dest)
    male.append("scarica_cartella ha accettato `..`")
except ValueError:
    pass
fuori = os.path.join(casa, ".crew", "studio", "cartella.nuovo", "..")
if os.path.isfile(os.path.join(casa, ".crew", "studio", "..")) or os.path.isfile(fuori):
    male.append("file scritto fuori dalla copia")
print("\n".join("❌ " + m for m in male) or "✅ studio: nessun file fuori dalla copia")
sys.exit(1 if male else 0)
