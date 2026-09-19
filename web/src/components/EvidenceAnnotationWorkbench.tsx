import { FormEvent, useCallback, useEffect, useState } from "react";
import { ArrowRight, BookOpenText, FlaskConical, Search } from "lucide-react";

import {
  createEvidenceFromAnnotation,
  excerptPreview,
  isAnnotationReady,
  type EvidenceAnnotationDraft,
} from "@/lib/annotation";
import {
  citationUrl,
  getChEMBLCompound,
  searchEuropePmc,
  type EvidenceRecord,
  type SourceArtifact,
} from "@/lib/decision-twin";

type SearchMode = "literature" | "compound";

const EMPTY_DRAFT: EvidenceAnnotationDraft = {
  id: "",
  claim: "",
  target_id: "",
  biological_system: "",
  readout: "",
  unit: "",
  genetic_context: "",
  outcome_direction: "unknown",
};

function draftFor(artifact: SourceArtifact): EvidenceAnnotationDraft {
  return {
    ...EMPTY_DRAFT,
    id: `ev-${artifact.citation.source}-${artifact.citation.source_id}`,
  };
}

function updateDraft(
  draft: EvidenceAnnotationDraft,
  field: keyof EvidenceAnnotationDraft,
  value: string,
): EvidenceAnnotationDraft {
  return { ...draft, [field]: value };
}

