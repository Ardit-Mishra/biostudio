"""
BioStudio featurization — the full RDKit descriptor set (200+), shared by
training (this file, imported by train_and_save_admet.py) and serving
(Ardit-BioStudio/models/descriptors.py — a separate git repo, kept
byte-identical to this file by hand, the same convention real_admet.py
already documents for the old 10-descriptor spec).

Computes ECFP4/Morgan fingerprint (2048 bits, radius 2) + every descriptor in
`rdkit.Chem.Descriptors._descList` (217 in RDKit 2025.9/2026.3 — this is what
makes the résumé's "computes 200+ molecular descriptors via RDKit" claim
actually true. The previous implementation, `MolecularProcessor.
calculate_molecular_descriptors` in Ardit-BioStudio/utils/molecular_utils.py,
computed ~30 real descriptors and padded the remaining 170 slots with the
literal integer 0 to hit the number 200 — a fabricated feature vector, not a
real one. That function is untouched by this change (it isn't on the ADMET
training/serving path) but must never be cited as the "200+ descriptors"
implementation; this module is.

Column order is the descriptor name sorted alphabetically, not
`Descriptors._descList`'s own insertion order — pinning it explicitly means a
future RDKit upgrade that reorders its internal list can't silently shift
every downstream feature index against models already trained on the old
order (the exact class of bug documented in real_admet.py's "NOTE ON A FIXED
BUG").

Per-descriptor failure handling: a descriptor that *raises* for a given
molecule (rare — e.g. the BCUT2D_* descriptors need Gasteiger partial charges
that don't converge on some structures) gets NaN in its slot for that
molecule, and the failure (which molecule, which descriptor, what exception)
is appended to the caller-supplied `failures` list — never silently replaced
with 0.0 or any other plausible-looking number. NaN is XGBoost's own default
"missing" sentinel, so trees route around it correctly with no extra work.
scikit-learn's RandomForest/MLP do not accept NaN, so callers training those
must impute explicitly (median, fit on train only — see
train_and_save_admet.py) rather than relying on a silent default.

A descriptor that returns a value without raising, but that value is itself
non-finite (NaN/inf — a legitimate degenerate result for some odd fragment,
e.g. an undefined ratio), is coerced to 0.0. That is a real computed result,
not a crash, and is intentionally distinct from the exception case above:
only an exception is a "failure" worth recording, matching the precedent set
in Ardit-BioStudio/models/real_admet.py's `_featurize_one`.
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import RDLogger

RDLogger.DisableLog("rdApp.*")

try:
    from rdkit.Chem import rdFingerprintGenerator

    _MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

    def _fp(m):
        return np.asarray(_MG.GetFingerprintAsNumPy(m), dtype=np.float32)
except Exception:
    from rdkit.Chem import AllChem, DataStructs

    def _fp(m):
        bv = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
        a = np.zeros((2048,), np.float32)
        DataStructs.ConvertToNumpyArray(bv, a)
        return a


FP_BITS = 2048

# Full RDKit descriptor set, name-sorted for a stable, documented column order.
_DESC_ITEMS = sorted(Descriptors._descList, key=lambda kv: kv[0])
DESC_NAMES: List[str] = [name for name, _ in _DESC_ITEMS]
_DESC_FUNCS = [func for _, func in _DESC_ITEMS]
N_DESC = len(DESC_NAMES)
NFEAT = FP_BITS + N_DESC

FEATURE_SPEC = {
    "fingerprint": f"ECFP4/Morgan radius=2 nBits={FP_BITS}",
    "descriptors": DESC_NAMES,
    "n_descriptors": N_DESC,
    "n_features": NFEAT,
    "descriptor_source": "rdkit.Chem.Descriptors._descList (full set, not a curated subset)",
    "missing_value_sentinel": "NaN — marks a descriptor that raised for this molecule; "
                               "never a substituted 0.0 or other plausible-looking value",
}


class FeaturizationError(RuntimeError):
    """The molecule itself could not be featurized at all (didn't parse)."""


def feature_name(index: int) -> str:
    """Human-readable name for column `index` of the NFEAT-length vector —
    used by SHAP reporting so a top contributing feature reads as
    'TPSA' or 'ECFP4 bit 1042', never a bare integer."""
    if index < FP_BITS:
        return f"ECFP4 bit {index}"
    return DESC_NAMES[index - FP_BITS]


def featurize_one(mol_or_smiles, source: Optional[str] = None,
                   failures: Optional[list] = None) -> np.ndarray:
    """One molecule -> length-NFEAT float32 vector.

    `mol_or_smiles` may be an RDKit Mol or a SMILES string. `source` labels
    this molecule in failure records (defaults to the SMILES / canonical
    SMILES). `failures`, if given, is appended to in place with one dict per
    descriptor that raised for this molecule — the caller decides what to do
    with that record (log it, drop the row, surface it); this function never
    decides silently on the caller's behalf.

    Raises FeaturizationError if the molecule doesn't parse at all — there is
    no valid feature vector to substitute for a structure RDKit can't read.
    """
    mol = Chem.MolFromSmiles(mol_or_smiles) if isinstance(mol_or_smiles, str) else mol_or_smiles
    if mol is None:
        raise FeaturizationError(f"no molecule (SMILES did not parse): {source or mol_or_smiles!r}")
    label = source if source is not None else (
        mol_or_smiles if isinstance(mol_or_smiles, str) else Chem.MolToSmiles(mol))

    fp = _fp(mol)
    desc = np.empty(N_DESC, dtype=np.float32)
    for i, (name, func) in enumerate(zip(DESC_NAMES, _DESC_FUNCS)):
        try:
            v = np.float32(func(mol))
            # Checked post-cast, not on the float64 value: a descriptor can
            # legitimately return a finite float64 (e.g. ~1e40 on some
            # complexity index for an unusual structure) that overflows to
            # +-inf only once narrowed to float32 -- catching it here, not
            # before the cast, is what actually keeps inf out of the array
            # this function returns.
            desc[i] = v if np.isfinite(v) else np.float32(0.0)
        except Exception as exc:
            desc[i] = np.nan
            if failures is not None:
                failures.append({
                    "molecule": label,
                    "descriptor": name,
                    "error": f"{type(exc).__name__}: {exc}",
                })
    return np.concatenate([fp, desc])


def featurize_many(smiles_list, failures: Optional[list] = None,
                    drop_unparseable: bool = True):
    """List of SMILES -> (n, NFEAT) float32 matrix (+ the kept-index list,
    since `drop_unparseable=True` may drop rows and callers need to filter
    their labels/ids the same way).

    A SMILES that fails to parse at all is dropped (not zero-filled) when
    `drop_unparseable` is True and recorded in `failures` as a
    'descriptor': '(unparseable molecule)' entry; with `drop_unparseable=False`
    the first bad SMILES raises FeaturizationError instead.

    Returns (X, kept_indices).
    """
    rows = []
    kept = []
    for i, sm in enumerate(smiles_list):
        try:
            rows.append(featurize_one(sm, source=sm, failures=failures))
            kept.append(i)
        except FeaturizationError as exc:
            if not drop_unparseable:
                raise
            if failures is not None:
                failures.append({"molecule": sm, "descriptor": "(unparseable molecule)",
                                  "error": str(exc)})
    X = np.vstack(rows) if rows else np.empty((0, NFEAT), dtype=np.float32)
    return X, kept
