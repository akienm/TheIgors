# D-adc-web-control-station-2026-05-18
**title:** Web UI phase 2 — two-tab control station + palace browser + Akien as rack device
**date:** 2026-05-18
**status:** open
**spawned_tickets:** T-akien-rack-device, T-web-palace-read, T-web-palace-edit, T-web-two-tabs, T-web-akien-comms

## Decision narrative
Formalize Akien as a rack device (devices/akien/) so web and Discord traffic share a comms://akien/ address. Add server-side HTML palace browser pages to the existing web server (/goals, /decisions, /questions, /hypotheses, /outcomes, /health) — no build step, any browser. Restructure web UI into two tabs: comms/chat and a control station showing device health and IMAP bus traffic.

## Hypothesis
Adding palace browser pages + Akien device shim will make all project state browsable and messageable from any machine with a browser, with no build step or terminal required.

## Measurement Signal
Akien navigates to /health from a remote browser and sees all device statuses; navigates to /goals and sees G-xxx list; navigates to /decisions and sees D-xxx list with linked tickets.

## Goal Link
Goals tree §3.5 (remote access / design from anywhere) + §1.4 (Igor helps Akien organize his world)
