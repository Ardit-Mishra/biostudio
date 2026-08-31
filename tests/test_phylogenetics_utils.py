"""
Tests for features/phylogenetics_utils.py (NJ / UPGMA tree construction
via Bio.Phylo.TreeConstruction).
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from features.phylogenetics_utils import (  # noqa: E402
    DISTANCE_MODELS,
    PhylogeneticsError,
    build_tree,
)

# Pre-aligned (equal length) toy sequences: a/b are near-identical, c is distant.
ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP = [
    ("a", "MKTAYIAK"),
    ("b", "MKTAYIAR"),
    ("c", "GPWDNRST"),
]


class TestBuildTree:
    def test_nj_produces_valid_newick(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="nj")
        assert result["newick"].strip().endswith(";")
        for name, _ in ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP:
            assert name in result["newick"]

    def test_upgma_produces_valid_newick(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="upgma")
        assert result["newick"].strip().endswith(";")

    def test_ascii_rendering_is_nonempty(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="nj")
        assert result["ascii"].strip()
        for name, _ in ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP:
            assert name in result["ascii"]

    def test_tip_labels_match_input_ids(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="nj")
        assert set(result["tip_labels"]) == {"a", "b", "c"}

    def test_distance_matrix_shape_matches_tip_count(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="nj")
        n = len(result["tip_labels"])
        assert len(result["distance_matrix"]) == n
        assert all(len(row) == n for row in result["distance_matrix"])

    def test_distance_matrix_diagonal_is_zero(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="nj")
        for i, row in enumerate(result["distance_matrix"]):
            assert row[i] == 0.0

    def test_close_pair_has_smaller_distance_than_to_outgroup(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="nj", model="identity")
        labels = result["tip_labels"]
        ia, ib, ic = labels.index("a"), labels.index("b"), labels.index("c")
        dm = result["distance_matrix"]
        assert dm[ia][ib] < dm[ia][ic]
        assert dm[ia][ib] < dm[ib][ic]

    def test_blosum62_model_is_accepted(self):
        assert "blosum62" in DISTANCE_MODELS
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="nj", model="blosum62")
        assert result["model"] == "blosum62"

    def test_method_is_echoed_back(self):
        result = build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="upgma")
        assert result["method"] == "upgma"

    def test_fewer_than_two_sequences_raises(self):
        with pytest.raises(PhylogeneticsError, match="at least 2"):
            build_tree([("a", "MKTAYIAK")])

    def test_unequal_length_sequences_raise(self):
        with pytest.raises(PhylogeneticsError, match="same length"):
            build_tree([("a", "MKTAYIAK"), ("b", "MKTAYIAKQR")])

    def test_unknown_method_raises(self):
        with pytest.raises(PhylogeneticsError, match="Unknown method"):
            build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, method="bogus")

    def test_unknown_model_raises(self):
        with pytest.raises(PhylogeneticsError, match="Unknown distance model"):
            build_tree(ALIGNED_CLOSE_PAIR_PLUS_OUTGROUP, model="bogus_matrix")
