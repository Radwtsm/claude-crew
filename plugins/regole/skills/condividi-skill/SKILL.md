---
name: condividi-skill
description: Mandare una skill (o una regola) alla libreria della crew. Usala quando l'utente dice "condividi questa skill", "manda alla crew", "aggiungila per gli amici", o quando una skill fatta insieme sembra utile anche agli altri.
---

# Condividi una skill con la crew

La libreria comune è il repo pubblico `Radwtsm/claude-crew`: tutto quello che ci entra lo può leggere chiunque.

## 1. Prepara la skill
- Una cartella con il nome della skill (minuscole e trattini) e dentro `SKILL.md` con frontmatter `name` e
  `description` (cosa fa + quando usarla, in italiano).
- Se l'utente ha solo un'idea o delle note, scrivi tu la skill con lui e fagliela rileggere.

## 2. Pulisci (obbligatorio)
Rileggi ogni file e togli, chiedendo conferma all'utente:
- password, token, chiavi, codici; indirizzi IP, nomi di PC o server, percorsi del suo computer, URL privati;
- nomi, email, account, dati di persone;
- preferenze solo sue (tono, come vuole essere chiamato): restano nelle sue regole personali, non nella crew.
Gli script inclusi devono essere brevi e leggibili; niente file eseguibili o scaricati.

## 3. Invia
- **GitHub collegato** (`gh auth status` va a buon fine): fork di `Radwtsm/claude-crew`, poi
  `python3 tools/aggiungi.py <cartella> <categoria>`, `sh check.sh`, commit e PR con una riga su cosa fa.
  Dì all'utente il link della PR.
- **Altrimenti** (caso normale): crea `<nome>.zip` con dentro la cartella della skill, salvalo sul Desktop
  (nell'app: come file da scaricare) e dì all'utente di mandarlo in chat a chi gestisce la crew.

Chi gestisce la crew la rilegge per intero prima di metterla dentro; poi arriva a tutti con il prossimo
aggiornamento.
