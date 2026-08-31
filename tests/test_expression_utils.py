"""
Tests for features/expression_utils.py (expression matrix parsing,
normalization, hierarchical clustering, Plotly heatmap/dendrogram
rendering).
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from features.expression_utils import (  # noqa: E402
    ExpressionError,
    bundled_example_matrix,
    cluster_matrix,
    create_clustered_heatmap_figure,
    create_dendrogram_figure,
    normalize_matrix,
    parse_expression_matrix,
)


class TestBundledExampleMatrix:
    def test_shape_and_type(self):
        df = bundled_example_matrix()
        assert df.shape[0] >= 2
        assert df.shape[1] >= 2
        assert all(pd.api.types.is_numeric_dtype(dt) for dt in df.dtypes)

    def test_no_missing_values(self):
        df = bundled_example_matrix()
        assert not df.isna().any().any()


class TestParseExpressionMatrix:
    def test_parses_csv(self):
        df = bundled_example_matrix()
        data = df.to_csv().encode("utf-8")
        parsed = parse_expression_matrix(data, "matrix.csv")
        assert parsed.shape == df.shape
        assert list(parsed.columns) == list(df.columns)

    def test_parses_tsv(self):
        df = bundled_example_matrix()
        data = df.to_csv(sep="\t").encode("utf-8")
        parsed = parse_expression_matrix(data, "matrix.tsv")
        assert parsed.shape == df.shape

    def test_empty_file_raises(self):
        with pytest.raises(ExpressionError, match="empty"):
            parse_expression_matrix(b"   ", "empty.csv")

    def test_non_numeric_value_raises_with_location(self):
        data = b"gene,s1,s2\nGENE_A,1.0,not_a_number\nGENE_B,2.0,3.0\n"
        with pytest.raises(ExpressionError, match="GENE_A"):
            parse_expression_matrix(data, "bad.csv")

    def test_single_gene_raises(self):
        data = b"gene,s1,s2\nGENE_A,1.0,2.0\n"
        with pytest.raises(ExpressionError, match="at least 2 genes"):
            parse_expression_matrix(data, "one_gene.csv")

    def test_single_sample_raises(self):
        data = b"gene,s1\nGENE_A,1.0\nGENE_B,2.0\n"
        with pytest.raises(ExpressionError, match="at least 2 samples"):
            parse_expression_matrix(data, "one_sample.csv")

    def test_undecodable_bytes_raise(self):
        with pytest.raises(ExpressionError, match="decode"):
            parse_expression_matrix(b"\xff\xfe\x00\x01", "bad.csv")


class TestNormalizeMatrix:
    def test_none_is_passthrough(self):
        df = bundled_example_matrix()
        out, dropped = normalize_matrix(df, "none")
        pd.testing.assert_frame_equal(out, df)
        assert dropped == []

    def test_log2_is_monotonic_and_nonnegative_input_safe(self):
        df = bundled_example_matrix()
        out, dropped = normalize_matrix(df, "log2")
        assert dropped == []
        # log2(x+1) is monotonic, so rank order within a row is preserved.
        for gene in df.index:
            assert list(np.argsort(df.loc[gene])) == list(np.argsort(out.loc[gene]))

    def test_log2_rejects_negative_values(self):
        df = pd.DataFrame({"s1": [-1.0, 2.0], "s2": [3.0, 4.0]}, index=["g1", "g2"])
        with pytest.raises(ExpressionError, match="negative"):
            normalize_matrix(df, "log2")

    def test_zscore_row_mean_near_zero_and_std_near_one(self):
        df = bundled_example_matrix()
        out, dropped = normalize_matrix(df, "zscore")
        assert dropped == []
        for gene in out.index:
            row = out.loc[gene]
            assert row.mean() == pytest.approx(0.0, abs=1e-8)
            assert row.std(ddof=0) == pytest.approx(1.0, abs=1e-6)

    def test_zscore_drops_zero_variance_genes_without_fabricating_values(self):
        df = pd.DataFrame(
            {"s1": [5.0, 1.0], "s2": [5.0, 2.0], "s3": [5.0, 9.0]},
            index=["flat_gene", "varying_gene"],
        )
        out, dropped = normalize_matrix(df, "zscore")
        assert dropped == ["flat_gene"]
        assert "flat_gene" not in out.index
        assert "varying_gene" in out.index

    def test_all_zero_variance_raises(self):
        df = pd.DataFrame({"s1": [5.0, 5.0], "s2": [5.0, 5.0]}, index=["g1", "g2"])
        with pytest.raises(ExpressionError, match="nothing left to show"):
            normalize_matrix(df, "zscore")

    def test_unknown_method_raises(self):
        df = bundled_example_matrix()
        with pytest.raises(ExpressionError, match="Unknown normalization"):
            normalize_matrix(df, "bogus")


class TestClusterMatrix:
    def test_reorders_rows_and_columns(self):
        df = bundled_example_matrix()
        result = cluster_matrix(df, cluster_rows=True, cluster_cols=True)
        assert set(result["matrix"].index) == set(df.index)
        assert set(result["matrix"].columns) == set(df.columns)
        assert result["row_linkage"] is not None
        assert result["col_linkage"] is not None

    def test_skips_clustering_when_disabled(self):
        df = bundled_example_matrix()
        result = cluster_matrix(df, cluster_rows=False, cluster_cols=False)
        assert list(result["matrix"].index) == list(df.index)
        assert list(result["matrix"].columns) == list(df.columns)
        assert result["row_linkage"] is None
        assert result["col_linkage"] is None

    def test_similar_genes_end_up_adjacent(self):
        # Two genes with near-identical profiles, one very different.
        df = pd.DataFrame(
            {
                "s1": [1.0, 1.1, 9.0],
                "s2": [2.0, 2.1, 8.5],
                "s3": [3.0, 2.9, 9.5],
            },
            index=["close_a", "close_b", "far"],
        )
        result = cluster_matrix(df, cluster_rows=True, cluster_cols=False)
        order = list(result["matrix"].index)
        assert abs(order.index("close_a") - order.index("close_b")) == 1

    def test_too_few_rows_raises(self):
        df = pd.DataFrame({"s1": [1.0], "s2": [2.0]}, index=["only_gene"])
        with pytest.raises(ExpressionError, match="at least 2 items"):
            cluster_matrix(df, cluster_rows=True, cluster_cols=False)

    def test_ward_requires_euclidean(self):
        df = bundled_example_matrix()
        with pytest.raises(ExpressionError, match="ward"):
            cluster_matrix(df, metric="correlation", method="ward")

    def test_unknown_metric_raises(self):
        df = bundled_example_matrix()
        with pytest.raises(ExpressionError, match="Unknown metric"):
            cluster_matrix(df, metric="bogus")

    def test_unknown_method_raises(self):
        df = bundled_example_matrix()
        with pytest.raises(ExpressionError, match="Unknown linkage method"):
            cluster_matrix(df, method="bogus")


class TestFigures:
    def test_heatmap_figure_has_one_trace_with_full_data(self):
        df = bundled_example_matrix()
        fig = create_clustered_heatmap_figure(df)
        assert len(fig.data) == 1
        z = fig.data[0].z
        assert np.array(z).shape == df.shape

    def test_dendrogram_figure_row_axis(self):
        df = bundled_example_matrix()
        fig = create_dendrogram_figure(df, axis="rows")
        assert len(fig.data) > 0

    def test_dendrogram_figure_col_axis(self):
        df = bundled_example_matrix()
        fig = create_dendrogram_figure(df, axis="cols")
        assert len(fig.data) > 0

    def test_dendrogram_invalid_axis_raises(self):
        df = bundled_example_matrix()
        with pytest.raises(ExpressionError, match="axis must be"):
            create_dendrogram_figure(df, axis="diagonal")

    def test_dendrogram_too_few_items_raises(self):
        df = pd.DataFrame({"only_sample": [1.0, 2.0]}, index=["g1", "g2"])
        with pytest.raises(ExpressionError, match="at least 2 items"):
            create_dendrogram_figure(df, axis="cols")
