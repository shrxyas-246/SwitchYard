import { STATUS, fmt } from "../api";

function Th({ children, className = "" }) {
  return <th className={"text-left font-medium py-2.5 px-3 " + className}>{children}</th>;
}

export default function TrainBoard({ trains, suggestions }) {
  const sug = {};
  suggestions.forEach((s) => { sug[s.train_id] = s; });

  return (
    <div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden">
      <h2 className="text-sm font-semibold px-5 pt-5 pb-3">Train board</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 dark:text-slate-400 border-y border-slate-100 dark:border-slate-800">
              <Th className="px-5">Train</Th><Th>Arr</Th><Th>Dep</Th><Th>Exp</Th><Th>Plt</Th><Th>Sugg</Th><Th className="px-5">Status</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {trains.map((t) => {
              const status = (t.status || "scheduled").toLowerCase();
              const s = sug[t.train_id];
              return (
                <tr key={t.train_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="px-5 py-3">
                    <div className="font-medium">{t.train_name}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">{t.train_id}</div>
                  </td>
                  <td className="px-3 py-3 tabular-nums">{fmt(t.arrival_time)}</td>
                  <td className="px-3 py-3 tabular-nums">{fmt(t.departure_time)}</td>
                  <td className="px-3 py-3 tabular-nums">{fmt(t.expected_arrival_time)}</td>
                  <td className="px-3 py-3">{t.platform ?? "—"}</td>
                  <td className="px-3 py-3">
                    {s
                      ? <span title={s.reason} className="text-emerald-600 dark:text-emerald-400 font-semibold cursor-help">→ P{s.suggested_platform}</span>
                      : <span className="text-slate-400">—</span>}
                  </td>
                  <td className="px-5 py-3">
                    <span className={"inline-block text-xs font-medium px-2.5 py-1 rounded-full capitalize " + (STATUS[status] || STATUS.scheduled)}>
                      {status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
