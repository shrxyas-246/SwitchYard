import { useEffect, useState } from "react";
import { api } from "./api";
import Header from "./components/Header";
import Selectors from "./components/Selectors";
import StatCards from "./components/StatCards";
import DetailPanel from "./components/DetailPanel";
import PlatformBoard from "./components/PlatformBoard";
import TrainBoard from "./components/TrainBoard";

export default function App() {
  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);
  const [stations, setStations] = useState([]);
  const [sel, setSel] = useState({ state: "", city: "", station: "" });
  const [data, setData] = useState(null);      // { stats, platforms, trains, suggestions }
  const [detail, setDetail] = useState(null);  // which stat card is expanded
  const [error, setError] = useState(null);

  // load the state list once
  useEffect(() => {
    api("/states").then(setStates).catch((e) => setError(e.message));
  }, []);

  // cascading dropdown handlers
  const onState = async (state) => {
    setSel({ state, city: "", station: "" });
    setCities([]); setStations([]); setData(null); setDetail(null); setError(null);
    if (state) setCities(await api("/cities?state=" + encodeURIComponent(state)));
  };

  const onCity = async (city) => {
    setSel((s) => ({ ...s, city, station: "" }));
    setStations([]); setData(null); setDetail(null);
    if (city) {
      setStations(await api(`/stations?state=${encodeURIComponent(sel.state)}&city=${encodeURIComponent(city)}`));
    }
  };

  const onStation = (station) => {
    setSel((s) => ({ ...s, station }));
    setData(null); setDetail(null);
  };

  // load the board for the chosen station, and refresh every 20s
  useEffect(() => {
    if (!sel.station) return;
    let active = true;
    const load = async () => {
      try {
        const [stats, platforms, trains, suggestions] = await Promise.all([
          api(`/stations/${sel.station}/stats`),
          api(`/stations/${sel.station}/platforms`),
          api(`/stations/${sel.station}/trains`),
          api(`/stations/${sel.station}/suggestions`),
        ]);
        if (active) setData({ stats, platforms, trains, suggestions });
      } catch (e) {
        if (active) setError(e.message);
      }
    };
    load();
    const t = setInterval(load, 20000);
    return () => { active = false; clearInterval(t); };
  }, [sel.station]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <Header />
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Selectors
          states={states} cities={cities} stations={stations} sel={sel}
          onState={onState} onCity={onCity} onStation={onStation}
        />

        {error && (
          <div className="rounded-2xl border border-rose-300 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/40 py-16 text-center text-rose-600 dark:text-rose-400 mb-6">
            Could not reach the API ({error}). Make sure the backend is running on http://localhost:8000.
          </div>
        )}

        {!sel.station && !error && (
          <div className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 py-24 text-center text-slate-500 dark:text-slate-400">
            Select a state, city and station to view the live board.
          </div>
        )}

        {sel.station && data && (
          <>
            <StatCards stats={data.stats} active={detail} onSelect={setDetail} />
            <DetailPanel type={detail} platforms={data.platforms} trains={data.trains} />
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <PlatformBoard platforms={data.platforms} />
              <TrainBoard trains={data.trains} suggestions={data.suggestions} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
