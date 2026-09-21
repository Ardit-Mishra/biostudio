/* Construct assembly.
 *
 * Up to here the bench treated a fragment as one opaque string. Real orders are
 * not strings, they are assemblies: an enzyme adapter, a homology arm, the
 * payload carrying the edit, another arm, another adapter. Ordering one means
 * committing to boundaries, and boundaries are where assembly actually fails.
 *
 * Two failures live ONLY at this level and are invisible to a whole-sequence
 * check, which is the reason this module exists rather than being decoration:
 *
 *   internal enzyme site - Golden Gate cuts every BsaI site it finds. A
 *       construct whose arm or payload contains GGTCTC (or GAGACC on the other
 *       strand) is cut in the middle and cannot assemble, no matter how
 *       perfectly its sequence encodes the requested variant.
 *
 *   overhang collision - BsaI leaves a 4 nt overhang, and parts join by
 *       matching overhangs. Two constructs in one reaction that share an
 *       overhang can ligate to each other. Every fragment is individually
 *       correct; the pool still misassembles.
 *
 * Neither is a sequence error. Both sink the experiment.
 */
(function (root) {
  "use strict";

  var E = (typeof module !== "undefined" && module.exports)
    ? require("./engine.js") : root.VCEngine;

  // Type IIS enzymes cut outside their recognition site, which is what lets
  // Golden Gate leave a designed overhang.
  var ENZYMES = {
    BsaI:   { site: "GGTCTC", rc: "GAGACC", spacer: 1, overhang: 4 },
    BsmBI:  { site: "CGTCTC", rc: "GAGACG", spacer: 1, overhang: 4 }
  };

  var ARM = 30;            // homology arm length, bp
  var PAD = "AATG";        // inert bases between the site and the cut, not a site

  function enzymeOf(name) { return ENZYMES[name] || ENZYMES.BsaI; }

  /** Decompose a locus into ordered, named parts. */
  function plan(L, opts) {
    opts = opts || {};
    var enz = enzymeOf(opts.enzyme || "BsaI");
    var arm = opts.arm || ARM;
    var win = L.window.seq, f = L.window.flank;

    var start5 = Math.max(0, f - arm);
    var arm5 = win.slice(start5, f);
    var payload = L.alt;
    var end3 = Math.min(win.length, f + L.ref.length + arm);
    var arm3 = win.slice(f + L.ref.length, end3);

    // The overhang is carried by the insert, not the adapter: the enzyme cuts
    // downstream of its site and leaves these four bases sticky.
    // The overhang is carved out of the arm, so an arm shorter than the
    // overhang cannot leave the overhang it claims to.
    var shortArm = arm5.length < enz.overhang || arm3.length < enz.overhang;
    var oh5 = arm5.slice(0, enz.overhang);
    var oh3 = arm3.slice(-enz.overhang);

    var parts = [
      { id: "adapter5", label: "5' adapter", kind: "adapter",
        seq: enz.site + PAD.slice(0, enz.spacer), note: enz.name || "type IIS site" },
      { id: "arm5", label: "5' homology arm", kind: "arm", seq: arm5,
        ref: { from: L.window.from + start5, to: L.window.from + f } },
      { id: "payload", label: "payload", kind: "payload", seq: payload,
        note: L.contig + ":" + L.pos + " " + L.ref + ">" + L.alt },
      { id: "arm3", label: "3' homology arm", kind: "arm", seq: arm3,
        ref: { from: L.window.from + f + L.ref.length, to: L.window.from + end3 } },
      { id: "adapter3", label: "3' adapter", kind: "adapter",
        seq: E.revcomp(enz.site + PAD.slice(0, enz.spacer)), note: "reverse orientation" }
    ];

    var at = 0;
    parts.forEach(function (p) { p.from = at; at += p.seq.length; p.to = at; });

    return {
      gene: L.gene, contig: L.contig, pos: L.pos,
      enzyme: opts.enzyme || "BsaI", arm: arm,
      overhang5: oh5, overhang3: oh3, shortArm: shortArm,
      parts: parts, length: at,
      sequence: parts.map(function (p) { return p.seq; }).join("")
    };
  }

  function findSites(seq, enz) {
    var hits = [], i;
    for (i = 0; i + enz.site.length <= seq.length; i++) {
      if (seq.slice(i, i + enz.site.length) === enz.site) hits.push({ at: i, strand: "+" });
      if (seq.slice(i, i + enz.rc.length) === enz.rc) hits.push({ at: i, strand: "-" });
    }
    return hits;
  }

  /**
   * Check one delivered construct against its plan.
   *
   * Boundary checks the whole-sequence verifier cannot make: the arms must be
   * reference-exact (an edit hiding in an arm is not a requested edit), and no
   * enzyme site may appear anywhere except the two adapters.
   */
  function checkConstruct(planned, delivered) {
    var enz = enzymeOf(planned.enzyme);
    var rows = [], raw = (delivered || "").toUpperCase();

    // Erasing characters outside the alphabet deletes the corruption before it
    // can be found: an inserted IUPAC symbol simply vanishes and the construct
    // measures the right length again. Report them instead.
    var offending = raw.replace(/[ACGTN\s]/g, "");
    if (offending.length) {
      rows.push({ part: "alphabet", label: "unsupported symbols", status: "alphabet",
        note: offending.length + " character(s) outside A/C/G/T/N: " +
              JSON.stringify(offending.slice(0, 12)) });
    }
    var seq = raw.replace(/\s/g, "");

    if (planned.shortArm) {
      rows.push({ part: "arm", label: "arm shorter than the overhang", status: "shortarm",
        note: "a " + enz.overhang + " nt overhang cannot be carved from an arm this short, " +
              "so the reported overhangs and the cut-site model disagree" });
    }

    if (seq.length !== planned.length) {
      rows.push({ part: "construct", status: "short",
        note: "delivered " + seq.length + " nt, ordered " + planned.length + " nt" });
    }

    planned.parts.forEach(function (p) {
      var got = seq.slice(p.from, p.to);
      if (got === p.seq) {
        rows.push({ part: p.id, label: p.label, status: "match",
          note: p.seq.length + " nt" + (p.note ? " · " + p.note : "") });
        return;
      }
      var why = got.length !== p.seq.length ? "length differs" : "sequence differs";
      rows.push({ part: p.id, label: p.label,
        status: p.kind === "arm" ? "armedit" : "mismatch",
        note: p.kind === "arm"
          ? "arm is not reference-exact (" + why + ") — an edit here was never requested"
          : p.label + " " + why });
    });

    // An enzyme site anywhere but the adapters means the construct cuts itself.
    var interior = seq.slice(planned.parts[0].to, planned.parts[4].from);
    findSites(interior, enz).forEach(function (h) {
      rows.push({ part: "interior", label: "internal " + planned.enzyme + " site",
        status: "uncuttable",
        note: planned.enzyme + " site on the " + h.strand + " strand at +" +
              (planned.parts[0].to + h.at) + " — the enzyme cuts here too, so this " +
              "construct cannot assemble even though its sequence is correct" });
    });

    var bad = rows.filter(function (r) { return r.status !== "match"; }).length;
    return { gene: planned.gene, rows: rows, discrepancies: bad,
             verdict: bad ? "held" : "released" };
  }

  /** Overhangs must be unique across everything in one reaction. */
  var COMPL = { A: "T", C: "G", G: "C", T: "A", N: "N" };
  function revcompLocal(s) {
    var o = "";
    for (var i = s.length - 1; i >= 0; i--) o += COMPL[s[i]] || "N";
    return o;
  }

  // Overhangs join by base pairing, not by being the same string. Two ends
  // ligate when one is the reverse complement of the other, and a palindromic
  // end is its own partner, so two copies of it ligate to each other.
  // Comparing literal strings misses both — which is precisely the failure
  // where every fragment is individually correct and the pool still assembles
  // into the wrong thing.
  function checkPool(plans) {
    var seen = {}, rows = [], count = 0;
    plans.forEach(function (p) {
      [["5'", p.overhang5], ["3'", p.overhang3]].forEach(function (pair) {
        var oh = pair[1];
        if (!oh) return;
        var who = p.gene + " " + pair[0], rc = revcompLocal(oh);

        if (oh === rc) {
          rows.push({ part: "pool", label: "palindromic overhang", status: "collide",
            note: pair[0] + " overhang " + oh + " on " + p.gene +
                  " is its own reverse complement, so two copies ligate to each other" });
        }
        if (seen[oh]) {
          rows.push({ part: "pool", label: "overhang collision", status: "collide",
            note: pair[0] + " overhang " + oh + " on " + p.gene + " is already used by " +
                  seen[oh] + " — these two can ligate to each other" });
        }
        if (seen[rc] && rc !== oh) {
          rows.push({ part: "pool", label: "complementary overhangs", status: "collide",
            note: pair[0] + " overhang " + oh + " on " + p.gene +
                  " is the reverse complement of " + seen[rc] +
                  " — those two ends base-pair and will ligate" });
        }
        if (!seen[oh]) { seen[oh] = who; count++; }
      });
    });
    return { rows: rows, unique: count, verdict: rows.length ? "held" : "released" };
  }

  var API = { plan: plan, checkConstruct: checkConstruct, checkPool: checkPool,
              findSites: findSites, ENZYMES: ENZYMES, ARM: ARM };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.VCAssembly = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
