#!/opt/homebrew/bin/bash
# Nightly /revenue-engine-imparatta runner (LaunchAgent com.federico.imparatta-leads,
# weekdays 23:00 America/Montevideo). Loaded into gui/$(id -u) so it can read the
# unlocked login Keychain; the plist wraps this in launchagent-alert-wrap.sh, which
# adds caffeinate (maintenance-sleep kills long claude runs) and pages Federico on
# any non-zero exit.
#
# Single-phase on purpose: this engine drafts at most 6 emails a night, so the blast
# radius of a partial run is small. What it borrows from the battle-tested
# ataraxy-leads runner is everything that failed there first: the run lock, the hard
# deadline, usage-limit detection, and asserting on ARTIFACTS instead of trusting
# claude's exit code (three of ataraxy's first six failures exited 0 having
# delivered nothing).
set -uo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export TZ="America/Montevideo"

DATA_DIR="$HOME/.revenue-engine-imparatta"
GOG_ACCOUNT="federico@imparatta.com"
LOGDIR="$DATA_DIR/cron-logs"
mkdir -p "$LOGDIR"
RUN_DATE="$(date +%F)"
RUN_ID="$(date +%Y-%m-%d_%H%M%S)"
LOG="$LOGDIR/imparatta-leads-$RUN_ID.log"
RUN_DIR="$HOME/.local/share/imparatta-leads/runs/$RUN_ID"
mkdir -p "$RUN_DIR"
BUNDLE="$HOME/Downloads/revenue-engine-imparatta-$RUN_DATE"
cd "$HOME" || exit 1

say() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

# A wedged run must not hold the lock into tomorrow's fire.
TIMEOUT_BIN=""
for c in /opt/homebrew/bin/gtimeout /usr/local/bin/gtimeout /opt/homebrew/bin/timeout /usr/bin/timeout; do
  [ -x "$c" ] && { TIMEOUT_BIN="$c"; break; }
done
[ -n "$TIMEOUT_BIN" ] || { say "RUNNER FAIL: no gtimeout/timeout on PATH. Install coreutils."; exit 76; }

# Config must exist before spending two hours discovering it does not.
for f in identity.md services.md icp.md preferences.md exclude.md; do
  [ -s "$DATA_DIR/$f" ] || { say "RUNNER FAIL: $DATA_DIR/$f missing or empty."; exit 78; }
done
[ -s "$DATA_DIR/.secrets/hunter.env" ] || { say "RUNNER FAIL: hunter.env missing."; exit 78; }

# gog must be able to reach the sending mailbox NOW; a stale token discovered at the
# first draft wastes the whole sweep. Bounded: an unbounded preflight can hang holding
# nothing, an unbounded postflight can hang holding the lock.
if ! "$TIMEOUT_BIN" 60s gog gmail drafts list -a "$GOG_ACCOUNT" --max 1 >/dev/null 2>>"$LOG"; then
  say "RUNNER FAIL: gog cannot read $GOG_ACCOUNT drafts (expired token?). Run: gog auth add"
  exit 78
fi

# Single-run lock: mkdir is atomic; reclaim only stale or dead-owner locks.
LOCK="$DATA_DIR/.run.lock"
take_lock() {
  if mkdir "$LOCK" 2>/dev/null; then echo $$ > "$LOCK/pid"; return 0; fi
  local owner; owner="$(cat "$LOCK/pid" 2>/dev/null)"
  if [ -z "$owner" ]; then
    if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +5 2>/dev/null)" ]; then
      say "reclaiming an abandoned lock with no owner recorded"
      rm -rf "$LOCK"; mkdir "$LOCK" 2>/dev/null || return 1; echo $$ > "$LOCK/pid"; return 0
    fi
    return 1
  fi
  if kill -0 "$owner" 2>/dev/null; then return 1; fi
  say "reclaiming lock from dead run $owner"
  rm -rf "$LOCK"; mkdir "$LOCK" 2>/dev/null || return 1; echo $$ > "$LOCK/pid"; return 0
}
take_lock || { say "RUNNER FAIL: another sweep holds the run lock."; exit 75; }
cleanup() {
  local rc=$?
  pkill -P $$ 2>/dev/null
  [ "$(cat "$LOCK/pid" 2>/dev/null)" = "$$" ] && rm -rf "$LOCK"
  exit "$rc"
}
trap cleanup EXIT
trap 'say "termination signal, shutting down"; exit 143' TERM INT HUP

