# Claude Code Bootstrap — TheIgors

Read this file on your first session in this repo. If you already have skills
and MCP working, skip it.

---

## What should already be set up

Migration 003 (runs automatically when Igor starts via `igor` / `igor.ps1`)
installs three things:

1. **MCP server** — `.claude/settings.local.json` with `mcpServers.igor`
2. **Skills** — symlinked from `claudecode/cc_skills/` to `~/.claude/skills/`
3. **Memory seeds** — copied from `claudecode/cc_memory_seed/` to your CC project memory

## Verify setup

1. Check skills are available: try typing `/context-load` — if CC recognizes it, skills are working.
2. Check MCP is connected: try calling `mcp__igor__channel_read` with `limit: 1`.
   - If it fails: restart Claude Code (`/quit` then reopen). MCP loads on startup.
   - If it still fails: check that Igor is running (`igor` or `igor.ps1`).
3. Check memory: your project memory directory should have seed files.

## If migration 003 hasn't run

This happens if you opened Claude Code before ever running Igor. Run the
bootstrap manually:

**Linux/macOS:**
```bash
bash claudecode/bootstrap_cc.sh
```

**Windows (PowerShell):**
```powershell
.\claudecode\bootstrap_cc.ps1
```

Then restart Claude Code to load the MCP server.

## First session workflow

1. Run `/context-load` to orient (reads today's slate, recent decisions, channel)
2. Read `CLAUDE.md` for working conventions (inertia levels, commit policy)
3. Check the slate for active tickets

## Uninstall

To remove Claude Code integration (skills + MCP config):

```bash
python wild_igor/setup_assets/installer.py --uninstall-cc
```

This removes skill symlinks and the igor MCP entry. Memory seeds are preserved.
