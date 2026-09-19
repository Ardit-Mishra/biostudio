"""Narrowing by study design is narrowing by level of evidence."""

import pytest
from fastapi.testclient import TestClient

import api.prediction_api as prediction_api
from decision_twin.study_types import BY_KEY, STUDY_TYPES, narrow

client = TestClient(prediction_api.app, raise_server_exceptions=False)


class TestNarrowing:
    def test_any_design_does_not_touch_the_query(self):
        assert narrow("osimertinib EGFR", "any") == "osimertinib EGFR"
        assert narrow("osimertinib EGFR", None) == "osimertinib EGFR"

    def test_a_design_appends_its_own_filter(self):
        narrowed = narrow("osimertinib EGFR", "case_report")
        assert narrowed == '(osimertinib EGFR) AND PUB_TYPE:"Case Reports"'

    def test_the_original_query_is_parenthesised(self):
        """Without the brackets, a query containing OR would silently rebind:
        `a OR b AND PUB_TYPE:x` is not `(a OR b) AND PUB_TYPE:x`."""
        assert narrow("a OR b", "randomized_trial").startswith("(a OR b) AND ")

    def test_an_unknown_design_is_refused_rather_than_ignored(self):
        """Silently returning everything would let a reader believe they were
        looking at randomized trials when they were looking at the whole index."""
        with pytest.raises(ValueError, match="unknown study_type"):
            narrow("osimertinib", "rct-ish")


class TestCatalogue:
    def test_every_design_states_what_it_cannot_support(self):
        """The caveat is the reason the filter exists; an empty one is a bug."""
        for study_type in STUDY_TYPES:
            assert study_type.supports.strip(), study_type.key
            assert study_type.cannot_support.strip(), study_type.key

    def test_the_case_report_caveat_names_the_actual_trap(self):
        assert "rate" in BY_KEY["case_report"].cannot_support.lower()

    def test_the_preprint_caveat_is_about_review_not_method(self):
        assert "review" in BY_KEY["preprint"].cannot_support.lower()

    def test_the_catalogue_is_served_so_the_client_cannot_drift(self):
        response = client.get("/v2/sources/study-types")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == len(STUDY_TYPES)
        assert {t["key"] for t in payload["study_types"]} == {t.key for t in STUDY_TYPES}
        for served in payload["study_types"]:
            assert served["cannot_support"]


class TestRouteContract:
    def test_an_unknown_study_type_is_a_422_not_a_500(self):
        response = client.get(
            "/v2/sources/europe-pmc/search",
            params={"query": "osimertinib", "study_type": "not-a-design"},
        )

        assert response.status_code == 422, response.text
        assert "unknown study_type" in response.json()["error"]["message"]
