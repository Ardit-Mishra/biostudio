import { Download, FileJson, FileSpreadsheet, FileText, Printer } from "lucide-react";

import { PrintableDecisionRecord } from "@/components/PrintableDecisionRecord";

import {
  downloadText,
  filenameFor,
  toCsv,
  toJson,
  toRis,
  type DecisionRecordInput,
} from "@/lib/decision-record";

/**
 * The way the work leaves the browser.
 *
 * Four formats, each for a different reader, and the panel says which is which
 * rather than offering an undifferentiated row of buttons. A researcher on a
 * deadline should be able to tell at a glance which one to press.
 */
const FORMATS = [
  {
    key: "pdf" as const,
    label: "Decision Record",
    hint: "Print or save as PDF — the document you attach to a memo",
    icon: Printer,
  },
  {
    key: "csv" as const,
    label: "Evidence table",
    hint: "CSV, one row per record — opens in Excel",
    icon: FileSpreadsheet,
  },
  {
    key: "ris" as const,
    label: "Citations",
    hint: "RIS — imports into Zotero, EndNote or Mendeley",
    icon: FileText,
  },
  {
    key: "json" as const,
    label: "Replay snapshot",
    hint: "JSON — re-compiles to the same digest",
    icon: FileJson,
  },
];

export function DecisionRecordExport({ record }: { record: DecisionRecordInput }) {
  function handle(kind: "pdf" | "csv" | "ris" | "json") {
    if (kind === "pdf") {
      // The browser's own print-to-PDF rather than a bundled PDF library: it
      // needs no dependency, honours the reader's paper size, and the print
      // stylesheet already lays the page out for it.
      window.print();
      return;
    }
    if (kind === "csv") {
      downloadText(filenameFor(record.studyId, "csv"), toCsv(record), "text/csv");
      return;
    }
    if (kind === "ris") {
      downloadText(filenameFor(record.studyId, "ris"), toRis(record), "application/x-research-info-systems");
      return;
    }
    downloadText(filenameFor(record.studyId, "json"), toJson(record), "application/json");
  }

  return (
    <section className="export-panel" aria-labelledby="export-heading">
      <div className="export-intro">
        <p className="section-index">05 / TAKE IT WITH YOU</p>
        <h2 id="export-heading">A decision nobody can carry is not a decision.</h2>
        <p>
          Every format below is built from the records in this study and nothing
          else. The snapshot re-compiles to digest{" "}
          <code>{record.compilation.snapshot_digest.slice(0, 16)}…</code>, which
          is what makes the recommendation checkable by someone who was not here.
        </p>
      </div>

      <ul className="export-list">
        {FORMATS.map((format) => {
          const Icon = format.icon;
          return (
            <li key={format.key}>
              <button type="button" onClick={() => handle(format.key)}>
                <Icon className="size-4" aria-hidden="true" />
                <span>
                  <strong>{format.label}</strong>
                  <em>{format.hint}</em>
                </span>
                <Download className="size-3.5 export-arrow" aria-hidden="true" />
              </button>
            </li>
          );
        })}
      </ul>

      {/* The printed document. Hidden on screen, typeset for paper -- printing
          the markdown export put "## Question" and raw pipe tables on the page. */}
      <PrintableDecisionRecord record={record} />
    </section>
  );
}