# --- the sweep ---------------------------------------------------------------
say "starting /revenue-engine-imparatta scheduled (run $RUN_ID)"
CLAUDE_LOG="$RUN_DIR/claude.log"
# Freshness baseline: a same-day re-run after a failed attempt would otherwise pass
# the assertions on the strength of the earlier attempt's artifacts.
START_STAMP="$RUN_DIR/.start"
touch "$START_STAMP"
"$TIMEOUT_BIN" --signal=TERM --kill-after=60s 150m \
  claude -p "/revenue-engine-imparatta scheduled $RUN_DATE" --dangerously-skip-permissions \
  > "$CLAUDE_LOG" 2>&1
CLAUDE_RC=$?
say "claude exited $CLAUDE_RC"

# --- assertions on artifacts, never on the exit code -------------------------
# A usage limit looks identical to broken research from the artifacts alone; say so
# explicitly or whoever reads the alert debugs the wrong thing.
if grep -qiE "reached your .* limit|usage limit|rate.?limit|quota" "$CLAUDE_LOG" 2>/dev/null \
   && [ ! -s "$BUNDLE/report.md" ]; then
  say "RUNNER FAIL: the model refused the run - usage limit or quota, not a research failure."
  say "             $(grep -hoiE "You've reached your [^.]*limit[^.]*" "$CLAUDE_LOG" 2>/dev/null | head -1)"
  exit 74
fi

FINAL_RC=0; FAILMSG=""
if [ ! -s "$BUNDLE/report.md" ]; then
  FAILMSG="no report at $BUNDLE/report.md"; FINAL_RC=87
elif [ ! "$BUNDLE/report.md" -nt "$START_STAMP" ]; then
  # Exists but predates this run: a leftover from an earlier same-day attempt.
  FAILMSG="report at $BUNDLE/report.md is from an earlier attempt, not this run"
  FINAL_RC=87
elif ! grep -qF "## [$RUN_DATE]" "$DATA_DIR/lead-history.md" 2>/dev/null; then
  # The skill writes the day heading even on a dry night, so an absent heading is a
  # failed run, not a quiet market.
  FAILMSG="report exists but lead-history.md has no heading for $RUN_DATE - dedupe record lost"
  FINAL_RC=88
elif [ ! -s "$DATA_DIR/outreach/$RUN_DATE-batch.md" ] || [ ! "$DATA_DIR/outreach/$RUN_DATE-batch.md" -nt "$START_STAMP" ]; then
  FAILMSG="no fresh outreach manifest at outreach/$RUN_DATE-batch.md (the skill writes one even when empty)"
  FINAL_RC=89
elif [ "$CLAUDE_RC" -ne 0 ]; then
  # Artifacts look complete but the agent process died or timed out: the tail of the
  # run (drafts, Slack) may be missing. Complete-looking artifacts must not silence a
  # dead process.
  FAILMSG="artifacts exist but claude exited $CLAUDE_RC - the end of the run may be missing; reconcile drafts before re-running"
  FINAL_RC=86
fi

if grep -qF "Background tasks still running" "$CLAUDE_LOG" 2>/dev/null; then
  FAILMSG="${FAILMSG:+$FAILMSG; }the run ended its turn with work still in background tasks"
  [ "$FINAL_RC" -eq 0 ] && FINAL_RC=73
fi

if [ "$FINAL_RC" -ne 0 ]; then
  say "RUNNER FAIL: $FAILMSG"
  say "             Check $CLAUDE_LOG. If drafts were partially created, list them with:"
  say "             gog gmail drafts list -a $GOG_ACCOUNT --max 20"
  say "             and reconcile against outreach/$RUN_DATE-batch.md before re-running:"
  say "             a blind re-run double-drafts every prospect already contacted."
else
  DRAFTED="$("$TIMEOUT_BIN" 60s gog gmail drafts list -a "$GOG_ACCOUNT" --max 20 -p 2>/dev/null | wc -l | tr -d ' ')"
  say "done: report at $BUNDLE, history heading written, manifest written ($DRAFTED drafts now in $GOG_ACCOUNT)."
fi

# best-effort housekeeping; never decides the exit status
ls -1t "$LOGDIR"/imparatta-leads-*.log 2>/dev/null | tail -n +31 | xargs -I{} rm -f {} || true
find "$HOME/.local/share/imparatta-leads/runs" -mindepth 1 -maxdepth 1 -type d -mtime +30 \
  -exec rm -rf {} + 2>/dev/null || true

exit "$FINAL_RC"
