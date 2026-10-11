"""Lightweight scheduled-worker placeholder. Run from cron/Task Scheduler."""
from datetime import datetime
from db import init_db, db, add_alert
init_db()
with db() as c:
    rows=c.execute("SELECT id,campaign,scheduled_date FROM approvals WHERE status='Scheduled'").fetchall()
for r in rows:
    add_alert(f"Scheduled campaign ready: {r['campaign']} ({r['scheduled_date']})")
print(f"iConnect scheduler checked {len(rows)} scheduled item(s) at {datetime.now().isoformat(timespec='seconds')}")
