# D-encapsulation-audit-2026-05-21
**title:** Encapsulation as first-class design principle — audit-design Check 10 + expert lens
**date:** 2026-05-21
**status:** open
**spawned_tickets:** T-audit-design-check-encapsulation, T-audit-expert-encapsulation-lens, T-consequence-encapsulation-audit

## Decision narrative
Encapsulation is a governing design principle (established by DB proxy, inference proxy, ADC, queue-as-black-box). Formalizing it as a recurring audit check (audit-design Check 10) and expert lens (Systems Architect + Process/Meta in EXPERTS.md) ensures future designs are reviewed through this lens before tickets are filed. The question "what could we be encapsulating that we're not?" becomes a standard part of every design review.

## Hypothesis
Future designs have smaller, more explicit interfaces because the audit catches cross-cutting reach early.

## Measurement Signal
audit-design Check 10 fires on at least one real design in the next 30 days; the Systems Architect expert surfaces at least one encapsulation finding in an audit-expert run within 30 days.

## Goal Link
3.6 (CC/Librarian/Igor system improves its own design through auditing).
