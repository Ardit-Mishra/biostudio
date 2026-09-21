/* Cross-model composer campaign.
 *
 * Asks each routed model to draft the alternate fragment for a locus, then puts
 * every draft through the SAME verifier used everywhere else. Two numbers come
 * out, and the second one is the point:
 *
 *   draft accuracy   - how often a model produced a correct fragment. Expected
 *                      to vary a lot between models.
 *   verifier verdict - whether the verifier's accept/reject matched the truth.
 *                      Expected not to vary at all, because the guarantee is
 *                      supposed to come from the checker, not from the model.
 *
 * A model is never asked whether its own output is right, and the verifier is
 * never told which model produced what.
 *
 * Usage:  node composer/llm-campaign.mjs [--models a,b,c] [--loci 3] [--probe]
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { probe, pick, chat } from "./router.mjs";

const require = createRequire(import.meta.url);
const here = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
const E = require(path.join(here, "..", "src", "engine.js"));
const DATA = JSON.parse(fs.readFileSync(path.join(here, "..", "data", "bench-data.json"), "utf8"));

const argv = process.argv.slice(2);
const arg = (n, d) => {
  const i = argv.indexOf("--" + n);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : d;
};

const SYSTEM =
  "You design DNA fragments for synthesis. You answer with sequence only: one line, " +
  "uppercase A/C/G/T, no FASTA header, no explanation, no code fences.";

function promptFor(L) {
  return [
    `Reference window, GRCh38 ${L.contig}:${L.window.from}-${L.window.to} (1-based, forward strand):`,
    L.window.seq,
    "",
    `Apply exactly this one edit and return the resulting sequence:`,
    `  position ${L.pos}  ref ${L.ref}  alt ${L.alt}`,
    "",
    "Change nothing else. Return only the edited sequence."
  ].join("\n");
}

function cleanSeq(text) {
  if (!text) return null;
  const m = String(text).toUpperCase().replace(/```[A-Z]*/g, "").match(/[ACGTN\s]{40,}/);
  if (!m) return null;
  const s = m[0].replace(/[^ACGTN]/g, "");
  return s.length >= 40 ? s : null;
}

// What the fragment SHOULD be, computed locally. Used only to score the model,
// never shown to the verifier.
function truthFor(L) {
  const w = L.window.seq, f = L.window.flank;
  return w.slice(0, f) + L.alt + w.slice(f + L.ref.length);
}

function verifyOne(L, seq) {
  const W = [{ key: L.gene, gene: L.gene, contig: L.contig, from: L.window.from, seq: L.window.seq }];
  const byKey = { [L.contig + ":" + L.gene]: W[0] };
  const fasta = ">draft\n" + seq + "\n";
  const findings = E.verify(fasta, W);                      // sequence + reference only
  const rows = E.reconcile(
    [{ gene: L.gene, contig: L.contig, pos: L.pos, ref: L.ref, alt: L.alt, hgvsp: L.hgvsp }],
    findings, byKey);
  const bad = rows.filter((r) => r.status !== "match").length;
  return { verdict: bad ? "held" : "released", rows, discrepancies: bad };
}

