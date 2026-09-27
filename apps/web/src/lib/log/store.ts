import Ajv2020 from "ajv/dist/2020";
import schema from "../../../../../contracts/analysis.schema.json";
import type { AnalysisResponse } from "../api/types";

export const LOG_KEY = "formcoach.workout-log.v1";
export const LOG_EVENT = "formcoach:workout-log";
const validateAnalysis = new Ajv2020({ strict: false }).compile<AnalysisResponse>(schema);
export type SavedSet = {
  id: string;
  analysisAt: string;
  performedDate: string;
  notes: string;
  /** The API currently has no analyzer revision. Never substitute the wire version. */
  analysisRevision: string | null;
  analysis: AnalysisResponse;
};
type StoragePort = Pick<Storage, "getItem" | "setItem">;
type Envelope = { version: 1; sets: unknown[] };
export type LogView = { sets: SavedSet[]; error: string | null; skipped: number };
export const EMPTY_LOG = '{"version":1,"sets":[]}';
export const STORAGE_UNAVAILABLE = "storage-unavailable";
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === "object" && !Array.isArray(value);
export function validDate(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T12:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}
export function localDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
export function isSavedSet(value: unknown): value is SavedSet {
  if (!object(value) || typeof value.id !== "string" || !/^[\w-]{1,100}$/.test(value.id)
    || typeof value.analysisAt !== "string" || !Number.isFinite(Date.parse(value.analysisAt))
    || !validDate(value.performedDate) || typeof value.notes !== "string" || value.notes.length > 1000
    || !(value.analysisRevision === null || typeof value.analysisRevision === "string")) return false;
  if (!validateAnalysis(value.analysis)) return false;
  const analysis = value.analysis;
  return analysis.provenance.kind === "measured" && analysis.status !== "not_implemented"
    && !!analysis.exercise && (analysis.summary.totalReps === null || analysis.summary.totalReps === analysis.reps.length);
}
function envelope(raw: string | null): Envelope {
  if (!raw) return { version: 1, sets: [] };
  let value: unknown;
  try { value = JSON.parse(raw); } catch { throw new Error("Your saved log could not be read. Existing data was kept unchanged."); }
  if (!object(value) || value.version !== 1 || !Array.isArray(value.sets)) {
    throw new Error("This saved log uses an unsupported format. Existing data was kept unchanged.");
  }
  return { version: 1, sets: value.sets };
}
export function readLog(raw: string | null): LogView {
  if (raw === STORAGE_UNAVAILABLE) return { sets: [], skipped: 0, error: "Device storage is unavailable. Your results can still be reviewed, but won’t be saved." };
  try {
    const data = envelope(raw);
    const ids = new Set<string>(), sessions = new Set<string>();
    const sets = data.sets.filter(isSavedSet).filter(set => {
      if (ids.has(set.id) || sessions.has(set.analysis.sessionId)) return false;
      ids.add(set.id); sessions.add(set.analysis.sessionId); return true;
    });
    return { sets, skipped: data.sets.length - sets.length, error: null };
  } catch (error) { return { sets: [], skipped: 0, error: (error as Error).message }; }
}
export function saveSet(storage: StoragePort, record: SavedSet, replace = false): SavedSet {
  if (!isSavedSet(record)) throw new Error("This set is not ready to save. Check the performed date and analysis.");
  // Project explicitly: no video, object URL, raw poses, or chat can enter the log.
  const safe: SavedSet = { id: record.id, analysisAt: record.analysisAt, performedDate: record.performedDate,
    notes: record.notes, analysisRevision: record.analysisRevision, analysis: record.analysis };
  const data = envelope(storage.getItem(LOG_KEY));
  const existing = data.sets.find((item): item is SavedSet => isSavedSet(item) && item.id === safe.id);
  const duplicate = data.sets.find((item): item is SavedSet => isSavedSet(item) && item.analysis.sessionId === safe.analysis.sessionId && item.id !== safe.id);
  if (duplicate) throw new Error("This analysis is already saved. Open it in your workout log.");
  if (replace && !existing) throw new Error("The saved set no longer exists. Choose Save as another set to create a new entry.");
  if (existing && (existing.analysis.exercise?.id !== safe.analysis.exercise?.id || existing.analysis.source.type !== safe.analysis.source.type)) {
    throw new Error("This analysis doesn’t match the saved exercise and source. Save it as another set instead.");
  }
  if (existing && existing.analysis.sessionId !== safe.analysis.sessionId && !replace) {
    throw new Error("A previous analysis is already saved for this set. Choose Update saved set.");
  }
  const entries = existing ? data.sets.map(item => item === existing ? safe : item) : [...data.sets, safe];
  try { storage.setItem(LOG_KEY, JSON.stringify({ version: 1, sets: entries })); }
  catch { throw new Error("Set not saved. Device storage may be full or blocked. Free space or allow storage, then try again."); }
  return safe;
}
export function deleteSet(storage: StoragePort, id: string) {
  const data = envelope(storage.getItem(LOG_KEY));
  try { storage.setItem(LOG_KEY, JSON.stringify({ version: 1, sets: data.sets.filter(item => !isSavedSet(item) || item.id !== id) })); }
  catch { throw new Error("The set could not be deleted. Device storage may be blocked. Try again."); }
}
