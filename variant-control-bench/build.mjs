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
  .replace("/*__DATA__*/",     () => read("data/bench-data.json"))
  .replace("/*__CAMPAIGN__*/", () => read("data/campaign.json"));

fs.mkdirSync("dist", { recursive: true });
fs.writeFileSync("dist/index.html", out, "utf8");
console.log("built dist/index.html  " + (out.length / 1024).toFixed(0) + " KB");

/* dist/index.html is a FRAGMENT. The artifact host supplies the document
   wrapper, a static host does not, and a fragment served directly is at the
   mercy of quirks-mode defaults. Same bytes, second envelope, one source. */
const page = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Construct-order verification: a separate verifier re-derives the requested edits from exported DNA sequence alone, and holds the order until it can.">
<style>html,body{margin:0;height:100%;background:#0b1016}[hidden]{display:none!important}</style>
</head>
<body>
${out}
</body>
</html>
`;
fs.mkdirSync("site", { recursive: true });
fs.writeFileSync("site/index.html", page, "utf8");
console.log("built site/index.html   " + (page.length / 1024).toFixed(0) + " KB  (standalone)");
