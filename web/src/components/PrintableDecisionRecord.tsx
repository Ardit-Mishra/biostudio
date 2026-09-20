import {
  RELATION_LABEL,
  STAGE_LABEL,
  STAGE_MEANING,
  TRANSLATION_STAGES,
  type AssayMapLane,
} from "@/lib/decision-twin";
import type { DecisionRecordInput } from "@/lib/decision-record";

/**
 * The printed dossier.
 *
 * The first version printed the markdown export inside a <pre>, which put
 * "## Question" and raw pipe tables on the page. The content was right and the
 * document was unusable -- nobody hands that to a colleague. Markdown is a fine
 * interchange format and a poor typeset one, so the printed record is laid out
 * as a document in its own right: real headings, a real table, and the citation
 * printed in full because a printed page cannot be clicked.
 *
 * Everything here is print-only. It is hidden on screen and revealed by the
 * print stylesheet, so the reader never sees two copies of the same study.
 */

function citationUrlFor(source: string, id: string): string {
  const safe = encodeURIComponent(id);
  if (source === "europe_pmc") {
    return id.startsWith("PMC")
      ? `https://europepmc.org/article/PMC/${safe}`
      : `https://europepmc.org/article/MED/${safe}`;
  }
  if (source === "open_targets") return `https://platform.opentargets.org/target/${safe}`;
  if (source === "chembl") return `https://www.ebi.ac.uk/chembl/explore/compound/${safe}`;
  return "";
}

const STATUS_LINE: Record<string, string> = {
  advance: "Advance",
  hold: "Hold",
  insufficient_evidence: "Insufficient evidence",
};

const STATUS_GLOSS: Record<string, string> = {
  advance: "Source-backed support is present and no conflict was recorded.",
  hold: "Incompatible observations must be resolved before advancing.",
  insufficient_evidence: "Nothing source-backed supports a step either way.",
};

