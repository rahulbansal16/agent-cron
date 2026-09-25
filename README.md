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

One command (macOS, Python 3). It installs the CLI, the launchd scheduler and the Claude Code skill:

```bash
curl -fsSL https://raw.githubusercontent.com/rahulbansal16/agent-cron/main/install.sh | sh
```

What it does, all idempotent (re-run it to update):

1. Clones the repo to `~/.local/share/agent-cron-src` (or pulls if already there).
2. Links `agent-cron` into `~/.local/bin` (make sure that is on your `PATH`).
3. Runs `agent-cron install`, a launchd agent that ticks every 60s.
4. Links the skill into `~/.claude/skills/agent-cron`.

Then start a new Claude Code session and ask *"what's scheduled in agent-cron?"*. The skill lets Claude schedule jobs and, in any later session, check what's scheduled, whether it ran and what it printed.

`agent-cron uninstall` removes the launchd agent. Jobs and history are stored in `~/.agent-cron/jobs.db`.

<details>
<summary>Manual install</summary>

```bash
git clone https://github.com/rahulbansal16/agent-cron.git ~/agent-cron
mkdir -p ~/.local/bin ~/.claude/skills
ln -sf ~/agent-cron/agent-cron ~/.local/bin/agent-cron
ln -sfn ~/agent-cron/skill ~/.claude/skills/agent-cron
agent-cron install
python3 ~/agent-cron/test_agent_cron.py   # optional self-check, prints "ok"
```

</details>

## Claude Code setup (optional extras)

The installer already adds the skill. Two optional tweaks:

### Allow the command without permission prompts

Add this to `~/.claude/settings.json` so Claude can call `agent-cron` without asking every time:

```json
{
  "permissions": {
    "allow": ["Bash(agent-cron:*)"]
  }
}
```

Merge it into your existing `permissions.allow` list if you already have one. Note that this also lets Claude *schedule* commands without asking, and those commands run later without further prompts. Leave it out if you want to approve each job.

### Tell Claude it exists

The skill is usually enough. To make Claude reach for it more consistently, add this to `~/.claude/CLAUDE.md`:

```markdown
# Scheduling
To run something later or on a schedule, use the `agent-cron` CLI (see the agent-cron skill),
not `sleep`, background shells or the system crontab. Check results with `agent-cron runs <id> --json`.
```

### Try it

Ask Claude:

> Schedule `echo hello` to run in 1 minute, then show me its result once it has run.

Claude should run `agent-cron add --in 1m -- echo hello` and, after a minute, `agent-cron runs <id>`. In a new session, *"did my hello job run?"* should find it again via `agent-cron list --all`.

## How it works

- `agent-cron install` writes `~/Library/LaunchAgents/com.agent-cron.tick.plist`, which runs `agent-cron tick` every 60 seconds.
- Each tick claims the jobs that are due and starts each one as a separate background process, so a long job doesn't hold up the others.
- A job runs with the working directory and `PATH` it was added from, so `claude`, `node` and similar tools work under launchd.
- If the Mac was asleep, a missed run fires once on the first tick after wake.
- Each run stores its status (`queued`, `running`, `ok`, `failed`), exit code and the last 64KB of output.

See `skill/SKILL.md` for the full command reference.

## License

MIT
