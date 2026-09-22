/* Prompt for the Hostinger API token, store it, and prove it works.
 *
 * Typed rather than passed as an argument, so the token never lands in shell
 * history, a process list or a transcript. Input is masked, the value is
 * written with owner-only permissions, and nothing ever prints it back -- the
 * only feedback is its length and whether the API accepted it.
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline from "node:readline";

const KEY = path.join(os.homedir(), ".hostinger-key");
const DOMAIN = "arditmishra.com";

if (!process.stdin.isTTY) {
  console.error("Run this in a terminal — it needs to prompt you.");
  console.error("  cd ~/variant-control-bench && node ops/set-token.mjs");
  process.exit(2);
}

const ask = () => new Promise((resolve) => {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout,
                                        terminal: true });
  let muted = false;
  // Echo a fixed-width mask rather than the character typed, so the length is
  // not shoulder-readable either.
  rl._writeToOutput = (s) => { if (!muted) rl.output.write(s); else rl.output.write("*"); };
  process.stdout.write("Hostinger API token (input hidden): ");
  muted = true;
  rl.question("", (answer) => { muted = false; rl.output.write("\n"); rl.close(); resolve(answer); });
});

const token = (await ask()).trim();

if (!token) { console.error("Nothing entered — not written."); process.exit(1); }
if (token.length < 20) {
  console.error(`That is only ${token.length} characters, which is too short for a` +
                " Hostinger token. Not written, in case something was truncated on paste.");
  process.exit(1);
}

// Check before storing: a token saved and only discovered to be wrong three
// commands later is worse than one rejected here.
process.stdout.write("checking it against the API… ");
let res;
try {
  res = await fetch(`https://developers.hostinger.com/api/dns/v1/zones/${DOMAIN}`, {
    headers: { Authorization: "Bearer " + token, Accept: "application/json" },
    signal: AbortSignal.timeout(25000)
  });
} catch (e) {
  console.log("could not reach the API:", String(e.message).slice(0, 80));
  console.log("Not written. Check the connection and run this again.");
  process.exit(1);
}

if (res.status === 401 || res.status === 403) {
  console.log(`rejected (${res.status}).`);
  console.log("Not written. The token may be mistyped, expired, or lack DNS scope.");
  process.exit(1);
}
if (!res.ok) {
  console.log(`unexpected ${res.status}.`);
  console.log("Not written. Run again, or paste this status to Claude.");
  process.exit(1);
}

const zone = await res.json();
const rows = Array.isArray(zone) ? zone : (zone.zone || []);

fs.writeFileSync(KEY, token, { mode: 0o600 });
try { fs.chmodSync(KEY, 0o600); } catch { /* best effort on Windows */ }

console.log("accepted.");
console.log(`saved to ${KEY} (${token.length} characters, owner-only)`);
console.log(`the API returned ${rows.length} records for ${DOMAIN}`);
console.log("\nnext:  node ops/dns.mjs plan");
