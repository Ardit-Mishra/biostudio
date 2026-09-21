/* Variant-control engine.

   compose()  builds an export from real GRCh38 reference sequence.
   verify()   recovers the edits from that export and the reference ALONE.

   verify() is never given the request, the locus list, or anything the composer
   knew. It receives a FASTA string and a reference window, and it returns what
   it can prove from them. That separation is the whole point, so it is enforced
   here by the function signature rather than by convention.

   Shared by the browser bench and the Node test harness; no imports either way.
*/
(function (root) {
  "use strict";

  var VERSION = "0.2.0";

  var COMP = { A: "T", C: "G", G: "C", T: "A", N: "N" };

  function revcomp(s) {
    var o = "";
    for (var i = s.length - 1; i >= 0; i--) o += COMP[s[i]] || "N";
    return o;
  }

  /* ---------------------------------------------------------------- compose */

  // Apply one VCF-style edit to a window. offset shifts the edit deliberately.
  function applyEdit(win, flank, ref, alt, offset) {
    var at = flank + (offset || 0);
    return win.slice(0, at) + alt + win.slice(at + ref.length);
  }

  function wrapFasta(header, seq, cols, softMask) {
    var body = "";
    for (var i = 0; i < seq.length; i += cols) {
      var chunk = seq.slice(i, i + cols);
      // Soft-masking marks repeats in lower case; it carries no sequence change.
      body += (softMask && (i / cols) % 2 === 1 ? chunk.toLowerCase() : chunk) + "\n";
    }
    return ">" + header + "\n" + body;
  }

  // Returns { fasta, requested } — requested is what the SCIENTIST asked for,
  // and is handed to the comparison step, never to the recovery step.
  function compose(loci, defectKey, decoy) {
    var records = [], requested = [], cols = 80, soft = false;

    loci.forEach(function (L, idx) {
      var win = L.window.seq, flank = L.window.flank;
      var seq = applyEdit(win, flank, L.ref, L.alt, 0);
      var name = L.gene + "_" + L.contig + "_" + L.pos;

      requested.push({
        gene: L.gene, contig: L.contig, pos: L.pos, ref: L.ref, alt: L.alt,
        hgvsp: L.hgvsp, record: name
      });

      switch (defectKey) {
        case "revcomp":
          seq = revcomp(seq); break;
        case "offbyone":
          seq = applyEdit(win, flank, L.ref, L.alt, 1); break;
        case "contig":
          // One fragment was built against the wrong region entirely: an
          // intergenic chr8 window that belongs to no locus in the order.
          if (idx === 0 && decoy) seq = decoy.seq;
          break;
        case "extra":
          // One unrequested transversion, 26 bp downstream of the real edit.
          var k = flank + 26;
          seq = seq.slice(0, k) + (seq[k] === "A" ? "C" : "A") + seq.slice(k + 1);
          break;
        case "truncate":
          seq = seq.slice(0, flank - 4); break;
        case "dup":
          if (idx === 1) records.push({ name: name + "_copy", seq: seq });
          break;
        case "rightalign":
          // The REQUEST is restated in an equivalent right-shifted form. The
          // sequence is untouched: this tests that both sides are normalised
          // before they are compared.
          var r = requested[requested.length - 1];
          var shifted = rightShift(win, flank, L.ref, L.alt);
          if (shifted) {
            r.pos = L.window.from + shifted.pos;
            r.ref = shifted.ref; r.alt = shifted.alt;
            r.restated = shifted.how;
          }
          break;
        case "wrap":
          cols = 60; soft = true; break;
      }
      records.push({ name: name, seq: seq });
    });

    var fasta = records.map(function (r) {
      return wrapFasta(r.name, r.seq, cols, soft);
    }).join("");
    return { fasta: fasta, requested: requested };
  }

  // Slide an indel as far right as it can go and still describe the same
  // resulting sequence. Returns null when the allele is not ambiguous.
  function rightShift(win, flank, ref, alt) {
    if (ref.length === alt.length) return null;
    var del = ref.length > alt.length;
    var unit = del ? ref.slice(alt.length) : alt.slice(ref.length);
    var shift = 0, at = flank + (del ? alt.length : ref.length);
    while (at + unit.length + shift < win.length &&
           win[at + shift] === win[at + shift + unit.length]) shift++;
    if (shift) {
      return { pos: flank + shift, ref: win[flank + shift] + unit,
               alt: win[flank + shift], shift: shift, how: "right-shifted into a repeat" };
    }
    // No repeat to slide into. Restate the same allele with a redundant
    // trailing base on both sides -- an equivalent, un-normalised VCF row.
    var tailAt = flank + ref.length;
    if (tailAt >= win.length) return null;
    var tail = win[tailAt];
    return { pos: flank, ref: ref + tail, alt: alt + tail, shift: 0,
             how: "padded with a redundant trailing base" };
  }

  /* ----------------------------------------------------------------- verify */

  function parseFasta(text) {
    var out = [], cur = null;
    text.split("\n").forEach(function (line) {
      if (!line) return;
      if (line[0] === ">") { cur = { name: line.slice(1).trim(), seq: "" }; out.push(cur); }
      else if (cur) cur.seq += line.trim().toUpperCase();   // case carries no meaning
    });
    return out;
  }

  // Left-align an indel against the reference, the way bcftools norm does.
  //
  // Deleting win[at+1 .. at+L] and deleting win[at .. at+L-1] describe the same
  // resulting sequence only when win[at] === win[at+L] -- that is, when the
  // anchor base equals the last deleted base. Testing the last deleted base
  // against win[at-1] instead rolls the allele onto a DIFFERENT one, which lets
  // a corrupted fragment normalise onto the requested edit and be released.
  // The normalizer this build shipped with before the campaign found the bug
  // below. Kept, and selectable, for one reason: a campaign that only ever
  // reports zero is unfalsifiable. Switching this on makes real false passes
  // appear, which is the only way to show the campaign detects anything.
  //
  // The defect: it tests the last deleted base against win[at-1] instead of
  // win[at], so it rolls a deletion onto a DIFFERENT allele. A corrupted
  // fragment then normalises onto the requested edit and is released.
  function leftAlignLegacy(win, at, ref, alt) {
    while (at > 0 && ref.length !== alt.length) {
      var rLast = ref[ref.length - 1], aLast = alt[alt.length - 1];
      if (ref.length > 1 && alt.length > 1 && rLast === aLast) {
        ref = ref.slice(0, -1); alt = alt.slice(0, -1); continue;
      }
      var prev = win[at - 1];
      if ((ref.length > alt.length && ref[ref.length - 1] === prev) ||
          (alt.length > ref.length && alt[alt.length - 1] === prev)) {
        at -= 1;
        ref = prev + ref.slice(0, -1);
        alt = prev + alt.slice(0, -1);
        continue;
      }
      break;
    }
    return { at: at, ref: ref, alt: alt };
  }

  var NORMALIZER = "fixed";
  function setNormalizer(mode) { NORMALIZER = (mode === "legacy") ? "legacy" : "fixed"; }
  function normalizerMode() { return NORMALIZER; }

  function leftAlign(win, at, ref, alt) {
    if (NORMALIZER === "legacy") return leftAlignLegacy(win, at, ref, alt);
    // Redundant bases carried on both alleles say nothing, at either end.
    var t = trimAllele(at, ref, alt);
    at = t.pos; ref = t.ref; alt = t.alt;
    while (at > 0 && ref.length !== alt.length &&
           (ref.length === 1 || alt.length === 1) && ref[0] === alt[0]) {
      var longer = ref.length > alt.length ? ref : alt;
      if (longer[longer.length - 1] !== win[at]) break;
      at -= 1;
      ref = win[at] + ref.slice(0, -1);
      alt = win[at] + alt.slice(0, -1);
    }
    return { at: at, ref: ref, alt: alt };
  }

  // Semi-global (glocal) affine alignment of a fragment into a reference window.
  //
  // Prefix and suffix heuristics cannot separate "the fragment was cut at an
  // end" from "the fragment lost bases near an end": a deletion 2 nt from the
  // 5' edge looks exactly like a cut plus one substitution, and guessing gets
  // it wrong. Gaps at the ends of the WINDOW are free, so a short fragment is
  // reported as reduced coverage; gaps inside are penalised, so a real
  // deletion is reported as an edit. The distinction then comes out of the
  // alignment instead of out of a rule of thumb.
  var SC = { match: 2, mismatch: -4, open: -8, ext: -1 }, NEG = -1e9;

  function align(win, obs) {
    var n = win.length, m = obs.length, W = n + 1, size = (m + 1) * W;
    var M = new Float64Array(size), X = new Float64Array(size), Y = new Float64Array(size);
    var pM = new Uint8Array(size), pX = new Uint8Array(size), pY = new Uint8Array(size);
    var i, j, k, a, b, c;

    for (j = 0; j <= n; j++) { M[j] = 0; X[j] = 0; Y[j] = NEG; }   // free leading window
    for (i = 1; i <= m; i++) {
      M[i * W] = NEG; X[i * W] = NEG;
      Y[i * W] = (i === 1 ? SC.open : Y[(i - 1) * W] + SC.ext);
      pY[i * W] = 2;
    }
    for (i = 1; i <= m; i++) {
      for (j = 1; j <= n; j++) {
        k = i * W + j;
        var d = (i - 1) * W + (j - 1);
        var sc = (obs[i - 1] === win[j - 1]) ? SC.match : SC.mismatch;
        a = M[d]; b = X[d]; c = Y[d];
        if (a >= b && a >= c) { M[k] = a + sc; pM[k] = 0; }
        else if (b >= c)      { M[k] = b + sc; pM[k] = 1; }
        else                  { M[k] = c + sc; pM[k] = 2; }

        var l = i * W + (j - 1);                       // skip a window base
        a = M[l] + SC.open; b = X[l] + SC.ext;
        if (a >= b) { X[k] = a; pX[k] = 0; } else { X[k] = b; pX[k] = 1; }

        var u = (i - 1) * W + j;                       // extra fragment base
        a = M[u] + SC.open; b = Y[u] + SC.ext;
        if (a >= b) { Y[k] = a; pY[k] = 0; } else { Y[k] = b; pY[k] = 2; }
      }
    }

    var best = NEG, bj = n, bs = 0;                    // free trailing window
    for (j = 0; j <= n; j++) {
      k = m * W + j;
      if (M[k] > best) { best = M[k]; bj = j; bs = 0; }
      if (Y[k] > best) { best = Y[k]; bj = j; bs = 2; }
    }

    var ops = [];                                      // traceback, 3' to 5'
    i = m; j = bj; var st = bs;
    while (i > 0 || (j > 0 && st === 1)) {
      k = i * W + j;
      if (st === 0) {
        if (i === 0 || j === 0) break;
        ops.push({ t: "m", i: i - 1, j: j - 1 });
        st = pM[k]; i--; j--;
      } else if (st === 1) {
        if (j === 0) break;
        ops.push({ t: "d", j: j - 1 });
        st = pX[k]; j--;
      } else {
        if (i === 0) break;
        ops.push({ t: "i", i: i - 1, j: j });
        st = pY[k]; i--;
      }
    }
    ops.reverse();
    return { ops: ops, score: best };
  }

  // Recover edits from one observed fragment against the reference window.
  // Returns the edits plus the span of the window the fragment actually covers,
  // so a locus outside that span is reported as uncovered, not as unedited.
  function callEdits(win, obs) {
    if (!obs.length) return { edits: [], aligned: false, from: 0, to: 0 };

    var a = align(win, obs);
    if (!a.ops.length) return { edits: [], aligned: false, from: 0, to: 0 };

    // Covered window span: first and last window base the fragment reaches.
    var lo = -1, hi = -1;
    a.ops.forEach(function (op) {
      if (op.t === "m") { if (lo < 0) lo = op.j; hi = op.j; }
    });
    if (lo < 0) return { edits: [], aligned: false, from: 0, to: 0 };

    var edits = [], run = null, o, p;
    for (var x = 0; x < a.ops.length; x++) {
      o = a.ops[x];
      if (o.t === "m") {
        if (run) { edits.push(run); run = null; }
        if (win[o.j] !== obs[o.i]) edits.push({ at: o.j, ref: win[o.j], alt: obs[o.i] });
      } else if (o.t === "d") {
        if (o.j < lo || o.j > hi) continue;             // free end gap, not an edit
        if (run && run.kind === "d" && run.end === o.j - 1) { run.end = o.j; continue; }
        if (run) edits.push(run);
        run = { kind: "d", start: o.j, end: o.j };
      } else {
        if (run && run.kind === "i" && run.at === o.j) { run.ins += obs[o.i]; continue; }
        if (run) edits.push(run);
        run = { kind: "i", at: o.j, ins: obs[o.i] };
      }
    }
    if (run) edits.push(run);

    // Turn gap runs into anchored VCF-style alleles, then left-align them.
    var out = [];
    edits.forEach(function (e) {
      if (!e.kind) { out.push(e); return; }
      if (e.kind === "d") {
        p = Math.max(0, e.start - 1);
        var nd = leftAlign(win, p, win.slice(p, e.end + 1), win[p]);
        out.push({ at: nd.at, ref: nd.ref, alt: nd.alt });
      } else if (e.at === 0) {
        // An insertion before the first reference base usually has no base to
        // anchor on, and anchoring it to win[0] would describe a DIFFERENT
        // molecule. But when the inserted bases repeat what the window already
        // starts with, inserting before and after the first base produce the
        // same sequence, so the anchored form is exact rather than invented.
        if (win.slice(0, e.ins.length) === e.ins) {
          var eq = leftAlign(win, 0, win[0], win[0] + e.ins);
          out.push({ at: eq.at, ref: eq.ref, alt: eq.alt });
        } else {
          out.push({ at: 0, ref: "-", alt: e.ins,
                     boundary: "insertion 5-prime of the reference window" });
        }
      } else {
        p = e.at - 1;
        var ni = leftAlign(win, p, win[p], win[p] + e.ins);
        out.push({ at: ni.at, ref: ni.ref, alt: ni.alt });
      }
    });

    return { edits: out, aligned: true, from: lo, to: hi + 1,
             truncated: (lo > 0 || hi < win.length - 1) };
  }

  // Seed placement on shared k-mers rather than on aligned positions. A
  // position-wise score collapses across an indel -- a real 15 bp deletion
  // scores 72% against its own window and would be rejected as unplaced.
  var K = 12;
  function kmers(s) {
    var set = Object.create(null);
    for (var i = 0; i + K <= s.length; i++) set[s.substr(i, K)] = 1;
    return set;
  }
  function seedScore(winKmers, obs) {
    var total = obs.length - K + 1;
    if (total <= 0) return 0;
    var hit = 0;
    for (var i = 0; i < total; i++) if (winKmers[obs.substr(i, K)]) hit++;
    return hit / total;
  }

  /* verify() sees ONLY the exported FASTA and the reference windows. */
  // Placement strategy. "sequence" is the real one. "header" is a deliberately
  // broken variant kept so the campaign can be shown detecting something: it
  // places a fragment by the name the composer wrote on it, which is the
  // composer asserting its own correctness. Renaming a header then changes a
  // verdict, which is exactly the property that must not hold.
  var PLACEMENT = "sequence";
  function setPlacement(mode) { PLACEMENT = (mode === "header") ? "header" : "sequence"; }
  function placementMode() { return PLACEMENT; }

  function verify(fasta, windows) {
    var records = parseFasta(fasta);
    var findings = [], seen = {};
    windows.forEach(function (W) { if (!W._k) W._k = kmers(W.seq); });

    records.forEach(function (rec) {
      // Match the fragment to a reference window by sequence identity alone,
      // never by the FASTA header — a header is the composer's own assertion.
      var best = null;
      if (PLACEMENT === "header") {
        var g = String(rec.name).split("_")[0];
        for (var wi = 0; wi < windows.length; wi++)
          if (windows[wi].gene === g) { best = { W: windows[wi], score: 1, reversed: false }; break; }
        if (!best) { findings.push({ record: rec.name, status: "unplaced", score: 0 }); return; }
      }
      if (!best) windows.forEach(function (W) {
        var direct = seedScore(W._k, rec.seq);
        var rc = seedScore(W._k, revcomp(rec.seq));
        var score = Math.max(direct, rc);
        if (!best || score > best.score) {
          best = { W: W, score: score, reversed: rc > direct };
        }
      });

      // Two edits in an 89 bp window break 24 of 78 seeds on their own, so a
      // high floor rejects honest fragments. Off-target windows score ~0, so
      // placement asks for a real signal, not a near-perfect one.
      if (!best || best.score < 0.25) {
        findings.push({ record: rec.name, status: "unplaced", score: best ? best.score : 0 });
        return;
      }
      if (best.reversed) {
        findings.push({ record: rec.name, status: "reversed", window: best.W, score: best.score,
                        reversed: true });
        return;
      }

      var obs = rec.seq;
      var called = callEdits(best.W.seq, obs);
      var truncated = !!called.truncated;
      if (!called.aligned) {
        findings.push({ record: rec.name, status: "unplaced", score: best.score });
        return;
      }

      var dupOf = seen[best.W.key];
      seen[best.W.key] = true;
      if (dupOf) {
        findings.push({ record: rec.name, status: "duplicate", window: best.W,
                        score: best.score, from: best.W.from + called.from,
                        to: best.W.from + called.to });
        return;
      }

      called.edits.forEach(function (e) {
        findings.push({
          record: rec.name, status: dupOf ? "duplicate" : "called", window: best.W,
          pos: best.W.from + e.at, ref: e.ref, alt: e.alt, truncated: truncated,
          from: best.W.from + called.from, to: best.W.from + called.to,
          score: best.score, reversed: false, bp: e.at
        });
      });
      if (!called.edits.length) {
        findings.push({ record: rec.name, status: "silent", window: best.W, truncated: truncated,
                        from: best.W.from + called.from, to: best.W.from + called.to,
                        score: best.score });
      }
    });
    return findings;
  }

  /* ------------------------------------------------------------- comparison */

  function normKey(win, at, ref, alt, from) {
    var n = leftAlign(win, at - from, ref, alt);
    return (from + n.at) + ":" + n.ref + ">" + n.alt;
  }

  // An edit that nobody requested is a finding -- unless the order declared it
  // in advance. An HDR repair template deliberately carries silent blocking
  // mutations at the PAM or cut site so the template is not re-cut; those are
  // unrequested by definition and would otherwise hold every real order.
  //
  // They are only accepted when they appear in the frozen manifest, so allowing
  // one is a recorded decision made before the delivery arrived, never a switch
  // someone flips afterwards to clear a red row.
  function isPermitted(permitted, W, f) {
    if (!permitted || !permitted.length || !W) return null;
    var key = normKey(W.seq, f.pos, f.ref, f.alt, W.from);
    for (var i = 0; i < permitted.length; i++) {
      var p = permitted[i];
      if (p.contig !== W.contig) continue;
      // A declared edit is a request like any other and gets the same
      // validation. An unvalidated one could name a REF the reference does not
      // carry and still be honoured once trimming discarded the mismatch.
      if (classifyRequest(W, p) !== "snv" && classifyRequest(W, p) !== "ins" &&
          classifyRequest(W, p) !== "del") continue;
      if (normKey(W.seq, p.pos, p.ref, p.alt, W.from) === key) return p;
    }
    return null;
  }

  // A row that is not a finding: the delivery matched, or matched something the
  // order declared up front.
  function isClean(status) { return status === "match" || status === "intended"; }

  // What the comparison step is able to reason about. Anything else is refused
  // by name rather than silently normalised into a different allele.
  // Standard VCF trimming: shared trailing bases first, then shared leading
  // bases, never consuming an allele entirely.
  function trimAllele(pos, ref, alt) {
    while (ref.length > 1 && alt.length > 1 &&
           ref[ref.length - 1] === alt[alt.length - 1]) {
      ref = ref.slice(0, -1); alt = alt.slice(0, -1);
    }
    while (ref.length > 1 && alt.length > 1 && ref[0] === alt[0]) {
      ref = ref.slice(1); alt = alt.slice(1); pos += 1;
    }
    return { pos: pos, ref: ref, alt: alt };
  }

  var NUCLEOTIDE = /^[ACGTN]+$/;

  function classifyRequest(W, q) {
    if (!W) return "unresolved";
    if (!NUCLEOTIDE.test(q.ref || "") || !NUCLEOTIDE.test(q.alt || "")) return "alphabet";
    var i = q.pos - W.from;
    if (i < 0 || i + q.ref.length > W.seq.length) return "outside";
    if (W.seq.slice(i, i + q.ref.length) !== q.ref) return "refmismatch";
    // H -- a deletion running to the last base of the window cannot be told
    // apart from a fragment that was simply cut there, because the reference
    // beyond the window is not held. Refuse it rather than guess.
    if (q.alt.length < q.ref.length && i + q.ref.length >= W.seq.length) return "boundary";
    var t = trimAllele(q.pos, q.ref, q.alt);
    if (t.ref.length === 1 && t.alt.length === 1) return "snv";
    if (t.ref.length === 1 && t.alt.length > 1 && t.alt[0] === t.ref) return "ins";
    if (t.alt.length === 1 && t.ref.length > 1 && t.ref[0] === t.alt) return "del";
    return "unsupported";
  }

  var REFUSAL = {
    unresolved:  "no reference window for this locus",
    outside:     "the requested allele falls outside the reference window",
    refmismatch: "REF does not match the reference at that coordinate",
    alphabet:    "alleles must be A, C, G, T or N",
    boundary:    "a deletion reaching the end of the window is indistinguishable " +
                 "from a fragment cut there; order a longer window",
    unsupported: "complex replacement; only SNVs and anchored indels are supported"
  };

  // Compare what was proven against what was asked. Both sides are normalised.
  function reconcile(requested, findings, windowsByKey, permitted) {
    var rows = [], used = {};

    requested.forEach(function (q) {
      var W = windowsByKey[q.wkey || (q.contig + ":" + q.gene)];
      var kind = classifyRequest(W, q);
      if (REFUSAL[kind]) {
        rows.push({ gene: q.gene, contig: q.contig, pos: q.pos, ref: q.ref, alt: q.alt,
                    hgvsp: q.hgvsp, recPos: null, status: "refused", note: REFUSAL[kind] });
        return;
      }
      var want = normKey(W.seq, q.pos, q.ref, q.alt, W.from);
      var hit = null;
      findings.forEach(function (f, i) {
        if (used[i] || f.status !== "called" || !f.window || f.window.key !== W.key) return;
        if (normKey(W.seq, f.pos, f.ref, f.alt, W.from) === want) { hit = f; used[i] = true; }
      });
      if (hit) {
        rows.push({ gene: q.gene, contig: q.contig, pos: q.pos, ref: q.ref, alt: q.alt,
                    hgvsp: q.hgvsp, recPos: hit.pos, status: "match",
                    note: q.restated ? "normalised from an allele " + q.restated : "recovered from alignment" });
        return;
      }
      // Anything else on this window is a wrong answer rather than no answer.
      var near = null;
      findings.forEach(function (f, i) {
        if (used[i] || !f.window || f.window.key !== W.key) return;
        if (f.status === "called" || f.status === "reversed" ||
            f.status === "duplicate" || f.status === "silent") { near = near || { f: f, i: i }; }
      });
      if (near && near.f.status === "called") {
        used[near.i] = true;
        rows.push({ gene: q.gene, contig: q.contig, pos: q.pos, ref: q.ref, alt: q.alt,
                    hgvsp: q.hgvsp, recPos: near.f.pos, status: "mismatch",
                    note: near.f.pos === q.pos ? "different allele at the requested position"
                        : "recovered " + (near.f.pos - q.pos) + " bp away" });
      } else if (near && near.f.status === "reversed") {
        used[near.i] = true;
        rows.push({ gene: q.gene, contig: q.contig, pos: q.pos, ref: q.ref, alt: q.alt,
                    hgvsp: q.hgvsp, recPos: null, status: "missing",
                    note: "fragment aligns only as reverse complement" });
      } else if (near && near.f.status === "silent") {
        used[near.i] = true;
        rows.push({ gene: q.gene, contig: q.contig, pos: q.pos, ref: q.ref, alt: q.alt,
                    hgvsp: q.hgvsp, recPos: null, status: "missing",
                    note: near.f.truncated ? "locus falls outside the delivered fragment"
                                           : "fragment is unedited reference" });
      } else {
        rows.push({ gene: q.gene, contig: q.contig, pos: q.pos, ref: q.ref, alt: q.alt,
                    hgvsp: q.hgvsp, recPos: null, status: "missing",
                    note: "no fragment aligns to this locus" });
      }
    });

    // Delivered span is part of the order, not a detail of presentation.
    //
    // A fragment short by a few bases at one end cannot be told apart from an
    // internal deletion near that end: with free end gaps both explain the
    // sequence equally well, and no aligner can separate them. Rather than
    // guess, require the delivered span to be the span that was requested.
    // Coverage and allele correctness are then reported as separate findings.
    var span = {};
    findings.forEach(function (f) {
      if (!f.window || f.from === undefined) return;
      var s = span[f.window.key] ||
              (span[f.window.key] = { lo: Infinity, hi: -Infinity, W: f.window });
      if (f.from < s.lo) s.lo = f.from;
      if (f.to > s.hi) s.hi = f.to;
    });
    Object.keys(span).forEach(function (k) {
      var s = span[k], end = s.W.from + s.W.seq.length;
      if (s.lo > s.W.from || s.hi < end) {
        rows.push({
          gene: s.W.gene, contig: s.W.contig, pos: s.W.from, ref: "", alt: "",
          hgvsp: "delivered span", recPos: s.lo, status: "short",
          note: "covers " + (s.hi - s.lo) + " of the " + s.W.seq.length +
                " nt requested (" + s.lo + "–" + s.hi + ")"
        });
      }
    });

    // A declared edit marked required must actually be delivered. Without this
    // a manifest could declare PAM-blocking mutations and the delivery simply
    // omit them, which is a different donor from the one that was ordered.
    (permitted || []).forEach(function (pe) {
      if (!pe.required) return;
      var W = null;
      Object.keys(windowsByKey).forEach(function (k) {
        var w = windowsByKey[k];
        if (w.contig === pe.contig && pe.pos >= w.from && pe.pos < w.from + w.seq.length) W = w;
      });
      var present = findings.some(function (f) {
        return f.status === "called" && f.window === W && isPermitted([pe], W, f);
      });
      if (!present) {
        rows.push({ gene: W ? W.gene : "—", contig: pe.contig, pos: pe.pos,
                    ref: pe.ref, alt: pe.alt, hgvsp: pe.why || "required secondary edit",
                    recPos: null, status: "missing",
                    note: "declared as required by the order but not delivered" });
      }
    });

    // Anything recovered that nobody asked for.
    findings.forEach(function (f, i) {
      if (used[i]) return;
      if (f.status === "called" || f.status === "duplicate") {
        var ok = (f.status === "called") ? isPermitted(permitted, f.window, f) : null;
        rows.push({ gene: f.window ? f.window.gene : "—", contig: f.window ? f.window.contig : "—",
                    pos: f.pos, ref: f.ref, alt: f.alt,
                    hgvsp: ok ? (ok.why || "declared in the manifest") : "not requested",
                    recPos: f.pos, status: ok ? "intended" : "extra",
                    note: ok ? "declared intended edit, matched"
                        : f.status === "duplicate" ? "second copy of the same fragment"
                                                   : "edit recovered that was never requested" });
      } else if (f.status === "unplaced") {
        rows.push({ gene: "—", contig: "—", pos: null, ref: "", alt: "", hgvsp: "unplaced fragment",
                    recPos: null, status: "extra",
                    note: "matches no requested window (best " +
                          (f.score * 100).toFixed(0) + "% shared 12-mers)" });
      } else if (f.status === "silent" || f.status === "reversed") {
        // A record nobody asked for is a finding even when it carries no edit:
        // it is still material that would go into the reaction.
        rows.push({ gene: f.window ? f.window.gene : "—",
                    contig: f.window ? f.window.contig : "—",
                    pos: null, ref: "", alt: "", hgvsp: "unrequested record",
                    recPos: null, status: "extra",
                    note: f.status === "reversed"
                      ? "extra record, reverse complement of " +
                        (f.window ? f.window.gene : "a window")
                      : "extra record carrying no edit" });
      }
    });
    return rows;
  }

  function run(loci, defectKey, decoy) {
    var windows = loci.map(function (L) {
      return { key: L.gene, gene: L.gene, contig: L.contig,
               from: L.window.from, seq: L.window.seq };
    });
    var byKey = {};
    windows.forEach(function (W) { byKey[W.contig + ":" + W.gene] = W; });

    var composed = compose(loci, defectKey, decoy);
    var findings = verify(composed.fasta, windows);          // sequence + reference only
    var rows = reconcile(composed.requested, findings, byKey);
    var bad = rows.filter(function (r) { return !isClean(r.status); });
    return {
      fasta: composed.fasta, requested: composed.requested, findings: findings,
      rows: rows, verdict: bad.length ? "held" : "released", discrepancies: bad.length
    };
  }

  var API = { VERSION: VERSION, K: K, isClean: isClean, setNormalizer: setNormalizer,
              setPlacement: setPlacement, placementMode: placementMode,
              normalizerMode: normalizerMode, run: run, compose: compose, verify: verify, reconcile: reconcile,
              revcomp: revcomp, parseFasta: parseFasta, leftAlign: leftAlign };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.VCEngine = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
