/* Independent reproduction of the fourth review, before anything is changed.
   Each case constructs its own ground truth; none of it asks the verifier what
   the answer should be. */
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const E = require("../src/engine.js");
const M = require("../src/manifest.js");

const D = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const L = D.loci[0], s = L.window.seq, f = L.window.from;
const fa = (x, n) => ">" + (n || "x") + "\n" + x + "\n";
const clean = E.parseFasta(E.compose([L], "none", D.decoy).fasta)[0].seq;

let real = 0, total = 0;
const say = (id, claim, reproduced, note) => {
  total++; if (reproduced) real++;
  console.log(`${reproduced ? "REAL " : "fixed"}  ${id}  ${claim}${note ? "  [" + note + "]" : ""}`);
};

// Verdict for one request against one window, using only sequence + reference.
function verdict(seq, offset, ref, alt, win) {
  const w = win || s;
  const W = { key: "w", gene: "g", contig: "c", from: f, seq: w };
  const rows = E.reconcile([{ gene: "g", contig: "c", pos: f + offset, ref, alt }],
    E.verify(fa(seq), [W]), { "c:g": W });
  return rows.every((r) => E.isClean(r.status)) ? "released" : "held";
}

// R1 - inserting before the first base equals inserting after it only when the
// insertion commutes across the anchor: ins + win[0] === win[0] + ins. Matching
// a reference prefix is a different, weaker condition.
{
  const wrong = verdict("CA" + s, 0, "C", "CCA");      // delivers CACAGAC..., asked CCAAGAC...
  const right = verdict("CAC" + s.slice(1), 0, "C", "CAC");
  say("R1a", "a multi-base boundary insertion releases the WRONG molecule",
      wrong === "released", wrong);
  say("R1b", "a correctly delivered multi-base boundary insertion is held",
      right === "held", right + " (false hold)");
}

// R2 - two ordered molecules sharing contig, gene and start but differing in
// length are one key, so a single record can satisfy both.
{
  const other = { ...L, pos: f + 70, ref: s[70], alt: "A",
                  window: { ...L.window, seq: s.slice(0, 80), to: f + 79, flank: 70 } };
  const m = await M.seal(M.build([L, other]));
  const r = await M.checkSealed(m, fa(clean.slice(0, 70) + "A" + clean.slice(71)),
    (it) => ({ from: f, seq: s.slice(0, it.span.length), assembly: "GRCh38" }));
  say("R2", "one record satisfies two molecules that share a start",
      r.verdict === "released", `${r.verdict}, ${r.records} record for ${m.items.length} items`);
}

// R3 - a declared secondary edit is matched anywhere in the order, so a
// blocking mutation delivered on the WRONG molecule satisfies the declaration.
{
  const g = s + D.loci[1].window.seq;
  const other2 = { ...L, gene: "OTHER", pos: f + 110, ref: g[110], alt: "A",
                   window: { from: f + 45, to: f + 133, flank: 65, seq: g.slice(45, 134) } };
  const m = M.build([L, other2]);
  m.items[0].permitted = [{ contig: L.contig, pos: f + 70, ref: s[70], alt: "A" }];
  await M.seal(m);
  const recs = E.parseFasta(E.compose([L, other2], "none", D.decoy).fasta);
  recs[1].seq = recs[1].seq.slice(0, 25) + "A" + recs[1].seq.slice(26);
  const r = await M.checkSealed(m, recs.map((x) => fa(x.seq)).join(""),
    (it) => ({ from: it.span.from, seq: g.slice(it.span.from - f, it.span.to - f + 1),
               assembly: "GRCh38" }));
  say("R3", "a required edit is satisfied by the wrong molecule",
      r.verdict === "released", r.verdict);
}

// R4 - boundary refusal is decided on the untrimmed allele, so padding a valid
// internal deletion out to the window end turns it into a refusal.
{
  const deleted = s.slice(0, 21) + s.slice(22);
  const padded = verdict(deleted, 20, s.slice(20), s[20] + s.slice(22));
  const minimal = verdict(deleted, 20, s.slice(20, 22), s[20]);
  say("R4", "an equivalent padded representation is refused",
      padded !== minimal, `padded ${padded}, minimal ${minimal}`);
}

// R5 - exhaustive sweep of requests the README says are supported, each with a
// delivery built directly from the requested edit. Any hold is a false hold.
{
  let checked = 0, held = 0; const examples = [];
  const alts = ["A", "C", "G", "T"], ins = ["A", "C", "G", "T", "AC", "CA", "ACGT"];
  for (const Lx of D.loci) {
    const w = Lx.window.seq, from0 = Lx.window.from, n = w.length;
    const W = { key: "w", gene: "g", contig: "c", from: from0, seq: w };
    const run = (seq, pos, ref, alt) => {
      const rows = E.reconcile([{ gene: "g", contig: "c", pos, ref, alt }],
        E.verify(fa(seq), [W]), { "c:g": W });
      checked++;
      if (!rows.every((r) => E.isClean(r.status))) {
        held++;
        if (examples.length < 4)
          examples.push(`${Lx.gene} ${pos - from0}:${ref}>${alt} -> ` +
            rows.filter((r) => !E.isClean(r.status)).map((r) => r.status).join(","));
      }
    };
    for (let i = 0; i < n; i++) {
      for (const a of alts) if (a !== w[i]) run(w.slice(0, i) + a + w.slice(i + 1), from0 + i, w[i], a);
      for (let k = 1; k <= 4; k++) {               // anchored deletions, not terminal
        if (i + k + 1 > n - 1) continue;
        run(w.slice(0, i + 1) + w.slice(i + 1 + k), from0 + i, w.slice(i, i + 1 + k), w[i]);
      }
      for (const x of ins) run(w.slice(0, i + 1) + x + w.slice(i + 1), from0 + i, w[i], w[i] + x);
    }
  }
  say("R5", `valid edits falsely held (${held} of ${checked})`, held > 0, examples.join(" | "));
}

// R6 - sequence before the first header is silently dropped, so bases that
// were in the file never reach the verdict.
{
  const m = await M.seal(M.build([L]));
  const r = await M.checkSealed(m, "ACGTACGT\n" + fa(clean),
    () => ({ from: f, seq: s, assembly: "GRCh38" }));
  say("R6", "sequence before the first header is discarded",
      r.verdict === "released", r.verdict);
}

// R7 - the right-shift restatement returns a deletion shape even for an
// insertion, so the control feeds the comparison a different variant class.
{
  const insertion = { ...L, pos: L.window.from + 4, ref: s[4], alt: s[4] + s[4],
                      window: { ...L.window, flank: 4 } };
  const q = E.compose([insertion], "rightalign", D.decoy).requested[0];
  const stillInsertion = q.alt.length > q.ref.length;
  say("R7", "right-shifting an insertion produces a deletion",
      !stillInsertion, `${q.ref}>${q.alt}`);
}

console.log(`\n${real} of ${total} reproduce against the packaged build`);
