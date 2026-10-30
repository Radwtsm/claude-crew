#!/bin/sh
# Controllo anti-fuga per un repo PUBBLICO: blocca IP, URL, email e segreti (README "Cosa NON ci va").
# Parole private in più (host, nomi): una regex per riga in ~/.config/claude-crew/parole-vietate, mai nel repo.
# Uso: sh check.sh  (lo lanciano il pre-commit in .githooks/ e la CI)
cd "$(dirname "$0")" || exit 1
p='([0-9]{1,3}\.){3}[0-9]{1,3}|https?://|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}'
p="$p|(\+39[ .]?)?3[0-9]{2}[ .]?[0-9]{6,7}\b|IT[0-9]{2}[A-Z][0-9]{10}|-----BEGIN|(api[_-]?key|token|password|secret)[\"' ]*[:=][\"' ]*[A-Za-z0-9/+_-]{8,}"
ok="https://(github\.com|raw\.githubusercontent\.com)/(\{\{REPO\}\}|Radwtsm/claude-crew|\{REPO\})|https://claude\.ai/install\.(sh|ps1)|https://raw\.githubusercontent\.com/Homebrew/install/|https://api\.github\.com/repos/cli/cli/|https://github\.com/\{repo\}|https://api\.github\.com/repos/nextcloud-releases/(desktop|talk-desktop)/|https://apps\.apple\.com/app/id[0-9]+|https://play\.google\.com/store/apps/details\?id=|https://\{host\}/|http://\{LOCALE\}"
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
python3 plugins/regole/scripts/lint_regole.py . || exit 1
# Ogni Esito di crew.py ha il suo passo di onboarding in PASSI (obbligatorio/facoltativo, sistemi): `pleyades-cli passi`
python3 tools/lint_passi.py || exit 1
python3 crew.py passi --json | python3 -c "import json,sys; json.load(sys.stdin)" || exit 1
# La guida di un collega nuovo in una casa finta (programmi con effetti finti, studio Nextcloud finto): percorso e forma
python3 tools/test_guida.py || exit 1
# Ogni plugin ha le sue `keywords` nel catalogo: da lì l'hook dei messaggi suggerisce un plugin mancante (personale.py)
senza=$(python3 -c "import json;print(' '.join(p['name'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'] if not p.get('keywords')))")
if [ -n "$senza" ]; then
  echo "check.sh: plugin senza keywords in .claude-plugin/marketplace.json: $senza (le parole e i programmi del mestiere)" >&2
  exit 1
fi
exit 0
