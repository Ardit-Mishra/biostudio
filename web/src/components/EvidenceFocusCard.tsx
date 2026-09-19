import { ExternalLink } from "lucide-react";

import {
  citationUrl,
  STAGE_LABEL,
  type AssayMapLane,
  type EvidenceRecord,
} from "@/lib/decision-twin";

export function EvidenceFocusCard({
  evidence,
  lanes,
  focusedEvidenceId,
}: {
  evidence: EvidenceRecord[];
  lanes: AssayMapLane[];
  focusedEvidenceId: string | null;
}) {
  const record = evidence.find((item) => item.id === focusedEvidenceId) ?? evidence[0];
  if (!record) return null;
  const stage = lanes.find((lane) => lane.evidence_ids.includes(record.id))?.stage;
  const href = citationUrl(record.citation);
  const context = record.assay_context;

  return (
    <aside className="evidence-focus" aria-labelledby="focus-heading">
      <p className="section-index">FOCUSED RECORD</p>
      <div className="focus-heading-row">
        <h2 id="focus-heading">{stage ? STAGE_LABEL[stage] : "Unclassified"} observation</h2>
        <span className={`direction-stamp direction-${record.outcome_direction}`}>{record.outcome_direction}</span>
      </div>
      <p className="focus-claim">{record.claim}</p>
      {record.excerpt && <p className="focus-excerpt">“{record.excerpt}”</p>}
      {context && (
        <dl className="focus-context">
          <div><dt>Target</dt><dd>{context.target_id}</dd></div>
          <div><dt>System</dt><dd>{context.biological_system}</dd></div>
          <div><dt>Readout</dt><dd>{context.readout}</dd></div>
          <div><dt>Unit</dt><dd>{context.unit}</dd></div>
        </dl>
      )}
      <div className="focus-provenance">
        <span>{record.citation.source.replace(/_/g, " ")} / {record.citation.source_id}</span>
        {href && <a href={href} target="_blank" rel="noopener noreferrer">Open record <ExternalLink className="size-3" aria-hidden="true" /></a>}
      </div>
    </aside>
  );
}
