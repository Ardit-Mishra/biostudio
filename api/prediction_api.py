# =============================================================================
# FASTAPI PREDICTION API MODULE
# =============================================================================
# REST API for the BioStudio prediction platform.
#
# HONESTY CONTRACT (why this file looks the way it does):
# The API used to import ONLY the heuristic modules (models/adme_predictors.py,
# models/toxicity_predictors.py, models/target_predictors.py) -- rule-based
# formulas over RDKit descriptors, explicitly documented in their own
# docstrings as "not from a trained model". Meanwhile the real, held-out-
# validated XGBoost models (models/real_admet.py, trained on TDC data with
# scaffold splits) were wired only into the Streamlit app. The endpoint list
# advertised externally was true; the substance behind it was not.
#
# This module now serves the real models wherever one exists for an endpoint,
# and falls back to the heuristic formulas only where no trained model is
# available -- and every response says, in an explicit "method" field, which
# kind of number it is looking at ("model" vs "heuristic" vs "rule_based").
# Nothing here infers a fact silently: a missing model reports itself as
# missing, a failed featurization reports itself as failed, and no failure
# path ever substitutes a number in place of an error.
#
# Old, unversioned paths (/predict/..., /batch/predict) keep working -- they
# are thin aliases onto the exact same /v1 handlers, so the fix applies to
# both without duplicating logic.
#
# Run with: uvicorn api.prediction_api:app --host 0.0.0.0 --port 8000
# =============================================================================

import os
import sys
import logging
from typing import Annotated, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints
from starlette.exceptions import HTTPException as StarletteHTTPException

# Add parent directory to Python path so sibling packages (utils, models)
# import cleanly regardless of the working directory uvicorn is launched from.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.molecular_utils import MolecularProcessor
from utils.drug_likeness import DrugLikenessCalculator
from models.adme_predictors import ADMEPredictor
from models.toxicity_predictors import ToxicityPredictor
from models.target_predictors import TargetClassPredictor
from models.real_admet import get_predictor as get_real_admet_predictor
from models.real_admet import _TOX_MAP as _REAL_TOX_LABEL_TO_TDC_NAME

_log = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Powered Drug Discovery API",
    description=(
        "REST API for molecular property prediction. ADME/toxicity endpoints "
        "backed by TDC-trained XGBoost models are served from models/real_admet.py "
        "with honest held-out metrics and per-model caveats; endpoints with no "
        "trained model fall back to clearly-labelled rule-based/heuristic scoring."
    ),
    version="2.0.0",
)

# ---- model instances (constructed once, reused for every request) ---------
mol_processor = MolecularProcessor()
drug_likeness = DrugLikenessCalculator()
adme_predictor = ADMEPredictor()          # heuristic fallback only
toxicity_predictor = ToxicityPredictor()  # heuristic fallback only
target_predictor = TargetClassPredictor() # heuristic only -- no trained model exists
real_admet = get_real_admet_predictor()   # validated XGBoost models

BATCH_LIMIT = 50

# =============================================================================
# ERROR ENVELOPE
# =============================================================================
# Every error response -- validation failure, bad SMILES, batch too large,
# unhandled exception -- comes back shaped the same way:
#   {"error": {"code": <int>, "message": <str>, ...}}
# so a client never has to guess whether "detail" is a string or a list, and
# a failure never resembles a successful payload.


