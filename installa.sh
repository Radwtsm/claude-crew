#!/bin/bash
# La riga unica (Mac, Linux): scarica la guida `pleyades-cli` (Pleyades tools) e la lancia. Si può rilanciare: salta ciò che c'è già.
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash
# Con un progetto a cui sei stato invitato:
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash -s -- PROPRIETARIO/REPO
# Qui solo ciò che serve a far partire Python; tutto il resto (Claude Code, GitHub, plugin, progetti, Nextcloud)
# lo fa crew.py, uguale su Mac, Linux e Windows.
set -u
if [ "$(uname)" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; then
  # come Homebrew: gli strumenti di Apple da softwareupdate (minuti) invece della finestra (che stima anche 35 h)
  printf '→ Installo gli strumenti di Apple (git e python3, circa 1 GB, qualche minuto).\n'
  printf '  Ti chiede la password del Mac (quella con cui accendi il computer): mentre la scrivi non si vede niente.\n'
  segnale=/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
  touch "$segnale"
  printf '  Cerco il pacchetto di Apple (1-2 minuti, senza scritte: non è bloccato)…\n'
  printf '  Se è aperta la finestra «Scarico il software» di un tentativo precedente, premi «Interrompi»: ne basta uno.\n'
  nome=$(softwareupdate -l 2>/dev/null | sed -n 's/^ *\* Label: //p' | grep 'Command Line Tools' | tail -1)
  if [ -n "$nome" ] && sudo softwareupdate -i "$nome" --verbose; then
    rm -f "$segnale"
  else
    rm -f "$segnale"
    xcode-select --install 2>/dev/null
    printf '→ Non ci sono riuscito dal Terminale: si è aperta la finestra di Apple. Premi «Installa», aspetta la fine,\n'
    printf '  poi incolla di nuovo la stessa riga.\n'
    exit 1
  fi
fi
if ! command -v python3 >/dev/null; then
  printf '❌ manca python3: installalo (es. sudo apt install python3 git) e rilancia la stessa riga.\n'
  exit 1
fi
mkdir -p "$HOME/.crew"
if ! curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py -o "$HOME/.crew/crew.py.tmp"; then
  printf '❌ non riesco a scaricare la guida: controlla internet e rilancia la stessa riga.\n'
  exit 1
fi
mv "$HOME/.crew/crew.py.tmp" "$HOME/.crew/crew.py"
if [ -r /dev/tty ]; then
  exec python3 "$HOME/.crew/crew.py" guida "$@" </dev/tty
fi
exec python3 "$HOME/.crew/crew.py" guida "$@"
