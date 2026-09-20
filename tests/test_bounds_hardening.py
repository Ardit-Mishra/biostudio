"""The bound has to reject the payload, not die trying to measure it.

The structured-record depth check walked only dicts and lists. A fifty-deep
tuple measured as depth 2, passed the bound it should have failed, and then
blew up later during JSON encoding for the digest or the export -- past the
point where a clean 422 was still available. Sets had the same hole.

A review claimed the old recursive walk also exhausted the interpreter stack.
It did not: it returned early once it passed the limit, so it never recursed
deep enough. The traversal gap was real and the crash was not, which is why
the tuple case below is the one that discriminates between the two versions.

The OpenAlex route had the mirror-image gap. The study design is mandatory in
the interface, but the route accepted a search without one, so the product's
single required choice was reachable-around by calling the API directly.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import api.prediction_api as prediction_api
from decision_twin.models import (
    MAX_RECORD_DEPTH,
    Citation,
    DecisionTwinRequest,
    EvidenceRecord,
)

client = TestClient(prediction_api.app)


def record(record_id: str = "r1", **kwargs) -> EvidenceRecord:
    payload = {
        "id": record_id,
        "claim": "a bounded claim",
        "citation": Citation(
            source="europe_pmc", source_id=record_id, retrieved_at=datetime.now(timezone.utc)
        ),
        "excerpt": "a retained excerpt",
    }
    payload.update(kwargs)
    return EvidenceRecord(**payload)


def nested(depth: int, kind: str = "dict"):
    """Build a structure `depth` containers deep."""
    node: object = {"leaf": 1}
    for _ in range(depth):
        node = {"next": node} if kind == "dict" else ([node] if kind == "list" else (node,))
    return node if kind == "dict" else {"root": node}


class TestDepthCheckRejectsRatherThanCrashes:
    def test_a_pathologically_deep_record_is_refused(self):
        """Both versions reject this; it pins the behaviour rather than the fix."""
        with pytest.raises(ValidationError):
            record(structured_record=nested(5_000))

    def test_the_refusal_names_the_depth_bound(self):
        with pytest.raises(ValidationError) as caught:
            record(structured_record=nested(MAX_RECORD_DEPTH + 5))
        assert "nests deeper" in str(caught.value)

    def test_a_deep_tuple_is_caught_at_validation_not_at_export(self):
        """Traversing only dict and list let a tuple through to JSON encoding."""
        with pytest.raises(ValidationError):
            record(structured_record=nested(MAX_RECORD_DEPTH + 5, kind="tuple"))

    def test_a_deep_list_is_caught(self):
        with pytest.raises(ValidationError):
            record(structured_record=nested(MAX_RECORD_DEPTH + 5, kind="list"))

    def test_a_record_at_the_limit_is_still_accepted(self):
        """The bound must reject what is over it without rejecting what is under."""
        shallow = record(structured_record=nested(MAX_RECORD_DEPTH - 2))
        assert shallow.structured_record is not None

    def test_a_wide_but_shallow_record_is_accepted(self):
        """Width is bounded by size, not by the depth rule."""
        wide = record(structured_record={f"k{i}": i for i in range(200)})
        assert len(wide.structured_record) == 200


class TestModelAssessmentsAreBounded:
    def test_a_deep_model_assessment_is_refused(self):
        with pytest.raises(ValidationError):
            DecisionTwinRequest(
                study_id="s1",
                evidence=[record()],
                model_assessments=[nested(5_000)],
            )

    def test_an_ordinary_model_assessment_is_accepted(self):
        request = DecisionTwinRequest(
            study_id="s1",
            evidence=[record()],
            model_assessments=[{"endpoint": "herg", "value": 0.21}],
        )
        assert request.model_assessments[0]["endpoint"] == "herg"


class TestOpenAlexRouteRequiresADesign:
    """The design belongs to the study, so no lane may be searched without one."""

    def test_a_search_without_a_study_type_is_refused(self):
        response = client.get("/v2/sources/openalex/search", params={"query": "EGFR"})
        assert response.status_code == 422, response.text

    def test_an_unknown_study_type_is_refused(self):
        response = client.get(
            "/v2/sources/openalex/search",
            params={"query": "EGFR", "study_type": "not-a-design"},
        )
        assert response.status_code == 422, response.text

    def test_europe_pmc_also_refuses_an_absent_design(self):
        response = client.get("/v2/sources/europe-pmc/search", params={"query": "EGFR"})
        assert response.status_code == 422, response.text


class TestEuropePmcEchoesTheDesign:
    """The client's study-type list arrives from a separate fetch.

    A search issued before that fetch resolved recorded a null design in the
    exported record -- the one field the product refuses to make optional. The
    route therefore returns the design it actually applied, so the record never
    depends on a race in the client.
    """

    def test_the_applied_design_comes_back_with_the_results(self, monkeypatch):
        from decision_twin.sources import SearchPage

        class _Client:
            def search_page(self, query, *, page_size):
                return SearchPage(records=[], total_hits=0)

        monkeypatch.setattr(prediction_api, "EuropePMCClient", lambda: _Client())
        response = client.get(
            "/v2/sources/europe-pmc/search",
            params={"query": "EGFR", "study_type": "randomized_trial", "page_size": 5},
        )
        assert response.status_code == 200, response.text
        design = response.json()["study_design"]
        assert design["key"] == "randomized_trial"
        assert design["label"]
        assert design["cannot_support"]
