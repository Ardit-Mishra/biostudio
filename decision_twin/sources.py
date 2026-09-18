"""Bounded connectors that normalize approved public evidence sources."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Protocol

import requests

from decision_twin.models import Citation, SourceArtifact


class SourceLookupError(RuntimeError):
    """An approved source could not provide a trustworthy response."""


class HTTPSession(Protocol):
    """The limited HTTP surface used by source connectors."""

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> Any: ...


class GraphQLSession(Protocol):
    """The limited GraphQL HTTP surface used by source connectors."""

    def post(self, url: str, *, json: dict[str, Any], timeout: float) -> Any: ...


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


class OpenTargetsClient:
    """Retrieve fixed target annotations from the Open Targets GraphQL API."""

    GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
    _ENSEMBL_GENE_ID = re.compile(r"ENSG\d{11}")
    TARGET_QUERY = """
        query TargetSummary($ensemblId: String!) {
          target(ensemblId: $ensemblId) {
            id
            approvedSymbol
            approvedName
            biotype
            tractability {
              label
              modality
              value
            }
          }
        }
    """

    def __init__(self, session: GraphQLSession | None = None, timeout_seconds: float = 15.0) -> None:
        self._session = session or requests.Session()
        self._timeout_seconds = timeout_seconds

    def target_summary(self, ensembl_id: str) -> list[SourceArtifact]:
        """Return one target annotation artifact, or no record for an unknown target."""
        normalized_id = ensembl_id.strip()
        if not self._ENSEMBL_GENE_ID.fullmatch(normalized_id):
            raise ValueError("ensembl_id must be a valid Ensembl gene identifier")

        try:
            response = self._session.post(
                self.GRAPHQL_URL,
                json={
                    "query": self.TARGET_QUERY,
                    "variables": {"ensemblId": normalized_id},
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as error:
            raise SourceLookupError("Open Targets lookup failed") from error

        if not isinstance(payload, dict) or payload.get("errors"):
            raise SourceLookupError("Open Targets returned an invalid response")
        try:
            target = payload["data"]["target"]
        except (KeyError, TypeError) as error:
            raise SourceLookupError("Open Targets returned an invalid response") from error
        if target is None:
            return []
        if not isinstance(target, dict):
            raise SourceLookupError("Open Targets returned an invalid target record")

        target_id = str(target.get("id") or "").strip()
        if not target_id:
            raise SourceLookupError("Open Targets returned an uncitable target record")

        symbol = str(target.get("approvedSymbol") or "").strip()
        approved_name = str(target.get("approvedName") or "").strip()
        title = f"{symbol}: {approved_name}" if symbol and approved_name else symbol or approved_name or target_id
        structured_record = {
            key: value
            for key, value in {
                "target_id": target_id,
                "approved_symbol": symbol or None,
                "approved_name": approved_name or None,
                "biotype": str(target.get("biotype") or "").strip() or None,
                "tractability": target.get("tractability") if isinstance(target.get("tractability"), list) else None,
            }.items()
            if value is not None
        }
        return [
            SourceArtifact(
                citation=Citation(
                    source="open_targets",
                    source_id=target_id,
                    retrieved_at=datetime.now(timezone.utc),
                ),
                title=title,
                structured_record=structured_record,
            )
        ]
