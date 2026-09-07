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
