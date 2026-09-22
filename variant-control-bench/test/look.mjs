import { chromium } from "file:///C:/Users/ardit/AppData/Local/Temp/claude/C--Users-ardit--tri-ai/8f9f1029-5db4-43cb-bb87-26b1496576ac/scratchpad/node_modules/playwright/index.mjs";
import fs from "node:fs";
import path from "node:path";
const dir = process.cwd();
const frag = fs.readFileSync(path.join(dir, "dist/index.html"), "utf8");
fs.writeFileSync(path.join(dir, "dist/preview.html"),
  "<!doctype html><html lang='en'><head><meta charset='utf-8'>" +
  "<meta name='viewport' content='width=device-width,initial-scale=1'>" +
  "<style>body{margin:0;background:#fafaf9}[hidden]{display:none!important}</style>" +
  "</head><body>" + frag + "</body></html>");
const w = Number(process.argv[3] || 1600), h = Number(process.argv[4] || 1000);
const b = await chromium.launch({ channel: "chrome", headless: true });
const p = await (await b.newContext({ viewport: { width: w, height: h },
  deviceScaleFactor: 1 })).newPage();
const errs = []; p.on("pageerror", e => errs.push(String(e.message).slice(0, 160)));
await p.goto("file:///" + path.join(dir, "dist/preview.html").split(String.fromCharCode(92)).join("/"),
  { waitUntil: "networkidle" });
await p.waitForTimeout(2500);
try { await p.click("#gclose", { timeout: 1500 }); } catch {}
await p.waitForTimeout(800);
const out = process.argv[2] || "dist/look.png";
await p.screenshot({ path: out, fullPage: process.argv[5] !== "viewport" });
console.log("wrote", out, "errors:", errs.length ? errs : "none");
await b.close();
