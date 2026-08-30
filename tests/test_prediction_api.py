"""
Tests for the FastAPI prediction service (api/prediction_api.py).

The centerpiece here is TestServeParity: the same SMILES, through the HTTP
API and directly through models.real_admet.RealADMETPredictor.predict_endpoint,
must produce byte-identical numbers. This is the check that would have caught
the historical bug where the API served a different (heuristic) code path
than the Streamlit app for what was supposedly "the same" prediction --
a feature-set/backend mismatch with no test anywhere to catch it.

Requires `httpx` (Starlette's TestClient dependency) in addition to the main
requirements.txt -- not part of api/requirements.txt, which is runtime-only.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from api.prediction_api import app, real_admet  # noqa: E402
from models.real_admet import get_predictor  # noqa: E402

client = TestClient(app)

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"
CAFFEINE = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
MALFORMED_NOT_SMILES = "this is not a smiles string!!!"
CHEMICALLY_INVALID_BUT_CHARSET_OK = "C(("  # passes the charset/length pattern, fails RDKit parsing


# =============================================================================
# Serve parity: API result === direct predictor result, for every real model.
# =============================================================================
class TestServeParityADME:
    """These four ADME endpoints are surfaced via real_admet.predict_endpoint
    with no reformatting in between -- the API's number must be exactly the
    predictor's number."""

    @pytest.mark.parametrize("smiles", [ASPIRIN, CAFFEINE])
    @pytest.mark.parametrize("tdc_name", ["BBB_Martins", "Pgp_Broccatelli", "CYP3A4_Veith", "Caco2_Wang"])
    def test_adme_endpoint_matches_direct_predictor(self, smiles, tdc_name):
        direct = get_predictor().predict_endpoint(smiles, tdc_name)
        if direct is None:
            pytest.skip(f"{tdc_name} model not loaded in this environment")

        resp = client.post("/v1/predict/adme", json={"smiles": smiles})
        assert resp.status_code == 200, resp.text
        body = resp.json()

        found = None
        for section in body["adme_profile"].values():
            for entry in section.values():
                if entry.get("tdc_name") == tdc_name:
                    found = entry
                    break
        assert found is not None, f"{tdc_name} not present anywhere in the ADME response"
        assert found["method"] == "model"
        assert found["available"] is True
        for key, value in direct.items():
            assert found.get(key) == value, f"{tdc_name}.{key}: api={found.get(key)!r} direct={value!r}"


class TestServeParityToxicity:
    """DILI/hERG/AMES are surfaced via real_admet.comprehensive_toxicity_profile
    (a reformatted, UI-shaped view, not the raw predict_endpoint dict) -- so
    parity here is against that same method, called independently, to prove
    the API is actually invoking it rather than some other code path that
    happens to produce a similarly-shaped number."""

    @pytest.mark.parametrize("smiles", [ASPIRIN, CAFFEINE])
    @pytest.mark.parametrize(
        "label,tdc_name", [("Hepatotoxicity", "DILI"), ("Cardiotoxicity (hERG)", "hERG"), ("Mutagenicity (Ames)", "AMES")]
    )
    def test_toxicity_endpoint_matches_direct_predictor(self, smiles, label, tdc_name):
        from rdkit import Chem

        predictor = get_predictor()
        if tdc_name not in predictor.models:
            pytest.skip(f"{tdc_name} model not loaded in this environment")
        direct_profile = predictor.comprehensive_toxicity_profile(Chem.MolFromSmiles(smiles))
        direct = direct_profile[label]

        resp = client.post("/v1/predict/toxicity", json={"smiles": smiles})
        assert resp.status_code == 200, resp.text
        found = resp.json()["toxicity_profile"][label]

        assert found["method"] == "model"
        assert found["tdc_name"] == tdc_name
        for key, value in direct.items():
            assert found.get(key) == value, f"{label}.{key}: api={found.get(key)!r} direct={value!r}"


