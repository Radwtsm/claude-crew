---
name: shopify-tema
description: Lavorare sul codice di un tema Shopify con la Shopify CLI senza rompere il negozio né cancellare le modifiche fatte dall'editor. Usala quando l'utente dice "personalizza il mio negozio Shopify", "modifica il tema", "carica le modifiche su Shopify", "aggiungi una sezione", "importa i prodotti", o quando un push ha cancellato qualcosa o l'intestazione Horizon si è scomposta.
---

# Tema Shopify con la CLI

## Prima di tutto chiedi
- Nome del negozio e quale tema è **pubblicato** (live) e quale è la copia di lavoro.
- Se il negozio è ancora **protetto da password** (nessun cliente lo vede) o è aperto al pubblico.
- Chi modifica dall'editor di Shopify (testi, foto, ordine delle sezioni): quei cambi vanno salvati, non
  sovrascritti.

## Regole
- **Tema live**: non si tocca. Si lavora su una copia non pubblicata e la si pubblica quando è pronta. Unica
  eccezione accettabile: negozio ancora protetto da password e l'utente lo decide esplicitamente.
- **Password del negozio e login**: li scrive sempre l'utente, mai Claude.
- **Git nella cartella del tema**: un commit prima di ogni push, così si può tornare indietro.
- Ogni blocco nuovo = una **sezione Liquid** con impostazioni (testi, immagini, colori, collezione), così l'utente
  lo cambia dall'editor senza codice. Prefisso comune per le tue sezioni e snippet (es. `negozio-*`).
- Theme Check pulito sui tuoi file prima di caricare.

## Comandi
Anteprima locale (chiede login e password del negozio, quindi va lanciata nel terminale dell'utente):
```
shopify theme dev --store <negozio>.myshopify.com
```
Su Windows, se PowerShell blocca gli script `.ps1`, usa il `.cmd`: `& "$env:APPDATA\npm\shopify.cmd" theme dev ...`.

**Prima di ogni push, pull** dei file che l'editor modifica, poi confronta:
```
shopify theme pull --store <negozio>.myshopify.com --theme <id> --only templates/*.json --only config/settings_data.json --only sections/*.json
git diff
```
Se il pull riporta solo una versione vecchia di un tuo JSON, ripristina il tuo (`git checkout -- <file>`). Poi:
```
shopify theme push --store <negozio>.myshopify.com --theme <id>
```
(`--allow-live` solo nell'eccezione del negozio protetto.)

## Trappole del tema Horizon
- Intestazione in modalità menu ☰: `.header__column` è `display: contents`, quindi ogni icona è una casella della
  griglia. **Non aggiungere elementi o `::before/::after` nella griglia**: spostano le icone in altre colonne.
- Horizon ha **due pulsanti di ricerca** e un pulsante account nascosti: lasciali nascosti.
- I pulsanti `.button-unstyled` hanno `overflow: hidden`: taglia bollini ed etichette → `overflow: visible`.
- L'icona carrello ha una maschera che la "buca" dove sta il numero: in icone piccole usa `mask: none`.
- Regole vecchie del tema con selettori più specifici vincono sulle tue: allunga il selettore invece di usare
  `!important` ovunque.
- Le sezioni senza collezione collegata mostrano prodotti d'esempio: ricordalo all'utente prima di aprire il sito.

## Prodotti e collezioni
- Catalogo da foglio Excel/annunci → **CSV di importazione Shopify** (una riga per variante e per foto in più);
  l'import lo fa l'utente dall'admin.
- Collezioni automatiche su regole (tipo prodotto, tag, prezzo di confronto > 0 per le offerte); per sezioni che
  leggono solo i primi prodotti imposta l'ordinamento giusto (es. prezzo crescente).
- Lista desideri senza app: `localStorage` sul dispositivo, cuore su intestazione e card.

## Dopo
Controlla il risultato **dal vivo** in formato telefono, tablet e computer (intestazione, carrello, sezioni nuove)
prima di dire che è fatto, e annota le decisioni dell'utente in un file del progetto.
