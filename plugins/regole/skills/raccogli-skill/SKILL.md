---
name: raccogli-skill
description: Inventario di tutti gli strumenti dell'utente (skill, comandi, plugin, MCP, hook, lezioni) in ogni progetto, confronto con Pleyades e condivisione di quelli utili, senza doppioni. Usala per "raccogli le mie skill", "porta tutto in Pleyades", "cosa posso condividere".
---

# Raccogli le skill in Pleyades

Obiettivo: nessuna skill utile resta chiusa in un solo progetto, e Pleyades non ha doppioni. Le regole su come si
scrive in Pleyades sono nel `CLAUDE.md` della libreria: leggilo prima di scrivere.

## 1. Allinea
- Ultima versione di Pleyades: `git pull --ff-only` nel clone, oppure
  `claude plugin marketplace update claude-crew`. Leggi l'elenco dei plugin (`.claude-plugin/marketplace.json`).

## 2. Inventario completo (tutte le fonti, non solo il progetto aperto)
- Claude Code: `~/.claude/skills/*/SKILL.md`, `~/.claude/commands/*.md`, i plugin installati che non sono della
  Pleyades (`claude plugin list`).
- Ogni progetto sul computer: cerca `.claude/skills/*/SKILL.md` e `.claude/commands/*.md` nelle cartelle di lavoro
  dell'utente (chiedigli dove tiene i progetti; salta `node_modules`, `.git`, cache).
- Procedure riutilizzabili scritte nei `CLAUDE.md` (personale e dei progetti): passi ripetibili che potrebbero
  diventare una skill.
- App Claude / Cowork: le skill in Personalizza → Skill (se non vedi i file, chiedi all'utente di scaricarle).
- Plugin di terzi: `claude plugin list` (quelli non di Pleyades); nell'app Personalizza → Plugin.
- Server MCP: `claude mcp list`, i file `.mcp.json` dei progetti; nell'app i connettori personalizzati.
- Hook: la chiave `hooks` in `~/.claude/settings.json` e in `.claude/settings.json` di ogni progetto.
- Lezioni: problemi risolti scritti nei `CLAUDE.md`, nelle note o nella memoria (sintomo → causa → soluzione).

## 3. Confronta e classifica
Per ognuna: **già in Pleyades** (uguale / Pleyades è più vecchia → proposta di aggiornamento) · **generica** (utile
ad altri → candidata) · **specifica** (macchine, account, progetti suoi → resta privata; se ha una parte generica,
proponi di estrarla) · **doppione** di un'altra (sua o di Pleyades → da unire in una sola).

## 4. Fai scegliere
Mostra una tabella breve (nome, tipo, cosa faresti) e chiedi con una domanda a scelta multipla quali portare.
Niente senza il suo sì.

## 5. Scrivi
Per ogni scelta: pulisci (vedi `CLAUDE.md`), unisci i doppioni in una skill sola, scrivi seguendo la struttura del
`CLAUDE.md` (sezioni "Strumenti: tutti qui" per plugin, MCP e hook; "Lezioni" per i problemi risolti).
Senza accesso alla libreria: usa `condividi-skill` (fork e pull request, o zip).
La skill privata originale non la cancelli:
se l'utente vuole, dopo la pubblicazione la sostituisce col plugin di Pleyades.

## 6. Riepilogo
Elenco di cosa è entrato in Pleyades, cosa è rimasto privato e perché, e cosa installare per usarle.
