import { Atom, BookOpenText, Boxes, Database, Dna, FlaskConical, Landmark } from "lucide-react";

const LIVE_SOURCES = [
  { name: "Europe PMC", detail: "Citable literature records", icon: BookOpenText },
  { name: "Open Targets", detail: "Target annotation", icon: Dna },
];

const WIRED_SOURCES = [
  { name: "ChEMBL", detail: "Bounded compound route; health checked per request", icon: FlaskConical },
];

const PLANNED_SOURCES = [
  { name: "BindingDB", detail: "Affinity cross-check", icon: Atom },
  { name: "PubChem", detail: "Compound & assay metadata", icon: Database },
  { name: "UniProt", detail: "Protein identity & domains", icon: Boxes },
  { name: "RCSB PDB / AlphaFold", detail: "Structure context", icon: Landmark },
];

type AtlasSource = { name: string; detail: string; icon: typeof BookOpenText };

function SourceRow({ source, state }: { source: AtlasSource; state: "live" | "wired" | "planned" }) {
  const Icon = source.icon;
  return (
    <li className={`source-row source-row-${state}`}>
      <Icon className="size-4" aria-hidden="true" />
      <div><strong>{source.name}</strong><span>{source.detail}</span></div>
      <em>{state === "live" ? "CONNECTED" : state === "wired" ? "ROUTE" : "GAP"}</em>
    </li>
  );
}

export function SourceAtlas() {
  return (
    <aside className="source-atlas" aria-labelledby="source-atlas-heading">
      <div>
        <p className="section-index">03 / SOURCE ATLAS</p>
        <h2 id="source-atlas-heading">The map names its blind spots.</h2>
        <p className="atlas-intro">A source has to be connected, bounded, and retained before it can change this study.</p>
      </div>
      <div className="atlas-group">
        <p>Connected now</p>
        <ul>{LIVE_SOURCES.map((source) => <SourceRow key={source.name} source={source} state="live" />)}</ul>
      </div>
      <div className="atlas-group">
        <p>Implemented route</p>
        <ul>{WIRED_SOURCES.map((source) => <SourceRow key={source.name} source={source} state="wired" />)}</ul>
      </div>
      <div className="atlas-group">
        <p>Explicit next lanes</p>
        <ul>{PLANNED_SOURCES.map((source) => <SourceRow key={source.name} source={source} state="planned" />)}</ul>
      </div>
    </aside>
  );
}
