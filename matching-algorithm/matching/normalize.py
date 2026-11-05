"""Turn raw profile and posting fields into comparable values. Pure functions, no I/O."""
from __future__ import annotations
import math
import re
from datetime import date, timedelta
from typing import Optional

from . import vocab

_WORD = re.compile(r"[a-z0-9+#./&-]+")
_STRIP = ".,;:!?()[]\"'"


# ------------------------------------------------------------------ text
def clean(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _stem(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def tokens(s: Optional[str]) -> list[str]:
    """Lowercase content words, light plural stemming, stopwords removed."""
    out = []
    for w in _WORD.findall(clean(s)):
        w = w.strip(_STRIP + "-./")
        if w and w not in vocab.STOPWORDS and not w.isdigit():
            out.append(_stem(w))
    return out


def cosine(a: list[str], b: list[str]) -> float:
    """Cosine similarity of two token lists, using term counts."""
    if not a or not b:
        return 0.0
    ca, cb = {}, {}
    for t in a: ca[t] = ca.get(t, 0) + 1
    for t in b: cb[t] = cb.get(t, 0) + 1
    dot = sum(v * cb.get(k, 0) for k, v in ca.items())
    na = math.sqrt(sum(v * v for v in ca.values())); nb = math.sqrt(sum(v * v for v in cb.values()))
    return dot / (na * nb) if na and nb else 0.0


def overlap(a: set, b: set) -> float:
    """Overlap coefficient: shared items / size of the smaller set."""
    return len(a & b) / min(len(a), len(b)) if a and b else 0.0


# ------------------------------------------------------------------ skills & values
def norm_skill(s: str) -> str:
    k = clean(s).strip(_STRIP)
    return vocab.SKILL_SYNONYMS.get(k, k)


def skill_set(items) -> set[str]:
    return {norm_skill(s) for s in items or [] if clean(s)}


def value_set(items) -> set[str]:
    return {clean(v) for v in items or [] if clean(v)}


# ------------------------------------------------------------------ titles & seniority
def _title_words(title: str) -> list[str]:
    return [w.strip(_STRIP) for w in re.split(r"[\s/,()-]+", clean(title)) if w.strip(_STRIP)]


def title_level(title: str) -> int:
    """0 intern, 1 entry, 2 mid, 3 senior, 4 lead/manager."""
    w = set(_title_words(title))
    if w & vocab.INTERN_WORDS:
        return 0
    if w & vocab.SENIOR_WORDS:
        return 3
    if w & vocab.MANAGER_WORDS:
        return 1 if w & {"assistant", "associate"} else 4   # "Assistant Project Manager" is entry level
    if w & vocab.MID_WORDS:
        return 2
    if w & vocab.ENTRY_WORDS:
        return 1
    return vocab.DEFAULT_TITLE_LEVEL


# Seniority words to drop when comparing what a role *is*. Coordinator, technician and
# representative stay, because they describe the job itself.
_LEVEL_WORDS = ((vocab.INTERN_WORDS | vocab.ENTRY_WORDS | vocab.MID_WORDS | vocab.SENIOR_WORDS)
                - {"coordinator", "technician", "representative"})


def role_tokens(title: str) -> set[str]:
    """Title words that describe the role itself, without seniority words."""
    return {_stem(w) for w in _title_words(title)
            if w not in _LEVEL_WORDS and w not in vocab.STOPWORDS and len(w) > 1}


def title_similarity(a: str, b: str) -> float:
    ta, tb = role_tokens(a), role_tokens(b)
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)


# ------------------------------------------------------------------ location
def metro(loc: Optional[str]) -> Optional[str]:
    """'Chicago, IL' -> 'chicago, il'; 'Remote (US)' -> 'remote'; blank -> None."""
    s = clean(loc)
    if not s:
        return None
    if s.startswith("remote"):
        return "remote"
    parts = [p.strip() for p in s.split(",")]
    return f"{parts[0]}, {parts[1][:2]}" if len(parts) >= 2 else parts[0]


# ------------------------------------------------------------------ pay
_MONEY = re.compile(r"\$?\s*(\d[\d,]*(?:\.\d+)?)\s*([kK])?")


def parse_salary(text: Optional[str], hours_per_year: int = 2080) -> Optional[tuple[float, float]]:
    """Return an annual (min, max) range in USD, or None if the text has no numbers ('Competitive', 'DOE')."""
    s = (text or "").strip()
    if not s:
        return None
    nums = []
    for m in _MONEY.finditer(s):
        v = float(m.group(1).replace(",", ""))
        if m.group(2):
            v *= 1000
        nums.append(v)
    if not nums:
        return None
    hourly = bool(re.search(r"/\s*h(ou)?r|per\s+hour|hourly|an hour", s, re.I)) or max(nums) < 300
    lo, hi = min(nums[:2]), max(nums[:2])
    if hourly:
        lo, hi = lo * hours_per_year, hi * hours_per_year
    return lo, hi


# ------------------------------------------------------------------ dates
_SEASON_START = {"spring": (1, 15), "summer": (6, 1), "fall": (9, 1), "autumn": (9, 1), "winter": (12, 1)}
_MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                       "august", "september", "october", "november", "december"], 1)}


def parse_availability(text: Optional[str], as_of: date) -> Optional[date]:
    """'Immediately' -> as_of, 'Within 2 weeks' -> as_of + 14, 'Summer 2027' -> 2027-06-01."""
    s = clean(text)
    if not s:
        return None
    if s in ("immediately", "now", "asap"):
        return as_of
    m = re.match(r"within (\d+) (day|week|month)s?", s)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        return as_of + timedelta(days=n * {"day": 1, "week": 7, "month": 30}[unit])
    m = re.match(r"([a-z]+) (\d{4})", s)
    if m:
        word, year = m.group(1), int(m.group(2))
        if word in _MONTHS:
            return date(year, _MONTHS[word], 1)
        if word in _SEASON_START:
            mo, d = _SEASON_START[word]
            return date(year, mo, d)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def parse_date(s) -> Optional[date]:
    if isinstance(s, date):
        return s
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", str(s or "").strip())
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)) if m else None


def parse_days(s) -> Optional[int]:
    m = re.search(r"(\d+)", str(s or ""))
    return int(m.group(1)) if m else None


def years_between(start: Optional[date], end: Optional[date]) -> float:
    if not start or not end or end < start:
        return 0.0
    return (end - start).days / 365.25


# ------------------------------------------------------------------ education
def education_rank(level: Optional[str]) -> Optional[int]:
    return vocab.EDUCATION_RANK.get((level or "").strip().upper())
