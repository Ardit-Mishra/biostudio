"""
3D Molecular Structure Utilities

Fetches/parses structures (PDB ID lookup against RCSB, or an uploaded
.pdb/.cif file) and small molecules (RDKit-embedded 3D coordinates from a
SMILES string), and renders them with py3Dmol — a pip-installable package
that renders via embedded JavaScript (3Dmol.js, loaded from a public CDN at
view time), so it works inside `streamlit.components.v1.html` with no
system binary required.

Every failure path here (bad PDB ID, network error, unparsable upload,
invalid SMILES, failed 3D embedding) raises `StructureError` with a message
naming what happened — callers must render that message, never a blank or
placeholder viewer that could be mistaken for an empty real structure.

Author: Ardit Mishra
"""

from __future__ import annotations

import io
import logging
import re
from typing import Optional

import py3Dmol
import requests
from rdkit import Chem
from rdkit.Chem import AllChem

logger = logging.getLogger(__name__)

RCSB_PDB_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"
RCSB_CIF_URL = "https://files.rcsb.org/download/{pdb_id}.cif"
_PDB_ID_RE = re.compile(r"^[A-Za-z0-9]{4}$")

# 3Dmol.js style keys this module exposes to the UI, with their spec.
# "cartoon" only draws a backbone trace (no side chains) — appropriate for
# a protein/nucleic-acid fold, meaningless for a small molecule, which is
# why smiles_to_molblock output defaults to "stick" instead.
STYLE_SPECS = {
    "cartoon": {"cartoon": {"color": "spectrum"}},
    "stick": {"stick": {}},
    "sphere": {"sphere": {}},
    "line": {"line": {}},
}


class StructureError(Exception):
    """Raised for any structure-fetch, parse, or 3D-embedding failure. The
    message is meant to be shown directly to the user in place of the
    viewer — never swallowed into a blank pane."""


def fetch_pdb_by_id(pdb_id: str, timeout: float = 15.0) -> str:
    """Fetch a structure from RCSB PDB by its 4-character ID.

    Args:
        pdb_id: e.g. "1CRN". Case-insensitive.
        timeout: request timeout in seconds.

    Returns:
        PDB-format file content as a string.

    Raises:
        StructureError: malformed ID, the ID doesn't exist at RCSB (404),
            or any network failure (timeout, DNS, connection refused).
            Never returns partial/truncated content as if it were complete.
    """
    pdb_id = (pdb_id or "").strip().upper()
    if not _PDB_ID_RE.match(pdb_id):
        raise StructureError(
            f"'{pdb_id}' is not a valid PDB ID (expected 4 alphanumeric characters)."
        )

    url = RCSB_PDB_URL.format(pdb_id=pdb_id)
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.exceptions.Timeout:
        raise StructureError(
            f"Timed out fetching {pdb_id} from RCSB PDB after {timeout:.0f}s."
        ) from None
    except requests.exceptions.RequestException as exc:
        raise StructureError(
            f"Network error fetching {pdb_id} from RCSB PDB: {exc}"
        ) from None

    if resp.status_code == 404:
        raise StructureError(
            f"No structure found for PDB ID '{pdb_id}' at RCSB — check the ID."
        )
    if resp.status_code != 200:
        raise StructureError(
            f"RCSB PDB returned HTTP {resp.status_code} for '{pdb_id}'."
        )
    if not resp.text.strip():
        raise StructureError(f"RCSB PDB returned an empty file for '{pdb_id}'.")

    return resp.text


