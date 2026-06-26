import { STATUS } from "../api";

function Legend({ color, label }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={"h-2.5 w-2.5 rounded-sm " + color}></span>{label}
    </span>
  );
}

export default function PlatformBoard({ platforms }) {
  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
      <h2 className="text-sm font-semibold mb-4">Platform status</h2>
      <div className="flex flex-wrap gap-2.5">
        {platforms.map((p) => (
          <div key={p.platform_no}
            className={"h-10 w-10 rounded-xl flex items-center justify-center text-sm font-semibold " + STATUS[p.status]}>
            {p.platform_no}
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-5 text-xs text-slate-500 dark:text-slate-400">
        <Legend color="bg-emerald-500" label="Free" />
        <Legend color="bg-amber-500" label="Arriving" />
        <Legend color="bg-rose-500" label="Occupied" />
      </div>
    </div>
  );
}