/* Interface audit: contrast, structure, names, targets, motion.
 *
 * Checks the built page rather than the source, because what ships is what the
 * reader gets. Contrast is computed from resolved styles, so a token that looks
 * fine in isolation is judged against the surface it actually sits on.
 */
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

const b = await chromium.launch({ channel: "chrome", headless: true });
const p = await (await b.newContext({ viewport: { width: 1600, height: 1000 } })).newPage();
const errs = [];
p.on("pageerror", (e) => errs.push(String(e.message).slice(0, 140)));
await p.goto("file:///" + path.join(dir, "dist/preview.html").split(String.fromCharCode(92)).join("/"),
  { waitUntil: "networkidle" });
await p.waitForTimeout(2200);
await p.click("#gclose");
await p.waitForTimeout(600);

const audit = await p.evaluate(() => {
  const lum = (c) => {
    const [r, g, bl] = c.map((v) => {
      v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
  };
  const parse = (s) => {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const n = m[1].split(",").map((x) => parseFloat(x));
    return { rgb: n.slice(0, 3), a: n.length > 3 ? n[3] : 1 };
  };
  // Walk up for the first opaque background, the way the eye does.
  const bgOf = (el) => {
    let e = el;
    while (e && e !== document.documentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0.55) return c.rgb;
      e = e.parentElement;
    }
    return [11, 16, 22];
  };
  const ratio = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };

  const lowContrast = [];
  const seen = new Set();
  document.querySelectorAll("body *").forEach((el) => {
    const txt = (el.childNodes.length && [...el.childNodes]
      .filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join("")) || "";
    if (!txt) return;
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || +cs.opacity === 0) return;
    const fg = parse(cs.color);
    if (!fg) return;
    const size = parseFloat(cs.fontSize);
    const bold = +cs.fontWeight >= 700;
    // WCAG large text: 18.66px bold, or 24px.
    const large = size >= 24 || (bold && size >= 18.66);
    const need = large ? 3 : 4.5;
    const r = ratio(fg.rgb, bgOf(el));
    if (r < need) {
      const key = cs.color + "|" + size + "|" + el.className;
      if (seen.has(key)) return;
      seen.add(key);
      lowContrast.push({ sample: txt.slice(0, 42), cls: String(el.className).slice(0, 36),
        px: +size.toFixed(1), ratio: +r.toFixed(2), need });
    }
  });

  const headings = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")]
    .map((h) => h.tagName + ": " + h.textContent.trim().slice(0, 40));

  const unnamed = [...document.querySelectorAll("button,select,textarea,[role=checkbox],a[href]")]
    .filter((el) => {
      const n = (el.getAttribute("aria-label") || el.textContent || "").trim();
      return !n && !el.getAttribute("aria-labelledby") && !el.getAttribute("title");
    }).map((el) => el.tagName + "#" + (el.id || el.className).slice(0, 30));

  const small = [...document.querySelectorAll("button,select,[role=checkbox]")]
    .map((el) => ({ id: el.id || String(el.className).slice(0, 26),
                    w: Math.round(el.getBoundingClientRect().width),
                    h: Math.round(el.getBoundingClientRect().height) }))
    .filter((x) => x.w > 0 && (x.h < 32 || x.w < 32));

  const live = [...document.querySelectorAll("[aria-live],[role=status],[role=alert]")]
    .map((el) => (el.id || el.className) + " → " + (el.getAttribute("aria-live") || el.getAttribute("role")));

  return {
    lowContrast: lowContrast.sort((a, b) => a.ratio - b.ratio).slice(0, 14),
    lowContrastCount: lowContrast.length,
    headings, unnamed, smallTargets: small.slice(0, 10), liveRegions: live,
    hasLang: !!document.documentElement.lang,
    focusVisibleRule: [...document.styleSheets].some((s) => {
      try { return [...s.cssRules].some((r) => (r.selectorText || "").includes(":focus-visible")); }
      catch { return false; }
    })
  };
});

console.log(JSON.stringify(audit, null, 1));
console.log("page errors:", errs.length ? errs : "none");
await b.close();
