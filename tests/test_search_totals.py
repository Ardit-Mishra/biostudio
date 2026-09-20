"""A page of results must carry its own denominator.

The search routes reported `count`, which was `len(records)` -- the size of the
page, named as though it were the size of the result. A reader shown five
records could not tell whether five was the entire evidence base or the visible
corner of it. Against the live sources that difference was six versus 5,974 for
the same query, and nothing on the page or in the export distinguished them.

These tests pin that a source's own total is read where the source reports one,
and that an absent total stays absent rather than being rounded down to zero --
"this source does not say" and "there are none" are different claims, and a
synthesis built on the second when the first is true is wrong.
"""

from __future__ import annotations

import pytest

from decision_twin.sources import EuropePMCClient, OpenAlexClient, SearchPage, _reported_total


class StubResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class StubSession:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.calls: list[dict] = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params})
        return StubResponse(self._payload)

    def post(self, url, json=None, timeout=None):  # pragma: no cover - unused here
        raise AssertionError("search must not POST")


EPMC_RESULT = {
    "pmid": "41524570",
    "title": "A Randomized Phase II Study",
    "abstractText": "Pancreatic ductal adenocarcinoma remains highly lethal.",
    "firstPublicationDate": "2026-01-01",
}


class TestReportedTotal:
    def test_reads_a_plain_integer(self):
        assert _reported_total(6) == 6

    def test_zero_is_a_real_total(self):
        assert _reported_total(0) == 0

    def test_absent_stays_absent(self):
        assert _reported_total(None) is None

    def test_a_bool_is_not_a_count(self):
        """`True` is an int in Python, and a count of True would be nonsense."""
        assert _reported_total(True) is None

    def test_nonsense_is_rejected_rather_than_coerced(self):
        assert _reported_total("many") is None
        assert _reported_total(-3) is None


class TestEuropePMCTotals:
    def test_hit_count_is_carried_through(self):
        session = StubSession({"hitCount": 6, "resultList": {"result": [EPMC_RESULT]}})
        page = EuropePMCClient(session=session).search_page("KRAS G12C pancreatic", page_size=5)
        assert isinstance(page, SearchPage)
        assert page.total_hits == 6
        assert len(page.records) == 1

    def test_a_missing_hit_count_is_none_not_zero(self):
        session = StubSession({"resultList": {"result": [EPMC_RESULT]}})
        page = EuropePMCClient(session=session).search_page("q", page_size=5)
        assert page.total_hits is None

    def test_search_still_returns_records_for_existing_callers(self):
        session = StubSession({"hitCount": 6, "resultList": {"result": [EPMC_RESULT]}})
        records = EuropePMCClient(session=session).search("q", page_size=5)
        assert isinstance(records, list)
        assert len(records) == 1


class TestOpenAlexTotals:
    def test_meta_count_is_carried_through(self):
        session = StubSession({
            "meta": {"count": 5974},
            "results": [{
                "id": "https://openalex.org/W123",
                "display_name": "A work",
                "publication_year": 2026,
            }],
        })
        page = OpenAlexClient(session=session).search_page("KRAS G12C pancreatic", page_size=5)
        assert page.total_hits == 5974

    def test_total_survives_an_empty_result_list(self):
        """A total with no page is still information: the filter was too narrow."""
        session = StubSession({"meta": {"count": 12}, "results": []})
        page = OpenAlexClient(session=session).search_page("q", page_size=5)
        assert page.total_hits == 12
        assert page.records == []

    def test_absent_meta_is_none(self):
        session = StubSession({"results": []})
        page = OpenAlexClient(session=session).search_page("q", page_size=5)
        assert page.total_hits is None


class TestPageSizeIsStillBounded:
    @pytest.mark.parametrize("bad", [0, -1, 999])
    def test_out_of_range_page_size_is_refused(self, bad):
        session = StubSession({"hitCount": 1, "resultList": {"result": []}})
        with pytest.raises(ValueError):
            EuropePMCClient(session=session).search_page("q", page_size=bad)
