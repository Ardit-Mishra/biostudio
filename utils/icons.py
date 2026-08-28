"""GENERATED from design-system/tokens.json — do not edit. Run design-system/build.py."""

from __future__ import annotations

_VIEWBOX = "0 0 24 24"
_STROKE = 1.5
_LINECAP = "round"
_LINEJOIN = "round"

_INK = "#E7ECF3"
_INK_MUTED = "#8D9AAA"
_BORDER = "#232C36"

#: What each glyph means. Kept next to the geometry so a call site can be
#: checked against the concept rather than against the name alone.
CONCEPTS = {
    "helix": "double-stranded nucleic acid. GenomeSight's primary mark and the marker for anything operating on DNA/RNA.",
    "peptide": "an amino-acid chain \u2014 beads on a backbone. Marks anything whose subject is a peptide sequence rather than a nucleotide one.",
    "mhcGroove": "PeptideMHC's signature mark. Two alpha-helices (the wavy rails) with a peptide lying in the groove between them \u2014 the actual structure the model predicts. The helices are outlined because they are the receptor; the peptide residues are filled because they are what is being measured.",
    "benzene": "aromatic ring. BioStudio's primary mark and the marker for small-molecule / cheminformatics work.",
    "molecule": "three atoms and their bonds, one of them a double bond. Marks structure input (SMILES), structure rendering, and descriptor calculation.",
    "alignment": "two sequences compared position by position. The vertical pipes are matches; the x is a mismatch \u2014 the icon states what alignment produces rather than just showing two lines.",
    "readingFrame": "an open reading frame: start bracket, directional translation, stop bracket. Marks ORF detection and anything frame-aware.",
    "composition": "base composition / GC content \u2014 four unequal columns over a baseline. The four columns are literal: A, C, G, T.",
    "kmer": "a fixed-width window sliding along a sequence. Marks k-mer frequency analysis; the boxed span is the k.",
    "motif": "a short pattern recurring at several positions along a sequence. Marks motif search; the diamonds are hits, the line is the sequence.",
    "split": "a dataset partitioned into a training majority and a held-out remainder. Marks every split disclosure \u2014 scaffold split, peptide-grouped split, leave-one-allele-out. The filled block is what the model saw; the outlined block is what it was scored on; the rule between them is the partition, and nothing crosses it.",
    "calibration": "a reliability diagram: the stepped line is the ideal y=x reference, the curve is observed frequency. Marks calibration reporting \u2014 the one place a probability is allowed to be called trustworthy.",
    "plate": "a microplate \u2014 many specimens measured in one run. Marks batch prediction and any many-at-once operation.",
    "membrane": "a lipid bilayer with something crossing it. Marks permeability endpoints \u2014 blood-brain barrier, Caco-2, absorption.",
    "metabolism": "biotransformation \u2014 substrate cycling to product. Marks CYP450 endpoints, clearance and half-life.",
    "hazard": "a toxicity or high-risk endpoint. Uses the caveat colour, never the accent \u2014 risk is a property of the compound, not a state of the control.",
    "receptor": "a ligand seated in a binding pocket. Marks target prediction and protein-ligand work. Pocket outlined, ligand filled \u2014 same encoding rule as the groove.",
    "graph": "a knowledge graph \u2014 entities and the relations between them. Marks the drug-target-disease graph and any network view.",
    "flask": "an assay or wet-lab measurement \u2014 the origin of every training label in these apps. Marks datasets, experimental sources and provenance.",
    "mutation": "one residue substituted in a chain. Marks saturation mutagenesis, variant effects and single-position sensitivity. The substituted residue is filled; its neighbours are not.",
    "sequenceFile": "a FASTA/FASTQ record \u2014 a file whose content is a sequence, not prose. Marks upload, export and file-format disclosure.",
    "ruler": "a measurement scale. Marks method/metric disclosure \u2014 the sections that say how a number was produced and on what."
}

