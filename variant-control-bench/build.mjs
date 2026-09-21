/* Inline every module and the snapshotted data into one self-contained page.
 *
 * The bench ships as a single HTML file on purpose: the page has to run from a
 * static host with no build step and no network, so every dependency that is
 * ours is inlined and the only external requests are pinned CDN scripts.
 */
import fs from "node:fs";

const read = (p) => fs.readFileSync(p, "utf8");
const out = read("src/bench.template.html")
  .replace("/*__ENGINE__*/",   () => read("src/engine.js"))
  .replace("/*__FUZZ__*/",     () => read("src/fuzz.js"))
  .replace("/*__ADVISE__*/",   () => read("src/advise.js"))
  .replace("/*__MANIFEST__*/", () => read("src/manifest.js"))
  .replace("/*__ASSEMBLY__*/", () => read("src/assembly.js"))
  .replace("/*__ASMPANEL__*/", () => read("src/asm-panel.js"))
  .replace("/*__DATA__*/",     () => read("data/bench-data.json"));

fs.mkdirSync("dist", { recursive: true });
fs.writeFileSync("dist/index.html", out, "utf8");
console.log("built dist/index.html  " + (out.length / 1024).toFixed(0) + " KB");
