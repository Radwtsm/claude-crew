#!/usr/bin/env python3
"""Prova da zero su Windows: un Windows nuovo (Windows Sandbox) fa la riga d'installazione di un collega.

    python3 tools/prova_da_zero.py windows      # «windows» = host ssh del PC di prova (Windows Pro, Sandbox attiva)

Copia `prova-da-zero/avvio.ps1` sul PC, apre la Sandbox nella sessione di chi è collegato al PC (la si vede sullo
schermo), aspetta la fine (max 20 min) e controlla l'esito con le stesse regole di test_guida. La Sandbox si cancella
alla chiusura: ogni prova parte da zero. Solo libreria standard; serve ssh senza password verso il PC."""
import base64, os, subprocess, sys, tempfile, time

QUI = os.path.dirname(os.path.abspath(__file__))
CARTELLA = "prova-da-zero"  # in C:\Users\Public: la vede anche l'utente sullo schermo, se è un altro
COMPITO = "PleyadesProvaDaZero"
MINUTI = 20  # una prova buona ne dura ~10
CHIUDI = ("schtasks /end /tn " + COMPITO + " 2>&1 | Out-Null; Get-Process WindowsSandbox* -EA SilentlyContinue | Stop-Process -Force; "
          "Restart-Service CmService -Force")  # finestra, VM rimasta e servizio: la prossima riparte pulita
WSB = """<Configuration>
  <MappedFolders><MappedFolder><HostFolder>{dir}</HostFolder><SandboxFolder>C:\\prova</SandboxFolder>
    <ReadOnly>false</ReadOnly></MappedFolder></MappedFolders>
  <LogonCommand><Command>powershell -ExecutionPolicy Bypass -File C:\\prova\\avvio.ps1</Command></LogonCommand>
</Configuration>"""


def ps(host, comando, check=True):
    # -EncodedCommand: niente virgolette da far passare per cmd; output in code page Windows → errors="replace"
    cod = base64.b64encode(("[Console]::OutputEncoding=[Text.Encoding]::UTF8; " + comando).encode("utf-16-le")).decode()
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", host,
                        "powershell", "-NoProfile", "-EncodedCommand", cod],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if check and r.returncode:
        sys.exit(f"prova_da_zero: sul PC «{comando[:60]}» non va:\n{r.stderr.strip()[-600:]}")
    return r.stdout.strip()


