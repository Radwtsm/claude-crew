#!/usr/bin/env python3
"""Il push automatico di claude-personale (hook Stop) non porta segreti su GitHub (A124): con un token nel diff
niente commit, la coda si svuota e l'utente è avvisato; senza segreti commit normale. In una casa finta.
Uso: python3 tools/test_segreti_push.py"""
import importlib.util, io, os, subprocess, sys, tempfile
from contextlib import redirect_stdout

os.environ["HOME"] = os.environ["USERPROFILE"] = casa = tempfile.mkdtemp(prefix="casa-")
radice = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("personale", os.path.join(radice, "plugins/regole/scripts/personale.py"))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
p.REPO = repo = os.path.join(casa, "claude-personale")
p.hook_input = lambda: {}
os.makedirs(repo)
for c in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
    p.git(*c)
male = []


def giro(testo):
    with open(os.path.join(repo, "memoria.md"), "a") as f:
        f.write(testo + "\n")
    out = io.StringIO()
    with redirect_stdout(out):
        p.fine()
    return out.getvalue(), p.git("rev-list", "--count", "--all").stdout.strip() or "0", p.git("diff", "--cached", "--name-only").stdout.strip()


out, n, coda = giro("nota normale")
if n != "1" or out:
    male.append(f"senza segreti: commit atteso, avuti {n}, messaggio {out!r}")
out, n, coda = giro("token: ghp_" + "a" * 36)
if n != "1" or coda or "segreto" not in out or "memoria.md" not in out:
    male.append(f"con segreto: commit {n}, coda {coda!r}, messaggio {out!r}")
print("\n".join("❌ " + m for m in male) or "✅ push automatico senza segreti")
sys.exit(1 if male else 0)