BODIES = {
    "helix": "<path d=\"M7 2c0 5 10 5 10 10s-10 5-10 10\"/><path d=\"M17 2c0 5-10 5-10 10s10 5 10 10\"/><path d=\"M9.2 5.4h5.6\"/><path d=\"M8.3 12h7.4\"/><path d=\"M9.2 18.6h5.6\"/>",
    "peptide": "<circle cx=\"4\" cy=\"15\" r=\"2\"/><circle cx=\"9.3\" cy=\"10.5\" r=\"2\"/><circle cx=\"14.7\" cy=\"15\" r=\"2\"/><circle cx=\"20\" cy=\"10.5\" r=\"2\"/><path d=\"M5.5 13.7 7.8 11.8\"/><path d=\"M10.8 11.8 13.2 13.7\"/><path d=\"M16.2 13.7 18.5 11.8\"/>",
    "mhcGroove": "<path d=\"M2 7q2.5-3 5 0t5 0t5 0t5 0\"/><path d=\"M2 17q2.5 3 5 0t5 0t5 0t5 0\"/><path d=\"M6 12h12\"/><circle cx=\"8\" cy=\"12\" r=\"1.3\" fill=\"currentColor\"/><circle cx=\"12\" cy=\"12\" r=\"1.3\" fill=\"currentColor\"/><circle cx=\"16\" cy=\"12\" r=\"1.3\" fill=\"currentColor\"/>",
    "benzene": "<path d=\"M12 3.5 19.4 7.75v8.5L12 20.5 4.6 16.25v-8.5z\"/><circle cx=\"12\" cy=\"12\" r=\"4\"/>",
    "molecule": "<circle cx=\"5.5\" cy=\"8\" r=\"2.3\"/><circle cx=\"18.5\" cy=\"8\" r=\"2.3\"/><circle cx=\"12\" cy=\"17.5\" r=\"2.3\"/><path d=\"M7.8 6.9h8.4\"/><path d=\"M7.8 9.1h8.4\"/><path d=\"M6.8 9.9 10.7 15.6\"/><path d=\"M17.2 9.9 13.3 15.6\"/>",
    "alignment": "<path d=\"M3 6h18\"/><path d=\"M3 18h18\"/><path d=\"M7 9v6\"/><path d=\"M11 9v6\"/><path d=\"M19 9v6\"/><path d=\"M14 10.5 16 13.5\"/><path d=\"M16 10.5 14 13.5\"/>",
    "readingFrame": "<path d=\"M4 6v12\"/><path d=\"M20 6v12\"/><path d=\"M7 12h9\"/><path d=\"M13 9l3 3-3 3\"/>",
    "composition": "<path d=\"M3 20h18\"/><path d=\"M6 20v-6\"/><path d=\"M10.5 20V7\"/><path d=\"M15 20v-9\"/><path d=\"M19.5 20v-4\"/>",
    "kmer": "<path d=\"M2 12h6\"/><path d=\"M16 12h6\"/><path d=\"M8 7h8v10H8z\"/><path d=\"M10.5 10v4\"/><path d=\"M13.5 10v4\"/>",
    "motif": "<path d=\"M3 16h18\"/><path d=\"M6 8l1.8 2L6 12l-1.8-2z\"/><path d=\"M12 8l1.8 2L12 12l-1.8-2z\"/><path d=\"M18 8l1.8 2L18 12l-1.8-2z\"/>",
    "split": "<rect x=\"2.5\" y=\"8.5\" width=\"11.5\" height=\"7\" rx=\"1.5\" fill=\"currentColor\"/><rect x=\"17.5\" y=\"8.5\" width=\"4\" height=\"7\" rx=\"1.5\"/><path d=\"M15.75 4.5v15\"/>",
    "calibration": "<path d=\"M4 3v18h17\"/><path d=\"M6.5 18.5 8.5 16.5\"/><path d=\"M11 14 13 12\"/><path d=\"M15.5 9.5 17.5 7.5\"/><path d=\"M5 19.5c5 .5 5.5-6 14-13\"/>",
    "plate": "<rect x=\"3\" y=\"5\" width=\"18\" height=\"14\" rx=\"2\"/><circle cx=\"7.5\" cy=\"9.5\" r=\"1.5\"/><circle cx=\"12\" cy=\"9.5\" r=\"1.5\"/><circle cx=\"16.5\" cy=\"9.5\" r=\"1.5\"/><circle cx=\"7.5\" cy=\"14.5\" r=\"1.5\"/><circle cx=\"12\" cy=\"14.5\" r=\"1.5\"/><circle cx=\"16.5\" cy=\"14.5\" r=\"1.5\"/>",
    "membrane": "<path d=\"M3 9h18\"/><path d=\"M3 15h18\"/><path d=\"M12 3v18\"/><path d=\"M9 18l3 3 3-3\"/>",
    "metabolism": "<path d=\"M20.5 12a8.5 8.5 0 1 1-2.9-6.4\"/><path d=\"M21 4v4.5h-4.5\"/><circle cx=\"12\" cy=\"12\" r=\"2.2\"/>",
    "hazard": "<path d=\"M12 3.5 21.5 20H2.5z\"/><path d=\"M12 10v4.5\"/><circle cx=\"12\" cy=\"17.3\" r=\"0.9\" fill=\"currentColor\"/>",
    "receptor": "<path d=\"M5 7v6a7 7 0 0 0 14 0V7\"/><circle cx=\"12\" cy=\"10.5\" r=\"2.6\" fill=\"currentColor\"/><path d=\"M12 20v2\"/>",
    "graph": "<circle cx=\"10\" cy=\"12\" r=\"2.8\"/><circle cx=\"4\" cy=\"4.5\" r=\"1.7\"/><circle cx=\"19.5\" cy=\"6\" r=\"1.7\"/><circle cx=\"20\" cy=\"16.5\" r=\"1.7\"/><circle cx=\"7\" cy=\"20\" r=\"1.7\"/><path d=\"M8.3 9.8 5.1 5.8\"/><path d=\"M12.4 10.5 18.1 6.9\"/><path d=\"M12.6 13.1 18.5 15.8\"/><path d=\"M9 14.6 7.6 18.4\"/><path d=\"M19.7 7.7 19.9 14.8\"/>",
    "flask": "<path d=\"M9 3v6.2L3.9 18.6A2 2 0 0 0 5.6 21.5h12.8a2 2 0 0 0 1.7-2.9L15 9.2V3\"/><path d=\"M8 3h8\"/><path d=\"M6.6 15h10.8\"/>",
    "mutation": "<path d=\"M3 15h18\"/><circle cx=\"6\" cy=\"15\" r=\"2\"/><circle cx=\"12\" cy=\"15\" r=\"2\" fill=\"currentColor\"/><circle cx=\"18\" cy=\"15\" r=\"2\"/><path d=\"M12 3v7\"/><path d=\"M9.5 5.5 12 3l2.5 2.5\"/>",
    "sequenceFile": "<path d=\"M14 2.5H7a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7.5z\"/><path d=\"M14 2.5v5h5\"/><path d=\"M8.5 12.5h4\"/><path d=\"M8.5 15.5h7\"/><path d=\"M8.5 18.5h5\"/>",
    "ruler": "<path d=\"M2.5 9h19v6h-19z\"/><path d=\"M6.5 9v3\"/><path d=\"M10 9v4\"/><path d=\"M13.5 9v3\"/><path d=\"M17 9v4\"/>"
}


