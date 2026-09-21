/* Pull real reference sequence, AlphaFold structure and ClinVar annotation for
   the demo loci, and bake them into one JSON the artifact can ship.

   Every value written here came from a public endpoint at build time; nothing
   is invented. Where a source disagrees with what we expected, the script says
   so rather than writing the expectation. */

import fs from "node:fs";

const FLANK = 44;                       // 89 bp window, edit at the centre

const LOCI = [
  { gene:"BRAF",   uniprot:"P15056", contig:"7",  pos:140753336, ref:"A", alt:"T",
    hgvsp:"p.Val600Glu", residue:600, strand:-1 },
  { gene:"KRAS",   uniprot:"P01116", contig:"12", pos:25245350,  ref:"C", alt:"T",
    hgvsp:"p.Gly12Asp",  residue:12,  strand:-1 },
  { gene:"TP53",   uniprot:"P04637", contig:"17", pos:7675088,   ref:"C", alt:"T",
    hgvsp:"p.Arg175His", residue:175, strand:-1 },
  { gene:"PIK3CA", uniprot:"P42336", contig:"3",  pos:179218303, ref:"G", alt:"A",
    hgvsp:"p.Glu545Lys", residue:545, strand:1 },
  { gene:"EGFR",   uniprot:"P00533", contig:"7",  pos:55174772,  ref:null, alt:null,
    hgvsp:"p.Glu746_Ala750del", residue:746, strand:1, delLen:15 }
];

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// EBI rejects requests with no User-Agent, so identify the client.
const UA = { "User-Agent": "variant-control-bench/0.1 (build-time data fetch)" };

async function getText(url, headers = {}) {
  const r = await fetch(url, { headers: Object.assign({}, UA, headers) });
  if (!r.ok) throw new Error(url + " -> " + r.status);
  return r.text();
}
async function getJSON(url) {
  const r = await fetch(url, { headers: Object.assign({ Accept: "application/json" }, UA) });
  if (!r.ok) throw new Error(url + " -> " + r.status);
  return r.json();
}

/* ------------------------------------------------------------ AlphaFold */
// Keep the CA trace only: enough for a recognisable fold, small enough to ship.
function parseCA(pdb) {
  const xs = [], ys = [], zs = [], plddt = [], seqn = [];
  for (const line of pdb.split("\n")) {
    if (!line.startsWith("ATOM")) continue;
    if (line.slice(12, 16).trim() !== "CA") continue;
    xs.push(+(+line.slice(30, 38)).toFixed(1));
    ys.push(+(+line.slice(38, 46)).toFixed(1));
    zs.push(+(+line.slice(46, 54)).toFixed(1));
    plddt.push(+(+line.slice(60, 66)).toFixed(1));
    seqn.push(+line.slice(22, 26));
  }
  return { xs, ys, zs, plddt, first: seqn[0], n: xs.length };
}

const out = { built: new Date().toISOString(), sources: {}, loci: [] };
out.sources = {
  sequence:  "Ensembl REST /sequence/region (GRCh38)",
  structure: "AlphaFold Protein Structure Database (EMBL-EBI)",
  variant:   "MyVariant.info (ClinVar, CADD, dbNSFP)"
};

for (const L of LOCI) {
  const notes = [];
  const from = L.pos - FLANK, to = L.pos + FLANK;

  // 1 — real GRCh38 reference window
  const seq = (await getText(
    `https://rest.ensembl.org/sequence/region/human/${L.contig}:${from}..${to}?content-type=text/plain`
  )).trim().toUpperCase();
  await sleep(250);

  const observedRef = seq[FLANK];
  let ref = L.ref, alt = L.alt;

  if (L.delLen) {
    // Represent the deletion the way a VCF does: anchor base + deleted span.
    ref = seq.slice(FLANK, FLANK + L.delLen + 1);
    alt = seq[FLANK];
    notes.push(`deletion span read from reference: ${ref.slice(1)}`);
  } else if (observedRef !== L.ref) {
    // The asserted protein consequence is only valid for the asserted allele,
    // so a reference mismatch invalidates the row rather than correcting it.
    throw new Error(
      `${L.gene} ${L.contig}:${L.pos} asserts ref ${L.ref} but GRCh38 reads ${observedRef}. ` +
      `Refusing to publish a locus whose protein consequence no longer applies.`);
  }

  // 2 — real AlphaFold model
  const meta = (await getJSON(`https://alphafold.ebi.ac.uk/api/prediction/${L.uniprot}`))[0];
  const pdb = await getText(meta.pdbUrl);
  const ca = parseCA(pdb);
  await sleep(250);

  const resIdx = L.residue - ca.first;
  const residuePlddt = (resIdx >= 0 && resIdx < ca.n) ? ca.plddt[resIdx] : null;
  if (residuePlddt === null) notes.push(`residue ${L.residue} outside modelled range`);

  // 3 — real ClinVar / CADD annotation
  let clin = null, cadd = null, rcvCount = null, reviewStatus = null;
  try {
    const hgvsg = L.delLen
      ? `chr${L.contig}:g.${L.pos + 1}_${L.pos + L.delLen}del`
      : `chr${L.contig}:g.${L.pos}${ref}>${alt}`;
    const mv = await getJSON(
      `https://myvariant.info/v1/variant/${encodeURIComponent(hgvsg)}?assembly=hg38` +
      `&fields=clinvar.rcv,clinvar.variant_id,cadd.phred`);
    if (mv && !mv.error) {
      const rcv = mv.clinvar && mv.clinvar.rcv
        ? (Array.isArray(mv.clinvar.rcv) ? mv.clinvar.rcv : [mv.clinvar.rcv]) : [];
      rcvCount = rcv.length || null;   // RCV records, not submissions
      if (rcv.length) {
        clin = rcv[0].clinical_significance || null;
        reviewStatus = rcv[0].review_status || null;
      }
      cadd = mv.cadd ? mv.cadd.phred : null;
    }
  } catch (e) { notes.push("MyVariant lookup unavailable: " + e.message); }
  await sleep(250);

  out.loci.push({
    gene: L.gene, uniprot: L.uniprot, contig: "chr" + L.contig, pos: L.pos,
    ref, alt, hgvsp: L.hgvsp, residue: L.residue, strand: L.strand,
    window: { from, to, flank: FLANK, seq },
    structure: {
      model: meta.modelEntityId, version: meta.latestVersion,
      globalPlddt: meta.globalMetricValue, residues: ca.n, first: ca.first,
      residuePlddt, xs: ca.xs, ys: ca.ys, zs: ca.zs, plddt: ca.plddt
    },
    clinvar: { significance: clin, reviewStatus, rcvRecords: rcvCount, caddPhred: cadd },
    notes
  });

  console.log(
    `${L.gene.padEnd(7)} ref=${(ref.length > 6 ? "del" + (ref.length - 1) : ref + ">" + alt).padEnd(8)}` +
    ` CA=${String(ca.n).padStart(4)} pLDDT@${L.residue}=${String(residuePlddt).padStart(5)}` +
    ` clinvar=${clin || "-"} cadd=${cadd || "-"}` + (notes.length ? "  ** " + notes.join("; ") : ""));
}

fs.writeFileSync("data/bench-data.json", JSON.stringify(out));
console.log("\nwritten bench-data.json  " +
  (fs.statSync("data/bench-data.json").size / 1024).toFixed(0) + " KB");
