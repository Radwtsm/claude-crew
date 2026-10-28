---
name: ripara-allineamento
description: Trova e sistema perché un computer della squadra non è all'ultima versione (pleyades-cli, plugin, progetto). Usala quando l'avvio dice «Squadra non allineata» o «da sistemare», per "sono indietro", "non mi arrivano gli aggiornamenti", "squadra rossa".
---

# Ripara l'allineamento

Ogni computer acceso si allinea da solo entro ~5 minuti da un push: qui si ripara quando non succede. Lavora sul
computer di chi è indietro, con il suo Claude. Prima la diagnosi, poi le correzioni con l'ok dell'utente (domanda a
crocette).

## Come funziona (per capire dove si rompe)
1. **Attività pianificata** (launchd sul Mac, Utilità di pianificazione su Windows «Pleyades tools», cron su Linux):
   ogni 5 minuti `pleyades-cli auto --leggero`, anche con Claude chiuso: pochi `git ls-remote`; c'è un commit nuovo
   (crew.py, progetto, plugin) → il giro intero. `auto` rimette l'attività da sola. Un solo giro alla volta.
2. **Avvio di Claude**: l'hook del plugin `regole` lancia lo stesso `auto` in background.
3. `auto` = `aggiorna` (crew.py da GitHub, cataloghi, `claude plugin update` di ogni plugin, `git pull` dei
   progetti) + `controlla --talk` (il resoconto 🔎 nella stanza, solo se è cambiato) + `squadra`.
4. **Sessione aperta**: i plugin nuovi valgono dalla sessione dopo; l'hook lo dice a Claude una volta.
5. `pleyades-cli squadra` confronta l'ultimo 🔎 di ognuno con l'ultima versione pubblicata: rosso = diverso,
   meno di tutti i controlli a posto, o resoconto di più di 7 giorni.

## Diagnosi: un comando
```
pleyades-cli diagnosi
```
Non cambia niente. Elenca versioni contro le ultime, esito dell'ultimo `auto` con le righe del suo log, modifiche non
pubblicate, cataloghi, stanza. Ogni ✗ ha già il comando che lo sistema: segui quello.

## Comandi
| Cosa | Comando |
|---|---|
| Tutto all'ultima versione, adesso | `pleyades-cli aggiorna` |
| Rifare il giro automatico subito | `pleyades-cli auto --subito` |
| Il resoconto nella stanza (vecchio) | `pleyades-cli controlla --talk` |
| Chi della squadra è allineato | `pleyades-cli squadra` |
| Rimettere l'attività pianificata | `pleyades-cli pianifica` (togli: `--togli`) |
| Un plugin fermo | `claude plugin marketplace update NOME-MARKETPLACE` poi `claude plugin update PLUGIN@MARKETPLACE` |
| Log | `~/.crew/auto.log` (avvio di Claude), `~/.crew/pianificato.log` (attività) — Windows: `%USERPROFILE%\.crew\` |
| Stato | `~/.config/crew/stato.json` (`auto.esito`, `squadra`) |

Dopo ogni aggiornamento dei plugin: chiudi e riapri Claude (`/clear` non basta).

## Sintomo → causa → cosa fare
- `progetto=abc1234*` → modifiche o commit non pubblicati → `git status`, commit + push (prima `git pull --rebase`).
  Push rifiutato da `check.sh` → leggi il suo messaggio e correggi il file, mai `--no-verify`.
- Rosso ma `diagnosi` tutto ✓ → il 🔎 nella stanza è vecchio → `pleyades-cli controlla --talk`.
- «mai controllato» → nella stanza ma senza 🔎 → `pleyades-cli controlla --talk` dalla cartella del progetto
  (o `pleyades-cli entra PROPRIETARIO/REPO` se non è ancora entrato).
- «accesso a Claude» ✗ ma il login è riuscito → `claude auth status` nello stesso terminale: se dice logged in,
  pleyades-cli è vecchio (`aggiorna`); se no il login era in un altro programma (app desktop ≠ Claude Code).
- `auto` «mai partito» → manca il plugin `regole` o il suo hook non trova python → `pleyades-cli controlla`;
  Windows: `python --version` deve rispondere (non lo Store).
- `auto` «interrotto» o «da sistemare: …» → le righe di log in `diagnosi` dicono quale passo; rilancia quel passo a
  mano e leggi l'errore intero.
- Attività pianificata ✗ → `pleyades-cli pianifica` e leggi il suo errore. Computer di lavoro: niente attività
  (profilo «lavoro»), è voluto.

## Insidie
- Push di pochi minuti fa e `aggiorna` porta ancora il vecchio crew.py → GitHub serve la copia in cache per ~5 minuti
  → aspetta e rilancia, non toccare i file a mano.
- Windows, limiti in byte di `check.sh` sforati solo lì → gli a capo CRLF contano doppio → si corregge il conteggio
  alla fonte, non accorciando il file.
- Plugin aggiornato ma regole o skill vecchie → la sessione aperta usa i file con cui è partita → riavvia Claude.
- Un solo computer sistemato a mano (copiando file, cambiando settings.json) → al giro dopo torna come prima →
  correggi alla fonte (crew.py, il repo del progetto) e pubblica: arriva a tutti.

## Se non si risolve
Scrivi nella stanza del progetto (talk.py del progetto) cosa dice `pleyades-cli diagnosi`, solo le righe ✗, mai
password o codici. Problema nuovo risolto → una riga in «Insidie» qui (`annota-lezione`).
