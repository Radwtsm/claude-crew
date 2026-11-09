#!/bin/sh
# Controllo anti-fuga per un repo PUBBLICO: blocca IP, URL, email e segreti (README "Cosa NON ci va").
# Parole private in più (host, nomi): una regex per riga in ~/.config/claude-crew/parole-vietate, mai nel repo.
# Uso: sh check.sh  (lo lanciano il pre-commit in .githooks/ e la CI)
cd "$(dirname "$0")" || exit 1
p='([0-9]{1,3}\.){3}[0-9]{1,3}|https?://|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}'
p="$p|(\+39[ .]?)?3[0-9]{2}[ .]?[0-9]{6,7}\b|IT[0-9]{2}[A-Z][0-9]{10}|-----BEGIN|(api[_-]?key|token|password|secret)[\"' ]*[:=][\"' ]*[A-Za-z0-9/+_-]{8,}"
ok="https://(github\.com|raw\.githubusercontent\.com)/(\{\{REPO\}\}|Radwtsm/(claude-crew|pleiadi-app)|\{REPO\})|https://claude\.ai/install\.(sh|ps1)|https://raw\.githubusercontent\.com/Homebrew/install/|https://github\.com(/\{repo\}|\"|/microsoft/winget-cli/releases/)|https://raw\\\.githubusercontent\\\.com/\[|https://apps\.apple\.com/app/id[0-9]+|https://play\.google\.com/store/apps/details\?id=|https://\{host\}/|http://\{LOCALE\}|http://schemas\.microsoft\.com/windows/2004/02/mit/task"
files=$(git ls-files 2>/dev/null; git ls-files -o --exclude-standard 2>/dev/null)
[ -n "$files" ] || files=$(find . -type f -not -path './.git/*' -not -path './dist/*')
hits=$(echo "$files" | grep -vE '^(\./)?(\.github/workflows/|check\.sh$)' | xargs grep -nIE "$p" 2>/dev/null | grep -vE "$ok")
deny="$HOME/.config/claude-crew/parole-vietate"
if [ -s "$deny" ]; then
  more=$(echo "$files" | xargs grep -nIiE -f "$deny" 2>/dev/null)
  hits=$(printf '%s\n%s' "$hits" "$more" | sed '/^$/d')
fi
if [ -n "$hits" ]; then
  echo "$hits"
  echo "check.sh: possibile dato privato/segreto qui sopra, togli prima del commit" >&2
  exit 1
fi
# Formato comune di regole e skill (README → Formato): solo i problemi nuovi bloccano, quelli noti in
# lint-regole-baseline.txt possono solo calare; in più i limiti in byte di limiti-contesto.txt (contesto snello)
# A115: i PC si aggiornano solo con la firma della squadra. Qui solo il controllo: firmare è un gesto voluto,
# `python3 tools/firma.py --firma` con conferma di una persona (A128), mai dal pre-commit
python3 tools/firma.py || exit 1
python3 plugins/regole/scripts/lint_regole.py . || exit 1
# Ogni Esito di crew.py ha il suo passo di onboarding in PASSI (obbligatorio/facoltativo, sistemi): `pleyades-cli passi`
python3 tools/lint_passi.py || exit 1
python3 crew.py passi --json | python3 -c "import json,sys; json.load(sys.stdin)" || exit 1
# La guida di un collega nuovo in una casa finta (programmi con effetti finti, studio Nextcloud finto): percorso e forma
python3 tools/test_guida.py || exit 1
# `squadra` conta solo chi è ancora nella stanza (chi è tolto dallo studio non resta rosso)
python3 tools/test_squadra.py || exit 1
# Dopo il login GitHub l'invito al repo del progetto si accetta da solo, solo quello
python3 tools/test_invito.py || exit 1
# Il setup tocca il PC solo dove serve: terminale fuori dal setup, `auto` non rimette app o attività tolte
python3 tools/test_setup_pc.py || exit 1
# `disinstalla` rimette i file come prima del setup e lascia le cose della persona (casa finta)
python3 tools/test_disinstalla.py || exit 1
python3 tools/test_pianifica.py || exit 1
# Gli interruttori dell'app (A119): scelte, dipendenze, allineato sugli accesi, spegni solo parti Pleyades
python3 tools/test_interruttori.py || exit 1
python3 tools/test_finestre.py || exit 1  # niente cmd che lampeggiano su Windows (DETACHED_PROCESS vietato)
# Chiede prima di installare (installa.ps1/.sh) e di cancellare la copia vecchia dell'app; `auto` non cancella
python3 tools/test_chiedi_prima.py || exit 1
# Con l'invito la riga installa solo l'app firmata dalla squadra, senza domande né altri programmi (A90)
python3 tools/test_solo_app.py || exit 1
# Il push automatico di claude-personale non porta segreti su GitHub (A124)
python3 tools/test_segreti_push.py || exit 1
# Lo scarico dello studio non scrive fuori dalla copia (A129); firma solo voluta e solo in avanti (A128)
python3 tools/test_studio_percorsi.py || exit 1
python3 tools/test_firma.py || exit 1
# Ogni plugin ha le sue `keywords` nel catalogo: da lì l'hook dei messaggi suggerisce un plugin mancante (personale.py)
senza=$(python3 -c "import json;print(' '.join(p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'] if not p.get('keywords')))")
if [ -n "$senza" ]; then
  echo "check.sh: plugin senza keywords in .claude-plugin/marketplace.json: $senza (le parole e i programmi del mestiere)" >&2
  exit 1
fi
# Ogni plugin del catalogo (tranne regole) ha la sua riga nell'indice plugin-spenti
fuori=$(python3 -c "import json;t=open('plugins/regole/skills/plugin-spenti/SKILL.md').read();print(' '.join(p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'] if p['name']!='regole' and '\`'+p['name']+'\`' not in t))")
if [ -n "$fuori" ]; then
  echo "check.sh: plugin senza riga in plugins/regole/skills/plugin-spenti/SKILL.md: $fuori" >&2
  exit 1
fi
exit 0
