"""Candidate <-> Job matching algorithm (AI Matching Buildout prototype)."""
from .config import MatchConfig
from .engine import MatchingEngine
from .loader import load_dataset
from .store import write_results

__all__ = ["MatchConfig", "MatchingEngine", "load_dataset", "write_results"]
