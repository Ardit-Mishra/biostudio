import {
  citationUrl,
  STAGE_LABEL,
  type AssayMapLane,
  type AssayStage,
  type EvidenceRecord,
  type OutcomeDirection,
} from "@/lib/decision-twin";

/**
 * The citation inspector.
 *
 * Every claim on this page has to be walkable back to a resolved public record,
 * so each row carries the assay context that decided whether it could be
 * compared at all — target, system, readout, unit, genetic context. Those five
 * fields are not decoration: `compare_evidence` in decision_twin/normalization.py
 * reads exactly them, and two records that differ on any of them are not the
 * same measurement. Showing them is showing the reason.
 */

const DIRECTION: Record<OutcomeDirection, { label: string; tone: string }> = {
  supports: { label: "Supports", tone: "text-[var(--ds-supporting)]" },
  contradicts: { label: "Contradicts", tone: "text-[var(--ds-contradicting)]" },
  unknown: { label: "Undirected", tone: "text-ink-faint" },
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-ink-faint">
        {label}
      </dt>
      <dd className="mt-0.5 truncate font-mono text-[12px] text-ink" title={value}>
        {value}
      </dd>
    </div>
  );
}

function stageOf(id: string, lanes: AssayMapLane[]): AssayStage | null {
  return lanes.find((lane) => lane.evidence_ids.includes(id))?.stage ?? null;
}

export function EvidenceInspector({
  evidence,
  lanes,
}: {
  evidence: EvidenceRecord[];
  lanes: AssayMapLane[];
}) {
  return (
    <section aria-labelledby="evidence-heading">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2
          id="evidence-heading"
          className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-ink-muted"
        >
          Evidence
        </h2>
        <p className="font-mono text-[11px] text-ink-faint tabular">
          {evidence.length} record{evidence.length === 1 ? "" : "s"}
        </p>
      </div>

      <ul className="mt-4 space-y-3">
        {evidence.map((record) => {
          const direction = DIRECTION[record.outcome_direction];
          const href = citationUrl(record.citation);
          const context = record.assay_context;
          const stage = stageOf(record.id, lanes);

          return (
            <li
              key={record.id}
              className="rounded-lg border border-line bg-surface p-4"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                <span className={`font-mono text-[11px] font-medium ${direction.tone}`}>
                  {direction.label}
                </span>
                {stage && (
                  <span className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
                    {STAGE_LABEL[stage]}
                  </span>
                )}
              </div>

              <p className="mt-2 text-[14.5px] leading-relaxed text-ink">
                {record.claim}
              </p>

              {record.excerpt && (
                <blockquote className="mt-3 border-l-2 border-line-strong pl-3 text-[13px] leading-relaxed text-ink-muted">
                  {record.excerpt}
                </blockquote>
              )}

              {context && (
                <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 border-t border-line pt-3 sm:grid-cols-3">
                  <Field label="Target" value={context.target_id} />
                  <Field label="System" value={context.biological_system} />
                  <Field label="Readout" value={context.readout} />
                  <Field label="Unit" value={context.unit} />
                  {context.genetic_context && (
                    <Field label="Genetic context" value={context.genetic_context} />
                  )}
                  {context.conditions &&
                    Object.entries(context.conditions).map(([key, value]) => (
                      <Field key={key} label={key.replace(/_/g, " ")} value={value} />
                    ))}
                </dl>
              )}

              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-line pt-3">
                <span className="font-mono text-[10.5px] uppercase tracking-[0.12em] text-ink-faint">
                  {record.citation.source.replace(/_/g, " ")}
                </span>
                {href ? (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-[12px] text-[var(--ds-accent-ink)] underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ds-accent)]"
                  >
                    {record.citation.source_id} &#8599;
                  </a>
                ) : (
                  <span className="font-mono text-[12px] text-ink">
                    {record.citation.source_id}
                  </span>
                )}
                <span className="font-mono text-[10.5px] text-ink-faint tabular">
                  retrieved {record.citation.retrieved_at.slice(0, 10)}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
