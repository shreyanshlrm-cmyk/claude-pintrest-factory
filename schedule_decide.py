"""
Decides whether THIS invocation should trigger a posting batch.
Called every 30 minutes by the scheduler workflow. Uses an adaptive
probability so that, across the day's active window, we land on exactly
TARGET_BATCHES_PER_DAY actual runs — but WHICH slots fire is different
every day, unlike a fixed-cron-plus-small-jitter approach.
"""

import json
import os
import random
from datetime import datetime, timezone

STATE_FILE = "schedule_state.json"
TARGET_BATCHES_PER_DAY = 5
WINDOW_START_HOUR = 4    # UTC — active window start
WINDOW_END_HOUR = 22     # UTC — active window end
SLOT_MINUTES = 30

now = datetime.now(timezone.utc)
today = now.strftime("%Y-%m-%d")

state = {"date": today, "posted_batches": 0}
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE) as f:
            loaded = json.load(f)
        if loaded.get("date") == today:
            state = loaded
    except Exception as e:
        print(f"[Scheduler] Could not read state file ({e}), starting fresh.")

should_run = False

if state["posted_batches"] >= TARGET_BATCHES_PER_DAY:
    print(f"[Scheduler] Already hit today's target of {TARGET_BATCHES_PER_DAY} batches. Skipping.")
elif not (WINDOW_START_HOUR <= now.hour < WINDOW_END_HOUR):
    print(f"[Scheduler] Outside active window ({WINDOW_START_HOUR}:00-{WINDOW_END_HOUR}:00 UTC). Skipping.")
else:
    minutes_now = now.hour * 60 + now.minute
    minutes_end = WINDOW_END_HOUR * 60
    remaining_slots = max(1, (minutes_end - minutes_now) // SLOT_MINUTES)
    remaining_target = TARGET_BATCHES_PER_DAY - state["posted_batches"]
    # Adaptive probability: guarantees we'll hit the target by window's end,
    # while WHEN exactly within the window is different each day.
    probability = min(1.0, remaining_target / remaining_slots)
    roll = random.random()
    should_run = roll < probability
    print(f"[Scheduler] {now.isoformat()} | posted_today={state['posted_batches']} "
          f"remaining_target={remaining_target} remaining_slots={remaining_slots} "
          f"probability={probability:.3f} roll={roll:.3f} -> should_run={should_run}")

if should_run:
    state["posted_batches"] += 1
    state["date"] = today
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"[Scheduler] Firing batch #{state['posted_batches']} of {TARGET_BATCHES_PER_DAY} for {today}.")

gh_output = os.environ.get("GITHUB_OUTPUT")
if gh_output:
    with open(gh_output, "a") as f:
        f.write(f"should_run={'true' if should_run else 'false'}\n")
