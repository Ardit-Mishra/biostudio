"""
CI gate for the served ADMET model suite (models/saved_models/*).

These tests exist to catch exactly what a model swap or a bad retrain could
silently break: an orphaned model file, a changed prediction schema, a model
that no longer loads, a known-direction prediction flipping, or a model card
that drifts from the manifest it is supposed to describe. They do not
re-validate the models' held-out scores (that is the training script's job,
recorded in admet_models_manifest.json) -- they validate that what is
shipped and documented stays consistent with itself.
"""
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

MODELDIR = os.path.join(ROOT, "models", "saved_models")
MANIFEST_PATH = os.path.join(MODELDIR, "admet_models_manifest.json")
MODEL_CARD_PATH = os.path.join(MODELDIR, "README.md")
ROOT_README_PATH = os.path.join(ROOT, "README.md")

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
# Caffeine is a well-documented CNS-active molecule -- its central stimulant
# effect depends on crossing the blood-brain barrier, so the BBB_Martins
# model predicting it a high-confidence permeant is a real, checkable fact,
# not an accuracy claim about the model in general.
CAFFEINE = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"


def _manifest() -> dict:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def _xgb_filename(name: str) -> str:
    return f"{name}_xgb.json"


def _meta_filename(name: str) -> str:
    return f"{name}_meta.json"


class TestArtifactMetadataValidity:
    """Every manifest entry must have both artifact files on disk, and every
    artifact file on disk must have a manifest entry -- no orphans in
    either direction."""

    def test_manifest_entries_have_both_files_on_disk(self):
        manifest = _manifest()
        missing = []
        for name in manifest:
            for path in (
                os.path.join(MODELDIR, _xgb_filename(name)),
                os.path.join(MODELDIR, _meta_filename(name)),
            ):
                if not os.path.exists(path):
                    missing.append(path)
        assert not missing, f"manifest entries missing on-disk files: {missing}"

    def test_no_orphan_model_files_outside_manifest(self):
        manifest = _manifest()
        on_disk = os.listdir(MODELDIR)
        xgb_names = {f[: -len("_xgb.json")] for f in on_disk if f.endswith("_xgb.json")}
        meta_names = {f[: -len("_meta.json")] for f in on_disk if f.endswith("_meta.json")}
        orphans = (xgb_names | meta_names) - set(manifest.keys())
        assert not orphans, f"model files on disk with no manifest entry: {orphans}"

    def test_meta_json_matches_its_own_manifest_entry(self):
        manifest = _manifest()
        for name, meta in manifest.items():
            with open(os.path.join(MODELDIR, _meta_filename(name)), encoding="utf-8") as f:
                on_disk_meta = json.load(f)
            assert on_disk_meta["test_score"] == meta["test_score"], (
                f"{name}: manifest test_score disagrees with {name}_meta.json"
            )
            assert on_disk_meta["model_file"] == _xgb_filename(name)


class TestModelsLoad:
    def test_every_manifest_model_actually_loads(self):
        from models.real_admet import RealADMETPredictor

        predictor = RealADMETPredictor(model_dir=MODELDIR)
        manifest = _manifest()
        missing = set(manifest.keys()) - set(predictor.models.keys())
        assert not missing, f"models present in manifest but failed to load: {missing}"
        assert predictor.available()


