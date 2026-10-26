---
name: indesign-script
description: Costruire un impaginato InDesign (magazine, libro, brochure) da uno script ExtendScript lanciato da Claude, con griglia, stili, immagini ed esportazione PDF ripetibili. Usala quando l'utente dice "impagina in InDesign", "fammi le pagine del magazine", "esporta il PDF con la griglia", "script per InDesign", o quando uno script InDesign dà "L'utente ha interrotto questa operazione", caratteri strani tipo "âœ" o immagini tagliate nel PDF.
---

# Impaginati InDesign da script

Regole imparate impaginando un articolo di magazine con InDesign 2025 su Windows, pilotato da Claude via COM.
Legenda: ✅ verificato · ⚠️ da verificare nella propria versione.

## Prima di tutto chiedi
- Versione di InDesign e sistema (su Mac si lancia con AppleScript `do script`, non COM ⚠️).
- Formato pagina, numero di pagine, font richiesti (controlla che siano attivi: `app.fonts`).
- Cosa consegnare: PDF finale, PDF con griglia, il file `.indd`.
- Non toccare documenti già aperti dell'utente: lo script lavora solo sul documento che crea.

## Lanciare lo script ✅
Da PowerShell (`1246973031` = JavaScript):
```
(New-Object -ComObject InDesign.Application.2025).DoScript("<percorso>\script.jsx", 1246973031)
```
- Restituisce il valore dell'ultima espressione dello script: usalo come rapporto (testo in eccesso, righe per
  cornice).
- Un errore arriva come "NullReferenceException" senza dettagli: lancia lo script tramite un piccolo `.jsx` che
  fa `$.evalFile(File(...))` dentro `try/catch` e restituisce `e + " @line " + e.line`.
- Per controllare il risultato esporta anche JPG delle doppie pagine a 60 ppi e guardali, o renderizza il PDF.

## Impostazioni che servono
- `app.scriptPreferences.measurementUnit = MeasurementUnits.MILLIMETERS` per la geometria; corpi e interlinee
  scritti come stringhe con unità (`"9.5pt"`), così non dipendono dall'unità.
- `documentPreferences.startPageNumber = 2` fa partire da una pagina sinistra: doppie pagine 2-3, 4-5…
- Griglia sulla linea di base: `baselineStart` = margine superiore + una interlinea, relativa alla pagina;
  spazio tra colonne = una interlinea, righe di modulo di N linee + 1 di spazio (es. 6×9 + 5 = 59 linee).
- Stili di paragrafo e di carattere per tutto (niente formattazione a mano), `alignToBaseline` sul corpo,
  didascalie con solo la prima riga sulla griglia (`gridAlignFirstLineOnly`).

## Trappole ✅
- `exportFile` PDF lanciato via COM si ferma con "L'utente ha interrotto questa operazione" → esporta con
  `doc.asynchronousExportFile(ExportFormat.PDF_TYPE, file, false).waitForTask()`.
- Caratteri speciali nel `.jsx` escono come "âœ" (il file è letto come Latin-1) → tieni il `.jsx` solo ASCII e
  scrivi `“`, `ü` ecc.; il testo lungo leggilo da un file con `f.encoding = "UTF-8"`.
- `graphic.move()` in orizzontale su una pagina **destra** di un documento a pagine affiancate: le coordinate
  lette sono giuste ma nel PDF l'immagine è ritagliata a una striscia → `fit(FitOptions.FILL_PROPORTIONALLY)` poi
  `fit(FitOptions.CENTER_CONTENT)`; spostamenti solo in verticale o su pagine sinistre.
- La griglia e le guide non finiscono nel PDF (`exportGuidesAndGrids` non basta) → disegna la griglia come
  oggetti (moduli con trasparenza, linee di base, margini) su un livello "Griglia" nel mastro, in cima ai livelli;
  livello nascosto per il PDF finale, visibile per il PDF con griglia.
- `app.documents.add(false)` crea il documento senza finestra e lo lascia aperto: il `.indd` resta bloccato →
  a fine script `doc.close(SaveOptions.YES)`; all'inizio chiudi un'eventuale copia rimasta aperta con lo stesso
  nome.
- `pdfExportPreferences` vale solo se esporti **senza** passare un preset: con il preset le tue impostazioni
  (es. `exportReaderSpreads`) vengono ignorate ⚠️.

## Checklist prima di consegnare
- Rapporto dello script: nessun testo in eccesso (`story.overflows == false`), nessuna cornice vuota.
- Guarda ogni doppia pagina renderizzata: immagini intere e ben ritagliate, citazioni con virgolette giuste.
- Elenco dei font incorporati nel PDF = solo quelli richiesti.
- Immagini sotto ~250 ppi alla misura stampata: dillo (ok a schermo, non per la stampa).
- Salva lo script accanto al progetto, così il PDF si rigenera.
