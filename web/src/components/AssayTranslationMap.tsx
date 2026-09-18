import {
  STAGE_LABEL,
  STAGE_MEANING,
  TRANSLATION_STAGES,
  type AssayMapLane,
  type AssayStage,
  type LaneStatus,
} from "@/lib/decision-twin";

/**
 * The Assay Translation Map.
 *
 * Not four status cards in a row. The product's claim is that evidence does not
 * automatically translate from a purified enzyme to a cell to an animal to a
 * person, so the *joins* between stages carry the argument and are drawn
 * explicitly:
 *
 *   intact    a solid rule      both stages hold evidence that agrees
 *   strained  a dashed ochre rule  one side contradicts the other
 *   broken    a faint gapped rule  one side has nothing to translate into
 *
 * Drawing a continuous line through an empty stage would assert a continuity
 * the data does not have. That is the failure this whole view exists to make
 * impossible to miss.
 */

type LinkState = "intact" | "strained" | "broken";

const STATUS_TEXT: Record<LaneStatus, string> = {
  supporting: "text-[var(--ds-supporting)]",
  contradicting: "text-[var(--ds-contradicting)]",
  conflicting: "text-[var(--ds-conflicting)]",
  inconclusive: "text-ink-muted",
  missing: "text-ink-faint",
  unclassified: "text-ink-faint",
};

const STATUS_LABEL: Record<LaneStatus, string> = {
  supporting: "Supporting",
  contradicting: "Contradicting",
  conflicting: "Conflicting",
  inconclusive: "Inconclusive",
  missing: "No evidence",
  unclassified: "Unclassified",
};

/** Solid fill for a recorded state; hollow for absence. */
function nodeSkin(status: LaneStatus): string {
  switch (status) {
    case "supporting":
      return "border-[var(--ds-supporting)] bg-[var(--ds-supporting-soft)]";
    case "contradicting":
      return "border-[var(--ds-contradicting)] bg-[var(--ds-contradicting-soft)]";
    case "conflicting":
      return "border-[var(--ds-conflicting)] bg-[var(--ds-conflicting-soft)]";
    case "inconclusive":
      return "border-line-strong bg-sunk";
    // Absence is hollow — a dashed outline over the page ground, with no fill of
    // its own, so it cannot read as a weak-but-present measurement.
    default:
      return "border-dashed border-line-strong bg-transparent";
  }
}

function linkBetween(left: AssayMapLane, right: AssayMapLane): LinkState {
  const empty = (lane: AssayMapLane) =>
    lane.status === "missing" || lane.status === "unclassified";
  if (empty(left) || empty(right)) return "broken";
  const opposed = (lane: AssayMapLane) =>
    lane.status === "contradicting" || lane.status === "conflicting";
  if (opposed(left) || opposed(right)) return "strained";
  return "intact";
}

const LINK_CLASS: Record<LinkState, string> = {
  intact: "link-intact",
  strained: "link-strained",
  broken: "link-broken",
};

const LINK_NOTE: Record<LinkState, string> = {
  intact: "carries",
  strained: "disputed",
  broken: "breaks",
};

function StageNode({ lane }: { lane: AssayMapLane }) {
  const count = lane.evidence_ids.length;
  return (
    <div
      className={`flex h-full flex-col rounded-lg border p-4 ${nodeSkin(lane.status)}`}
    >
      <div className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-ink-faint">
        {STAGE_MEANING[lane.stage]}
      </div>
      <h3 className="mt-1.5 text-base font-semibold text-ink">
        {STAGE_LABEL[lane.stage]}
      </h3>

      <div
        className={`mt-3 font-mono text-xs font-medium ${STATUS_TEXT[lane.status]}`}
      >
        {STATUS_LABEL[lane.status]}
      </div>

      <div className="mt-1 font-mono text-[11px] text-ink-faint tabular">
        {count > 0
          ? `${count} record${count === 1 ? "" : "s"}`
          : "—"}
      </div>

      {lane.gaps.length > 0 && (
        <p className="mt-3 border-t border-line pt-3 text-[12.5px] leading-snug text-ink-muted">
          {lane.gaps[0]}
        </p>
      )}
    </div>
  );
}

function Link({ state }: { state: LinkState }) {
  return (
    // A fixed lane of its own. Given only padding, the label ran under the
    // neighbouring cards; the connector needs real width so the rule and its
    // note sit between the stages rather than on top of them.
    <div
      className="flex shrink-0 flex-col items-center justify-center gap-1.5 self-center py-3 md:w-20 md:py-0 lg:w-24"
      aria-hidden="true"
    >
      {/* Horizontal on wide screens, vertical when the chain stacks. */}
      <div className={`h-6 w-px md:h-px md:w-full ${LINK_CLASS[state]}`} />
      <span className="whitespace-nowrap font-mono text-[9.5px] uppercase tracking-[0.1em] text-ink-faint">
        {LINK_NOTE[state]}
      </span>
    </div>
  );
}

export function AssayTranslationMap({ lanes }: { lanes: AssayMapLane[] }) {
  const byStage = new Map<AssayStage, AssayMapLane>(
    lanes.map((lane) => [lane.stage, lane]),
  );
  const chain = TRANSLATION_STAGES.map(
    (stage) =>
      byStage.get(stage) ?? {
        stage,
        status: "missing" as LaneStatus,
        evidence_ids: [],
        gaps: ["No evidence was supplied for this stage."],
      },
  );

  const unclassified = byStage.get("unclassified");
  const brokenCount = chain
    .slice(0, -1)
    .filter((lane, i) => linkBetween(lane, chain[i + 1]) === "broken").length;

  return (
    <section aria-labelledby="atm-heading">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2
          id="atm-heading"
          className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-ink-muted"
        >
          Assay translation map
        </h2>
        <p className="font-mono text-[11px] text-ink-faint tabular">
          {brokenCount === 0
            ? "chain intact"
            : `${brokenCount} of 3 steps do not translate`}
        </p>
      </div>

      <p className="mt-2 max-w-prose text-[13.5px] leading-relaxed text-ink-muted">
        Evidence does not automatically carry from a purified target to a cell to
        an animal to a person. Where a step has nothing to translate into, the
        chain is drawn broken rather than continuous.
      </p>

      <div className="mt-5 flex flex-col md:flex-row md:items-stretch">
        {chain.map((lane, i) => (
          <div key={lane.stage} className="contents">
            <div className="min-w-0 flex-1">
              <StageNode lane={lane} />
            </div>
            {i < chain.length - 1 && (
              <Link state={linkBetween(lane, chain[i + 1])} />
            )}
          </div>
        ))}
      </div>

      {unclassified && unclassified.evidence_ids.length > 0 && (
        <p className="mt-4 rounded-md border border-dashed border-line-strong px-3 py-2 font-mono text-[11.5px] text-ink-muted">
          {unclassified.evidence_ids.length} record
          {unclassified.evidence_ids.length === 1 ? "" : "s"} could not be placed
          on the chain — no recognised biological system was recorded.
        </p>
      )}
    </section>
  );
}
