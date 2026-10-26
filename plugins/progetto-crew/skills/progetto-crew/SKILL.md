---
name: progetto-crew
description: Solo per i progetti fatti insieme dalla crew - portare avanti un progetto che tocca più settori (es. server + sito + negozio online + campagna SEO + video promozionale) con una sola identità coerente in ogni pezzo - scheda di progetto, piano per settori, consegne tra le skill, controllo di coerenza, lezioni a fine progetto. Usala quando l'utente dice "progetto della crew", "progetto insieme", "lanciamo X insieme", "facciamo sito e video per il nostro progetto", "progetto per un cliente", "proponiamo a un negozio", o quando c'è un progetto.md nella cartella. Anche per progetti per clienti esterni (piccole attività): demo, pilota, proposta, consegna.
---

# Progetto con più settori

Scopo: ogni pezzo (server, sito, negozio, campagna, video) nasce dalle stesse scelte e si incastra con gli altri.
Le scelte stanno in un posto solo: `progetto.md` nella cartella del progetto.

## Prima di tutto chiedi
- La cartella o il repo del progetto (lì va `progetto.md`) e chi ci lavora.
- C'è già `progetto.md`? Leggilo e continua da lì, non rifarlo.
- Quali pezzi devono uscire alla fine, ed entro quando.

## 1. Scheda
- Copia `scheda.md` (accanto a questa skill) in `<progetto>/progetto.md` e compilala con l'utente, con domande a
  scelta dove si può. Quello che non sa ancora va in "Da decidere" e diventa il primo passo del piano.
- La scheda è la sola fonte: nome, colori, font, tono, indirizzi non si ricopiano in altri file, si citano.
- Mai password, chiavi o dati personali nella scheda: la leggono tutti quelli del progetto.

## 2. Piano per settori
- Per ogni pezzo: settore, skill della crew che lo copre (elenco dei plugin), chi lo fa, cosa gli serve, cosa
  consegna. Scrivilo nella tabella "Pezzi e piano" della scheda.
- Prima i pezzi da cui dipendono gli altri: identità (logo, palette, font, testi base) → sito e negozio →
  contenuti (video, post, SEO) → lancio.
- Settore senza skill nella crew: dillo, lavora con le regole comuni e annota i passi; a fine progetto diventano
  una skill (`condividi-skill`).

## 3. Consegne tra settori
- Ogni consegna va in `<progetto>/consegne/<settore>/` con un nome chiaro, e una riga nella tabella "Consegne".
- Chi riceve legge la scheda e la consegna e non rifà la scelta: il video usa logo e palette di `grafica`, il sito
  usa i testi già approvati.
- Una scelta che cambia (un colore, il nome) si cambia nella scheda, in "Decisioni" con data e perché; poi elenca
  i pezzi già fatti da aggiornare.

## 4. Controllo di coerenza
Prima di dire "fatto" su un pezzo, e di nuovo a fine progetto:
- nome, logo, colori, font, tono e link uguali alla scheda in ogni pezzo (sito, negozio, video, post, server);
- le consegne usate sono l'ultima versione;
- ogni pezzo provato davvero: sito aperto, video guardato fino in fondo, server che risponde.

## 5. Fine progetto: cosa abbiamo imparato
- Rivedi con l'utente cosa è andato storto o è stato lento: ogni problema non ovvio → `annota-lezione`; ogni
  sequenza di passi nuova e riutilizzabile → una skill nuova o migliorata (`condividi-skill`).
- Così il prossimo progetto parte già da qui.

## Progetto per un cliente esterno (negozio, bar, studio)
Quando il progetto è per un'attività che paga o prova il nostro lavoro, oltre ai passi sopra:
- **Prima del sì**: il problema detto dal cliente con parole sue, chi userà la cosa, orari di apertura, hardware e
  rete che ha già. Meglio una demo con il suo nome e dati finti che una presentazione.
- **Si parte in piccolo**: un pilota con durata, cosa è incluso e cosa no scritti in una pagina, anche se gratis.
- **Proposta scritta**: cosa è incluso ed escluso, tempi, costo una tantum e mensile, assistenza (canale, orari,
  tempi di risposta), cosa succede ai dati a fine rapporto (export). Il primo modello lo rivede un commercialista o
  un legale; la forma per incassare si decide con il commercialista prima del primo incasso.
- **Account a nome del cliente** (dominio, profilo Google, fornitori, app): lui è proprietario, la crew ha accesso
  delegato. Credenziali solo in un gestore password condiviso, mai in chat o nella scheda.
- **Dati personali** dei suoi clienti o dipendenti: accordo GDPR per il trattamento, dati in UE, mai nei test o
  nelle demo.
- **Fisco** (fattura elettronica, registratore telematico): solo tramite un fornitore abilitato, mai rifatto da noi.
- **Consegna**: backup attivo e ripristino provato, guida di una pagina, 15 minuti di formazione, versione taggata
  per tornare indietro.
- **Dopo**: aggiornamenti a negozio chiuso e prima su un solo dispositivo; ogni richiesta di assistenza che rivela un
  errore → `annota-lezione`.

## Insidie con i clienti
- Lavoro che non finisce mai → "già che ci sei" accettato a voce → ogni cosa fuori dalla proposta è una richiesta
  nuova, con tempi e costo.
- Cliente bloccato o crew bloccata → dominio o account registrati a nome di uno di noi → sempre a nome del cliente.
- Pagamento che non arriva → lavoro iniziato senza nulla di scritto → proposta accettata per iscritto (anche una
  mail) prima di iniziare.
- Prodotto che non serve → costruito prima di parlare con chi lo usa → prima demo e pilota, poi il prodotto.
