---
name: ticket
description: Create or update a ticket. Args: "last" for thing just discussed, or description text.
model: haiku
---

# /ticket — Create or update a ticket

## Usage
- `/ticket last` — ticket whatever we just discussed
- `/ticket <description>` — create new or update existing

## Description template

The ticket's `description` field must have this shape:

    <1-3 sentences: problem and proposed shape>

    **Affected files:** <comma-separated paths, or "TBD — discovery step in sprint" if genuinely unknown>
    **Design rules:** <which palace checks under theigors/rules/ticket_design_checks/ apply — e.g. "no-sqlite, test-plan-or-why-not". Say "none apply" only if you have thought about it.>
    **Scope boundary:** <what's explicitly in scope; what's explicitly out of scope>
    **Test plan:** <specific tests to add or run, OR "no tests because: <reason>" — do not leave blank>

Structure lives in description TEXT as labeled sections. Do NOT add columns to cc_queue.py's DB row. Free-form narrative on top, labeled fields below.

## Steps

1. **Identify**: New ticket or update to existing?
   ```bash
   python3 ~/TheIgors/lab/claudecode/cc_queue.py list 2>/dev/null | grep -i "<keyword>"
   ```

2. **Fill structured fields** (see `## Description template` above): the description must include Affected files, Design rules, Scope boundary, Test plan. For `/ticket last`, infer each field from the conversation; mark genuinely unknown fields as "TBD" rather than skipping. Missing fields will be flagged by /review at filing time.

3. **Review**: Check the plan before creating — inertia levels, scope, tests planned?

4. **Create or update**:
   - ID format: `T-<kebab-slug>` (max 5 words)
   - Check for collision before creating
   - For new: write JSON to /tmp/ticket.json, then `cc_queue.py add /tmp/ticket.json`
   - For update: `cc_queue.py done/block/claim <id>`

5. **Add to slate**: Put ticket ID in today's slate under ## Planned or ## Ad hoc.

6. **Run /savestateauto**
