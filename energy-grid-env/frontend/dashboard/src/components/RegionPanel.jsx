const REGIONS = ['Region A', 'Region B', 'Region C'];

export default function RegionPanel({ regionDemands = [], blackout = false }) {
  const maxDemand = Math.max(...regionDemands, 1);

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-slate-300 font-semibold mb-3 flex items-center gap-2">
        Regional Demand
        {blackout && (
          <span className="text-xs bg-red-900 text-red-300 px-2 py-0.5 rounded-full animate-pulse">
            BLACKOUT
          </span>
        )}
      </h3>
      <div className="space-y-3">
        {REGIONS.map((name, i) => {
          const demand = regionDemands[i] ?? 0;
          const pct = (demand / maxDemand) * 100;
          return (
            <div key={name}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-400">{name}</span>
                <span className="text-slate-300 font-medium">{demand.toFixed(1)} MW</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-violet-500 rounded-full transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
