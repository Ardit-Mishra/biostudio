import type { Compilation, DecisionStatus } from "@/lib/decision-twin";

/**
 * The decision gate.
 *
 * Deliberately not a score, a percentage, or a confidence dial. The compiler
 * returns one of three discrete states and a list of reasons, and the surface
 * should not imply a continuum the backend never computed — inventing a "78%
 * confidence" here would be exactly the overclaim the product argues against.
 *
 * `hold` is the interesting state and gets the strongest treatment, because a
 * system that only looks decisive when it says yes is not worth trusting when
 * it says no.
 */

const COPY: Record<
  DecisionStatus,
  { label: string; gloss: string; tone: string; rule: string }
> = {
  advance: {
    label: "Advance",
    gloss: "Source-backed support, no recorded conflict",
    tone: "text-[var(--ds-supporting)]",
    rule: "bg-[var(--ds-supporting)]",
  },
  hold: {
    label: "Hold",
    gloss: "Incompatible observations must be resolved first",
    tone: "text-[var(--ds-conflicting)]",
    rule: "bg-[var(--ds-conflicting)]",
  },
  insufficient_evidence: {
    label: "Insufficient evidence",
    gloss: "Nothing source-backed supports a step either way",
    tone: "text-ink-muted",
    rule: "bg-line-strong",
  },
};

export function VerdictBanner({ compilation }: { compilation: Compilation }) {
  const copy = COPY[compilation.status];

  return (
    <section
      aria-labelledby="verdict-heading"
      className="relative overflow-hidden rounded-xl border border-line bg-surface"
    >
      {/* A single edge rule carries the status colour. The panel itself stays
          neutral so the verdict reads as a stamp on a document, not as an alert. */}
      <div className={`absolute inset-y-0 left-0 w-1 ${copy.rule}`} aria-hidden="true" />

      <div className="px-6 py-5 pl-7">
        <p className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-ink-faint">
          Research recommendation
        </p>

        <div className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1">
          <h2
            id="verdict-heading"
            className={`text-3xl font-semibold tracking-tight ${copy.tone}`}
          >
            {copy.label}
          </h2>
          <p className="text-sm text-ink-muted">{copy.gloss}</p>
        </div>

        {compilation.reasons.length > 0 && (
          <ul className="mt-4 space-y-1.5">
            {compilation.reasons.map((reason) => (
              <li
                key={reason}
                className="flex gap-2.5 text-[14.5px] leading-relaxed text-ink"
              >
                <span aria-hidden="true" className="text-ink-faint">
                  &rarr;
                </span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        )}

        <p className="mt-5 border-t border-line pt-4 text-[12.5px] leading-relaxed text-ink-muted">
          A research recommendation about what to do next, not a clinical or
          regulatory conclusion. It is derived only from the records listed
          below, and it changes when they do.
        </p>
      </div>
    </section>
  );
}
