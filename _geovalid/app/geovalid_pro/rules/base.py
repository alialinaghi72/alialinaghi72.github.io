"""Rule registry (01 §5.2, simplified for v0.1): one function per rule, declared inputs, catalogue metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

REGISTRY: list["RuleSpec"] = []


@dataclass
class RuleSpec:
    id: str
    fn: Callable
    needs: tuple[str, ...]
    note: str = ""


def rule(rule_id: str, needs: tuple[str, ...] = (), note: str = ""):
    """Register a rule. `needs` names inputs that must exist; otherwise the rule is NOT_APPLICABLE."""
    def deco(fn):
        REGISTRY.append(RuleSpec(rule_id, fn, needs, note))
        return fn
    return deco
