/* Record the adversarial campaign as a dated, replayable figure.
 *
 * The page cannot fetch anything, so the number it shows at rest has to be
 * baked in. Baking in a number is only honest if the reader can reproduce it,
 * which is why this writes the seed range as well as the counts: pressing
 * Start campaign in the page replays the same seeds through the same operators
 * and must land on the same figure.
 */
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const F = require("../src/fuzz.js");

const data = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const N = Number(process.argv[2] || 20000);
const START = Number(process.argv[3] || 1);

let run = 0, declined = 0, fp = 0, fh = 0, reclassified = 0;
const ops = {};
for (let seed = START; seed < START + N; seed++) {
  const a = F.attempt(data.loci, data.decoy, seed);
  if (!a) { declined++; continue; }
  run++;
  ops[a.op] = (ops[a.op] || 0) + 1;
  if (a.misdeclared) reclassified++;
  if (a.failure === "false pass") fp++;
  if (a.failure === "false hold") fh++;
}

const out = {
  attempts: run, declined, falsePass: fp, falseHold: fh, reclassified,
  seedFrom: START, seedTo: START + N - 1,
  operators: Object.keys(ops).length,
  corrupting: F.CORRUPTING.length, preserving: F.PRESERVING.length,
  recorded: new Date().toISOString().slice(0, 10)
};
fs.writeFileSync("data/campaign.json", JSON.stringify(out, null, 1) + "\n");
console.log(JSON.stringify(out, null, 1));
if (fp || fh) process.exit(1);
