# Riuso per il team (Pleyades)

Regole comuni di Pleyades (skill `regole-crew`), lette quando servono; le regole personali vincono dove dicono altro.
Scopo: quello che uno costruisce si collega a quello degli altri, invece di restare un pezzo a sé.

## Quando avvisare
Prima di creare (o mentre l'utente crea) una struttura, uno script, una skill, un formato o un'app, controlla se:
- **esiste già** qualcosa che fa la stessa cosa nel team (`grep -ril <tema>` nei repo, skill e strumenti di
  Pleyades, schede in `persone/`): allora si estende quello, non se ne fa un secondo;
- **servirebbe anche ad altri** (stesso problema in un altro mestiere, progetto o sistema): allora va fatto generico;
- **è legato a una persona o a un computer** (percorsi, nomi, utenti, colori o testi scritti nel codice): allora
  quei pezzi diventano dati o impostazioni;
- **una piattaforma sola** quando il team ne usa due (Mac e Windows): allora la parte comune sta in un posto solo.

## Come avvisare
Una riga «💡 Più riusabile: …» con la versione comune (dove metterla, cosa diventa dato) e il costo in più in righe;
se l'utente sceglie comunque la sua strada è una scelta sua: annotala come debito nel backlog del progetto.

## La versione comune, di solito
- Logica in un posto (libreria, motore, script) e i client sottili sopra; formati condivisi documentati (JSON, md).
- Ciò che cambia da persona a persona = dati: scheda in `persone/`, ambiti, pacchetti (temi, intro, frasi).
- Si aggancia agli strumenti che ci sono: `pleyades-cli` per installare e aggiornare, Talk per avvisare chi serve,
  Proposte per le idee, i controlli (`check.sh`, lint) per non tornare indietro.
- Una cosa nuova arriva con il suo controllo e con la riga nell'indice che dice dove sta.
