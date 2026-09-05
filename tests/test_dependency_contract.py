"""One dependency declaration, enforced.

BioStudio previously declared its dependencies in three places that disagreed:

  * ``pyproject.toml`` -- ``requires-python`` and the 23-entry dependency list
    were nested under ``[project.urls]``. Under PEP 621 that table holds URLs
    only, so packaging tools saw a project with *no* dependencies and *no*
    Python constraint. The committed ``uv.lock`` was 137 bytes and locked zero
    packages, which is what that looks like from the outside.
  * ``requirements.txt`` -- a hand-maintained list claiming in its own header
    to mirror ``[project.dependencies]``, which did not exist.
  * ``Dockerfile`` -- a hardcoded ``pip install`` argument list that had since
    drifted: it installed ``rdkit-pypi`` (a community wheel abandoned at
    2022.9.5) rather than ``rdkit``, and omitted ``py3Dmol`` and ``pyfamsa``,
    both imported by shipped code. The container could not run parts of the
    app that CI tested.

The contract now is: ``pyproject.toml [project.dependencies]`` is canonical,
``requirements.txt`` is compiled from it, and both the container and CI
install that lock -- so they run the same runtime dependency graph. CI
additionally installs ``requirements-dev.txt`` (pytest and its test client);
the image does not, and ``.dockerignore`` keeps ``tests/`` out of it. The two
environments are therefore identical in runtime dependencies and differ only
by that test-only tier, which is the claim these tests hold to.

They compare *values* against that source of truth rather than matching
phrasings someone thought of in advance, so a new divergence fails here
instead of shipping.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
LOCK = ROOT / "requirements.txt"
DOCKERFILE = ROOT / "Dockerfile"
CI = ROOT / ".github" / "workflows" / "ci.yml"
MANIFEST = ROOT / "models" / "saved_models" / "admet_models_manifest.json"

# The abandoned community RDKit wheel. Its last release was 2022.9.5; the
# official `rdkit` package is years ahead. Named explicitly because the two
# ship the same `rdkit` import name, so having both installed is not merely
# redundant -- it is ambiguous which one the app gets.
OBSOLETE = "rdkit-pypi"


def project() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]


def declared_requirements() -> dict[str, Requirement]:
    """Canonical dependency name -> parsed requirement, from pyproject."""
    return {canonicalize_name(r.name): r
            for r in (Requirement(d) for d in project()["dependencies"])}


def lock_entries() -> list[tuple[str, Version, set[str]]]:
    """Every pin in the lock as (canonical name, version, `# via` sources)."""
    entries: list[tuple[str, Version, set[str]]] = []
    current: tuple[str, Version] | None = None
    vias: set[str] = set()
    for raw in LOCK.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if raw.startswith("#"):  # file header, not an annotation
            continue
        if stripped.startswith("#"):  # indented `# via` annotation
            note = stripped.lstrip("#").strip()
            if note.startswith("via"):
                note = note[3:].strip()
            if note and current is not None:
                vias.add(note)
            continue
        if current is not None:
            entries.append((*current, vias))
        spec = stripped.split(";", 1)[0].strip()
        name, _, version = spec.partition("==")
        current, vias = (canonicalize_name(name), Version(version)), set()
    if current is not None:
        entries.append((*current, vias))
    return entries


def python_requirement() -> SpecifierSet:
    return SpecifierSet(project()["requires-python"])


# --------------------------------------------------------------------------
# The declaration itself
# --------------------------------------------------------------------------

def test_project_metadata_declares_dependencies_and_python():
    """The exact defect that existed: PEP 621 keys nested under the wrong table.

    Reading them through a TOML parser rather than by regex is the point --
    that is how pip, uv and build back-ends see the file, and it is why the
    committed lock was empty while the file looked plausible to a reader.
    """
    proj = project()
    assert proj.get("dependencies"), (
        "[project.dependencies] is missing or empty. Packaging tools will "
        "resolve this project to zero dependencies."
    )
    assert proj.get("requires-python"), "[project] declares no requires-python."


def test_project_urls_contains_urls_only():
    urls = project().get("urls", {})
    misplaced = {k: v for k, v in urls.items()
                 if not (isinstance(v, str) and v.startswith("http"))}
    assert not misplaced, (
        f"[project.urls] must hold URLs only; found {sorted(misplaced)}. "
        "Non-URL keys here are silently ignored as project metadata."
    )


def _uncommented(path: Path) -> str:
    """File contents with comments removed, so prose about a package is not
    mistaken for a declaration of it."""
    kept = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        kept.append(line.split("#", 1)[0])
    return "\n".join(kept)


def test_obsolete_rdkit_wheel_is_not_declared_anywhere():
    offenders = [p.relative_to(ROOT).as_posix()
                 for p in (PYPROJECT, LOCK, DOCKERFILE)
                 if OBSOLETE in _uncommented(p).lower()]
    assert not offenders, (
        f"{OBSOLETE} is declared in {offenders}. It is abandoned at 2022.9.5 "
        "and collides with the official rdkit package on the same import name."
    )


# --------------------------------------------------------------------------
# The lock agrees with the declaration
# --------------------------------------------------------------------------

def test_lock_is_fully_pinned():
    unpinned = [line.strip() for line in LOCK.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
                and "==" not in line]
    assert not unpinned, f"lock contains unpinned requirements: {unpinned}"


def test_lock_direct_dependencies_match_pyproject_exactly():
    """Set equality in both directions, so adding *or* removing drifts loudly.

    `uv pip compile` annotates each pin with what pulled it in; a dependency
    declared in pyproject appears as `via biostudio (pyproject.toml)`. If the
    lock were regenerated with `--no-annotate` this comparison would lose its
    meaning rather than quietly weaken, so the annotations are asserted first.
    """
    entries = lock_entries()
    assert entries, "no pins parsed out of the lock"
    annotated = [e for e in entries if e[2]]
    assert annotated, (
        "the lock carries no `# via` annotations. Regenerate it with the "
        "command in its header; this guard depends on them."
    )
    direct = {name for name, _, vias in entries
              if any(v.startswith("biostudio (pyproject.toml)") for v in vias)}
    assert direct == set(declared_requirements()), (
        "lock and pyproject disagree on the direct dependency set.\n"
        f"  only in pyproject: {sorted(set(declared_requirements()) - direct)}\n"
        f"  only in lock     : {sorted(direct - set(declared_requirements()))}\n"
        "Regenerate the lock (see its header) after editing pyproject."
    )


def test_lock_versions_satisfy_the_declared_constraints():
    """A pin below a declared floor means the lock predates the declaration."""
    declared = declared_requirements()
    violations = []
    for name, version, _ in lock_entries():
        req = declared.get(name)
        if req is not None and not req.specifier.contains(version, prereleases=True):
            violations.append(f"{name}=={version} violates {req.specifier}")
    assert not violations, "\n".join(violations)


# --------------------------------------------------------------------------
# Everything installs that lock, on the interpreter the contract names
# --------------------------------------------------------------------------

def test_dockerfile_installs_the_lock_and_hardcodes_nothing():
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert re.search(r"pip install[^\n]*-r\s+requirements\.txt", text), (
        "the Dockerfile does not install requirements.txt."
    )
    # Derived from pyproject, not from a fixed list of package names: any
    # dependency spelled out in a build step is a second declaration.
    install_steps = "\n".join(
        line for line in text.splitlines()
        if "pip install" in line or line.rstrip().endswith("\\")
    )
    inline = sorted(name for name in declared_requirements()
                    if re.search(rf"\b{re.escape(name)}\b[><=~!]", install_steps, re.I))
    assert not inline, (
        f"the Dockerfile names {inline} directly in a build step. Install the "
        "lock instead so there is one dependency source."
    )


def test_dockerfile_base_image_satisfies_requires_python():
    text = DOCKERFILE.read_text(encoding="utf-8")
    match = re.search(r"^FROM\s+python:(\d+\.\d+)", text, re.M)
    assert match, "no `FROM python:<version>` base image found"
    version = Version(match.group(1))
    assert python_requirement().contains(version), (
        f"the image runs Python {version} but the project requires "
        f"{python_requirement()}. The container would be the one environment "
        "on a different interpreter."
    )


def dockerfile_run_steps() -> list[str]:
    """Logical RUN steps, backslash continuations joined into one line."""
    steps, buf = [], None
    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        if buf is not None:
            buf += " " + line.strip().rstrip("\\").strip()
        elif line.startswith("RUN "):
            buf = line[4:].strip().rstrip("\\").strip()
        else:
            continue
        if not line.rstrip().endswith("\\"):
            steps.append(buf)
            buf = None
    if buf is not None:
        steps.append(buf)
    return steps


def test_dockerfile_installs_the_system_library_rdkit_drawing_needs():
    """`libexpat1` is a runtime dependency of RDKit that pip cannot express.

    `rdkit.Chem.Draw.rdMolDraw2D` links `libexpat.so.1`. Without the Debian
    package, `from rdkit.Chem import Draw` raises ImportError, `app.py` dies at
    its top-level imports, and the container serves a traceback instead of the
    UI -- a failure no Python-level check catches, because the wheel installs
    perfectly well and only fails when loaded.

    This is guarded rather than merely fixed because the apt list was written
    for rdkit-pypi 2022.9.5 and silently stopped matching what current RDKit
    needs. Dropping the package again would break the app exactly as before.
    """
    apt_steps = [s for s in dockerfile_run_steps() if "apt-get install" in s]
    assert apt_steps, "the Dockerfile installs no system packages"
    installed = " ".join(apt_steps)
    assert re.search(r"(?<![\w.-])libexpat1(?![\w.-])", installed), (
        "libexpat1 is missing from the apt-get install list. RDKit's drawing "
        "module links libexpat.so.1; without it the Streamlit app cannot "
        "import and the container renders an ImportError traceback."
    )


def test_dockerfile_does_not_upgrade_build_tooling_unpinned():
    """An unpinned `pip install --upgrade pip` re-opens what the digest closed.

    The base image is pinned by digest precisely so the build does not depend
    on when it runs. Upgrading pip (or setuptools, or wheel) to whatever is
    latest that day puts the time dependency straight back, one layer down,
    where it is easier to miss. Upgrading is fine -- upgrading to an
    unspecified version is not, so this rejects the missing pin rather than
    the upgrade.
    """
    offenders = []
    for step in dockerfile_run_steps():
        match = re.search(r"\bpip\s+install\b(?P<args>.*)", step)
        if not match:
            continue
        args = match.group("args")
        if not re.search(r"(?:^|\s)(?:--upgrade|-U)(?:\s|$)", args):
            continue
        # Only the operands matter; flags and their values are not packages.
        named = [tok.strip("\"'") for tok in args.split() if not tok.startswith("-")]
        unpinned = [tok for tok in named
                    if canonicalize_name(re.split(r"[<>=!~]", tok)[0])
                    in {"pip", "setuptools", "wheel"} and "==" not in tok]
        if unpinned:
            offenders.append(f"{unpinned} in: RUN {step}")
    assert not offenders, (
        "unpinned upgrade of build tooling makes the build time-dependent "
        "again despite the digest-pinned base image:\n  " + "\n  ".join(offenders)
    )


def test_dockerfile_base_image_is_pinned_by_digest():
    """A tag is not a pin.

    `python:3.12-slim` is rebuilt as its base and security patches change, so
    two builds a month apart from an identical Dockerfile can start from
    different bytes. The digest closes that one hole: it prevents base-image
    tag drift.

    It does not make the build byte-identical, and nothing here claims it
    does. Two gaps remain deliberately open: the `apt-get install` layer
    resolves whatever Debian ships that day, and the Python lock carries exact
    versions but no hashes (`--generate-hashes` is not used). What the project
    guarantees is pinned *versions* -- of the interpreter, the base image, and
    every Python package -- not reproducible *bytes*.
    """
    text = DOCKERFILE.read_text(encoding="utf-8")
    from_line = next((l for l in text.splitlines() if l.startswith("FROM ")), "")
    assert re.search(r"@sha256:[0-9a-f]{64}\b", from_line), (
        f"base image is not pinned by digest: {from_line!r}. Re-resolve with "
        "`docker buildx imagetools inspect python:3.12-slim` and pin the "
        "multi-arch index digest."
    )


def test_ci_installs_the_runtime_lock():
    """CI must test against the same lock the image ships.

    Before this contract existed CI installed a hand-maintained requirements
    list while the image installed a hardcoded and by then different one, so
    a green CI run said nothing about what the container would contain.
    """
    text = CI.read_text(encoding="utf-8")
    assert re.search(r"--with-requirements\s+requirements\.txt\b", text), (
        "CI does not install requirements.txt. It would then be testing a "
        "different dependency graph from the one the image ships."
    )
    # The comments in the Dockerfile and in requirements.txt both state that
    # CI additionally installs the test-only tier. Guarded so that claim
    # cannot quietly stop being true.
    assert re.search(r"--with-requirements\s+requirements-dev\.txt\b", text), (
        "CI does not install requirements-dev.txt, but the Dockerfile and "
        "requirements.txt both say it does."
    )


def test_ci_python_satisfies_requires_python():
    match = re.search(r"--python\s+(\d+\.\d+)", CI.read_text(encoding="utf-8"))
    assert match, "CI does not pin a Python version for the test run"
    version = Version(match.group(1))
    assert python_requirement().contains(version), (
        f"CI runs Python {version}, outside the declared {python_requirement()}."
    )


@pytest.mark.skipif(not MANIFEST.exists(), reason="model manifest not present")
def test_served_models_were_trained_on_a_supported_python():
    """Ties the contract to the artifacts, not just to the other config files.

    The manifest records the environment that produced each served model. If
    requires-python ever excludes it, the project is claiming to run the
    models somewhere they were never built.
    """
    import json
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    spec = python_requirement()
    mismatched = {
        endpoint: meta["library_versions"]["python"]
        for endpoint, meta in manifest.items()
        if isinstance(meta, dict) and "library_versions" in meta
        and not spec.contains(Version(meta["library_versions"]["python"]))
    }
    assert not mismatched, (
        f"served models were trained on Python outside {spec}: {mismatched}"
    )
