---
name: condividi-skill
description: Mandare una skill (o una regola) alla libreria di Pleyades. Usala quando l'utente dice "aggiungi a Pleyades", "condividi questa skill", "manda a Pleyades", "aggiungila per gli amici", o quando una skill fatta insieme sembra utile anche agli altri.
---

# Condividi una skill con Pleyades

La libreria comune è pubblica (repo `Radwtsm/claude-crew`): tutto quello che ci entra lo può leggere chiunque.

## 1. Trova la skill
- Più skill o "tutte le mie": usa prima `raccogli-skill` (inventario completo). Una skill privata dell'utente: in Claude Code `~/.claude/skills/<nome>/`; nell'app, se non vedi i suoi file,
  chiedigli di scaricarla da Personalizza → Skill e di dartela.
- Solo un'idea o delle note: scrivi tu la skill con lui e fagliela rileggere.

## 2. Pulisci (obbligatorio)
Togli, chiedendo conferma all'utente: password, token, chiavi; IP, nomi di PC o server, percorsi del suo computer,
URL privati; nomi, email, account, dati di persone; preferenze solo sue (tono, come vuole essere chiamato): quelle
restano nelle sue regole personali.

## 3. Invia
- **Hai un clone del repo di Pleyades** (sei collaboratore): `git pull --ff-only`, leggi il suo `CLAUDE.md`, scrivi
  la skill seguendolo, `sh check.sh`, commit e push.
- **Altrimenti**: crea `<nome>.zip` con dentro la cartella della skill (`<nome>/SKILL.md`), salvalo sul Desktop
  (nell'app: come file da scaricare) e di' all'utente di mandarlo in chat a un manutentore di Pleyades.

Dopo la pubblicazione arriva a tutti con la sincronizzazione dei plugin.
