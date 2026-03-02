# Integration notes for main.py
# How to wire build_boot_message() into the boot sequence.
# These are NOT a full file replacement — they are the specific changes needed.
#
# Updated: 2026-03-02

# ── 1. Import ──────────────────────────────────────────────────────────────────
# Add to imports at top of main.py:
from .cognition.system_prompt import build_system_prompt, build_boot_message, invalidate_cache

# ── 2. Boot sequence addition (in Igor.__init__ or Igor.run(), after warm context loads) ──
#
# After _load_warm_context() completes, inject the synthetic boot message
# as the first item in the session. This ensures Igor reads orientation
# before any external input arrives.
#
# warm_ctx = self._load_warm_context()  # already exists
#
# boot_msg = build_boot_message(
#     cortex=self.cortex,
#     instance_id=self.instance_id,
#     warm_context=warm_ctx,      # None if cold start or TTL expired
# )
#
# # Process as a synthetic internal message — not from user, not from network.
# # Write to ring so NE sees it as session context.
# self.cortex.write_ring(boot_msg, category="session_control")
#
# # Also push to TWM with urgency=0.9 so it surfaces immediately.
# self.cortex.twm_push(
#     source="boot_sequence",
#     content_csb=boot_msg[:500],   # abbreviated for TWM
#     salience=0.9,
#     urgency=0.9,
#     metadata={"type": "boot_orientation"},
#     ttl_seconds=1800,
# )

# ── 3. boot_notes.md installation ─────────────────────────────────────────────
#
# boot_notes.md should be written to the instance directory at first boot
# (alongside SOUL.md and IDENTITY.md in _export_portable_identity()).
# It is a static file — update manually when operational guidance changes.
# Path: ~/.TheIgors/igor_{instance_id}/boot_notes.md
#
# In _export_portable_identity(), add:
#
# boot_notes_src = Path(__file__).parent.parent / "cognition" / "boot_notes.md"
# boot_notes_dst = self._instance_dir() / "boot_notes.md"
# if boot_notes_src.exists() and not boot_notes_dst.exists():
#     import shutil
#     shutil.copy(boot_notes_src, boot_notes_dst)

# ── 4. Cache invalidation ──────────────────────────────────────────────────────
#
# After any cortex.store() call that involves CP, ID, or PROC memory types,
# call invalidate_cache() so the next session gets a fresh system prompt.
# The simplest place: at the end of _pre_compaction_flush() and after
# _arbiter_resolve() stores learning memories.
#
# invalidate_cache()  # from cognition.system_prompt

# ── 5. system_prompt.py file location ─────────────────────────────────────────
# Place at: wild_igor/igor/cognition/system_prompt.py
# (alongside narrative_engine.py, push_sources.py, etc.)
#
# The existing system prompt logic in anthropic.py (hardcoded string)
# should be replaced with:
#
# from ..cognition.system_prompt import build_system_prompt
# ...
# system_prompt = build_system_prompt(self.cortex, self.instance_id)
