import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const A = require("../src/assembly.js");
const data = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));

let fails = 0;
const chk = (name, got, want) => {
  const ok = got === want; if (!ok) fails++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name.padEnd(56)} got=${got} want=${want}`);
};

const plans = data.loci.map((L) => A.plan(L));
console.log("planned constructs:");
for (const p of plans) {
  console.log(`  ${p.gene.padEnd(7)} ${String(p.length).padStart(3)} nt  ` +
    `parts ${p.parts.length}  oh5=${p.overhang5} oh3=${p.overhang3}`);
}
console.log();

// A construct delivered exactly as planned must pass.
for (const p of plans) chk(`${p.gene}: exact delivery passes`, A.checkConstruct(p, p.sequence).verdict, "released");

// One base changed inside a homology arm is not a requested edit.
const p0 = plans[0];
const armPart = p0.parts.find((x) => x.id === "arm5");
const armMut = p0.sequence.slice(0, armPart.from + 5) +
  (p0.sequence[armPart.from + 5] === "A" ? "C" : "A") + p0.sequence.slice(armPart.from + 6);
const armRes = A.checkConstruct(p0, armMut);
chk("edit hidden in a homology arm is caught", armRes.verdict, "held");
chk("  and is labelled as an arm edit", armRes.rows.some((r) => r.status === "armedit"), true);

// A construct whose payload region carries the enzyme site cannot assemble,
// even though every base of the requested variant is present.
const pay = p0.parts.find((x) => x.id === "payload");
const withSite = p0.sequence.slice(0, pay.from) + "GGTCTC" + p0.sequence.slice(pay.from);
const siteRes = A.checkConstruct(p0, withSite);
chk("internal BsaI site is caught", siteRes.rows.some((r) => r.status === "uncuttable"), true);
chk("  and the construct is held", siteRes.verdict, "held");

// Do any of the five real loci already contain a site? Worth knowing.
const enz = A.ENZYMES.BsaI;
for (const p of plans) {
  const interior = p.sequence.slice(p.parts[0].to, p.parts[4].from);
  const hits = A.findSites(interior, enz);
  if (hits.length) console.log(`  NOTE ${p.gene} interior already contains a BsaI site`, hits);
}

// Overhangs must be distinct across the pool.
const pool = A.checkPool(plans);
chk("real five-locus pool has unique overhangs", pool.verdict, "released");
const collide = A.checkPool([plans[0], { ...plans[1], gene: "CLONE", overhang5: plans[0].overhang5 }]);
chk("a duplicated overhang is caught", collide.verdict, "held");

console.log(`\n${fails ? fails + " FAILED" : "all checks passed"}`);
process.exit(fails ? 1 : 0);