def _error_response(status_code: int, message: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": status_code, "message": message, **extra}})


@app.exception_handler(StarletteHTTPException)
async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # 422: the request body itself doesn't satisfy the schema (bad type,
    # SMILES charset/length violation, missing field, etc).
    return _error_response(422, "Request validation failed", details=exc.errors())


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Last resort. The point of this handler existing at all is that no
    # unexpected exception is allowed to turn into a 500 with an HTML
    # traceback page, or worse, a partially-built JSON body that looks like
    # a real result. Log the real exception server-side; never leak internals
    # to the client, and never fabricate a substitute value.
    _log.exception("unhandled exception in %s", request.url.path)
    return _error_response(500, "Internal server error")


# =============================================================================
# REQUEST MODELS
# =============================================================================
# SMILES is not a bare `str`. It is constrained to a plausible SMILES
# character set with sane length bounds, so obviously-malformed input (empty,
# whitespace, prose, absurdly long strings) is rejected as a structured 422
# before it ever reaches RDKit. A syntactically-plausible-but-chemically-
# invalid SMILES (e.g. "C(" ) still passes this constraint and is rejected
# with a 400 by the existing RDKit-backed validate_smiles() check below --
# that distinction (shape vs chemistry) is deliberate.
_SMILES_PATTERN = r"^[A-Za-z0-9@+\-\[\]\(\)=#$:%./\\*]+$"

SmilesStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500, pattern=_SMILES_PATTERN),
]
MoleculeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class MoleculeInput(BaseModel):
    smiles: SmilesStr
    name: Optional[MoleculeName] = None


class BatchMoleculeInput(BaseModel):
    molecules: Annotated[List[MoleculeInput], Field(min_length=1)]


# =============================================================================
# SHARED HELPERS
# =============================================================================


def _validated_mol(smiles: str):
    """Canonicalize + parse a SMILES already known to satisfy the request
    schema. Raises HTTPException(400) for anything RDKit itself rejects --
    never returns a placeholder molecule."""
    is_valid, canonical_or_error = mol_processor.validate_smiles(smiles)
    if not is_valid:
        raise HTTPException(status_code=400, detail=canonical_or_error)
    mol = mol_processor.smiles_to_mol(canonical_or_error)
    if mol is None:
        # Should be unreachable given validate_smiles just approved it, but
        # this is exactly the kind of gap the honesty pass exists to close:
        # if it ever does happen, surface it, don't compute over None.
        raise HTTPException(status_code=400, detail="SMILES parsed as valid but molecule construction failed")
    return canonical_or_error, mol


def _real_model_entry(mol, tdc_name: str) -> Dict:
    """One real-model endpoint result, tagged so a caller can never mistake
    it for a heuristic. `available: False` (never a number) when the model
    didn't load or featurization failed."""
    result = real_admet.predict_endpoint(mol, tdc_name)
    if result is None:
        return {
            "method": "model",
            "available": False,
            "tdc_name": tdc_name,
            "reason": "model not loaded, or featurization failed for this molecule",
        }
    return {"method": "model", "available": True, "tdc_name": tdc_name, **result}


def _heuristic_entry(result: Dict) -> Dict:
    return {"method": "heuristic", **result}


def build_adme_profile(mol) -> Dict:
    """ADME profile grouped by pharmacokinetic phase. Each leaf is tagged
    "model" (real_admet.py, TDC-validated XGBoost) or "heuristic"
    (models/adme_predictors.py -- rule-based, per its own docstring)."""
    return {
        "absorption": {
            "caco2_permeability": _real_model_entry(mol, "Caco2_Wang"),
            "pgp_inhibition": _real_model_entry(mol, "Pgp_Broccatelli"),
            "logp_heuristic": _heuristic_entry(adme_predictor.predict_logp(mol)),
        },
        "distribution": {
            "bbb_penetration": _real_model_entry(mol, "BBB_Martins"),
        },
        "metabolism": {
            "cyp3a4_inhibition": _real_model_entry(mol, "CYP3A4_Veith"),
            # No trained model covers the other CYP isoforms -- heuristic only.
            "cyp450_isoforms_heuristic": _heuristic_entry(adme_predictor.predict_cyp450_metabolism(mol)),
        },
        "excretion": {
            # No trained clearance model exists at all -- heuristic only.
            "clearance_heuristic": _heuristic_entry(adme_predictor.predict_clearance(mol)),
        },
    }


