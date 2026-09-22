import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const F = require("../src/fuzz.js");

const data = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const N = Number(process.argv[2] || 4000);
const START = Number(process.argv[3] || 1);

const byOp = {}, failures = [];
let run = 0, declined = 0, misdeclared = 0;

for (let seed = START; seed < START + N; seed++) {
  const a = F.attempt(data.loci, data.decoy, seed);
  if (!a) { declined++; continue; }
  run++;
  const b = (byOp[a.op] ||= { kind: a.declared, n: 0, bad: 0, misdeclared: 0 });
  b.n++;
  if (a.misdeclared) { b.misdeclared++; misdeclared++; }
  if (!a.ok) { b.bad++; failures.push(a); }
}

const fp = failures.filter(f => f.failure === "false pass");
const fh = failures.filter(f => f.failure === "false hold");

console.log(`attempts run      : ${run}  (${declined} draws declined by an operator)`);
console.log(`false passes      : ${fp.length}   (corrupted export released)`);
console.log(`false holds       : ${fh.length}   (clean export blocked)\n`);
console.log("by operator:");
for (const [op, v] of Object.entries(byOp).sort((a, b) => a[1].kind.localeCompare(b[1].kind))) {
  const rate = v.n ? (100 * (v.n - v.bad) / v.n).toFixed(1) : "0.0";
  console.log(`  ${v.kind === "corrupting" ? "catch " : "allow "} ${op.padEnd(12)} ` +
    `${String(v.n).padStart(5)} attempts  ${String(v.bad).padStart(4)} wrong  ${rate}% correct` +
    (v.misdeclared ? `  (${v.misdeclared} reclassified by the file)` : ""));
}

if (failures.length) {
  console.log("\nfirst failing attempts (replay with the seed):");
  for (const f of failures.slice(0, 12)) {
    console.log(`  seed ${String(f.seed).padStart(6)}  ${f.failure.padEnd(11)} ` +
      `${f.op}  ${f.note}${f.detail ? " [" + f.detail + "]" : ""}`);
  }
  fs.writeFileSync("fuzz-failures.json", JSON.stringify(
    failures.slice(0, 60).map(({ fasta, rows, ...rest }) => rest), null, 1));
  console.log(`\nwrote fuzz-failures.json (${failures.length} total)`);
}
process.exit(0);
