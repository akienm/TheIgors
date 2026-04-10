---
name: igor_never_anthropic_direct
description: Igor never calls Anthropic API directly — always routes through OpenRouter
type: feedback
---

Igor never uses the Anthropic account directly. All inference routes through OpenRouter, including haiku. Any code path that would call Anthropic direct (ChatAnthropic, ANTHROPIC_API_KEY, Anthropic() client) in Igor's runtime is wrong and should be replaced with the OpenRouter equivalent.

**Why:** Cost control and account separation. Claude Code uses the real Anthropic key; Igor uses OpenRouter. Keeping them separate is a hard rule.

**How to apply:** When writing or reviewing Igor tool code, if a fallback uses ChatAnthropic or Anthropic direct, replace it with ChatOpenRouter using the same or equivalent model slug (e.g. `anthropic/claude-haiku-4-5`). Missing OR key → raise RuntimeError, don't silently fall back to direct.
