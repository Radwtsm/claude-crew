"""L'attività di Windows parte anche a batteria, dopo uno standby, all'accesso, e un giro appeso non blocca gli altri
(i default di `schtasks /SC MINUTE` lasciavano un PC indietro, 02/11); il log dell'attività tiene i giri di prima.
Uso: python3 tools/test_pianifica.py  (su ogni sistema: solo XML e file in una cartella finta)"""
import os, sys, tempfile, xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import crew  # noqa: E402

male = []
x = crew.xml_attivita(r"C:\Python312\pythonw.exe", r'"C:\Users\a & b\.crew\crew.py" auto --leggero')
n = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
t = ET.fromstring(x.split("?>", 1)[1])
voluto = {"DisallowStartIfOnBatteries": "false", "StopIfGoingOnBatteries": "false", "StartWhenAvailable": "true",
          "MultipleInstancesPolicy": "IgnoreNew", "ExecutionTimeLimit": "PT20M"}
for k, v in voluto.items():
    e = t.find(f"t:Settings/t:{k}", n)
    if e is None or e.text != v:
        male.append(f"Settings/{k} = {None if e is None else e.text}, voluto {v}")
if t.find("t:Triggers/t:LogonTrigger", n) is None:
    male.append("manca il trigger all'accesso")
if t.find("t:Triggers/t:TimeTrigger/t:Repetition/t:Interval", n).text != "PT5M":
    male.append("non ogni 5 minuti")
if t.find("t:Actions/t:Exec/t:Arguments", n).text != r'"C:\Users\a & b\.crew\crew.py" auto --leggero':
    male.append("argomenti cambiati (& non scappato?)")

crew.LOG_PIANO = os.path.join(tempfile.mkdtemp(), "pianificato.log")
for giro in ("primo giro: errore", "secondo giro"):
    f = crew.log_pianificato()
    f.write(giro + "\n")
    f.close()
if "primo giro: errore" not in open(crew.LOG_PIANO, encoding="utf-8").read():
    male.append("il log del giro dopo cancella quello prima")
with open(crew.LOG_PIANO, "a", encoding="utf-8") as f:
    f.write("x" * 300_000)
crew.log_pianificato().close()
if os.path.getsize(crew.LOG_PIANO) > 150_000:
    male.append("il log non si accorcia oltre 200 kB")

print("\n".join(f"✗ {m}" for m in male) or "✓ test_pianifica")
sys.exit(1 if male else 0)
