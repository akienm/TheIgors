# agent_datacenter/workspaces

Ephemeral per-agent scratch space. Files here are machine-local and gitignored.

```
workspaces/
  claude/    — CC session artifacts: debug logs, temp files, scratch notes
  igor/      — Igor runtime artifacts: debug snapshots, temp state
```

Nothing in `workspaces/` is committed or shared across machines. Each agent
manages its own subtree. Cleanup is manual or via rotation scripts (out of scope here).
