"""
registry.py — Tool + ToolRegistry + ToolStats (UC canonical home).

T-uc-registry-move: moved from wild_igor/igor/tools/registry.py as the
prereq for inverting T-uc-budget-shelf and T-uc-filesystem-shelf. The
wild_igor-side file is now a thin re-export shim; any new import should
target lab.utility_closet.registry directly.

Tools are AI-agnostic: they describe their parameters once, and adapter
methods (to_anthropic_schema / to_openai_schema / to_text_description)
convert to whichever protocol the caller's reasoner speaks. The registry
is a process-singleton (`registry`) — tool modules self-register on
import.

Design choice: parent class is AgentBase (not IgorBase). The registry
does not need Igor-specific logging helpers (get_timer, paths().logs),
and using the UC base avoids a UC→wild_igor import loop that blocked
the earlier shelf-inversion attempts.

misfire_counter is resolved lazily via absolute import, so the
registry doesn't pull wild_igor.igor at module-load time.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from .agent_base import AgentBase


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict  # JSON Schema for the parameters
    fn: Callable

    def execute(self, **kwargs) -> str:
        return self.fn(**kwargs)

    def to_anthropic_schema(self) -> dict:
        """Convert to Anthropic tool_use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def to_openai_schema(self) -> dict:
        """Convert to OpenAI function-calling format."""
        params = self.parameters
        # Normalize shorthand {param: {type, desc}} to full JSON Schema object.
        # OpenAI/gpt-4o-mini rejects schemas missing "type": "object" at top level.
        if params.get("type") != "object" and "properties" not in params:
            params = {
                "type": "object",
                "properties": params,
                "required": [],
            }
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": params,
            },
        }

    def to_text_description(self) -> str:
        """Plain text description for browser-based / text-only reasoners."""
        props = self.parameters.get("properties", {})
        params = ", ".join(
            f"{k}: {v.get('description', v.get('type', ''))}" for k, v in props.items()
        )
        return f"{self.name}({params})\n  {self.description}"


@dataclass
class ToolStats:
    """Per-tool call statistics. Keeps newest-1000 latency samples for percentiles.

    T-toolstats-sample-semantics-fix: previously used bisect.insort into a
    sorted list and pop(0) on overflow — which drops the fastest call, not
    the oldest, biasing p50/p95 toward slow as the buffer fills. Now uses a
    deque with maxlen=1000 for insertion-order eviction; percentile math
    sorts a snapshot on demand.
    """

    call_count: int = 0
    error_count: int = 0
    _samples: deque = field(default_factory=lambda: deque(maxlen=1000))

    _MAX_SAMPLES = 1000

    def record(self, elapsed_ms: int, success: bool) -> None:
        self.call_count += 1
        if not success:
            self.error_count += 1
        self._samples.append(elapsed_ms)

    @property
    def error_rate(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.error_count / self.call_count

    def _pct(self, p: int) -> int | None:
        if not self._samples:
            return None
        ordered = sorted(self._samples)
        idx = max(0, int(len(ordered) * p / 100) - 1)
        return ordered[idx]

    @property
    def p50(self) -> int | None:
        return self._pct(50)

    @property
    def p95(self) -> int | None:
        return self._pct(95)

    def to_dict(self) -> dict:
        return {
            "calls": self.call_count,
            "errors": self.error_count,
            "error_rate": round(self.error_rate, 4),
            "p50_ms": self.p50,
            "p95_ms": self.p95,
        }


class ToolRegistry(AgentBase):
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._stats: dict[str, ToolStats] = {}

    def register(self, tool: "Tool"):
        self._tools[tool.name] = tool
        return tool  # allows use as decorator (if tool is already an instance)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def execute(self, name: str, kwargs: dict) -> str:
        tool = self.get(name)
        if not tool:
            available = ", ".join(sorted(self._tools.keys()))
            return (
                f"Error: Unknown tool '{name}'. "
                f"Do not retry — use one of the available tools instead: {available}"
            )
        t0 = time.perf_counter()
        try:
            result = tool.execute(**kwargs)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            success = not str(result).startswith("Error")
            self._record(name, elapsed_ms, success)
            return result
        except Exception as e:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            self._record(name, elapsed_ms, False)

            # Track repeated tool errors as misfires
            error_type = type(e).__name__
            self._record_misfire(name, error_type)

            return f"Error executing {name}: {e}"

    def _record(self, name: str, elapsed_ms: int, success: bool) -> None:
        if name not in self._stats:
            self._stats[name] = ToolStats()
        self._stats[name].record(elapsed_ms, success)

    def _record_misfire(self, tool_name: str, error_type: str) -> None:
        """Record a tool error for misfire tracking.

        Lazy absolute import to avoid UC→wild_igor import loops at load time.
        Non-critical — any failure is debug-logged and swallowed.
        """
        try:
            from wild_igor.igor.tools.misfire_counter import get_misfire_counter

            counter = get_misfire_counter()
            counter.record_tool_error(
                tool_name, error_type, dispatch_path="tool_execute"
            )
        except Exception as e:
            _log.debug(f"Failed to record misfire for {tool_name}: {e}")

    def tool_stats(self) -> dict[str, dict]:
        """Return per-tool stats dict, sorted by call count descending."""
        return {
            k: v.to_dict()
            for k, v in sorted(
                self._stats.items(), key=lambda x: x[1].call_count, reverse=True
            )
        }

    def to_anthropic_schemas(self) -> list[dict]:
        return [t.to_anthropic_schema() for t in self.all()]

    def to_openai_schemas(self) -> list[dict]:
        return [t.to_openai_schema() for t in self.all()]

    def to_text_descriptions(self) -> str:
        """All tools described in plain text - for non-API reasoners."""
        return "\n\n".join(t.to_text_description() for t in self.all())


# Global registry - tools register themselves on import
registry = ToolRegistry()
