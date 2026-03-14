# Subsystem: Tools

*Updated: 2026-03-14 | Machine-readable: `design_docs_for_igor/subsystem_tools.dsb` | Full index: `design_docs_for_igor/capabilities_index.dsb`*

---

## Design Principles

- **AI-agnostic**: tools know nothing about which tier calls them. Reasoner adapters convert the registry schema to the appropriate protocol (Anthropic vs. OpenAI/OR).
- **Self-registration**: each module calls `registry.register(Tool(...))` at module level on import. No manual wiring.
- **Schema normalization**: `to_openai_schema()` wraps shorthand params in `{"type":"object","properties":{}}` for gpt-4o-mini compatibility.
- **Hot-reloadable**: LOW-inertia modules can be reloaded with `reload_module()` — their registration re-executes automatically.

---

## Tool Registry (`tools/registry.py`)

```python
class Tool(name, description, parameters, fn)
    execute(**kwargs) → str        # never raises; returns error string on unknown tool
    to_anthropic_schema()          # Anthropic tool-use format
    to_openai_schema()             # OpenAI/OR format (normalizes shorthand params)
    to_text_description()          # plain text for prompt injection
```

Load path: `tools/__init__.py` imports all modules; each self-registers.

---

## Key Tools

| Tool group | File | Key functions |
|-----------|------|---------------|
| **self_edit** | `tools/self_edit.py` | `patch_source_file` (preferred), `edit_source_file` — gate: `IGOR_SELF_EDIT_ENABLED`; auto-commit+push; hot-reload if LOW inertia |
| **hot_reload** | `tools/hot_reload.py` | `reload_module(module_name)`, `list_loaded_modules` — HIGH inertia blocked |
| **filesystem** | `tools/filesystem.py` | `read_file`, `write_file`, `list_directory`, `read_system_file` — sandboxed to `/home/akien` |
| **runner** | `tools/runner.py` | `run_bash`, `run_python`, `get_current_time`, `restart_self(note="")` — restart exits code 42 |
| **senses** | `tools/senses.py` | `take_photo`, `record_audio`, `list_cameras` |
| **web_search** | `tools/web_search.py` | `web_search(query)` |
| **budget** | `tools/budget.py` | `get_budget_status`, `set_spending_cap`, `check_openrouter_balance`, `is_cloud_blocked` |
| **learner** | `tools/learner.py` | `learn_about(user_input)`, `process_learn_queue`, `drain_learn_queue`, `list_absorbed_books`, `get_reading_list`, `add_to_reading_list`, `update_reading_status` |
| **ebook_reader** | `tools/ebook_reader.py` | `find_book`, `open_book`, `read_chunk`, `jump_to_chapter`, `reading_position`, `list_reading_sessions` |
| **word_graph** | `tools/word_graph.py` | `index_text_into_word_graph`, `query_word_graph_stats`, `analyze_word_graph`, `train_word_graph` |
| **metrics** | `tools/metrics.py` | `get_metrics_report` — `/metrics` slash command output |
| **filesystem_extra** | `tools/filesystem.py` | `check_resource_load`, `check_disk_usage`, `evaluate_threshold_habits` |

Full 118-tool inventory: `design_docs_for_igor/capabilities_index.dsb`

---

## Reactive Habit Pattern

A PROC habit can carry `code_ref` + `twm_ttl_seconds` in its metadata. On fire, the habit:
1. Dispatches the tool named in `code_ref`
2. Pushes the result to TWM with the given TTL (short = self-cleaning)

Example: `PROC_WHAT_TIME` → `get_current_time()`, 30s TTL. Igor always knows the time without an LLM call.

---

## Threshold Habit Pattern

`habit_type="threshold"` + `condition_field/op/value` in metadata. Evaluated by:
- `ResourceMonitorSource` (background, every 60s)
- Pre-submit hook in `main.py`

Example: `PROC_CPU_THRESHOLD` fires when `cpu_load_pct ≥ 80%`.

---

## Learn Queue

`~/.TheIgors/learn_queue.json` — entries with `calibre://ID` sentinel or HTTP URLs. Drained by:
- **Manual**: `process_learn_queue(max_items=5)` — 3s human pace between launches
- **Background**: `drain_learn_queue()` → spawns `claudecode/drain_learn_queue.py` (PID-guarded, 60s between, loops until empty)
- **Auto**: `learn_about()` calls `_launch_queue_runner()` whenever items are queued
