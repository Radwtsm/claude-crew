# Trappole: Modifiche al codice

Letto da `SKILL.md` prima di: rinomine, spostamenti, rimozioni in blocco, Swift, formati cifrati.

- Swift `URLSession.AsyncBytes.lines` scarta le righe vuote: mai per SSE o protocolli dove la riga vuota conta.
- "Cifrato?" non si decide dai magic byte: controlla oltre l'header.
- Rinominare o spostare un'impostazione salvata (chiave, dominio, bundle ID): cerca la chiave anche negli script.
- Spostare un tipo in un altro modulo: cerca ogni file che lo usa e aggiungi l'import; poi build completa.
- Rimozioni in blocco da script: dopo, controlla il diff per dichiarazioni tolte che non erano nel bersaglio.
- Strumenti di "codice inutilizzato" = lista da verificare, non da cancellare; build + test dopo ogni lotto.
- `re.sub` con un percorso Windows nel testo di sostituzione (`~\agenzia`) → `\a` diventa un carattere speciale
  → passa una funzione come sostituzione (`lambda _: testo`).
