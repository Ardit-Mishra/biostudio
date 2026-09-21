/* Model routing for the composer: OmniRoute first, freellmapi as fallback.
 *
 * Both expose an OpenAI-compatible /v1, so one client covers them and the only
 * real difference is which base URL and key answer. Whichever one served a
 * request is recorded on the response and ends up in the run evidence, because
 * "which model drafted this" is provenance, not a detail.
 *
 * Nothing here is trusted. Whatever a model returns goes through the same
 * verifier as everything else -- that is the entire reason an LLM is allowed
 * anywhere near this pipeline.
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// A key may come from the environment or from a one-line file, so it can be
// pasted once and picked up by later runs without re-exporting it in a shell.
// The file is read at call time and its contents are never logged.
function fromFile(name) {
  try {
    const p = path.join(os.homedir(), name);
    if (!fs.existsSync(p)) return undefined;
    const v = fs.readFileSync(p, "utf8").trim();
    return v || undefined;
  } catch { return undefined; }
}

export const KEY_FILES = { omniroute: ".omniroute-key", freellmapi: ".freellmapi-key" };

export const BACKENDS = [
  {
    id: "omniroute",
    baseUrl: process.env.OMNIROUTE_BASE_URL || "http://127.0.0.1:3000/v1",
    key: () => process.env.OMNIROUTE_API_KEY || process.env.OMNIROUTE_KEY ||
               fromFile(KEY_FILES.omniroute),
    keyName: "OMNIROUTE_API_KEY",
    keyFile: "~/" + KEY_FILES.omniroute,
    note: "local OmniRoute gateway"
  },
  {
    id: "freellmapi",
    baseUrl: process.env.FREELLMAPI_BASE_URL || "http://127.0.0.1:3001/v1",
    key: () => process.env.FREELLMAPI_KEY || process.env.FREELLM_API_KEY ||
               fromFile(KEY_FILES.freellmapi),
    keyName: "FREELLMAPI_KEY",
    keyFile: "~/" + KEY_FILES.freellmapi,
    note: "local freellmapi router (unified freellmapi-… token)"
  }
];

async function call(backend, path, init = {}, timeoutMs = 45000) {
  const key = backend.key();
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const r = await fetch(backend.baseUrl + path, {
      ...init,
      signal: ctl.signal,
      headers: {
        "Content-Type": "application/json",
        ...(key ? { Authorization: "Bearer " + key } : {}),
        ...(init.headers || {})
      }
    });
    const text = await r.text();
    let body;
    try { body = JSON.parse(text); } catch { body = { _raw: text.slice(0, 400) }; }
    return { ok: r.ok, status: r.status, body, routedVia: r.headers.get("x-routed-via") };
  } catch (e) {
    return { ok: false, status: 0, body: { error: { message: String(e.message || e) } } };
  } finally {
    clearTimeout(timer);
  }
}

/** Which backends are reachable, and whether a usable credential is present. */
export async function probe() {
  const out = [];
  for (const b of BACKENDS) {
    const hasKey = Boolean(b.key());
    const r = await call(b, "/models", { method: "GET" }, 8000);
    const models = Array.isArray(r.body?.data) ? r.body.data.map((m) => m.id) : [];
    out.push({
      id: b.id, baseUrl: b.baseUrl, hasKey, keyName: b.keyName, keyFile: b.keyFile, note: b.note,
      reachable: r.status !== 0,
      authed: r.ok,
      status: r.status,
      detail: r.ok ? `${models.length} models` : (r.body?.error?.message || "unreachable"),
      models
    });
  }
  return out;
}

/** First backend that is reachable AND authenticated. */
export async function pick() {
  for (const b of BACKENDS) {
    if (!b.key()) continue;
    const r = await call(b, "/models", { method: "GET" }, 8000);
    if (r.ok) return b;
  }
  return null;
}

/**
 * One chat completion. `model` may be an explicit id, or "auto" / "auto:fast"
 * / "auto:smart" where the backend supports a routing profile.
 */
export async function chat({ backend, model, system, user, temperature = 0, maxTokens = 1400, timeoutMs = 45000 }) {
  const started = Date.now();
  const r = await call(backend, "/chat/completions", {
    method: "POST",
    body: JSON.stringify({
      model,
      temperature,
      max_tokens: maxTokens,
      messages: [
        ...(system ? [{ role: "system", content: system }] : []),
        { role: "user", content: user }
      ]
    })
  }, timeoutMs);
  return {
    ok: r.ok,
    status: r.status,
    ms: Date.now() - started,
    text: r.body?.choices?.[0]?.message?.content ?? null,
    error: r.ok ? null : (r.body?.error?.message || `HTTP ${r.status}`),
    provenance: {
      backend: backend.id,
      baseUrl: backend.baseUrl,
      model,
      routedVia: r.routedVia || r.body?.model || null,
      usage: r.body?.usage || null
    }
  };
}
