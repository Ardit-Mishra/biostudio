"""
Phylogenetic Tree Construction

Builds neighbour-joining (NJ) and UPGMA trees from an existing multiple
sequence alignment using `Bio.Phylo.TreeConstruction` — pure Python, already
a dependency (biopython), no external binary. This module only *builds*
trees; it does not align sequences (see `features/alignment_utils.py`).

Author: Ardit Mishra
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Tuple

from Bio.Align import MultipleSeqAlignment
from Bio.Phylo import draw_ascii, write as phylo_write
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

METHODS = ("nj", "upgma")
# DistanceCalculator's protein substitution/identity models. "identity" is
# the simplest (fraction mismatched, model-free); the rest are amino-acid
# substitution matrices. Restricting to this list keeps the UI's dropdown
# exactly matched to what the calculator will actually accept.
DISTANCE_MODELS = ("identity",) + tuple(DistanceCalculator.protein_models)


class PhylogeneticsError(Exception):
    """Raised for any input this module cannot honestly turn into a tree —
    too few sequences, unequal alignment length, or an unknown method/model.
    Never falls back to a partial or fabricated tree."""


def build_tree(
    records: List[Tuple[str, str]],
    method: str = "nj",
    model: str = "identity",
) -> Dict[str, Any]:
    """Build a phylogenetic tree from an existing alignment.

    Args:
        records: (id, aligned_sequence) pairs — all sequences must already
            be the same length (i.e. output of an MSA step).
        method: "nj" (neighbour-joining) or "upgma".
        model: a name from `DISTANCE_MODELS` ("identity" or a Biopython
            protein substitution matrix name, e.g. "blosum62").

    Returns:
        Dict with:
          - method, model: str, echoed back for the UI caption.
          - newick: str, Newick-format tree string.
          - ascii: str, `Bio.Phylo.draw_ascii` rendering.
          - tip_labels: List[str], in the tree's own order.
          - distance_matrix: List[List[float]], the pairwise distances the
            tree was built from (same order as `tip_labels`).

    Raises:
        PhylogeneticsError: fewer than 2 records, sequences of unequal
            length, or an unrecognised method/model name.
    """
    if len(records) < 2:
        raise PhylogeneticsError(
            f"Tree construction needs at least 2 sequences (got {len(records)})."
        )

    method = method.lower()
    if method not in METHODS:
        raise PhylogeneticsError(
            f"Unknown method '{method}'. Choose one of: {', '.join(METHODS)}"
        )

    if model not in DISTANCE_MODELS:
        raise PhylogeneticsError(
            f"Unknown distance model '{model}'. Choose one of: "
            f"{', '.join(DISTANCE_MODELS)}"
        )

    lengths = {len(seq) for _, seq in records}
    if len(lengths) > 1:
        raise PhylogeneticsError(
            "All sequences must be the same length (i.e. already aligned); "
            f"got lengths {sorted(lengths)}."
        )

    seq_records = [SeqRecord(Seq(seq), id=rid) for rid, seq in records]
    alignment = MultipleSeqAlignment(seq_records)

    try:
        calculator = DistanceCalculator(model)
        distance_matrix = calculator.get_distance(alignment)
    except ValueError as exc:
        raise PhylogeneticsError(f"Could not compute distances: {exc}") from None

    constructor = DistanceTreeConstructor()
    try:
        tree = constructor.nj(distance_matrix) if method == "nj" else constructor.upgma(distance_matrix)
    except Exception as exc:  # Bio.Phylo raises plain Exception on degenerate matrices
        raise PhylogeneticsError(f"Tree construction failed ({method}): {exc}") from None

    newick_buf = io.StringIO()
    phylo_write(tree, newick_buf, "newick")

    ascii_buf = io.StringIO()
    draw_ascii(tree, file=ascii_buf, column_width=60)

    tip_labels = list(distance_matrix.names)
    dm_rows = [[float(distance_matrix[i, j]) for j in tip_labels] for i in tip_labels]

    return {
        "method": method,
        "model": model,
        "newick": newick_buf.getvalue().strip(),
        "ascii": ascii_buf.getvalue(),
        "tip_labels": tip_labels,
        "distance_matrix": dm_rows,
    }
