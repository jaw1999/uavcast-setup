import { Telemetry } from '@/types';
import { Gauge, Navigation, Battery, Satellite, AlertCircle } from 'lucide-react';

interface Props {
  telemetry?: Telemetry;
}

export default function TelemetryDisplay({ telemetry }: Props) {
  if (!telemetry) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="text-center text-slate-400">
          No telemetry data available. Connect flight controller to see live data.
        </div>
      </div>
    );
  }

  const getGPSFixType = (fix: number | undefined) => {
    if (!fix) return 'No Fix';
    switch (fix) {
      case 0:
      case 1:
        return 'No Fix';
      case 2:
        return '2D Fix';
      case 3:
        return '3D Fix';
      case 4:
        return 'DGPS';
      case 5:
        return 'RTK Float';
      case 6:
        return 'RTK Fixed';
      default:
        return 'Unknown';
    }
  };

  const getBatteryColor = (remaining?: number) => {
    if (!remaining) return 'text-slate-400';
    if (remaining > 50) return 'text-green-400';
    if (remaining > 20) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Altitude & Speed */}
      <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <div className="relative flex items-center gap-2 mb-3">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Gauge className="text-blue-400" size={20} />
          </div>
          <h4 className="font-semibold text-white">Flight Data</h4>
        </div>
        <div className="relative space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-400">Altitude:</span>
            <span className="text-white font-mono">
              {telemetry.altitude !== null && telemetry.altitude !== undefined
                ? `${telemetry.altitude.toFixed(1)} m`
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Ground Speed:</span>
            <span className="text-white font-mono">
              {telemetry.groundspeed !== null && telemetry.groundspeed !== undefined
                ? `${telemetry.groundspeed.toFixed(1)} m/s`
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Air Speed:</span>
            <span className="text-white font-mono">
              {telemetry.airspeed !== null && telemetry.airspeed !== undefined
                ? `${telemetry.airspeed.toFixed(1)} m/s`
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Climb Rate:</span>
            <span className="text-white font-mono">
              {telemetry.climb_rate !== null && telemetry.climb_rate !== undefined
                ? `${telemetry.climb_rate.toFixed(1)} m/s`
                : '--'}
            </span>
          </div>
        </div>
      </div>

      {/* Heading & Position */}
      <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <div className="relative flex items-center gap-2 mb-3">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Navigation className="text-purple-400" size={20} />
          </div>
          <h4 className="font-semibold text-white">Navigation</h4>
        </div>
        <div className="relative space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-400">Heading:</span>
            <span className="text-white font-mono">
              {telemetry.heading !== null && telemetry.heading !== undefined
                ? `${telemetry.heading.toFixed(0)}°`
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Latitude:</span>
            <span className="text-white font-mono text-sm">
              {telemetry.latitude !== null && telemetry.latitude !== undefined
                ? telemetry.latitude.toFixed(6)
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Longitude:</span>
            <span className="text-white font-mono text-sm">
              {telemetry.longitude !== null && telemetry.longitude !== undefined
                ? telemetry.longitude.toFixed(6)
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Throttle:</span>
            <span className="text-white font-mono">
              {telemetry.throttle !== null && telemetry.throttle !== undefined
                ? `${telemetry.throttle}%`
                : '--'}
            </span>
          </div>
        </div>
      </div>

      {/* Battery */}
      <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-green-500/10 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <div className="relative flex items-center gap-2 mb-3">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <Battery className="text-green-400" size={20} />
          </div>
          <h4 className="font-semibold text-white">Battery</h4>
        </div>
        <div className="relative space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-400">Voltage:</span>
            <span className="text-white font-mono">
              {telemetry.battery_voltage !== null &&
              telemetry.battery_voltage !== undefined
                ? `${telemetry.battery_voltage.toFixed(2)} V`
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Current:</span>
            <span className="text-white font-mono">
              {telemetry.battery_current !== null &&
              telemetry.battery_current !== undefined
                ? `${telemetry.battery_current.toFixed(2)} A`
                : '--'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Remaining:</span>
            <span className={`font-mono ${getBatteryColor(telemetry.battery_remaining)}`}>
              {telemetry.battery_remaining !== null &&
              telemetry.battery_remaining !== undefined
                ? `${telemetry.battery_remaining}%`
                : '--'}
            </span>
          </div>
          {telemetry.battery_remaining !== null &&
            telemetry.battery_remaining !== undefined && (
              <div className="mt-2">
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      telemetry.battery_remaining > 50
                        ? 'bg-green-500'
                        : telemetry.battery_remaining > 20
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${telemetry.battery_remaining}%` }}
                  />
                </div>
              </div>
            )}
        </div>
      </div>

      {/* GPS */}
      <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-orange-500/10 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-amber-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <div className="relative flex items-center gap-2 mb-3">
          <div className="p-2 bg-orange-500/20 rounded-lg">
            <Satellite className="text-orange-400" size={20} />
          </div>
          <h4 className="font-semibold text-white">GPS</h4>
        </div>
        <div className="relative space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-400">Fix Type:</span>
            <span
              className={`font-medium ${
                telemetry.gps_fix_type && telemetry.gps_fix_type >= 3
                  ? 'text-green-400'
                  : 'text-red-400'
              }`}
            >
              {getGPSFixType(telemetry.gps_fix_type)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Satellites:</span>
            <span className="text-white font-mono">
              {telemetry.gps_satellites !== null && telemetry.gps_satellites !== undefined
                ? telemetry.gps_satellites
                : '--'}
            </span>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-yellow-500/10 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/5 to-amber-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <div className="relative flex items-center gap-2 mb-3">
          <div className="p-2 bg-yellow-500/20 rounded-lg">
            <AlertCircle className="text-yellow-400" size={20} />
          </div>
          <h4 className="font-semibold text-white">Status</h4>
        </div>
        <div className="relative space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-slate-400">Armed:</span>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                telemetry.armed
                  ? 'bg-red-500/20 text-red-400'
                  : 'bg-green-500/20 text-green-400'
              }`}
            >
              {telemetry.armed ? 'ARMED' : 'DISARMED'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Mode:</span>
            <span className="text-white font-mono">
              {telemetry.mode !== null && telemetry.mode !== undefined
                ? telemetry.mode
                : '--'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
