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
- Branch: codex/biostudio-backend-readiness
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
8. Current worktree slice - Europe PMC abstracts are parsed into
   readable text before clipping, so harmless source presentation markup does
   not leak into clients.

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

## Validation

Backend full suite:

~~~powershell
uv run --no-project --python 3.12 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/ -q
~~~

Last verified on 2026-09-19: 246 passed, 1 warning.

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

1. Add a public-source-to-operator-annotation flow. A source artifact must not
   automatically become evidence; the operator supplies the claim, assay
   context, readout, unit, and directional interpretation.
2. Only after that foundation: durable private workspaces, controlled public
   uploads, bounded research agents, and cloud deployment architecture.

## Current Verification Snapshot

- The React preview at http://127.0.0.1:5173 was visually checked in both
  dark and light themes. Its public EGFR/osimertinib exemplar compiles to
  `hold` with no browser-console errors, visibly showing missing biochemical
  and in-vivo translation stages and the cited cellular/human conflict.
- `npm run build` completed successfully on 2026-09-19.
- The Impeccable detector was run once across the Decision Twin surface and
  returned an empty findings list.
- The focused frontend contract suite is 4 passing tests: incomplete source
  annotations remain inert, operator-authored claims retain citations,
  source-list previews are short without mutating their retained excerpts, and
  the client uses the API's bounded `page_size` search contract.
