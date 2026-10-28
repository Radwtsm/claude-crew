# Buone pratiche (crew)

Come usare bene Claude, per chi inizia e per il Claude che lo aiuta. Claude lo dice in una riga «💡 Meglio: …» solo
quando vede una di queste cose, una volta per tema; se la persona sceglie diversamente, è una sua scelta.

## Le regole d'uso (da spiegare a chi inizia, in 1 minuto)
1. **Un argomento per conversazione**: finito, scrivi `/clear` (Claude ti lascia una riga per ripartire).
2. **Frasi brevi e precise**: cosa vuoi ottenere, non come farlo; «sì», «1» bastano per rispondere a una domanda.
3. **Mai password, codici o chiavi in chat**: Claude ti fa scrivere i segreti in un comando che li chiede.
4. **Di un errore, solo la parte che conta** (o una foto dello schermo), non pagine di log.
5. **Lavora nella cartella del progetto**: lì Claude ha regole e strumenti giusti per quel lavoro.
6. **Prima di un'azione che non si annulla** (cancellare, inviare, pubblicare) Claude chiede: rispondi pensandoci.

## Cattive pratiche → cosa fare invece
| Cosa succede | Perché costa | Meglio |
|---|---|---|
| Più argomenti nello stesso messaggio o conversazione | contesto lungo: risposte peggiori e più token | un argomento, poi `/clear` |
| Log o file interi incollati | migliaia di token per poche righe utili | l'errore, o il percorso del file |
| Password o token in chat | finiscono nei log, vanno cambiati | comando che li chiede, gestore password |
| Chiedere di saltare un controllo (`--no-verify`, test) | l'errore arriva agli altri | correggere ciò che il controllo segnala |
| La stessa cosa fatta a mano per la seconda volta | si ripeterà ancora | uno script o una skill |
| Chiedere "fai tutto" senza dire cosa serve | Claude indovina, si rifà | lo scopo in una riga e cosa deve venire fuori |
| Lavorare fuori dalla cartella del progetto | mancano regole e strumenti | aprire Claude nel progetto |
| File di lavoro su Desktop o Download | si perdono, non li vede nessuno | la cartella del progetto o dello studio |
