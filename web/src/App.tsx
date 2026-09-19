import { useCallback, useEffect, useState } from "react";
import { FlaskConical, Moon, Orbit, RotateCw, Sun } from "lucide-react";

import { EvidenceAnnotationWorkbench } from "@/components/EvidenceAnnotationWorkbench";
import { EvidenceFocusCard } from "@/components/EvidenceFocusCard";
import { EvidenceSignalPlot } from "@/components/EvidenceSignalPlot";
import { EvidenceTopology } from "@/components/EvidenceTopology";
import { IntegrityPanel } from "@/components/IntegrityPanel";
import { Landing } from "@/components/Landing";
import { SourceAtlas } from "@/components/SourceAtlas";
import { VerdictBanner } from "@/components/VerdictBanner";
import { compileStudy, type Compilation, type EvidenceRecord } from "@/lib/decision-twin";
import {
  EXEMPLAR_EVIDENCE,
  EXEMPLAR_QUESTION,
  EXEMPLAR_STUDY_ID,
  EXEMPLAR_TITLE,
} from "@/exemplar";

type Theme = "light" | "dark";

function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem("biostudio-theme");
      if (stored === "light" || stored === "dark") return stored;
    } catch {
      /* private window or blocked storage — fall through to the OS preference */
    }
    return "light";
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

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [compilation, setCompilation] = useState<Compilation | null>(null);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>(EXEMPLAR_EVIDENCE);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(true);
  const [focusedEvidenceId, setFocusedEvidenceId] = useState<string | null>(EXEMPLAR_EVIDENCE[0]?.id ?? null);
  const [screen, setScreen] = useState<"landing" | "study">(() =>
    window.location.hash === "#study" ? "study" : "landing",
  );

  const run = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      setCompilation(
        await compileStudy({
          study_id: EXEMPLAR_STUDY_ID,
          evidence,
        }),
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Compilation failed.");
      setCompilation(null);
    } finally {
      setPending(false);
    }
  }, [evidence]);

  useEffect(() => {
    void run();
  }, [run]);

  const lanes = compilation?.assay_translation_map.lanes ?? [];
  const addEvidence = useCallback((record: EvidenceRecord) => {
    setEvidence((current) => [...current, record]);
  }, []);
  const openStudy = useCallback(() => {
    window.location.hash = "study";
    setScreen("study");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  return (
    <div className="min-h-screen bio-shell">
      <header className="bio-header">
        <div className="bio-header-inner">
          <div className="bio-brand">
            <div className="bio-mark"><Orbit className="size-[19px]" aria-hidden="true" /><FlaskConical className="size-3" aria-hidden="true" /></div>
            <div><p>BIOSTUDIO</p><span>Evidence cartography</span></div>
          </div>

          <div className="flex items-center gap-2">
            {screen === "study" ? <button type="button" onClick={() => void run()} disabled={pending} className="header-button"><RotateCw className={`size-3.5 ${pending ? "animate-spin" : ""}`} aria-hidden="true" />Recompile</button> : <button type="button" onClick={openStudy} className="header-button">Open study</button>}
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

      {screen === "landing" ? <Landing onOpenStudy={openStudy} /> : <main className="bio-main">
        <div className="study-intro">
          <p className="section-index">PUBLIC EXAMPLE / {EXEMPLAR_STUDY_ID}</p>
          <h1>{EXEMPLAR_TITLE}</h1>
          <p>{EXEMPLAR_QUESTION}</p>
        </div>

        {error && (
          <p role="alert" className="compile-error">
            {error}{" "}
            <span className="text-ink-muted">
              The Decision Twin API must be running for this study to compile.
            </span>
          </p>
        )}

        {pending && !compilation && (
          <p className="compile-loading">
            Compiling the study from its evidence&hellip;
          </p>
        )}

        {compilation && (
          <div className="study-flow">
            <VerdictBanner compilation={compilation} />
            <EvidenceTopology evidence={evidence} lanes={lanes} focusedEvidenceId={focusedEvidenceId} onFocusEvidence={setFocusedEvidenceId} />
            <div className="analysis-grid">
              <EvidenceSignalPlot evidence={evidence} lanes={lanes} focusedEvidenceId={focusedEvidenceId} onFocusEvidence={setFocusedEvidenceId} />
              <EvidenceFocusCard evidence={evidence} lanes={lanes} focusedEvidenceId={focusedEvidenceId} />
            </div>
            <div className="atlas-grid"><SourceAtlas /><IntegrityPanel compilation={compilation} /></div>
            <EvidenceAnnotationWorkbench onEvidenceAdded={addEvidence} />
          </div>
        )}
      </main>}

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
