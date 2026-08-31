"""
Multiple Sequence Alignment (MSA)

Runs multiple sequence alignment with FAMSA — "Fast and Accurate Multiple
Sequence Alignment of huge datasets" (Deorowicz, Debudaj-Grabysz & Gudys,
2016) — via the `pyfamsa` bindings.

This is deliberately NOT ClustalW or MUSCLE. Both of those are external
binaries that a Streamlit host will not have installed, and shelling out to
a missing executable is a silent-looking crash for the user. FAMSA has a
pip-installable wheel with no system dependency, so it is the engine that
can actually run in this deployment. Every place this module's output
reaches the UI must say "FAMSA", not "ClustalW" or "MUSCLE" — see
`ENGINE_NAME` / `ENGINE_CITATION` below, which callers should render rather
than hard-coding a tool name.

Author: Ardit Mishra
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from pyfamsa import Aligner, Sequence

logger = logging.getLogger(__name__)

# Rendered verbatim in the UI so the tool never gets mislabeled as
# ClustalW/MUSCLE (which are unrelated external binaries this app does not
# ship or call).
ENGINE_NAME = "FAMSA"
ENGINE_CITATION = (
    "Deorowicz, S., Debudaj-Grabysz, A., & Gudys, A. (2016). FAMSA: Fast "
    "and accurate multiple sequence alignment of huge datasets. "
    "Scientific Reports, 6, 33964."
)

AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWYBZXJUO*")
NUCLEOTIDES = set("ACGTUN")


class AlignmentError(Exception):
    """Raised for any input or engine failure that would otherwise produce
    a misleading or empty alignment. Callers must surface this message —
    never fall back to a partial or fabricated alignment."""


def parse_fasta_multi(text: str) -> List[Tuple[str, str]]:
    """Parse one or more FASTA records, or bare newline/blank-line-separated
    sequences, into ``(id, sequence)`` pairs.

    Args:
        text: raw pasted or uploaded content.

    Returns:
        List of (record_id, sequence) in input order.

    Raises:
        AlignmentError: on empty input, a record with no sequence data, or
            a sequence containing characters outside the amino-acid alphabet.
            Never returns a partial list silently missing a bad record.
    """
    if not text or not text.strip():
        raise AlignmentError("No sequence data provided.")

    raw = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    records: List[Tuple[str, str]] = []

    if ">" in raw:
        # FASTA format: split on '>' record markers.
        chunks = [c for c in raw.split(">") if c.strip()]
        if not chunks:
            raise AlignmentError("No FASTA records found.")
        for chunk in chunks:
            lines = chunk.split("\n")
            header = lines[0].strip() or f"seq{len(records) + 1}"
            seq = "".join(line.strip() for line in lines[1:]).upper()
            seq = seq.replace(" ", "")
            if not seq:
                raise AlignmentError(f"Record '{header}' has no sequence data.")
            records.append((header, seq))
    else:
        # No '>' anywhere: treat each non-blank line as one bare sequence.
        for i, line in enumerate(raw.split("\n"), start=1):
            seq = line.strip().replace(" ", "").upper()
            if not seq:
                continue
            records.append((f"seq{i}", seq))
        if not records:
            raise AlignmentError("No sequence data found in input.")

    for header, seq in records:
        invalid = set(seq) - AMINO_ACIDS - set("-")
        if invalid:
            raise AlignmentError(
                f"Record '{header}' contains characters outside the amino-acid "
                f"alphabet: {', '.join(sorted(invalid))}"
            )

    return records


def _percent_identity(a: str, b: str) -> float:
    """Pairwise percent identity over aligned columns where neither side is
    a gap. Two all-gap-overlap sequences (no comparable column) return 0.0
    rather than raising, since that is a real — if uninformative — answer,
    not a computation failure."""
    matches = 0
    compared = 0
    for x, y in zip(a, b):
        if x == "-" or y == "-":
            continue
        compared += 1
        if x == y:
            matches += 1
    if compared == 0:
        return 0.0
    return round(100.0 * matches / compared, 1)


def _consensus(aligned_seqs: List[str]) -> str:
    """Majority-vote consensus, one column at a time. A column that is
    entirely gaps consensus to '-'; ties break on first-seen residue so the
    result is deterministic."""
    if not aligned_seqs:
        return ""
    length = len(aligned_seqs[0])
    out = []
    for col in range(length):
        counts: Dict[str, int] = {}
        for s in aligned_seqs:
            ch = s[col]
            if ch == "-":
                continue
            counts[ch] = counts.get(ch, 0) + 1
        if not counts:
            out.append("-")
        else:
            out.append(max(counts.items(), key=lambda kv: (kv[1], -ord(kv[0])))[0])
    return "".join(out)


def _conservation(aligned_seqs: List[str]) -> List[float]:
    """Per-column conservation: fraction of non-gap residues that match the
    column's most common residue. A fully-gapped column reports 0.0."""
    if not aligned_seqs:
        return []
    length = len(aligned_seqs[0])
    scores = []
    for col in range(length):
        residues = [s[col] for s in aligned_seqs if s[col] != "-"]
        if not residues:
            scores.append(0.0)
            continue
        top = max(residues.count(r) for r in set(residues))
        scores.append(round(top / len(residues), 3))
    return scores