# =============================================================================
# Endpoints respond, are labelled honestly, and never fabricate a number.
# =============================================================================
class TestEndpointsRespond:
    def test_root_lists_v1_endpoints(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "/v1/predict/comprehensive" in resp.json()["endpoints"]

    def test_druglikeness_v1(self):
        resp = client.post("/v1/predict/druglikeness", json={"smiles": ASPIRIN, "name": "aspirin"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["molecule_name"] == "aspirin"
        assert body["analysis"]["method"] == "rule_based"

    def test_adme_v1_labels_model_and_heuristic_entries(self):
        resp = client.post("/v1/predict/adme", json={"smiles": ASPIRIN})
        assert resp.status_code == 200, resp.text
        profile = resp.json()["adme_profile"]
        assert profile["absorption"]["caco2_permeability"]["method"] == "model"
        assert profile["absorption"]["caco2_permeability"]["available"] is True
        assert profile["absorption"]["logp_heuristic"]["method"] == "heuristic"
        assert profile["excretion"]["clearance_heuristic"]["method"] == "heuristic"

    def test_toxicity_v1_real_models_carry_provenance_and_carcinogenicity_falls_back(self):
        resp = client.post("/v1/predict/toxicity", json={"smiles": ASPIRIN})
        assert resp.status_code == 200, resp.text
        profile = resp.json()["toxicity_profile"]
        assert profile["Hepatotoxicity"]["method"] == "model"
        assert "TDC held-out test" in profile["Hepatotoxicity"]["confidence"]
        # No trained Carcinogens_Lagunin model ships today -- must fall back
        # to the heuristic, explicitly labelled, never silently "model".
        assert profile["Carcinogenicity"]["method"] == "heuristic"

    def test_target_v1_is_wholly_heuristic(self):
        resp = client.post("/v1/predict/target", json={"smiles": ASPIRIN})
        assert resp.status_code == 200, resp.text
        assert resp.json()["target_prediction"]["method"] == "heuristic"

    def test_comprehensive_v1(self):
        resp = client.post("/v1/predict/comprehensive", json={"smiles": ASPIRIN})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        for key in ("basic_properties", "drug_likeness", "adme_profile", "toxicity_profile", "target_prediction"):
            assert key in body

    def test_batch_predict_v1(self):
        resp = client.post(
            "/v1/batch/predict",
            json={"molecules": [{"smiles": ASPIRIN, "name": "aspirin"}, {"smiles": CAFFEINE, "name": "caffeine"}]},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body) == 2
        assert all("error" not in r for r in body)


# =============================================================================
# Old unversioned paths are aliases, not a second implementation.
# =============================================================================
class TestBackCompatAliases:
    def test_unversioned_druglikeness_matches_v1(self):
        r1 = client.post("/predict/druglikeness", json={"smiles": ASPIRIN})
        r2 = client.post("/v1/predict/druglikeness", json={"smiles": ASPIRIN})
        assert r1.status_code == r2.status_code == 200
        assert r1.json() == r2.json()

    def test_unversioned_batch_predict_exists(self):
        resp = client.post("/batch/predict", json={"molecules": [{"smiles": ASPIRIN}]})
        assert resp.status_code == 200


# =============================================================================
# Structured errors -- never a number on a failure path.
# =============================================================================
class TestErrorEnvelope:
    def test_malformed_smiles_is_structured_422(self):
        resp = client.post("/v1/predict/druglikeness", json={"smiles": MALFORMED_NOT_SMILES})
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body and "code" in body["error"] and "message" in body["error"]

    def test_empty_smiles_is_structured_422(self):
        resp = client.post("/v1/predict/druglikeness", json={"smiles": ""})
        assert resp.status_code == 422
        assert "error" in resp.json()

    def test_missing_smiles_field_is_structured_422(self):
        resp = client.post("/v1/predict/druglikeness", json={})
        assert resp.status_code == 422
        assert "error" in resp.json()

    def test_chemically_invalid_smiles_is_structured_400(self):
        resp = client.post("/v1/predict/druglikeness", json={"smiles": CHEMICALLY_INVALID_BUT_CHARSET_OK})
        assert resp.status_code == 400
        body = resp.json()
        assert "error" in body and "code" in body["error"] and "message" in body["error"]

    def test_batch_over_limit_is_413(self):
        molecules = [{"smiles": ASPIRIN} for _ in range(51)]
        resp = client.post("/v1/batch/predict", json={"molecules": molecules})
        assert resp.status_code == 413
        body = resp.json()
        assert body["error"]["code"] == 413

    def test_batch_at_limit_is_accepted(self):
        molecules = [{"smiles": ASPIRIN} for _ in range(50)]
        resp = client.post("/v1/batch/predict", json={"molecules": molecules})
        assert resp.status_code == 200
        assert len(resp.json()) == 50


# =============================================================================
# Health vs readiness are different questions with different answers.
# =============================================================================
class TestHealthAndReadiness:
    def test_health_is_liveness_only(self):
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_ready_reports_which_models_actually_loaded(self):
        resp = client.get("/v1/ready")
        body = resp.json()
        assert "models_loaded" in body and "models_missing" in body
        if real_admet.available() and not body["models_missing"]:
            assert resp.status_code == 200
            assert body["ready"] is True
        else:
            assert resp.status_code == 503
            assert body["ready"] is False


# =============================================================================
# OpenAPI docs are free with FastAPI -- confirm they're actually served.
# =============================================================================
class TestDocs:
    def test_docs_served(self):
        assert client.get("/docs").status_code == 200

    def test_openapi_schema_served(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        assert resp.json()["info"]["version"] == "2.0.0"
