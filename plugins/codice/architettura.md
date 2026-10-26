# Architettura

Regole comuni della crew (plugin `codice`). Le regole tue e il CLAUDE.md del progetto vincono dove sono più precise.

## Ricostruibile
- Tutto ciò che non è dato vive in un repo (config, unit, cron, policy, versioni fissate + hash) con un check che
  segnala le differenze. Una modifica manuale su un host non è finita finché non è nel repo.
- Niente lock-in a una macchina, un provider o un fornitore: ogni servizio esterno è un pezzo sostituibile, mai
  l'unica copia di qualcosa.
- Dati su hardware proprio o cifrati prima che escano.

## Una casa per ogni cosa
- Una sola implementazione per ogni comando/logica; i client (scorciatoie, domotica, app) la chiamano e restano
  allineati, con un check che segnala la deriva.
- Uno script nuovo arriva con i suoi punti d'accesso nello stesso task.
- Le app che fanno la stessa cosa su più piattaforme condividono un kit comune; una funzione o un fix su una va
  sull'altra nello stesso task (o in una voce di backlog subito).
- Più app dello stesso proprietario = un unico ecosistema: stesse parole, icone, flussi; un hub che le collega.
- Spec + convenzioni della piattaforma (es. HIG) = una sola fonte di verità per ogni schermata, inclusa la
  navigazione (cosa sta in alto, sheet vs push), non solo lo stile.
- Liste che possono crescere a centinaia di elementi: ricerca/filtro fin dall'inizio.

## Accesso e sicurezza
- Pannelli admin, sblocchi, SSH, domotica: raggiungibili solo dai dispositivi del proprietario (rete privata, chiavi
  in un chip, niente di pubblico). Mai allargare l'accesso per comodità.
- Preferire soluzioni a chiavi/permessi a nuove password.

## Affidabilità
- I servizi critici restano su: ogni modifica che può fermarli ha un piano di ritorno (watchdog, riavvio automatico,
  rollback) e si verifica che rispondano dopo.
- Prima di ricostruire un servizio, tagga la versione in esecuzione per poter tornare indietro.
- Un dato che deve esserci sempre non dipende da un servizio che può essere spento o bloccato.
- Una modifica non toglie mai progressi o dati all'utente: ciò che passava la vecchia regola continua a passarla;
  prima di rilasciare confronta i conteggi vecchio/nuovo sui dati reali (solo conteggi).
- Parser di log/formati di terzi: dopo un aggiornamento del terzo, verifica che trovino ancora qualcosa (un parser
  che non trova nulla fallisce in silenzio).

## Avvisi
- Un avviso = un problema reale o un'azione del proprietario. Controlla lo stato "occupato/manutenzione", richiede
  che il problema persista, dice cosa fare. Un caso gestito non stampa parole che un monitor legge come errore.
