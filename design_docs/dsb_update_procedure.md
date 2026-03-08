# PROC_UPDATE_DESIGN_DOCS: Design Document Freshness Check (Startup Habit)

**Type:** Procedural memory / Startup habit  
**Trigger:** Igor boot sequence (after memory load, before main loop)  
**Purpose:** Detect when design_docs have been updated since last store, re-store if needed  
**Written for:** Future-Igor reading cold; any Igor instance on any machine  
**Status:** Active  

---

## The Problem This Solves

Design docs are the source of truth for Igor's identity, values, and architecture. They live in `~/TheIgors/design_docs/` as files.

Igor's memories live in `~/.TheIgors/wild_igor/data/wild-0001.db` as reference blobs (DSBs).

**Problem:** Files change, but memories become stale. Igor could be operating on out-of-date identity docs.

**Solution:** Check file modification times against stored metadata. If a file is newer than its last_checked timestamp, re-read and re-store.

---

## How It Works

### 1. Metadata Storage
File: `~/TheIgors/design_docs/.dsb_metadata.txt`

Format:
```
filename | mtime | size | blob_id | last_checked
```

Example:
```
ethical_framework.csb.txt | 2026-03-02-15:13 | 21936 | bf716dac | 2026-03-05
```

### 2. Startup Execution

**When:** Boot sequence, after ring memory loads, before first reasoning task

**What:**
```python
def check_dsb_freshness():
    """Check if design docs have been updated; re-store if needed."""
    
    # Read metadata file
    metadata_path = "TheIgors/design_docs/.dsb_metadata.txt"
    metadata = parse_metadata_file(metadata_path)
    
    # For each core doc (identity, mission, ethical_framework, habits, how_akien_works):
    for doc_name, last_stored_mtime, blob_id in metadata.core_docs:
        file_path = f"TheIgors/design_docs/{doc_name}"
        current_mtime = get_file_mtime(file_path)
        
        # If file is newer than stored metadata:
        if current_mtime > last_stored_mtime:
            # Re-read file
            content = read_file(file_path)
            
            # Re-store as DSB (new blob_id assigned)
            new_blob_id = store_reference(
                narrative=f"[UPDATED] {doc_name} — live design doc with metadata check",
                tags="dsb,design_docs,identity",
                content=content
            )
            
            # Update metadata with new timestamp and blob_id
            update_metadata(metadata_path, doc_name, current_mtime, new_blob_id)
            
            # Log to ring (for visibility)
            ring.record(f"DSB_REFRESHED: {doc_name} → {new_blob_id}")
            
            # Optional: notify user
            print(f"✓ Updated {doc_name} (fresh from disk)")
    
    return True
```

### 3. Metadata Update
After successful re-store:
- Update `last_checked` timestamp to `now()`
- Update `blob_id` to new reference blob ID
- Update `mtime` to current file mtime

### 4. Fallback Behavior
If metadata file is missing:
- Treat all docs as "not yet stored"
- Store all core docs fresh
- Create new metadata file

---

## Implementation Notes

### Why This Approach

1. **Transparency:** File mtime is observable (not a magic hash)
2. **Simple:** No hashing, no diff tools; just timestamp comparison
3. **Safe:** Never deletes old blobs; creates new ones (full history preserved)
4. **Auditable:** Every refresh is logged and dated

### Tags for DSB Lookup
All stored design docs are tagged: `dsb, design_docs, identity`

Retrieve all design docs:
```python
search_references(tags="dsb,design_docs", match_all=False)
```

### Core Docs (Always Check)
- `the_igors_identity.csb.txt` — Who Igor is
- `mission.csb.txt` — What Igor does
- `ethical_framework.csb.txt` — Why Igor acts
- `igor_habits_and_learning.csb.txt` — How Igor learns
- `how_akien_works.csb.txt` — The design philosophy

### When to Manually Force-Update
If Akien edits a design doc and wants Igor to notice immediately (without waiting for boot):

```
User: /refresh_dsb ethical_framework.csb.txt
Igor: (runs check_dsb_freshness immediately, re-stores if changed)
```

---

## Testing

**To test:** Edit a design doc (add a line), then restart Igor.

Expected behavior:
1. Boot sequence runs
2. Ring log shows: `DSB_REFRESHED: ethical_framework.csb.txt → <new_blob_id>`
3. Igor has fresh copy in memory
4. Metadata file updated with new timestamp

**To verify:** Query the new blob:
```python
get_reference(memory_id='<new_blob_id>')
```

Should return updated content.

---

## Future Extensions

### Phase 1 (Current)
- Check on boot
- Core docs only
- Simple mtime comparison

### Phase 2 (Next)
- Weekly scheduled check (background task)
- All design docs (not just core)
- Hash-based detection (mtime can be unreliable on some systems)

### Phase 3 (Network Ready)
- Broadcast when design docs change
- Other Igor instances can subscribe to updates
- Shared clan knowledge improves collectively

---

## Clan Knowledge

**For other Igors:**
- Procedure applies identically on any machine
- Metadata file path is relative (~/TheIgors/design_docs/.dsb_metadata.txt)
- No system-specific hardcoding
- Each instance maintains its own metadata, but templates are identical

---

## Written By
Igor (wild-0001) — 2026-03-05  
Reviewed by: Akien  
Status: Ready to implement
