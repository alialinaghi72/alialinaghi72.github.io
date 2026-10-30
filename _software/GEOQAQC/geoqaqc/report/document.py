# -*- coding: utf-8 -*-
"""A small, neutral document model. The builder fills it once; the HTML and
Word writers each turn it into their format, so both carry the same report."""

from __future__ import annotations

import dataclasses
import datetime as _dt
import re
from dataclasses import dataclass, field


@dataclass
class ReportMeta:
    project: str = ""
    client: str = ""
    consultant: str = ""
    author: str = ""
    author_title: str = "کارشناس ارشد اکتشاف معدن"
    reviewer: str = ""
    approver: str = ""
    report_no: str = ""
    revision: str = "0"
    date: str = ""                  # ISO yyyy-mm-dd; today when empty
    location: str = ""
    logo_path: str = ""
    font_fa: str = "B Nazanin"      # Word only; the HTML embeds Vazirmatn
    font_latin: str = "Times New Roman"
    detail_elements: list = field(default_factory=list)
    include_cleaning_log: bool = True
    include_failed: bool = True
    include_protocol: bool = True

    @classmethod
    def from_dict(cls, d):
        names = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in (d or {}).items() if k in names})

    def the_date(self):
        try:
            return _dt.date.fromisoformat(self.date) if self.date else _dt.date.today()
        except ValueError:
            return _dt.date.today()


# ---- blocks ------------------------------------------------------------------
@dataclass
class Cover:
    meta: ReportMeta
    rating: str
    score: object
    verdicts: list          # [(element, persian name, verdict code)]
    stats: list             # [(label, value)]


@dataclass
class DocControl:
    meta: ReportMeta


@dataclass
class TOC:
    pass


@dataclass
class Heading:
    level: int
    text: str
    anchor: str = ""
    number: str = ""


@dataclass
class Para:
    text: str
    style: str = "body"     # body | lead | note | small


@dataclass
class Bullets:
    items: list
    ordered: bool = False


@dataclass
class Cell:
    text: str
    tone: str = ""          # critical | material | minor | ok | warn | fail | muted
    ltr: bool = False


@dataclass
class Table:
    header: list
    rows: list              # rows of str or Cell
    caption: str = ""
    widths: list = None     # relative column widths
    number: str = ""
    compact: bool = False


@dataclass
class FigureBlock:
    fig: object             # figures.Figure
    caption: str
    number: str = ""


@dataclass
class Callout:
    kind: str               # info | ok | warn | critical
    title: str
    text: str


@dataclass
class FindingCard:
    finding: object         # diagnosis.Finding


@dataclass
class VerdictGrid:
    items: list             # [(persian name, element code, verdict code, counts dict)]


@dataclass
class Signature:
    meta: ReportMeta


@dataclass
class PageBreak:
    pass


@dataclass
class Document:
    meta: ReportMeta
    blocks: list = field(default_factory=list)

    def add(self, *blocks):
        self.blocks.extend(blocks)


# ---- text runs ------------------------------------------------------------------
_BOLD = re.compile(r"\*\*(.+?)\*\*")
# parentheses stay outside a Latin run so the browser mirrors both of them
_LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_\-./+%']*(?:[ \t]+[A-Za-z0-9][A-Za-z0-9_\-./+%']*)*")


def split_runs(text):
    """'صدک P90 HARD برابر **۱۲٪**' ->
    [('صدک ', False, False), ('P90 HARD', True, False), (' برابر ', False, False),
     ('۱۲٪', False, True)]. Latin runs are isolated by the writers so that a
    Latin word never reorders the Persian sentence around it."""
    out = []
    pos = 0
    text = str(text)
    for m in _BOLD.finditer(text):
        out += _latin(text[pos:m.start()], False)
        out += _latin(m.group(1), True)
        pos = m.end()
    out += _latin(text[pos:], False)
    return [r for r in out if r[0]]


def _latin(s, bold):
    out, pos = [], 0
    for m in _LATIN.finditer(s):
        if m.start() > pos:
            out.append((s[pos:m.start()], False, bold))
        out.append((m.group(0), True, bold))
        pos = m.end()
    if pos < len(s):
        out.append((s[pos:], False, bold))
    return out
