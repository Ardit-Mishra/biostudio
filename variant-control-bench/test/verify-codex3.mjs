/* Reproduce the third review's findings against the packaged build, before
   changing anything. Two of them were already fixed after that review started,
   so the point is to find out which are real here. */
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const E = require("../src/engine.js");
const M = require("../src/manifest.js");
const A = require("../src/assembly.js");

const D = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const L = D.loci[0], s = L.window.seq, from = L.window.from;
const fa = (seq, n) => ">" + (n || "frag") + "\n" + seq + "\n";
const clean = E.compose([L], "none", D.decoy).fasta;
const c = E.parseFasta(clean)[0].seq;
const ref = () => ({ from, seq: s, assembly: "GRCh38" });

let real = 0;
const say = (id, claim, reproduced, note) => {
  if (reproduced) real++;
  console.log(`${reproduced ? "REAL " : "fixed"}  ${id}  ${claim}${note ? "  [" + note + "]" : ""}`);
};

// A (P0) — two manifest items sharing a gene label on different contigs.
{
  const other = {
    ...L, contig: "chr8", pos: from + 70, ref: s[70], alt: "A",
    window: { ...L.window, flank: 70, seq: "A" + s.slice(1) }
  };
  const m = await M.seal(M.build([L, other]));
  const r = await M.checkSealed(m, fa(c.slice(0, 70) + "A" + c.slice(71)),
    (it) => ({ from, assembly: "GRCh38",
               seq: it.contig === "chr8" ? other.window.seq : s }));
  say("A", "two items sharing a gene label collide; one record satisfies both",
      r.verdict === "released", `${r.verdict}, ${r.records} record(s), ${m.items.length} items`);
}

// B — the body that verified is not the body that got checked.
{
  const m = await M.seal(M.build([L]));
  const pending = M.checkSealed(m, fa(s.slice(0, 44) + "G" + s.slice(45)), ref);
  m.items[0].alt = "G";
  const r = await pending;
  const after = await M.verifySeal(m);
  say("B", "seal verifies one body while a mutated one is checked",
      r.verdict === "released" && r.seal.ok && !after.ok,
      `${r.verdict}, sealOk ${r.seal.ok}, later ${after.ok}`);
}

// C — a declaration imported as JSON with neither required nor optional.
{
  let m = M.build([L]);
  m.items[0].permitted = [{ contig: L.contig, pos: from + 70, ref: s[70], alt: "A" }];
  m = M.parse(JSON.stringify(await M.seal(m)));
  const r = await M.checkSealed(m, clean, ref);
  say("C", "imported declaration lacking required may be absent",
      r.verdict === "released", r.verdict);
}

// D — secondary edits skip the REF validation the primary request gets.
{
  const m = await M.seal(M.build([L], {
    permitted: [{ contig: L.contig, pos: from + 70, ref: "TA", alt: "AA" }] }));
  const r = await M.checkSealed(m, fa(c.slice(0, 70) + "A" + c.slice(71)), ref);
  say("D", "secondary edit with a wrong REF is accepted after trimming",
      r.verdict === "released", `${r.verdict}, reference at 70-71 is ${s.slice(70, 72)}`);
}

// E — endpoint alone made inconsistent.
{
  const m = M.build([L]);
  m.items[0].span.to += 1000;
  await M.seal(m);
  const r = await M.checkSealed(m, clean, ref);
  say("E", "span.to alone can contradict from+length", r.verdict === "released", r.verdict);
}

// F — nobody states which assembly the reference is.
{
  const m = M.build([L]);
  m.assembly = "GRCh37";
  await M.seal(m);
  const bare = () => ({ from, seq: s });            // no assembly declared
  const r = await M.checkSealed(m, clean, bare);    // and none supplied
  say("F", "an unidentified reference is accepted for any assembly",
      r.verdict === "released", r.verdict);
}

// G — a legitimate insertion at the first base of the window (FALSE HOLD).
{
  const W = [{ key: "g", gene: "g", contig: "chrG", from, seq: s }];
  const byKey = { "chrG:g": W[0] };
  const req = [{ gene: "g", contig: "chrG", pos: from, ref: s[0], alt: s[0] + s[0],
                 hgvsp: "dup first base" }];
  const delivered = s[0] + s;
  const rows = E.reconcile(req, E.verify(fa(delivered), W), byKey);
  const v = rows.filter((r) => !E.isClean(r.status)).length ? "held" : "released";
  say("G", "a valid first-base insertion is falsely held", v === "held",
      `${v} (false hold)`);
}

// H — a deletion of the final base, correctly delivered (FALSE HOLD).
{
  const W = [{ key: "h", gene: "h", contig: "chrH", from, seq: s }];
  const byKey = { "chrH:h": W[0] };
  const n = s.length;
  const req = [{ gene: "h", contig: "chrH", pos: from + n - 2,
                 ref: s.slice(n - 2), alt: s[n - 2], hgvsp: "drop last base" }];
  const delivered = s.slice(0, n - 1);
  const rows = E.reconcile(req, E.verify(fa(delivered), W), byKey);
  // A deletion running to the last base cannot be told apart from a fragment
  // cut there, because the reference beyond the window is not held. The right
  // outcome is an explicit refusal naming that limit -- silently holding it as
  // a mismatch would blame the delivery for the checker's blind spot.
  const refused = rows.find((r) => r.status === "refused");
  say("H", "a terminal deletion is mishandled rather than refused by name",
      !refused || !/indistinguishable/.test(refused.note || ""),
      refused ? "refused: " + refused.note.slice(0, 64) : rows.map((r) => r.status).join(","));
}

// I — an ALT that is not a nucleotide.
{
  const bad = { ...L, alt: "?" };
  const r = E.run([bad], "none", D.decoy);
  say("I", "a non-nucleotide ALT is accepted as an SNV",
      r.verdict === "released", `${r.verdict}, fasta has '?': ${r.fasta.includes("?")}`);
}

// J — assembly erases unsupported symbols instead of rejecting them.
{
  const plan = A.plan(L);
  const withR = plan.sequence.slice(0, 20) + "R" + plan.sequence.slice(20);
  const res = A.checkConstruct(plan, withR);
  say("J", "an IUPAC symbol is stripped, hiding an extra base",
      res.verdict === "released", res.verdict);
}

// K — overhang compatibility ignores strand and palindromes.
{
  const mk = (gene, oh5, oh3) => ({ gene, overhang5: oh5, overhang3: oh3 });
  const comp = A.checkPool([mk("X", "AAGC", "TTTT"), mk("Y", "GCTT", "CCCC")]);
  const pal = A.checkPool([mk("P", "ATAT", "GGGG")]);
  say("K", "complementary or palindromic overhangs are not caught",
      comp.verdict === "released" || pal.verdict === "released",
      `AAGC/GCTT -> ${comp.verdict}, palindromic ATAT -> ${pal.verdict}`);
}

// Arm shorter than the overhang it claims to leave.
{
  const p = A.plan(L, { arm: 1 });
  const res = A.checkConstruct(p, p.sequence);
  say("M", "an arm shorter than the overhang still reports a 4 nt overhang",
      res.verdict === "released" && p.overhang5.length < 4,
      `overhang5 "${p.overhang5}" (${p.overhang5.length} nt)`);
}

console.log(`\n${real} of 12 reproduce against the packaged build`);
