---
name: annota-lezione
description: Trasformare un problema appena risolto in una lezione per tutta la crew, così nessuno ci ricasca. Usala subito dopo aver risolto un problema non ovvio - un errore strano, un comando o un'impostazione che non funzionava come sembrava, un tuo consiglio sbagliato, una soluzione trovata dopo vari tentativi - e quando l'utente dice "finalmente funziona", "era questo il problema", "ricordatelo", "segnatelo per la prossima volta".
---

# Annota una lezione

## 1. Vale la pena?
Sì se: ha richiesto più di un tentativo, la causa non era quella che sembrava, oppure capiterà ad altri (stesso
programma, stesso sistema). No se: un errore di battitura o un caso solo suo (account, file, macchina sua: quello
va nelle sue note personali).

## 2. Scrivila in una riga
`sintomo → causa → cosa fare`. Esempio: "Render Blender tutto nero → camera con clip_start 0,1 m in una scena
macro → clip_start 0.002". Niente nomi, percorsi o dati personali.

## 3. Mettila nel posto giusto
- C'è una skill della crew sul tema → nella sua sezione **Insidie** o **Trappole** (crea la sezione se manca, con
  una di queste parole nel titolo: così gli altri Claude la trovano cercando quelle parole).
- Programmazione, sistemi, strumenti in generale → plugin `codice`, skill `trappole-tecniche` (in fondo).
- Vale per qualunque lavoro → regole comuni (skill `regole-crew`, sezione "Imparare insieme").
- Nessuna skill sul tema e capiterà ancora → proponi una skill nuova (`condividi-skill`).
Prima cerca se la lezione c'è già: se sì, migliora quella riga.

## 4. Si può controllare con uno script?
Se l'errore si riconosce in automatico (un valore, un formato, un file), proponi anche un piccolo controllo nella
skill: una regola si dimentica, un controllo no.

## 5. Invia
Chiedi all'utente l'ok con la riga già scritta. Poi: accesso alla cartella condivisa → scrivila lì seguendo il suo
`CLAUDE.md`; altrimenti `condividi-skill`.
