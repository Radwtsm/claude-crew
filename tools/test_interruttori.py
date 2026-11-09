#!/usr/bin/env python3
"""Gli interruttori dell'app (A119) in una casa finta: `scelte` li elenca con spiegazione e dipendenze, `accendi`
rifiuta senza le dipendenze, la prima scelta parte da ciò che c'è già, «allineato» conta solo gli accesi, `spegni`
toglie solo le parti Pleyades, `--json` scrive solo righe JSON. Nessun programma vero (run finto).
Uso: python3 tools/test_interruttori.py"""
import contextlib, importlib.util, io, json, os, sys, tempfile

CASA = tempfile.mkdtemp(prefix="casa-")
os.environ["HOME"] = os.environ["USERPROFILE"] = CASA  # Windows: ~ è USERPROFILE
spec = importlib.util.spec_from_file_location("crew", os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "crew.py"))
crew = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crew)
male, chiamate, programmi = [], [], {"git"}


def finto(*cmd, **k):
    chiamate.append(cmd)
    return 0, ""


crew.run = finto
crew.ha = lambda x: x in programmi
crew.casa_di_prova = lambda: True  # niente attività pianificate vere
crew.claude_collegato = lambda: True
crew.installa_claude = lambda: (programmi.add("claude"), (True, ""))[1]
crew.assicura_plugin = lambda mk, p: ([], True)
crew.impostazioni_utente = lambda *a: None
crew.app_nextcloud = crew.app_talk = crew.profilo_dav_installato = crew.terminale_messo = lambda: False


def prova(cosa, ok):
    if not ok:
        male.append(cosa)


def lancia(*a):
    """main() con questi argomenti: (codice, righe JSON lette)."""
    sys.argv, out = ["crew.py", *a], io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        codice = crew.main()
    righe = [r for r in out.getvalue().splitlines() if r.strip()]
    try:
        return codice, [json.loads(r) for r in righe]
    except ValueError:
        male.append(f"{a}: righe non JSON: {righe[:3]}")
        return codice, []


# casa vuota: tutto spento, consigliati Claude, regole e aggiornamento automatico
s = {x["id"]: x for x in crew.scelte()}
prova("scelte: claude, crew, auto, talk", {"claude", "crew", "auto", "talk"} <= set(s))
prova("scelte: niente acceso in una casa vuota", not any(x.get("acceso") for x in s.values()))
prova("scelte: consigliati = claude, crew, auto",
      {i for i, x in s.items() if x.get("consigliato")} == {"claude", "crew", "auto"})
prova("scelte: ogni voce con spiegazione", all(x["spiega"] for x in s.values()))
prova("scelte: i passi con Claude restano bottoni (fa skill)", s.get("scheda", {}).get("fa", "").startswith("skill:"))

# dipendenze: le regole vogliono Claude
codice, r = lancia("accendi", "crew", "--json")
prova(f"accendi crew senza Claude → 3 (era {codice})", codice == 3)
prova("accendi crew senza Claude: riga «dipende» con claude", r and r[-1].get("mancano") == ["claude"])
prova("rifiutato: niente scelto", crew.accesi() is None)

codice, r = lancia("accendi", "claude", "--json")
prova(f"accendi claude → 0 (era {codice})", codice == 0)
prova("accendi claude: ultima riga «fine» acceso", r and r[-1] == {"tipo": "fine", "id": "claude", "acceso": True,
                                                                     "ok": True})
prova("accendi claude: avanzamento con esiti", any(x["tipo"] == "esito" and x["passo"] == "claude" for x in r))
prova(f"accesi = claude (era {crew.accesi()})", crew.accesi() == ["claude"])

# allineato = solo gli accesi: le regole spente non mancano, Claude acceso sì
prova("spento non manca", not crew.Esito("regole comuni", False).manca)
prova("spento proposto", crew.Esito("regole comuni", False).proposto)
prova("acceso manca", crew.Esito("Claude Code", False).manca)
prova("fisso resta obbligatorio", crew.Esito("git", False).manca)

codice, _ = lancia("accendi", "crew", "--json")
prova(f"accendi crew con Claude → 0 (era {codice})", codice == 0)
codice, r = lancia("spegni", "claude", "--json")
prova(f"spegni claude con le regole accese → 3 (era {codice})", codice == 3 and r and r[-1].get("mancano") == ["crew"])

# comando: spegni toglie il comando, la copia di crew.py (per `auto`) resta
lancia("accendi", "comando", "--json")
lanc = os.path.join(crew.BIN, crew.NOME_CLI + (".cmd" if crew.WIN else ""))
prova("accendi comando: c'è il comando", os.path.isfile(lanc))
codice, r = lancia("spegni", "comando", "--json")
prova(f"spegni comando → 0 (era {codice})", codice == 0)
prova("spegni comando: comando tolto", not os.path.isfile(lanc))
prova("spegni comando: crew.py resta per `auto`", os.path.isfile(os.path.join(crew.CARTELLA, "crew.py")))
prova("spegni comando: tolto dagli accesi", "comando" not in crew.accesi())

# spegni Claude: le regole prima; Claude Code resta e lo dice
lancia("spegni", "crew", "--json")
prova("spegni crew: plugin regole tolto", ("claude", "plugin", "uninstall", "regole@claude-crew") in chiamate)
codice, r = lancia("spegni", "claude", "--json")
prova(f"spegni claude → 0 (era {codice})", codice == 0)
prova("spegni claude: dice che Claude Code resta", any("resta" in x.get("testo", "") for x in r))
prova("spegni claude: il programma c'è ancora", "claude" in programmi)
prova("niente acceso", crew.accesi() == [])
prova("spento: la guida non lo rifà", crew.spento("crew") and crew.spento("talk") and not crew.spento("git"))
prova("passi fissi mai spenti (la guida fa profilo e sistema)", not crew.spento("") and not crew.spento("sistema"))
prova("progetti spenti: solo proposti", crew.livello_di(crew.PASSI_ID["progetti"]) == "facoltativo")

# id sbagliati
for x in ("niente", "progetto:", "progetto:senza-barra"):
    prova(f"accendi {x} → 2", lancia("accendi", x, "--json")[0] == 2)

for m in male:
    print("test_interruttori: " + m, file=sys.stderr)
sys.exit(1 if male else 0)
