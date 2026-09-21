/* The frozen request manifest.
 *
 * Everything else in this bench checks an export the composer just produced.
 * That is the easy case. The job people actually have is the other one: a
 * vendor sends back a FASTA weeks later and someone has to say whether it is
 * the thing that was ordered.
 *
 * A manifest is that order, written down and sealed. It names the assembly,
 * each locus, each allele, the span that was ordered, and any additional edits
 * the order declared on purpose. Sealing hashes the canonical form, so the
 * check can state WHICH order a delivery was compared against rather than
 * asking anyone to take it on trust.
 *
 * The delivery is checked the same way as anything else: sequence and reference
 * go in, the edits are re-derived, and only then is the result compared to the
 * manifest. The manifest never reaches the recovery step.
 */
(function (root) {
  "use strict";

  var E = (typeof module !== "undefined" && module.exports)
    ? require("./engine.js") : root.VCEngine;

  // Stable serialisation: key order must not change a manifest's identity.
  function canonical(v) {
    if (v === null || typeof v !== "object") return JSON.stringify(v);
    if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
    return "{" + Object.keys(v).sort().map(function (k) {
      return JSON.stringify(k) + ":" + canonical(v[k]);
    }).join(",") + "}";
  }

  function sha256Hex(str) {
    if (typeof module !== "undefined" && module.exports) {
      return Promise.resolve(require("crypto").createHash("sha256").update(str, "utf8").digest("hex"));
    }
    if (root.crypto && root.crypto.subtle && root.TextEncoder) {
      return root.crypto.subtle.digest("SHA-256", new root.TextEncoder().encode(str))
        .then(function (b) {
          return Array.prototype.map.call(new Uint8Array(b), function (x) {
            return ("0" + x.toString(16)).slice(-2);
          }).join("");
        });
    }
    return Promise.resolve(null);
  }

  /** Build an unsealed manifest from the loci an order covers. */
  function build(loci, opts) {
    opts = opts || {};
    return {
      manifest_version: 1,
      assembly: opts.assembly || "GRCh38",
      reference_source: opts.source || "Ensembl REST /sequence/region",
      engine: E.VERSION,
      created: opts.created || new Date().toISOString(),
      items: loci.map(function (L) {
        var item = {
          gene: L.gene, contig: L.contig, pos: L.pos, ref: L.ref, alt: L.alt,
          hgvsp: L.hgvsp,
          span: { from: L.window.from, to: L.window.to, length: L.window.seq.length }
        };
        var p = (opts.permitted || []).filter(function (x) {
          return x.contig === L.contig && x.pos >= L.window.from && x.pos <= L.window.to;
        }).map(function (x) {
          // Required by default. A PAM-blocking edit named in the order is part
          // of the donor that was ordered, not something a vendor may skip.
          return Object.assign({ required: x.optional !== true }, x);
        });
        if (p.length) item.permitted = p;
        return item;
      })
    };
  }

  function body(m) {
    var c = {};
    Object.keys(m).forEach(function (k) { if (k !== "id") c[k] = m[k]; });
    return c;
  }

  /** Seal: attach the content hash. Two identical orders get the same id. */
  function seal(m) {
    return sha256Hex(canonical(body(m))).then(function (h) {
      m.id = h ? "sha256:" + h : null;
      return m;
    });
  }

  /** Re-derive the id and compare. Catches a manifest edited after sealing. */
  function verifySeal(m) {
    if (!m || !m.id) return Promise.resolve({ ok: false, reason: "manifest is not sealed" });
    return sha256Hex(canonical(body(m))).then(function (h) {
      var want = "sha256:" + h;
      return { ok: want === m.id, computed: want, declared: m.id,
               reason: want === m.id ? "seal matches" : "manifest changed after it was sealed" };
    });
  }

  function parse(text) {
    var m = JSON.parse(text);
    if (!m || m.manifest_version !== 1 || !Array.isArray(m.items))
      throw new Error("not a version 1 manifest");
    return m;
  }

  /**
   * Check a delivery against a sealed manifest.
   *
   * `refFor(item)` must return { from, seq } for that item's span, or null when
   * the reference is not held locally. An item whose reference is missing is
   * reported as unresolved rather than quietly passed or quietly failed.
   */
  // Async front door: verifies the seal, then checks. Callers that already know
  // the seal state can still call check() directly with opts.sealOk.
  function checkSealed(manifest, fasta, refFor, opts) {
    return verifySeal(manifest).then(function (seal) {
      var o = Object.assign({}, opts || {}, { sealOk: seal.ok });
      var res = check(manifest, fasta, refFor, o);
      res.seal = seal;
      return res;
    });
  }

  function check(manifest, fasta, refFor, opts) {
    opts = opts || {};
    var windows = [], byKey = {}, requested = [], permitted = [], unresolved = [];

    // A reference that is not the one the order named makes every downstream
    // comparison meaningless, so the span and assembly are checked here rather
    // than trusted from whatever the resolver happened to return.
    var refAssembly = opts.assembly || null;
    if (refAssembly && manifest.assembly && refAssembly !== manifest.assembly) {
      return { rows: [], unresolved: [], verdict: "held", discrepancies: 1, records: 0,
               note: "manifest names assembly " + manifest.assembly +
                     " but the reference in use is " + opts.assembly };
    }

    manifest.items.forEach(function (it) {
      var ref = refFor(it);
      if (ref && ref.assembly && manifest.assembly && ref.assembly !== manifest.assembly) {
        unresolved.push({ gene: it.gene, contig: it.contig, pos: it.pos,
          reason: "order names " + manifest.assembly + " but the reference offered is " +
                  ref.assembly });
        return;
      }
      if (it.span.to !== it.span.from + it.span.length - 1) {
        unresolved.push({ gene: it.gene, contig: it.contig, pos: it.pos,
          reason: "sealed span is self-inconsistent: " + it.span.from + "-" + it.span.to +
                  " is not " + it.span.length + " nt" });
        return;
      }
      if (ref && (ref.from !== it.span.from || ref.seq.length !== it.span.length)) {
        unresolved.push({ gene: it.gene, contig: it.contig, pos: it.pos,
          reason: "sealed span " + it.span.from + "-" + it.span.to + " (" + it.span.length +
                  " nt) does not match the reference offered (" + ref.from + ", " +
                  ref.seq.length + " nt)" });
        return;
      }
      if (!ref) {
        unresolved.push({ gene: it.gene, contig: it.contig, pos: it.pos,
                          reason: "no local reference for " + it.contig + ":" +
                                  it.span.from + "-" + it.span.to });
        return;
      }
      var W = { key: it.gene, gene: it.gene, contig: it.contig, from: ref.from, seq: ref.seq };
      windows.push(W);
      byKey[it.contig + ":" + it.gene] = W;
      requested.push({ gene: it.gene, contig: it.contig, pos: it.pos,
                       ref: it.ref, alt: it.alt, hgvsp: it.hgvsp });
      (it.permitted || []).forEach(function (p) {
        permitted.push(Object.assign({}, p, { required: p.optional !== true }));
      });
    });

    if (!windows.length) {
      return { rows: [], unresolved: unresolved, verdict: "held", discrepancies: 0,
               records: 0, note: "no item in the manifest could be resolved to a reference" };
    }

    // A broken OR UNVERIFIED seal means the order on screen may not be the order
    // that was approved, so neither can produce a pass. Callers opt in to a
    // verified seal explicitly; the default is to withhold.
    if (opts.sealOk !== true) {
      return { rows: [], unresolved: unresolved, verdict: "held", discrepancies: 1,
               records: 0,
               note: opts.sealOk === false
                 ? "manifest seal does not verify; re-seal before checking"
                 : "manifest seal was not verified, so no pass can be issued" };
    }

    var records = E.parseFasta(fasta);
    var findings = E.verify(fasta, windows);                 // sequence + reference only
    var rows = E.reconcile(requested, findings, byKey, permitted);
    var bad = rows.filter(function (r) { return !E.isClean(r.status); }).length;

    return {
      rows: rows, findings: findings, unresolved: unresolved,
      records: records.length, permitted: permitted.length,
      discrepancies: bad,
      // An unresolved item is not a pass. It is a question nobody answered.
      verdict: (bad === 0 && unresolved.length === 0) ? "released" : "held",
      note: unresolved.length
        ? unresolved.length + " item(s) could not be checked for lack of a local reference"
        : null
    };
  }

  var API = { build: build, seal: seal, verifySeal: verifySeal, parse: parse,
              checkSealed: checkSealed,
              check: check, canonical: canonical, sha256Hex: sha256Hex };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.VCManifest = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
