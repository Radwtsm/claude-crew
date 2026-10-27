# After Effects: pannello che funziona su Windows e Mac

Letto da `SKILL.md` prima di toccare percorsi, font, scorciatoie o il pacchetto da distribuire.

- `getSystemPath("extension")` restituisce un URL: `file:///C:/...` su Windows, `file:///Library/...` su Mac.
  Togliere `"file:///"` rompe il Mac (resta `Library/...` senza barra): togli `file://` e poi solo la `/` davanti
  alla lettera di unità (`replace(/^\/([A-Za-z]:)/, "$1")`).
- Da percorso a URL per `<img>`: `C:\...` → `file:///C:/...`, `/Users/...` → `file:///Users/...`,
  `\\server\...` → `file://server/...`; codifica anche `#` e `?`. Provalo con un percorso per tipo.
- Font: Segoe UI e Consolas su Mac non esistono. Tieni gli id nei preset e su Mac sostituiscili con equivalenti di
  sistema usando i nomi PostScript che vuole AE (`HelveticaNeue-Bold`, `Menlo-Regular`). Presenti su entrambi:
  Arial, Georgia, Impact, Verdana, Trebuchet MS, Times New Roman, Courier New.
- Scorciatoie: controlla `e.ctrlKey || e.metaKey` e nei testi mostra ⌘ su Mac.
- Pacchetto da distribuire: uno script che copia **solo** un elenco di file consentiti in una cartella **fuori**
  dalla cartella del pannello (quella collegata alle estensioni verrebbe caricata da AE), e si ferma se trova
  percorsi utente, email o il nome utente del PC.
