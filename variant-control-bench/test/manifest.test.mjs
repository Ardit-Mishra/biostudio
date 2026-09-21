import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const E = require("../src/engine.js");
const M = require("../src/manifest.js");

const data = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const loci = data.loci;
const refFor = (it) => {
  const L = loci.find((x) => x.contig === it.contig && x.window.from === it.span.from);
  return L ? { from: L.window.from, seq: L.window.seq, assembly: "GRCh38" } : null;
};

let fails = 0;
const check = (name, got, want) => {
  const ok = got === want;
  if (!ok) fails++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name.padEnd(52)} got=${got} want=${want}`);
};

const m = await M.seal(M.build(loci, { source: data.sources.sequence }));
console.log("manifest id:", m.id);
console.log("items:", m.items.length, "\n");

// Identity is content-addressed and stable.
const again = await M.seal(M.build(loci, { source: data.sources.sequence, created: m.created }));
check("re-sealing identical content gives the same id", again.id === m.id, true);
check("seal verifies", (await M.verifySeal(m)).ok, true);
const tampered = JSON.parse(JSON.stringify(m));
tampered.items[0].alt = "G";
check("tampered manifest fails its seal", (await M.verifySeal(tampered)).ok, false);

// A correct delivery.
const clean = E.compose(loci, "none", data.decoy).fasta;
check("correct delivery releases", (await M.checkSealed(m, clean, refFor)).verdict, "released");

// Each seeded defect, arriving as a vendor delivery.
for (const d of ["revcomp", "offbyone", "contig", "extra", "truncate", "dup"]) {
  const bad = E.compose(loci, d, data.decoy).fasta;
  check(`delivery with ${d} is held`, (await M.checkSealed(m, bad, refFor)).verdict, "held");
}
for (const d of ["wrap"]) {
  const ok = E.compose(loci, d, data.decoy).fasta;
  check(`delivery with ${d} still releases`, (await M.checkSealed(m, ok, refFor)).verdict, "released");
}

// An intended silent edit: held when undeclared, accepted when the manifest
// declared it, and still held if the delivery carries a DIFFERENT extra edit.
const L0 = loci[0], f0 = L0.window.flank, extraAt = f0 + 26;
const win = L0.window.seq;
const withEdit = win.slice(0, f0) + L0.alt + win.slice(f0 + L0.ref.length);
const silentBase = withEdit[extraAt] === "A" ? "C" : "A";
const withSilent = withEdit.slice(0, extraAt) + silentBase + withEdit.slice(extraAt + 1);
const oneRec = ">" + L0.gene + "_" + L0.contig + "_" + L0.pos + "\n" + withSilent + "\n";
const oneItem = (permitted) => M.build([L0], { permitted });

const undeclared = await M.seal(oneItem([]));
check("undeclared silent edit is held", (await M.checkSealed(undeclared, oneRec, refFor)).verdict, "held");

const declaredPos = L0.window.from + extraAt;
const declared = await M.seal(oneItem([{
  contig: L0.contig, pos: declaredPos, ref: win[extraAt], alt: silentBase,
  why: "PAM-blocking silent substitution"
}]));
const dres = await M.checkSealed(declared, oneRec, refFor);
check("declared silent edit releases", dres.verdict, "released");
check("declared edit is labelled intended",
  dres.rows.some((r) => r.status === "intended"), true);

const wrongDeclared = await M.seal(oneItem([{
  contig: L0.contig, pos: declaredPos + 5, ref: win[extraAt + 5], alt: "T",
  why: "a different silent edit"
}]));
check("declaring a DIFFERENT edit does not excuse this one",
  (await M.checkSealed(wrongDeclared, oneRec, refFor)).verdict, "held");

// An item with no local reference must not be silently passed.
const foreign = await M.seal({
  ...M.build([L0], {}),
  items: [{ gene: "XYZ", contig: "chr22", pos: 100, ref: "A", alt: "T",
            hgvsp: "p.?", span: { from: 50, to: 150, length: 101 } }]
});
const fres = await M.checkSealed(foreign, clean, refFor);
check("unresolvable item is held, not passed", fres.verdict, "held");
check("unresolvable item is reported", fres.unresolved.length, 1);

console.log(`\n${fails ? fails + " FAILED" : "all checks passed"}`);
process.exit(fails ? 1 : 0);
