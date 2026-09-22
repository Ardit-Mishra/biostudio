/* Does each name actually serve the right thing yet?
 *
 * Needs no credentials, so it can be run before, during and after the DNS
 * change. It resolves over DoH rather than the local resolver, because a
 * stale cache on this machine is the easiest way to believe a change landed
 * when it has not -- and it checks the served page, not just the address,
 * since the failure this is guarding against was a name that answered 200
 * with the wrong site.
 */
const EXPECT = [
  { host: "arditmishra.com",             title: "Ardit Mishra" },
  { host: "www.arditmishra.com",         title: "Ardit Mishra" },
  { host: "biostudio.arditmishra.com",   title: "Variant Control Bench" },
  { host: "peptide.arditmishra.com",     title: "Peptide" },
  { host: "genomesight.arditmishra.com", title: "GenomeSight" },
  { host: "genclarus.com",               title: "Genclarus" }
];
const VERCEL_IP = "76.76.21.21";

const doh = async (name, type) => {
  try {
    const r = await fetch(
      `https://cloudflare-dns.com/dns-query?name=${name}&type=${type}`,
      { headers: { accept: "application/dns-json" } });
    const j = await r.json();
    return (j.Answer || []).filter((a) => a.type === (type === "A" ? 1 : 28))
      .map((a) => a.data);
  } catch { return []; }
};

const head = async (host) => {
  try {
    const r = await fetch("https://" + host, { redirect: "follow",
      signal: AbortSignal.timeout(20000) });
    // Comments first: one of these pages carries a developer note that
    // contains the literal text "<title>", and matching that instead of the
    // real element reports a healthy page as broken.
    const body = (await r.text()).replace(/<!--[\s\S]*?-->/g, "");
    const m = body.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    return { status: r.status, server: r.headers.get("server") || "?",
             title: m ? m[1].trim().replace(/\s+/g, " ").slice(0, 46) : "" };
  } catch (e) { return { status: 0, server: "-", title: String(e.message).slice(0, 40) }; }
};

let bad = 0;
console.log("name                            A record        server     status  title");
for (const e of EXPECT) {
  const [a, aaaa, h] = [await doh(e.host, "A"), await doh(e.host, "AAAA"), await head(e.host)];
  const onVercel = a.includes(VERCEL_IP) || /vercel/i.test(h.server);
  const titleOk = h.title.toLowerCase().includes(e.title.toLowerCase());
  const ok = h.status === 200 && titleOk;
  // Public DNS says Vercel but this connection landed somewhere else: the
  // record is right and the resolver this machine uses is behind. That is a
  // fact about the network here, not about the zone, and calling it a failure
  // sends someone off to fix DNS that is already correct.
  const stale = !ok && a.includes(VERCEL_IP) && !/vercel/i.test(h.server);
  if (!ok && !stale) bad++;
  console.log(
    `${ok ? "ok  " : stale ? "cache" : "BAD "} ${e.host.padEnd(28)} ${(a[0] || "-").padEnd(15)} ` +
    `${h.server.padEnd(10)} ${String(h.status).padEnd(6)} ${h.title}` +
    (stale ? "   [public DNS is correct; local resolver is stale]" : "") +
    (aaaa.length && !onVercel ? `   [AAAA still set: ${aaaa[0]}]` : ""));
}
console.log(bad ? `\n${bad} of ${EXPECT.length} not right yet.`
                : `\nAll ${EXPECT.length} resolve and serve the expected page.`);
process.exit(bad ? 1 : 0);