export function EvidenceAnnotationWorkbench({
  onEvidenceAdded,
  initialQuery = "",
  autoSearch = false,
  primary = false,
}: {
  onEvidenceAdded: (record: EvidenceRecord) => void;
  /** Seeded from whatever the researcher typed on the landing page. */
  initialQuery?: string;
  /** Run that query on mount, so arriving from the hero lands on results. */
  autoSearch?: boolean;
  /** This is the whole screen, not a panel at the bottom of a finished study. */
  primary?: boolean;
}) {
  const [query, setQuery] = useState(initialQuery || "EGFR osimertinib resistance");
  const [mode, setMode] = useState<SearchMode>("literature");
  const [records, setRecords] = useState<SourceArtifact[]>([]);
  const [selected, setSelected] = useState<SourceArtifact | null>(null);
  const [draft, setDraft] = useState<EvidenceAnnotationDraft>(EMPTY_DRAFT);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSearch = useCallback(
    async (rawQuery: string, searchMode: SearchMode) => {
      const normalized = rawQuery.trim();
      if (!normalized) return;

      setPending(true);
      setError(null);
      try {
        setRecords(
          searchMode === "literature"
            ? await searchEuropePmc(normalized, 5)
            : await getChEMBLCompound(normalized),
        );
      } catch (cause) {
        setRecords([]);
        setError(cause instanceof Error ? cause.message : "Source lookup failed.");
      } finally {
        setPending(false);
      }
    },
    [],
  );

  // Arriving from the landing search should land on results, not on an empty
  // box the researcher has to submit a second time.
  useEffect(() => {
    if (autoSearch && initialQuery.trim()) void runSearch(initialQuery, "literature");
    // Intentionally mount-only: re-running on every keystroke would hammer the
    // source and fight the researcher's own edits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch(query, mode);
  }

  function selectRecord(record: SourceArtifact) {
    setSelected(record);
    setDraft(draftFor(record));
    setError(null);
  }

  function addToStudy() {
    if (!selected || !isAnnotationReady(draft)) return;
    onEvidenceAdded(createEvidenceFromAnnotation(selected, draft));
    setSelected(null);
    setDraft(EMPTY_DRAFT);
  }

  return (
    <section className="annotation-workbench" aria-labelledby="source-workbench-heading">
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <div>
          <p className="section-index">{primary ? "01 / SEARCH THE PUBLIC RECORD" : "04 / OPERATOR ANNOTATION"}</p>
          <h2 id="source-workbench-heading" className="workbench-title">
            {primary ? "Start from a record, not a hunch." : "Bring a source in carefully."}
          </h2>
          <p className="workbench-intro">
            {primary
              ? "Search Europe PMC or resolve a ChEMBL compound, inspect what comes back, then supply the biological context yourself. The study compiles as soon as you add the first record."
              : "Retrieve a public record, inspect it, then supply the biological context yourself. Retrieval never promotes itself to evidence."}
          </p>

          <div className="source-mode" role="group" aria-label="Public source to search">
            <button type="button" aria-pressed={mode === "literature"} onClick={() => { setMode("literature"); setQuery("EGFR osimertinib resistance"); setRecords([]); }} className={mode === "literature" ? "is-active" : ""}>
              <BookOpenText className="size-3.5" aria-hidden="true" /> Literature
            </button>
            <button type="button" aria-pressed={mode === "compound"} onClick={() => { setMode("compound"); setQuery("CHEMBL3353410"); setRecords([]); }} className={mode === "compound" ? "is-active" : ""}>
              <FlaskConical className="size-3.5" aria-hidden="true" /> Compound
            </button>
          </div>

          <form className="mt-5 flex gap-2" onSubmit={search}>
            <label className="sr-only" htmlFor="source-query">{mode === "literature" ? "Search Europe PMC" : "Look up a ChEMBL compound"}</label>
            <input
              id="source-query"
              name="source-query"
              autoComplete="off"
              spellCheck={false}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={mode === "literature" ? "Target, disease, compound, or assay…" : "ChEMBL compound ID, e.g. CHEMBL3353410"}
              className="min-w-0 flex-1 rounded-md border border-line bg-surface px-3 py-2.5 text-[14px] text-ink shadow-sm outline-none placeholder:text-ink-faint focus:border-[var(--ds-accent)] focus:ring-2 focus:ring-[var(--ds-accent-soft)]"
            />
            <button
              type="submit"
              disabled={pending || !query.trim()}
              className="inline-flex shrink-0 items-center gap-2 rounded-md bg-[var(--ds-accent)] px-3.5 py-2.5 text-[13px] font-medium text-[var(--ds-on-accent)] transition-colors hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ds-accent)]"
            >
              <Search className="size-3.5" aria-hidden="true" />
              {pending ? "Searching…" : mode === "literature" ? "Search" : "Resolve"}
            </button>
          </form>

          {error && <p role="alert" className="mt-3 text-[13px] text-[var(--ds-conflicting)]">{error}</p>}

          {records.length > 0 && (
            <ul className="mt-5 divide-y divide-line border-y border-line">
              {records.map((record) => {
                const active = selected?.citation.source_id === record.citation.source_id;
                const preview = excerptPreview(record.excerpt);
                return (
                  <li key={`${record.citation.source}-${record.citation.source_id}`}>
                    <button
                      type="button"
                      onClick={() => selectRecord(record)}
                      className={`w-full py-4 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ds-accent)] ${
                        active ? "bg-accent-soft px-3" : "hover:bg-surface-sunk"
                      }`}
                    >
                      <span className="block text-[14px] font-medium leading-snug text-ink">{record.title}</span>
                      {preview && (
                        <span className="mt-1.5 block text-[12.5px] leading-relaxed text-ink-muted">{preview}</span>
                      )}
                      <span className="mt-2 block font-mono text-[10.5px] uppercase tracking-[0.1em] text-ink-faint">
                        {record.citation.source.replace(/_/g, " ")} · {record.citation.source_id}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="min-w-0 border-t border-line pt-7 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
          <h2 className="text-xl font-semibold tracking-tight text-ink">Annotate before use</h2>
          {!selected ? (
            <p className="mt-3 max-w-prose text-[14px] leading-relaxed text-ink-muted">
              Select a public record to create an evidence draft. The draft stays in
              this browser until you add it to the current study.
            </p>
          ) : (
            <div className="mt-4">
              <div className="border-b border-line pb-4">
                <p className="text-[13.5px] font-medium leading-relaxed text-ink">{selected.title}</p>
                {citationUrl(selected.citation) && (
                  <a
                    href={citationUrl(selected.citation) ?? undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 inline-block font-mono text-[11.5px] text-[var(--ds-accent-ink)] underline-offset-2 hover:underline"
                  >
                    View source record ↗
                  </a>
                )}
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <label className="sm:col-span-2">
                  <span className="text-[12px] font-medium text-ink">What does this record support or challenge?</span>
                  <textarea
                    name="claim"
                    autoComplete="off"
                    value={draft.claim}
                    onChange={(event) => setDraft(updateDraft(draft, "claim", event.target.value))}
                    rows={3}
                    placeholder="Write a bounded claim in your own words…"
                    className="mt-1.5 w-full resize-y rounded-md border border-line bg-surface px-3 py-2.5 text-[13.5px] leading-relaxed text-ink outline-none placeholder:text-ink-faint focus:border-[var(--ds-accent)] focus:ring-2 focus:ring-[var(--ds-accent-soft)]"
                  />
                </label>
                <Field label="Target ID" name="target-id" value={draft.target_id} onChange={(value) => setDraft(updateDraft(draft, "target_id", value))} placeholder="e.g. ENSG00000146648" />
                <Field label="Biological system" name="biological-system" value={draft.biological_system} onChange={(value) => setDraft(updateDraft(draft, "biological_system", value))} placeholder="e.g. human or cell_line" />
                <Field label="Readout" name="readout" value={draft.readout} onChange={(value) => setDraft(updateDraft(draft, "readout", value))} placeholder="e.g. progression_free_survival" />
                <Field label="Unit" name="unit" value={draft.unit} onChange={(value) => setDraft(updateDraft(draft, "unit", value))} placeholder="e.g. months or nM" />
                <Field label="Genetic context (optional)" name="genetic-context" value={draft.genetic_context ?? ""} onChange={(value) => setDraft(updateDraft(draft, "genetic_context", value))} placeholder="e.g. EGFR T790M" />
                <label>
                  <span className="text-[12px] font-medium text-ink">Observed direction</span>
                  <select
                    name="outcome-direction"
                    value={draft.outcome_direction}
                    onChange={(event) => setDraft(updateDraft(draft, "outcome_direction", event.target.value))}
                    className="mt-1.5 h-[42px] w-full rounded-md border border-line bg-surface px-3 text-[13.5px] text-ink outline-none focus:border-[var(--ds-accent)] focus:ring-2 focus:ring-[var(--ds-accent-soft)]"
                  >
                    <option value="unknown">Undirected</option>
                    <option value="supports">Supports</option>
                    <option value="contradicts">Contradicts</option>
                  </select>
                </label>
              </div>

              <button
                type="button"
                disabled={!isAnnotationReady(draft)}
                onClick={addToStudy}
                className="mt-6 inline-flex items-center gap-2 rounded-md border border-[var(--ds-accent)] px-3.5 py-2.5 text-[13px] font-medium text-[var(--ds-accent-ink)] transition-colors hover:bg-accent-soft disabled:cursor-not-allowed disabled:border-line disabled:text-ink-faint focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ds-accent)]"
              >
                Add annotated evidence to this study
                <ArrowRight className="size-3.5" aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Field({
  label,
  name,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  name: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label>
      <span className="text-[12px] font-medium text-ink">{label}</span>
      <input
        name={name}
        autoComplete="off"
        spellCheck={false}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-1.5 h-[42px] w-full rounded-md border border-line bg-surface px-3 text-[13.5px] text-ink outline-none placeholder:text-ink-faint focus:border-[var(--ds-accent)] focus:ring-2 focus:ring-[var(--ds-accent-soft)]"
      />
    </label>
  );
}
