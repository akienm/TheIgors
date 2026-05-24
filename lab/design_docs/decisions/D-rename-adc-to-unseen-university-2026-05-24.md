# D-rename-adc-to-unseen-university-2026-05-24
**title:** Rename agent_datacenter repo to UnseenUniversity
**date:** 2026-05-24
**status:** closed
**spawned_tickets:** T-gh-rename-adc-to-uu, T-codebase-refs-adc-to-uu, T-local-dir-rename-adc-to-uu, T-consequence-rename-adc-to-uu

## Hypothesis
GitHub renamed, local path renamed, all source references updated to UnseenUniversity.

## Measurement Signal
`git remote -v` shows new URL + `grep -r UnseenUniversity .` clean on live code paths.

## Goal Link
none: platform naming hygiene — platform identity clarity before Igor migration begins

## Decision narrative
Rename the `UnseenUniversity` GitHub repo and local directory to `UnseenUniversity` — the portable agent platform gets a permanent Discworld-themed name reflecting its purpose as a research institution where agents live (Igor, Librarian, Scraps). Renaming `UnseenUniversity` rather than `TheIgors` because GitHub issues/discussions (#792, #7, all T- ticket GH links) are already there and redirect automatically on rename. Alternative considered: move UnseenUniversity into TheIgors repo; rejected because it would require migrating all GH issues/discussions to the renamed repo — painful and lossy.
