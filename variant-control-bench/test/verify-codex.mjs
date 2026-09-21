/* Reproduce each P0 Codex reported, independently, before fixing anything. */
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const E = require("../src/engine.js");
const M = require("../src/manifest.js");

const data = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const L = data.loci[0];                       // BRAF
const win = L.window.seq, from = L.window.from;
const W = [{ key: L.gene, gene: L.gene, contig: L.contig, from, seq: win }];
const byKey = { [L.contig + ":" + L.gene]: W[0] };
const fa = (s, n) => ">" + (n || "frag") + "\n" + s + "\n";
const run = (requested, fasta, permitted) => {
  const f = E.verify(fasta, W);
  const rows = E.reconcile(requested, f, byKey, permitted);
  const bad = rows.filter((r) => !E.isClean(r.status)).length;
  return { verdict: bad ? "held" : "released", rows, bad };
};
const say = (claim, reproduced) =>
  console.log(`${reproduced ? "CONFIRMED" : "NOT REPRODUCED"}  ${claim}`);

console.log("BRAF window", L.contig + ":" + from + "-" + L.window.to, "\n");

// 1 — complex replacement TT>A normalised into a different allele.
{
  const at = 10;                                  // window index with TT
  let i = win.indexOf("TT");
  const pos = from + i;
  const requested = [{ gene: L.gene, contig: L.contig, pos, ref: "TT", alt: "A", hgvsp: "test" }];
  const delivered = win.slice(0, i) + "T" + win.slice(i + 2);   // delete ONE T, keep a T
  const r = run(requested, fa(delivered));
  const n = E.leftAlign(win, i, "TT", "A");
  console.log(`  request ${L.contig}:${pos} TT>A  normalises to index ${n.at} ${n.ref}>${n.alt}`);
  say("1. leftAlign turns a complex replacement into a different allele",
      r.verdict === "released" || n.alt !== "A");
}

// 2 — insertion at the very start of the window.
{
  const requested = [{ gene: L.gene, contig: L.contig, pos: from, ref: win[0],
                       alt: win[0] + "A", hgvsp: "test" }];
  const delivered = "A" + win;                     // A BEFORE the reference
  const r = run(requested, fa(delivered));
  say("2. leading insertion anchored on the wrong side releases", r.verdict === "released");
}

// 3 — extra unrequested records riding along with a correct one.
{
  const f = L.window.flank;
  const correct = win.slice(0, f) + L.alt + win.slice(f + L.ref.length);
  const requested = [{ gene: L.gene, contig: L.contig, pos: L.pos, ref: L.ref, alt: L.alt,
                       hgvsp: L.hgvsp }];
  const plusRef = fa(correct, "a") + fa(win, "b");                    // extra unedited record
  const plusRC  = fa(correct, "a") + fa(E.revcomp(win), "c");         // extra reversed record
  const a = run(requested, plusRef), b = run(requested, plusRC);
  console.log("  +unedited record ->", a.verdict, " +revcomp record ->", b.verdict);
  say("3. extra unrequested records are not reported",
      a.verdict === "released" || b.verdict === "released");
}

// 4 — sealed span and assembly are not enforced.
{
  const m = await M.seal(M.build([L], {}));
  const clean = E.compose([L], "none", data.decoy).fasta;
  const refFor = (it) => (it.contig === L.contig && it.span.from === L.window.from)
    ? { from: L.window.from, seq: win } : null;

  const stretched = JSON.parse(JSON.stringify(m));
  stretched.items[0].span.to += 1000; stretched.items[0].span.length += 1000;
  await M.seal(stretched);
  const s1 = await M.checkSealed(stretched, clean, refFor);

  const wrongAsm = JSON.parse(JSON.stringify(m));
  wrongAsm.assembly = "GRCh37";
  await M.seal(wrongAsm);
  const s2 = await M.checkSealed(wrongAsm, clean, refFor, { assembly: "GRCh38" });
  console.log("  span +1000 ->", s1.verdict, " assembly GRCh37 ->", s2.verdict);
  say("4. sealed span / assembly are not validated against the reference used",
      s1.verdict === "released" || s2.verdict === "released");
}

// 5 — a broken seal does not block acceptance.
{
  const m = await M.seal(M.build([L], {}));
  m.items[0].hgvsp = "tampered";                    // breaks the seal
  const clean = E.compose([L], "none", data.decoy).fasta;
  const refFor = () => ({ from: L.window.from, seq: win });
  const res = await M.checkSealed(m, clean, refFor);
  const seal = await M.verifySeal(m);
  console.log("  seal ok?", seal.ok, " check verdict ->", res.verdict);
  say("5. check() accepts a manifest whose seal is broken", !seal.ok && res.verdict === "released");
}

// 6 — a declared intended edit is optional, not required.
{
  const f = L.window.flank;
  const correct = win.slice(0, f) + L.alt + win.slice(f + L.ref.length);
  const at = f + 26;
  const requested = [{ gene: L.gene, contig: L.contig, pos: L.pos, ref: L.ref, alt: L.alt,
                       hgvsp: L.hgvsp }];
  const permitted = [{ contig: L.contig, pos: from + at, ref: win[at],
                       alt: win[at] === "A" ? "C" : "A", why: "declared", required: true }];
  const r = run(requested, fa(correct), permitted);   // declared edit ABSENT from delivery
  say("6. a declared intended edit can simply be missing", r.verdict === "released");
}

// 7 — two records substituted for one ordered molecule.
{
  const f = L.window.flank;
  const correct = win.slice(0, f) + L.alt + win.slice(f + L.ref.length);
  const requested = [{ gene: L.gene, contig: L.contig, pos: L.pos, ref: L.ref, alt: L.alt,
                       hgvsp: L.hgvsp }];
  const split = fa(correct.slice(0, 60), "p1") + fa(win.slice(60), "p2");
  const gapped = fa(correct.slice(0, 60), "p1") + fa(win.slice(66), "p2");
  const a = run(requested, split), b = run(requested, gapped);
  console.log("  split into 2 records ->", a.verdict, " split with a 6 nt hole ->", b.verdict);
  say("7. coverage can be assembled from disconnected records",
      a.verdict === "released" || b.verdict === "released");
}