# Real-model toxicity endpoints, by the exact UI label real_admet.py already
# uses, mapped to the heuristic method that stands in when no model is
# loaded for that label (only Carcinogenicity has no trained model today).
_TOX_HEURISTIC_FALLBACK = {
    "Hepatotoxicity": toxicity_predictor.predict_hepatotoxicity,
    "Cardiotoxicity (hERG)": toxicity_predictor.predict_cardiotoxicity_herg,
    "Mutagenicity (Ames)": toxicity_predictor.predict_mutagenicity_ames,
    "Carcinogenicity": toxicity_predictor.predict_carcinogenicity,
}


def build_toxicity_profile(mol) -> Dict:
    """Toxicity profile. Real model output (with provenance + any caveat)
    where a trained model exists for the endpoint; explicitly-labelled
    heuristic fallback otherwise. Never blends the two under one number."""
    model_profile = real_admet.comprehensive_toxicity_profile(mol)
    out: Dict[str, Dict] = {}
    for label, entry in model_profile.items():
        if entry.get("risk_level") == "Unavailable":
            fallback_fn = _TOX_HEURISTIC_FALLBACK.get(label)
            fallback = fallback_fn(mol) if fallback_fn else {"error": "no heuristic available either"}
            out[label] = _heuristic_entry(fallback)
        else:
            tdc_name = _REAL_TOX_LABEL_TO_TDC_NAME.get(label)
            out[label] = {"method": "model", "tdc_name": tdc_name, **entry}
    return out


def build_target_profile(mol) -> Dict:
    """No trained target-class model exists anywhere in this repo -- this
    endpoint is heuristic end to end, and says so at the top level rather
    than per-field, since every field here is the same kind of number."""
    return {"method": "heuristic", "prediction": target_predictor.comprehensive_target_prediction(mol)}


def build_druglikeness_profile(mol) -> Dict:
    """Lipinski/Veber/QED/SA are established deterministic cheminformatics
    formulas, not a fitted model and not a guess -- "rule_based" distinguishes
    this from both "model" (held-out-validated) and "heuristic" (informal
    rule-of-thumb scoring)."""
    return {"method": "rule_based", **drug_likeness.comprehensive_analysis(mol)}


# =============================================================================
# ROOT / HEALTH / READINESS
# =============================================================================


@app.get("/")
def read_root() -> Dict:
    return {
        "message": "AI-Powered Drug Discovery API",
        "description": "Computational chemistry and machine learning platform for pharmaceutical research",
        "version": app.version,
        "docs": "/docs",
        "endpoints": [
            "/v1/predict/druglikeness",
            "/v1/predict/adme",
            "/v1/predict/toxicity",
            "/v1/predict/target",
            "/v1/predict/comprehensive",
            "/v1/batch/predict",
            "/v1/health",
            "/v1/ready",
        ],
        "note": "Unversioned /predict/* and /batch/predict paths still work as aliases of the /v1/* routes above.",
    }


@app.get("/v1/health")
def health() -> Dict:
    """Liveness only: the process is up and answering requests. Says nothing
    about whether the real models actually loaded -- that's /v1/ready."""
    return {"status": "ok"}


@app.get("/v1/ready")
def ready() -> Dict:
    """Readiness: did the 7 validated XGBoost models actually load, not just
    'is the process running'. Reports exactly which ones are missing rather
    than collapsing to a single ok/not-ok bit."""
    manifest_names = sorted(real_admet.meta.keys()) if real_admet.meta else sorted(real_admet.models.keys())
    loaded_names = sorted(real_admet.models.keys())
    missing = sorted(set(manifest_names) - set(loaded_names))
    is_ready = real_admet.available() and not missing and len(loaded_names) > 0
    body = {
        "ready": is_ready,
        "models_loaded": loaded_names,
        "models_expected": manifest_names,
        "models_missing": missing,
        "model_dir": real_admet.model_dir,
    }
    if not is_ready:
        return JSONResponse(status_code=503, content=body)
    return body


# =============================================================================
# V1 PREDICTION ENDPOINTS
# =============================================================================


