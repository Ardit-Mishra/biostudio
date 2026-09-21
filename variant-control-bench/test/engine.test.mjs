import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const E = require("../src/engine.js");

const data = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const loci = data.loci, decoy = data.decoy;

const CLASSES = [
  ["none",       "released", "clean construct"],
  ["revcomp",    "held",     "reverse complement"],
  ["offbyone",   "held",     "off-by-one position"],
  ["contig",     "held",     "wrong contig"],
  ["extra",      "held",     "unrequested substitution"],
  ["truncate",   "held",     "truncated flank"],
  ["dup",        "held",     "duplicated fragment"],
  ["rightalign", "released", "right-aligned indel (must NOT flag)"],
  ["wrap",       "released", "line wrap + soft-mask (must NOT flag)"],
];

let fails = 0;
console.log("loci in order: " + loci.map(l => l.gene).join(", ") + "\n");

for (const [key, expect, label] of CLASSES) {
  const r = E.run(loci, key, decoy);
  const ok = r.verdict === expect;
  if (!ok) fails++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${label.padEnd(38)} ` +
    `verdict=${r.verdict.padEnd(8)} expected=${expect.padEnd(8)} discrepancies=${r.discrepancies}`);
  for (const row of r.rows) {
    if (row.status === "match" && key !== "none" && !row.note.includes("normalised")) continue;
    console.log(`        ${String(row.status).padEnd(9)} ${(row.gene + " " + (row.hgvsp||"")).padEnd(26)} ` +
      `${row.recPos === null ? "—" : row.recPos}  ${row.note}`);
  }
}

// The separation claim, checked rather than asserted: verify() must reach the
// same conclusion when it is given ONLY sequence and reference.
const composed = E.compose(loci, "offbyone", decoy);
const windows = loci.map(L => ({ key:L.gene, gene:L.gene, contig:L.contig,
                                 from:L.window.from, seq:L.window.seq }));
const blind = E.verify(composed.fasta, windows);
const calledAt = blind.filter(f => f.status === "called").map(f => f.pos);
const requestedAt = composed.requested.map(q => q.pos);
console.log("\nseparation check — verify() given only FASTA + reference:");
console.log("  requested positions: " + requestedAt.join(", "));
console.log("  recovered positions: " + calledAt.join(", "));
console.log("  recovered != requested: " +
  (JSON.stringify(calledAt) !== JSON.stringify(requestedAt)));

console.log(`\n${CLASSES.length - fails}/${CLASSES.length} classes resolved as specified`);
console.log("\nexported FASTA, first record (clean run):");
console.log(E.run(loci, "none", decoy).fasta.split(">").slice(1,2).map(s=>">"+s).join(""));
process.exit(fails ? 1 : 0);
