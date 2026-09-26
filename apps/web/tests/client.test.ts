import assert from "node:assert/strict";
import test from "node:test";
import { ApiError, createApiClient } from "../src/lib/api/client";

test("health uses the centralized versioned URL", async () => {
  const fetcher: typeof fetch = async (input) => {
    assert.equal(input, "http://localhost:8000/api/v1/health");
    return Response.json({ status: "ok", service: "formcoach-api" });
  };
  assert.equal((await createApiClient("http://localhost:8000/", fetcher).health()).status, "ok");
});

test("video sends multipart and surfaces the 501 placeholder without substituting demo data", async () => {
  const fetcher: typeof fetch = async (_input, init) => {
    assert.ok(init?.body instanceof FormData);
    assert.equal(init.body.get("exerciseHint"), "squat");
    assert.equal(init.headers, undefined);
    return Response.json({ detail: { code: "VIDEO_ANALYSIS_NOT_IMPLEMENTED", message: "Not implemented" } }, { status: 501 });
  };
  await assert.rejects(
    createApiClient("http://localhost:8000", fetcher).analyzeVideo(new File(["demo"], "test.mp4"), "squat"),
    (error: unknown) => error instanceof ApiError && error.status === 501 && error.code === "VIDEO_ANALYSIS_NOT_IMPLEMENTED",
  );
});

test("network failures have an actionable message", async () => {
  const fetcher: typeof fetch = async () => { throw new Error("network failed"); };
  await assert.rejects(createApiClient("http://localhost:8000", fetcher).health(), /backend is running/);
});

test("incompatible successful responses are rejected", async () => {
  const fetcher: typeof fetch = async () => Response.json({ contractVersion: "2.0" });
  await assert.rejects(
    createApiClient("http://localhost:8000", fetcher).analyzeVideo(new File(["demo"], "test.mp4")),
    /unsupported or invalid response/,
  );
});
