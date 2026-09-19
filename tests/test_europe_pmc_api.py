"""HTTP contracts for the read-only Europe PMC source boundary."""

from fastapi.testclient import TestClient

import api.prediction_api as prediction_api
from decision_twin.models import Citation, SourceArtifact
from decision_twin.sources import SourceLookupError


client = TestClient(prediction_api.app)


class _Client:
    def __init__(self, records=None, error: Exception | None = None):
        self.records = records or []
        self.error = error
        self.calls = []

    def search(self, query: str, *, page_size: int):
        self.calls.append({"query": query, "page_size": page_size})
        if self.error:
            raise self.error
        return self.records


def _artifact() -> SourceArtifact:
    return SourceArtifact(
        citation=Citation(
            source="europe_pmc",
            source_id="12345678",
            retrieved_at="2026-09-18T12:00:00Z",
        ),
        title="EGFR literature record",
        excerpt="A retained source excerpt.",
        structured_record={"europe_pmc_id": "12345678"},
    )


def test_search_endpoint_exposes_normalized_artifacts_but_not_decision_claims(monkeypatch):
    """The public retrieval route must remain separate from study assembly."""
    source_client = _Client(records=[_artifact()])
    monkeypatch.setattr(prediction_api, "EuropePMCClient", lambda: source_client)

    response = client.get("/v2/sources/europe-pmc/search", params={"query": "EGFR AND NSCLC", "page_size": 5, "study_type": "any"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == "europe_pmc"
    assert body["count"] == 1
    assert body["records"][0]["citation"]["source_id"] == "12345678"
    assert "claim" not in body["records"][0]
    assert "outcome_direction" not in body["records"][0]
    assert source_client.calls == [{"query": "EGFR AND NSCLC", "page_size": 5}]


def test_search_endpoint_reports_a_source_outage_without_leaking_transport_details(monkeypatch):
    """A source failure cannot masquerade as zero evidence or expose internals."""
    monkeypatch.setattr(
        prediction_api,
        "EuropePMCClient",
        lambda: _Client(error=SourceLookupError("Europe PMC lookup failed: private network detail")),
    )

    response = client.get("/v2/sources/europe-pmc/search", params={"query": "EGFR", "study_type": "any"})

    assert response.status_code == 502
    assert response.json() == {
        "error": {"code": 502, "message": "Europe PMC is temporarily unavailable"}
    }


def test_search_endpoint_rejects_an_unbounded_page_size_before_contacting_the_source():
    """The HTTP surface preserves the connector's bounded retrieval policy."""
    response = client.get("/v2/sources/europe-pmc/search", params={"query": "EGFR", "page_size": 21, "study_type": "any"})

    assert response.status_code == 422