class TestPredictionSchema:
    @classmethod
    @pytest.fixture(scope="class")
    def predictor(cls):
        from models.real_admet import RealADMETPredictor

        return RealADMETPredictor(model_dir=MODELDIR)

    def test_classification_schema(self, predictor):
        manifest = _manifest()
        clf_name = next(n for n, m in manifest.items() if m["task"] == "classification")
        result = predictor.predict_endpoint(ASPIRIN, clf_name)
        assert result is not None
        for key in ("task", "probability", "threshold", "positive", "metric",
                    "test_score", "provenance", "app_label"):
            assert key in result, f"classification result missing '{key}'"
        assert result["task"] == "classification"
        assert isinstance(result["probability"], float)
        assert 0.0 <= result["probability"] <= 1.0
        assert isinstance(result["positive"], bool)

    def test_regression_schema(self, predictor):
        manifest = _manifest()
        reg_name = next(n for n, m in manifest.items() if m["task"] == "regression")
        result = predictor.predict_endpoint(ASPIRIN, reg_name)
        assert result is not None
        for key in ("task", "value", "metric", "test_score", "provenance", "app_label"):
            assert key in result, f"regression result missing '{key}'"
        assert result["task"] == "regression"
        assert isinstance(result["value"], float)

    def test_unknown_endpoint_returns_none(self, predictor):
        assert predictor.predict_endpoint(ASPIRIN, "NotARealEndpoint") is None

    def test_invalid_smiles_returns_none(self, predictor):
        any_name = next(iter(_manifest()))
        assert predictor.predict_endpoint("not a smiles!!", any_name) is None


class TestKnownMoleculeRange:
    def test_caffeine_predicted_bbb_permeant(self):
        from models.real_admet import RealADMETPredictor

        predictor = RealADMETPredictor(model_dir=MODELDIR)
        if "BBB_Martins" not in predictor.models:
            pytest.skip("BBB_Martins model not present")
        result = predictor.predict_endpoint(CAFFEINE, "BBB_Martins")
        assert result is not None
        assert result["positive"] is True
        assert result["probability"] > 0.5


class TestModelCardMatchesManifest:
    """models/saved_models/README.md's 'Held-out test performance' table is
    the model card a recruiter or reviewer actually reads. Its numbers must
    trace to admet_models_manifest.json (what real_admet.py serves from) --
    otherwise it is an unreproducible claim, which is exactly what this
    stage exists to prevent."""

    def test_readme_table_scores_match_manifest(self):
        manifest = _manifest()
        with open(MODEL_CARD_PATH, encoding="utf-8") as f:
            readme = f.read()
        for name, meta in manifest.items():
            label = re.escape(meta["app_label"])
            score_str = re.escape(f"{meta['test_score']:.3f}")
            pattern = rf"\|\s*{label}\s*\|[^|]*\|[^|]*\|\s*{score_str}"
            assert re.search(pattern, readme), (
                f"{name}: model card does not show manifest test_score "
                f"{meta['test_score']:.3f} for '{meta['app_label']}'"
            )

    # Short label each endpoint is known by in the top-level README's prose
    # summary (README.md is not a table -- it's a one-line "DILI 0.925, hERG
    # 0.809, ..." sentence aimed at a skimming recruiter, not the detailed
    # model card). This is what caught the P0: the root README had drifted
    # to the pre-swap numbers while the model card was updated.
    ROOT_README_LABELS = {
        "DILI": "DILI",
        "hERG": "hERG",
        "AMES": "Ames",
        "BBB_Martins": "BBB",
        "Pgp_Broccatelli": "P-gp",
        "CYP3A4_Veith": "CYP3A4",
        "Caco2_Wang": "Caco-2",
    }

    def test_root_readme_scores_match_manifest(self):
        manifest = _manifest()
        with open(ROOT_README_PATH, encoding="utf-8") as f:
            root_readme = f.read()
        # Collapse whitespace/newlines so a score wrapped across lines still matches.
        flat = re.sub(r"\s+", " ", root_readme)
        for name, meta in manifest.items():
            short_label = self.ROOT_README_LABELS[name]
            score_str = re.escape(f"{meta['test_score']:.3f}")
            pattern = rf"{re.escape(short_label)}\s+{score_str}"
            assert re.search(pattern, flat), (
                f"{name}: top-level README.md does not show current manifest "
                f"test_score {meta['test_score']:.3f} next to '{short_label}' "
                f"-- it has likely drifted from models/saved_models/admet_models_manifest.json"
            )