@app.post("/v1/predict/druglikeness")
def predict_druglikeness_v1(molecule: MoleculeInput) -> Dict:
    canonical_smiles, mol = _validated_mol(molecule.smiles)
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "analysis": build_druglikeness_profile(mol),
    }


@app.post("/v1/predict/adme")
def predict_adme_v1(molecule: MoleculeInput) -> Dict:
    canonical_smiles, mol = _validated_mol(molecule.smiles)
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "adme_profile": build_adme_profile(mol),
    }


@app.post("/v1/predict/toxicity")
def predict_toxicity_v1(molecule: MoleculeInput) -> Dict:
    canonical_smiles, mol = _validated_mol(molecule.smiles)
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "toxicity_profile": build_toxicity_profile(mol),
    }


@app.post("/v1/predict/target")
def predict_target_v1(molecule: MoleculeInput) -> Dict:
    canonical_smiles, mol = _validated_mol(molecule.smiles)
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "target_prediction": build_target_profile(mol),
    }


@app.post("/v1/predict/comprehensive")
def predict_comprehensive_v1(molecule: MoleculeInput) -> Dict:
    canonical_smiles, mol = _validated_mol(molecule.smiles)
    return {
        "molecule_name": molecule.name or "Unknown",
        "smiles": canonical_smiles,
        "basic_properties": mol_processor.calculate_basic_properties(mol),
        "drug_likeness": build_druglikeness_profile(mol),
        "adme_profile": build_adme_profile(mol),
        "toxicity_profile": build_toxicity_profile(mol),
        "target_prediction": build_target_profile(mol),
    }


@app.post("/v1/batch/predict")
def batch_predict_v1(batch: BatchMoleculeInput) -> List[Dict]:
    if len(batch.molecules) > BATCH_LIMIT:
        raise HTTPException(
            status_code=413,
            detail=f"Batch of {len(batch.molecules)} molecules exceeds the {BATCH_LIMIT}-molecule limit",
        )

    results = []
    for molecule in batch.molecules:
        try:
            canonical_smiles, mol = _validated_mol(molecule.smiles)
        except HTTPException as exc:
            # Per-molecule failure, not a batch failure: report it and keep
            # going, exactly like the rest of the batch's siblings expect.
            results.append({"molecule_name": molecule.name or "Unknown", "error": str(exc.detail)})
            continue
        try:
            results.append({
                "molecule_name": molecule.name or "Unknown",
                "smiles": canonical_smiles,
                "drug_likeness": build_druglikeness_profile(mol),
                "adme_profile": build_adme_profile(mol),
                "toxicity_profile": build_toxicity_profile(mol),
            })
        except Exception as exc:  # noqa: BLE001 -- deliberately broad: one bad
            # molecule in a 50-molecule batch must not fail the other 49, but
            # it must show up as an explicit error, never as a missing or
            # substitute result.
            _log.exception("batch prediction failed for molecule %r", molecule.smiles)
            results.append({
                "molecule_name": molecule.name or "Unknown",
                "smiles": canonical_smiles,
                "error": f"{type(exc).__name__}: {exc}",
            })
    return results


# =============================================================================
# BACK-COMPAT ALIASES -- same handlers, old unversioned paths
# =============================================================================
# The résumé/README-documented paths keep working. These are not separate
# implementations to keep in sync -- add_api_route binds the exact same
# function object /v1 uses, so the honesty fix applies to both automatically.

app.add_api_route("/predict/druglikeness", predict_druglikeness_v1, methods=["POST"])
app.add_api_route("/predict/adme", predict_adme_v1, methods=["POST"])
app.add_api_route("/predict/toxicity", predict_toxicity_v1, methods=["POST"])
app.add_api_route("/predict/target", predict_target_v1, methods=["POST"])
app.add_api_route("/predict/comprehensive", predict_comprehensive_v1, methods=["POST"])
app.add_api_route("/batch/predict", batch_predict_v1, methods=["POST"])


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
