# BioStudio Decision Twin Handoff

Last updated: 2026-09-19

## Purpose

BioStudio is evolving from a broad educational drug-discovery workbench into a
research-facing Decision Twin. Its differentiator is decision integrity: it
shows what evidence supports, contradicts, or fails to translate across
biochemical, cellular, in-vivo, and human contexts. It is not a clinical
decision tool, a wet-lab protocol generator, or a substitute for validation.

## Working Checkout

- Worktree: C:\Users\ardit\worktrees\biostudio-backend-readiness
- Branch: feat/decision-twin
- Do not push, deploy, alter DNS, or use credentials without a new explicit
  user request.
- The canonical checkout has an older, untracked frontend Vite starter.
  Preserve it. The tracked Decision Twin client is web.
- Retained evidence files test-full.log.pid and test-full.log.stderr may exist
  locally; leave them untouched and never stage them.

## Implemented Backend

The following commits are local and ordered:

1. ad00c31 - Decision Twin contracts: registered citations, assay context,
   evidence records, deterministic outcomes, provenance digest, compile API.
2. 8c5256c - Bounded Europe PMC connector. It uses the official endpoint,
   drops uncitable records, bounds page size, and wraps source failures.
3. 73d5b17 - Read-only Europe PMC API route:
   GET /v2/sources/europe-pmc/search.
4. 3c2149a - Bounded Open Targets connector using a fixed official GraphQL
   target query and Ensembl gene IDs only.
5. 400ce11 - Read-only Open Targets API route:
   GET /v2/sources/open-targets/targets/{ensembl_id}.
6. d6640e7 - Assay Translation Map contract is included in
   POST /v2/decision-twins/compile.
7. df2a6c5 - Europe PMC abstracts are clipped to the evidence excerpt
   contract rather than causing a validation error.
8. Europe PMC abstracts are parsed into readable text before clipping, so
   harmless source presentation markup does not leak into clients.
9. Current worktree slice - bounded ChEMBL compound-identity retrieval:
   `GET /v2/sources/chembl/compounds/{CHEMBL_ID}`. It only accepts one fixed
   compound identifier and returns a source artifact; it does not query
   activity data or create evidence.

All source routes return source artifacts only. They never create a research
claim, trigger an agent, mutate a study, or execute a model.

## Visual Client

- 7f6a91f tracks the standalone React/Vite client under web.
- 99a3b4b reshapes the client around the Assay Translation Map, Evidence
  Inspector, Integrity Panel, and Verdict Banner.
- The UI is light-first with an explicit dark toggle. It treats missing
  evidence as hollow and translation breaks as visible gaps, not weak data.
- The typed API client is implemented at web/src/lib/decision-twin.ts and calls
  only the deterministic compile endpoint. The development proxy and the
  documented FastAPI command both use port 8000; keep them aligned.
- The Evidence Annotation Workbench lets an operator search Europe PMC, inspect
  a source artifact, and supply a claim plus target, biological system,
  readout, unit, and direction before it can enter the in-browser study. It
  holds no credentials, makes no writes, and does not persist or upload the
  annotation. `web/src/lib/annotation.ts` owns the guard that prevents an
  artifact from being promoted automatically.
- The root route is now a deliberate light-first BioStudio landing experience,
  not the EGFR workspace. Its evidence-network scene explains the product in
  one viewport; `#study` opens the live Decision Twin exemplar. The workspace
  has a separate responsive SVG evidence topology, signal plot, source atlas,
  and click-to-focus record inspector.
- The source atlas distinguishes a successfully connected source from an
  implemented connector whose upstream health is checked per request. ChEMBL
  was observed timing out from this network during this work; the UI must not
  claim that it retrieved a record when it returns a 502.

## Validation

Backend full suite:

~~~powershell
uv run --no-project --python 3.12 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/ -q
~~~

Last verified on 2026-09-19: 254 passed, 1 warning.

Frontend:

~~~powershell
Set-Location web
npm test
npm run build
npm run dev -- --host 127.0.0.1 --port 5173
~~~

Use Vite's local URL for visual review. The FastAPI server must be running for
the compilation API:

~~~powershell
uv run --no-project --python 3.12 --with-requirements requirements.txt uvicorn api.prediction_api:app --host 127.0.0.1 --port 8000
~~~

## Next Work

1. Add the next measured-data connector, not a generic search box. BindingDB
   or ChEMBL activity retrieval needs a separate contract preserving target,
   assay identity, relationship/confidence, value, unit, and citation before
   an operator may annotate it.
2. Add PubChem/UniProt/RCSB metadata lanes only as independently bounded
   source boundaries. Structure metadata is context, never efficacy proof.
3. Only after the multi-source foundation: durable private workspaces,
   controlled public uploads, bounded research agents, and cloud deployment
   architecture with per-user quotas and credentials.

## Current Verification Snapshot

- The React preview at http://127.0.0.1:5173 was visually checked as a
  first-visit landing page in its light theme and at a 390px viewport. The
  responsive Decision Twin workspace was also checked in light and dark themes:
  its public EGFR/osimertinib exemplar compiles to `hold`, visibly showing
  missing biochemical/in-vivo translation stages and cited cellular/human
  conflict without horizontal panning on mobile.
- `npm run build` completed successfully on 2026-09-19.
- The Impeccable detector was run once across the Decision Twin surface and
  returned an empty findings list.
- The focused frontend contract suite is 7 passing tests: incomplete source
  annotations remain inert, operator-authored claims retain citations,
  source-list previews are short without mutating their retained excerpts, and
  the client uses the API's bounded `page_size` search contract. It also tests
  the fixed ChEMBL route and a pure evidence-topology model that cannot fill an
  absent biological layer.
