"""Self-check: python3 test_agent_cron.py"""
import importlib.machinery, importlib.util, json, os, stat, subprocess, tempfile, time
from datetime import datetime
here = os.path.dirname(os.path.abspath(__file__))
loader = importlib.machinery.SourceFileLoader("ac", os.path.join(here, "agent-cron"))
spec = importlib.util.spec_from_loader("ac", loader); ac = importlib.util.module_from_spec(spec); loader.exec_module(ac)

# --- cron math (Asia/Kolkata: no DST) ---
os.environ["TZ"] = "Asia/Kolkata"; time.tzset()
base = datetime(2026, 9, 25, 14, 30).timestamp()  # Friday
nx = lambda e, b=base: datetime.fromtimestamp(ac.next_cron(e, b)).strftime("%a %Y-%m-%d %H:%M")
assert nx("*/15 * * * *") == "Fri 2026-09-25 14:45"
assert nx("0 9 * * 1-5") == "Mon 2026-09-28 09:00"
assert nx("0 0 1 * *") == "Thu 2026-10-01 00:00"
assert nx("0 9 * * 7") == "Sun 2026-09-27 09:00"
assert nx("0 9 13 * 5") == "Fri 2026-10-02 09:00"   # dom and dow both restricted: OR
assert nx("0 9 */1 * 1") == "Mon 2026-09-28 09:00"  # "*/1" dom stays a wildcard: Mondays only
assert nx("0 0 29 2 *") == "Tue 2028-02-29 00:00"   # leap day, more than a year out
try:
    ac.next_cron("0 0 30 2 *", base); raise AssertionError("Feb 30 should never fire")
except ValueError:
    pass

# --- DST (America/New_York): time keeps moving forward through fall-back, and a gap time is skipped ---
os.environ["TZ"] = "America/New_York"; time.tzset()
t = datetime(2026, 11, 1, 0, 50).timestamp()
for _ in range(200):  # walk "every minute" across the 01:00-02:00 repeated hour
    n = ac.next_cron("* * * * *", t); assert n == t // 60 * 60 + 60, (t, n); t = n
assert nx("30 2 * * *", datetime(2026, 3, 8, 0, 0).timestamp()) == "Mon 2026-03-09 02:30"  # 02:30 doesn't exist on 3/8
os.environ["TZ"] = "Asia/Kolkata"; time.tzset()

# --- CLI end to end, isolated store ---
home = tempfile.mkdtemp()
env = {**os.environ, "AGENT_CRON_HOME": home}
cli = lambda *a: subprocess.run([os.path.join(here, "agent-cron"), *a], env=env, capture_output=True, text=True)
runs_of = lambda jid: json.loads(cli("runs", str(jid), "--json").stdout)

def wait_done(jid):
    for _ in range(50):
        r = runs_of(jid)
        if r and all(x["status"] in ("ok", "failed") for x in r):
            return r
        time.sleep(0.1)
    raise AssertionError(f"job {jid} never finished: {runs_of(jid)}")

j = json.loads(cli("add", "--in", "0s", "--json", "--", "echo", "hi there").stdout)
cli("tick")
runs = wait_done(j["id"])
assert runs[0]["status"] == "ok" and runs[0]["output"] == "hi there\n", runs
assert json.loads(cli("list", "--json").stdout) == []  # one-shot done

# store is owner-only
assert stat.S_IMODE(os.stat(home).st_mode) == 0o700
assert stat.S_IMODE(os.stat(os.path.join(home, "jobs.db")).st_mode) == 0o600

# ids are never reused after rm
assert cli("rm", str(j["id"])).returncode == 0 and json.loads(cli("list", "--all", "--json").stdout) == []
j2 = json.loads(cli("add", "--in", "1h", "--json", "--", "true").stdout)
assert j2["id"] > j["id"], (j, j2)
cli("rm", str(j2["id"]))

# overlapping ticks fire a due one-shot exactly once
j = json.loads(cli("add", "--in", "0s", "--json", "--", "echo once").stdout)
procs = [subprocess.Popen([os.path.join(here, "agent-cron"), "tick"], env=env) for _ in range(8)]
[p.wait() for p in procs]
assert len(wait_done(j["id"])) == 1, runs_of(j["id"])

# output is capped to the tail
j = json.loads(cli("add", "--in", "0s", "--json", "--",
                   "python3 -c \"import sys; sys.stdout.write('x' * 200000 + 'END')\"").stdout)
cli("tick")
out = wait_done(j["id"])[0]["output"]
assert len(out) == ac.OUTPUT_CAP and out.endswith("END"), len(out)

# a schedule that errors disables only its own job, and the tick still runs the others
c = ac.db.__globals__["sqlite3"].connect(os.path.join(home, "jobs.db"))
c.execute("INSERT INTO jobs(command, cron, next_run) VALUES('true', '0 0 30 2 *', 0)"); c.commit()
bad = c.execute("SELECT max(id) FROM jobs").fetchone()[0]
good = json.loads(cli("add", "--in", "0s", "--json", "--", "echo fine").stdout)
assert cli("tick").returncode == 0
assert wait_done(good["id"])[0]["output"] == "fine\n"
r = runs_of(bad)
assert r[0]["status"] == "failed" and "disabled" in r[0]["output"], r
assert not [x for x in json.loads(cli("list", "--json").stdout) if x["id"] == bad]

# install writes a valid plist even for paths with XML characters, carrying AGENT_CRON_HOME
weird = tempfile.mkdtemp(suffix="a & <b>")
ac.HOME, ac.PLIST = ac.Path(weird) / "store", ac.Path(weird) / "x.plist"
real_run = subprocess.run
ac.subprocess.run = lambda *a, **k: None  # don't touch the real launchd
ac.install()
real_run(["plutil", "-lint", str(ac.PLIST)], check=True, capture_output=True)
home_val = real_run(["plutil", "-extract", "EnvironmentVariables.AGENT_CRON_HOME", "raw", "-o", "-", str(ac.PLIST)],
                    capture_output=True, text=True, check=True).stdout
assert home_val.rstrip("\n") == str(ac.HOME), home_val
print("ok")
