import { afterEach, describe, expect, it, vi } from "vitest";

import { citationUrl, getChEMBLCompound, searchEuropePmc } from "../src/lib/decision-twin";

describe("Decision Twin source client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the API's bounded page_size contract for literature searches", async () => {
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ records: [] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetch);

    await searchEuropePmc("EGFR resistance", 5);

    expect(fetch).toHaveBeenCalledWith(
      "/v2/sources/europe-pmc/search?query=EGFR%20resistance&page_size=5&study_type=any",
    );
  });

  it("resolves a single ChEMBL compound through the fixed public route", async () => {
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ records: [] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetch);

    await getChEMBLCompound("CHEMBL3353410");

    expect(fetch).toHaveBeenCalledWith("/v2/sources/chembl/compounds/CHEMBL3353410");
  });
});

describe("citationUrl", () => {
  it("encodes the source id it interpolates into the path", () => {
    // Regression: the id arrives from an external source and used to be pasted
    // in raw, so a value carrying a slash or a query character could reshape
    // the URL it was placed into.
    const url = citationUrl({
      source: "europe_pmc",
      source_id: "12345/../../evil?x=1",
      retrieved_at: "2026-09-19T00:00:00Z",
    });

    expect(url).not.toContain("../");
    expect(url).not.toContain("?x=1");
    expect(url?.startsWith("https://europepmc.org/article/MED/")).toBe(true);
  });

  it("routes PMC ids to the PMC path and PMIDs to MED", () => {
    const pmc = citationUrl({ source: "europe_pmc", source_id: "PMC13585410", retrieved_at: "" });
    const med = citationUrl({ source: "europe_pmc", source_id: "42714840", retrieved_at: "" });
    expect(pmc).toContain("/article/PMC/PMC13585410");
    expect(med).toContain("/article/MED/42714840");
  });
});
