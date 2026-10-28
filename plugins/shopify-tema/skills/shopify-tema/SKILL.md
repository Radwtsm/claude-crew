---
name: shopify-tema
description: Codice di un tema Shopify con la Shopify CLI senza rompere il negozio né perdere le modifiche dell'editor. Usala per "personalizza il negozio Shopify", "modifica il tema", "carica le modifiche", "aggiungi una sezione", o un push che ha cancellato qualcosa.
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
Dagli strumenti di Claude `theme dev` non parte (chiede la password in modo interattivo), e il terminale dell'utente
può non vedere la CLI installata da Claude: dagli il comando con il percorso completo del `.cmd`.

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
- Elementi fuori dal contenitore delle tue sezioni (es. decorazioni dell'hero) non prendono gli stili con il tuo
  prefisso: controllali a parte.
- Prova di una modifica all'intestazione fuori dal tema: copia la **struttura vera** (colonne, doppia ricerca,
  account nascosto, CSS di Horizon), non una versione semplificata, o la prova passa e il tema si rompe.

## Admin Shopify dal browser di Claude
- Dopo un clic su un campo aspetta ~2 s prima di scrivere, o il testo si perde.
- Scorri con la rotella (azione di scroll): nell'admin `window.scrollY` resta 0, non usarlo per capire dove sei.
- Il banner dei cookie del negozio copre la pagina: per i test nascondilo da JS solo nella tua vista, mai nel tema.

## Prodotti e collezioni
- Catalogo da foglio Excel/annunci → **CSV di importazione Shopify** (una riga per variante e per foto in più);
  l'import lo fa l'utente dall'admin.
- Collezioni automatiche su regole (tipo prodotto, tag, prezzo di confronto > 0 per le offerte); per sezioni che
  leggono solo i primi prodotti imposta l'ordinamento giusto (es. prezzo crescente).
- Lista desideri senza app: `localStorage` sul dispositivo, cuore su intestazione e card.

## Dopo
Controlla il risultato **dal vivo** in formato telefono, tablet e computer (intestazione, carrello, sezioni nuove)
prima di dire che è fatto, e annota le decisioni dell'utente in un file del progetto.
