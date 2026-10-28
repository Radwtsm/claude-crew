---
name: interfacce
description: Regole d'interfaccia di Pleyades per app e siti (azioni, menu, conferme, parole, icone, layout stabile, stile visivo). Usala prima di progettare, rivedere o cambiare una schermata, un menu o un flusso.
---

# Interfacce: le regole comuni di Pleyades

Valgono per app (Mac, iPhone, iPad, Windows) e siti. Le regole di un progetto (il suo DESIGN.md o simile) vincono
dove dicono altro; poi le convenzioni della piattaforma (skill `linee-guida-apple` per Apple).

## Azioni e menu
- **Un posto solo**: un'azione compare una volta per schermata; mai la stessa etichetta due volte nello stesso menu.
- **Ordine dei menu ⋯**: dalla più usata alla più rara, separatore, quella distruttiva per ultima (in rosso).
- **In barra solo il frequente**: ciò che si usa meno di una volta a settimana va nel menu ⋯.
- **Due modi di eliminare**: "Sposta nel Cestino" (recuperabile: la conferma dice dove recuperarlo) ed "Elimina
  definitivamente" (la conferma dice che non si annulla). La parola "Elimina" da sola non è un'etichetta.
- **Niente modalità "Seleziona" per un elemento solo**: pressione lunga (telefono) o clic destro (computer) danno le
  stesse azioni del menu ⋯ del dettaglio.
- **Avvia e dimentica**: un'operazione lunga parte, mostra il suo stato altrove (barra, notifica) e non blocca.

## Parole e icone
- **Stesse parole ovunque**: stessa etichetta su ogni piattaforma; "…" in fondo quando l'azione apre una finestra,
  un selettore o una conferma prima di fare qualcosa.
- **Un'icona per azione**, sempre la stessa (una tabella azione → icona nel progetto).
- **Nessuna parola tecnica interna** in ciò che vede l'utente (nomi di file, di server, sigle): un elenco di parole
  vietate nel progetto, controllato da un lint.

## Navigazione
- **Stessa mappa su ogni dispositivo**: le destinazioni principali sono le stesse e nello stesso ordine (barra in
  basso sul telefono, barra laterale su computer e tablet); ogni schermata a ≤ 2 tocchi dall'inizio.
- **Una cosa che c'è su una piattaforma sola** si scrive in un elenco col motivo.
- **Tornare al centro**: da ogni sezione o app della stessa famiglia un pulsante riporta alla pagina principale.
- **Sezioni senza dati**: un messaggio "in arrivo" chiaro, mai una schermata vuota.

## Layout stabile (niente salti)
- Spazi riservati per ciò che si carica (immagini, numeri, liste): niente che sposta il resto mentre arriva.
- Le parti fisse (titolo, barra, stato) restano ferme; scorre solo il contenuto. Al cambio di misura della
  finestra si ridisegna senza perdere il punto.
- Grafici nel tempo: stessi colori e scale in tutte le schermate.

## Stile visivo
- Base neutra (nero, grigio chiarissimo, bianco) e **un solo colore d'accento** per azioni e navigazione (ogni
  progetto il suo: Pleyades = azzurro stella).
- Tipografia stretta e curata; pochi pesi; testo leggibile (≥ 15-17 px su telefono, contrasto WCAG AA).
- Controlli a capsula o cerchio; raggi degli angoli a livelli (piccolo, medio, grande), non uno solo.
- Ombre e sfumature rare: la scena la fanno contenuti e immagini.
- Token (colori, spazi, raggi, caratteri) definiti una volta e usati ovunque. Dettagli: `riferimenti/sistema-apple.md`
  del plugin (aprilo solo se serve una misura precisa).

## Controllare, non solo scrivere
- Le regole che contano diventano un lint (parole vietate, etichette doppie, icone diverse per la stessa azione) che
  fallisce sulle violazioni nuove, agganciato al pre-commit.
- Prima di dire "fatto": schermata vera su ogni dispositivo previsto, anche stretta e in modalità scura.

## Insidie
- Stessa azione con due nomi in due schermate → l'utente non la ritrova → una tabella azione → etichetta → icona.
- Conferma che dice "Elimina?" anche quando si può recuperare → paura di usarla → testo diverso per i due casi.
- Contenuto che arriva e sposta i pulsanti → tocco sbagliato → spazio riservato prima del caricamento.
