import { useEffect, useState } from "react";

export default function Header() {
  const [clock, setClock] = useState("—");

  useEffect(() => {
    const tick = () => {
      const utcMs = Date.now();
      const istMs = utcMs + (5 * 60 + 30) * 60 * 1000; // UTC+5:30
      const ist   = new Date(istMs);
      setClock("IST " + String(ist.getUTCHours()).padStart(2, "0") + ":" + String(ist.getUTCMinutes()).padStart(2, "0"));
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, []);

  const toggleTheme = () => {
    const html = document.documentElement;
    html.classList.toggle("dark");
    localStorage.setItem("theme", html.classList.contains("dark") ? "dark" : "light");
  };

  return (
    <header className="sticky top-0 z-10 backdrop-blur border-b border-slate-200/70 dark:border-slate-800/70 bg-white/70 dark:bg-slate-950/70">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
          <span className="text-lg font-bold tracking-tight">Switchyard</span>
          <span className="text-xs font-normal text-slate-500 dark:text-slate-400 mt-0.5">Station Control</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm tabular-nums text-slate-500 dark:text-slate-400">{clock}</span>
          <button onClick={toggleTheme} aria-label="Toggle theme"
            className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <svg className="w-4 h-4 hidden dark:block" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
            </svg>
            <svg className="w-4 h-4 block dark:hidden" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}