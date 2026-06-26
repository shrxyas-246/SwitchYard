// One place for the backend address + shared helpers.
const API = "http://localhost:8000/api";

export async function api(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(res.status + " " + res.statusText);
  return res.json();
}

// ISO datetime -> "HH:MM" in IST (UTC+5:30)
export function fmt(iso) {
  if (!iso) return "—";
  const utcMs = new Date(iso).getTime();
  const istMs = utcMs + (5 * 60 + 30) * 60 * 1000; // shift by +5h30m
  const ist   = new Date(istMs);
  return String(ist.getUTCHours()).padStart(2, "0") + ":" + String(ist.getUTCMinutes()).padStart(2, "0");
}

// status -> tailwind classes, reused by tiles, badges and chips
export const STATUS = {
  free:      "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400",
  boarding:  "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400",
  occupied:  "bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400",
  scheduled: "bg-sky-100 text-sky-700 dark:bg-sky-950/50 dark:text-sky-400",
  departed:  "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
};
