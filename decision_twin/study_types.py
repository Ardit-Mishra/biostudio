"""Study designs, and what each one can and cannot support.

A researcher filtering literature is really choosing a level of evidence, and
the levels are not interchangeable. A case report establishes that something
*can* happen; it says nothing about how often. A randomized trial establishes an
effect in the population that was enrolled, and nothing about the population
that was not. Collapsing those into an undifferentiated "search results" list is
the same mistake this whole product exists to refuse -- it is the literature
equivalent of averaging a cell line against a patient.

So the filter carries its own justification. `supports` and `cannot_support` are
shown next to the choice, not buried in documentation, because the point is to
make the reader think about evidence strength at the moment they pick.

The hierarchy here is the conventional one used in evidence-based medicine, with
preprints called out separately: a preprint is not a design at all, it is a
publication state, and it is the one filter where the caveat is about review
rather than method.

Europe PMC's PUB_TYPE values were verified against the live API rather than
copied from documentation; each `query_fragment` returned a non-zero hit count
for an ordinary query at the time of writing.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

StudyTypeKey = Literal[
    "any",
    "systematic_review",
    "randomized_trial",
    "clinical_trial",
    "observational",
    "case_report",
    "review",
    "preprint",
]


class StudyType(BaseModel):
    """One selectable level of evidence, with the reason to pick it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: StudyTypeKey
    label: str
    #: Appended to a Europe PMC query. Empty means "do not narrow".
    query_fragment: str
    #: What a reader may legitimately conclude from this design.
    supports: str
    #: The conclusion this design cannot carry, however many hits are returned.
    cannot_support: str
    #: Conventional evidence rank, 1 strongest. Preprints are unranked (0).
    rank: int


STUDY_TYPES: tuple[StudyType, ...] = (
    StudyType(
        key="any",
        label="Any design",
        query_fragment="",
        supports="Everything indexed, at every level of evidence.",
        cannot_support="A claim about evidence strength — the results are unsorted by design.",
        rank=0,
    ),
    StudyType(
        key="systematic_review",
        label="Systematic review / meta-analysis",
        query_fragment='(PUB_TYPE:"Systematic Review" OR PUB_TYPE:"Meta-Analysis")',
        supports="A synthesized effect across studies, with its own stated search and inclusion criteria.",
        cannot_support="A new mechanism. A synthesis inherits every limitation of the studies inside it.",
        rank=1,
    ),
    StudyType(
        key="randomized_trial",
        label="Randomized controlled trial",
        query_fragment='PUB_TYPE:"Randomized Controlled Trial"',
        supports="A causal effect in the population that was actually enrolled.",
        cannot_support="Generalisation to patients who would not have met the eligibility criteria.",
        rank=2,
    ),
    StudyType(
        key="clinical_trial",
        label="Clinical trial (any phase)",
        query_fragment='PUB_TYPE:"Clinical Trial"',
        supports="Measured outcomes in humans under a registered protocol.",
        cannot_support="A comparative effect, unless the trial was itself controlled.",
        rank=3,
    ),
    StudyType(
        key="observational",
        label="Cohort / observational",
        query_fragment='(PUB_TYPE:"Observational Study" OR PUB_TYPE:"Comparative Study")',
        supports="An association in a real-world population, at realistic scale.",
        cannot_support="Causation. Confounding is not excluded by design here.",
        rank=4,
    ),
    StudyType(
        key="case_report",
        label="Case report / series",
        query_fragment='PUB_TYPE:"Case Reports"',
        supports="That something can happen at all, and what it looked like when it did.",
        cannot_support="How often it happens, or that it generally does. A case is not a rate.",
        rank=5,
    ),
    StudyType(
        key="review",
        label="Narrative review",
        query_fragment='PUB_TYPE:"Review"',
        supports="Orientation in an unfamiliar area, and pointers to primary work.",
        cannot_support="An evidential claim of its own — the selection behind it is not stated.",
        rank=6,
    ),
    StudyType(
        key="preprint",
        label="Preprint",
        query_fragment="SRC:PPR",
        supports="The most current claim, often months ahead of the journal version.",
        cannot_support="Anything resting on peer review, because none has happened yet.",
        rank=0,
    ),
)

BY_KEY: dict[str, StudyType] = {study_type.key: study_type for study_type in STUDY_TYPES}


def narrow(query: str, study_type: str | None) -> str:
    """Return the Europe PMC query narrowed to one study design.

    An unknown key is a caller error rather than something to silently ignore:
    quietly returning unfiltered results would let a reader believe they were
    looking at randomized trials when they were looking at everything.
    """
    if not study_type or study_type == "any":
        return query
    selected = BY_KEY.get(study_type)
    if selected is None:
        raise ValueError(f"unknown study_type: {study_type}")
    if not selected.query_fragment:
        return query
    return f"({query}) AND {selected.query_fragment}"
