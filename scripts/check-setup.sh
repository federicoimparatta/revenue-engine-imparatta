#!/usr/bin/env bash
# Revenue Engine - environment check. Run anytime:
#   bash ~/.claude/skills/revenue-engine-imparatta/scripts/check-setup.sh
# Everything marked "optional" only limits features; the skill runs without it.
set -uo pipefail

ok()   { printf '  [ok]   %s\n' "$1"; }
warn() { printf '  [--]   %s\n' "$1"; }
fail() { printf '  [MISS] %s\n' "$1"; }

echo "Revenue Engine setup check"
echo

# Required
if command -v claude >/dev/null 2>&1; then
  ok "Claude Code CLI installed ($(claude --version 2>/dev/null | head -1))"
else
  fail "Claude Code CLI not found - install from https://claude.com/claude-code"
fi

if [ -f "$HOME/.claude/skills/revenue-engine-imparatta/SKILL.md" ]; then
  ok "Skill installed at ~/.claude/skills/revenue-engine-imparatta"
else
  fail "Skill not installed - git clone the repo into ~/.claude/skills/revenue-engine-imparatta"
fi

# Config
if [ -f "$HOME/.revenue-engine-imparatta/identity.md" ] && [ -f "$HOME/.revenue-engine-imparatta/icp.md" ]; then
  ok "Configured (~/.revenue-engine-imparatta seeded) - run /revenue-engine-imparatta"
else
  warn "Not configured yet - seed ~/.revenue-engine-imparatta (see README)"
fi

# Deterministic quality helpers are required even when email is unavailable.
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if python3 - "$SKILL_DIR" <<'PYCHECK'
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(sys.argv[1]) / 'scripts'))
from domain_util import excluded, registrable
from high_gate import evaluate
from validate_job_posting import inspect
rules = json.loads((Path.home() / '.revenue-engine-imparatta/clients-exclude.json').read_text())
assert isinstance(rules, list) and rules, 'missing exclusion rules'
assert registrable('https://www.nike.com/careers') == 'nike.com'
assert registrable('careers.acme.co.uk') == 'acme.co.uk'
for name in ('Ataraxy', 'TransGrid Energy', 'EnergyFluo', 'SMG', 'Squadron Data',
             'Mozart', 'SweatWorks', 'Nike', 'Equinox', 'SoulCycle', 'Verusen',
             'Kleva', 'White Pearl', 'WPTG', 'Sidetool', 'Grimco'):
    assert excluded(name, '', '', rules), 'missing hard exclusion: ' + name
PYCHECK
then
  ok "Quality helpers, suffix list and hard client-exclusion list loaded"
else
  fail "Quality gate/exclusion setup failed - drafting must stop"
  exit 1
fi

# Optional
if command -v python3 >/dev/null 2>&1; then
  if python3 -c "import docx" >/dev/null 2>&1; then
    ok "python-docx available (.docx reports enabled)"
  else
    warn "python-docx missing (optional) - 'pip3 install python-docx' for .docx reports; markdown works without it"
  fi
else
  warn "python3 missing (optional) - needed only for .docx reports and Hunter lookups"
fi

if [ -s "$HOME/.revenue-engine-imparatta/.secrets/hunter.env" ] || [ -n "${HUNTER_API_KEY:-}" ]; then
  ok "Hunter.io key configured (verified-email mode)"
else
  warn "No Hunter.io key (optional) - LinkedIn-first mode; add one at ~/.revenue-engine-imparatta/.secrets/hunter.env"
fi

echo
echo "Gmail drafting uses gog with account federico@imparatta.com"
