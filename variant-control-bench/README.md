# Variant Control Bench

You are about to pay for DNA synthesis. Before the order goes out, something
independent should prove the fragments actually carry the variants you asked
for — and say so in a form a reviewer can audit.

That is all this does, and it refuses to claim more.

Part of **[BioStudio](../README.md)**. Self-contained page, no build step, no
network at runtime.

---

## The one idea

A composer drafts DNA fragments. A **verifier** receives only the exported FASTA
and the reference window, re-derives the edits from those bases, and compares the
result against the order. It never reads the composer's record of what it meant
to do.

That separation is enforced by the function signature, not by convention:

```js
verify(fasta, windows)        // there is no parameter through which the request could arrive
```

Everything else follows from it. If the verifier could see the request, it would
be grading its own homework.

---

## Measured, not asserted

| Suite | What it establishes | Result |
|---|---|---|
| `npm run test:engine` | Nine named defect classes resolve as specified | **9/9** |
| `npm run test:manifest` | Sealed-order behaviour, including fail-closed paths | **17/17** |
| `npm run test:assembly` | Part boundaries, internal enzyme sites, overhang collisions | **11/11** |
| `npm run test:stress` | Pathological sequence, hostile input, scale, determinism | **45/45** |
| `npm run test:repro` | Defects from the first review stay fixed | **9/9** |
| `npm run test:repro3` | Defects from the third review stay fixed | **12/12** |
| `npm run test:repro4` | Defects from the fourth review stay fixed | **8/8** |
| `npm run test:repro5` | Defects from the fifth review stay fixed | **3/3** |
| `npm run test:a11y` | Contrast, heading structure, names, targets, live region | **0 failures** |
| `npm run campaign` | Adversarial mutation, 22 operators | **19,823 attempts · 0 false pass · 0 false hold** |

Every `test:repro*` suite was written **before** the corresponding fix and run
against the then-current build, so each one is a reproduction first and a
regression second. Thirty-two defects found by review are closed this way.

### Why the campaign number is worth anything

A checker that holds on everything is worthless, so the campaign scores both
directions. Twelve **corrupting** operators must be held; ten **preserving**
operators — re-wrapping, lower case, CRLF, blank lines, trailing spaces,
renamed and decorated headers, reordered records — must *not* be flagged.

Ground truth is read from the **file**, never from the verifier and never from
the operator's own declaration. An operator says which side it means to be on,
but intent is not evidence: reverse-complementing a molecule that is its own
reverse complement changes nothing, and re-emitting a record as plain reference
changes nothing when the ordered molecule already was the reference. Scored by
declaration, both draws demand a hold for a file that is exactly what was
ordered, and the verifier is recorded as committing a false pass it did not
commit — a campaign able to manufacture failures is no better evidence than one
unable to find them.

The specification does not need the declaration. It is checkable from the bytes:
the delivered file must contain the ordered molecules, as a multiset, and
nothing besides. Presentation may move freely; the multiset may not. So every
attempt re-parses what it emitted, compares molecules, and reports how many
draws its operator had declared wrongly.

And the number is falsifiable. Two deliberately broken verifier builds ship with
the bench so you can watch the campaign catch them:

| Build | Attempts | False pass | False hold |
|---|---|---|---|
| Current | 19,823 | 0 | 0 |
| Pre-fix normalizer | 19,823 | **1** | 0 |
| Header-trusting placement | 2,971 | 0 | **160** |

The pre-fix normalizer is a real bug this campaign found: `leftAlign` compared
the last deleted base to `win[at-1]` instead of `win[at]`, rolling a deletion
onto a **different allele** so a corrupted fragment normalised onto the requested
one. One false pass in twenty thousand, which is exactly why it survived to ship.

---

## What it checks

**Allele identity** · **delivered span** · **strand** · **duplicate records** ·
**construct assembly** · **declared intended edits**

Reported but never gating: **reading frame** and **GC / homopolymer** screens.
The verdict answers one narrow question — do the exported fragments encode
exactly the requested edits — and mixing "your request may be a bad idea" into
that answer would make both claims mushy.

### Coverage is a property of a molecule, not of a window

