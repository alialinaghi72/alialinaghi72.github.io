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


def closest_collars(hole_id, collar_ids, n: int = 3, cutoff: float = 0.6) -> list[str]:
    """SCH-04b: the most similar collar IDs to an orphan ID (difflib ratio on upper-case IDs). Suggestion only."""
    import difflib
    cands = {str(c).upper(): str(c) for c in collar_ids}
    hits = difflib.get_close_matches(str(hole_id).upper(), list(cands), n=n, cutoff=cutoff)
    return [cands[h] for h in hits]
