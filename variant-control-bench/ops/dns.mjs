/* Hostinger DNS zone operations for arditmishra.com.
 *
 * Reads the token from ~/.hostinger-key and never prints it. Every run that
 * changes anything writes the current zone to a timestamped backup first, so
 * a wrong edit is one restore away rather than a reconstruction from memory.
 *
 *   node ops/dns.mjs show              print the live zone
 *   node ops/dns.mjs plan              show what apply would change
 *   node ops/dns.mjs apply             back up, then write the records
 *   node ops/dns.mjs restore <file>    put a backup back
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DOMAIN = "arditmishra.com";
const API = "https://developers.hostinger.com/api/dns/v1";
const VERCEL_IP = "76.76.21.21";

// The records this project owns. Anything not named here -- MX, SPF, DKIM,
// verification TXT -- is left exactly as it is, which is the point of editing
// records instead of moving nameservers.
const WANT = [
  { name: "@",           type: "A", content: VERCEL_IP },
  { name: "www",         type: "A", content: VERCEL_IP },
  { name: "biostudio",   type: "A", content: VERCEL_IP },
  { name: "peptide",     type: "A", content: VERCEL_IP },
  { name: "genomesight", type: "A", content: VERCEL_IP }
];
// Records that must not survive: an AAAA on the apex silently wins for any
// visitor whose network prefers IPv6, so fixing only the A record would look
// fixed here and stay broken for them.
const DROP = [{ name: "@", type: "AAAA" }, { name: "www", type: "CNAME" }];

const keyFile = path.join(os.homedir(), ".hostinger-key");
if (!fs.existsSync(keyFile)) {
  console.error("No token at ~/.hostinger-key — create one in hPanel first.");
  process.exit(2);
}
const token = fs.readFileSync(keyFile, "utf8").trim();
if (!token) { console.error("~/.hostinger-key is empty."); process.exit(2); }

const call = async (method, url, body) => {
  const r = await fetch(url, {
    method,
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      Accept: "application/json"
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await r.text();
  let json = null;
  try { json = JSON.parse(text); } catch { /* keep the raw text */ }
  return { ok: r.ok, status: r.status, json, text };
};

const getZone = () => call("GET", `${API}/zones/${DOMAIN}`);

const backup = (zone) => {
  const dir = path.join(process.cwd(), "ops", "dns-backups");
  fs.mkdirSync(dir, { recursive: true });
  const f = path.join(dir, `zone-${new Date().toISOString().replace(/[:.]/g, "-")}.json`);
  fs.writeFileSync(f, JSON.stringify(zone, null, 1));
  return f;
};

const summarise = (zone) => {
  const rows = Array.isArray(zone) ? zone : (zone && zone.zone) || [];
  rows.forEach((r) => {
    const vals = (r.records || []).map((x) => x.content || x).join(", ");
    console.log(`  ${String(r.type).padEnd(6)} ${String(r.name).padEnd(14)} ${vals}`);
  });
  return rows;
};

const cmd = process.argv[2] || "show";

if (cmd === "show" || cmd === "plan") {
  const res = await getZone();
  if (!res.ok) {
    console.error(`GET zone failed: ${res.status}`);
    console.error(res.text.slice(0, 300));
    process.exit(1);
  }
  console.log(`Live zone for ${DOMAIN}:`);
  const rows = summarise(res.json);

  if (cmd === "plan") {
    console.log("\nWould set:");
    WANT.forEach((w) => {
      const cur = rows.find((r) => r.name === w.name && r.type === w.type);
      const now = cur ? (cur.records || []).map((x) => x.content).join(", ") : "(absent)";
      const same = now === w.content;
      console.log(`  ${same ? "=" : "~"} ${w.type} ${w.name.padEnd(14)} ${now}  ->  ${w.content}`);
    });
    console.log("\nWould remove:");
    DROP.forEach((d) => {
      const cur = rows.find((r) => r.name === d.name && r.type === d.type);
      console.log(`  ${cur ? "x" : "-"} ${d.type} ${d.name}  ${cur ? "present" : "already absent"}`);
    });
    const kept = rows.filter((r) =>
      !WANT.some((w) => w.name === r.name && w.type === r.type) &&
      !DROP.some((d) => d.name === r.name && d.type === r.type));
    console.log(`\nWould leave untouched (${kept.length}):`);
    kept.forEach((r) => console.log(`  ${r.type} ${r.name}`));
  }
  process.exit(0);
}

if (cmd === "apply") {
  const before = await getZone();
  if (!before.ok) { console.error(`GET zone failed: ${before.status}`); process.exit(1); }
  const file = backup(before.json);
  console.log("backed up live zone to", file);

  const rows = Array.isArray(before.json) ? before.json : (before.json.zone || []);
  const keep = rows.filter((r) =>
    !WANT.some((w) => w.name === r.name && w.type === r.type) &&
    !DROP.some((d) => d.name === r.name && d.type === r.type));
  const next = keep.concat(WANT.map((w) => ({
    name: w.name, type: w.type, ttl: 3600, records: [{ content: w.content }]
  })));

  const res = await call("PUT", `${API}/zones/${DOMAIN}`, { overwrite: true, zone: next });
  console.log(res.ok ? "zone written" : `PUT failed: ${res.status}`);
  if (!res.ok) { console.error(res.text.slice(0, 400)); process.exit(1); }
  console.log("restore with:  node ops/dns.mjs restore " + path.basename(file));
  process.exit(0);
}

if (cmd === "restore") {
  const name = process.argv[3];
  if (!name) { console.error("restore needs a backup filename"); process.exit(2); }
  const f = path.isAbsolute(name) ? name : path.join(process.cwd(), "ops", "dns-backups", name);
  const zone = JSON.parse(fs.readFileSync(f, "utf8"));
  const rows = Array.isArray(zone) ? zone : (zone.zone || []);
  const res = await call("PUT", `${API}/zones/${DOMAIN}`, { overwrite: true, zone: rows });
  console.log(res.ok ? "zone restored from " + f : `restore failed: ${res.status}`);
  if (!res.ok) { console.error(res.text.slice(0, 400)); process.exit(1); }
  process.exit(0);
}

console.error("unknown command: " + cmd);
process.exit(2);
