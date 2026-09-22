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
// Records that must not survive. The apex is served by an ALIAS -- Hostinger's
// CNAME-flattening record -- so adding an A record beside it leaves two answers
// for the same name and the ALIAS goes on winning: the change would read as
// applied and nothing would move. AAAA is listed because an apex AAAA would
// quietly take precedence for anyone whose network prefers IPv6; this zone has
// none today, and the entry costs nothing if one appears later.
const DROP = [
  { name: "@",   type: "ALIAS" },
  { name: "@",   type: "AAAA" },
  { name: "www", type: "CNAME" }
];

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
let ok = false;

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
  ok = true;
}

if (cmd === "apply") {
  const before = await getZone();
  if (!before.ok) { console.error(`GET zone failed: ${before.status}`); process.exit(1); }
  const file = backup(before.json);
  console.log("backed up live zone to", file);
  const rows = Array.isArray(before.json) ? before.json : (before.json.zone || []);

  // PUT with overwrite:true replaces records matching name+type and leaves
  // everything else alone -- it does not rewrite the zone. So omitting a
  // record does not delete it, and the old CNAME on www would survive to
  // collide with the A record going in. Deletions are their own call, and
  // they have to happen first: a name cannot hold a CNAME and an A at once.
  const toDrop = DROP.filter((x) =>
    rows.some((r) => r.name === x.name && r.type === x.type));
  if (toDrop.length) {
    const del = await call("DELETE", `${API}/zones/${DOMAIN}`,
      { filters: toDrop.map((x) => ({ name: x.name, type: x.type })) });
    console.log(del.ok
      ? "removed: " + toDrop.map((x) => x.type + " " + x.name).join(", ")
      : `DELETE failed: ${del.status}`);
    if (!del.ok) {
      console.error(del.text.slice(0, 400));
      console.log("nothing else attempted; zone is as it was.");
      process.exitCode = 1;
      ok = true;
    }
  } else {
    console.log("nothing to remove");
  }

  if (process.exitCode !== 1) {
    const res = await call("PUT", `${API}/zones/${DOMAIN}`, {
      overwrite: true,
      zone: WANT.map((w) => ({
        name: w.name, type: w.type, ttl: 3600, records: [{ content: w.content }]
      }))
    });
    console.log(res.ok ? "wrote " + WANT.length + " records" : `PUT failed: ${res.status}`);
    if (!res.ok) { console.error(res.text.slice(0, 400)); process.exitCode = 1; }
    else {
      // "Nothing else was touched" is a claim, so check it: read the zone back
      // and account for every record that existed before.
      const after = await getZone();
      const now = Array.isArray(after.json) ? after.json : (after.json.zone || []);
      const key = (r) => r.type + " " + r.name;
      const content = (r) => (r.records || []).map((x) => x.content).sort().join(" | ");
      const nowBy = new Map(now.map((r) => [key(r), content(r)]));

      let lost = 0, changed = 0, kept = 0;
      rows.forEach((r) => {
        if (DROP.some((x) => x.name === r.name && x.type === r.type)) return;
        if (WANT.some((w) => w.name === r.name && w.type === r.type)) return;
        if (!nowBy.has(key(r))) { console.log("  LOST     " + key(r)); lost++; }
        else if (nowBy.get(key(r)) !== content(r)) { console.log("  CHANGED  " + key(r)); changed++; }
        else kept++;
      });
      console.log("");
      console.log(`untouched records verified: ${kept} identical, ${changed} changed, ${lost} lost`);

      const mail = now.filter((r) => r.type === "MX" ||
        (r.type === "TXT" && /spf|dmarc/i.test(content(r))) || /domainkey|auto/.test(r.name));
      console.log(`mail records present after write: ${mail.length}`);
      mail.forEach((r) => console.log("  " + key(r)));

      const gone = DROP.filter((x) => nowBy.has(x.type + " " + x.name));
      if (gone.length) console.log("still present, expected removed: " +
        gone.map((x) => x.type + " " + x.name).join(", "));

      console.log("");
      if (lost || changed || gone.length) {
        console.log("Something moved that should not have. Restore with:");
        console.log("  node ops/dns.mjs restore " + path.basename(file));
        process.exitCode = 1;
      } else {
        console.log("restore if needed:  node ops/dns.mjs restore " + path.basename(file));
      }
    }
  }
  ok = true;
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
  ok = true;
}

if (!ok) {
  console.error("unknown command: " + cmd);
  process.exitCode = 2;
}
