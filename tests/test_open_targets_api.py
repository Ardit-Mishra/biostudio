"""HTTP contracts for the read-only Open Targets source boundary."""

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

    def target_summary(self, ensembl_id: str):
        self.calls.append(ensembl_id)
        if self.error:
            raise self.error
        return self.records


def _artifact() -> SourceArtifact:
    return SourceArtifact(
        citation=Citation(
            source="open_targets",
            source_id="ENSG00000146648",
            retrieved_at="2026-09-18T12:00:00Z",
        ),
        title="EGFR: epidermal growth factor receptor",
        structured_record={"target_id": "ENSG00000146648"},
    )


def test_target_endpoint_exposes_target_annotations_but_not_evidence_claims(monkeypatch):
    """Source retrieval must not be mistaken for an agent-authored study finding."""
    source_client = _Client(records=[_artifact()])
    monkeypatch.setattr(prediction_api, "OpenTargetsClient", lambda: source_client)

    response = client.get("/v2/sources/open-targets/targets/ENSG00000146648")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == "open_targets"
    assert body["count"] == 1
    assert body["records"][0]["citation"]["source_id"] == "ENSG00000146648"
    assert "claim" not in body["records"][0]
    assert "outcome_direction" not in body["records"][0]
    assert source_client.calls == ["ENSG00000146648"]


def test_target_endpoint_reports_source_failure_without_leaking_graphql_details(monkeypatch):
    """Upstream errors must be explicit without exposing raw provider messages."""
    monkeypatch.setattr(
        prediction_api,
        "OpenTargetsClient",
        lambda: _Client(error=SourceLookupError("Open Targets upstream schema detail")),
    )

    response = client.get("/v2/sources/open-targets/targets/ENSG00000146648")

    assert response.status_code == 502
    assert response.json() == {
        "error": {"code": 502, "message": "Open Targets is temporarily unavailable"}
    }


def test_target_endpoint_rejects_non_ensembl_identifiers_at_the_http_boundary():
    """A caller cannot use this path to submit an arbitrary GraphQL variable."""
    response = client.get("/v2/sources/open-targets/targets/EGFR")

    assert response.status_code == 422
