"""
Tests for features/alignment_utils.py (FAMSA-backed multiple sequence
alignment).
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from features.alignment_utils import (  # noqa: E402
    ENGINE_NAME,
    AlignmentError,
    align_sequences,
    parse_fasta_multi,
)

INSULIN_B = "FVNQHLCGSHLVEALYLVCGERGFFYTPKA"
SEMAGLUTIDE = "HAEGTFTSDVSSYLEGQAAKEFIAWLVKGR"
EXENATIDE = "HGEGTFTSDLSKQMEEEAVRLFIEWLKNGGPSSGAPPPS"
GLUCAGON = "HSQGTFTSDYSKYLDSRRAQDFVQWLMNT"

MULTI_FASTA = f""">Insulin
{INSULIN_B}
>Semaglutide
{SEMAGLUTIDE}
>Exenatide
{EXENATIDE}
>Glucagon
{GLUCAGON}
"""


class TestParseFastaMulti:
    def test_parses_multiple_fasta_records(self):
        records = parse_fasta_multi(MULTI_FASTA)
        assert [r[0] for r in records] == ["Insulin", "Semaglutide", "Exenatide", "Glucagon"]
        assert records[0][1] == INSULIN_B

    def test_parses_bare_sequences_without_headers(self):
        text = f"{INSULIN_B}\n{SEMAGLUTIDE}\n"
        records = parse_fasta_multi(text)
        assert len(records) == 2
        assert records[0][1] == INSULIN_B
        assert records[1][1] == SEMAGLUTIDE

    def test_empty_input_raises(self):
        with pytest.raises(AlignmentError):
            parse_fasta_multi("")

    def test_whitespace_only_input_raises(self):
        with pytest.raises(AlignmentError):
            parse_fasta_multi("   \n  \n")

    def test_header_with_no_sequence_raises(self):
        with pytest.raises(AlignmentError):
            parse_fasta_multi(">OnlyAHeader\n")

    def test_invalid_amino_acid_character_raises(self):
        with pytest.raises(AlignmentError, match="outside the amino-acid alphabet"):
            parse_fasta_multi(">Bad\nMKT123\n")

    def test_lowercase_is_normalized_to_uppercase(self):
        records = parse_fasta_multi(">x\nmktq\n")
        assert records[0][1] == "MKTQ"


class TestAlignSequences:
    def test_engine_is_famsa_not_clustalw_or_muscle(self):
        result = align_sequences([("a", "MKTAYIAK"), ("b", "MKTAYIAR")])
        assert result["engine"] == "FAMSA" == ENGINE_NAME
        assert "clustal" not in result["engine"].lower()
        assert "muscle" not in result["engine"].lower()
        assert result["engine_citation"]  # non-empty attribution string

    def test_aligns_related_peptide_family(self):
        records = parse_fasta_multi(MULTI_FASTA)
        result = align_sequences(records)
        assert len(result["records"]) == 4
        # Every aligned sequence must be the same length (that's what "aligned" means).
        lengths = {len(r["aligned_sequence"]) for r in result["records"]}
        assert len(lengths) == 1
        assert result["alignment_length"] == lengths.pop()
        # Alignment only inserts gaps, never changes residue order.
        for original, aligned in zip(records, result["records"]):
            assert aligned["aligned_sequence"].replace("-", "") == original[1]

    def test_consensus_length_matches_alignment_length(self):
        result = align_sequences([("a", "MKTAYIAK"), ("b", "MKTAYIAR"), ("c", "MKTAYQAK")])
        assert len(result["consensus"]) == result["alignment_length"]

    def test_conservation_scores_are_fractions(self):
        result = align_sequences([("a", "MKTAYIAK"), ("b", "MKTAYIAR"), ("c", "MKTAYQAK")])
        assert len(result["conservation"]) == result["alignment_length"]
        assert all(0.0 <= c <= 1.0 for c in result["conservation"])

    def test_identical_sequences_are_fully_conserved(self):
        result = align_sequences([("a", "MKTAYIAK"), ("b", "MKTAYIAK"), ("c", "MKTAYIAK")])
        assert all(c == 1.0 for c in result["conservation"])
        assert result["consensus"] == "MKTAYIAK"

    def test_identity_matrix_diagonal_is_100(self):
        result = align_sequences([("a", "MKTAYIAK"), ("b", "MKTAYIAR"), ("c", "GGGGGGGG")])
        n = len(result["records"])
        for i in range(n):
            assert result["identity_matrix"][i][i] == 100.0

    def test_identity_matrix_is_symmetric(self):
        result = align_sequences([("a", "MKTAYIAK"), ("b", "MKTAYIAR"), ("c", "GGGGGGGG")])
        m = result["identity_matrix"]
        n = len(m)
        for i in range(n):
            for j in range(n):
                assert m[i][j] == pytest.approx(m[j][i])

    def test_dissimilar_sequences_have_low_identity(self):
        result = align_sequences([("a", "MKTAYIAKQRQISFVK"), ("b", "GPWDNRSTLKQEACVF")])
        assert result["identity_matrix"][0][1] < 30.0

    def test_single_sequence_raises(self):
        with pytest.raises(AlignmentError, match="at least 2"):
            align_sequences([("a", "MKTAYIAK")])

    def test_empty_record_list_raises(self):
        with pytest.raises(AlignmentError):
            align_sequences([])

    def test_empty_sequence_in_records_raises(self):
        with pytest.raises(AlignmentError):
            align_sequences([("a", "MKTAYIAK"), ("b", "")])

    def test_output_preserves_input_order(self):
        records = [("z_last", "MKTAYIAK"), ("a_first", "MKTAYIAR")]
        result = align_sequences(records)
        assert [r["id"] for r in result["records"]] == ["z_last", "a_first"]
