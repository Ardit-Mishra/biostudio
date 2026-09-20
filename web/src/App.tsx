import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FlaskConical, Moon, Orbit, RotateCw, Sun } from "lucide-react";

import { DecisionRecordExport } from "@/components/DecisionRecordExport";
import { EvidenceAnnotationWorkbench } from "@/components/EvidenceAnnotationWorkbench";
import { EvidenceFocusCard } from "@/components/EvidenceFocusCard";
import { EvidenceSignalPlot } from "@/components/EvidenceSignalPlot";
import { EvidenceTopology } from "@/components/EvidenceTopology";
import { IntegrityPanel } from "@/components/IntegrityPanel";
import { Landing } from "@/components/Landing";
import { SourceAtlas } from "@/components/SourceAtlas";
import { VerdictBanner } from "@/components/VerdictBanner";
import { compileStudy, type Compilation, type EvidenceRecord } from "@/lib/decision-twin";
import type { SearchProvenance } from "@/lib/decision-record";
import {
  EXEMPLAR_EVIDENCE,
  EXEMPLAR_QUESTION,
  EXEMPLAR_STUDY_ID,
  EXEMPLAR_TITLE,
} from "@/exemplar";

type Theme = "light" | "dark";

/**
 * Two people have to be served by the same screen, and they want opposite
 * things on arrival:
 *
 *   a researcher on a deadline  wants to type their own target and get on with
 *                               it, and should never have to read someone
 *                               else's study first
 *   someone judging the tool    wants one click to a finished, non-obvious
 *                               result, clearly labelled as an example
 *
 * So the landing carries a real search box AND an explicit worked example, and
 * the study screen states which of the two you are looking at. The previous
 * build had one door that opened into a pre-loaded EGFR study with no
 * explanation, which served neither: the researcher had to scroll past it, and
 * the evaluator could not tell whether the app had done anything.
 */
type Screen = "landing" | "study";
type StudyMode = "example" | "own";

function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem("biostudio-theme");
      if (stored === "light" || stored === "dark") return stored;
    } catch {
      /* private window or blocked storage — fall through to the OS preference */
    }
    // Fall through to the OS preference rather than forcing light. Someone who
    // has told their system they want dark should not have to say it again
    // here, and the dark palette is fully specified, not an afterthought.
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("biostudio-theme", theme);
    } catch {
      /* the toggle still works for this session without persistence */
    }
  }, [theme]);

  return [theme, () => setTheme((t) => (t === "dark" ? "light" : "dark"))];
}

/**
 * A study survived exactly as long as the tab did. Only the theme was persisted,
 * so an accidental reload destroyed every annotation a researcher had written --
 * and annotating is the slow, human part of the work. Saving the study is not a
 * feature so much as the absence of a way to lose an afternoon.
 */
const STUDY_KEY = "biostudio-study-v1";

interface SavedStudy {
  mode: StudyMode;
  evidence: EvidenceRecord[];
  seedQuery: string;
  seedStudyType: string;
}

