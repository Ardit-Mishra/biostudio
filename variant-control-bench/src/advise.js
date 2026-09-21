/* Advisories: things that are true about an order but are not the verifier's
   pass/fail question.
 *
 * These deliberately do NOT gate the verdict. The verdict answers one narrow
 * question -- do the exported fragments encode exactly the requested edits --
 * and mixing "your request may be a bad idea" into that answer would make both
 * claims mushy. They are reported beside it instead.
 *
 * The frame advisory is the important one. The verifier will happily release a
 * frameshift if a frameshift is what was asked for, so something has to look at
 * the request itself and say so.
 */
(function (root) {
  "use strict";

  function netDelta(loci) {
    var d = 0;
    loci.forEach(function (L) { d += L.alt.length - L.ref.length; });
    return d;
  }

  function gcPercent(s) {
    var gc = 0;
    for (var i = 0; i < s.length; i++) if (s[i] === "G" || s[i] === "C") gc++;
    return s.length ? (100 * gc / s.length) : 0;
  }

  function longestRun(s) {
    var best = 0, run = 0, prev = "";
    for (var i = 0; i < s.length; i++) {
      run = (s[i] === prev) ? run + 1 : 1;
      prev = s[i];
      if (run > best) best = run;
    }
    return best;
  }

  // Vendor screens differ; these are conventional research-use thresholds and
  // are stated as advisory, never as an accept/reject.
  var GC_LO = 25, GC_HI = 75, HOMO_MAX = 8;

  function advise(loci, fasta, parseFasta) {
    var out = [];

    loci.forEach(function (L) {
      var d = L.alt.length - L.ref.length;
      if (d === 0) return;
      out.push({
        scope: L.gene, kind: "frame",
        level: (d % 3 === 0) ? "note" : "warn",
        text: (d % 3 === 0)
          ? "net " + d + " nt, a multiple of 3 — in-frame if this span is coding"
          : "net " + d + " nt, NOT a multiple of 3 — frameshift if this span is coding"
      });
    });

    var total = netDelta(loci);
    if (total % 3 !== 0 && loci.length > 1) {
      out.push({ scope: "order", kind: "frame", level: "warn",
        text: "requested edits change length by " + total + " nt in total" });
    }

    var recs = fasta ? parseFasta(fasta) : [];
    recs.forEach(function (r) {
      var gc = gcPercent(r.seq), run = longestRun(r.seq);
      if (gc < GC_LO || gc > GC_HI) {
        out.push({ scope: r.name, kind: "gc", level: "warn",
          text: "GC " + gc.toFixed(0) + "% is outside " + GC_LO + "–" + GC_HI +
                "%, many vendors will flag this" });
      }
      if (run > HOMO_MAX) {
        out.push({ scope: r.name, kind: "homopolymer", level: "warn",
          text: run + " nt homopolymer run, above the usual " + HOMO_MAX + " nt screen" });
      }
    });

    return out;
  }

  function summary(loci, fasta, parseFasta) {
    var a = advise(loci, fasta, parseFasta);
    var warns = a.filter(function (x) { return x.level === "warn"; });
    return { items: a, warnings: warns.length,
             clean: warns.length === 0, thresholds: { GC_LO: GC_LO, GC_HI: GC_HI, HOMO_MAX: HOMO_MAX } };
  }

  var API = { advise: advise, summary: summary, gcPercent: gcPercent, longestRun: longestRun };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.VCAdvise = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