def icon(name: str, size: int = 20, color: str = "currentColor", stroke: float = _STROKE) -> str:
    """Return one glyph as an inline ``<svg>`` string.

    Args:
        name: key from ``BODIES``.
        size: rendered edge length in px.
        color: any CSS colour; ``currentColor`` inherits from the parent rule.
        stroke: override the 1.5 default only to match an unusually heavy or
            light neighbouring type weight.

    Raises:
        KeyError: on an unknown name — a typo fails loudly instead of
            rendering an invisible empty box.
    """
    try:
        body = BODIES[name]
    except KeyError:
        raise KeyError(
            f"unknown icon {name!r}. Available: {', '.join(sorted(BODIES))}"
        ) from None
    # `color:` on the element matters as much as `stroke:` here. Several glyphs
    # fill a sub-shape with currentColor to mark the thing being measured (the
    # peptide in the groove, the substituted residue, the training block), and
    # currentColor resolves against the inherited text colour, not against the
    # stroke attribute. Without this the outline would tint and the fill would
    # silently keep whatever colour the surrounding Streamlit text happened to be.
    return (
        f'<svg viewBox="{_VIEWBOX}" width="{size}" height="{size}" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="{_LINECAP}" '
        f'stroke-linejoin="{_LINEJOIN}" aria-hidden="true" focusable="false" '
        f'style="flex:none;display:block;color:{color}">{body}</svg>'
    )


def section_header(name: str, title: str, subtitle: str = "", color: str = "") -> str:
    """A section heading with its domain glyph, as one HTML block.

    Defined here rather than per-app so the two Streamlit apps cannot drift
    into two different heading treatments — which is how they drifted before.
    Pass to ``st.markdown(..., unsafe_allow_html=True)``.
    """
    tint = color or _INK_MUTED
    sub = (
        f'<div style="font-size:.85rem;color:{_INK_MUTED};margin:.3rem 0 0 2.1rem;'
        f'max-width:70ch">{subtitle}</div>'
        if subtitle
        else ""
    )
    return (
        f'<div style="margin:2rem 0 .9rem 0">'
        f'<div style="display:flex;align-items:center;gap:.65rem">'
        f'{icon(name, 22, tint)}'
        f'<span style="font-size:1.15rem;font-weight:600;color:{_INK};'
        f'letter-spacing:-.01em">{title}</span>'
        f'</div>{sub}</div>'
    )


def inline(name: str, text: str, size: int = 15, color: str = "") -> str:
    """A glyph and a run of text on one baseline — for chips, legends, list rows."""
    tint = color or _INK_MUTED
    return (
        f'<span style="display:inline-flex;align-items:center;gap:.4rem;'
        f'color:{tint};font-size:.85rem">{icon(name, size, tint)}<span>{text}</span></span>'
    )
