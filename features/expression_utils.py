"""
Gene-Expression Heatmap Utilities

Parses a genes x samples expression matrix (CSV/TSV), offers log2 and
per-gene z-score normalisation, hierarchically clusters genes and/or
samples with scipy, and renders a clustered heatmap (dendrograms + heatmap)
with Plotly.

Author: Ardit Mishra
"""

from __future__ import annotations

import io
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist

NORMALIZATIONS = ("none", "log2", "zscore", "log2_zscore")
LINKAGE_METHODS = ("average", "complete", "single", "ward")
DISTANCE_METRICS = ("euclidean", "correlation", "cosine", "cityblock")


class ExpressionError(Exception):
    """Raised for any input this module cannot honestly turn into a
    heatmap — malformed matrix, non-numeric values, too few rows/columns to
    cluster, or a degenerate normalisation. Never substitutes a zero or an
    empty result for a real failure."""


def parse_expression_matrix(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse an uploaded genes x samples expression matrix.

    Expects the first column to be the gene/feature identifier (becomes the
    DataFrame index) and the remaining columns to be numeric sample values,
    comma- or tab-delimited (delimiter chosen by file extension, falling
    back to sniffing the first line).

    Args:
        file_bytes: raw uploaded file content.
        filename: original filename, used to pick '.csv' vs '.tsv'/'.txt'
            delimiter and to name errors.

    Returns:
        DataFrame indexed by gene ID, columns are sample names, all values
        numeric float64.

    Raises:
        ExpressionError: undecodable content, empty file, any non-numeric
            expression value, fewer than 2 genes, or fewer than 2 samples.
            A matrix with bad cells is rejected outright rather than
            coercing those cells to NaN/0 and rendering a heatmap with
            fabricated holes.
    """
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ExpressionError(f"Could not decode '{filename}' as text: {exc}") from None

    if not text.strip():
        raise ExpressionError(f"'{filename}' is empty.")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    first_line = text.strip().split("\n", 1)[0]
    if ext == "csv":
        sep = ","
    elif ext in {"tsv", "txt"}:
        sep = "\t"
    else:
        # Sniff: prefer tab if present, else comma.
        sep = "\t" if "\t" in first_line else ","

    try:
        df = pd.read_csv(io.StringIO(text), sep=sep, index_col=0)
    except Exception as exc:
        raise ExpressionError(f"Could not parse '{filename}' as a delimited matrix: {exc}") from None

    if df.shape[0] == 0 or df.shape[1] == 0:
        raise ExpressionError(
            f"'{filename}' parsed to an empty matrix ({df.shape[0]} rows x {df.shape[1]} cols)."
        )

    non_numeric_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric_cols:
        # Try coercion once, per-column, so we can report exactly which
        # cell is bad rather than a vague "some column is bad".
        for col in non_numeric_cols:
            coerced = pd.to_numeric(df[col], errors="coerce")
            bad_mask = coerced.isna() & df[col].notna()
            if bad_mask.any():
                bad_gene = bad_mask.idxmax()
                bad_value = df.loc[bad_mask, col].iloc[0]
                raise ExpressionError(
                    f"Non-numeric expression value in column '{col}', row "
                    f"'{bad_gene}': '{bad_value}'. Every value except the "
                    "gene-ID column must be numeric."
                )
            df[col] = coerced

    if df.isna().any().any():
        raise ExpressionError(
            "Matrix contains missing values after parsing — every gene x "
            "sample cell must have a numeric value."
        )

    if df.shape[0] < 2:
        raise ExpressionError(f"Need at least 2 genes to cluster (got {df.shape[0]}).")
    if df.shape[1] < 2:
        raise ExpressionError(f"Need at least 2 samples to cluster (got {df.shape[1]}).")

    return df.astype(float)


def normalize_matrix(df: pd.DataFrame, method: str = "none") -> Tuple[pd.DataFrame, List[str]]:
    """Normalise an expression matrix.

    Args:
        df: genes (rows) x samples (columns), numeric.
        method: one of `NORMALIZATIONS`.
            - "none": pass through unchanged.
            - "log2": log2(x + 1), a standard variance-stabilising
              transform for count-like data with a fixed, honest pseudocount.
            - "zscore": per-gene (row) z-score, (x - mean) / std.
            - "log2_zscore": log2(x + 1) then per-gene z-score.

    Returns:
        (normalized_df, dropped_gene_ids) — a z-score step drops any gene
        with zero variance across samples (its z-score is 0/0, mathematically
        undefined) rather than reporting a fabricated 0.0 for it. For
        "none"/"log2", dropped_gene_ids is always empty.

    Raises:
        ExpressionError: unknown method, a negative value under log2 (log
            of a negative number is undefined for real expression data —
            surfaced rather than silently producing NaN), or every gene
            dropped for zero variance (nothing left to show).
    """
    if method not in NORMALIZATIONS:
        raise ExpressionError(f"Unknown normalization '{method}'. Choose one of: {', '.join(NORMALIZATIONS)}")

    out = df.copy()
    dropped: List[str] = []

    if method in {"log2", "log2_zscore"}:
        if (out < 0).any().any():
            raise ExpressionError(
                "Matrix contains negative values — log2 normalization expects "
                "non-negative expression values (counts/TPM/FPKM)."
            )
        out = np.log2(out + 1.0)

    if method in {"zscore", "log2_zscore"}:
        std = out.std(axis=1, ddof=0)
        zero_var = std[std == 0].index.tolist()
        if zero_var:
            dropped = list(zero_var)
            out = out.drop(index=zero_var)
        if out.shape[0] == 0:
            raise ExpressionError(
                "Every gene had zero variance across samples — z-score "
                "normalization has nothing left to show."
            )
        mean = out.mean(axis=1)
        std = out.std(axis=1, ddof=0)
        out = out.sub(mean, axis=0).div(std, axis=0)

    return out, dropped


def _linkage_and_order(
    matrix: np.ndarray, metric: str, method: str
) -> Tuple[np.ndarray, List[int]]:
    """Shared clustering step for rows or columns. `matrix` is items x features."""
    if matrix.shape[0] < 2:
        raise ExpressionError(f"Need at least 2 items to cluster (got {matrix.shape[0]}).")
    if method == "ward" and metric != "euclidean":
        # scipy itself would raise for this combination; naming it here
        # produces a clearer message than the underlying ValueError text.
        raise ExpressionError("The 'ward' linkage method requires the 'euclidean' metric.")
    try:
        distances = pdist(matrix, metric=metric)
    except Exception as exc:
        raise ExpressionError(f"Could not compute {metric} distances: {exc}") from None
    if not np.all(np.isfinite(distances)):
        raise ExpressionError(
            f"{metric} distance produced a non-finite value — check for constant rows/columns."
        )
    z = linkage(distances, method=method)
    order = dendrogram(z, no_plot=True)["leaves"]
    return z, order


def cluster_matrix(
    df: pd.DataFrame,
    cluster_rows: bool = True,
    cluster_cols: bool = True,
    metric: str = "euclidean",
    method: str = "average",
) -> dict:
    """Hierarchically cluster a normalized expression matrix.

    Args:
        df: genes x samples, numeric, already normalized if desired.
        cluster_rows, cluster_cols: whether to reorder that axis by its
            dendrogram leaf order (the axis is left in its original order
            if False).
        metric: a `scipy.spatial.distance.pdist` metric name.
        method: a `scipy.cluster.hierarchy.linkage` method name.

    Returns:
        Dict with:
          - matrix: DataFrame reordered per the requested clustering.
          - row_linkage, col_linkage: scipy linkage matrices, or None if
            that axis wasn't clustered.

    Raises:
        ExpressionError: fewer than 2 rows/columns on an axis being
            clustered, an incompatible metric/method pairing, or a
            non-finite distance (e.g. from a constant row under the
            'correlation' metric, whose variance is zero).
    """
    if metric not in DISTANCE_METRICS:
        raise ExpressionError(f"Unknown metric '{metric}'. Choose one of: {', '.join(DISTANCE_METRICS)}")
    if method not in LINKAGE_METHODS:
        raise ExpressionError(f"Unknown linkage method '{method}'. Choose one of: {', '.join(LINKAGE_METHODS)}")

    row_linkage = None
    col_linkage = None
    ordered = df

    if cluster_rows:
        row_linkage, row_order = _linkage_and_order(df.to_numpy(), metric, method)
        ordered = ordered.iloc[row_order]

    if cluster_cols:
        col_linkage, col_order = _linkage_and_order(df.to_numpy().T, metric, method)
        ordered = ordered.iloc[:, col_order]

    return {"matrix": ordered, "row_linkage": row_linkage, "col_linkage": col_linkage}


def bundled_example_matrix() -> pd.DataFrame:
    """A small, fixed (non-random) example expression matrix — 12 genes x 6
    samples (3 control, 3 treated) — so the heatmap page has something to
    show before a user uploads their own data. Values are illustrative
    TPM-like numbers, not real experimental data.
    """
    genes = [
        "IL6", "TNF", "IL1B", "NFKB1", "STAT3",  # inflammatory, up in treated
        "COL1A1", "COL3A1", "FN1",                # fibrosis, up in treated
        "ACTB", "GAPDH", "B2M",                   # housekeeping, flat
        "MYC",                                     # proliferation, down in treated
    ]
    samples = ["Control_1", "Control_2", "Control_3", "Treated_1", "Treated_2", "Treated_3"]
    data = {
        "IL6":     [12, 14, 11, 88, 95, 79],
        "TNF":     [20, 18, 22, 61, 58, 65],
        "IL1B":    [15, 13, 17, 70, 66, 74],
        "NFKB1":   [30, 28, 33, 60, 57, 63],
        "STAT3":   [40, 38, 42, 75, 71, 78],
        "COL1A1":  [25, 22, 27, 110, 105, 118],
        "COL3A1":  [18, 20, 16, 92, 88, 96],
        "FN1":     [35, 33, 37, 130, 122, 128],
        "ACTB":    [500, 512, 495, 505, 498, 510],
        "GAPDH":   [610, 598, 605, 615, 602, 608],
        "B2M":     [220, 215, 225, 218, 222, 219],
        "MYC":     [95, 90, 98, 30, 28, 33],
    }
    rows = {g: data[g] for g in genes}
    return pd.DataFrame.from_dict(rows, orient="index", columns=samples)


def create_clustered_heatmap_figure(
    matrix: pd.DataFrame,
    colorscale: str = "RdBu_r",
    value_label: str = "Expression",
) -> go.Figure:
    """Build the Plotly heatmap for an (already clustered/reordered) matrix.

    Args:
        matrix: genes x samples DataFrame, rows/columns already in the
            order `cluster_matrix(...)` produced (or original order, if
            clustering was skipped for that axis).
        colorscale: a Plotly diverging colorscale name — diverging because
            z-scored expression is signed (down/up relative to the gene's
            own mean); a sequential scale would visually flatten that.
        value_label: colorbar title.

    Returns:
        A `plotly.graph_objects.Figure` ready for `st.plotly_chart`.
    """
    values = matrix.to_numpy()
    heatmap = go.Heatmap(
        z=values,
        x=list(matrix.columns),
        y=list(matrix.index),
        colorscale=colorscale,
        colorbar=dict(title=value_label),
        zmid=0 if values.min() < 0 else None,
        hovertemplate="Gene: %{y}<br>Sample: %{x}<br>Value: %{z:.3f}<extra></extra>",
    )
    fig = go.Figure(data=[heatmap])
    fig.update_layout(
        xaxis=dict(side="bottom", tickangle=45),
        yaxis=dict(autorange="reversed"),
        height=max(360, 24 * len(matrix.index) + 120),
        margin=dict(l=10, r=10, t=30, b=80),
    )
    return fig


def create_dendrogram_figure(
    matrix: pd.DataFrame,
    axis: str,
    metric: str = "euclidean",
    method: str = "average",
    orientation: str = "left",
) -> go.Figure:
    """Build an independent dendrogram figure for one axis, using the same
    metric/method as `cluster_matrix` so the grouping shown matches the
    heatmap's clustering — via Plotly's own `figure_factory.create_dendrogram`
    (which computes and draws in one step) rather than hand-drawn line
    traces, so leaf order and tick labels are guaranteed consistent.

    Args:
        matrix: genes x samples DataFrame (original orientation — this
            function does its own clustering, it does not take a
            pre-computed linkage).
        axis: "rows" (genes) or "cols" (samples).
        metric, method: as in `cluster_matrix`.
        orientation: "left"/"right"/"top"/"bottom", passed to Plotly.

    Returns:
        A `plotly.graph_objects.Figure`.

    Raises:
        ExpressionError: fewer than 2 items on the requested axis, or an
            unknown metric/method (see `cluster_matrix` for the same checks
            — this mirrors them so a bad parameter fails before Plotly's
            own less-specific error would).
    """
    if axis not in {"rows", "cols"}:
        raise ExpressionError(f"axis must be 'rows' or 'cols', got '{axis}'.")
    if metric not in DISTANCE_METRICS:
        raise ExpressionError(f"Unknown metric '{metric}'. Choose one of: {', '.join(DISTANCE_METRICS)}")
    if method not in LINKAGE_METHODS:
        raise ExpressionError(f"Unknown linkage method '{method}'. Choose one of: {', '.join(LINKAGE_METHODS)}")
    if method == "ward" and metric != "euclidean":
        raise ExpressionError("The 'ward' linkage method requires the 'euclidean' metric.")

    if axis == "rows":
        data = matrix.to_numpy()
        labels = list(matrix.index)
    else:
        data = matrix.to_numpy().T
        labels = list(matrix.columns)

    if data.shape[0] < 2:
        raise ExpressionError(f"Need at least 2 items to cluster (got {data.shape[0]}).")

    import plotly.figure_factory as ff

    fig = ff.create_dendrogram(
        data,
        orientation=orientation,
        labels=labels,
        distfun=lambda m: pdist(m, metric=metric),
        linkagefun=lambda d: linkage(d, method=method),
    )
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=60), height=260)
    return fig
