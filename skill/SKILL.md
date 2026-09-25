---
name: agent-cron
description: Schedule a shell command to run later (one-shot at a time, or recurring cron) on this Mac, then check its status/output. Use when asked to "run X at 9am", "remind/check back in 2 hours", "run this every day", or to list/delete scheduled commands.
---

# agent-cron

Local scheduler backed by launchd (ticks every 60s). Jobs and run history live in `~/.agent-cron/jobs.db`. Jobs run with the `cwd` and `PATH` of whoever added them. Times are local.

```bash
agent-cron add --at "2026-09-26 09:00" --name morning-report -- node scripts/report.mjs
agent-cron add --in 2h -- 'claude -p "check PR #123 CI and summarize" > /tmp/pr123.txt'
agent-cron add --cron "0 9 * * 1-5" --cwd ~/repo -- ./sync.sh
agent-cron list [--all] [--json]       # scheduled jobs + last status
agent-cron runs [JOB_ID] [-n 5] --json # history: status ok|failed|running, exit_code, output (last 64KB)
agent-cron run JOB_ID                  # run now in foreground
agent-cron rm JOB_ID                   # delete job and its history
```

- Put the command after `--`. Shell syntax (pipes, `;`, `$(...)`) needs a single quoted argument.
- Use `--json` when you will parse the output.
- If `add` warns "scheduler not installed", run `agent-cron install`.
- Missed runs (Mac asleep) fire once on the next tick after wake. A cron job whose schedule can never fire is disabled, with the reason in `runs`.
