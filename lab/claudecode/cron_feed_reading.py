#!/usr/bin/env python3
"""
cron_feed_reading.py — Hourly reading list feeder trigger.

Called via crontab to pull pending books from reading_list into the learn queue
and spawn drain_learn_queue if needed.

Runs at: 0 * * * * (every hour, at :00)
"""

import sys
import os
from pathlib import Path

# Setup paths
REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
os.environ.setdefault(
    "IGOR_DB_PATH", os.path.expanduser("~/.TheIgors/Igor-wild-0001/wild-0001.db")
)

# Import the tool directly
from wild_igor.igor.tools.learner import feed_reading_list

# Call it
result = feed_reading_list()
print(result)
