const REGIONS = [
  { name: 'Region A', color: '#6d5dfc' },
  { name: 'Region B', color: '#10b981' },
  { name: 'Region C', color: '#f59e0b' },
];

export default function RegionPanel({ regionDemands = [], blackout = false }) {
  const maxDemand = Math.max(...regionDemands, 1);

  return (
    <div className="widget-panel panel-animate">
      <div className="flex items-center justify-between mb-3">
        <h3 className="section-title">Regional Demand</h3>
        {blackout && (
          <span className="row-status row-status-pending">
            Blackout
          </span>
        )}
      </div>
      <p className="section-subtitle">Load distribution across grid nodes</p>
      <div className="space-y-3 mt-3">
        {REGIONS.map((r, i) => {
          const demand = regionDemands[i] ?? 0;
          const pct = (demand / maxDemand) * 100;
          return (
            <div key={r.name}>
              <div className="flex justify-between text-xs mb-1.5 text-slate-500">
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: r.color }} />
                  {r.name}
                </span>
                <span className="text-slate-700 font-semibold tabular-nums">{demand.toFixed(1)} MW</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700 ease-out"
                  style={{ background: r.color, width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
