---
name: configura-claude
description: Configura il Claude Code di un amico come quello del manutentore, su Mac o Windows: regole personali in repo privato, memoria unica, sincronizzazione, barra di stato, avviso di uso alto. Usala per "configura il mio Claude", "setup di Claude", "sincronizza le mie regole".
---

# Configurare il proprio Claude Code

Fa tutto lo script `personale.py` (accanto a questa skill, in `../../scripts/`); tu guidi, spieghi in breve e
chiedi solo le scelte. Struttura e strati: skill `organizza-claude`.

## Cosa ottiene l'utente
| Pezzo | Dove | Come resta aggiornato |
|---|---|---|
| Regole personali | `~/claude-personale/regole.md` (repo GitHub **privato**), importate da `~/.claude/CLAUDE.md` | hook: pull all'avvio, commit + push a fine risposta |
| Memoria unica | `~/claude-personale/memoria/`; ogni progetto vi punta (collegamento; su Windows una giunzione) | idem, e ogni progetto nuovo si collega all'avvio |
| Mappa di ogni PC | `~/claude-personale/mappa-<computer>.md`: md che Claude legge, skill, plugin, progetti, scarti dalla struttura comune | rifatta all'avvio, va nel repo col sync |
| Barra di stato | `settings.json` → `statusLine`: modello · contesto % · 5h/7g con reset · durata | arriva con il plugin `regole` |
| Avviso di uso alto | una riga a Claude quando 5h o 7g supera l'85%: chiude il passo e salva lo stato | idem |
| Plugin | `extraKnownMarketplaces` con `autoUpdate` per ogni marketplace GitHub installato | da soli all'avvio |
| Controllo | all'avvio: regole e `MEMORY.md` sotto i byte di `limiti-contesto.txt`; lint di Pleyades su skill e CLAUDE.md | hook |

## Passi
1. **Prima**: Pleyades tools installati (`INSTALLA.md`, almeno il plugin `regole`), `git --version`, `gh --version`
   (GitHub CLI dalla fonte ufficiale) e `gh auth login` fatto. Manca qualcosa → di' come installarlo e fermati.
2. **Setup** (Mac: `python3`; Windows: `python`, in Git Bash o PowerShell):
   `python3 ~/.claude/plugins/marketplaces/claude-crew/plugins/regole/scripts/personale.py setup`
   Crea o clona `claude-personale`, fa le copie `*.prima-di-configura` di CLAUDE.md e settings.json, unisce le
   memorie esistenti (copie `memory.prima-di-unire-*`, niente perso).
3. **Regole**: se `~/.claude/CLAUDE.md` aveva regole sue, spostale in `regole.md` con `organizza-claude` (stesse
   parole); poi chiedi all'utente le sezioni vuote di `regole.md` (chi è, come rispondere, cosa non fare mai).
4. **Verifica**: `personale.py controlla` → "tutto a posto"; riapri Claude Code (o `/reload-plugins`): la barra di
   stato compare, "che regole hai?" mostra le sue.
5. **Altro computer**: Pleyades + `gh auth login` + lo stesso `setup`: clona il repo invece di crearlo.

## Regole
- Il repo personale resta **privato**: mai regole personali, memoria o nomi in Pleyades.
- Mai togliere o riscrivere quello che l'utente ha già: solo aggiungere, con la copia di sicurezza prima.
- Barra di stato già presente: lasciala, chiedi se vuole quella di Pleyades.

## Insidie
- Barra di stato vuota dopo aver reinstallato Python → `statusLine` punta a un Python che non c'è più → rilancia
  `setup`.
- Windows, "python3" apre lo Store o non fa niente → è l'alias finto di Windows → usa `python` (gli hook lo fanno
  da soli con la seconda voce).
- Memoria di un progetto non condivisa → la cartella è nata a sessione aperta → si collega al prossimo avvio
  (o lancia `setup`).
