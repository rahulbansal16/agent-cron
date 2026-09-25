# agent-cron

Tiny scheduler CLI for AI agents. An agent schedules a shell command with `--at`, `--in` or `--cron`, then lists, runs or deletes jobs and reads each run's status, exit code and output. Single file, Python stdlib only, macOS (launchd).

```bash
agent-cron add --in 2h -- 'claude -p "check PR #123 CI" > /tmp/pr.txt'
agent-cron add --cron "0 9 * * 1-5" --cwd ~/repo -- ./sync.sh
agent-cron list --json
agent-cron runs 3 --json
agent-cron rm 3
```

## Install

Requires macOS and Python 3.

```bash
git clone https://github.com/rahulbansal16/agent-cron.git ~/agent-cron
cd ~/agent-cron
mkdir -p ~/.local/bin
ln -sf "$PWD/agent-cron" ~/.local/bin/agent-cron   # ~/.local/bin must be on your PATH
agent-cron install                                 # launchd agent that ticks every 60s
python3 test_agent_cron.py                         # optional self-check, prints "ok"
```

`agent-cron uninstall` removes the launchd agent. Jobs and history are stored in `~/.agent-cron/jobs.db`.

## Add it to Claude Code

### 1. Install the skill

The skill tells Claude when and how to use `agent-cron`, e.g. when you say "run this at 9am" or "check back in 2 hours".

```bash
mkdir -p ~/.claude/skills
ln -sfn ~/agent-cron/skill ~/.claude/skills/agent-cron
```

Restart Claude Code (or start a new session). `agent-cron` should now appear in the skill list, and you can call it directly with `/agent-cron`.

### 2. Allow the command without permission prompts (optional)

Add this to `~/.claude/settings.json` so Claude can call `agent-cron` without asking every time:

```json
{
  "permissions": {
    "allow": ["Bash(agent-cron:*)"]
  }
}
```

Merge it into your existing `permissions.allow` list if you already have one. Note that this also lets Claude *schedule* commands without asking, and those commands run later without further prompts. Leave it out if you want to approve each job.

### 3. Tell Claude it exists (optional)

The skill is usually enough. To make Claude reach for it more consistently, add this to `~/.claude/CLAUDE.md`:

```markdown
# Scheduling
To run something later or on a schedule, use the `agent-cron` CLI (see the agent-cron skill),
not `sleep`, background shells or the system crontab. Check results with `agent-cron runs <id> --json`.
```

### Try it

Ask Claude:

> Schedule `echo hello` to run in 1 minute, then show me its result once it has run.

Claude should run `agent-cron add --in 1m -- echo hello` and, after a minute, `agent-cron runs <id>`.

## How it works

- `agent-cron install` writes `~/Library/LaunchAgents/com.agent-cron.tick.plist`, which runs `agent-cron tick` every 60 seconds.
- Each tick claims the jobs that are due and starts each one as a separate background process, so a long job doesn't hold up the others.
- A job runs with the working directory and `PATH` it was added from, so `claude`, `node` and similar tools work under launchd.
- If the Mac was asleep, a missed run fires once on the first tick after wake.
- Each run stores its status (`queued`, `running`, `ok`, `failed`), exit code and the last 64KB of output.

See `skill/SKILL.md` for the full command reference.

## License

MIT