def align_sequences(records: List[Tuple[str, str]], guide_tree: str = "sl") -> Dict[str, Any]:
    """Run a FAMSA multiple sequence alignment.

    Args:
        records: (id, sequence) pairs, e.g. from `parse_fasta_multi`.
        guide_tree: FAMSA guide-tree heuristic ("sl" single-linkage is the
            FAMSA default; "upgma" is also supported by the engine).

    Returns:
        Dict with:
          - engine, engine_citation: str, for UI attribution.
          - records: [{"id", "aligned_sequence"}] in input order.
          - alignment_length: int, number of columns.
          - consensus: str.
          - conservation: List[float], one fraction per column.
          - identity_matrix: List[List[float]], pairwise percent identity.

    Raises:
        AlignmentError: fewer than 2 records, a record with an empty
            sequence, an unsupported character for the engine's scoring
            alphabet, or an internal FAMSA failure. Never returns a
            best-effort partial alignment for a failed run.
    """
    if len(records) < 2:
        raise AlignmentError(
            "Multiple sequence alignment needs at least 2 sequences "
            f"(got {len(records)})."
        )

    seq_objs = []
    for header, seq in records:
        if not seq:
            raise AlignmentError(f"Record '{header}' is empty.")
        try:
            seq_objs.append(Sequence(header.encode("utf-8"), seq.encode("ascii")))
        except (ValueError, UnicodeEncodeError) as exc:
            raise AlignmentError(f"Record '{header}': {exc}") from None

    try:
        aligner = Aligner(guide_tree=guide_tree)
        msa = aligner.align(seq_objs)
    except ValueError as exc:
        raise AlignmentError(f"FAMSA rejected the input: {exc}") from None
    except RuntimeError as exc:
        raise AlignmentError(f"FAMSA alignment failed internally: {exc}") from None

    aligned = [(gs.id.decode("utf-8"), gs.sequence.decode("ascii")) for gs in msa]
    aligned_seqs_only = [seq for _, seq in aligned]

    identity_matrix = [
        [_percent_identity(a, b) for _, b in aligned]
        for _, a in aligned
    ]

    return {
        "engine": ENGINE_NAME,
        "engine_citation": ENGINE_CITATION,
        "records": [{"id": rid, "aligned_sequence": seq} for rid, seq in aligned],
        "alignment_length": len(aligned_seqs_only[0]) if aligned_seqs_only else 0,
        "consensus": _consensus(aligned_seqs_only),
        "conservation": _conservation(aligned_seqs_only),
        "identity_matrix": identity_matrix,
    }
