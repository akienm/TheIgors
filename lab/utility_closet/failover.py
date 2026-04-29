"""
failover.py — T-postgres-home-db-failover

Failover appointment: promote a surviving box to home DB when the
primary goes down. Human triggers: appoint_home_db(hostname).

The tool:
1. Validates the target hostname is in the machines registry
2. Builds the new IGOR_HOME_DB_URL from the machine's IP
3. Updates the local .env file
4. Posts to comms://swarm/failover so all instances know
5. Returns instructions for manual steps (restart Igor instances)

This is NOT automatic failover — it requires a human decision.
The automation is in propagating that decision to the swarm.
"""

import json
import logging
from lab.utility_closet.agent_base import get_logger
import os
from datetime import datetime
from typing import Optional

log = get_logger(__name__)


def appoint_home_db(
    hostname: str,
    db_name: str = "Igor-wild-0001",
    db_user: str = "igor",
    db_password: str = "choose_a_password",
    db_port: int = 5432,
) -> dict:
    """
    Appoint a new home DB host. Returns status dict.

    This does NOT migrate data — the swarm sync should have already
    replicated to the target. This just updates the pointer.
    """
    # Validate hostname is known
    try:
        from lab.utility_closet.machine_manager import get_machine

        machine = get_machine(hostname)
        if not machine:
            return {"error": f"Unknown hostname: {hostname}. Use a registered machine."}
        ip = machine.ip
    except Exception as exc:
        return {"error": f"Cannot look up machine: {exc}"}

    # Build new URL
    new_url = f"postgresql://{db_user}:{db_password}@{ip}:{db_port}/{db_name}"

    # Record the old URL
    old_url = os.environ.get("IGOR_HOME_DB_URL", "")

    result = {
        "action": "appoint_home_db",
        "old_host": (
            old_url.split("@")[-1].split("/")[0] if "@" in old_url else "unknown"
        ),
        "new_host": f"{ip}:{db_port}",
        "new_url_masked": f"postgresql://{db_user}:***@{ip}:{db_port}/{db_name}",
        "timestamp": datetime.now().isoformat(),
    }

    # Update local environment (takes effect for this process)
    os.environ["IGOR_HOME_DB_URL"] = new_url
    result["env_updated"] = True

    # Post to comms channel for swarm notification
    try:
        from lab.utility_closet.comms import ChannelMessage

        # Try to get the comms module from UC server
        try:
            from lab.claudecode.utility_closet_server import _comms

            if _comms:
                _comms.ensure_channel("comms://swarm/failover")
                _comms.send(
                    ChannelMessage(
                        channel="comms://swarm/failover",
                        source="failover_tool",
                        content_type="application/json",
                        payload=json.dumps(result),
                    )
                )
                result["comms_notified"] = True
        except Exception:
            result["comms_notified"] = False
    except Exception:
        result["comms_notified"] = False

    # Instructions for human
    result["manual_steps"] = [
        f"1. Verify Postgres is running on {hostname} ({ip}:{db_port})",
        f"2. Verify {db_name} database exists and has recent data",
        "3. Restart all Igor instances (they'll pick up the new IGOR_HOME_DB_URL)",
        "4. On each remote box, update IGOR_HOME_DB_URL in .env",
    ]

    log.info("Home DB appointed: %s → %s", result["old_host"], result["new_host"])
    return result


def check_home_db_health() -> dict:
    """Quick health check on the current home DB."""
    db_url = os.environ.get("IGOR_HOME_DB_URL", "")
    if not db_url:
        return {"healthy": False, "reason": "IGOR_HOME_DB_URL not set"}

    try:
        import psycopg2

        conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        host = db_url.split("@")[-1].split("/")[0] if "@" in db_url else "unknown"
        return {"healthy": True, "host": host}
    except Exception as exc:
        return {"healthy": False, "reason": str(exc)}
