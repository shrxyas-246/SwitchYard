const Grid = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
    <rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" />
    <rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" />
  </svg>
);
const Check = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="9" /><path d="m8.5 12 2.4 2.4 4.6-5.1" />
  </svg>
);
const Ban = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
    <circle cx="12" cy="12" r="9" /><path d="m6 6 12 12" />
  </svg>
);
const Clock = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="9" /><path d="M12 7.5V12l3 2" />
  </svg>
);

export default function StatCards({ stats, active, onSelect }) {
  const cards = [
    { key: "platforms", label: "Platforms", value: stats.total_platforms, valueCls: "", iconCls: "text-slate-400", Icon: Grid },
    { key: "free", label: "Free", value: stats.free, valueCls: "text-emerald-600 dark:text-emerald-400", iconCls: "text-emerald-500", Icon: Check },
    { key: "occupied", label: "Occupied", value: stats.occupied, valueCls: "text-rose-600 dark:text-rose-400", iconCls: "text-rose-500", Icon: Ban },
    { key: "arriving", label: "Arriving · 1h", value: stats.arriving_next_hour, valueCls: "", iconCls: "text-amber-500", Icon: Clock },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map(({ key, label, value, valueCls, iconCls, Icon }) => (
        <button key={key}
          onClick={() => onSelect(active === key ? null : key)}
          className={
            "text-left rounded-2xl border bg-white dark:bg-slate-900 p-4 transition hover:ring-2 " +
            (active === key
              ? "border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-500/20"
              : "border-slate-200 dark:border-slate-800 hover:ring-slate-200 dark:hover:ring-slate-700")
          }>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
            <span className={iconCls}><Icon /></span>
          </div>
          <div className={"text-3xl font-bold tracking-tight " + valueCls}>{value ?? 0}</div>
        </button>
      ))}
    </div>
  );
}