# Regole che funzionano

Letto quando si scrive o si cambia una regola, o si misura se le regole servono (skill `organizza-claude`).

## Ogni regola dichiara quattro cose
- **Livello**: Pleyades, personale o progetto (vedi «I tre strati»).
- **Chi la tiene**: chi può cambiarla; gli altri propongono.
- **Perché**: il motivo o l'errore da cui nasce, in una riga.
- **Come è imposta**: blocco automatico (hook, pre-commit, lint), test, revisione, o semplice consiglio. Un errore
  grave che si ripete sale di gradino: da consiglio a controllo automatico.

## Si misura se servono
- Contano gli errori ripetuti (le lezioni dello stesso tema) e il costo per attività (token, passaggi). Se non
  calano, la struttura delle regole non funziona: va cambiata, non allungata.

## Contesto a strati che invecchia da solo
- Mappa minima sempre caricata → schede per modulo lette a richiesta → note di dettaglio per parola chiave → il
  codice solo quando serve.
- Ogni scheda di un modulo porta il commit (o la data) del codice che descrive; un check la segna «vecchia» quando
  quel codice cambia dopo, così nessuno si fida di una scheda scaduta.
