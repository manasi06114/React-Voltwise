import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Polygon, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getGridTopology } from '../api/gridApi';

// Fix default marker icons in Leaflet + Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const ICON_COLORS = {
  city: '#6d5dfc',
  solar: '#f59e0b',
  wind: '#3b82f6',
  battery: '#10b981',
  generator: '#ef4444',
};

const ICON_EMOJI = {
  city: '\u{1F3D9}',
  solar: '\u2600\uFE0F',
  wind: '\u{1F32C}\uFE0F',
  battery: '\u{1F50B}',
  generator: '\u26A1',
};

function createIcon(type) {
  const color = ICON_COLORS[type] || '#64748b';
  const size = type === 'city' ? 36 : 28;
  return L.divIcon({
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    html: `<div style="
      width:${size}px;height:${size}px;border-radius:50%;
      background:${color};border:3px solid #fff;
      display:flex;align-items:center;justify-content:center;
      font-size:${size > 30 ? 16 : 13}px;
      box-shadow:0 2px 8px ${color}88;
      color:#fff;font-weight:bold;
    ">${ICON_EMOJI[type] || '?'}</div>`,
  });
}

function getFlowColor(flowMw, maxFlow) {
  const ratio = flowMw / Math.max(maxFlow, 1);
  if (ratio > 0.7) return '#ef4444';
  if (ratio > 0.4) return '#f59e0b';
  return '#10b981';
}

function PopupContent({ node }) {
  const type = node.type;
  return (
    <div style={{ minWidth: 140, fontFamily: 'Inter, sans-serif' }}>
      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4, color: ICON_COLORS[type] }}>
        {ICON_EMOJI[type]} {node.label}
      </div>
      <div style={{ fontSize: 11, color: '#334155', lineHeight: 1.6 }}>
        {type === 'city' && (
          <>
            <div>Demand: <b>{node.demand} MW</b></div>
            <div>Supply: <b>{node.supply} MW</b></div>
            <div>Status: <b style={{ color: node.status === 'surplus' ? '#10b981' : '#ef4444' }}>
              {node.status === 'surplus' ? 'Surplus' : 'Deficit'}
            </b></div>
            {node.has_generator && <div>Backup generator available</div>}
          </>
        )}
        {type === 'solar' && (
          <>
            <div>Output: <b>{node.output} MW</b></div>
            <div>Capacity: {node.capacity} MW</div>
          </>
        )}
        {type === 'wind' && (
          <>
            <div>Output: <b>{node.output} MW</b></div>
            <div>Capacity: {node.capacity} MW</div>
          </>
        )}
        {type === 'battery' && (
          <>
            <div>Charge: <b>{node.charge_pct}%</b></div>
            <div>Capacity: {node.capacity} MWh</div>
          </>
        )}
        {type === 'generator' && (
          <div>Output: <b>{node.output} MW</b></div>
        )}
      </div>
    </div>
  );
}

function AnimatedPolylines({ edges, nodes }) {
  const maxFlow = Math.max(...edges.map(e => e.flow_mw), 1);

  return edges.map((edge, i) => {
    const from = nodes.find(n => n.id === edge.from);
    const to = nodes.find(n => n.id === edge.to);
    if (!from || !to) return null;

    const color = getFlowColor(edge.flow_mw, maxFlow);
    return (
      <Polyline
        key={i}
        positions={[[from.lat, from.lng], [to.lat, to.lng]]}
        pathOptions={{
          color,
          weight: 2.5,
          opacity: 0.7,
          dashArray: '8 12',
          className: 'power-line-animated',
        }}
      />
    );
  });
}

function RegionOverlays({ regions }) {
  return regions.map((r, i) => (
    <Polygon
      key={r.id || i}
      positions={r.bounds}
      pathOptions={{
        color: r.color,
        fillColor: r.color,
        fillOpacity: 0.15,
        weight: 2,
        opacity: 0.6,
      }}
    >
      <Popup>
        <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 11 }}>
          <b>{r.id}</b><br />
          Supply: {r.supply} MW | Demand: {r.demand} MW<br />
          Ratio: {(r.ratio * 100).toFixed(0)}%
        </div>
      </Popup>
    </Polygon>
  ));
}

export default function GridMap({ task, refreshTrigger }) {
  const [topology, setTopology] = useState(null);

  useEffect(() => {
    getGridTopology(task).then(setTopology).catch(() => {});
  }, [task, refreshTrigger]);

  return (
    <div className="widget-panel panel-animate" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: '12px 16px 8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 className="section-title">Pune Smart Grid Map</h3>
            <p className="section-subtitle">Live power distribution across Pune region</p>
          </div>
          <div style={{ display: 'flex', gap: 10, fontSize: 10 }}>
            {Object.entries(ICON_COLORS).map(([type, color]) => (
              <span key={type} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div style={{ height: 420, width: '100%' }}>
        <MapContainer
          center={[18.52, 73.85]}
          zoom={11}
          style={{ height: '100%', width: '100%', borderRadius: '0 0 16px 16px' }}
          zoomControl={true}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {topology && (
            <>
              {/* Region overlays (heatmap) */}
              <RegionOverlays regions={topology.regions || []} />

              {/* Power flow lines */}
              <AnimatedPolylines edges={topology.edges} nodes={topology.nodes} />

              {/* Node markers */}
              {topology.nodes.map(node => (
                <Marker
                  key={node.id}
                  position={[node.lat, node.lng]}
                  icon={createIcon(node.type)}
                >
                  <Popup><PopupContent node={node} /></Popup>
                </Marker>
              ))}
            </>
          )}
        </MapContainer>
      </div>
    </div>
  );
}
