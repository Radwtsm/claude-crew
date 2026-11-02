#!/usr/bin/env python3
"""Con l'invito la riga installa solo l'app Pleiadi (A90, owner 02/11): niente Git, Python, strumenti di Apple né domande;
installa solo un'app con la firma della squadra; codice sbagliato = nessun download. Rete e programmi finti.
Uso: python3 tools/test_solo_app.py"""
import os, shutil, stat, subprocess, sys, tempfile

radice = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
male = []

# installa.sh: un Mac finto (uname), un curl finto che dà un'app senza firma, un codesign finto che la rifiuta
casa = tempfile.mkdtemp(prefix="solo-app-")
bin_, app = os.path.join(casa, "bin"), os.path.join(casa, "Applicazioni")
os.makedirs(os.path.join(casa, "pacchetto", "Pleiadi.app", "Contents"))
os.makedirs(bin_)
subprocess.run(["tar", "-czf", os.path.join(casa, "app.tar.gz"), "-C", os.path.join(casa, "pacchetto"), "Pleiadi.app"],
               check=True)
registro = os.path.join(casa, "chiamati")
finti = {"uname": "echo Darwin",
         "curl": f'echo curl >>{registro}; o=; while [ $# -gt 0 ]; do [ "$1" = -o ] && o=$2; shift; done; cp {casa}/app.tar.gz "$o"',
         "codesign": f"echo codesign >>{registro}; exit ${{FIRMA_ESITO:-1}}",
         "xcode-select": f"echo xcode-select >>{registro}; exit 1", "softwareupdate": f"echo softwareupdate >>{registro}",
         "python3": f"echo python3 >>{registro}", "open": f"echo open >>{registro}", "sudo": f"echo sudo >>{registro}",
         "ditto": 'cp -R "$1" "$2"'}
for nome, corpo in finti.items():
    p = os.path.join(bin_, nome)
    open(p, "w").write(f"#!/bin/sh\n{corpo}\n")
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)


def riga(invito, **env):
    open(registro, "w").close()
    e = {"PATH": f"{bin_}:/usr/bin:/bin", "HOME": casa, "INVITO": invito, "PLEYADES_APP_DIR": app, **env}
    r = subprocess.run(["bash", os.path.join(radice, "installa.sh")], env=e, capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, timeout=60)
    return r.returncode, r.stdout + r.stderr, open(registro).read().split()


codice = "ABCDE-FGHJK-MNPQR-STUVW"
esito, testo, chiamati = riga("sbagliato")
if esito == 0 or chiamati:
    male.append(f"installa.sh: codice sbagliato deve fermarsi prima di tutto (esito {esito}, chiamati {chiamati})")
esito, testo, chiamati = riga(codice.lower())
if esito == 0 or os.path.exists(os.path.join(app, "Pleiadi.app")) or "firma della squadra" not in testo:
    male.append(f"installa.sh: un'app senza la firma della squadra non si installa (esito {esito}): {testo[-200:]}")
esito, testo, chiamati = riga(codice, FIRMA_ESITO="0")
if esito != 0 or not os.path.isdir(os.path.join(app, "Pleiadi.app")) or "open" not in chiamati:
    male.append(f"installa.sh: con la firma giusta installa e apre l'app (esito {esito}): {testo[-200:]}")
for vietato in ("xcode-select", "softwareupdate", "python3", "sudo"):
    if vietato in chiamati:
        male.append(f"installa.sh: con l'invito chiama {vietato} (deve installare solo l'app)")
if "[S/N]" in testo:
    male.append("installa.sh: con l'invito fa domande")
shutil.rmtree(casa, ignore_errors=True)

for m in male:
    print("test_solo_app: " + m, file=sys.stderr)
sys.exit(1 if male else print("test_solo_app: ok"))