function loadStudy(): SavedStudy | null {
  try {
    const raw = localStorage.getItem(STUDY_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SavedStudy;
    // Anything could be in storage -- an older shape, a hand-edited value.
    // Restore only what is structurally a study, and otherwise start clean.
    if (!Array.isArray(parsed?.evidence)) return null;
    if (parsed.mode !== "example" && parsed.mode !== "own") return null;
    return {
      mode: parsed.mode,
      evidence: parsed.evidence,
      seedQuery: String(parsed.seedQuery ?? ""),
      seedStudyType: String(parsed.seedStudyType ?? ""),
    };
  } catch {
    return null;
  }
}

/** A study id the API will accept, derived from what the researcher asked. */
function studyIdFor(query: string): string {
  const slug = query
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
  return `study-${slug || "untitled"}-${new Date().toISOString().slice(0, 10)}`;
}

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [screen, setScreen] = useState<Screen>(() =>
    window.location.hash === "#study" ? "study" : "landing",
  );
  const saved = useRef(loadStudy()).current;
  const [mode, setMode] = useState<StudyMode>(saved?.mode ?? "example");
  const [evidence, setEvidence] = useState<EvidenceRecord[]>(saved?.evidence ?? []);
  const [seedQuery, setSeedQuery] = useState(saved?.seedQuery ?? "");
  const [seedStudyType, setSeedStudyType] = useState(saved?.seedStudyType ?? "");
  const [compilation, setCompilation] = useState<Compilation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [focusedEvidenceId, setFocusedEvidenceId] = useState<string | null>(null);
  // The method behind the evidence: which source was asked what, and how much
  // of the answer was looked at. Held here because the exported record needs
  // it and the workbench is where it is learned.
  const [searchProvenance, setSearchProvenance] = useState<SearchProvenance | null>(null);

  // Compiles are fired by a button a reader can hammer, and responses are not
  // guaranteed to arrive in the order they were sent. Without this, the twelfth
  // click can be overwritten by the third one's reply and the page shows a
  // verdict that is not the latest. Only the newest run may write state.
  const runSeq = useRef(0);

  // Persist on every change rather than on a Save button: there is no server,
  // so an unsaved study is a lost study.
  useEffect(() => {
    try {
      localStorage.setItem(
        STUDY_KEY,
        JSON.stringify({ mode, evidence, seedQuery, seedStudyType }),
      );
    } catch {
      /* quota or a private window -- the session still works, it just will not survive */
    }
  }, [mode, evidence, seedQuery, seedStudyType]);

  const studyId = useMemo(
    () => (mode === "example" ? EXEMPLAR_STUDY_ID : studyIdFor(seedQuery)),
    [mode, seedQuery],
  );

  const run = useCallback(async () => {
    // The compiler requires at least one record. An empty study is a normal
    // state here -- it is where every researcher-authored study begins -- so it
    // gets its own screen rather than a validation error from the API.
    if (evidence.length === 0) {
      setCompilation(null);
      setError(null);
      setPending(false);
      return;
    }
    const seq = ++runSeq.current;
    setPending(true);
    setError(null);
    try {
      const result = await compileStudy({ study_id: studyId, evidence });
      if (seq !== runSeq.current) return;
      setCompilation(result);
    } catch (cause) {
      if (seq !== runSeq.current) return;
      setError(cause instanceof Error ? cause.message : "Compilation failed.");
      setCompilation(null);
    } finally {
      if (seq === runSeq.current) setPending(false);
    }
  }, [evidence, studyId]);

  useEffect(() => {
    void run();
  }, [run]);

  const goHome = useCallback(() => {
    window.location.hash = "";
    setScreen("landing");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const openExample = useCallback(() => {
    setMode("example");
    setEvidence(EXEMPLAR_EVIDENCE);
    setFocusedEvidenceId(EXEMPLAR_EVIDENCE[0]?.id ?? null);
    window.location.hash = "study";
    setScreen("study");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const startOwnStudy = useCallback((query: string, studyType: string) => {
    setMode("own");
    setEvidence([]);
    setCompilation(null);
    setFocusedEvidenceId(null);
    setSeedQuery(query);
    setSeedStudyType(studyType);
    window.location.hash = "study";
    setScreen("study");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const addEvidence = useCallback((record: EvidenceRecord) => {
    setEvidence((current) => [...current, record]);
    setFocusedEvidenceId((current) => current ?? record.id);
  }, []);

  const lanes = compilation?.assay_translation_map.lanes ?? [];
  const isExample = mode === "example";
  const empty = evidence.length === 0;

  return (
    <div className="min-h-screen bio-shell">
      <header className="bio-header">
        <div className="bio-header-inner">
          {/* The wordmark is the way home, as it is on every site. It was a
              plain <div> before, so the only way back to the landing page was
              the browser's back button. An <a> keeps Cmd/Ctrl-click working. */}
          <a
            href="#"
            className="bio-brand"
            onClick={(event) => {
              event.preventDefault();
              goHome();
            }}
            aria-label="BioStudio home"
          >
            <div className="bio-mark">
              <Orbit className="size-[19px]" aria-hidden="true" />
              <FlaskConical className="size-3" aria-hidden="true" />
            </div>
            <div>
              <p>BIOSTUDIO</p>
              <span>Evidence cartography</span>
            </div>
          </a>

          <div className="flex items-center gap-2">
            {screen === "study" && (
              <>
                <button type="button" onClick={goHome} className="header-button">
                  New search
                </button>
                {!empty && (
                  <button
                    type="button"
                    onClick={() => void run()}
                    disabled={pending}
                    className="header-button"
                  >
                    <RotateCw
                      className={`size-3.5 ${pending ? "animate-spin" : ""}`}
                      aria-hidden="true"
                    />
                    Recompile
                  </button>
                )}
              </>
            )}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
              className="theme-button"
            >
              {theme === "dark" ? (
                <Sun className="size-4" aria-hidden="true" />
              ) : (
                <Moon className="size-4" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </header>

      {screen === "landing" ? (
        <Landing onSearch={startOwnStudy} onOpenExample={openExample} />
      ) : (
        <main className="bio-main">
          <div className="study-intro">
            <p className="section-index">
              {isExample ? `WORKED EXAMPLE / ${EXEMPLAR_STUDY_ID}` : `YOUR STUDY / ${studyId}`}
            </p>
            <h1>{isExample ? EXEMPLAR_TITLE : seedQuery || "Untitled study"}</h1>
            <p>
              {isExample
                ? EXEMPLAR_QUESTION
                : "Search the public record, annotate what you retain, and the decision compiles from exactly what you added."}
            </p>
          </div>

          {error && (
            <p role="alert" className="compile-error">
              {error}{" "}
              <span className="text-ink-muted">
                The Decision Twin API must be running for this study to compile.
              </span>
            </p>
          )}

          {/* An empty study puts retrieval first. Nothing else on this page can
              say anything true yet, so nothing else is shown. */}
          {empty ? (
            <div className="study-flow">
              <EvidenceAnnotationWorkbench
                onEvidenceAdded={addEvidence}
                initialQuery={seedQuery}
                initialStudyType={seedStudyType}
                autoSearch={Boolean(seedQuery && seedStudyType)}
                primary
              />
            </div>
          ) : (
            <>
              {pending && !compilation && (
                <p className="compile-loading">
                  Compiling the study from its evidence&hellip;
                </p>
              )}

              {compilation && (
                <div className="study-flow">
                  <VerdictBanner compilation={compilation} />
                  <EvidenceTopology
                    evidence={evidence}
                    lanes={lanes}
                    focusedEvidenceId={focusedEvidenceId}
                    onFocusEvidence={setFocusedEvidenceId}
                  />
                  <div className="analysis-grid">
                    <EvidenceSignalPlot
                      evidence={evidence}
                      lanes={lanes}
                      focusedEvidenceId={focusedEvidenceId}
                      onFocusEvidence={setFocusedEvidenceId}
                    />
                    <EvidenceFocusCard
                      evidence={evidence}
                      lanes={lanes}
                      focusedEvidenceId={focusedEvidenceId}
                    />
                  </div>
                  <div className="atlas-grid">
                    <SourceAtlas />
                    <IntegrityPanel compilation={compilation} />
                  </div>
                  <EvidenceAnnotationWorkbench
                    onEvidenceAdded={addEvidence}
                    initialQuery={seedQuery}
                    initialStudyType={seedStudyType}
                    onSearchRan={setSearchProvenance}
                  />
                  <DecisionRecordExport
                    record={{
                      studyId,
                      title: isExample ? EXEMPLAR_TITLE : seedQuery || "Untitled study",
                      question: isExample
                        ? EXEMPLAR_QUESTION
                        : "Is the public evidence consistent enough to justify the next research step?",
                      searchQuery: seedQuery,
                      searchProvenance: searchProvenance ?? undefined,
                      isExample,
                      evidence,
                      compilation,
                    }}
                  />
                </div>
              )}
            </>
          )}
        </main>
      )}

      <footer className="bio-footer">
        <div>
          Educational and research use. BioStudio reports whether public evidence
          is consistent enough to justify a next research step; it does not
          discover drugs, replace experimental validation, or make clinical
          recommendations.
        </div>
      </footer>
    </div>
  );
}
