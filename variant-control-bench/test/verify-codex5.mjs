/* Independent reproduction of the two points left open after the fourth
   review. Ground truth is constructed here; nothing asks the verifier or the
   campaign what the answer should be. */
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const E = require("../src/engine.js");
const F = require("../src/fuzz.js");

const D = JSON.parse(fs.readFileSync("data/bench-data.json", "utf8"));
const L = D.loci[0], s = L.window.seq, from = L.window.from, flank = L.window.flank;
const fa = (seq, n) => ">" + (n || "frag") + "\n" + seq + "\n";

let real = 0, total = 0;
const say = (id, claim, reproduced, note) => {
  total++; if (reproduced) real++;
  console.log(`${reproduced ? "REAL " : "fixed"}  ${id}  ${claim}${note ? "  [" + note + "]" : ""}`);
};

// S1 - delivered coverage is aggregated across every record that landed on the
// window, so one record covers for another. A molecule short at the tail stops
// being reported the moment a second record reaches the tail: the report names
// the extra record and says nothing about the truncation. The extra record is
// the easy half to fix. Re-shipping the same short molecule is the half that
// costs an experiment.
{
  const W = { key: "s1", gene: L.gene, contig: L.contig, from, seq: s };
  const byKey = {}; byKey[L.contig + ":" + L.gene] = W;
  const edited = s.slice(0, flank) + L.alt + s.slice(flank + L.ref.length);
  const req = [{ gene: L.gene, contig: L.contig, pos: L.pos, ref: L.ref, alt: L.alt,
                 hgvsp: L.hgvsp }];
  const run = (txt) => E.reconcile(req, E.verify(txt, [W]), byKey);

  const alone = run(fa(edited.slice(0, 79), "a"));
  const withCopy = run(fa(edited.slice(0, 79), "a") + fa(s.slice(60), "b"));
  const short = (rows) => rows.some((r) => r.status === "short");

  say("S1", "a second record conceals the first record's truncation",
      short(alone) && !short(withCopy),
      `alone ${alone.map((r) => r.status).join(",")} | with copy ` +
      withCopy.map((r) => r.status).join(","));
}

// S2 - the campaign assigns ground truth from which array an operator was
// declared in. Reverse-complementing a molecule that is its own reverse
// complement changes nothing, so the file still encodes exactly what was
// ordered - but the attempt is scored as though it had been damaged, and the
// verifier is recorded as having committed a false pass it did not commit.
{
  const half = s.slice(0, 40);
  const mol = half + E.revcomp(half);                  // palindromic molecule
  const alt = mol[20] === "A" ? "C" : "A";
  const win = mol.slice(0, 20) + alt + mol.slice(21);  // reference differs by one base
  const P = { gene: "PAL", contig: "chrP", pos: from + 20, ref: alt, alt: mol[20],
              hgvsp: "p.Pal1Pal", window: { from, to: from + win.length - 1,
              flank: 20, seq: win } };
  const isPal = E.revcomp(mol) === mol;

  let seen = null;
  for (let seed = 1; seed < 4000 && !seen; seed++) {
    const a = F.attempt([P], D.decoy, seed);
    if (a && a.op === "revcomp") seen = a;
  }
  say("S2", "reverse-complementing a palindromic molecule is scored as damage",
      !!seen && isPal && seen.expected === "held",
      seen ? `expected ${seen.expected}, verifier said ${seen.verdict}, ` +
             `scored ${seen.ok ? "ok" : seen.failure}` : "operator never drawn");
}

// S2b - the same unchecked precondition on the other operator that rebuilds a
// record from the reference: if the ordered molecule already IS the reference,
// delivering the reference is not an omission.
{
  const ops = F.CORRUPTING.filter((o) => o.id === "revcomp" || o.id === "refOnly");
  say("S2b", "operators declare a class without checking it holds for the draw",
      ops.length === 2 && !/molecules|multiset|unchanged/i.test(String(F.attempt)),
      "revcomp and refOnly both assume their draw damages the file");
}

console.log(`\n${real} of ${total} reproduce against the packaged build`);
