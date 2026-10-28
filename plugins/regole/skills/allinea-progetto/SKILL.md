---
name: allinea-progetto
description: Allinea un progetto fra i Claude di più persone in 2-3 messaggi, per un task: ognuno porta solo i fatti del suo dominio che servono a quel task (es. server, codice). Usala per "allineiamoci", "allinea il progetto", "sincronizza con il suo Claude", "cosa deve sapere lui".
---

# Allinea il progetto

Ogni persona conosce bene un pezzo (il suo **dominio**); il suo Claude lo vede sul suo computer. Allinearsi = per **un
task preciso** (es. "gioco del labirinto", "primo setup"), ognuno scrive solo i fatti del suo dominio che servono a
quel task, poi i due Claude sistemano la struttura in pochi passaggi. Niente del resto del computer, niente voci che
il task non usa.

## Prima
`git pull --ff-only`, poi leggi `.claude/allineamento.md` del repo: chi ha quale dominio, cosa deve dire all'altro e
da dove lo prende. Non c'è? Proponilo all'utente (modello sotto), con un dominio per persona.

## Passi
1. **Il task**: quello chiesto dall'utente o dall'altro Claude, in una riga. Delle voci del tuo dominio elencate lì
   tieni solo quelle che servono a questo task (nel dubbio: no, l'altro può chiederla).
   **Raccogli** quelle, dal tuo computer, in sola lettura (file, comandi, API pubbliche). Mai segreti, indirizzi
   privati, dati personali, cose non elencate: se una voce li richiede, scrivi "chiedi a <persona>".
2. **Scrivi** `allineamento/<nickname>.md`: in testa `Task: …`, poi una riga per voce (`voce: valore · fonte ·
   data`), ≤ 2 KB; poi una sezione **Domande** per l'altro dominio (cosa ti serve sapere). Commit + push.
3. **Avvisa** sul canale del progetto (`.claude/allineamento.md` → Canale): una riga con il percorso.
4. **Chi riceve**: legge il file dell'altro, confronta con il suo dominio, risponde alle Domande nel suo file e
   sistema i documenti del suo campo (es. regole tecniche, struttura del codice). Ciò che è del campo dell'altro si
   propone, non si cambia.
5. **Chiudi** in 2-3 giri al massimo: una riga sul canale "allineati: cosa è cambiato, dove". Restano dubbi → una
   domanda alla persona, non un giro in più.

## Regole
- Un fatto in un posto solo: se esiste già un documento del progetto (es. `TECNICO.md`), aggiornalo e nel file di
  allineamento metti solo il rimando.
- Ogni voce ha la fonte e la data: un fatto vecchio si vede.
- Rifallo quando cambia qualcosa di grosso nel tuo dominio (versioni, struttura, regole).

## Modello di `.claude/allineamento.md`
```
Canale: <stanza Talk del repo (strumenti/talk.py) | commenti della pull request>
## <nickname> — dominio: <cosa sa>
- <voce che deve dire all'altro> · fonte: <dove la trova sul suo computer>
```

## Insidie
- Il file di allineamento diventa lungo → ci finiscono dati invece di fatti → solo ciò che l'altro usa davvero.
