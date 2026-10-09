"""Read GEDCOM files: detect the character set, parse people and families.

No third-party dependency, so the app needs nothing but `streamlit`.
The 3D rendering itself happens in viewer.html.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LINE = re.compile(r"^\s*(\d+)\s+(?:(@[^@\s]+@)\s+)?(\S+)(?: (.*))?$")
CHAR = re.compile(rb"^\s*1\s+CHAR\s+(\S+)", re.M)


def decode_ged(raw: bytes) -> str:
    """Decode GED bytes (UTF-8/16, ANSI/Latin-1; ANSEL is read like ANSI)."""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw[:2] == b"0\x00":
        return raw.decode("utf-16-le")
    if raw[:2] == b"\x000":
        return raw.decode("utf-16-be")
    m = CHAR.search(raw[:4000])
    charset = m.group(1).decode("ascii", "ignore").upper() if m else ""
    if re.match(r"(ANSI|WINDOWS|CP1252|ISO|LATIN|IBMPC|ASCII)", charset):
        return raw.decode("cp1252", errors="replace")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


@dataclass
class Person:
    id: str
    given: str = ""
    surname: str = ""
    married: str = ""
    birth_year: int | None = None
    death_year: int | None = None
    famc: list[str] = field(default_factory=list)
    fams: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.given} {self.married or self.surname}".strip() or "?"

    def label(self, nee: str = "née") -> str:
        born = f" · * {self.birth_year}" if self.birth_year else ""
        maiden = f" ({nee} {self.surname})" if self.married and self.surname else ""
        return f"{self.name}{maiden}{born}"


@dataclass
class Tree:
    people: dict[str, Person]
    families: dict[str, dict]

    @property
    def years(self) -> list[int]:
        return sorted(p.birth_year for p in self.people.values() if p.birth_year)


def _year(value: str) -> int | None:
    if not value or value.upper().startswith(("BEF", "AFT")):
        return None
    m = re.search(r"\b(\d{3,4})\b", value)
    return int(m.group(1)) if m else None


def parse_ged(text: str) -> Tree:
    people: dict[str, Person] = {}
    families: dict[str, dict] = {}
    rec = None          # current record (person or family)
    lvl1 = ""           # current level-1 tag
    for raw in text.lstrip("﻿").splitlines():
        m = LINE.match(raw)
        if not m:
            continue
        lvl, xref, tag, val = int(m.group(1)), m.group(2), m.group(3).upper(), (m.group(4) or "").strip()
        if lvl == 0:
            lvl1 = ""
            if tag == "INDI" and xref:
                rec = people.setdefault(xref, Person(xref))
            elif tag == "FAM" and xref:
                rec = families.setdefault(xref, {"id": xref, "husb": None, "wife": None, "chil": []})
            else:
                rec = None
            continue
        if rec is None:
            continue
        if lvl == 1:
            lvl1 = tag
        if isinstance(rec, Person):
            if lvl == 1 and tag == "NAME" and not rec.given:
                sur = re.search(r"/(.*?)/", val)
                rec.surname = sur.group(1).strip() if sur else ""
                rec.given = re.sub(r"/.*?/", "", val).strip()
            elif lvl == 2 and lvl1 == "NAME" and tag == "GIVN":
                rec.given = val
            elif lvl == 2 and lvl1 == "NAME" and tag == "SURN":
                rec.surname = val
            elif lvl == 2 and lvl1 == "NAME" and tag == "_MARNM" and val != rec.surname:
                rec.married = val
            elif lvl == 2 and tag == "DATE" and lvl1 in ("BIRT", "CHR", "BAPM") and rec.birth_year is None:
                rec.birth_year = _year(val)
            elif lvl == 2 and tag == "DATE" and lvl1 in ("DEAT", "BURI") and rec.death_year is None:
                rec.death_year = _year(val)
            elif lvl == 1 and tag == "FAMC":
                rec.famc.append(val)
            elif lvl == 1 and tag == "FAMS":
                rec.fams.append(val)
        elif lvl == 1 and tag in ("HUSB", "WIFE"):
            rec[tag.lower()] = val
        elif lvl == 1 and tag == "CHIL":
            rec["chil"].append(val)
    return Tree(people, families)
