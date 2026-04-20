---
name: ticket
description: Create or update a ticket. Args: "last" for thing just discussed, or description text.
---

# /ticket — Create or update a ticket

## Usage
- `/ticket last` — ticket whatever we just discussed
- `/ticket <description>` — create new or update existing

## Steps

1. **Identify**: New ticket or update to existing?
   ```bash
   python3 ~/TheIgors/lab/claudecode/cc_queue.py list 2>/dev/null | grep -i "<keyword>"
   ```

2. **Review**: Check the plan before creating — inertia levels, scope, tests planned?

3. **Create or update**:
   - ID format: `T-<kebab-slug>` (max 5 words)
   - Check for collision before creating
   - For new: write JSON to /tmp/ticket.json, then `cc_queue.py add /tmp/ticket.json`
   - For update: `cc_queue.py done/block/claim <id>`

4. **Add to slate**: Put ticket ID in today's slate under ## Planned or ## Ad hoc.

5. **Run /savestateauto**