def sveglia(host, schermo, dir_pc, argomenti=""):
    tr = f"powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File {dir_pc}\\sveglia.ps1 {argomenti}"
    ps(host, f"schtasks /create /f /tn {COMPITO} /sc once /st 23:59 /ru '{schermo}' /it /tr '{tr}' | Out-Null; "
             f"schtasks /run /tn {COMPITO} | Out-Null")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    host, a_mano = sys.argv[1], "--a-mano" in sys.argv
    if "--sveglia" in sys.argv:  # solo riaccendere lo schermo e tenerlo sveglio per la Sandbox già aperta
        dir_pc = ps(host, "$env:PUBLIC") + "\\" + CARTELLA
        subprocess.run(["scp", "-q", "-o", "BatchMode=yes", os.path.join(QUI, CARTELLA, "sveglia.ps1"), f"{host}:{dir_pc}/".replace("\\", "/")], check=True)
        return sveglia(host, ps(host, "(Get-CimInstance Win32_ComputerSystem).UserName"), dir_pc)
    if ps(host, "(Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM).State") != "Enabled":
        sys.exit("prova_da_zero: Windows Sandbox non è attiva sul PC (serve Windows Pro: Funzionalità di Windows)")
    # ne gira una alla volta: quella di una prova interrotta (o rimasta a metà) si chiude; il PC è solo di prova
    ps(host, "if (Get-Process WindowsSandbox*, vmmemWindowsSandbox -EA SilentlyContinue) { " + CHIUDI + "; Start-Sleep 5 }")
    schermo = ps(host, "(Get-CimInstance Win32_ComputerSystem).UserName", False)  # chi ha l'accesso allo schermo
    if not schermo:
        sys.exit("prova_da_zero: nessuno ha fatto l'accesso a Windows sul PC: entra (anche bloccato va bene) e rilancia")
    dir_pc = ps(host, "$env:PUBLIC") + "\\" + CARTELLA
    ps(host, f"Remove-Item -Recurse -Force '{dir_pc}' -ErrorAction SilentlyContinue; New-Item -ItemType Directory '{dir_pc}' | Out-Null")
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", os.path.join(QUI, CARTELLA, "avvio.ps1"), os.path.join(QUI, CARTELLA, "sveglia.ps1"),
                    os.path.join(QUI, "..", "installa.ps1"), f"{host}:{dir_pc}/".replace("\\", "/")], check=True)  # provato prima del push
    wsb = WSB.format(dir=dir_pc).replace("'", "''")
    ps(host, f"Set-Content -Encoding UTF8 '{dir_pc}\\prova.wsb' '{wsb}'" + ("" if a_mano else f"; New-Item '{dir_pc}\\chiudi' | Out-Null"))
    # da ssh la Sandbox non si apre (nessuno schermo): un compito nella sessione di chi è allo schermo, che la apre
    # e tiene sveglio il PC finché resta aperta (sveglia.ps1); standby a metà prova = prova ferma
    sveglia(host, schermo, dir_pc, f"-Wsb {dir_pc}\\prova.wsb")
    for _ in range(12):  # la Sandbox parte in pochi secondi; se no il compito non è partito
        time.sleep(5)
        if ps(host, "(Get-Process WindowsSandbox* -EA SilentlyContinue).Count", False) not in ("", "0"):
            break
    else:
        ps(host, f"schtasks /delete /f /tn {COMPITO} | Out-Null", False)
        sys.exit("prova_da_zero: la Sandbox non è partita sul PC (compito interattivo non eseguito): guarda lo schermo del PC")
    print(f"Sandbox aperta sul PC ({'resta aperta' if a_mano else 'si chiude alla fine'}); aspetto la fine…", flush=True)
    visti, t = "", time.time()
    while time.time() - t < MINUTI * 60:
        time.sleep(30)
        passi = ps(host, f"Get-Content '{dir_pc}\\esito\\passi.txt' -ErrorAction SilentlyContinue", False)
        if time.time() - t > 6 * 60 and passi == visti and passi.endswith("installa.ps1"):  # bloccata: cosa gira dentro
            print(ps(host, f"Get-Content '{dir_pc}\\esito\\processi.txt' -Tail 8 -EA SilentlyContinue", False), flush=True)
        if passi != visti:
            print("\n".join(passi.splitlines()[len(visti.splitlines()):]), flush=True)
            visti = passi
        if passi.endswith("fine"):
            break
    else:
        print(f"prova_da_zero: {MINUTI} minuti senza finire: chiudo la Sandbox", file=sys.stderr)
        ps(host, CHIUDI, False)
    dest = tempfile.mkdtemp(prefix="da-zero-")
    subprocess.run(["scp", "-q", "-r", "-o", "BatchMode=yes", f"{host}:{dir_pc}/esito".replace("\\", "/"), dest])
    esito = os.path.join(dest, "esito")
    leggi = lambda f: open(os.path.join(esito, f), encoding="utf-8-sig", errors="replace").read() if os.path.exists(os.path.join(esito, f)) else ""
    sys.path.insert(0, QUI)
    from test_guida import forma, esiti  # stesse regole di UX della prova in casa finta
    err = forma(leggi("guida.txt"), "guida (da zero)") + forma(leggi("controlla.txt"), "controlla (da zero)")
    if "fine" not in visti:
        err.append("non è arrivata alla fine")
    if "a posto" not in leggi("guida.txt"):
        err.append("guida: manca il riepilogo finale («x/y a posto»): si è fermata prima")
    print(leggi("programmi.txt"))
    print("esiti:", ", ".join(esiti(leggi("controlla.txt")) or esiti(leggi("guida.txt"))) or "nessuno")
    for e in err:
        print("prova_da_zero: " + e, file=sys.stderr)
    print(f"file: {esito}")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
