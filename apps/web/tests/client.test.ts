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
    assert.equal(init.body.get("exerciseHint"), "push-up");
    assert.equal(init.headers, undefined);
    return Response.json({ detail: { code: "VIDEO_ANALYSIS_NOT_IMPLEMENTED", message: "Not implemented" } }, { status: 501 });
  };
  await assert.rejects(
    createApiClient("http://localhost:8000", fetcher).analyzeVideo(new File(["demo"], "test.mp4"), "push-up"),
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


test("upload timeout is five minutes; health remains fifteen seconds", async (t) => {
  const durations: number[] = [];
  t.mock.method(AbortSignal, "timeout", (ms: number) => { durations.push(ms); return new AbortController().signal; });
  const api = createApiClient("http://localhost:8000", async () => Response.json({ contractVersion: "1.0" }));
  await api.health();
  await api.analyzeVideo(new File(["video"], "clip.mp4"), "push-up");
  assert.deepEqual(durations, [15_000, 300_000]);
});
test("caller cancellation is distinct from network failure", async () => {
  const controller = new AbortController();
  controller.abort();
  let called = false;
  const api = createApiClient("http://localhost:8000", async () => { called = true; return Response.json({}); });
  await assert.rejects(api.analyzeVideo(new File(["video"], "clip.mp4"), "push-up", controller.signal),
    (error: unknown) => error instanceof ApiError && error.code === "REQUEST_ABORTED");
  assert.equal(called, false);
});
test("deadline covers reading the response body", async (t) => {
  const deadline = new AbortController();
  t.mock.method(AbortSignal, "timeout", () => deadline.signal);
  const response = Response.json({});
  t.mock.method(response, "json", async () => {
    deadline.abort(new DOMException("timeout", "TimeoutError"));
    throw deadline.signal.reason;
  });
  const api = createApiClient("http://localhost:8000", async () => response);
  await assert.rejects(api.analyzeVideo(new File(["video"], "clip.mp4"), "push-up"),
    (error: unknown) => error instanceof ApiError && error.code === "REQUEST_TIMEOUT");
});

test("detailed coaching gets fifty seconds; live keeps fifteen and both retain cancellation", async (t) => {
  const durations: number[] = [];
  t.mock.method(AbortSignal, "timeout", (ms: number) => { durations.push(ms); return new AbortController().signal; });
  const bodies: unknown[] = [];
  const signals: AbortSignal[] = [];
  const api = createApiClient("http://localhost:8000", async (_input, init) => {
    assert.equal((init?.headers as Record<string, string>)["Content-Type"], "application/json");
    bodies.push(JSON.parse(init!.body as string));
    signals.push(init!.signal!);
    return Response.json({ contractVersion: "1.0" });
  });
  const controller = new AbortController();
  const { getMockAnalysis } = await import("../src/lib/api/mock");
  const analysis = getMockAnalysis();
  await api.coach({ analysis, mode: "summary" }, controller.signal);
  await api.analyzeLiveBatch({ sessionId: "test", exerciseHint: "push-up", frames: [], imageWidth: 640, imageHeight: 480, isFinal: true }, controller.signal);
  assert.deepEqual(durations, [50_000, 15_000]);
  assert.equal(bodies.length, 2);
  controller.abort();
  assert.ok(signals.every((signal) => signal.aborted));
});
