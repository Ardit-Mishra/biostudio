# Portfolio Program Handoff

Last updated: 2026-09-19

## Product Thesis

Ardit's portfolio is a connected set of research and AI-engineering products,
not five copies of a chatbot or prediction form. The shared standard is that a
claim, decision, or automated action must remain inspectable back to its source
evidence or verification result.

| Product | Distinct job | Current engineering proof | Next honest milestone |
| --- | --- | --- | --- |
| Tri-AI | Verification-gated agent orchestration | durable board, exit-code acceptance, Telegram control, JARVIS read-only observability | govern GenClarus end to end; then trusted remote delegation and measured offload |
| GenClarus | Grounded genomic interpretation | typed public-source facts, deterministic cited explanations, retrieval/eval surface | maintain deployed source integrity and prove Tri-AI-governed work |
| Peptide-MHC | Browser-local ML inference | allele-conditioned XGBoost runtime, model card, reproducibility fixtures, local-only privacy boundary | public release cutover after final portfolio review |
| GenomeSight | Sequencing-analysis workflows | FASTA/FASTQ analysis and computational-biology utilities on the existing deployed stack | release/audit current frontend and API provenance before new scope |
| BioStudio | Drug-discovery evidence cartography | source-backed Decision Twin, deterministic assay translation, held-out ADMET artifacts | multi-source evidence graph, bounded public connectors, and later controlled workspaces/agents |

## BioStudio: What Must Be Different

BioStudio is not a generic molecular-property dashboard and must not imitate the
Peptide-MHC workbench. Its product question is:

> Given a molecule, target, and research hypothesis, what public evidence exists,
> at what biological layer was it measured, and where does the path to a next
> experiment break?

The visual language should therefore be an evidence map: source records feed
explicit assay-layer nodes; support, contradiction, and absence use different
edge treatments; provenance remains click-through. A planned connector is a
capability gap, not a measurement.

## Public-Source Plan

Only source artifacts may cross a connector boundary. An operator supplies a
claim, assay context, and direction before an artifact becomes study evidence.
No connector may run an agent, make a recommendation, or create a study row.

| Source | Role in BioStudio | State |
| --- | --- | --- |
| Europe PMC / PubMed | citable literature and source excerpts | Europe PMC active; PubMed follows only with a separate bounded contract |
| Open Targets | target identity, target-disease and tractability context | active, fixed Ensembl-ID lookup |
| ChEMBL | curated compound, target, assay and activity records | active compound-record connector in this slice; activity joins are a later bounded slice |
| BindingDB | measured protein-ligand affinity cross-check | planned; first implementation must retain units, target identifier, and provenance |
| PubChem | compound identity, public assay metadata, and chemical cross-references | planned; rate-limited resolver only |
| UniProt | protein identity, function, domains, and cross-references | planned; accession-only lookup |
| RCSB PDB / AlphaFold DB | experimental and predicted structure context | planned; structure metadata is context, never proof of efficacy |
| ClinicalTrials.gov | trial registry context | planned; retrieved trial facts must remain distinct from trial outcomes or publications |

The current external-source facts and API references are captured in the
implementation notes and tests. Do not present any planned source as retrieved
evidence in a UI, resume bullet, or public demo.

## Release Discipline

- Do not push, deploy, modify DNS, or change credentials without a fresh,
  explicit user request naming the target.
- A deploy preview must identify the exact branch/commit, target host, and user
  visible change before production cutover.
- Public account uploads, agent execution, cloud routing, and paid API usage are
  future work. They need explicit quotas, per-user credentials, cost visibility,
  and a separate threat-model review; none exists in the current BioStudio
  Decision Twin client.

## Current BioStudio Verification

~~~powershell
uv run --no-project --python 3.12 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/ -q
Set-Location web
npm test
npm run build
~~~

The React/Vite Decision Twin lives under `web/`; the legacy Streamlit app is
preserved but is not the client being evolved in this worktree.
