import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { JSDOM } from "jsdom";
import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import fixture from "../../../contracts/examples/visual-review-analysis.json";
import zeroFixture from "../../../contracts/examples/pushup-movement-observation.json";
import type { AnalysisResponse } from "../src/lib/api/types";
import { LOG_KEY, readLog } from "../src/lib/log/store";

// DOM behavior tests only. CSS and browser/media layout are verified separately.
const require = createRequire(resolve("tests/review-ui.test.ts"));
require.extensions[".css"] = module => { module.exports = new Proxy({}, { get: (_, key) => key === "__esModule" ? false : String(key) }); };
function setup() {
  const dom = new JSDOM('<!doctype html><div id="root"></div>', { url: "http://localhost:3000", pretendToBeVisual: true });
  for (const key of ["window", "document", "navigator", "HTMLElement", "Event", "MouseEvent", "KeyboardEvent", "StorageEvent"] as const) Object.defineProperty(globalThis, key, { value: dom.window[key], configurable: true });
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true, self: dom.window, requestAnimationFrame: dom.window.requestAnimationFrame.bind(dom.window), cancelAnimationFrame: dom.window.cancelAnimationFrame.bind(dom.window) });
  const container = dom.window.document.getElementById("root")!;
  return { dom, container, root: createRoot(container) };
}
function button(container: Element, text: string) {
  const found = [...container.querySelectorAll<HTMLButtonElement>("button")].find(item => item.textContent?.includes(text));
  assert.ok(found, `Button not found: ${text}`); return found;
}
function measured(source: AnalysisResponse = fixture as AnalysisResponse): AnalysisResponse {
  const result = structuredClone(source); result.provenance = { kind: "measured", label: "Controlled test response" }; return result;
}

test("review tabs support keyboard navigation, seeking, and retain the set conversation", async () => {
  const { dom, container, root } = setup();
  const { UploadedResults } = await import("../src/components/uploaded-results");
  const { api } = await import("../src/lib/api/client");
  const oldCoach = api.coach;
  const analysis = measured(); const seeks: number[] = [];
  api.coach = async request => ({ contractVersion: "1.0", sessionId: request.analysis.sessionId, mode: request.mode, provider: "fallback", message: "A retained test reply.", evidence: [], limitations: ["Controlled test"] });
  try {
    await act(async () => root.render(createElement(UploadedResults, { analysis, canSeek: true, onSeek: ms => seeks.push(ms) })));
    const overview = container.querySelector<HTMLButtonElement>('[role="tab"][aria-selected="true"]')!;
    assert.equal(overview.textContent, "Overview");
    await act(async () => button(container, "Watch moment").click());
    assert.equal(seeks[0], analysis.visualReview!.findings[0].evidenceTimestampsMs[0]);
    await act(async () => overview.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: "End", bubbles: true })));
    assert.equal(dom.window.document.activeElement?.textContent, "Coach");
    await act(async () => button(container, "How did my set go?").click());
    assert.match(container.textContent!, /A retained test reply/);
    await act(async () => button(container, "Overview").click());
    await act(async () => button(container, "Coach").click());
    assert.match(container.querySelector('[role="log"]')!.textContent!, /A retained test reply/);
    await act(async () => root.render(createElement(UploadedResults, { analysis: { ...analysis, sessionId: "new-set" }, canSeek: false, onSeek: ms => seeks.push(ms) })));
    assert.ok(!container.querySelector('[role="log"]')!.textContent!.includes("A retained test reply"));
    assert.ok(![...container.querySelectorAll("button")].some(item => item.textContent?.includes("Watch moment")));
  } finally { api.coach = oldCoach; await act(async () => root.unmount()); dom.window.close(); }
});

test("zero reps keeps movement observations visible and synthetic responses never seek", async () => {
  const { dom, container, root } = setup();
  const { UploadedResults } = await import("../src/components/uploaded-results");
  const seeks: number[] = [];
  try {
    await act(async () => root.render(createElement(UploadedResults, { analysis: zeroFixture as AnalysisResponse, canSeek: true, onSeek: ms => seeks.push(ms) })));
    assert.match(container.querySelector('[role="tabpanel"]')!.textContent!, /body line bent/);
    assert.match(container.textContent!, /synthetic data/);
    assert.equal(seeks.length, 0);
    assert.ok(![...container.querySelectorAll("button")].some(item => item.textContent?.includes("Watch moment")));
  } finally { await act(async () => root.unmount()); dom.window.close(); }
});

