"""
cc1.py — CC.1 test minion: haiku-backed skill executor + tool-call interceptor.

CC.1 loads a skill (inline content or file path), feeds it to haiku as a
system prompt, and intercepts the resulting Bash calls WITHOUT executing them.
Smoke-test fidelity: passing means haiku would call the right things; failing
means something in the skill text is ambiguous or broken.

Usage:
    from agent_datacenter.test_minions.cc1 import CC1Minion
    minion = CC1Minion()
    result = minion.run_skill(
        task="Claim T-test-id",
        skill_content="## Step 2\\nAlways run: cc_queue.py claim T-test-id",
    )
    assert any("cc_queue.py claim" in c.input.get("command", "") for c in result.tool_calls)

Requires ANTHROPIC_API_KEY env var. Unit tests mock the Anthropic client and
never call the API; the live integration test is gated by the env var.

T-cc1-test-minion
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic

from lab.utility_closet.agent_base import AgentBase

_MODEL_DEFAULT = "claude-haiku-4-5-20251001"

_BASH_TOOL_DEF: dict[str, Any] = {
    "name": "Bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run"},
        },
        "required": ["command"],
    },
}

_SYSTEM_SUFFIX = """
You are following the skill above. Execute each step by calling the Bash tool.
Do NOT explain — act. Call Bash with the exact commands the skill instructs.
"""


@dataclass
class ToolCallRecord:
    """One intercepted tool call from the haiku response."""

    name: str
    input: dict[str, Any]


@dataclass
class RunResult:
    """Result of a CC.1 skill run."""

    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    stop_reason: str = "unknown"
    rounds: int = 0


class CC1Minion(AgentBase):
    """
    Haiku-backed skill executor.

    Intercepts Bash tool calls without executing them — callers assert on
    the captured calls to verify skill fidelity.
    """

    def __init__(
        self,
        model: str = _MODEL_DEFAULT,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )

    def run_skill(
        self,
        task: str,
        *,
        skill_content: str | None = None,
        skill_path: str | Path | None = None,
        max_rounds: int = 3,
    ) -> RunResult:
        """
        Run haiku against a skill + task, capturing tool calls.

        skill_content takes precedence over skill_path.
        If neither is given, task is sent as a bare user message.
        """
        if skill_content is None and skill_path is not None:
            skill_content = Path(skill_path).read_text()

        system = (
            (skill_content + _SYSTEM_SUFFIX)
            if skill_content
            else _SYSTEM_SUFFIX.strip()
        )

        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
        result = RunResult()

        for _ in range(max_rounds):
            result.rounds += 1
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system,
                tools=[_BASH_TOOL_DEF],
                messages=messages,
            )
            result.stop_reason = response.stop_reason or "unknown"

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            for block in tool_use_blocks:
                result.tool_calls.append(
                    ToolCallRecord(name=block.name, input=block.input)
                )

            if response.stop_reason != "tool_use" or not tool_use_blocks:
                break

            # Append assistant response + fake tool results so haiku can continue.
            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "OK",
                        }
                        for block in tool_use_blocks
                    ],
                }
            )

        return result
