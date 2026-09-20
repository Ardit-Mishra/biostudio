"""Narrowing by study design is narrowing by level of evidence."""

import pytest
from fastapi.testclient import TestClient

import api.prediction_api as prediction_api
from decision_twin.study_types import BY_KEY, STUDY_TYPES, narrow

client = TestClient(prediction_api.app, raise_server_exceptions=False)


class TestNarrowing:
    def test_any_design_does_not_touch_the_query(self):
        """Breadth is still available -- it just has to be asked for."""
        assert narrow("osimertinib EGFR", "any") == "osimertinib EGFR"

    def test_not_choosing_a_design_is_refused(self):
        """A default of "any" gave an unranked mix to a caller who never thought
        about study design, with no way to know it. Choosing is mandatory now;
        choosing breadth is not."""
        for absent in (None, "", "   "):
            with pytest.raises(ValueError, match="study_type is required"):
                narrow("osimertinib EGFR", absent)

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


class TestTheRouteRequiresAChoice:
    def test_omitting_study_type_is_refused(self):
        """No default: a caller who never considered study design must be told,
        not quietly handed an unranked mix."""
        response = client.get("/v2/sources/europe-pmc/search", params={"query": "osimertinib"})

        assert response.status_code == 422, response.text

    def test_choosing_breadth_explicitly_is_allowed(self):
        """Mandatory means chosen, not narrow. "any" is a legitimate answer."""
        assert narrow("osimertinib", "any") == "osimertinib"


class TestTheRejectionDoesNotRepeatTheInput:
    """A 422 names the designs that exist, not the one the caller invented.

    Stress-probing the running API found the rejection echoing the submitted
    `study_type` verbatim. It is a small reflection -- the value is already in
    the query string -- but it put caller-controlled text into a response body
    that travels to proxy logs and error trackers the study never touches, and
    it was the less useful half of the message: somebody who typed a wrong key
    needs the list of right ones, not their own typo returned to them.
    """

    def test_the_submitted_value_is_not_repeated(self):
        from decision_twin.study_types import narrow

        canary = "PRIVATE_CANARY_7d9f2c"
        with pytest.raises(ValueError) as caught:
            narrow("EGFR", canary)
        assert canary not in str(caught.value)

    def test_the_valid_designs_are_named_instead(self):
        from decision_twin.study_types import BY_KEY, narrow

        with pytest.raises(ValueError) as caught:
            narrow("EGFR", "not-a-design")
        message = str(caught.value)
        assert "randomized_trial" in message
        assert "any" in message
        for key in BY_KEY:
            assert key in message

    def test_the_route_does_not_echo_it_either(self):
        from fastapi.testclient import TestClient

        import api.prediction_api as prediction_api

        canary = "PRIVATE_CANARY_7d9f2c"
        client = TestClient(prediction_api.app)
        response = client.get(
            "/v2/sources/europe-pmc/search",
            params={"query": "EGFR", "page_size": 1, "study_type": canary},
        )
        assert response.status_code == 422
        assert canary not in response.text
