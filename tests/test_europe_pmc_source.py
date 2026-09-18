"""Boundary contracts for the registered Europe PMC literature connector."""

import pytest

from decision_twin.sources import EuropePMCClient, SourceLookupError


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


def test_search_normalizes_a_literature_record_into_a_registered_source_artifact():
    """Changing the source tag or dropping retained metadata must fail this test."""
    session = _Session(
        _Response(
            {
                "resultList": {
                    "result": [
                        {
                            "source": "MED",
                            "id": "12345678",
                            "pmid": "12345678",
                            "title": "EGFR evidence in a public research record",
                            "abstractText": "A source-backed abstract used for research triage.",
                            "journalTitle": "Example Journal",
                            "pubYear": "2024",
                            "authorString": "Example A; Researcher B",
                        }
                    ]
                }
            }
        )
    )

    result = EuropePMCClient(session=session).search("EGFR AND NSCLC", page_size=5)

    assert len(result) == 1
    record = result[0]
    assert record.citation.source == "europe_pmc"
    assert record.citation.source_id == "12345678"
    assert record.excerpt == "A source-backed abstract used for research triage."
    assert record.structured_record["journal"] == "Example Journal"
    assert session.calls == [
        {
            "url": "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            "params": {"query": "EGFR AND NSCLC", "format": "json", "pageSize": 5, "resultType": "core"},
            "timeout": 15.0,
        }
    ]


def test_search_drops_unidentified_results_instead_of_inventing_a_citation():
    """A record without a stable Europe PMC identifier is not evidence."""
    session = _Session(_Response({"resultList": {"result": [{"title": "No identifier"}]}}))

    result = EuropePMCClient(session=session).search("EGFR")

    assert result == []


def test_search_retains_a_minimal_but_citable_record():
    """Sparse source metadata cannot erase a real stable identifier."""
    session = _Session(
        _Response({"resultList": {"result": [{"id": "PMC123", "title": "Citable record"}]}})
    )

    result = EuropePMCClient(session=session).search("EGFR")

    assert result[0].citation.source_id == "PMC123"
    assert result[0].structured_record == {"europe_pmc_id": "PMC123", "record_id": "PMC123"}


def test_search_rejects_an_unbounded_page_request_before_calling_the_service():
    """A caller cannot bypass the connector's source-cost guardrail."""
    session = _Session(_Response({"resultList": {"result": []}}))

    with pytest.raises(ValueError, match="page_size"):
        EuropePMCClient(session=session).search("EGFR", page_size=21)

    assert session.calls == []


def test_search_converts_upstream_failure_into_a_source_boundary_error():
    """A source outage must not look like an empty evidence set."""
    session = _Session(_Response({}, error=RuntimeError("upstream unavailable")))

    with pytest.raises(SourceLookupError, match="Europe PMC"):
        EuropePMCClient(session=session).search("EGFR")
