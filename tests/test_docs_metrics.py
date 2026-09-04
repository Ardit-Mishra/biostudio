"""Public metric tables must not drift from the manifest that produced them.

WHY THIS EXISTS
---------------
METHODOLOGY.md and VALIDATION.md carried a full endpoint table from an earlier
retrain while README.md and admet_models_manifest.json carried a later one. Both
documents named the manifest as the source of truth, and neither matched it:
DILI 0.925 vs 0.920, hERG 0.809 vs 0.824, Caco-2 MAE 0.339 vs 0.272. A reader
comparing the two files could not tell which numbers the project actually ships.

Nothing caught it because no test read the prose. Correcting the values by hand
would have produced the same situation one retrain later, so the fix is this
guard rather than the edit: `models/saved_models/admet_models_manifest.json` is
the only source of truth, and any table claiming to present current shipped
performance is checked against it, cell by cell, on every run.

HOW TO UPDATE A DOCUMENT AFTER A RETRAIN
----------------------------------------
Run `pytest tests/test_docs_metrics.py -k render -s` to print the canonical
table, then paste it between the markers. Do not edit the numbers by hand.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "models" / "saved_models" / "admet_models_manifest.json"

# Documents that publish a "current shipped performance" table. Each must carry
# exactly one marked block; a file with no markers fails loudly rather than
# being silently skipped, because silence is how the drift survived.
GUARDED_DOCS = ["METHODOLOGY.md", "VALIDATION.md"]

START = "<!-- ADMET-METRICS:START -->"
END = "<!-- ADMET-METRICS:END -->"

FEAT_START = "<!-- ADMET-FEATURES:START -->"
FEAT_END = "<!-- ADMET-FEATURES:END -->"

# Higher is better for ranking metrics; MAE is an error, so lower is better.
# Getting this backwards would turn a regression into an apparent improvement,
# which is the specific mistake the old Caco-2 prose had to explain at length.
DIRECTION = {"AUROC": "higher", "AUPRC": "higher", "MAE": "lower"}


def load_manifest() -> dict:
    with MANIFEST.open(encoding="utf-8") as fh:
        return json.load(fh)


def canonical_rows() -> list[dict]:
    """One row per endpoint, derived only from the manifest."""
    rows = []
    for name, m in load_manifest().items():
        metric = m["official_metric"]
        thr = m.get("threshold")
        rows.append(
            {
                "endpoint": name,
                "label": m["app_label"],
                "class": m["admet_class"],
                "metric": metric,
                "direction": DIRECTION[metric],
                "score": f"{m['test_score']:.3f}",
                "threshold": "n/a" if thr is None else f"{thr:.2f}",
                "n_train": str(m["n_train"]),
                "n_test": str(m["n_test"]),
            }
        )
    return rows


def render_table() -> str:
    """The canonical markdown block. The docs must contain this verbatim."""
    head = (
        "| Endpoint | Task | Class | Metric | Better | Score | Threshold | n_train | n_test |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    body = "".join(
        f"| `{r['endpoint']}` | {r['label']} | {r['class']} | {r['metric']} | "
        f"{r['direction']} | **{r['score']}** | {r['threshold']} | "
        f"{r['n_train']} | {r['n_test']} |\n"
        for r in canonical_rows()
    )
    return head + body


def feature_contract() -> dict:
    """The one feature spec every endpoint must share.

    If endpoints ever diverge, no single sentence in the docs can describe the
    featurisation and this raises rather than silently picking the first one.
    """
    manifest = load_manifest()
    specs = {
        name: (m["feature_spec"]["fingerprint"], tuple(sorted(m["feature_spec"]["descriptors"])))
        for name, m in manifest.items()
    }
    distinct = set(specs.values())
    if len(distinct) != 1:
        differing = sorted(specs)
        pytest.fail(
            "endpoints no longer share one feature spec, so the docs cannot state a "
            f"single descriptor/total count: {differing}"
        )
    fingerprint, descriptors = distinct.pop()
    m = re.search(r"nBits=(\d+)", fingerprint)
    if not m:
        pytest.fail(f"cannot read nBits from fingerprint spec {fingerprint!r}")
    n_bits = int(m.group(1))
    return {
        "fingerprint": fingerprint,
        "n_bits": n_bits,
        "n_descriptors": len(descriptors),
        "n_total": n_bits + len(descriptors),
    }


def render_feature_spec() -> str:
    """Canonical featurisation block, derived only from the manifest."""
    c = feature_contract()
    return (
        f"| Component | Count |\n"
        f"|---|---|\n"
        f"| {c['fingerprint']} | {c['n_bits']:,} |\n"
        f"| RDKit descriptors | {c['n_descriptors']} |\n"
        f"| **Total features per molecule** | **{c['n_total']:,}** |\n"
    )


def extract_block(text: str, path: str, start: str = START, end: str = END) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        pytest.fail(
            f"{path}: expected exactly one {start} / {end} pair. "
            "A guarded document without markers is unverified, which is how the "
            "previous drift went unnoticed."
        )
    return text.split(start, 1)[1].split(end, 1)[0].strip("\n")


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_doc_metric_table_matches_manifest(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    block = extract_block(text, doc)
    expected = render_table().strip("\n")
    # Compare line by line so a failure names the offending endpoint rather
    # than dumping two tables and leaving the reader to diff them.
    got_lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    exp_lines = [ln.strip() for ln in expected.splitlines() if ln.strip()]
    assert got_lines == exp_lines, (
        f"{doc}: metric table has drifted from admet_models_manifest.json.\n"
        f"  expected {len(exp_lines)} lines, found {len(got_lines)}.\n"
        + "\n".join(
            f"  line {i + 1}:\n    manifest: {e}\n    document: {g}"
            for i, (e, g) in enumerate(zip(exp_lines, got_lines))
            if e != g
        )
    )


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_superseded_scores_are_not_presented_as_current(doc: str) -> None:
    """Values from the previous retrain must not reappear outside a block that
    explicitly labels them historical."""
    superseded = {
        "0.925": "DILI (now 0.920)",
        "0.809": "hERG (now 0.824)",
        "0.845": "AMES (now 0.866)",
        "0.905": "BBB_Martins (now 0.900)",
        "0.926": "Pgp_Broccatelli (now 0.927)",
        "0.869": "CYP3A4_Veith (now 0.880)",
        "0.339": "Caco2_Wang (now 0.272)",
    }
    text = (ROOT / doc).read_text(encoding="utf-8")
    offenders = []
    for line_no, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        # A line may cite an old number only while marking it as superseded.
        if any(w in low for w in ("historical", "superseded", "previous", "earlier", "gen 2")):
            continue
        for value, what in superseded.items():
            if re.search(rf"(?<![\d.]){re.escape(value)}(?![\d])", line):
                offenders.append(f"  {doc}:{line_no} cites {value} ({what}): {line.strip()[:90]}")
    assert not offenders, (
        "superseded metric values presented as current:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_doc_feature_spec_matches_manifest(doc: str) -> None:
    """Featurisation claims drift the same way metric tables do, and more quietly.

    Both documents described "10 RDKit descriptors ... = 2,058 features" while
    every manifest entry recorded 217 descriptors and 2,265 total. That is not a
    rounding difference -- it misstates the model's input width by an order of
    magnitude in the descriptor block, and nothing checked it.
    """
    text = (ROOT / doc).read_text(encoding="utf-8")
    block = extract_block(text, doc, FEAT_START, FEAT_END)
    expected = render_feature_spec().strip("\n")
    got_lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    exp_lines = [ln.strip() for ln in expected.splitlines() if ln.strip()]
    assert got_lines == exp_lines, (
        f"{doc}: feature spec has drifted from admet_models_manifest.json.\n"
        + "\n".join(
            f"  line {i + 1}:\n    manifest: {e}\n    document: {g}"
            for i, (e, g) in enumerate(zip(exp_lines, got_lines))
            if e != g
        )
    )


# Prose that explicitly scopes itself to something other than the current served
# models. A claim inside such a span is allowed to differ from the manifest.
EXEMPT = ("historical", "superseded", "previous", "earlier", "legacy", "deprecated", "gen 2")

# Documents that describe the served models. Swept whole, not line by line.
SWEPT_DOCS = GUARDED_DOCS + ["README.md", "TUTORIAL.md", "SETUP.md"]


def _flatten(text: str) -> str:
    """Collapse whitespace so a claim split across lines is still one string.

    The first version of this sweep matched the literal `10 RDKit descriptors`
    and therefore missed `10 RDKit physicochemical descriptors` wrapped across
    two lines in METHODOLOGY.md -- a live claim about the served models. Matching
    a fixed phrase only ever catches the wording you already thought of.
    """
    return re.sub(r"\s+", " ", text)


@pytest.mark.parametrize("doc", SWEPT_DOCS)
def test_feature_claims_agree_with_manifest(doc: str) -> None:
    """Any descriptor or total-feature count stated as current must match the manifest.

    Value-based, not phrase-based: it reads whatever number precedes "RDKit
    ... descriptors" or "... features" and compares it to the contract, so new
    phrasings are caught without being enumerated in advance.
    """
    c = feature_contract()
    flat = _flatten((ROOT / doc).read_text(encoding="utf-8"))
    offenders = []

    def exempt(at: int) -> bool:
        window = flat[max(0, at - 160) : at + 160].lower()
        return any(w in window for w in EXEMPT)

    # "<n> RDKit [any words] descriptors"
    for m in re.finditer(r"([\d,]+)\s+RDKit[\w\s-]{0,40}?descriptors", flat):
        if exempt(m.start()):
            continue
        n = int(m.group(1).replace(",", ""))
        if n != c["n_descriptors"]:
            offenders.append(
                f"  {doc}: claims {n} RDKit descriptors, manifest says "
                f"{c['n_descriptors']} -- ...{flat[max(0, m.start() - 60):m.end() + 30]}..."
            )

    # "<n> features", "<n> total features", or "<n> total" -- the last form is
    # how TUTORIAL.md writes it ("(2,265 total)"), and an earlier version of this
    # pattern required the word "features" to follow, so a drift injected there
    # passed the guard. Any count in a featurisation context must match.
    for m in re.finditer(r"([\d,]{3,})\s+(?:total\s+features|features|total)\b", flat):
        if exempt(m.start()):
            continue
        window = flat[max(0, m.start() - 200) : m.end() + 60].lower()
        if not any(k in window for k in ("ecfp", "morgan", "fingerprint", "descriptor")):
            continue  # some other use of the word "features"
        n = int(m.group(1).replace(",", ""))
        if n != c["n_total"]:
            offenders.append(
                f"  {doc}: claims {n} total features, manifest says "
                f"{c['n_total']} -- ...{flat[max(0, m.start() - 60):m.end() + 30]}..."
            )

    assert not offenders, (
        "feature-representation claims disagree with admet_models_manifest.json.\n"
        "(Scope a genuinely historical or legacy claim with one of "
        f"{EXEMPT} to exempt it.)\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("doc", GUARDED_DOCS)
def test_no_unnegated_production_ready_claim(doc: str) -> None:
    """"Production-ready" may appear only where it is denied.

    Three separate places claimed production-readiness for different components,
    and each was corrected separately -- the summary table, the Category 0 block,
    then two trailing summary bullets found only by grep. A claim that survives
    in three phrasings across two files is not a wording slip; it needs a guard.

    Permitted forms are a denial ("not production-ready", "Production Ready: No")
    and the interrogative column header ("Production Ready?"). Anything else is
    an application-readiness claim this project does not support: no prospective,
    external or assay validation exists for any component.
    """
    flat = _flatten((ROOT / doc).read_text(encoding="utf-8"))
    offenders = []
    for m in re.finditer(r"production[-\s]?ready", flat, flags=re.IGNORECASE):
        before = flat[max(0, m.start() - 60) : m.start()].lower()
        after = flat[m.end() : m.end() + 60].lower()
        negated = (
            re.search(r"\bnot\s+(?:\w+\s+){0,2}$", before)          # "... not production-ready"
            or re.match(r"\?", after.strip())                        # "Production Ready?" header
            or re.match(r"[^a-z0-9]{0,12}(no\b|\*\*no)", after.strip())  # ": No" / ": **No.**"
        )
        if not negated:
            offenders.append(
                f"  {doc}: unnegated production-readiness claim -- "
                f"...{flat[max(0, m.start() - 70):m.end() + 70]}..."
            )
    assert not offenders, (
        "production-readiness is claimed without denial:\n" + "\n".join(offenders)
    )


def test_manifest_covers_every_served_model() -> None:
    """The table is only trustworthy if the manifest describes everything served."""
    manifest = load_manifest()
    shipped = {
        p.name.replace("_meta.json", "")
        for p in (ROOT / "models" / "saved_models").glob("*_meta.json")
    }
    assert shipped == set(manifest), (
        f"manifest endpoints {sorted(manifest)} do not match shipped "
        f"*_meta.json artifacts {sorted(shipped)}"
    )


def test_manifest_scores_agree_with_per_endpoint_meta() -> None:
    """The manifest must not disagree with the per-endpoint artifacts it summarises."""
    for name, m in load_manifest().items():
        meta_path = ROOT / "models" / "saved_models" / f"{name}_meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert abs(meta["test_score"] - m["test_score"]) < 1e-9, (
            f"{name}: manifest test_score {m['test_score']} != "
            f"{meta_path.name} test_score {meta['test_score']}"
        )


def test_render(capsys) -> None:
    """Not an assertion -- run with -s to print the block to paste into a doc."""
    with capsys.disabled():
        print("\n" + START)
        print(render_table(), end="")
        print(END)


def test_readme_inline_scores_match_manifest() -> None:
    """README quotes the headline scores inline rather than in a marked table.

    That is a reasonable choice for a shop window, but it is still a second copy
    of numbers whose source of truth is the manifest -- and the README's own
    sentence claims the scores are "kept current there rather than duplicated
    here" while duplicating them. Guard the copy instead of trusting the claim.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manifest = load_manifest()
    # The README uses short human names, not manifest keys.
    aliases = {
        "DILI": "DILI", "hERG": "hERG", "AMES": "Ames",
        "BBB_Martins": "BBB", "Pgp_Broccatelli": "P-gp",
        "CYP3A4_Veith": "CYP3A4", "Caco2_Wang": "Caco-2",
    }
    missing = []
    for key, shown in aliases.items():
        score = f"{manifest[key]['test_score']:.3f}"
        if not re.search(rf"{re.escape(shown)}\s+{re.escape(score)}", readme):
            missing.append(f"  README does not state {shown} {score} (manifest test_score)")
    assert not missing, (
        "README headline scores disagree with admet_models_manifest.json:\n"
        + "\n".join(missing)
    )
