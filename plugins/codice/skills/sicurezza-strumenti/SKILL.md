---
name: sicurezza-strumenti
description: Sicurezza degli strumenti che scrivi (CLI, script, installer): sola lettura imposta, accessi a tempo, modo prova, certificati fissati, aggiornamenti verificabili, config come dato, impostazioni di sistema. Usala prima di toccare credenziali, accessi o aggiornamenti.
---

# Sicurezza degli strumenti

Regole comuni di Pleyades (plugin `codice`), lette prima di toccare accessi, credenziali, aggiornamenti o
impostazioni di sistema. Uno strato più basso (tue regole, progetto) può solo stringerle; allentarle = proposta ai
manutentori.

- **Sola lettura imposta dal codice**: uno strumento che deve solo leggere non può scrivere. Lo limita il codice
  (solo richieste di lettura, credenziali senza permessi di scrittura), mai un commento o la buona volontà.
- **Accesso a tempo**: un accesso privilegiato (rete riservata, credenziali elevate) si apre solo per l'operazione e
  si chiude sempre, anche se fallisce (`try/finally`, `trap`).
- **Modo prova**: ogni comando con effetti mostra cosa farebbe senza farlo; comandi di lettura e con effetti
  separati e dichiarati come tali.
- **Certificati**: con un'autorità interna non riconosciuta si fissa l'impronta attesa, con la sua scadenza; mai
  spegnere la verifica.
- **Il tuo codice che si aggiorna da solo è codice di terzi per chi lo riceve**: versioni pubblicate e verificabili
  (impronta o firma), mai l'ultimo commit del ramo principale controllato solo perché è sintatticamente valido;
  aggiornamento esplicito o almeno annunciato.
- **I dati non diventano codice**: configurazione, aspetto o marchio forniti da un progetto restano dato
  dichiarativo (JSON, TOML), mai importati ed eseguiti; altrimenti chi scrive quel file controlla ogni computer che
  lo apre.
- **Impostazioni di sistema**: uno strumento comune non le cambia per estetica (temi, colori di sistema, attività
  pianificate frequenti): solo su richiesta, con un modo sicuro per tornare indietro, mai su macchine gestite da
  altri (computer di lavoro).
