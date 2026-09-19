import {
  STAGE_LABEL,
  TRANSLATION_STAGES,
  type AssayMapLane,
  type AssayStage,
  type EvidenceRecord,
} from "@/lib/decision-twin";

const Y_BY_DIRECTION = { supports: 42, unknown: 105, contradicts: 168 } as const;
const X_BY_STAGE: Record<AssayStage, number> = {
  biochemical: 82,
  cellular: 248,
  in_vivo: 414,
  human: 580,
  unclassified: 0,
};

export function EvidenceSignalPlot({
  evidence,
  lanes,
  focusedEvidenceId,
  onFocusEvidence,
}: {
  evidence: EvidenceRecord[];
  lanes: AssayMapLane[];
  focusedEvidenceId: string | null;
  onFocusEvidence: (id: string) => void;
}) {
  const stageByEvidenceId = new Map<string, AssayStage>();
  lanes.forEach((lane) => lane.evidence_ids.forEach((id) => stageByEvidenceId.set(id, lane.stage)));
  const records = evidence.filter((record) => stageByEvidenceId.has(record.id));

  return (
    <section className="signal-plot" aria-labelledby="signal-heading">
      <div className="signal-heading">
        <div>
          <p className="section-index">02 / EVIDENCE SIGNAL</p>
          <h2 id="signal-heading">Where the observations land</h2>
        </div>
        <p>Each mark is a retained record. Position reports assay context; color reports its stated direction.</p>
      </div>

      <svg viewBox="0 0 660 220" role="img" aria-label="Evidence direction by assay layer">
        <line x1="54" x2="622" y1="105" y2="105" className="signal-baseline" />
        {[
          [42, "Supports"],
          [105, "Undirected"],
          [168, "Contradicts"],
        ].map(([y, label]) => (
          <g key={String(label)}>
            <line x1="54" x2="622" y1={Number(y)} y2={Number(y)} className="signal-rule" />
            <text x="0" y={Number(y) + 4} className="signal-axis-label">{label}</text>
          </g>
        ))}
        {TRANSLATION_STAGES.map((stage) => {
          const x = X_BY_STAGE[stage];
          return (
            <g key={stage}>
              <line x1={x} x2={x} y1="28" y2="186" className="signal-guide" />
              <text x={x} y="208" textAnchor="middle" className="signal-stage-label">{STAGE_LABEL[stage]}</text>
            </g>
          );
        })}
        {records.map((record, index) => {
          const stage = stageByEvidenceId.get(record.id)!;
          const x = X_BY_STAGE[stage] + ((index % 3) - 1) * 16;
          const y = Y_BY_DIRECTION[record.outcome_direction];
          const focused = focusedEvidenceId === record.id;
          return (
            <g
              key={record.id}
              role="button"
              tabIndex={0}
              aria-label={`Focus plotted evidence ${record.id}`}
              onClick={() => onFocusEvidence(record.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onFocusEvidence(record.id);
                }
              }}
            >
              <circle cx={x} cy={y} r={focused ? 10 : 7} className={`signal-mark signal-${record.outcome_direction}`} />
              {focused && <circle cx={x} cy={y} r="15" className="signal-focus-ring" />}
            </g>
          );
        })}
      </svg>
      <p className="signal-footnote">
        Empty assay columns are meaningful: no retained observation was supplied for that layer.
      </p>
    </section>
  );
}
