import type { SavedSet } from "./store";
import { localDate } from "./store";
/** Calendar arithmetic at noon avoids UTC date drift and DST-length assumptions. */
export function activitySeries(sets: SavedSet[], today: string, days: number) {
  const end = new Date(`${today}T12:00:00`);
  return Array.from({ length: days }, (_, index) => {
    const day = new Date(end); day.setDate(end.getDate() - (days - index - 1));
    const date = localDate(day);
    const entries = sets.filter(set => set.performedDate === date);
    return { date, sets: entries.length, reps: entries.some(set => set.analysis.summary.totalReps !== null) ? entries.reduce((sum, set) => sum + (set.analysis.summary.totalReps ?? 0), 0) : null, unknown: entries.filter(set => set.analysis.summary.totalReps === null).length };
  });
}
