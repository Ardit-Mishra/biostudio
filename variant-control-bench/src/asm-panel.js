/* Assembly panel — a React island inside the otherwise vanilla bench.
 *
 * React earns its place here rather than being sprinkled on: this panel is a
 * list of parts whose rendering is a pure function of (plan, how many have
 * seated, verdicts). Driving that imperatively means hand-tracking which block
 * is in which of four states while an animation is mid-flight. Everything else
 * on the page stays vanilla because everything else is a canvas.
 *
 * Motion One does the choreography. The order parts land in is the order they
 * are physically joined, so the animation is reporting assembly order, not
 * decorating a list.
 */
(function () {
  "use strict";
  var React = window.React, ReactDOM = window.ReactDOM, htm = window.htm, Motion = window.Motion;
  var A = window.VCAssembly, E = window.VCEngine;
  if (!React || !ReactDOM || !htm || !A) return;

  var h = React.createElement, html = htm.bind(h);
  var useState = React.useState, useEffect = React.useEffect, useRef = React.useRef;
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Wide enough that a part name is readable rather than ellipsised.
  var MIN_W = 78, PX_NT = 7.2;
  function widthOf(p) { return Math.max(MIN_W, Math.round(p.seq.length * PX_NT)); }

  // Faults are applied to the DELIVERED construct only. The plan never changes,
  // so the check is always "does what arrived match what was ordered".
  var FAULTS = [
    { id: "none", label: "None — built as ordered" },
    { id: "armedit", label: "Silent base changed inside a homology arm" },
    { id: "internalsite", label: "Enzyme site lands inside the insert" },
    { id: "shortadapter", label: "Adapter delivered truncated" }
  ];

  function applyFault(plan, id) {
    var s = plan.sequence;
    if (id === "armedit") {
      var arm = plan.parts.find(function (p) { return p.id === "arm5"; });
      var at = arm.from + 5;
      return s.slice(0, at) + (s[at] === "A" ? "C" : "A") + s.slice(at + 1);
    }
    if (id === "internalsite") {
      var pay = plan.parts.find(function (p) { return p.id === "payload"; });
      return s.slice(0, pay.from) + "GGTCTC" + s.slice(pay.from);
    }
    if (id === "shortadapter") return s.slice(0, s.length - 3);
    return s;
  }

  function Part(props) {
    var ref = useRef(null), done = useRef(false);
    var seated = props.seated, verdict = props.verdict;
    useEffect(function () {
      if (!seated || done.current || !ref.current) return;
      done.current = true;
      if (REDUCED || !Motion) return;
      // Animate the transform components individually. Passing a whole
      // `transform` string ending in "none" makes Motion decompose it and
      // resolve the missing scaleX to 0, which commits scaleX(0) and collapses
      // the block to zero width once the animation finishes.
      Motion.animate(ref.current,
        { y: [-26, 0], scaleX: [0.74, 1] },
        { duration: 0.44, easing: [0.16, 1, 0.3, 1] });
    }, [seated]);
    useEffect(function () { if (!seated) done.current = false; }, [seated]);

    var cls = "apart k-" + props.part.kind + (seated ? " seated" : "") +
      (verdict ? " v-" + verdict : "");
    return html`
      <div class=${cls} ref=${ref} style=${{ width: widthOf(props.part) + "px" }}
           title=${props.part.note || props.part.label}>
        <b>${props.part.label}</b>
        <i>${props.part.seq.length} nt</i>
      </div>`;
  }

  function AssemblyPanel() {
    var s0 = useState("BsaI"), enzyme = s0[0], setEnzyme = s0[1];
    var s1 = useState("none"), fault = s1[0], setFault = s1[1];
    var s2 = useState(0), seated = s2[0], setSeated = s2[1];
    var s3 = useState(null), result = s3[0], setResult = s3[1];
    var s4 = useState(false), running = s4[0], setRunning = s4[1];
    var s5 = useState(0), tick = s5[0], setTick = s5[1];

    var api = window.__bench || {};
    var loci = (api.order && api.order()) || [];
    var focus = (api.focus && api.focus()) || loci[0];
    var plan = focus ? A.plan(focus, { enzyme: enzyme }) : null;
    var pool = loci.length ? A.checkPool(loci.map(function (L) {
      return A.plan(L, { enzyme: enzyme }); })) : null;

    // Re-render when the bench's selection changes underneath us.
    useEffect(function () {
      var id = setInterval(function () { setTick(function (t) { return t + 1; }); }, 700);
      return function () { clearInterval(id); };
    }, []);
    useEffect(function () { setSeated(0); setResult(null); }, [enzyme, fault, focus && focus.gene]);

    function run() {
      if (!plan || running) return;
      setRunning(true); setResult(null); setSeated(0);
      var delivered = applyFault(plan, fault);
      var i = 0;
      var step = function () {
        i += 1; setSeated(i);
        if (i < plan.parts.length) setTimeout(step, REDUCED ? 0 : 300);
        else setTimeout(function () {
          setResult(A.checkConstruct(plan, delivered));
          setRunning(false);
        }, REDUCED ? 0 : 340);
      };
      setTimeout(step, REDUCED ? 0 : 120);
    }

    var verdictOf = function (part) {
      if (!result) return null;
      var row = result.rows.find(function (r) { return r.part === part.id; });
      return row ? (row.status === "match" ? "ok" : "bad") : null;
    };

    if (!plan) return html`<p class="faHint">Select a locus to plan a construct.</p>`;

    return html`
      <div>
        <p class="faHint" style=${{ margin: "0 0 10px" }}>
          <b>A construct is not a string, it is an assembly.</b> Two failures live only at this level:
          an enzyme site inside the insert cuts the construct in half, and two constructs sharing a
          4 nt overhang ligate to each other. Both are invisible to a whole-sequence check, and both
          sink the experiment.
        </p>

        <div class="asmbar">
          <label>Enzyme
            <select value=${enzyme} onChange=${function (e) { setEnzyme(e.target.value); }}>
              ${Object.keys(A.ENZYMES).map(function (k) {
                return html`<option key=${k} value=${k}>${k}</option>`; })}
            </select>
          </label>
          <label>Build fault
            <select value=${fault} onChange=${function (e) { setFault(e.target.value); }}>
              ${FAULTS.map(function (f) {
                return html`<option key=${f.id} value=${f.id}>${f.label}</option>`; })}
            </select>
          </label>
          <button class="prim" onClick=${run} disabled=${running}>
            ${running ? "Assembling…" : "Assemble " + plan.gene}
          </button>
          ${result && html`<span class=${"verdict " + (result.verdict === "released" ? "released" : "held")}>
            ${result.verdict === "released" ? "assembles" : "will not assemble"}</span>`}
        </div>

        <div class="asmtrack">
          ${plan.parts.map(function (p, i) {
            return html`<${Part} key=${p.id} part=${p} seated=${i < seated} verdict=${verdictOf(p)} />`;
          })}
        </div>
        <div class="asmscale">
          ${plan.length} nt ordered · ${plan.arm} nt arms · overhangs
          <b>${plan.overhang5}</b> / <b>${plan.overhang3}</b>
          · parts under ${Math.ceil(MIN_W / PX_NT)} nt drawn at minimum width
        </div>

        ${result && html`
          <div class="asmrows">
            ${result.rows.map(function (r, i) {
              return html`<div class=${"asmrow s-" + r.status} key=${i}>
                <b>${r.label || r.part}</b><span>${r.note}</span></div>`;
            })}
          </div>`}

        ${pool && html`
          <div class=${"asmpool " + (pool.verdict === "released" ? "ok" : "bad")}>
            <b>Pool check</b> ${loci.length} construct(s), ${pool.unique} distinct overhang(s).
            ${pool.rows.length
              ? pool.rows.map(function (r, i) { return html`<span key=${i}> ${r.note}</span>`; })
              : " No two constructs share an overhang, so the pool cannot misassemble."}
          </div>`}
      </div>`;
  }

  var mount = document.getElementById("asm");
  if (mount) ReactDOM.createRoot(mount).render(h(AssemblyPanel));
})();
