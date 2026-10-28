#!/bin/bash
# Installa tutto con una riga (Mac; Linux senza i passi di Apple). Si può rilanciare: salta ciò che c'è già.
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash
# Con un progetto privato a cui sei stato invitato (lo clona e lancia il suo onboarding.py, se c'è):
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash -s -- PROPRIETARIO/REPO
# Fa: strumenti di Apple (git, python3) → Claude Code → crew (solo regole + aggiornamento automatico) → progetto.
set -u
PROGETTO="${1:-}"
tty=/dev/tty
ok() { printf '✅ %s\n' "$1"; }
stop() { printf '❌ %s\n   Poi rilancia la stessa riga.\n' "$1"; exit 1; }

if [ "$(uname)" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install 2>/dev/null
  stop "Si è aperta la finestra degli strumenti di Apple: premi Installa e aspetta la fine"
fi
command -v git >/dev/null && command -v python3 >/dev/null || stop "mancano git o python3"
ok "git e python3"

export PATH="$HOME/.local/bin:$PATH"
if ! command -v claude >/dev/null; then
  curl -fsSL https://claude.ai/install.sh | bash || stop "installazione di Claude Code non riuscita"
fi
command -v claude >/dev/null || stop "Claude Code installato ma non nel PATH: apri un terminale nuovo"
ok "Claude Code"

# HTTPS per i plugin (niente chiave SSH di GitHub) e aggiornamento automatico della crew, senza toccare il resto
impostazioni() {
  python3 - "$@" <<'PY'
import json, os, sys
p = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
try:
    s = json.load(open(p, encoding="utf-8"))
except (OSError, ValueError):
    s = {}
s.setdefault("env", {})["CLAUDE_CODE_PLUGIN_PREFER_HTTPS"] = "1"
for nome in sys.argv[1:]:
    m = s.get("extraKnownMarketplaces", {}).get(nome)
    if isinstance(m, dict):
        m["autoUpdate"] = True
json.dump(s, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
PY
}
impostazioni
claude plugin marketplace list 2>/dev/null | grep -q claude-crew || claude plugin marketplace add Radwtsm/claude-crew >/dev/null
for x in regole; do  # il resto per mestiere: «aggiorna la crew» (mai strumenti di un altro settore)
  claude plugin list 2>/dev/null | grep -q "$x@claude-crew" || claude plugin install "$x@claude-crew" >/dev/null
done
impostazioni claude-crew  # `marketplace add` toglie autoUpdate: rimesso dopo
claude plugin list 2>/dev/null | grep -q "regole@claude-crew" || stop "plugin della crew non installati"
ok "crew (regole) con aggiornamento automatico; gli strumenti del tuo mestiere: in Claude «aggiorna la crew»"

[ -n "$PROGETTO" ] || { ok "fatto: apri Claude Code (claude) e scrivi «configura il mio Claude»"; exit 0; }

if ! command -v gh >/dev/null; then
  if ! command -v brew >/dev/null && [ "$(uname)" = Darwin ]; then
    echo "Serve Homebrew per installare GitHub CLI (chiede la password del Mac):"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" <$tty
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
  fi
  command -v brew >/dev/null && brew install gh >/dev/null
fi
command -v gh >/dev/null || stop "installa GitHub CLI (cli.github.com)"
gh auth status >/dev/null 2>&1 || gh auth login --web --git-protocol https <$tty || stop "accesso a GitHub non riuscito"
ok "GitHub"

dir="$HOME/code/${PROGETTO#*/}"
if [ ! -d "$dir/.git" ]; then
  gh repo clone "$PROGETTO" "$dir" >/dev/null 2>&1 || stop "non vedo $PROGETTO: accetta l'invito su GitHub (mail o notifiche)"
fi
ok "progetto in ${dir/#$HOME/~}"
onb=$(find "$dir" -maxdepth 4 -name onboarding.py -not -path '*/.git/*' | head -1)
if [ -n "$onb" ]; then
  python3 "$onb" <$tty
else
  ok "fatto: apri Claude Code in ${dir/#$HOME/~} e scrivi «controlla il mio setup»"
fi
