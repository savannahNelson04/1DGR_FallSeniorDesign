"""Runs the engine on data/sample and checks every planted case in expected_matches."""
from datetime import date

import pytest

from conftest import SAMPLE
from matching import MatchingEngine, load_dataset
from matching.evaluate import evaluate

pytestmark = pytest.mark.skipif(not (SAMPLE / "json").exists() and not (SAMPLE / "csv").exists(),
                                reason="data/sample not found")
AS_OF = date(2026, 10, 22)   # the date the sample data was generated for


@pytest.fixture(scope="module")
def engine():
    return MatchingEngine(load_dataset(SAMPLE), as_of=AS_OF)


@pytest.mark.parametrize("kind", ["strong", "poor", "sparse_profile", "gate_excluded", "never_shown"])
def test_expected_matches(engine, kind):
    report = evaluate(engine)
    assert report[kind]["fail"] == 0, report[kind]["failures"]


def test_csv_and_json_give_same_scores(engine):
    csv_engine = MatchingEngine(load_dataset(SAMPLE / "csv"), as_of=AS_OF)
    cid = next(iter(engine.data.candidates))
    a = [(r.job_id, r.score) for r in engine.ranked_results_for_candidate(cid)]
    b = [(r.job_id, r.score) for r in csv_engine.ranked_results_for_candidate(cid)]
    assert a == b


def test_rankings_are_repeatable():
    a = MatchingEngine(load_dataset(SAMPLE), as_of=AS_OF)
    b = MatchingEngine(load_dataset(SAMPLE), as_of=AS_OF)
    for cid in list(a.data.candidates)[:20]:
        assert [r.job_id for r in a.ranked_results_for_candidate(cid)] == \
               [r.job_id for r in b.ranked_results_for_candidate(cid)]


def test_all_scores_in_range(engine):
    assert all(0 <= r.score <= 100 for r in engine.score_all())
