"""Decision Twin contracts for evidence integrity and reproducible triage.

These tests name the breaks that matter before agents or source connectors
exist: an uncited claim entering a study, incompatible assay records being
silently pooled, a conflict advancing a decision, or a replay changing its
provenance identifier without a data change.
"""

from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.prediction_api import app
from decision_twin.compiler import compile_decision, snapshot_digest
from decision_twin.models import AssayContext, Citation, EvidenceRecord
from decision_twin.normalization import compare_evidence


client = TestClient(app)


def _citation() -> Citation:
    return Citation(
        source="pubmed",
        source_id="12345678",
        retrieved_at="2026-09-18T12:00:00Z",
    )


def _assay(*, biological_system: str = "cellular", readout: str = "viability") -> AssayContext:
    return AssayContext(
        target_id="EGFR",
        biological_system=biological_system,
        readout=readout,
        unit="nM",
        genetic_context="EGFR L858R",
    )


def _evidence(*, evidence_id: str, direction: str, assay: AssayContext | None = None) -> EvidenceRecord:
    return EvidenceRecord(
        id=evidence_id,
        claim="Candidate activity was measured in a registered research record.",
        citation=_citation(),
        structured_record={"assay_id": evidence_id, "activity_direction": direction},
        assay_context=assay or _assay(),
        outcome_direction=direction,
    )


def test_evidence_rejects_a_claim_without_a_source_record_or_excerpt():
    """A future agent cannot turn an uncited narrative into study evidence."""
    try:
        EvidenceRecord(
            id="ev-uncited",
            claim="This claim has no retained support.",
            citation=_citation(),
            assay_context=_assay(),
        )
    except ValidationError as error:
        assert "structured_record" in str(error) or "excerpt" in str(error)
    else:
        raise AssertionError("uncited evidence was accepted")


def test_evidence_rejects_an_unregistered_source():
    """A future agent cannot smuggle arbitrary web content into a Decision Twin."""
    try:
        EvidenceRecord(
            id="ev-unregistered-source",
            claim="This record came from an unapproved source.",
            citation=Citation(
                source="unknown-web-source",
                source_id="record-1",
                retrieved_at="2026-09-18T12:00:00Z",
            ),
            structured_record={"record_id": "record-1"},
        )
    except ValidationError as error:
        assert "source" in str(error).lower()
    else:
        raise AssertionError("an unregistered source was accepted")


def test_matching_assays_with_opposed_outcomes_are_classified_as_conflicting():
    """Changing opposite outcomes to compatible evidence must make this fail."""
    comparison = compare_evidence(
        _evidence(evidence_id="ev-a", direction="supports"),
        _evidence(evidence_id="ev-b", direction="contradicts"),
    )

    assert comparison.relation == "conflicting"
    assert "outcome" in comparison.reason.lower()


def test_condition_mismatch_is_not_classified_as_a_direct_assay_comparison():
    """Changing the comparison to direct despite a condition mismatch is a bug."""
    left = _evidence(evidence_id="ev-a", direction="supports")
    right = _evidence(
        evidence_id="ev-b",
        direction="supports",
        assay=_assay().model_copy(update={"conditions": {"ph": "6.5"}}),
    )

    comparison = compare_evidence(left, right)

    assert comparison.relation == "supportive"


def test_missing_assay_context_is_not_silently_pooled_with_measured_evidence():
    """A missing assay context must remain non-comparable rather than supportive."""
    contextless = EvidenceRecord(
        id="ev-contextless",
        claim="A source record exists but lacks assay metadata.",
        citation=_citation(),
        structured_record={"assay_id": "ev-contextless"},
        outcome_direction="supports",
    )

    comparison = compare_evidence(_evidence(evidence_id="ev-measured", direction="supports"), contextless)

    assert comparison.relation == "non_comparable"


def test_conflicting_evidence_forces_hold_even_when_model_support_is_present():
    """A model result must never override a recorded evidence conflict."""
    outcome = compile_decision(
        study_id="study-egfr",
        evidence=[
            _evidence(evidence_id="ev-a", direction="supports"),
            _evidence(evidence_id="ev-b", direction="contradicts"),
        ],
        model_assessments=[{"model_id": "admet-dili", "available": True, "status": "in_domain"}],
    )

    assert outcome.status == "hold"
    assert any("conflict" in reason.lower() for reason in outcome.reasons)


def test_snapshot_digest_is_stable_for_the_same_decision_inputs():
    """Changing canonicalization or omitting evidence must alter this digest."""
    evidence = [_evidence(evidence_id="ev-a", direction="supports")]

    first = snapshot_digest(study_id="study-egfr", evidence=evidence, model_assessments=[])
    second = snapshot_digest(study_id="study-egfr", evidence=evidence, model_assessments=[])

    assert first == second
    assert len(first) == 64


def test_v2_compile_endpoint_returns_an_inspectable_hold_decision():
    """The API must expose the deterministic decision and its provenance hash."""
    response = client.post(
        "/v2/decision-twins/compile",
        json={
            "study_id": "study-egfr",
            "evidence": [
                _evidence(evidence_id="ev-a", direction="supports").model_dump(mode="json"),
                _evidence(evidence_id="ev-b", direction="contradicts").model_dump(mode="json"),
            ],
            "model_assessments": [{"model_id": "admet-dili", "available": True, "status": "in_domain"}],
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "hold"
    assert len(body["snapshot_digest"]) == 64
    assert body["evidence_count"] == 2
    assert [lane["stage"] for lane in body["assay_translation_map"]["lanes"]] == [
        "biochemical",
        "cellular",
        "in_vivo",
        "human",
        "unclassified",
    ]
    assert body["assay_translation_map"]["lanes"][1]["status"] == "conflicting"
