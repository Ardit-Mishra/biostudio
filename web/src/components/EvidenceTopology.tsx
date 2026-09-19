import { useMemo } from "react";

import {
  STAGE_LABEL,
  STAGE_MEANING,
  TRANSLATION_STAGES,
  type AssayMapLane,
  type AssayStage,
  type EvidenceRecord,
  type LaneStatus,
} from "@/lib/decision-twin";
import { buildEvidenceTopology } from "@/lib/topology";

type Point = { x: number; y: number };

const STAGE_POINTS: Record<AssayStage, Point> = {
  biochemical: { x: 735, y: 82 },
  cellular: { x: 735, y: 166 },
  in_vivo: { x: 735, y: 250 },
  human: { x: 735, y: 334 },
  unclassified: { x: 0, y: 0 },
};

const STATUS_CLASS: Record<LaneStatus, string> = {
  supporting: "topology-supporting",
  contradicting: "topology-contradicting",
  conflicting: "topology-conflicting",
  inconclusive: "topology-inconclusive",
  missing: "topology-missing",
  unclassified: "topology-missing",
};

const DIRECTION_CLASS: Record<EvidenceRecord["outcome_direction"], string> = {
  supports: "topology-supporting",
  contradicts: "topology-contradicting",
  unknown: "topology-inconclusive",
};

function path(from: Point, to: Point): string {
  const middle = (from.x + to.x) / 2;
  return `M ${from.x} ${from.y} C ${middle} ${from.y}, ${middle} ${to.y}, ${to.x} ${to.y}`;
}

