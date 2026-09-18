import { FormEvent, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  CloudSun,
  Database,
  FlaskConical,
  LoaderCircle,
  Moon,
  Search,
  ShieldCheck,
  Sun,
  Trash2,
  X,
} from "lucide-react";

type SourceName = "europe_pmc" | "open_targets";
type SourceArtifact = {
  citation: { source: SourceName; source_id: string; retrieved_at: string };
  title: string;
  excerpt?: string | null;
  structured_record: Record<string, unknown>;
};
type EvidenceRecord = {
  id: string;
  claim: string;
  citation: SourceArtifact["citation"];
  excerpt?: string | null;
  structured_record?: Record<string, unknown> | null;
  assay_context: {
    target_id: string;
    biological_system: string;
    readout: string;
    unit: string;
  };
  outcome_direction: "supports" | "contradicts" | "unknown";
};
type Lane = {
  stage: "biochemical" | "cellular" | "in_vivo" | "human" | "unclassified";
  status: "supporting" | "contradicting" | "conflicting" | "inconclusive" | "missing" | "unclassified";
  evidence_ids: string[];
  gaps: string[];
};
type Compilation = {
  status: "advance" | "hold" | "insufficient_evidence";
  reasons: string[];
  snapshot_digest: string;
  evidence_count: number;
  assay_translation_map: { lanes: Lane[] };
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const initialLanes: Lane[] = [
  { stage: "biochemical", status: "missing", evidence_ids: [], gaps: ["No biochemical evidence was supplied."] },
  { stage: "cellular", status: "missing", evidence_ids: [], gaps: ["No cellular evidence was supplied."] },
  { stage: "in_vivo", status: "missing", evidence_ids: [], gaps: ["No in vivo evidence was supplied."] },
  { stage: "human", status: "missing", evidence_ids: [], gaps: ["No human evidence was supplied."] },
  { stage: "unclassified", status: "missing", evidence_ids: [], gaps: [] },
];

function App() {
  const [dark, setDark] = useState(false);
  const [query, setQuery] = useState("EGFR AND NSCLC");
  const [targetId, setTargetId] = useState("ENSG00000146648");
  const [artifacts, setArtifacts] = useState<SourceArtifact[]>([]);
  const [selected, setSelected] = useState<SourceArtifact | null>(null);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [compilation, setCompilation] = useState<Compilation | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isCompiling, setIsCompiling] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const lanes = compilation?.assay_translation_map.lanes ?? initialLanes;
  const metrics = useMemo(() => ({
    sources: new Set(evidence.map((record) => record.citation.source)).size,
    evidence: evidence.length,
    gaps: lanes.filter((lane) => lane.status === "missing").length,
  }), [evidence, lanes]);

  async function findSources() {
    setIsSearching(true);
    setMessage(null);
    setCompilation(null);
    const requests: Promise<Response>[] = [];
    if (query.trim()) {
      requests.push(fetch(`${API_BASE_URL}/v2/sources/europe-pmc/search?query=${encodeURIComponent(query.trim())}&page_size=6`));
    }
    if (targetId.trim()) {
      requests.push(fetch(`${API_BASE_URL}/v2/sources/open-targets/targets/${encodeURIComponent(targetId.trim())}`));
    }
    try {
      const responses = await Promise.all(requests);
      const payloads = await Promise.all(responses.map(async (response) => {
        if (!response.ok) throw new Error("A public source could not be reached.");
        return response.json() as Promise<{ records: SourceArtifact[] }>;
      }));
      setArtifacts(payloads.flatMap((payload) => payload.records));
      setSelected(null);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "A public source could not be reached.");
    } finally {
      setIsSearching(false);
    }
  }

  function addEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    const claim = String(form.get("claim") ?? "").trim();
    const stage = String(form.get("stage") ?? "cellular");
    const readout = String(form.get("readout") ?? "").trim();
    const unit = String(form.get("unit") ?? "").trim();
    const direction = String(form.get("direction") ?? "unknown") as EvidenceRecord["outcome_direction"];
    if (!claim || !readout || !unit) {
      setMessage("Claim, readout, and unit are required to add study evidence.");
      return;
    }
    const record: EvidenceRecord = {
      id: `ev-${String(evidence.length + 1).padStart(3, "0")}`,
      claim,
      citation: selected.citation,
      excerpt: selected.excerpt,
      structured_record: selected.structured_record,
      assay_context: {
        target_id: targetId.trim() || "unresolved-target",
        biological_system: stage,
        readout,
        unit,
      },
      outcome_direction: direction,
    };
    setEvidence((current) => [...current, record]);
    setSelected(null);
    setCompilation(null);
    setMessage(null);
    event.currentTarget.reset();
  }

  async function compile() {
    if (!evidence.length) return;
    setIsCompiling(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_BASE_URL}/v2/decision-twins/compile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ study_id: "operator-draft", evidence, model_assessments: [] }),
      });
      if (!response.ok) throw new Error("The Decision Twin could not compile this evidence draft.");
      setCompilation(await response.json() as Compilation);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The Decision Twin could not compile this evidence draft.");
    } finally {
      setIsCompiling(false);
    }
  }

  return (
    <main className={dark ? "app dark" : "app"}>
      <header className="topbar">
        <a className="brand" href="/" aria-label="BioStudio home">
          <span className="brand-mark"><FlaskConical size={20} strokeWidth={1.8} /></span>
          <span>BioStudio</span>
        </a>
        <div className="topbar-actions">
          <span className="research-status"><span /> Research workspace</span>
          <button className="icon-button" onClick={() => setDark((value) => !value)} aria-label="Toggle color theme">
            {dark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      <section className="workspace">
        <aside className="rail" aria-label="Workspace navigation">
          <button className="rail-item active"><ClipboardCheck size={18} /><span>Decision Twin</span></button>
          <button className="rail-item" disabled><Database size={18} /><span>Evidence library</span></button>
          <button className="rail-item" disabled><CloudSun size={18} /><span>Model runs</span></button>
        </aside>

        <div className="content">
          <section className="heading-row">
            <div>
              <p className="kicker">Target-to-candidate triage</p>
              <h1>Decision Twin</h1>
              <p className="lede">Trace what supports a decision, what contradicts it, and where the evidence has not arrived yet.</p>
            </div>
            <div className="metrics" aria-label="Study metrics">
              <Metric label="Evidence" value={metrics.evidence} />
              <Metric label="Sources" value={metrics.sources} />
              <Metric label="Open gaps" value={metrics.gaps} />
            </div>
          </section>

          {message && <div className="notice error"><AlertTriangle size={17} />{message}<button onClick={() => setMessage(null)} aria-label="Dismiss message"><X size={16} /></button></div>}

          <section className="map-panel" aria-labelledby="map-title">
            <div className="panel-heading">
              <div><p className="kicker">Evidence translation</p><h2 id="map-title">Assay Translation Map</h2></div>
              <OutcomePill status={compilation?.status} />
            </div>
            <div className="translation-map">
              {lanes.map((lane, index) => <LaneCard lane={lane} index={index} key={lane.stage} />)}
            </div>
            {compilation && (
              <div className="decision-readout">
                <div><ShieldCheck size={18} /><span>{compilation.reasons.join(" ")}</span></div>
                <code title={compilation.snapshot_digest}>snapshot {compilation.snapshot_digest.slice(0, 12)}</code>
              </div>
            )}
          </section>

          <section className="work-grid">
            <div className="work-panel">
              <div className="panel-heading compact"><div><p className="kicker">Public records</p><h2>Source finder</h2></div><BookOpen size={19} /></div>
              <div className="source-fields">
                <label>Literature query<input value={query} onChange={(event) => setQuery(event.target.value)} /></label>
                <label>Ensembl target ID<input value={targetId} onChange={(event) => setTargetId(event.target.value)} /></label>
              </div>
              <button className="primary-button" onClick={findSources} disabled={isSearching || (!query.trim() && !targetId.trim())}>
                {isSearching ? <LoaderCircle className="spin" size={17} /> : <Search size={17} />} Find records
              </button>
              <div className="artifact-list">
                {artifacts.map((artifact) => (
                  <button className={selected?.citation.source_id === artifact.citation.source_id ? "artifact selected" : "artifact"} key={`${artifact.citation.source}:${artifact.citation.source_id}`} onClick={() => setSelected(artifact)}>
                    <span className="artifact-source">{artifact.citation.source.replace("_", " ")}</span>
                    <strong>{artifact.title}</strong>
                    <small>{artifact.citation.source_id}</small>
                    <ChevronRight size={16} />
                  </button>
                ))}
                {!artifacts.length && <p className="empty-copy">No records loaded in this workspace.</p>}
              </div>
            </div>

            <div className="work-panel">
              <div className="panel-heading compact"><div><p className="kicker">Operator annotation</p><h2>Study evidence</h2></div><FlaskConical size={19} /></div>
              {selected ? (
                <form onSubmit={addEvidence} className="evidence-form">
                  <div className="selected-record"><Check size={16} /><span>{selected.citation.source_id}</span><button type="button" onClick={() => setSelected(null)} aria-label="Clear selected source"><X size={15} /></button></div>
                  <label>Claim<textarea name="claim" required placeholder="State only what the source supports." /></label>
                  <div className="form-split">
                    <label>Assay layer<select name="stage" defaultValue="cellular"><option value="biochemical">Biochemical</option><option value="cellular">Cellular</option><option value="in_vivo">In vivo</option><option value="human">Human</option></select></label>
                    <label>Direction<select name="direction" defaultValue="unknown"><option value="supports">Supports</option><option value="contradicts">Contradicts</option><option value="unknown">Unknown</option></select></label>
                  </div>
                  <div className="form-split"><label>Readout<input name="readout" required placeholder="e.g. viability" /></label><label>Unit<input name="unit" required placeholder="e.g. nM" /></label></div>
                  <button className="secondary-button" type="submit">Add evidence <ArrowRight size={16} /></button>
                </form>
              ) : (
                <div className="annotation-empty"><CircleHelp size={20} /><p>Select a public record before adding a study annotation.</p></div>
              )}
            </div>
          </section>

          <section className="draft-panel">
            <div className="panel-heading compact"><div><p className="kicker">Current draft</p><h2>{evidence.length ? `${evidence.length} evidence record${evidence.length === 1 ? "" : "s"}` : "No evidence records"}</h2></div>
              {evidence.length > 0 && <button className="text-button destructive" onClick={() => { setEvidence([]); setCompilation(null); }}> <Trash2 size={15} /> Clear draft</button>}
            </div>
            {evidence.length > 0 && <div className="draft-list">{evidence.map((record) => <div className="draft-row" key={record.id}><code>{record.id}</code><span>{record.claim}</span><span className={`direction ${record.outcome_direction}`}>{record.outcome_direction}</span></div>)}</div>}
            <button className="compile-button" onClick={compile} disabled={!evidence.length || isCompiling}>
              {isCompiling ? <LoaderCircle className="spin" size={17} /> : <ClipboardCheck size={17} />} Compile Decision Twin
            </button>
          </section>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="metric"><strong>{value}</strong><span>{label}</span></div>;
}

function OutcomePill({ status }: { status?: Compilation["status"] }) {
  if (!status) return <span className="outcome-pill neutral">Awaiting evidence</span>;
  return <span className={`outcome-pill ${status}`}>{status.replace("_", " ")}</span>;
}

function LaneCard({ lane, index }: { lane: Lane; index: number }) {
  return <article className={`lane ${lane.status}`}>
    <div className="lane-top"><span>{String(index + 1).padStart(2, "0")}</span><span className="lane-status">{lane.status}</span></div>
    <h3>{lane.stage.replace("_", " ")}</h3>
    {lane.evidence_ids.length ? <div className="lane-records">{lane.evidence_ids.map((id) => <code key={id}>{id}</code>)}</div> : <p className="lane-empty">No record</p>}
    {lane.gaps.map((gap) => <p className="lane-gap" key={gap}>{gap}</p>)}
  </article>;
}

export default App;
