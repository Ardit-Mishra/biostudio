"""
Tests for features/structure_utils.py (PDB fetch/upload parsing, SMILES 3D
embedding, py3Dmol HTML rendering).

The `TestFetchPdbById.test_*_live` tests hit the real RCSB PDB REST API
(no key required, free). They are the only network-dependent tests in this
module; everything else exercises parsing/rendering logic against local or
synthetic data.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from features.structure_utils import (  # noqa: E402
    StructureError,
    fetch_pdb_by_id,
    parse_uploaded_structure,
    render_structure_html,
    smiles_to_molblock,
)

ASPIRIN_SMILES = "CC(=O)Oc1ccccc1C(=O)O"

MINIMAL_PDB = """\
ATOM      1  N   ALA A   1      11.104  13.207   2.052  1.00 20.00           N
ATOM      2  CA  ALA A   1      12.560  13.207   2.052  1.00 20.00           C
ATOM      3  C   ALA A   1      13.090  14.610   2.052  1.00 20.00           C
ATOM      4  O   ALA A   1      12.400  15.610   2.052  1.00 20.00           O
END
"""


class TestFetchPdbByIdValidation:
    def test_malformed_id_raises_without_network_call(self):
        with pytest.raises(StructureError, match="not a valid PDB ID"):
            fetch_pdb_by_id("12")

    def test_empty_id_raises(self):
        with pytest.raises(StructureError):
            fetch_pdb_by_id("")


@pytest.mark.network
class TestFetchPdbByIdLive:
    def test_known_id_returns_pdb_text(self):
        text = fetch_pdb_by_id("1CRN")
        assert "ATOM" in text
        assert len(text) > 1000

    def test_lowercase_id_is_normalized(self):
        text = fetch_pdb_by_id("1crn")
        assert "ATOM" in text

    def test_nonexistent_id_raises_named_error(self):
        with pytest.raises(StructureError, match="No structure found"):
            fetch_pdb_by_id("ZZZZ")


class TestParseUploadedStructure:
    def test_pdb_passthrough(self):
        result = parse_uploaded_structure(MINIMAL_PDB.encode("utf-8"), "toy.pdb")
        assert result == MINIMAL_PDB

    def test_unsupported_extension_raises(self):
        with pytest.raises(StructureError, match="Unsupported file type"):
            parse_uploaded_structure(b"hello", "notes.txt")

    def test_empty_file_raises(self):
        with pytest.raises(StructureError, match="empty"):
            parse_uploaded_structure(b"   ", "empty.pdb")

    def test_undecodable_bytes_raise(self):
        with pytest.raises(StructureError, match="decode"):
            parse_uploaded_structure(b"\xff\xfe\x00\x01", "bad.pdb")

    def test_unparsable_cif_raises(self):
        with pytest.raises(StructureError):
            parse_uploaded_structure(b"this is not mmCIF at all", "broken.cif")


@pytest.mark.network
class TestParseUploadedStructureCifLive:
    """mmCIF has enough interdependent required loop columns (label_alt_id,
    auth_asym_id, pdbx_PDB_model_num, ...) that a hand-written minimal
    fixture is more likely to test Biopython's leniency than this module's
    logic. A real RCSB .cif file is the honest fixture."""

    def test_real_cif_is_converted_to_pdb_atom_records(self):
        import requests

        cif_text = requests.get("https://files.rcsb.org/download/1CRN.cif", timeout=15).text
        result = parse_uploaded_structure(cif_text.encode("utf-8"), "1crn.cif")
        assert "ATOM" in result
        assert "M  END" not in result  # sanity: this is PDB, not a MolBlock


class TestSmilesToMolblock:
    def test_valid_smiles_produces_molblock_with_3d_coords(self):
        molblock = smiles_to_molblock(ASPIRIN_SMILES)
        assert "RDKit" in molblock
        assert "M  END" in molblock
        # 3D coordinates must not all collapse onto the z=0 plane (which
        # would indicate a 2D layout mislabeled as 3D).
        z_coords = []
        for line in molblock.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                try:
                    z_coords.append(float(parts[2]))
                except ValueError:
                    continue
        assert any(abs(z) > 1e-6 for z in z_coords)

    def test_invalid_smiles_raises(self):
        with pytest.raises(StructureError, match="not a valid SMILES"):
            smiles_to_molblock("not_a_smiles!!!")

    def test_empty_smiles_raises(self):
        with pytest.raises(StructureError):
            smiles_to_molblock("")

    def test_reproducible_with_fixed_seed(self):
        mb1 = smiles_to_molblock(ASPIRIN_SMILES, seed=7)
        mb2 = smiles_to_molblock(ASPIRIN_SMILES, seed=7)
        assert mb1 == mb2


class TestRenderStructureHtml:
    def test_pdb_render_includes_3dmol_and_content(self):
        html = render_structure_html(MINIMAL_PDB, "pdb")
        assert "3Dmol" in html
        assert "addModel" in html

    def test_mol_render_defaults_to_stick_style(self):
        molblock = smiles_to_molblock(ASPIRIN_SMILES)
        html = render_structure_html(molblock, "mol")
        assert "stick" in html

    def test_pdb_render_defaults_to_cartoon_style(self):
        html = render_structure_html(MINIMAL_PDB, "pdb")
        assert "cartoon" in html

    def test_unsupported_format_raises(self):
        with pytest.raises(StructureError, match="Unsupported render format"):
            render_structure_html(MINIMAL_PDB, "xyz")

    def test_empty_content_raises(self):
        with pytest.raises(StructureError, match="No structure content"):
            render_structure_html("", "pdb")

    def test_explicit_style_overrides_default(self):
        html = render_structure_html(MINIMAL_PDB, "pdb", style="stick")
        assert "stick" in html
