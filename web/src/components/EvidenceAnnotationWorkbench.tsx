import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, BookOpenText, FlaskConical, Search } from "lucide-react";

import {
  createEvidenceFromAnnotation,
  excerptPreview,
  isAnnotationReady,
  missingFromAnnotation,
  type EvidenceAnnotationDraft,
} from "@/lib/annotation";
import {
  citationUrl,
  getChEMBLCompound,
  listStudyTypes,
  searchEuropePmc,
  searchOpenAlex,
  LITERATURE_SOURCES,
  type LiteratureSource,
  type StudyType,
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
  direction_rationale: "",
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
  initialStudyType = "",
  autoSearch = false,
  primary = false,
}: {
  onEvidenceAdded: (record: EvidenceRecord) => void;
  /** Seeded from whatever the researcher typed on the landing page. */
  initialQuery?: string;
  /** The level of evidence they chose there. No default: choosing is required. */
  initialStudyType?: string;
  /** Run that query on mount, so arriving from the hero lands on results. */
  autoSearch?: boolean;
  /** This is the whole screen, not a panel at the bottom of a finished study. */
  primary?: boolean;
}) {
  const [query, setQuery] = useState(initialQuery || "EGFR osimertinib resistance");
  const [mode, setMode] = useState<SearchMode>("literature");
  const [literatureSource, setLiteratureSource] = useState<LiteratureSource>("europe_pmc");
  const [studyType, setStudyType] = useState(initialStudyType);
  const [studyTypes, setStudyTypes] = useState<StudyType[]>([]);
  const [records, setRecords] = useState<SourceArtifact[]>([]);
  const [selected, setSelected] = useState<SourceArtifact | null>(null);
  const [draft, setDraft] = useState<EvidenceAnnotationDraft>(EMPTY_DRAFT);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Same ordering hazard as compile: a slow earlier search must not overwrite
  // the results of a later one.
  const searchSeq = useRef(0);

  const runSearch = useCallback(
    async (rawQuery: string, searchMode: SearchMode) => {
      const normalized = rawQuery.trim();
      if (!normalized) return;

      const seq = ++searchSeq.current;
      setPending(true);
      setError(null);
      try {
        const found =
          searchMode !== "literature"
            ? await getChEMBLCompound(normalized)
            : literatureSource === "openalex"
              ? await searchOpenAlex(normalized, 5)
              : await searchEuropePmc(normalized, 5, studyType);
        if (seq !== searchSeq.current) return;
        setRecords(found);
      } catch (cause) {
        if (seq !== searchSeq.current) return;
        setRecords([]);
        setError(cause instanceof Error ? cause.message : "Source lookup failed.");
      } finally {
        if (seq === searchSeq.current) setPending(false);
      }
    },
    // Both are read inside, so both must be dependencies. Leaving this empty
    // pinned the callback to the first render and sent study_type=any forever,
    // however the reader set the picker -- a filter that silently does nothing
    // is worse than no filter, because the results look narrowed.
    [literatureSource, studyType],
  );

  useEffect(() => {
    // Served by the API so the caveats cannot drift from the filter that
    // applies them. If it fails the picker stays empty, which blocks the search
    // rather than quietly falling back to an unranked mix.
    void listStudyTypes().then(setStudyTypes).catch(() => setStudyTypes([]));
  }, []);

  // Arriving from the landing search should land on results, not on an empty
  // box the researcher has to submit a second time.
  useEffect(() => {
    if (autoSearch && initialQuery.trim() && initialStudyType) {
      void runSearch(initialQuery, "literature");
    }
    // Intentionally mount-only: re-running on every keystroke would hammer the
    // source and fight the researcher's own edits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // The design is a property of the study, not of the source that happens to
  // be selected: it decides what the evidence is allowed to support once it is
  // annotated. Gating it on europe_pmc meant switching lane to OpenAlex walked
  // straight past a choice the product treats as mandatory.
  const needsDesign = mode === "literature" && !studyType;
  // Only Europe PMC can actually narrow a query by publication type. Saying so
  // is the same rule as everywhere else here: a filter that silently does
  // nothing is worse than no filter, because the results look narrowed.
  const designFiltersSource = literatureSource === "europe_pmc";

  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (needsDesign) return;
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

          {mode === "literature" && (
            <div className="source-refine">
              <div className="refine-row" role="group" aria-label="Literature database">
                <span className="refine-label">Database</span>
                {LITERATURE_SOURCES.map((source) => (
                  <button
                    key={source.key}
                    type="button"
                    aria-pressed={literatureSource === source.key}
                    onClick={() => { setLiteratureSource(source.key); setRecords([]); }}
                    className={literatureSource === source.key ? "is-active" : ""}
                    title={source.blurb}
                  >
                    {source.label}
                  </button>
                ))}
              </div>
              <p className="refine-why">
                {LITERATURE_SOURCES.find((x) => x.key === literatureSource)?.blurb}{" "}
                The lanes are searched separately, never merged: a record found in
                only one of them is a fact about coverage.
              </p>

              {studyTypes.length > 0 && (
                <>
                  <div className="refine-row">
                    <label className="refine-label" htmlFor="study-type">
                      Study design
                    </label>
                    <select
                      id="study-type"
                      name="study-type"
                      value={studyType}
                      onChange={(event) => { setStudyType(event.target.value); setRecords([]); }}
                      className="refine-select"
                      required
                    >
                      <option value="" disabled>
                        Choose a level of evidence&hellip;
                      </option>
                      {studyTypes.map((type) => (
                        <option key={type.key} value={type.key}>{type.label}</option>
                      ))}
                    </select>
                  </div>
                  {!designFiltersSource && (
                    <p className="refine-why">
                      This lane cannot filter by publication type. The design is
                      recorded and still bounds what the evidence can support &mdash;
                      it just does not narrow the search.
                    </p>
                  )}
                  {/* Choosing a design is choosing a level of evidence, so the
                      limit of that level is shown at the moment of choosing. */}
                  {(() => {
                    const chosen = studyTypes.find((t) => t.key === studyType);
                    if (!chosen) return null;
                    return (
                      <dl className="refine-caveat">
                        <div>
                          <dt>Can support</dt>
                          <dd>{chosen.supports}</dd>
                        </div>
                        <div className="cannot">
                          <dt>Cannot support</dt>
                          <dd>{chosen.cannot_support}</dd>
                        </div>
                      </dl>
                    );
                  })()}
                </>
              )}
            </div>
          )}

          {needsDesign && (
            <p className="refine-required" role="status">
              Choose a study design before searching. A case report and a
              randomized trial are not interchangeable, so the level of evidence
              is chosen deliberately rather than defaulted into.
            </p>
          )}

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

                {draft.outcome_direction !== "unknown" && (
                  <label className="sm:col-span-2">
                    <span className="text-[12px] font-medium text-ink">
                      Why does it {draft.outcome_direction === "supports" ? "support" : "contradict"}?
                    </span>
                    <textarea
                      name="direction-rationale"
                      autoComplete="off"
                      value={draft.direction_rationale}
                      onChange={(event) =>
                        setDraft(updateDraft(draft, "direction_rationale", event.target.value))
                      }
                      rows={2}
                      placeholder="Name what in this record points that way — the measured outcome, the population, the comparison…"
                      className="mt-1.5 w-full resize-y rounded-md border border-line bg-surface px-3 py-2.5 text-[13.5px] leading-relaxed text-ink outline-none placeholder:text-ink-faint focus:border-[var(--ds-accent)] focus:ring-2 focus:ring-[var(--ds-accent-soft)]"
                    />
                    <span className="mt-1.5 block text-[11.5px] leading-snug text-ink-muted">
                      Required. Opposing directions on comparable records are what
                      force a hold, so the direction must not be the least
                      justified field in the study.
                    </span>
                  </label>
                )}
              </div>

              {!isAnnotationReady(draft) && (
                <p className="mt-5 text-[12.5px] leading-relaxed text-ink-muted">
                  Still needed: {missingFromAnnotation(draft).join(", ")}.
                </p>
              )}

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
