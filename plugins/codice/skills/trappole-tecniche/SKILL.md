---
name: trappole-tecniche
description: Trappole tecniche già incontrate, con la soluzione: shell (bash, zsh, Git Bash), hook, ssh, Docker, Cloudflare, SQLite, Swift, macOS, Playwright, immagini, layout web, Node. Usala prima di script, hook, ssh, test end-to-end, e quando qualcosa si comporta in modo strano.
---

# Trappole tecniche

Ognuna è già costata tempo a qualcuno di Pleyades. Apri **solo** il file del tema che tocchi:

| Tema | File | Leggilo prima di… |
|---|---|---|
| Shell, ssh e hook | [`shell.md`](shell.md) | script bash/zsh/Git Bash, comandi ssh, hook, heredoc, file di config scritti da script, wrapper (19) |
| macOS | [`mac.md`](mac.md) | launchd, File Provider (iCloud/Drive), sips (3) |
| Web e test end-to-end | [`web-test.md`](web-test.md) | Playwright, screenshot, layout (CLS), Node, JS generato da Python, WebKit (8) |
| Server, rete e servizi | [`server-rete.md`](server-rete.md) | SQLite, server HTTP, VPN/mesh, Docker e firewall, Cloudflare, API pubbliche, versioni di terzi, cache (10) |
| Modifiche al codice | [`codice.md`](codice.md) | rinomine, spostamenti, rimozioni in blocco, Swift, formati cifrati (6) |

Una trappola nuova (`sintomo → causa → cosa fare`) va in fondo al file del suo tema; un tema nuovo = un file
nuovo + una riga qui.
