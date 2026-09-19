"""Boundary contracts for the bounded ChEMBL compound connector."""

import pytest

from decision_twin.sources import ChEMBLClient, SourceLookupError


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

    def get(self, url, *, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.response


def test_compound_summary_normalizes_only_a_citable_chembl_compound_record():
    session = _Session(
        _Response(
            {
                "molecule_chembl_id": "CHEMBL3353410",
                "pref_name": "OSIMERTINIB",
                "molecule_type": "Small molecule",
                "max_phase": 4,
                "molecule_structures": {"canonical_smiles": "COC1=CC=CC=C1"},
            }
        )
    )

    records = ChEMBLClient(session=session).compound_summary("chembl3353410")

    assert len(records) == 1
    record = records[0]
    assert record.citation.source == "chembl"
    assert record.citation.source_id == "CHEMBL3353410"
    assert record.title == "OSIMERTINIB"
    assert record.structured_record == {
        "chembl_id": "CHEMBL3353410",
        "molecule_type": "Small molecule",
        "max_phase": 4,
        "canonical_smiles": "COC1=CC=CC=C1",
    }
    assert session.calls == [
        {
            "url": "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL3353410.json",
            "params": {},
            "timeout": 30.0,
        }
    ]


def test_compound_summary_rejects_arbitrary_resource_paths_before_contacting_chembl():
    session = _Session(_Response({}))

    with pytest.raises(ValueError, match="ChEMBL compound identifier"):
        ChEMBLClient(session=session).compound_summary("CHEMBL3353410/activities")

    assert session.calls == []


def test_compound_summary_returns_no_record_for_an_empty_source_payload():
    session = _Session(_Response({"molecule_chembl_id": "CHEMBL3353410"}))

    assert ChEMBLClient(session=session).compound_summary("CHEMBL3353410") == []


def test_compound_summary_converts_transport_failures_to_a_source_boundary_error():
    session = _Session(_Response({}, error=RuntimeError("upstream unavailable")))

    with pytest.raises(SourceLookupError, match="ChEMBL"):
        ChEMBLClient(session=session).compound_summary("CHEMBL3353410")
