/* Adversarial campaign against the verifier.

   Each attempt mutates a clean export and asks one question: did the verifier
   reach the verdict that the mutation logically requires?

   Ground truth is established by CONSTRUCTION, never by asking the verifier.
   An operator is only allowed into the pool if its effect on the encoded edit
   set is knowable in advance:

     corrupting  - the export no longer encodes exactly the requested edits,
                   so the verifier MUST hold. Releasing is a FALSE PASS.
     preserving  - the encoded edit set is unchanged and only its presentation
                   or its uninformative flanks moved, so the verifier MUST
                   release. Holding is a FALSE HOLD.

   A checker that holds on everything is worthless, which is why the preserving
   half carries equal weight. Every attempt is reproducible from its seed.
*/
(function (root) {
  "use strict";

  var E = (typeof module !== "undefined" && module.exports)
    ? require("./engine.js") : root.VCEngine;

  var BASES = "ACGT";

  // Deterministic PRNG so any failing attempt can be replayed from its seed.
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function pick(rnd, arr) { return arr[Math.floor(rnd() * arr.length) % arr.length]; }
  function int(rnd, lo, hi) { return lo + Math.floor(rnd() * (hi - lo + 1)); }

  function parse(fasta) { return E.parseFasta(fasta); }
  // Real vendor files differ from freshly generated ones in line endings,
  // wrapping, stray whitespace and header decoration. None of that changes a
  // molecule, so all of it belongs on the preserving side of the campaign.
  function emit(recs, cols, soft, opt) {
    opt = opt || {};
    var eol = opt.eol || "\n";
    return recs.map(function (r) {
      var body = "";
      for (var i = 0; i < r.seq.length; i += cols) {
        var c = r.seq.slice(i, i + cols);
        if (soft && (i / cols) % 2 === 1) c = c.toLowerCase();
        body += c + (opt.pad ? "   " : "") + eol;
      }
      return ">" + r.name + eol + body + (opt.gap ? eol : "");
    }).join("");
  }

  /* ------------------------------------------------- presentation-only ---- */
  var PRESERVING = [
    { id: "rewrap", note: "re-wrapped at a different column width",
      run: function (recs, rnd) { return { recs: recs, cols: int(rnd, 35, 110) }; } },

    { id: "softmask", note: "soft-masked in lower case",
      run: function (recs, rnd) { return { recs: recs, cols: int(rnd, 50, 90), soft: true }; } },

    { id: "reorder", note: "records emitted in a different order",
      run: function (recs, rnd) {
        var out = recs.slice();
        for (var i = out.length - 1; i > 0; i--) {
          var j = Math.floor(rnd() * (i + 1)); var t = out[i]; out[i] = out[j]; out[j] = t;
        }
        return { recs: out };
      } },

    // The verifier must place fragments by sequence. If a renamed header can
    // change a verdict, the header is being trusted, and it must not be.
    { id: "rename", note: "FASTA headers renamed",
      run: function (recs, rnd) {
        return { recs: recs.map(function (r, i) {
          return { name: "frag_" + int(rnd, 1000, 9999) + "_" + i, seq: r.seq }; }) };
      } },

    // False holds hide in file-format trivia, so the preserving half needs to
    // cover the ways a real vendor file differs from a freshly generated one.
    { id: "lowercase", note: "whole file in lower case",
      run: function (recs) {
        return { recs: recs.map(function (r) {
          return { name: r.name, seq: r.seq.toLowerCase() }; }), raw: function (t) {
            return t.toLowerCase().replace(/^>(.*)$/gm, function (m) { return m; }); } };
      } },

    { id: "crlf", note: "Windows line endings",
      run: function (recs) { return { recs: recs, eol: "\r\n" }; } },

    { id: "blanklines", note: "blank lines between records",
      run: function (recs) { return { recs: recs, gap: true }; } },

    { id: "trailingspace", note: "trailing spaces on sequence lines",
      run: function (recs) { return { recs: recs, pad: true }; } },

    { id: "unwrapped", note: "each record on a single long line",
      run: function (recs) { return { recs: recs, cols: 100000 }; } },

    { id: "richheader", note: "vendor description appended to the header",
      run: function (recs, rnd) {
        return { recs: recs.map(function (r) {
          return { name: r.name + " | order " + int(rnd, 10000, 99999) +
                         " | synthesised " + int(rnd, 1, 28) + " Mar", seq: r.seq }; }) };
      } }
  ];
  // "flank trimmed, edit retained" was a preserving operator until the campaign
  // showed that was the wrong call: a fragment short at one end cannot be told
  // apart from one carrying a deletion near that end. The delivered span is now
  // part of the request, so trimming is a real finding and the operator moved
  // to CORRUPTING.

  /* ------------------------------------------------------- real damage ---- */
  var CORRUPTING = [
    { id: "substitute", note: "one base changed",
      run: function (recs, rnd) {
        var k = int(rnd, 0, recs.length - 1), r = recs[k];
        var at = int(rnd, 0, r.seq.length - 1), from = r.seq[at];
        var to = pick(rnd, BASES.replace(from, "").split(""));
        var out = recs.slice();
        out[k] = { name: r.name, seq: r.seq.slice(0, at) + to + r.seq.slice(at + 1) };
        return { recs: out, detail: from + ">" + to + " at " + at };
      } },

    { id: "deletion", note: "bases removed",
      run: function (recs, rnd) {
        var k = int(rnd, 0, recs.length - 1), r = recs[k], n = int(rnd, 1, 8);
        var at = int(rnd, 1, r.seq.length - n - 1);
        var out = recs.slice();
        out[k] = { name: r.name, seq: r.seq.slice(0, at) + r.seq.slice(at + n) };
        return { recs: out, detail: n + " nt at " + at };
      } },

    { id: "insertion", note: "bases inserted",
      run: function (recs, rnd) {
        var k = int(rnd, 0, recs.length - 1), r = recs[k], n = int(rnd, 1, 6), ins = "";
        for (var i = 0; i < n; i++) ins += pick(rnd, BASES.split(""));
        var at = int(rnd, 1, r.seq.length - 1);
        var out = recs.slice();
        out[k] = { name: r.name, seq: r.seq.slice(0, at) + ins + r.seq.slice(at) };
        return { recs: out, detail: ins + " at " + at };
      } },

    { id: "revcomp", note: "one fragment reverse-complemented",
      run: function (recs, rnd) {
        var k = int(rnd, 0, recs.length - 1), out = recs.slice();
        out[k] = { name: recs[k].name, seq: E.revcomp(recs[k].seq) };
        return { recs: out, detail: recs[k].name };
      } },

    { id: "dropped", note: "a requested fragment is missing",
      run: function (recs, rnd) {
        if (recs.length < 2) return null;
        var k = int(rnd, 0, recs.length - 1), out = recs.slice();
        var gone = out.splice(k, 1)[0];
        return { recs: out, detail: gone.name };
      } },

    { id: "duplicated", note: "a fragment shipped twice",
      run: function (recs, rnd) {
        var k = int(rnd, 0, recs.length - 1), out = recs.slice();
        out.splice(k, 0, { name: recs[k].name + "_copy", seq: recs[k].seq });
        return { recs: out, detail: recs[k].name };
      } },

    // The operators below were added after a review found false passes in
    // classes this campaign never generated. A "0 false passes" number only
    // ever covers the mutations that were actually produced, so the honest
    // response to a missed class is to add the operator, not to re-state the
    // old number.
    { id: "extraRecord", note: "an extra unrequested record rides along",
      run: function (recs, rnd, ctx) {
        var k = int(rnd, 0, recs.length - 1), W = ctx.windows[recs[k].name];
        if (!W) return null;
        var out = recs.slice();
        out.push({ name: "extra_" + int(rnd, 100, 999), seq: W });   // plain reference
        return { recs: out, detail: "unedited copy" };
      } },

    { id: "extraRevcomp", note: "an extra reverse-complement record rides along",
      run: function (recs, rnd, ctx) {
        var k = int(rnd, 0, recs.length - 1), W = ctx.windows[recs[k].name];
        if (!W) return null;
        var out = recs.slice();
        out.push({ name: "rc_" + int(rnd, 100, 999), seq: E.revcomp(W) });
        return { recs: out, detail: "reverse strand copy" };
      } },

    { id: "splitRecord", note: "one ordered molecule delivered as two records",
      run: function (recs, rnd) {
        var k = int(rnd, 0, recs.length - 1), r = recs[k];
        if (r.seq.length < 30) return null;
        var cut = int(rnd, 12, r.seq.length - 12);
        var out = recs.slice();
        out.splice(k, 1, { name: r.name + "_a", seq: r.seq.slice(0, cut) },
                          { name: r.name + "_b", seq: r.seq.slice(cut) });
        return { recs: out, detail: "cut at " + cut };
      } },

    { id: "refOnly", note: "a record delivered as plain reference, edit missing",
      run: function (recs, rnd, ctx) {
        var k = int(rnd, 0, recs.length - 1), W = ctx.windows[recs[k].name];
        if (!W) return null;
        var out = recs.slice();
        out[k] = { name: recs[k].name, seq: W };
        return { recs: out, detail: recs[k].name };
      } },

    { id: "trimflank", note: "flank trimmed, requested edit retained",
      run: function (recs, rnd, ctx) {
        var k = int(rnd, 0, recs.length - 1), r = recs[k], m = ctx.marks[r.name];
        if (!m || m.indel) return null;
        var headroom = m.start, tailroom = r.seq.length - m.end;
        if (headroom < 6 && tailroom < 6) return null;
        var out = recs.slice(), seq = r.seq, cut;
        if (tailroom >= 6 && rnd() < 0.5) {
          cut = int(rnd, 1, tailroom - 2); seq = seq.slice(0, r.seq.length - cut);
        } else if (headroom >= 6) {
          cut = int(rnd, 1, headroom - 2); seq = seq.slice(cut);
        } else return null;
        out[k] = { name: r.name, seq: seq };
        return { recs: out, detail: cut + " nt of flank" };
      } },

    { id: "cutpastedit", note: "truncated past the requested edit",
      run: function (recs, rnd, ctx) {
        var k = int(rnd, 0, recs.length - 1), r = recs[k], m = ctx.marks[r.name];
        if (!m) return null;
        var out = recs.slice();
        out[k] = { name: r.name, seq: r.seq.slice(0, Math.max(8, m.start - int(rnd, 1, 5))) };
        return { recs: out, detail: "kept " + out[k].seq.length + " nt" };
      } }
  ];

  // Where each requested edit sits inside its own exported fragment, so the
  // adversary can aim. The verifier is never given this.
  function markEdits(loci, composed) {
    var marks = {};
    loci.forEach(function (L) {
      var name = L.gene + "_" + L.contig + "_" + L.pos;
      marks[name] = { start: L.window.flank, end: L.window.flank + L.alt.length,
                      indel: L.ref.length !== L.alt.length };
    });
    return marks;
  }

  // Reference window per record name, so record-level operators can build a
  // plain-reference or reverse-complement copy of the right molecule.
  function windowsFor(loci) {
    var w = {};
    loci.forEach(function (L) { w[L.gene + "_" + L.contig + "_" + L.pos] = L.window.seq; });
    return w;
  }

  /* ------------------------------------------------------------ oracle ----
     Ground truth is the FILE, not the array an operator was declared in.

     An operator states which side it means to be on, but intent is not
     evidence, and two of them have preconditions nobody was checking:
     reverse-complementing a molecule that is its own reverse complement
     changes nothing, and re-emitting a record as plain reference changes
     nothing when the ordered molecule already was the reference. Scored by
     declaration, both draws demand a hold for a file that is exactly what was
     ordered - and the verifier gets recorded as committing a false pass it did
     not commit. A campaign that can manufacture failures is no better evidence
     than one that cannot find them.

     The specification does not need the declaration. It is checkable from the
     bytes: the delivered file must contain the ordered molecules, as a
     multiset, and nothing besides. Presentation may move freely; the multiset
     may not. So the oracle reads both files and compares molecules, and the
     declaration becomes an assertion that is itself reported on. */
  function molecules(recs) {
    return recs.map(function (r) { return r.seq.toUpperCase(); }).sort().join("|");
  }

  function attempt(loci, decoy, seed) {
    var rnd = mulberry32(seed);
    var clean = E.compose(loci, "none", decoy);
    var ctx = { marks: markEdits(loci, clean), windows: windowsFor(loci) };
    var corrupting = rnd() < 0.5;
    var op = pick(rnd, corrupting ? CORRUPTING : PRESERVING);

    var res = op.run(parse(clean.fasta), rnd, ctx);
    if (!res) return null;                      // operator declined this draw

    var fasta = emit(res.recs, res.cols || 80, !!res.soft,
                     { eol: res.eol, gap: res.gap, pad: res.pad });
    if (!corrupting && fasta.replace(/\s/g, "") === clean.fasta.replace(/\s/g, "") &&
        op.id === "trimflank") return null;

    var windows = loci.map(function (L) {
      return { key: L.gene, gene: L.gene, contig: L.contig, from: L.window.from, seq: L.window.seq };
    });
    var byKey = {};
    windows.forEach(function (W) { byKey[W.contig + ":" + W.gene] = W; });

    // Re-parse what was emitted, so the oracle sees the same bytes the verifier
    // will, and an emitter that damaged something cannot hide behind the
    // in-memory records it was handed.
    var damaged = molecules(parse(fasta)) !== molecules(parse(clean.fasta));
    var declared = corrupting ? "corrupting" : "preserving";
    var kind = damaged ? "corrupting" : "preserving";

    var findings = E.verify(fasta, windows);
    var rows = E.reconcile(clean.requested, findings, byKey);
    var bad = rows.filter(function (r) { return r.status !== "match"; }).length;
    var verdict = bad ? "held" : "released";
    var expected = damaged ? "held" : "released";

    return {
      seed: seed, op: op.id, note: op.note, detail: res.detail || "",
      kind: kind, declared: declared, misdeclared: kind !== declared,
      verdict: verdict, expected: expected, ok: verdict === expected,
      failure: verdict === expected ? null : (damaged ? "false pass" : "false hold"),
      fasta: fasta, rows: rows, discrepancies: bad
    };
  }

  var API = { attempt: attempt, PRESERVING: PRESERVING, CORRUPTING: CORRUPTING,
              mulberry32: mulberry32 };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.VCFuzz = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
