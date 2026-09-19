"""A client mistake must never come back as 500.

Both regressions here were found by pressure-testing the running API rather than
by the unit suite, and both turned an ordinary bad request into "Internal server
error" -- the one response that tells a caller nothing and points the blame at
the wrong side.
"""

from fastapi.testclient import TestClient

import api.prediction_api as prediction_api

RATIONALE = "The cited record reports this outcome for the stated assay context."

client = TestClient(prediction_api.app, raise_server_exceptions=False)


def _record(**over):
    base = {
        "id": "ev-1",
        "claim": "An observation bounded to its record.",
        "citation": {
            "source": "europe_pmc",
            "source_id": "40000001",
            "retrieved_at": "2026-09-19T00:00:00Z",
        },
        "excerpt": "Retained excerpt.",
        "assay_context": {
            "target_id": "ENSG00000146648",
            "biological_system": "cell_line",
            "readout": "viability_ic50",
            "unit": "nM",
        },
        "outcome_direction": "supports",
        "direction_rationale": RATIONALE,
    }
    base.update(over)
    return base


class TestValidatorErrorsAreClientErrors:
    """Regression: a model_validator failure used to 500.

    Pydantic stores the original exception object in `ctx["error"]` when a
    `model_validator` raises. JSONResponse cannot serialize an exception, so the
    validation handler itself raised `TypeError: Object of type ValueError is
    not JSON serializable`, fell through to the unhandled-exception handler, and
    answered 500.

    It was the most likely mistake a caller can make while assembling a study:
    posting an EvidenceRecord with neither a structured_record nor an excerpt.
    """

    def test_evidence_without_retained_support_is_422_not_500(self):
        response = client.post(
            "/v2/decision-twins/compile",
            json={
                "study_id": "no-support",
                "evidence": [_record(excerpt=None, structured_record=None)],
            },
        )

        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == 422

    def test_the_validator_message_survives_into_the_response(self):
        """Stringifying ctx must keep the reason, not just the status."""
        response = client.post(
            "/v2/decision-twins/compile",
            json={
                "study_id": "no-support",
                "evidence": [_record(excerpt=None, structured_record=None)],
            },
        )

        details = response.json()["error"]["details"]
        assert any(
            "structured_record or excerpt" in str(detail.get("msg", "")) for detail in details
        ), details

    def test_the_whole_error_envelope_is_json_serializable(self):
        """The failure was inside the handler, so serializing it is the test."""
        response = client.post(
            "/v2/decision-twins/compile",
            json={
                "study_id": "no-support",
                "evidence": [_record(excerpt=None, structured_record=None)],
            },
        )

        # .json() would raise if any value had leaked through unserialized.
        payload = response.json()
        for detail in payload["error"]["details"]:
            for value in detail.get("ctx", {}).values():
                assert isinstance(value, str), f"ctx carries a non-string: {value!r}"

    def test_a_plain_field_violation_still_reports_422(self):
        """The fix must not change the path that already worked."""
        response = client.post(
            "/v2/decision-twins/compile",
            json={"study_id": "long-claim", "evidence": [_record(claim="c" * 4_001)]},
        )

        assert response.status_code == 422, response.text


class TestBlankSourceQuery:
    """Regression: a whitespace-only query used to 500.

    `Query(min_length=1)` counts characters, not content, so "   " passed the
    route signature and then raised ValueError inside EuropePMCClient.search.
    """

    def test_whitespace_only_query_is_422_not_500(self):
        response = client.get("/v2/sources/europe-pmc/search", params={"query": "   ", "study_type": "any"})

        assert response.status_code == 422, response.text
        assert "blank" in response.json()["error"]["message"].lower()

    def test_an_empty_query_is_still_rejected_by_the_signature(self):
        response = client.get("/v2/sources/europe-pmc/search", params={"query": "", "study_type": "any"})

        assert response.status_code == 422
