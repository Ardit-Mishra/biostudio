"""HTTP contracts for the read-only ChEMBL compound boundary."""

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

    def compound_summary(self, chembl_id: str):
        self.calls.append(chembl_id)
        if self.error:
            raise self.error
        return self.records


def _artifact() -> SourceArtifact:
    return SourceArtifact(
        citation=Citation(
            source="chembl",
            source_id="CHEMBL3353410",
            retrieved_at="2026-09-19T12:00:00Z",
        ),
        title="OSIMERTINIB",
        structured_record={"chembl_id": "CHEMBL3353410"},
    )


def test_compound_endpoint_exposes_artifacts_without_promoting_them_to_evidence(monkeypatch):
    source_client = _Client(records=[_artifact()])
    monkeypatch.setattr(prediction_api, "ChEMBLClient", lambda: source_client)

    response = client.get("/v2/sources/chembl/compounds/CHEMBL3353410")

    assert response.status_code == 200, response.text
    assert response.json()["source"] == "chembl"
    assert response.json()["records"][0]["citation"]["source_id"] == "CHEMBL3353410"
    assert "claim" not in response.json()["records"][0]
    assert source_client.calls == ["CHEMBL3353410"]


def test_compound_endpoint_redacts_source_transport_details(monkeypatch):
    monkeypatch.setattr(
        prediction_api,
        "ChEMBLClient",
        lambda: _Client(error=SourceLookupError("ChEMBL failed: private network detail")),
    )

    response = client.get("/v2/sources/chembl/compounds/CHEMBL3353410")

    assert response.status_code == 502
    assert response.json() == {
        "error": {"code": 502, "message": "ChEMBL is temporarily unavailable"}
    }


def test_compound_endpoint_rejects_non_compound_identifiers_before_contacting_source():
    response = client.get("/v2/sources/chembl/compounds/CHEMBL3353410%2Factivities")

    assert response.status_code == 404
