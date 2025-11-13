import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import { Icon, LatLngExpression } from 'leaflet';
import { Telemetry } from '@/types';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in Leaflet with Vite
// Use CDN URLs for marker icons to avoid import issues
const defaultIcon = new Icon({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

interface Props {
  telemetry?: Telemetry;
}

// Component to update map center when drone moves
function MapUpdater({ position }: { position: LatLngExpression }) {
  const map = useMap();

  useEffect(() => {
    map.setView(position, map.getZoom());
  }, [position, map]);

  return null;
}

export default function FlightMap({ telemetry }: Props) {
  const [flightPath, setFlightPath] = useState<LatLngExpression[]>([]);
  const [center, setCenter] = useState<LatLngExpression>([0, 0]);

  useEffect(() => {
    if (telemetry?.latitude && telemetry?.longitude) {
      const newPosition: LatLngExpression = [telemetry.latitude, telemetry.longitude];
      setCenter(newPosition);

      // Add to flight path (limit to last 100 points)
      setFlightPath((prev) => {
        const updated = [...prev, newPosition];
        return updated.slice(-100);
      });
    }
  }, [telemetry?.latitude, telemetry?.longitude]);

  // If no GPS position, show placeholder
  if (!telemetry?.latitude || !telemetry?.longitude) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="aspect-video flex items-center justify-center text-slate-400">
          <div className="text-center">
            <div className="text-4xl mb-2">🗺️</div>
            <div>Waiting for GPS position...</div>
            <div className="text-sm mt-2">
              Map will appear when telemetry includes valid coordinates
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
      <MapContainer
        center={center}
        zoom={16}
        style={{ height: '500px', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Flight path */}
        {flightPath.length > 1 && (
          <Polyline positions={flightPath} color="blue" weight={3} opacity={0.7} />
        )}

        {/* Drone marker */}
        <Marker position={center} icon={defaultIcon}>
          <Popup>
            <div className="text-sm">
              <div className="font-bold mb-1">Drone Position</div>
              <div>Lat: {telemetry.latitude?.toFixed(6)}</div>
              <div>Lon: {telemetry.longitude?.toFixed(6)}</div>
              {telemetry.altitude !== undefined && (
                <div>Alt: {telemetry.altitude.toFixed(1)}m</div>
              )}
              {telemetry.heading !== undefined && (
                <div>Heading: {telemetry.heading.toFixed(0)}°</div>
              )}
            </div>
          </Popup>
        </Marker>

        <MapUpdater position={center} />
      </MapContainer>

      {/* Map info overlay */}
      <div className="absolute top-2 left-2 bg-slate-900/90 backdrop-blur-sm rounded px-3 py-2 text-xs text-white border border-slate-700">
        <div>Lat: {telemetry.latitude?.toFixed(6)}</div>
        <div>Lon: {telemetry.longitude?.toFixed(6)}</div>
        {telemetry.altitude !== undefined && <div>Alt: {telemetry.altitude.toFixed(1)}m</div>}
      </div>
    </div>
  );
}
