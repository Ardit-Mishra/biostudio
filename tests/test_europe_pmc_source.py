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


def test_a_long_abstract_is_trimmed_to_the_excerpt_contract_and_marked():
    """Regression: a real-length abstract used to 500 the search endpoint.

    SourceArtifact.excerpt is capped at 2000 characters because the contract is a
    short citable excerpt, not a redistributed abstract. The connector passed
    Europe PMC's abstractText straight through, so any ordinary query returning a
    long abstract raised a pydantic ValidationError and the endpoint answered 500.
    Every fixture in this file was short, so nothing failed until a live search
    ran. The trim has to stay at the connector boundary, and it has to be visible
    -- a reader must be able to tell the excerpt was cut.
    """
    abstract = "Osimertinib resistance in EGFR-mutant NSCLC is multifactorial. " * 60
    assert len(abstract) > 2_000

    session = _Session(
        _Response(
            {
                "resultList": {
                    "result": [
                        {
                            "source": "MED",
                            "id": "40000001",
                            "title": "Acquired resistance mechanisms to osimertinib",
                            "abstractText": abstract,
                            "journalTitle": "Journal of Thoracic Oncology",
                            "pubYear": "2025",
                        }
                    ]
                }
            }
        )
    )

    artifacts = EuropePMCClient(session=session).search("osimertinib resistance")

    assert len(artifacts) == 1
    excerpt = artifacts[0].excerpt
    assert excerpt is not None
    assert len(excerpt) <= 2_000, "excerpt must satisfy the ExcerptText contract"
    assert excerpt.endswith("…"), "a trimmed excerpt must say so"
    assert excerpt.startswith("Osimertinib resistance in EGFR-mutant NSCLC")


def test_a_short_abstract_is_retained_verbatim():
    """Trimming must not touch excerpts that already satisfy the contract."""
    session = _Session(
        _Response(
            {
                "resultList": {
                    "result": [
                        {
                            "source": "MED",
                            "id": "40000002",
                            "title": "A concise report",
                            "abstractText": "EGFR L858R confers osimertinib sensitivity in vitro.",
                        }
                    ]
                }
            }
        )
    )

    artifacts = EuropePMCClient(session=session).search("egfr l858r")

    assert artifacts[0].excerpt == "EGFR L858R confers osimertinib sensitivity in vitro."
    assert "…" not in artifacts[0].excerpt


def test_search_normalizes_abstract_markup_into_readable_excerpt_text():
    """Europe PMC formatting must not leak raw tags into every research client."""
    session = _Session(
        _Response(
            {
                "resultList": {
                    "result": [
                        {
                            "source": "MED",
                            "id": "40000003",
                            "title": "A formatted abstract",
                            "abstractText": "<h4>Background</h4> EGFR &amp; MET were measured.<br/>Results were retained.",
                        }
                    ]
                }
            }
        )
    )

    artifacts = EuropePMCClient(session=session).search("egfr met")

    assert artifacts[0].excerpt == "Background EGFR & MET were measured. Results were retained."


def test_escaped_markup_in_a_title_does_not_reach_the_reader():
    """Regression: titles arrive with escaped markup and rendered literally.

    Europe PMC returns e.g. "Acquired &lt;i&gt;EML4-ALK&lt;/i&gt; fusion". One
    parser pass with convert_charrefs=True decodes the entities but never
    re-tokenises the result, so "<i>" survived as visible characters in the UI.
    Abstracts went through the reader; titles did not go through it at all.
    """
    session = _Session(
        _Response(
            {
                "resultList": {
                    "result": [
                        {
                            "source": "MED",
                            "id": "40000003",
                            "title": "Acquired &lt;i&gt;EML4-ALK&lt;/i&gt; fusion and &lt;i&gt;BRAF&lt;/i&gt; mutation",
                            "abstractText": "An abstract with &lt;sup&gt;13&lt;/sup&gt;C labelling &amp; markup.",
                        }
                    ]
                }
            }
        )
    )

    artifact = EuropePMCClient(session=session).search("egfr")[0]

    assert artifact.title == "Acquired EML4-ALK fusion and BRAF mutation"
    assert "<" not in artifact.title and "&lt;" not in artifact.title
    assert artifact.excerpt is not None
    assert "<" not in artifact.excerpt and "&lt;" not in artifact.excerpt
    # An ampersand is content, not markup, and must survive.
    assert "&" in artifact.excerpt
