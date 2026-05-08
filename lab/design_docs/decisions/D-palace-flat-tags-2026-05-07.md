# D-palace-flat-tags-2026-05-07

**title:** Palace uses flat namespaces with tags, not nested project hierarchies
**date:** 2026-05-07
**status:** open
**spawned_tickets:** T-adc-palace-bootstrap (pending)

## Decision narrative

The original schema had `palace.projects.<name>.tickets.*` and `palace.projects.<name>.decisions.*`
as per-project subtrees. This was replaced with flat `palace.tickets.*` and `palace.decisions.*`
namespaces where project/domain membership is carried in `metadata.tags`. Prompted by Akien's
observation that the boundary between Igor, ADC, swadl, and other projects is nearly nonexistent
in his head — siloing by path hierarchy forces artificial barriers where none exist conceptually.
Tags allow a node to belong to multiple projects simultaneously, support cross-cutting search,
and match how both Akien and CC actually navigate (by topic/content, not by project container).
