#!/bin/sh
# agent-cron installer: CLI on PATH, launchd scheduler, Claude Code skill.
#
#   curl -fsSL https://raw.githubusercontent.com/rahulbansal16/agent-cron/main/install.sh | sh
#
# or, from a checkout:  sh install.sh
# Re-run any time to update. Set AGENT_CRON_REPO / AGENT_CRON_SRC to override the source.
set -eu

REPO="${AGENT_CRON_REPO:-https://github.com/rahulbansal16/agent-cron}"
SRC="${AGENT_CRON_SRC:-$HOME/.local/share/agent-cron-src}"
BIN="$HOME/.local/bin"
SKILLS="$HOME/.claude/skills"

[ "$(uname)" = Darwin ] || { echo "agent-cron: macOS only (uses launchd)" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "agent-cron: python3 required" >&2; exit 1; }

# Running from inside a checkout? Use it. Otherwise clone or update the source.
here="$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)"
if [ -n "$here" ] && [ -x "$here/agent-cron" ] && [ -d "$here/skill" ]; then
  SRC="$here"
elif [ -d "$SRC/.git" ]; then
  git -C "$SRC" pull --ff-only --quiet
else
  command -v git >/dev/null 2>&1 || { echo "agent-cron: git required" >&2; exit 1; }
  mkdir -p "$(dirname "$SRC")"
  git clone --depth 1 --quiet "$REPO" "$SRC"
fi

# 1. CLI on PATH
mkdir -p "$BIN"
ln -sf "$SRC/agent-cron" "$BIN/agent-cron"
echo "linked   $BIN/agent-cron"

# 2. launchd scheduler (ticks every 60s)
"$SRC/agent-cron" install

# 3. Claude Code skill, so Claude can schedule and check jobs in any session
mkdir -p "$SKILLS"
ln -sfn "$SRC/skill" "$SKILLS/agent-cron"
echo "linked   $SKILLS/agent-cron (Claude Code skill)"

case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "note: add $BIN to your PATH, e.g.  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc" ;;
esac
echo "done. Start a new Claude Code session and ask: \"what's scheduled in agent-cron?\""
