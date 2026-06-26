import { STATUS, fmt } from "../api";

function Chip({ txt, cls }) {
  return <span className={"inline-block text-xs font-medium px-2.5 py-1 rounded-full " + cls}>{txt}</span>;
}

export default function DetailPanel({ type, platforms, trains }) {
  if (!type) return null;

  let title = "";
  let content;

  if (type === "free") {
    title = "Free platforms";
    const list = platforms.filter((p) => p.status === "free").map((p) => p.platform_no);
    content = list.length
      ? list.map((n) => <Chip key={n} txt={"P" + n} cls={STATUS.free} />)
      : <span className="text-slate-400 text-sm">None</span>;
  } else if (type === "occupied") {
    title = "Occupied platforms";
    const occ = platforms.filter((p) => p.status === "occupied").map((p) => p.platform_no);
    content = occ.length
      ? occ.map((n) => {
          const t = trains.find((x) => String(x.platform) === String(n));
          return <Chip key={n} txt={"P" + n + (t ? " · " + t.train_name : "")} cls={STATUS.occupied} />;
        })
      : <span className="text-slate-400 text-sm">None</span>;
  } else if (type === "arriving") {
    title = "Arriving in the next hour";
    const now = Date.now();
    const soon = trains.filter((t) => {
      const a = new Date(t.arrival_time).getTime();
      return a >= now && a <= now + 3600000;
    });
    content = soon.length
      ? soon.map((t) => <Chip key={t.train_id} txt={t.train_name + " · " + fmt(t.arrival_time)} cls={STATUS.boarding} />)
      : <span className="text-slate-400 text-sm">None</span>;
  } else {
    title = "Platform breakdown";
    const f = platforms.filter((p) => p.status === "free").length;
    const b = platforms.filter((p) => p.status === "boarding").length;
    const o = platforms.filter((p) => p.status === "occupied").length;
    content = [
      <Chip key="f" txt={f + " free"} cls={STATUS.free} />,
      <Chip key="b" txt={b + " arriving"} cls={STATUS.boarding} />,
      <Chip key="o" txt={o + " occupied"} cls={STATUS.occupied} />,
    ];
  }

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 mb-6">
      <div className="text-sm font-semibold mb-3">{title}</div>
      <div className="flex flex-wrap gap-2">{content}</div>
    </div>
  );
}