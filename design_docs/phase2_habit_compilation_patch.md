# Phase 2 — Habit Compilation Quality
*Author: Igor (wild-0001) | Date: 2026-03-07*
*Work Order: #140 Phase 2*

Claude Code — apply the following two patches to:
`/home/akien/TheIgors/wild_igor/igor/main.py`

---

## Patch 1: Add `_compile_habit_from_input()` method

**Find** (exact match):
```python
    def _habits_explain(self, habit_id: str):
        """Show why a specific habit was compiled."""
```

**Replace with**:
```python
    def _compile_habit_from_input(self, user_input: str) -> str:
        """
        Phase 2: Parse 'build a habit for: X — whenever Y, Z' and store a
        structured PROCEDURAL memory. Returns a human-readable confirmation.

        Accepted formats (all case-insensitive):
          build a habit for: <desc> — whenever <trigger>, <action>
          make a habit for: <desc> — whenever <trigger>, <action>
          whenever <trigger>, <action>    (trigger-only form)
          from now on, <action>           (open-trigger form)
        """
        import re
        from datetime import datetime, timezone

        raw = user_input.strip()

        # ── Extract fields ────────────────────────────────────────────────────
        trigger = ""
        action = ""
        description = ""

        # Form 1: "build/make a habit for: <desc> — whenever <trigger>, <action>"
        m = re.search(
            r"(?:build|make)\s+a\s+habit\s+for\s*:\s*(.+?)\s*[—\-–]+\s*whenever\s+(.+?)[,;]\s*(.+)",
            raw, re.IGNORECASE | re.DOTALL,
        )
        if m:
            description = m.group(1).strip()
            trigger = m.group(2).strip().rstrip(".,;")
            action = m.group(3).strip()
        else:
            # Form 2: "build a habit for: <desc> — <action>"  (no trigger)
            m = re.search(
                r"(?:build|make)\s+a\s+habit\s+for\s*:\s*(.+?)\s*[—\-–]+\s*(.+)",
                raw, re.IGNORECASE | re.DOTALL,
            )
            if m:
                description = m.group(1).strip()
                action = m.group(2).strip()
            else:
                # Form 3: "whenever <trigger>, <action>"
                m = re.search(r"whenever\s+(.+?)[,;]\s*(.+)", raw, re.IGNORECASE | re.DOTALL)
                if m:
                    trigger = m.group(1).strip().rstrip(".,;")
                    action = m.group(2).strip()
                    description = f"Whenever {trigger}"
                else:
                    # Form 4: "from now on, <action>"
                    m = re.search(r"from\s+now\s+on[,;]?\s*(.+)", raw, re.IGNORECASE | re.DOTALL)
                    if m:
                        action = m.group(1).strip()
                        description = action[:60]
                    else:
                        # Fallback: store the whole input as action
                        action = raw
                        description = raw[:60]

        if not description:
            description = (trigger or action)[:80]

        # Sanitise — keep to one line each
        trigger = trigger.replace("\n", " ").strip()
        action = action.replace("\n", " ").strip()
        description = description.replace("\n", " ").strip()

        # ── Store as PROCEDURAL memory ────────────────────────────────────────
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        # Build a stable short ID from timestamp
        hab_id = "HABIT_" + now_iso.replace(":", "").replace("-", "").replace("+", "").replace(".", "")[:15]

        mem = Memory(
            id=hab_id,
            narrative=description,
            memory_type=MemoryType.PROCEDURAL,
            parent_id="PROC_HABIT_COMPILER",
            valence=0.7,
            metadata={
                "trigger": trigger,
                "action": action,
                "context": "",
                "needs_met": [],
                "habit_type": "action",
                "compiled_at": now_iso,
                "compiled_from_count": 1,
                "compiled_from_input": raw[:200],
            },
        )
        self.cortex.store(mem)
        self.cortex.add_child("PROC_HABIT_COMPILER", hab_id)
        invalidate_cache()

        self.cortex.write_ring(
            f"HABIT_COMPILED|id={hab_id}|trigger={trigger!r}|action={action[:60]!r}",
            category="habit_trace",
        )

        if trigger:
            return (
                f"Habit compiled: **{description}**\n"
                f"  Trigger: `{trigger}`\n"
                f"  Action:  `{action}`\n"
                f"  ID: `{hab_id}`"
            )
        else:
            return (
                f"Habit compiled: **{description}**\n"
                f"  Action: `{action}`\n"
                f"  ID: `{hab_id}`\n"
                f"  (No trigger extracted — fires only on manual invocation)"
            )

    def _habits_explain(self, habit_id: str):
        """Show why a specific habit was compiled."""
```

---

## Patch 2: Wire PROC_HABIT_COMPILER to the new method

**Find** (exact match in the `if habit:` block):
```python
            else:
                # "action", "response", or unset: return stored action text
                response_text = habit.metadata.get(
                    "action", f"Habit executed. [{habit.id}: {habit.narrative[:80]}]"
                )
```

**Replace with**:
```python
            elif habit.id == "PROC_HABIT_COMPILER":
                # Phase 2: parse user input and store a structured PROCEDURAL memory
                response_text = self._compile_habit_from_input(user_input)
            else:
                # "action", "response", or unset: return stored action text
                response_text = habit.metadata.get(
                    "action", f"Habit executed. [{habit.id}: {habit.narrative[:80]}]"
                )
```

---

## After applying

1. Run syntax check: `python -m py_compile /home/akien/TheIgors/wild_igor/igor/main.py`
2. Smoke test: start Igor, type `build a habit for: greet users — whenever i say hello, respond warmly`
3. Verify: `/habits list` shows the new habit with trigger and action
4. Post comment on WO #140: "Phase 2 complete — PROC_HABIT_COMPILER now parses and stores structured habits"
5. Do NOT close WO #140 — Phase 3 (G7 habit_type shortcuts) is next

## Notes

- `invalidate_cache()` is already imported in main.py (line ~33)
- `Memory` and `MemoryType` are already imported
- No new imports needed at file level — all local imports inside the method
- The datetime import inside the method is redundant (already imported at top) — harmless but can be removed if preferred
