# agent-cron

Tiny scheduler CLI for agents: add/list/rm commands scheduled `--at`, `--in`, or `--cron`; each run's status, exit code, and output is stored in `~/.agent-cron/jobs.db`. Single file, Python stdlib only.

```bash
ln -sf "$PWD/agent-cron" ~/.local/bin/agent-cron
agent-cron install                     # launchd agent, ticks every 60s
ln -sfn "$PWD/skill" ~/.claude/skills/agent-cron   # Claude Code skill
python3 test_agent_cron.py             # self-check
```

See `skill/SKILL.md` for usage.
