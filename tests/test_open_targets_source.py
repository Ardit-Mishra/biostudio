"""Boundary contracts for the registered Open Targets target connector."""

import pytest

from decision_twin.sources import OpenTargetsClient, SourceLookupError


class _Response:
    def __init__(self, payload, error: Exception | None = None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


class _Session:
    def __init__(self, response: _Response):
        self.response = response
        self.calls = []

    def post(self, url, *, json, timeout):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return self.response


def test_target_summary_normalizes_a_registered_open_targets_artifact():
    """The fixed query must retain target identity and source-provided annotations."""
    session = _Session(
        _Response(
            {
                "data": {
                    "target": {
                        "id": "ENSG00000146648",
                        "approvedSymbol": "EGFR",
                        "approvedName": "epidermal growth factor receptor",
                        "biotype": "protein_coding",
                        "tractability": [{"label": "High-Quality Ligand", "modality": "SM", "value": True}],
                    }
                }
            }
        )
    )

    result = OpenTargetsClient(session=session).target_summary("ENSG00000146648")

    assert len(result) == 1
    artifact = result[0]
    assert artifact.citation.source == "open_targets"
    assert artifact.citation.source_id == "ENSG00000146648"
    assert artifact.title == "EGFR: epidermal growth factor receptor"
    assert artifact.structured_record["biotype"] == "protein_coding"
    assert artifact.structured_record["tractability"][0]["modality"] == "SM"
    assert session.calls[0]["url"] == "https://api.platform.opentargets.org/api/v4/graphql"
    assert session.calls[0]["json"]["variables"] == {"ensemblId": "ENSG00000146648"}


def test_target_summary_rejects_non_ensembl_identifiers_before_the_network_call():
    """Callers cannot use this connector to submit arbitrary target strings."""
    session = _Session(_Response({"data": {"target": None}}))

    with pytest.raises(ValueError, match="Ensembl"):
        OpenTargetsClient(session=session).target_summary("EGFR")

    assert session.calls == []


def test_target_summary_returns_no_artifact_for_an_unknown_but_valid_target():
    """A missing target is distinct from a source transport failure."""
    session = _Session(_Response({"data": {"target": None}}))

    assert OpenTargetsClient(session=session).target_summary("ENSG00000146648") == []


def test_target_summary_converts_graphql_errors_into_a_source_boundary_error():
    """GraphQL error payloads cannot masquerade as empty target evidence."""
    session = _Session(_Response({"errors": [{"message": "upstream schema failure"}]}))

    with pytest.raises(SourceLookupError, match="Open Targets"):
        OpenTargetsClient(session=session).target_summary("ENSG00000146648")
