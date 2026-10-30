# Installare e lanciare i test (stack web, Tauri, Playwright)

Vale per ogni app del team con Node e Playwright; i comandi esatti di un progetto stanno nel suo `package.json`.
Versioni fissate: `npm ci`, mai `npm install`.

## Una volta
1. Node LTS e, per Tauri, Rust (`rustup`). Windows: anche Visual Studio Build Tools (C++) e WebView2.
2. Nella cartella dell'app:
   ```
   npm ci
   npx playwright install webkit chromium
   ```

## A ogni lavoro
| Comando | Cosa fa |
|---|---|
| `npm run controlla` | token, lint del CSS, tipi: pochi secondi |
| `npx playwright test --project=webkit` | un motore solo, mentre lavori |
| `npm test` | tutto, prima del push |
| `npm run foto` | fogli da guardare a occhio |
| `npm run consumi` | CPU e memoria dell'app ferma |

## Insidie
- `controlla` verde subito e senza messaggi → lo script non è partito → metti un difetto apposta: deve fallire.
- Script che su Windows non parte mai → `import.meta.url` confrontato con `file://…` a mano → `pathToFileURL`.
- WebKit in timeout → troppi worker o macchina carica → `--workers=4`.
- Tab salta i link in WebKit → impostazione predefinita di Safari, non un bug → nel test usa il focus diretto.
- Timeout a caso → due suite insieme sulla stessa macchina → una alla volta.