const main = async () => {
  const status = await probe();
  console.log("backends");
  for (const b of status) {
    console.log(`  ${b.id.padEnd(11)} ${b.baseUrl.padEnd(30)} key:${b.hasKey ? "yes" : "no "} ` +
      `reachable:${b.reachable ? "yes" : "no "} authed:${b.authed ? "yes" : "no "}  ${b.detail}${b.hasKey ? "" : "  (key file " + b.keyFile + ")"}`);
  }
  if (argv.includes("--probe")) return;

  const backend = await pick();
  if (!backend) {
    console.log("\nNo backend is both reachable and authenticated, so no models were called.");
    const need = status.filter((b) => b.reachable && !b.authed).map((b) => b.keyName);
    if (need.length) {
      console.log("Export a key and re-run, e.g.:");
      for (const n of new Set(need)) console.log(`  export ${n}=...`);
      console.log("or paste the token on one line into the matching key file:");
      for (const b of status) if (b.reachable && !b.authed) console.log(`  ${b.keyFile}`);
      console.log("A freellmapi token is minted in its dashboard at http://127.0.0.1:3001 .");
    }
    process.exitCode = 2;
    return;
  }
  console.log(`\nusing ${backend.id} at ${backend.baseUrl}\n`);

  const models = arg("models", "auto:fast,auto,auto:smart").split(",").map((s) => s.trim());
  const loci = DATA.loci.slice(0, Number(arg("loci", 5)));
  const table = [];

  for (const model of models) {
    const row = { model, drafted: 0, correctDraft: 0, verdictRight: 0, n: 0, ms: 0, routed: new Set() };
    for (const L of loci) {
      row.n++;
      // Free tiers rate-limit hard, and a burst just turns the whole run into
      // cooldown errors. --delay spaces the calls out.
      const wait = Number(arg("delay", 0));
      if (wait && row.n > 1) await new Promise((r) => setTimeout(r, wait * 1000));

      // Free tiers answer "rate-limited, soonest reset ~Ns" and transient 503s.
      // Neither is a result, so honour the stated cooldown and try again rather
      // than recording a model as having failed the task.
      const TMO = Number(arg("timeout", 45)) * 1000;
      let r = await chat({ backend, model, system: SYSTEM, user: promptFor(L), timeoutMs: TMO });
      for (let attempt = 0; attempt < Number(arg("retries", 3)); attempt++) {
        const msg = (r.text ? "" : (r.error || "")) + (r.text || "");
        const cooling = /rate-limited|on cooldown|high demand|503|exhausted/i.test(msg);
        if (r.text || !cooling) break;
        const m = msg.match(/reset ~(\d+)s/);
        const pause = Math.min(90, m ? Number(m[1]) + 3 : 15);
        console.log(`  ${model} / ${L.gene}: cooling down ${pause}s, retry ${attempt + 1}`);
        await new Promise((res) => setTimeout(res, pause * 1000));
        r = await chat({ backend, model, system: SYSTEM, user: promptFor(L), timeoutMs: TMO });
      }
      row.ms += r.ms;
      if (r.provenance.routedVia) row.routed.add(r.provenance.routedVia);
      const seq = cleanSeq(r.text);
      if (!seq) { console.log(`  ${model} / ${L.gene}: no usable sequence (${r.error || "unparseable"})`); continue; }
      row.drafted++;

      const isCorrect = seq === truthFor(L);
      if (isCorrect) row.correctDraft++;
      const v = verifyOne(L, seq);
      // The verifier is right when it releases a correct draft and holds a wrong one.
      const shouldRelease = isCorrect;
      if ((v.verdict === "released") === shouldRelease) row.verdictRight++;
      else console.log(`  ** ${model} / ${L.gene}: draft ${isCorrect ? "correct" : "wrong"} ` +
        `but verifier said ${v.verdict}`);
    }
    table.push(row);
    // Verifier correctness is scored over drafts that actually arrived. A model
    // that returned nothing gave the verifier nothing to be right or wrong about.
    console.log(`${model.padEnd(22)} drafted ${row.drafted}/${row.n}  ` +
      `correct ${row.correctDraft}/${row.drafted || "-"}  ` +
      `verifier right ${row.verdictRight}/${row.drafted || "-"}  ` +
      `${Math.round(row.ms / Math.max(row.n, 1))} ms/call`);
  }

  console.log("\n--- the claim this measures ---");
  const scored = table.filter((r) => r.drafted > 0);
  if (!scored.length) {
    console.log("No model returned a usable sequence, so nothing was measured.");
    return;
  }
  const drafts = scored.map((r) => r.correctDraft / r.drafted);
  const verd = scored.map((r) => r.verdictRight / r.drafted);
  const spread = (a) => (Math.max(...a) - Math.min(...a)) * 100;
  console.log(`models that answered                : ${scored.length}/${table.length}`);
  console.log(`draft accuracy spread across models : ${spread(drafts).toFixed(0)} points ` +
    `(${(Math.min(...drafts) * 100).toFixed(0)}%-${(Math.max(...drafts) * 100).toFixed(0)}%)`);
  console.log(`verifier correctness spread         : ${spread(verd).toFixed(0)} points`);
  console.log(verd.every((v) => v === 1)
    ? "The verifier was right for every model that answered. Draft quality moved; the guarantee did not."
    : "The verifier was NOT right for every model - that is a defect in the checker, not the models.");

  fs.writeFileSync(path.join(here, "..", "data", "llm-campaign-result.json"), JSON.stringify(
    table.map((r) => ({ ...r, routed: [...r.routed] })), null, 1));
};

main();
