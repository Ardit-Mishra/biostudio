"""Deterministic layout data for the Decision Twin Assay Translation Map."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from decision_twin.models import EvidenceRecord


AssayStage = Literal["biochemical", "cellular", "in_vivo", "human", "unclassified"]
LaneStatus = Literal["supporting", "contradicting", "conflicting", "inconclusive", "missing", "unclassified"]
STAGE_ORDER: tuple[AssayStage, ...] = ("biochemical", "cellular", "in_vivo", "human", "unclassified")

_BIOCHEMICAL_SYSTEMS = {"biochemical", "binding", "enzymatic", "biophysical"}
_CELLULAR_SYSTEMS = {"cellular", "cell_line", "cell_line_assay", "organoid", "ex_vivo"}
_IN_VIVO_SYSTEMS = {"in_vivo", "animal", "mouse", "rat", "xenograft"}
_HUMAN_SYSTEMS = {"human", "clinical", "patient", "human_trial"}


class AssayMapLane(BaseModel):
    """One inspection lane in a Decision Twin's evidence translation map."""

    model_config = ConfigDict(extra="forbid")

    stage: AssayStage
    status: LaneStatus
    evidence_ids: list[str]
    gaps: list[str]


class AssayTranslationMap(BaseModel):
    """Stable visual model that makes missing and conflicting evidence visible."""

    model_config = ConfigDict(extra="forbid")

    lanes: list[AssayMapLane]


def build_assay_translation_map(evidence: list[EvidenceRecord]) -> AssayTranslationMap:
    """Classify supplied evidence into fixed assay-translation lanes."""
    grouped: dict[AssayStage, list[EvidenceRecord]] = {stage: [] for stage in STAGE_ORDER}
    for record in evidence:
        grouped[_stage_for(record)].append(record)

    return AssayTranslationMap(
        lanes=[
            _build_lane(stage, grouped[stage])
            for stage in STAGE_ORDER
        ]
    )


def _stage_for(record: EvidenceRecord) -> AssayStage:
    if record.assay_context is None:
        return "unclassified"

    normalized_system = record.assay_context.biological_system.lower().replace("-", "_").replace(" ", "_")
    if normalized_system in _BIOCHEMICAL_SYSTEMS:
        return "biochemical"
    if normalized_system in _CELLULAR_SYSTEMS:
        return "cellular"
    if normalized_system in _IN_VIVO_SYSTEMS:
        return "in_vivo"
    if normalized_system in _HUMAN_SYSTEMS:
        return "human"
    return "unclassified"


def _build_lane(stage: AssayStage, records: list[EvidenceRecord]) -> AssayMapLane:
    evidence_ids = sorted(record.id for record in records)
    if not records:
        if stage == "unclassified":
            return AssayMapLane(stage=stage, status="missing", evidence_ids=[], gaps=[])
        return AssayMapLane(
            stage=stage,
            status="missing",
            evidence_ids=[],
            gaps=[f"No {stage.replace('_', ' ')} evidence was supplied."],
        )
    if stage == "unclassified":
        return AssayMapLane(
            stage=stage,
            status="unclassified",
            evidence_ids=evidence_ids,
            gaps=["At least one record is missing or has unrecognized assay context."],
        )

    directions = {record.outcome_direction for record in records}
    if {"supports", "contradicts"} <= directions:
        return AssayMapLane(
            stage=stage,
            status="conflicting",
            evidence_ids=evidence_ids,
            gaps=["This assay layer contains recorded outcomes in opposition."],
        )
    if directions == {"supports"}:
        return AssayMapLane(stage=stage, status="supporting", evidence_ids=evidence_ids, gaps=[])
    if directions == {"contradicts"}:
        return AssayMapLane(stage=stage, status="contradicting", evidence_ids=evidence_ids, gaps=[])
    return AssayMapLane(
        stage=stage,
        status="inconclusive",
        evidence_ids=evidence_ids,
        gaps=["Recorded outcomes are unknown and cannot yet support a directional conclusion."],
    )