export function EvidenceTopology({
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
  const topology = useMemo(() => buildEvidenceTopology(evidence, lanes), [evidence, lanes]);
  const sourcePoints = new Map(
    topology.sources.map((source, index) => [source.id, { x: 92, y: 120 + index * 156 }]),
  );
  const recordPoints = new Map(
    topology.records.map((record, index) => [record.id, { x: 382, y: 72 + index * 110 }]),
  );
  const decisionPoint = { x: 1015, y: 208 };

  return (
    <section className="evidence-map" aria-labelledby="topology-heading">
      <div className="map-heading">
        <div>
          <p className="section-index">01 / LIVE STUDY MAP</p>
          <h2 id="topology-heading">Evidence does not travel on faith.</h2>
        </div>
        <p className="map-key">
          Solid paths are retained observations. Dotted paths mark an unfilled
          translation step, not weak evidence.
        </p>
      </div>

      <div className="topology-canvas topology-canvas-wide" role="group" aria-label="Evidence topology">
        <svg viewBox="0 0 1100 420" role="img" aria-labelledby="topology-title topology-description">
          <title id="topology-title">Source records, assay layers, and research decision topology</title>
          <desc id="topology-description">
            Retained source records connect to their measured biological layer.
            Filled paths reach the decision compiler; missing layers remain visibly broken.
          </desc>

          <g className="topology-guides" aria-hidden="true">
            {[82, 166, 250, 334].map((y) => <line key={y} x1="650" x2="890" y1={y} y2={y} />)}
          </g>

          {topology.records.map((record) => {
            const source = sourcePoints.get(record.source)!;
            const point = recordPoints.get(record.id)!;
            return <path key={`source-${record.id}`} className="topology-source-edge" d={path(source, point)} />;
          })}

          {topology.records.map((record) => {
            const from = recordPoints.get(record.id)!;
            if (record.stage === "unclassified") return null;
            return (
              <path
                key={`measurement-${record.id}`}
                className={`topology-edge ${DIRECTION_CLASS[record.direction]}`}
                d={path({ x: from.x + 130, y: from.y }, { x: STAGE_POINTS[record.stage].x - 74, y: STAGE_POINTS[record.stage].y })}
              />
            );
          })}

          {topology.stages.map((stage) => {
            const from = STAGE_POINTS[stage.id];
            return (
              <path
                key={`decision-${stage.id}`}
                className={`topology-edge ${STATUS_CLASS[stage.status]}`}
                d={path({ x: from.x + 77, y: from.y }, { x: decisionPoint.x - 67, y: decisionPoint.y })}
              />
            );
          })}

          <g className="topology-flow" aria-hidden="true">
            {topology.records.map((record) => {
              const source = sourcePoints.get(record.source)!;
              const point = recordPoints.get(record.id)!;
              return <path key={`flow-source-${record.id}`} className="topology-flow-source" d={path(source, point)} />;
            })}
            {topology.records.map((record) => {
              const from = recordPoints.get(record.id)!;
              if (record.stage === "unclassified") return null;
              return (
                <path
                  key={`flow-measurement-${record.id}`}
                  className={`topology-flow-path ${DIRECTION_CLASS[record.direction]}`}
                  d={path({ x: from.x + 130, y: from.y }, { x: STAGE_POINTS[record.stage].x - 74, y: STAGE_POINTS[record.stage].y })}
                />
              );
            })}
            {topology.stages.filter((stage) => stage.evidenceCount > 0).map((stage) => {
              const from = STAGE_POINTS[stage.id];
              return (
                <path
                  key={`flow-decision-${stage.id}`}
                  className={`topology-flow-path ${STATUS_CLASS[stage.status]}`}
                  d={path({ x: from.x + 77, y: from.y }, { x: decisionPoint.x - 67, y: decisionPoint.y })}
                />
              );
            })}
          </g>

          {topology.sources.map((source) => {
            const point = sourcePoints.get(source.id)!;
            return (
              <g key={source.id} transform={`translate(${point.x} ${point.y})`}>
                <circle r="34" className="topology-source-node" />
                <text className="topology-source-initial" textAnchor="middle" dy="5">{source.label.slice(0, 1)}</text>
                <text className="topology-label" textAnchor="middle" y="54">{source.label}</text>
                <text className="topology-count" textAnchor="middle" y="70">{source.recordCount} retained</text>
              </g>
            );
          })}

          {topology.records.map((record) => {
            const point = recordPoints.get(record.id)!;
            const focused = focusedEvidenceId === record.id;
            return (
              <g
                key={record.id}
                transform={`translate(${point.x} ${point.y})`}
                className={`topology-record ${focused ? "is-focused" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={`Focus evidence: ${record.citationLabel}`}
                onClick={() => onFocusEvidence(record.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onFocusEvidence(record.id);
                  }
                }}
              >
                <rect x="-130" y="-36" width="260" height="72" rx="5" className={`topology-record-box ${DIRECTION_CLASS[record.direction]}`} />
                <text x="-112" y="-12" className="topology-record-label">
                  {record.titleLines.map((line, index) => <tspan key={line} x="-112" dy={index === 0 ? 0 : 14}>{line}</tspan>)}
                </text>
                <text x="-112" y="22" className="topology-record-meta">{record.citationLabel}</text>
              </g>
            );
          })}

          {topology.stages.map((stage) => {
            const point = STAGE_POINTS[stage.id];
            const empty = stage.evidenceCount === 0;
            return (
              <g key={stage.id} transform={`translate(${point.x} ${point.y})`}>
                <rect x="-74" y="-30" width="148" height="60" rx="5" className={`topology-stage-box ${STATUS_CLASS[stage.status]} ${empty ? "is-empty" : ""}`} />
                <text textAnchor="middle" y="-6" className="topology-stage-label">{STAGE_LABEL[stage.id]}</text>
                <text textAnchor="middle" y="14" className="topology-stage-meta">
                  {empty ? "NO RETAINED RECORD" : `${stage.evidenceCount} RECORD${stage.evidenceCount === 1 ? "" : "S"}`}
                </text>
              </g>
            );
          })}

          <g transform={`translate(${decisionPoint.x} ${decisionPoint.y})`}>
            <circle r="63" className="topology-decision-ring" />
            <circle r="46" className="topology-decision-core" />
            <text textAnchor="middle" y="-5" className="topology-decision-label">DECISION</text>
            <text textAnchor="middle" y="15" className="topology-decision-meta">COMPILER</text>
          </g>
        </svg>
      </div>

      <MobileTopology
        evidence={evidence}
        topology={topology}
        focusedEvidenceId={focusedEvidenceId}
        onFocusEvidence={onFocusEvidence}
      />

      <div className="map-stage-legend">
        {topology.stages.map((stage) => (
          <div key={stage.id} className="stage-legend-item">
            <span className={`stage-dot ${STATUS_CLASS[stage.status]}`} />
            <div>
              <strong>{STAGE_LABEL[stage.id]}</strong>
              <span>{STAGE_MEANING[stage.id]}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function MobileTopology({
  evidence,
  topology,
  focusedEvidenceId,
  onFocusEvidence,
}: {
  evidence: EvidenceRecord[];
  topology: ReturnType<typeof buildEvidenceTopology>;
  focusedEvidenceId: string | null;
  onFocusEvidence: (id: string) => void;
}) {
  const source = topology.sources[0];
  const recordY = (index: number) => 132 + index * 78;
  const decision = { x: 175, y: 555 };
  const stageX = [48, 133, 218, 303];

  return (
    <div className="topology-canvas topology-canvas-narrow" role="group" aria-label="Mobile evidence topology">
      <svg viewBox="0 0 350 620" role="img" aria-label="Evidence topology arranged for a narrow screen">
        {source && (
          <g transform="translate(175 46)">
            <circle r="25" className="topology-source-node" />
            <text className="topology-source-initial" textAnchor="middle" dy="5">{source.label.slice(0, 1)}</text>
            <text className="topology-label" textAnchor="middle" y="42">{source.label} / {source.recordCount} retained</text>
          </g>
        )}
        {topology.records.map((record, index) => {
          const y = recordY(index);
          const stageIndex = TRANSLATION_STAGES.indexOf(record.stage as AssayStage);
          const stage = stageIndex >= 0 ? { x: stageX[stageIndex], y: 400 } : null;
          const focused = focusedEvidenceId === record.id;
          return (
            <g key={record.id}>
              <path className="topology-source-edge" d={path({ x: 175, y: 71 }, { x: 175, y: y - 23 })} />
              {stage && <path className={`topology-edge ${DIRECTION_CLASS[record.direction]}`} d={path({ x: 175, y: y + 23 }, { x: stage.x, y: stage.y - 23 })} />}
              <g
                transform={`translate(175 ${y})`}
                className={`topology-record ${focused ? "is-focused" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={`Focus evidence: ${record.citationLabel}`}
                onClick={() => onFocusEvidence(record.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onFocusEvidence(record.id);
                  }
                }}
              >
                <rect x="-128" y="-23" width="256" height="46" rx="4" className={`topology-record-box ${DIRECTION_CLASS[record.direction]}`} />
                <text x="-114" y="-3" className="topology-record-label">{record.titleLines[0]}</text>
                <text x="-114" y="13" className="topology-record-meta">{record.citationLabel}</text>
              </g>
            </g>
          );
        })}
        {topology.stages.map((stage, index) => {
          const x = stageX[index];
          const empty = stage.evidenceCount === 0;
          return (
            <g key={stage.id} transform={`translate(${x} 400)`}>
              <path className={`topology-edge ${STATUS_CLASS[stage.status]}`} d={path({ x, y: 423 }, { x: decision.x, y: decision.y - 38 })} />
              <rect x="-36" y="-23" width="72" height="46" rx="4" className={`topology-stage-box ${STATUS_CLASS[stage.status]} ${empty ? "is-empty" : ""}`} />
              <text textAnchor="middle" y="-3" className="topology-stage-label">{STAGE_LABEL[stage.id]}</text>
              <text textAnchor="middle" y="13" className="topology-stage-meta">{empty ? "GAP" : `${stage.evidenceCount} REC.`}</text>
            </g>
          );
        })}
        <g transform={`translate(${decision.x} ${decision.y})`}>
          <circle r="38" className="topology-decision-ring" />
          <circle r="29" className="topology-decision-core" />
          <text textAnchor="middle" y="-3" className="topology-decision-label">DECISION</text>
          <text textAnchor="middle" y="12" className="topology-decision-meta">COMPILER</text>
        </g>
      </svg>
    </div>
  );
}
