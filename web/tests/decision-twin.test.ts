import { afterEach, describe, expect, it, vi } from "vitest";

import { getChEMBLCompound, searchEuropePmc } from "../src/lib/decision-twin";

describe("Decision Twin source client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the API's bounded page_size contract for literature searches", async () => {
    const fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ records: [] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetch);

    await searchEuropePmc("EGFR resistance", 5);

    expect(fetch).toHaveBeenCalledWith(
      "/v2/sources/europe-pmc/search?query=EGFR%20resistance&page_size=5",
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
