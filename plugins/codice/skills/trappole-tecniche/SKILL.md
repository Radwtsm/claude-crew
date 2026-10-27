---
name: trappole-tecniche
description: Trappole tecniche già incontrate dalla crew, con la soluzione - shell (bash, zsh, Git Bash su Windows), hook, ssh, Docker e firewall, Cloudflare Access, SQLite, Python http.server, Swift, macOS (launchd, File Provider, sips), Playwright e test end-to-end, immagini ed EXIF, layout web (CLS), Node. Usala prima di scrivere script shell o hook, comandi ssh, test end-to-end, codice che tocca file di sistema, immagini o layout web, e quando qualcosa si comporta in modo strano o un test fallisce solo ogni tanto.
---

# Trappole tecniche

Ognuna è già costata tempo a qualcuno della crew. Apri **solo** il file del tema che tocchi:

| Tema | File | Leggilo prima di… |
|---|---|---|
| Shell, ssh e hook | [`shell.md`](shell.md) | script bash/zsh/Git Bash, comandi ssh, hook, heredoc, file di config scritti da script (12) |
| macOS | [`mac.md`](mac.md) | launchd, File Provider (iCloud/Drive), sips (3) |
| Web e test end-to-end | [`web-test.md`](web-test.md) | Playwright, screenshot, layout (CLS), Node, JS generato da Python (6) |
| Server, rete e servizi | [`server-rete.md`](server-rete.md) | SQLite, server HTTP, VPN/mesh, Docker e firewall, Cloudflare, API pubbliche, versioni di terzi (8) |
| Modifiche al codice | [`codice.md`](codice.md) | rinomine, spostamenti, rimozioni in blocco, Swift, formati cifrati (6) |

Una trappola nuova (`sintomo → causa → cosa fare`) va in fondo al file del suo tema; un tema nuovo = un file
nuovo + una riga qui.
