"""
installer.py — D321 unified entry point for Igor (T-installer-cfg-split).

Called by the thin igor (bash) and igor.ps1 (Windows) shell wrappers.
Responsibilities:
  1. Apply pending migrations (idempotent, tracked via sentinel files)
  2. Run the Igor restart loop (replaces bash restart loop logic)

Migration sentinels: ~/.TheIgors/swarm/migrations/NNN.done
  001.done — .env distributed to split cfg files
  002.done — .env renamed to .env.backup-pre-d319 (decommissioned)

Stage 1: stub only. Full implementation in T-installer-stage2.
"""

if __name__ == "__main__":
    raise NotImplementedError(
        "installer.py is not yet implemented — see T-installer-stage2.\n"
        "Use the original 'igor' bash script to launch Igor in the meantime."
    )
