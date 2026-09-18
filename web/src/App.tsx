import { useCallback, useEffect, useState } from "react";
import { FlaskConical, Moon, RotateCw, Sun } from "lucide-react";

import { AssayTranslationMap } from "@/components/AssayTranslationMap";
import { EvidenceInspector } from "@/components/EvidenceInspector";
import { IntegrityPanel } from "@/components/IntegrityPanel";
import { VerdictBanner } from "@/components/VerdictBanner";
import { compileStudy, type Compilation } from "@/lib/decision-twin";
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

export default function App() {
  const [theme, toggleTheme] = useTheme();
  const [compilation, setCompilation] = useState<Compilation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(true);

  const run = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      setCompilation(
        await compileStudy({
          study_id: EXEMPLAR_STUDY_ID,
          evidence: EXEMPLAR_EVIDENCE,
        }),
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Compilation failed.");
      setCompilation(null);
    } finally {
      setPending(false);
    }
  }, []);

  useEffect(() => {
    void run();
  }, [run]);

  const lanes = compilation?.assay_translation_map.lanes ?? [];

  return (
    <div className="min-h-screen bg-ground">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="grid size-9 shrink-0 place-items-center rounded-lg border border-[var(--ds-accent)]/40 bg-accent-soft text-[var(--ds-accent-ink)]">
              <FlaskConical className="size-4.5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <p className="font-mono text-[12.5px] font-semibold tracking-[0.14em] text-ink">
                BIOSTUDIO
              </p>
              <p className="text-[12px] text-ink-muted">
                Research-decision integrity
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => void run()}
              disabled={pending}
              className="inline-flex min-h-9 items-center gap-2 rounded-md border border-line px-3 font-mono text-[12px] text-ink-muted transition-colors hover:border-line-strong hover:text-ink disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ds-accent)]"
            >
              <RotateCw
                className={`size-3.5 ${pending ? "animate-spin" : ""}`}
                aria-hidden="true"
              />
              Recompile
            </button>
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
              className="grid size-9 place-items-center rounded-md border border-line text-ink-muted transition-colors hover:border-line-strong hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ds-accent)]"
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

      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-6 sm:py-10">
        <div className="max-w-3xl">
          <p className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-[var(--ds-accent-ink)]">
            Public exemplar study
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">
            {EXEMPLAR_TITLE}
          </h1>
          <p className="mt-3 text-[15px] leading-relaxed text-ink-muted">
            {EXEMPLAR_QUESTION}
          </p>
          <p className="mt-3 font-mono text-[11.5px] text-ink-faint">
            {EXEMPLAR_STUDY_ID}
          </p>
        </div>

        {error && (
          <p
            role="alert"
            className="mt-8 rounded-lg border border-[var(--ds-conflicting)] bg-[var(--ds-conflicting-soft)] px-4 py-3 text-[14px] text-ink"
          >
            {error}{" "}
            <span className="text-ink-muted">
              The Decision Twin API must be running for this study to compile.
            </span>
          </p>
        )}

        {pending && !compilation && (
          <p className="mt-8 font-mono text-[12.5px] text-ink-muted">
            Compiling the study from its evidence&hellip;
          </p>
        )}

        {compilation && (
          <div className="mt-8 space-y-10">
            <VerdictBanner compilation={compilation} />

            <AssayTranslationMap lanes={lanes} />

            <div className="grid gap-10 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
              <EvidenceInspector evidence={EXEMPLAR_EVIDENCE} lanes={lanes} />
              <IntegrityPanel compilation={compilation} />
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto max-w-6xl px-5 py-6 text-[12px] leading-relaxed text-ink-faint sm:px-6">
          Educational and research use. BioStudio reports whether public evidence
          is consistent enough to justify a next research step; it does not
          discover drugs, replace experimental validation, or make clinical
          recommendations.
        </div>
      </footer>
    </div>
  );
}
