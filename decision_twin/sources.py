"""Bounded connectors that normalize approved public evidence sources."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

import requests

from decision_twin.models import Citation, SourceArtifact


class SourceLookupError(RuntimeError):
    """An approved source could not provide a trustworthy response."""


class HTTPSession(Protocol):
    """The limited HTTP surface used by source connectors."""

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> Any: ...


class EuropePMCClient:
    """Retrieve bounded, citable literature records from Europe PMC."""

    SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    MAX_PAGE_SIZE = 20

    def __init__(self, session: HTTPSession | None = None, timeout_seconds: float = 15.0) -> None:
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds

    def search(self, query: str, *, page_size: int = 10) -> list[SourceArtifact]:
        """Return citable literature records without inventing missing metadata."""
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")
        if not 1 <= page_size <= self.MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {self.MAX_PAGE_SIZE}")

        try:
            response = self._session.get(
                self.SEARCH_URL,
                params={
                    "query": normalized_query,
                    "format": "json",
                    "pageSize": page_size,
                    "resultType": "core",
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as error:
            raise SourceLookupError("Europe PMC lookup failed") from error

        try:
            raw_results = payload["resultList"]["result"]
        except (KeyError, TypeError) as error:
            raise SourceLookupError("Europe PMC returned an invalid result payload") from error
        if not isinstance(raw_results, list):
            raise SourceLookupError("Europe PMC returned an invalid result payload")

        return [
            artifact
            for raw_result in raw_results
            if (artifact := self._to_artifact(raw_result)) is not None
        ]

    @staticmethod
    def _to_artifact(raw_result: object) -> SourceArtifact | None:
        if not isinstance(raw_result, dict):
            return None

        source_id = str(raw_result.get("pmid") or raw_result.get("id") or "").strip()
        title = str(raw_result.get("title") or "").strip()
        if not source_id or not title:
            return None

        abstract = str(raw_result.get("abstractText") or "").strip() or None
        structured_record = {
            key: value
            for key, value in {
                "europe_pmc_id": source_id,
                "record_id": str(raw_result.get("id") or "").strip() or None,
                "record_source": str(raw_result.get("source") or "").strip() or None,
                "journal": str(raw_result.get("journalTitle") or "").strip() or None,
                "publication_year": str(raw_result.get("pubYear") or "").strip() or None,
                "authors": str(raw_result.get("authorString") or "").strip() or None,
            }.items()
            if value is not None
        }
        return SourceArtifact(
            citation=Citation(
                source="europe_pmc",
                source_id=source_id,
                retrieved_at=datetime.now(timezone.utc),
            ),
            title=title,
            excerpt=abstract,
            structured_record=structured_record,
        )