test("explicit save updates dashboard once, survives remount, and reacts to external deletion", async () => {
  const { dom, container, root } = setup();
  const { SaveSet } = await import("../src/components/save-set");
  const { WorkoutLog } = await import("../src/components/workout-log");
  const analysis = measured();
  try {
    await act(async () => root.render(createElement("div", null, createElement(SaveSet, { analysis, logId: "test-set" }), createElement(WorkoutLog))));
    await act(async () => button(container, "Save set").click());
    assert.equal(readLog(dom.window.localStorage.getItem(LOG_KEY)).sets.length, 1);
    assert.equal(button(container, "Saved ✓").disabled, true);
    assert.equal(container.querySelectorAll('a[href="/sets/test-set"]').length, 1);
    await act(async () => root.render(createElement(WorkoutLog)));
    assert.equal(container.querySelectorAll('a[href="/sets/test-set"]').length, 1);
    dom.window.localStorage.removeItem(LOG_KEY);
    await act(async () => dom.window.dispatchEvent(new dom.window.StorageEvent("storage", { key: LOG_KEY })));
    assert.match(container.textContent!, /Your story starts with a set/);
  } finally { await act(async () => root.unmount()); dom.window.close(); }
});

test("reanalysis explicitly updates a saved set; a quota failure remains visibly unsaved", async () => {
  const { dom, container, root } = setup();
  const { SaveSet } = await import("../src/components/save-set");
  const analysis = measured();
  const originalWrite = dom.window.Storage.prototype.setItem;
  try {
    await act(async () => root.render(createElement(SaveSet, { analysis, logId: "repeat-set" })));
    dom.window.Storage.prototype.setItem = () => { throw new Error("QuotaExceededError"); };
    await act(async () => button(container, "Save set").click());
    assert.match(container.querySelector('[role="alert"]')!.textContent!, /Set not saved/);
    assert.equal(dom.window.localStorage.getItem(LOG_KEY), null);
    dom.window.Storage.prototype.setItem = originalWrite;
    await act(async () => button(container, "Save set").click());
    const next = { ...analysis, sessionId: "new-analysis" };
    await act(async () => root.render(createElement(SaveSet, { analysis: next, logId: "repeat-set" })));
    assert.equal(readLog(dom.window.localStorage.getItem(LOG_KEY)).sets[0].analysis.sessionId, analysis.sessionId);
    await act(async () => button(container, "Update saved set").click());
    const saved = readLog(dom.window.localStorage.getItem(LOG_KEY)).sets;
    assert.equal(saved.length, 1); assert.equal(saved[0].analysis.sessionId, "new-analysis");
  } finally { dom.window.Storage.prototype.setItem = originalWrite; await act(async () => root.unmount()); dom.window.close(); }
});

test("saved summary has no player or seek actions, retains evidence, and deletes only its own set", async () => {
  const { dom, container, root } = setup();
  const { SavedSetReview } = await import("../src/components/saved-set-review");
  const { AppRouterContext } = await import("next/dist/shared/lib/app-router-context.shared-runtime");
  const { saveSet } = await import("../src/lib/log/store");
  const record = { id: "saved", analysis: measured(), analysisAt: "2026-09-27T10:00:00Z", performedDate: "2026-09-26", notes: "A real note", analysisRevision: null };
  saveSet(dom.window.localStorage, record);
  saveSet(dom.window.localStorage, { ...record, id: "keep", analysis: { ...record.analysis, sessionId: "keep" } });
  const navigated: string[] = [];
  const router = { bfcacheId: "test-route", push: (path: string) => navigated.push(path), replace: () => {}, refresh: () => {}, back: () => {}, forward: () => {}, prefetch: () => {}, hmrRefresh: () => {} };
  try {
    await act(async () => root.render(createElement(AppRouterContext.Provider, { value: router }, createElement(SavedSetReview, { id: "saved" }))));
    assert.match(container.textContent!, /Playback and skeleton seeking are unavailable/);
    assert.equal(container.querySelector("video"), null);
    assert.equal(container.querySelectorAll('button').length > 0, true);
    assert.ok(![...container.querySelectorAll("button")].some(item => item.textContent?.includes("Watch moment")));
    assert.ok(container.querySelector('a[href*="replace=saved"]'));
    assert.equal(container.querySelector("textarea")?.value, "A real note");
    await act(async () => button(container, "Delete saved set").click());
    assert.deepEqual(readLog(dom.window.localStorage.getItem(LOG_KEY)).sets.map(set => set.id), ["keep"]);
    assert.deepEqual(navigated, ["/"]);
  } finally { await act(async () => root.unmount()); dom.window.close(); }
});
