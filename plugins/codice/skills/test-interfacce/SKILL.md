---
name: test-interfacce
description: Tecniche e strumenti per scoprire le incongruenze di un'interfaccia mentre cambiano schermate, opzioni e misura, per ogni stack (web, Tauri, Electron, SwiftUI, Flutter, Android). Usala prima dei test di una UI e per "layout rotto", "bug visivi", "al ridimensionamento salta", "griglia".
---

# Test delle interfacce

Un bug di layout nasce quasi sempre MENTRE si usa l'app. Le foto a poche misure non lo vedono. Ogni progetto con una UI
ha queste tecniche, nell'ordine in cui rendono di più.

Installare e lanciare i test: `installare.md`.

## Prima di tutto chiedi
Stack, motori da coprire (es. WebKit e Chromium), misure minime e massime, regole di design scritte.

## Tecniche
| Tecnica | Cosa scopre | Come |
|---|---|---|
| Invarianti | ciò che deve valere sempre | una funzione sola: bordi di colonna, passo, file pari, niente coperto, niente fuori dal contenitore |
| Spazzata | bug fra due misure provate | ogni 40 px da minimo a massimo, più i due lati di ogni soglia, senza ricaricare |
| Andata e ritorno | stato che resta sporco | impronta delle misure, cambia schermata e misura, torna: identica |
| Combinazioni | opzioni che si pestano | ogni valore di modo, grandezza, tema, per schermata; troppe: a coppie |
| Percorso a caso | sequenze mai pensate | azioni casuali con seme fisso, invarianti dopo ogni passo; il seme ripete il bug |
| Dati al limite | layout che regge solo coi dati buoni | nomi lunghissimi senza spazi, liste vuote e piene, numeri enormi |
| Più motori | differenze fra sistemi | stessi test su ogni motore vero; niente fiducia in uno solo |
| Stabilità | salti mentre arriva qualcosa | spazio riservato; Layout Shift a 0 durante i caricamenti |
| Foto con griglia | ciò che le regole non dicono | fogli per misura e modo, con griglia sopra, guardati da una persona |
| Difetti apposta | test che non scoprono niente | rompi il CSS di proposito: ogni difetto deve far fallire qualcosa |

## Regole
- Le invarianti in un file solo, usate da test e foto: una regola nuova vale subito ovunque.
- La griglia legge il layout vivo e si ridisegna da sola. Mai misure copiate nel test.
- Griglie e strumenti di prova restano fuori dal pacchetto: gli utenti non li vedono.
- Test tutti verdi al primo colpo → difetti apposta prima di fidarti.
- Bug trovato a occhio → prima la regola che lo scopre, poi il fix.

## Strumenti per stack
| Stack | Strumenti |
|---|---|
| Web, Tauri, Electron | Playwright (WebKit, Chromium, Firefox), axe, `getBoundingClientRect`, `elementFromPoint` |
| SwiftUI, UIKit | XCUITest, swift-snapshot-testing, audit di accessibilità di XCTest |
| Flutter | golden test, `tester.binding.setSurfaceSize`, `integration_test` |
| Android | Compose UI test, Paparazzi o Roborazzi, Espresso |
| Terminale | snapshot del testo a più larghezze |

## Insidie
- Test verdi, bug su Mac → provato solo su Chromium → WebKit a ogni giro.
- Riga sovrapposta ridimensionando dal vivo → WebKit non ricalcola `flex-wrap` → usa una container query.
- Layout che salta nei test → ricaricare a ogni misura nasconde lo stato vecchio → ridimensiona senza ricaricare.
- `page.evaluate` con «__name is not defined» → esbuild aggiunge `__name` → definiscilo nella pagina.