export function PrintableDecisionRecord({ record }: { record: DecisionRecordInput }) {
  const { compilation: c, evidence } = record;
  const lanes = c.assay_translation_map.lanes;
  const at = record.generatedAt ?? new Date();
  const laneFor = (stage: string): AssayMapLane | undefined =>
    lanes.find((lane) => lane.stage === stage);
  const decisive = c.comparisons.filter(
    (x) => x.relation === "conflicting" || x.relation === "non_comparable",
  );

  return (
    <article className="print-only dossier" lang="en">
      <header className="dossier-head">
        <p className="dossier-kicker">BioStudio Decision Twin — Decision Record</p>
        <h1>{record.title}</h1>
        <p className="dossier-question">{record.question}</p>
        <dl className="dossier-meta">
          <div>
            <dt>Study</dt>
            <dd>{record.studyId}</dd>
          </div>
          <div>
            <dt>Compiled</dt>
            <dd>{at.toISOString().slice(0, 10)}</dd>
          </div>
          <div>
            <dt>Records</dt>
            <dd>{c.evidence_count}</dd>
          </div>
          <div>
            <dt>Snapshot digest</dt>
            <dd className="dossier-digest">{c.snapshot_digest}</dd>
          </div>
        </dl>
        {record.isExample && (
          <p className="dossier-note">
            This is the published worked example, not a study assembled by the reader.
          </p>
        )}
      </header>

      <section>
        <h2>Recommendation</h2>
        <p className={`dossier-verdict verdict-${c.status}`}>
          {STATUS_LINE[c.status]}
          <span> — {STATUS_GLOSS[c.status]}</span>
        </p>
        <ul className="dossier-reasons">
          {c.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
        <p className="dossier-boundary">
          A research recommendation about what to investigate next. Not a clinical,
          regulatory or purchasing decision, and derived only from the records listed
          below.
        </p>
      </section>

      <section>
        <h2>Assay translation</h2>
        <table className="dossier-table">
          <thead>
            <tr>
              <th>Stage</th>
              <th>What it measures</th>
              <th>Status</th>
              <th className="num">Records</th>
              <th>Gap</th>
            </tr>
          </thead>
          <tbody>
            {TRANSLATION_STAGES.map((stage) => {
              const lane = laneFor(stage);
              const status = lane?.status ?? "missing";
              return (
                <tr key={stage} className={status === "missing" ? "row-missing" : undefined}>
                  <td>{STAGE_LABEL[stage]}</td>
                  <td className="dim">{STAGE_MEANING[stage]}</td>
                  <td>{status}</td>
                  <td className="num">{lane?.evidence_ids.length ?? 0}</td>
                  <td className="dim">{lane?.gaps[0] ?? "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="dossier-caption">
          Evidence does not automatically carry from a purified target to a cell to an
          animal to a person. A stage marked missing has no retained observation; that
          is not weak evidence, it is none.
        </p>
      </section>

      <section>
        <h2>Evidence ({evidence.length})</h2>
        {evidence.map((r) => (
          <div className="dossier-record" key={r.id}>
            <h3>
              <span className={`dossier-dir dir-${r.outcome_direction}`}>
                {r.outcome_direction}
              </span>
              {r.source_title ?? r.claim}
            </h3>
            <p className="dossier-claim">
              <strong>Claim.</strong> {r.claim}
            </p>
            {/* The direction is what turns two records into a conflict, so the
                reason for it is printed beside it rather than left implicit. */}
            {r.direction_rationale && (
              <p className="dossier-why">
                <strong>Why it {r.outcome_direction}.</strong> {r.direction_rationale}
              </p>
            )}
            {r.assay_context && (
              <p className="dossier-context">
                <strong>Assay context.</strong> target {r.assay_context.target_id}; system{" "}
                {r.assay_context.biological_system}; readout {r.assay_context.readout}; unit{" "}
                {r.assay_context.unit}
                {r.assay_context.genetic_context
                  ? `; genetic context ${r.assay_context.genetic_context}`
                  : ""}
                {r.assay_context.conditions
                  ? Object.entries(r.assay_context.conditions).map(
                      ([k, v]) => `; ${k.replace(/_/g, " ")} ${v}`,
                    )
                  : null}
              </p>
            )}
            {/* Printed in full: a page cannot be clicked, so the reader needs the
                identifier and the address to check it themselves. */}
            <p className="dossier-cite">
              {r.citation.source.replace(/_/g, " ")} {r.citation.source_id} &middot; retrieved{" "}
              {r.citation.retrieved_at.slice(0, 10)}
              <br />
              {citationUrlFor(r.citation.source, r.citation.source_id)}
            </p>
          </div>
        ))}
      </section>

      <section>
        <h2>Integrity checks</h2>
        <p className="dossier-caption">
          {c.comparisons.length.toLocaleString()} pairwise comparison
          {c.comparisons.length === 1 ? "" : "s"} across {c.evidence_count} records.
          {decisive.length === 0
            ? " No comparison was conflicting or non-comparable."
            : " Every decisive comparison is listed; agreeing pairs are counted but not enumerated, and none changed the recommendation."}
        </p>
        {decisive.length > 0 && (
          <table className="dossier-table">
            <thead>
              <tr>
                <th>Left</th>
                <th>Right</th>
                <th>Relation</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {decisive.map((x) => (
                <tr key={`${x.left_evidence_id}-${x.right_evidence_id}`}>
                  <td>{x.left_evidence_id}</td>
                  <td>{x.right_evidence_id}</td>
                  <td>{RELATION_LABEL[x.relation]}</td>
                  <td className="dim">{x.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="dossier-method">
        <h2>How this was produced</h2>
        <dl>
          <dt>Tool</dt>
          <dd>BioStudio Decision Twin</dd>
          <dt>Retrieval</dt>
          <dd>
            {record.searchQuery
              ? `Public sources searched for “${record.searchQuery}”.`
              : "Records supplied directly to the study."}{" "}
            Retrieval never promotes a record to evidence; an operator supplied every
            claim and assay context above.
          </dd>
          {record.searchProvenance && (
            <>
              <dt>Search executed</dt>
              <dd>
                <code>{record.searchProvenance.executedQuery}</code> against{" "}
                {record.searchProvenance.source}.
              </dd>
              {record.searchProvenance.studyDesignLabel && (
                <>
                  <dt>Study design</dt>
                  <dd>
                    {record.searchProvenance.studyDesignLabel}.
                    {record.searchProvenance.studyDesignCannotSupport
                      ? ` Cannot support: ${record.searchProvenance.studyDesignCannotSupport}`
                      : ""}
                  </dd>
                </>
              )}
              <dt>Coverage</dt>
              <dd>
                {record.searchProvenance.totalHits === null
                  ? `${record.searchProvenance.returned} retrieved; this source reports no total.`
                  : `${record.searchProvenance.returned} of ${record.searchProvenance.totalHits} matching records retrieved.` +
                    (record.searchProvenance.totalHits > record.searchProvenance.returned
                      ? ` ${record.searchProvenance.totalHits - record.searchProvenance.returned} were not retrieved.`
                      : " All matching records were retrieved.")}
              </dd>
            </>
          )}
          <dt>Comparison rule</dt>
          <dd>
            Two records are comparable only when target, biological system, readout,
            unit and genetic context agree. Opposing directions on the same target are
            recorded as conflicting and force a hold.
          </dd>
          <dt>Replay</dt>
          <dd>
            Re-compiling the exported JSON snapshot reproduces the digest above. A
            changed source produces a different digest, which is the study diff.
          </dd>
        </dl>
        <p className="dossier-boundary">
          Educational and research use. BioStudio reports whether public evidence is
          consistent enough to justify a next research step; it does not discover drugs,
          replace experimental validation, or make clinical recommendations.
        </p>
      </section>
    </article>
  );
}
