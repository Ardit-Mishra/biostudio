"""Bounds and leak guards on the decision path.

Four properties, each one a defect found by pressure-testing the running API
rather than by reading the code:

1. `conditions` and `structured_record` were unbounded. Every record posted is
   carried through comparison, hashing and export and echoed back on read, so
   an unbounded map is not just memory - it is memory multiplied by everything
   downstream of it.
2. The snapshot digest sorted object keys but not list order, so the same study
   re-posted with its evidence annotated in a different order hashed
   differently. The digest exists to answer "did the inputs change", and it was
   answering yes to a reordering.
3. Validation errors echoed the caller's submitted value. A 422 body reaches
   proxy logs and error trackers that the study itself never touches.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from decision_twin.compiler import snapshot_digest
from decision_twin.models import (
    MAX_CONDITIONS,
    MAX_RECORD_BYTES,
    MAX_RECORD_DEPTH,
    AssayContext,
    Citation,
    EvidenceRecord,
)


def citation(source_id: str = "PMC1") -> Citation:
    return Citation(source="europe_pmc", source_id=source_id, retrieved_at=datetime.now(timezone.utc))


def record(record_id: str, **kwargs) -> EvidenceRecord:
    payload = {
        "id": record_id,
        "claim": f"claim for {record_id}",
        "citation": citation(record_id),
        "excerpt": "a retained excerpt",
    }
    payload.update(kwargs)
    return EvidenceRecord(**payload)


class TestConditionsAreBounded:
    def test_accepts_a_reasonable_map(self):
        context = AssayContext(
            target_id="EGFR", biological_system="cellular", readout="IC50", unit="nM",
            conditions={"buffer": "HEPES", "temperature": "37C"},
        )
        assert context.conditions["buffer"] == "HEPES"

    def test_rejects_too_many_conditions(self):
        with pytest.raises(ValidationError):
            AssayContext(
                target_id="EGFR", biological_system="cellular", readout="IC50", unit="nM",
                conditions={f"k{i}": "v" for i in range(MAX_CONDITIONS + 1)},
            )

    def test_rejects_an_oversized_value(self):
        with pytest.raises(ValidationError):
            AssayContext(
                target_id="EGFR", biological_system="cellular", readout="IC50", unit="nM",
                conditions={"buffer": "x" * 5_000},
            )

    def test_rejects_an_oversized_key(self):
        with pytest.raises(ValidationError):
            AssayContext(
                target_id="EGFR", biological_system="cellular", readout="IC50", unit="nM",
                conditions={"k" * 5_000: "HEPES"},
            )


class TestStructuredRecordIsBounded:
    def test_accepts_an_ordinary_source_record(self):
        kept = record("r1", structured_record={"doi": "10.1/x", "authors": ["A", "B"]})
        assert kept.structured_record["doi"] == "10.1/x"

    def test_rejects_excessive_nesting(self):
        deep: dict = {"leaf": 1}
        for _ in range(MAX_RECORD_DEPTH + 3):
            deep = {"next": deep}
        with pytest.raises(ValidationError):
            record("r2", structured_record=deep)

    def test_rejects_an_oversized_record(self):
        """Two keys can still carry a megabyte, so size is measured on the encoding."""
        with pytest.raises(ValidationError):
            record("r3", structured_record={"blob": "x" * (MAX_RECORD_BYTES + 1)})


class TestDigestIsOrderIndependent:
    def test_same_evidence_in_a_different_order_hashes_the_same(self):
        a, b, c = record("r1"), record("r2"), record("r3")
        forward = snapshot_digest(study_id="s", evidence=[a, b, c], model_assessments=[])
        shuffled = snapshot_digest(study_id="s", evidence=[c, a, b], model_assessments=[])
        assert forward == shuffled

    def test_model_assessment_order_does_not_change_the_digest(self):
        one = {"endpoint": "herg", "value": 0.2}
        two = {"endpoint": "logp", "value": 3.1}
        forward = snapshot_digest(study_id="s", evidence=[], model_assessments=[one, two])
        shuffled = snapshot_digest(study_id="s", evidence=[], model_assessments=[two, one])
        assert forward == shuffled

    def test_a_real_change_still_changes_the_digest(self):
        """Order-independence must not become blindness to content."""
        before = snapshot_digest(study_id="s", evidence=[record("r1")], model_assessments=[])
        after = snapshot_digest(study_id="s", evidence=[record("r1", claim="different")], model_assessments=[])
        assert before != after

    def test_study_id_still_participates(self):
        left = snapshot_digest(study_id="s1", evidence=[record("r1")], model_assessments=[])
        right = snapshot_digest(study_id="s2", evidence=[record("r1")], model_assessments=[])
        assert left != right


class TestValidationErrorsDoNotEchoInput:
    def test_submitted_value_is_replaced_by_a_summary(self):
        from api.prediction_api import _serializable_errors

        secret = "unpublished-compound-AZ-99817"
        cleaned = _serializable_errors(
            [{"type": "string_too_long", "loc": ("body", "claim"), "msg": "too long", "input": secret}]
        )
        assert "input" not in cleaned[0]
        assert cleaned[0]["input_summary"] == {"type": "str", "length": len(secret)}
        assert secret not in repr(cleaned)

    def test_validator_message_is_still_delivered(self):
        """Redaction must not cost the caller the reason for the rejection."""
        from api.prediction_api import _serializable_errors

        cleaned = _serializable_errors(
            [{
                "type": "value_error",
                "loc": ("body", "evidence", 0),
                "msg": "Value error, EvidenceRecord requires a structured_record or excerpt",
                "input": {"id": "r1"},
                "ctx": {"error": ValueError("EvidenceRecord requires a structured_record or excerpt")},
            }]
        )
        assert "structured_record or excerpt" in cleaned[0]["msg"]
        assert "structured_record or excerpt" in cleaned[0]["ctx"]["error"]
        assert cleaned[0]["input_summary"]["type"] == "dict"
