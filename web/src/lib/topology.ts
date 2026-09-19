import {
  TRANSLATION_STAGES,
  type AssayMapLane,
  type AssayStage,
  type EvidenceRecord,
  type LaneStatus,
  type SourceName,
} from "@/lib/decision-twin";

export type TopologyConnectorKind = "source" | "measurement" | "decision" | "missing";

export interface TopologySource {
  id: SourceName;
  label: string;
  recordCount: number;
}

export interface TopologyRecord {
  id: string;
  source: SourceName;
  stage: AssayStage | "unclassified";
  direction: EvidenceRecord["outcome_direction"];
  titleLines: string[];
  citationLabel: string;
}

export interface TopologyStage {
  id: AssayStage;
  status: LaneStatus;
  evidenceCount: number;
}

export interface TopologyConnector {
  kind: TopologyConnectorKind;
  from: string;
  to: string;
  status?: LaneStatus;
}

export interface EvidenceTopology {
  sources: TopologySource[];
  records: TopologyRecord[];
  stages: TopologyStage[];
  connectors: TopologyConnector[];
}

const SOURCE_LABEL: Record<SourceName, string> = {
  chembl: "ChEMBL",
  europe_pmc: "Europe PMC",
  open_targets: "Open Targets",
};

function citationTitleLines(text: string): string[] {
  const normalized = text.replace(/\s+/g, " ").trim();
  const words = normalized.split(" ");
  const lines: string[] = [];
  let line = "";

  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (candidate.length <= 29 || !line) {
      line = candidate;
      continue;
    }
    lines.push(line);
    line = word;
    if (lines.length === 2) break;
  }
  if (line && lines.length < 2) lines.push(line);
  const consumed = lines.join(" ").length;
  if (normalized.length > consumed && lines.length > 0) {
    lines[lines.length - 1] = `${lines[lines.length - 1].replace(/[.,;:]$/, "")}…`;
  }
  return lines;
}

/**
 * Make every visible node traceable to a retained EvidenceRecord or explicit
 * assay-map gap. This stays pure so presentation cannot invent a connector.
 */
export function buildEvidenceTopology(
  evidence: EvidenceRecord[],
  lanes: AssayMapLane[],
): EvidenceTopology {
  const stageByEvidenceId = new Map<string, AssayStage>();
  const laneByStage = new Map<AssayStage, AssayMapLane>();
  lanes.forEach((lane) => {
    laneByStage.set(lane.stage, lane);
    lane.evidence_ids.forEach((id) => stageByEvidenceId.set(id, lane.stage));
  });

  const sources = [...new Set(evidence.map((record) => record.citation.source))]
    .sort()
    .map((source) => ({
      id: source,
      label: SOURCE_LABEL[source],
      recordCount: evidence.filter((record) => record.citation.source === source).length,
    }));

  const records = evidence.map((record) => ({
    id: record.id,
    source: record.citation.source,
    stage: stageByEvidenceId.get(record.id) ?? "unclassified",
    direction: record.outcome_direction,
    titleLines: citationTitleLines(record.source_title ?? record.excerpt ?? record.claim),
    citationLabel: `${SOURCE_LABEL[record.citation.source]} · ${record.citation.source_id}`,
  }));

  const stages = TRANSLATION_STAGES.map((stage) => {
    const lane = laneByStage.get(stage);
    return {
      id: stage,
      status: lane?.status ?? "missing",
      evidenceCount: lane?.evidence_ids.length ?? 0,
    };
  });

  const connectors: TopologyConnector[] = [];
  records.forEach((record) => {
    connectors.push({ kind: "source", from: record.source, to: record.id });
    if (record.stage !== "unclassified") {
      connectors.push({
        kind: "measurement",
        from: record.id,
        to: record.stage,
        status: stages.find((stage) => stage.id === record.stage)?.status,
      });
    }
  });
  stages.forEach((stage) => {
    connectors.push({
      kind: stage.evidenceCount === 0 ? "missing" : "decision",
      from: stage.id,
      to: "decision",
      status: stage.status,
    });
  });

  return { sources, records, stages, connectors };
}