def parse_uploaded_structure(file_bytes: bytes, filename: str) -> str:
    """Convert an uploaded structure file to PDB-format text.

    .pdb files pass through as-is (decoded). .cif/.mmcif files are parsed
    with Biopython's MMCIFParser and re-serialised to PDB — py3Dmol's PDB
    parser is the most reliably supported path in 3Dmol.js, so normalising
    here avoids a viewer that silently renders nothing for a format it
    only partially understands.

    Args:
        file_bytes: raw uploaded file content.
        filename: original filename, used only to pick the parser by
            extension.

    Returns:
        PDB-format text.

    Raises:
        StructureError: unrecognised extension, undecodable content, or a
            structure the parser cannot make sense of.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in {"pdb", "ent", "cif", "mmcif"}:
        raise StructureError(
            f"Unsupported file type '.{ext}'. Upload a .pdb or .cif structure file."
        )

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StructureError(f"Could not decode '{filename}' as text: {exc}") from None

    if not text.strip():
        raise StructureError(f"'{filename}' is empty.")

    if ext in {"pdb", "ent"}:
        return text

    # .cif / .mmcif: reparse into PDB text via Biopython.
    try:
        from Bio.PDB import MMCIFParser, PDBIO
    except ImportError as exc:  # pragma: no cover - biopython is a hard dependency
        raise StructureError(f"CIF support unavailable: {exc}") from None

    try:
        parser = MMCIFParser(QUIET=True)
        structure = parser.get_structure(filename, io.StringIO(text))
        pdb_io = PDBIO()
        pdb_io.set_structure(structure)
        out = io.StringIO()
        pdb_io.save(out)
    except Exception as exc:
        raise StructureError(f"Could not parse '{filename}' as mmCIF: {exc}") from None

    pdb_text = out.getvalue()
    if not pdb_text.strip():
        raise StructureError(
            f"'{filename}' parsed as mmCIF but produced no atom records."
        )
    return pdb_text


def smiles_to_molblock(smiles: str, seed: int = 42) -> str:
    """Generate 3D coordinates for a small molecule from SMILES.

    Uses RDKit's ETKDG distance-geometry embedding followed by an MMFF94
    force-field optimisation.

    Args:
        smiles: a SMILES string.
        seed: RNG seed for the embedding, for reproducible layouts.

    Returns:
        A MolBlock (SDF single-molecule) string with 3D coordinates.

    Raises:
        StructureError: invalid SMILES, or RDKit's embedding fails to place
            the molecule (can happen for degenerate/disconnected inputs) —
            never returns 2D coordinates mislabeled as a 3D structure.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None or mol.GetNumAtoms() == 0:
        raise StructureError(f"'{smiles}' is not a valid SMILES string.")

    mol = Chem.AddHs(mol)
    embed_result = AllChem.EmbedMolecule(mol, randomSeed=seed, useRandomCoords=True)
    if embed_result != 0:
        raise StructureError(
            f"RDKit could not generate 3D coordinates for '{smiles}' "
            "(embedding failed — the structure may be too unusual for "
            "distance-geometry embedding)."
        )

    try:
        AllChem.MMFFOptimizeMolecule(mol)
    except Exception as exc:
        # Optimization is a refinement step; a raw embedded geometry is
        # still a genuine 3D structure, so this is logged, not fatal.
        logger.warning("MMFF optimization failed for %r: %s", smiles, exc)

    return Chem.MolToMolBlock(mol)


def render_structure_html(
    content: str,
    fmt: str,
    style: Optional[str] = None,
    width: int = 640,
    height: int = 480,
    background: str = "#171E27",
) -> str:
    """Build a self-contained HTML/JS fragment that renders a structure
    with py3Dmol, suitable for `st.components.v1.html`.

    Args:
        content: file content — PDB text (fmt="pdb") or a MolBlock (fmt="mol").
        fmt: "pdb" or "mol" (py3Dmol/3Dmol.js format identifiers).
        style: one of `STYLE_SPECS` ("cartoon", "stick", "sphere", "line");
            defaults to "cartoon" for pdb (colored by chain/spectrum) and
            "stick" for mol (small molecules have no secondary structure
            to cartoon).
        width, height: viewer pane size in px.
        background: hex background colour to match the app's dark theme.

    Returns:
        HTML string.

    Raises:
        StructureError: unknown `fmt`, unknown `style`, or empty `content`.
    """
    if fmt not in {"pdb", "mol"}:
        raise StructureError(f"Unsupported render format '{fmt}'.")
    if not content or not content.strip():
        raise StructureError("No structure content to render.")

    if style is None:
        style = "cartoon" if fmt == "pdb" else "stick"
    if style not in STYLE_SPECS:
        raise StructureError(
            f"Unknown style '{style}'. Choose one of: {', '.join(STYLE_SPECS)}"
        )

    style_spec = STYLE_SPECS[style]

    view = py3Dmol.view(width=width, height=height)
    view.addModel(content, fmt)
    view.setStyle(style_spec)
    if fmt == "pdb":
        # Ligands/waters embedded in a PDB file are not covered by a cartoon
        # style (which only draws backbone trace), so add sticks for any
        # HETATM records to avoid silently hiding a bound ligand.
        view.addStyle({"hetflag": True}, {"stick": {}})
    view.setBackgroundColor(background)
    view.zoomTo()
    # write_html(f=None) is py3Dmol's public entry point for getting the
    # viewer as a standalone HTML/JS string (used internally by both
    # _repr_html_ and file export) — preferred over calling the
    # underscore-prefixed _make_html() directly.
    return view.write_html()
