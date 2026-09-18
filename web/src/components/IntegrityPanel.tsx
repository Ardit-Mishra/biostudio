import {
  RELATION_LABEL,
  type AssayComparison,
  type Compilation,
  type Relation,
} from "@/lib/decision-twin";

/**
 * Decision-integrity checks and the replay handle.
 *
 * Every pair of evidence records is compared, and the pair-wise result is what
 * produces the verdict — a single `conflicting` pair forces a hold no matter
 * how much support surrounds it. Listing the comparisons is how the verdict
 * stops being an opinion: the reader can see which two records disagreed and
 * on what grounds.
 *
 * `non_comparable` is shown with the same weight as the rest rather than hidden
 * as a null result. "These two measurements cannot be compared" is a finding,
 * and it is the one a tool that silently averages everything would destroy.
 */

const RELATION_TONE: Record<Relation, string> = {
  direct: "text-[var(--ds-supporting)]",
  supportive: "text-[var(--ds-supporting)]",
  inferred: "text-ink-muted",
  non_comparable: "text-ink-faint",
  conflicting: "text-[var(--ds-conflicting)]",
};

function ComparisonRow({ comparison }: { comparison: AssayComparison }) {
  const decisive = comparison.relation === "conflicting";
  return (
    <li
      className={`py-3 ${decisive ? "border-l-2 border-[var(--ds-conflicting)] pl-3 -ml-px" : ""}`}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <span className="min-w-0 font-mono text-[11.5px] text-ink-muted">
          <span className="text-ink">{comparison.left_evidence_id}</span>
          <span className="px-1.5 text-ink-faint" aria-hidden="true">
            &#215;
          </span>
          <span className="text-ink">{comparison.right_evidence_id}</span>
        </span>
        <span
          className={`font-mono text-[11px] font-medium ${RELATION_TONE[comparison.relation]}`}
        >
          {RELATION_LABEL[comparison.relation]}
        </span>
      </div>
      <p className="mt-1 text-[13px] leading-snug text-ink-muted">
        {comparison.reason}
      </p>
    </li>
  );
}

export function IntegrityPanel({ compilation }: { compilation: Compilation }) {
  const { comparisons } = compilation;
  const conflicts = comparisons.filter((c) => c.relation === "conflicting").length;
  const incomparable = comparisons.filter(
    (c) => c.relation === "non_comparable",
  ).length;

  // Decisive pairs first: a reader looking for "why hold?" should not have to
  // scan past agreeing pairs to find the one that forced it.
  const ordered = [...comparisons].sort((a, b) => {
    const rank = (r: Relation) => (r === "conflicting" ? 0 : r === "non_comparable" ? 1 : 2);
    return rank(a.relation) - rank(b.relation);
  });

  return (
    <section aria-labelledby="integrity-heading" className="space-y-5">
      <div>
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h2
            id="integrity-heading"
            className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-ink-muted"
          >
            Integrity checks
          </h2>
          <p className="font-mono text-[11px] text-ink-faint tabular">
            {comparisons.length} pair{comparisons.length === 1 ? "" : "s"}
          </p>
        </div>

        <div className="mt-3 grid grid-cols-3 gap-px overflow-hidden rounded-lg border border-line bg-line">
          {[
            { label: "Conflicting", value: conflicts, tone: conflicts > 0 ? "text-[var(--ds-conflicting)]" : "text-ink" },
            { label: "Not comparable", value: incomparable, tone: "text-ink" },
            { label: "Records", value: compilation.evidence_count, tone: "text-ink" },
          ].map((cell) => (
            <div key={cell.label} className="bg-surface px-3 py-3">
              <div className={`font-mono text-xl font-semibold tabular ${cell.tone}`}>
                {cell.value}
              </div>
              <div className="mt-0.5 font-mono text-[9.5px] uppercase tracking-[0.12em] text-ink-faint">
                {cell.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      <ul className="divide-y divide-line rounded-lg border border-line bg-surface px-4">
        {ordered.map((comparison) => (
          <ComparisonRow
            key={`${comparison.left_evidence_id}-${comparison.right_evidence_id}`}
            comparison={comparison}
          />
        ))}
      </ul>

      <div className="rounded-lg border border-line bg-sunk px-4 py-3">
        <p className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-ink-faint">
          Snapshot digest
        </p>
        {/* The replay handle. The same inputs always hash here, so a changed
            source produces a different digest and a visible study diff. */}
        <p className="mt-1 break-all font-mono text-[11.5px] text-ink tabular">
          {compilation.snapshot_digest}
        </p>
        <p className="mt-2 text-[12.5px] leading-relaxed text-ink-muted">
          Hashes the exact study inputs used for this decision. Re-running with
          unchanged sources reproduces it; a changed record produces a different
          digest, which is what makes the decision replayable.
        </p>
      </div>
    </section>
  );
}
