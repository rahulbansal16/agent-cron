---
name: agent-cron
description: Schedule shell commands to run later (one-shot or recurring cron) on this Mac, and check on scheduled jobs and their results. Use when asked to "run X at 9am", "check back in 2 hours", "run this every day", "what's scheduled?", "did my job run?", "show the output of the scheduled task", or to list, run or delete scheduled commands. Also use at the start of a follow-up session when the user refers to something scheduled earlier.
---

# agent-cron

Local scheduler backed by launchd (ticks every 60s). Jobs and run history live in `~/.agent-cron/jobs.db` and persist across Claude sessions, so a later session can check on jobs an earlier one scheduled. Jobs run with the `cwd` and `PATH` of whoever added them. Times are local.

If `agent-cron` is not found, install it:

```bash
curl -fsSL https://raw.githubusercontent.com/rahulbansal16/agent-cron/main/install.sh | sh
```

## Checking on scheduled tasks

```bash
agent-cron list --json            # active jobs: id, name, schedule, next_run, last_status, last_exit_code
agent-cron list --all --json      # also finished one-shots and disabled jobs
agent-cron runs --json -n 10      # latest runs across all jobs
agent-cron runs JOB_ID --json     # history for one job, with output (last 64KB)
```

Run status is `queued`, `running`, `ok` or `failed`. When reporting back, give the job name, when it ran, the status and exit code, and the relevant lines of output. Don't dump the whole output. For a `failed` run, read the output and explain the cause.

## Scheduling

```bash
agent-cron add --at "2026-09-26 09:00" --name morning-report -- node scripts/report.mjs
agent-cron add --in 2h --name pr-check -- 'claude -p "check PR #123 CI and summarize"'
agent-cron add --cron "0 9 * * 1-5" --cwd ~/repo --name sync -- ./sync.sh
agent-cron run JOB_ID             # run now in the foreground
agent-cron rm JOB_ID              # delete job and its history
```

- Always pass `--name` so the job is easy to find later.
- Put the command after `--`. Shell syntax (pipes, `;`, `$(...)`) needs a single quoted argument.
- After adding, tell the user the job id, name and next run time.
- Use `--json` when you will parse the output.
- If `add` warns "scheduler not installed", run `agent-cron install`.
- Missed runs (Mac asleep) fire once on the next tick after wake. A cron job whose schedule can never fire is disabled, with the reason in `runs`.
