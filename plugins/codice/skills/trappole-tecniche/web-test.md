# Trappole: Web e test end-to-end

Letto da `SKILL.md` prima di: Playwright, screenshot, layout (CLS), Node, JS generato da Python, WebKit.

- Stringhe JS dentro stringhe Python non-raw: `\n` diventa un a capo vero; verifica il JS estratto con `node --check`.
- Chrome headless non scende sotto 500 px di larghezza: uno screenshot a 414 è solo ritagliato (sembra un overflow).
  Misura `innerWidth` prima di giudicare un layout da telefono, o usa l'emulazione del dispositivo.
- Test di posizione con la rotella (Playwright `mouse.wheel`) rosso solo ogni tanto: lo scorrimento è animato e
  finisce dopo il clic → prima del clic aspetta che `scrollY` sia fermo per due frame e misura tutto in un solo
  `evaluate`.
- Screenshot di riferimento vecchio e test verde lo stesso: una tolleranza dell'1% di pixel non vede un'etichetta
  cambiata → dopo una modifica voluta alla UI rigenera i riferimenti e guardali; i testi li controllano le asserzioni.
- Node `execFileSync` con output binario grande (es. screenshot via `adb exec-out screencap`): `ENOBUFS` oltre il
  milione di byte di default → `maxBuffer` grande.
- Salto della pagina (CLS) all'apertura: ciò che sta sotto un contenuto caricato dopo viene spinto giù → compare
  solo con i dati (`hidden` finché non c'è) o ha lo spazio riservato; trova chi si sposta con le `sources` delle
  `layout-shift`, non a occhio.
- Script Node che su Windows non fa niente ed esce con 0 (il controllo sembra passato): la guardia
  `` import.meta.url === `file://${process.argv[1]}` `` non è mai vera con `C:\…` → confronta con
  `pathToFileURL(process.argv[1]).href` (da `node:url`).
- WebKit (Safari, WKWebView, Playwright WebKit) con le impostazioni di serie: Tab salta gli elementi `<a>`, quindi
  un test di tastiera è rosso solo lì → ciò che deve essere raggiungibile con Tab è un `<button>` (o un campo).
