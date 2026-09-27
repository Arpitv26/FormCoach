"use client";

import { useMemo, useSyncExternalStore } from "react";
import { EMPTY_LOG, LOG_EVENT, LOG_KEY, readLog, STORAGE_UNAVAILABLE } from "./store";

function snapshot() {
  try { return window.localStorage.getItem(LOG_KEY) ?? EMPTY_LOG; }
  catch { return STORAGE_UNAVAILABLE; }
}
function subscribe(notify: () => void) {
  const onStorage = (event: StorageEvent) => { if (event.key === LOG_KEY || event.key === null) notify(); };
  window.addEventListener("storage", onStorage);
  window.addEventListener(LOG_EVENT, notify);
  return () => { window.removeEventListener("storage", onStorage); window.removeEventListener(LOG_EVENT, notify); };
}
export function useWorkoutLog() {
  const raw = useSyncExternalStore(subscribe, snapshot, () => null);
  return useMemo(() => ({ ...readLog(raw), ready: raw !== null }), [raw]);
}
/** Serialize read/modify/write across tabs when Web Locks is available. */
export async function changeLog<T>(change: (storage: Storage) => T): Promise<T> {
  const run = () => {
    let storage: Storage;
    try { storage = window.localStorage; } catch { throw new Error("Device storage is blocked. Your set is not saved."); }
    const result = change(storage);
    window.dispatchEvent(new Event(LOG_EVENT));
    return result;
  };
  return navigator.locks ? navigator.locks.request(LOG_KEY, run) : run();
}
