const cls =
  "w-full px-3.5 py-2.5 rounded-xl text-sm border border-slate-200 dark:border-slate-800 " +
  "bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 " +
  "transition disabled:opacity-50 disabled:cursor-not-allowed";

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">{label}</label>
      {children}
    </div>
  );
}

export default function Selectors({ states, cities, stations, sel, onState, onCity, onStation }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <Field label="State">
        <select className={cls} value={sel.state} onChange={(e) => onState(e.target.value)}>
          <option value="">Select state…</option>
          {states.map((x) => <option key={x} value={x}>{x}</option>)}
        </select>
      </Field>
      <Field label="City">
        <select className={cls} value={sel.city} disabled={!sel.state} onChange={(e) => onCity(e.target.value)}>
          <option value="">Select city…</option>
          {cities.map((x) => <option key={x} value={x}>{x}</option>)}
        </select>
      </Field>
      <Field label="Station">
        <select className={cls} value={sel.station} disabled={!sel.city} onChange={(e) => onStation(e.target.value)}>
          <option value="">Select station…</option>
          {stations.map((x) => <option key={x.station_id} value={x.station_id}>{x.station_name}</option>)}
        </select>
      </Field>
    </div>
  );
}
