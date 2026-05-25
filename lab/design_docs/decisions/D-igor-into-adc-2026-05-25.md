# D-igor-into-adc-2026-05-25
**title:** Migrate Igor cognition code from TheIgors/wild_igor/ into UnseenUniversity/devices/igor/
**date:** 2026-05-25
**status:** open
**spawned_tickets:** T-igor-subtree-import, T-igor-import-rewrite, T-igor-theigers-archive, T-consequence-igor-migration

## Decision narrative
Igor's 273-file cognition engine (wild_igor/) has lived in a separate repo (TheIgors) as an inversion of the correct dependency direction. Igor is a device on the rack, not the host for everything. This decision migrates wild_igor/igor/ into UnseenUniversity/devices/igor/ using git subtree (full history preserved), rewrites all imports from wild_igor.igor.* → devices.igor.*, and converts TheIgors into a docs/skills/slates archive. Utility closet removal is tracked separately (T-remove-utility-closet-all with grep-based pass condition). Three alternatives were considered: no-merge (symlinks — rejected: already tried three times, still debt), copy-only (history lost — rejected: Akien wants history in single repo), and git filter-repo+merge (chosen).

## Hypothesis
Igor starts and runs exclusively from devices.igor.* imports inside UnseenUniversity; TheIgors contains no runnable Python source.

## Measurement Signal
`grep -rn 'wild_igor' ~/dev/src/UnseenUniversity/ --include='*.py'` returns zero results; Igor boots from new location; all tests pass.

## Goal Link
G-system-self-improving / architecture-separation: Igor is a device, UnseenUniversity is the platform.