A fragment short at one end cannot be told apart from one carrying a deletion
near that end: with free end gaps both explain the sequence equally well. So the
delivered span is part of the order, and every delivered record answers for its
own extent. Taking the widest extent seen across all records that landed on a
window would let one record cover for another — a molecule short at the tail
stops being reported the moment a second record reaches the tail, and the reader
is told about the extra record instead of the short one. The extra record is the
easy half to fix; re-shipping the same truncated molecule is the half that costs
an experiment.

### Two failures that live only at the assembly level

A construct is not a string, it is an ordered set of parts: enzyme adapter,
homology arm, payload, arm, adapter.

- An **enzyme site inside the insert** means BsaI cuts the construct in half. The
  sequence can be perfectly correct and the thing still cannot be built.
- Parts join by matching 4 nt overhangs, so **two constructs sharing an overhang**
  can ligate to each other. Every fragment individually correct, the pool
  misassembled.

Neither is a sequence error. Both sink the experiment, and neither is visible to
a whole-sequence check.

### Declared intended edits

An HDR repair template deliberately carries silent blocking mutations at the PAM
or cut site so the template is not re-cut. Those are unrequested by definition
and would otherwise hold every real order.

They are accepted **only** when the sealed manifest declares them, so allowing one
is a decision made before the delivery arrived — not a switch someone flips after
seeing a red row. Declared edits are required by default; `optional: true` opts
out. Declaring a *different* edit does not excuse an undeclared one.

---

## Checking a real delivery

Seal the order into a manifest, then months later check whatever the vendor sent
back against it. The manifest names the assembly, every allele and every ordered
span, and is content-addressed, so the result states *which* order it checked
against.

```js
import M from "./src/manifest.js";

const order = await M.seal(M.build(loci, { source: "Ensembl REST" }));
const result = await M.checkSealed(order, vendorFasta, refFor, { assembly: "GRCh38" });
// result.verdict === "released" | "held"
```

`checkSealed` is **fail-closed**. A broken *or unverified* seal cannot produce a
pass, a span that does not match the reference actually used is held, and an item
with no local reference is held rather than assumed good — an unanswered question
is not a pass.

---

## Data

Real, fetched at build time and snapshotted into the page:

- **Ensembl REST** — GRCh38 reference windows
- **AlphaFold DB** — structures and per-residue pLDDT
- **MyVariant.info** — ClinVar significance

`npm run data:refresh` re-fetches. It **fails the build** on a reference
mismatch rather than substituting the observed base, because the asserted protein
consequence is only valid for the asserted allele.

Five loci ship with it: BRAF V600E, KRAS G12D, TP53 R175H, PIK3CA E545K and the
EGFR exon 19 deletion.

---

## Model routing

The composer can be driven by any OpenAI-compatible gateway — OmniRoute first,
freellmapi as fallback — and whichever served a call is recorded as provenance.

```bash
npm run models:probe      # backend status, no calls made
npm run models            # cross-model campaign
```

Nothing a model returns is trusted; it goes through the same verifier as anything
else. That is the entire reason a language model is allowed near this pipeline,
and the campaign measures it:

| Model | Drafted | Correct | Verifier right |
|---|---|---|---|
| `auto` | 5/5 | **2/5** | **5/5** |
| `qwen3-0.6b-iq4` | 4/5 | **0/4** | **4/4** |

Draft accuracy moved 40 points between models. Verifier correctness did not move
at all. The guarantee comes from the checker, not from picking a good model.

---

## What this does not claim

- Sequence verified is not synthesis confirmed.
- Synthesis confirmed is not experimentally qualified.
- Structural confidence is a model score, not an assay. pLDDT is local model
  confidence, **not** variant effect.
- A self-hash proves content identity, not approval time.
- Supported variant representations are SNVs and anchored indels. Complex
  replacements are refused by name rather than silently normalised.

---

## Layout

```text
src/       engine (align, call, reconcile), manifest, assembly, fuzz, advisories, UI
test/      the four suites plus the regression harness for reviewed defects
composer/  OpenAI-compatible routing and the cross-model campaign
data/      snapshotted reference, structures and annotations
build.mjs  inlines everything into dist/index.html
```

MIT licensed.
