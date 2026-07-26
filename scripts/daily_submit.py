"""Idempotent daily competition submit.

Reads submit_config.json at the repo root, checks whether the team's daily
submission slot (resets at UTC midnight) is already used, and if not submits
the configured kernel version. Safe to run any number of times per day.

Auth: KAGGLE_API_TOKEN env var (Kaggle access token, KGAT_...).
"""

import datetime
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def list_submissions(token: str, competition: str):
    req = urllib.request.Request(
        f"https://www.kaggle.com/api/v1/competitions/submissions/list/{competition}?page=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def todays(subs, today: str):
    return [s for s in subs if str(s.get("date", ""))[:10] == today]


def main() -> int:
    token = os.environ["KAGGLE_API_TOKEN"].strip()
    with open(os.path.join(ROOT, "submit_config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    competition = cfg["competition"]
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

    used = todays(list_submissions(token, competition), today)
    if used:
        print(f"slot already used today ({today}): ref {used[0].get('ref')} "
              f"status {used[0].get('status')} - skipping")
        return 0

    cmd = [
        "kaggle", "competitions", "submit", competition,
        "-k", cfg["kernel"], "-v", str(cfg["version"]),
        "-f", "submission.parquet", "-m", cfg["message"],
    ]
    print("submitting:", cfg["kernel"], "version", cfg["version"])
    subprocess.run(cmd, check=True)

    used = todays(list_submissions(token, competition), today)
    if not used:
        print("ERROR: submission not visible in list after submit", file=sys.stderr)
        return 1
    print(f"submitted: ref {used[0].get('ref')} status {used[0].get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
