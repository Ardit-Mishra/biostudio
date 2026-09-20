import { FormEvent, useEffect, useState } from "react";
import { listStudyTypes, type StudyType } from "@/lib/decision-twin";
import { ArrowDownRight, ArrowUpRight, BookOpenText, Dna, FlaskConical, GitCompareArrows, Network, Search } from "lucide-react";

/** Queries that return real records, offered so the box is never a blank stare. */
const STARTERS = [
  "KRAS G12C pancreatic",
  "SOD1 ALS antisense",
  "PCSK9 LDL lowering",
];

export function Landing({
  onSearch,
  onOpenExample,
}: {
  onSearch: (query: string, studyType: string) => void;
  onOpenExample: () => void;
}) {
  const [query, setQuery] = useState("");
  // No default. Choosing a design is choosing a level of evidence, and a
  // default would make that choice on the reader's behalf without telling them.
  const [studyType, setStudyType] = useState("");
  const [studyTypes, setStudyTypes] = useState<StudyType[]>([]);

  useEffect(() => {
    void listStudyTypes().then(setStudyTypes).catch(() => setStudyTypes([]));
  }, []);

  const chosen = studyTypes.find((t) => t.key === studyType);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed && studyType) onSearch(trimmed, studyType);
  }

  return (
    <main className="landing-main">
      <section className="landing-hero" aria-labelledby="landing-title">
        <div className="landing-copy">
          <p className="section-index">PUBLIC RESEARCH WORKSPACE</p>
          <h1 id="landing-title">Drug discovery without the evidence blind spot.</h1>
          <p>
            BioStudio turns public records into an inspectable research map: what
            was measured, where it was measured, what agrees, and exactly where
            the translation path breaks.
          </p>
          <form className="landing-search" onSubmit={submit}>
            <label className="sr-only" htmlFor="landing-query">
              Target, disease, compound, or assay to search in the public record
            </label>
            <div className="landing-search-row">
              <Search className="size-4" aria-hidden="true" />
              <input
                id="landing-query"
                name="landing-query"
                autoComplete="off"
                spellCheck={false}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Target, disease, compound, or assay&hellip;"
              />
              <button type="submit" disabled={!query.trim() || !studyType}>
                Search public records
              </button>
            </div>
            <div className="landing-design">
              <label htmlFor="landing-design">Study design</label>
              <select
                id="landing-design"
                name="landing-design"
                required
                value={studyType}
                onChange={(event) => setStudyType(event.target.value)}
              >
                <option value="" disabled>
                  Choose a level of evidence&hellip;
                </option>
                {studyTypes.map((type) => (
                  <option key={type.key} value={type.key}>{type.label}</option>
                ))}
              </select>
            </div>
            {chosen ? (
              <p className="landing-caveat">
                <strong>{chosen.label}</strong> cannot support: {chosen.cannot_support}
              </p>
            ) : (
              <p className="landing-caveat dim">
                A case report and a randomized trial are not interchangeable, so the
                design is chosen before the search rather than sorted out after it.
              </p>
            )}

            <div className="landing-starters">
              <span>Try</span>
              {STARTERS.map((starter) => (
                <button
                  key={starter}
                  type="button"
                  disabled={!studyType}
                  onClick={() => studyType && onSearch(starter, studyType)}
                >
                  {starter}
                </button>
              ))}
            </div>
          </form>

          <div className="landing-actions">
            <button type="button" onClick={onOpenExample} className="landing-secondary">
              Or open a worked example <ArrowUpRight className="size-3.5" aria-hidden="true" />
            </button>
            <a href="#how-it-holds" className="landing-secondary">How the evidence stays honest <ArrowDownRight className="size-3.5" aria-hidden="true" /></a>
          </div>
          <p className="landing-boundary">For education and research. Not a clinical recommendation or a substitute for experimental validation.</p>
        </div>

        <div className="landing-map" aria-hidden="true">
          <svg viewBox="0 0 900 570">
            <defs>
              <linearGradient id="landing-stroke" x1="0" x2="1">
                <stop stopColor="var(--ds-accent)" stopOpacity=".18" />
                <stop offset=".45" stopColor="var(--ds-accent)" stopOpacity=".72" />
                <stop offset="1" stopColor="var(--ds-contradicting)" stopOpacity=".55" />
              </linearGradient>
            </defs>
            <g className="landing-map-guides">
              <path d="M 35 125 H 865 M 35 285 H 865 M 35 445 H 865" />
              <path d="M 205 40 V 530 M 455 40 V 530 M 700 40 V 530" />
            </g>
            <g className="landing-map-links">
              <path d="M 146 130 C 240 130, 300 184, 385 228" />
              <path d="M 146 278 C 250 278, 292 260, 385 252" />
              <path d="M 146 426 C 255 426, 316 326, 385 276" />
              <path d="M 490 250 C 570 250, 600 170, 693 142" />
              <path d="M 490 250 C 570 250, 604 274, 693 286" />
              <path className="landing-map-broken" d="M 490 250 C 575 250, 607 392, 693 425" />
              <path d="M 790 145 C 830 170, 836 220, 837 270" />
              <path d="M 790 287 C 824 287, 830 286, 837 283" />
              <path className="landing-map-broken" d="M 790 426 C 820 390, 828 330, 837 295" />
            </g>
            <g className="landing-map-pulses">
              <path d="M 146 130 C 240 130, 300 184, 385 228" />
              <path d="M 146 278 C 250 278, 292 260, 385 252" />
              <path d="M 490 250 C 570 250, 600 170, 693 142" />
              <path d="M 490 250 C 570 250, 604 274, 693 286" />
            </g>
            <g className="landing-source-node" transform="translate(110 130)"><circle r="35"/><text y="5" textAnchor="middle">LIT</text><text y="61" textAnchor="middle">Literature</text></g>
            <g className="landing-source-node" transform="translate(110 278)"><circle r="35"/><text y="5" textAnchor="middle">TGT</text><text y="61" textAnchor="middle">Target</text></g>
            <g className="landing-source-node" transform="translate(110 426)"><circle r="35"/><text y="5" textAnchor="middle">CMP</text><text y="61" textAnchor="middle">Compound</text></g>
            <g className="landing-core-node" transform="translate(440 250)"><circle r="61"/><circle r="46"/><text y="-5" textAnchor="middle">EVIDENCE</text><text y="15" textAnchor="middle">MAP</text></g>
            <g className="landing-stage-node live" transform="translate(742 142)"><rect x="-49" y="-25" width="98" height="50"/><text y="-2" textAnchor="middle">Biochemical</text><text y="14" textAnchor="middle">measured</text></g>
            <g className="landing-stage-node live" transform="translate(742 286)"><rect x="-49" y="-25" width="98" height="50"/><text y="-2" textAnchor="middle">Cellular</text><text y="14" textAnchor="middle">measured</text></g>
            <g className="landing-stage-node gap" transform="translate(742 426)"><rect x="-49" y="-25" width="98" height="50"/><text y="-2" textAnchor="middle">In vivo</text><text y="14" textAnchor="middle">gap visible</text></g>
            <g className="landing-decision-node" transform="translate(850 282)"><circle r="47"/><text y="-3" textAnchor="middle">NEXT</text><text y="13" textAnchor="middle">STEP</text></g>
          </svg>
        </div>
      </section>

      <section id="how-it-holds" className="landing-principles" aria-labelledby="principles-title">
        <div><p className="section-index">THE DISTINCTION</p><h2 id="principles-title">A decision is only as useful as the path behind it.</h2></div>
        <div className="principle-list">
          <article><BookOpenText className="size-5" aria-hidden="true" /><h3>Retained sources</h3><p>Every displayed observation begins as a bounded public-source artifact, never a generated summary.</p></article>
          <article><GitCompareArrows className="size-5" aria-hidden="true" /><h3>Assay translation</h3><p>Biochemical, cellular, animal, and human evidence are separate biological contexts, not numbers to average.</p></article>
          <article><Network className="size-5" aria-hidden="true" /><h3>Visible absence</h3><p>When a layer is missing, the line breaks. The interface does not paint an inference across an empty space.</p></article>
        </div>
      </section>

      <section className="landing-sources" aria-label="BioStudio source lanes">
        <div className="source-rail-heading"><p className="section-index">SOURCE LANE CONTRACTS</p><p>Only a successfully retained record can enter a study.</p></div>
        <div className="source-rail">
          <span><BookOpenText className="size-4" aria-hidden="true" /> Europe PMC <em>literature</em></span>
          <span><Dna className="size-4" aria-hidden="true" /> Open Targets <em>target context</em></span>
          <span><BookOpenText className="size-4" aria-hidden="true" /> OpenAlex <em>general scholarly</em></span>
          <span className="source-rail-wired"><FlaskConical className="size-4" aria-hidden="true" /> ChEMBL <em>bounded compound route</em></span>
        </div>
      </section>

      <section className="landing-study-link" aria-label="Open the public study exemplar">
        <div><p className="section-index">LIVE PUBLIC EXAMPLE</p><h2>EGFR / osimertinib in non-small-cell lung cancer</h2><p>Inspect a study where human evidence and acquired-resistance observations force a transparent hold instead of a false yes.</p></div>
        <button type="button" onClick={onOpenExample} aria-label="Open the EGFR worked example"><ArrowUpRight className="size-6" aria-hidden="true" /></button>
      </section>
    </main>
  );
}
