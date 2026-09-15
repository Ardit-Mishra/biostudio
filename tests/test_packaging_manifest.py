"""
Guards the packaging manifest against the failure that produced this file.

At some point `requires-python` and the whole `dependencies` array were moved
under the `[project.urls]` table in pyproject.toml. That is valid TOML -- urls
just gained two odd keys -- but under PEP 621 it means `[project]` declares no
dependencies at all. `pip install .` then installs nothing, and `uv lock`
produces a lockfile containing only this package: uv.lock went from 1302 lines
to 8 in 2ba537c and no build broke, because the Dockerfile hardcodes its own
install list and CI installs from requirements.txt.

That is the shape of bug worth a test: it cannot be seen in a diff review, it
produces no error, and every gate stays green while the manifest says nothing.
The checks below are cheap and have no third-party imports beyond tomllib, so
they run in every environment the suite runs in.
"""
import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - the project requires >=3.11
    import tomli as tomllib

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PYPROJECT_PATH = os.path.join(ROOT, "pyproject.toml")
REQUIREMENTS_PATH = os.path.join(ROOT, "requirements.txt")


def _pyproject():
    with open(PYPROJECT_PATH, "rb") as handle:
        return tomllib.load(handle)


def _requirements():
    """Requirement lines from requirements.txt, comments and blanks removed."""
    lines = []
    with open(REQUIREMENTS_PATH, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.split("#", 1)[0].strip()
            if line:
                lines.append(line)
    return lines


class TestProjectTable:
    def test_dependencies_are_declared_on_the_project_table(self):
        project = _pyproject()["project"]
        assert "dependencies" in project, (
            "pyproject.toml [project] declares no dependencies. If the array is "
            "present in the file, check which table it is under -- indenting it "
            "beneath [project.urls] parses fine and silently empties this."
        )
        assert project["dependencies"], "[project].dependencies is empty"

    def test_requires_python_is_declared_on_the_project_table(self):
        project = _pyproject()["project"]
        assert "requires-python" in project

    def test_urls_table_holds_only_urls(self):
        """A packaging key that lands here is the bug this module exists for."""
        urls = _pyproject()["project"].get("urls", {})
        for key, value in urls.items():
            assert isinstance(value, str), (
                f"[project.urls].{key} is a {type(value).__name__}, not a URL "
                "string -- a packaging key has been indented into this table"
            )
            assert value.startswith(("http://", "https://")), (
                f"[project.urls].{key} = {value!r} is not a URL"
            )


class TestManifestParity:
    """requirements.txt says it mirrors [project.dependencies]. Hold it to that."""

    def test_the_two_dependency_lists_are_identical(self):
        declared = sorted(_pyproject()["project"]["dependencies"])
        mirrored = sorted(_requirements())
        assert declared == mirrored, (
            "pyproject.toml and requirements.txt have drifted.\n"
            f"  only in pyproject.toml: {sorted(set(declared) - set(mirrored))}\n"
            f"  only in requirements.txt: {sorted(set(mirrored) - set(declared))}"
        )

    def test_rdkit_is_not_declared_twice(self):
        """rdkit-pypi is the legacy fork; installing both gives two RDKits."""
        names = {d.split(">")[0].split("=")[0].split("<")[0].strip().lower()
                 for d in _pyproject()["project"]["dependencies"]}
        assert not ({"rdkit", "rdkit-pypi"} <= names), (
            "both rdkit and rdkit-pypi are declared; keep only rdkit"
        )


class TestPythonVersionRange:
    def test_the_range_admits_the_interpreter_running_the_tests(self):
        """
        CI runs 3.12 while the Docker image is python:3.11-slim. The bound was
        ">=3.11,<3.12", which excluded the interpreter the suite runs on -- the
        manifest disagreed with both gates at once.
        """
        spec = _pyproject()["project"]["requires-python"]
        packaging = pytest.importorskip(
            "packaging.specifiers", reason="packaging not installed"
        )
        running = ".".join(str(part) for part in sys.version_info[:3])
        assert packaging.SpecifierSet(spec).contains(running), (
            f"requires-python = {spec!r} excludes the running interpreter {running}"
        )
