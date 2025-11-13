import { SystemStats } from '@/types';
import { Cpu, MemoryStick, HardDrive, Network, Clock } from 'lucide-react';

interface Props {
  systemStats: SystemStats | null;
}

export default function SystemMonitor({ systemStats }: Props) {
  if (!systemStats) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Loading system statistics...</p>
      </div>
    );
  }

  const formatUptime = (seconds?: number) => {
    if (!seconds) return 'Unknown';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number) => {
    if (bytes >= 1073741824) {
      return `${(bytes / 1073741824).toFixed(2)} GB`;
    } else if (bytes >= 1048576) {
      return `${(bytes / 1048576).toFixed(2)} MB`;
    } else if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`;
    }
    return `${bytes} B`;
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">System Monitor</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* CPU */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center gap-3 mb-4">
            <Cpu className="text-blue-500" size={24} />
            <h3 className="text-lg font-semibold text-white">CPU</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Usage:</span>
              <span className="text-white font-medium">
                {systemStats.cpu.percent}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Cores:</span>
              <span className="text-white">{systemStats.cpu.count}</span>
            </div>
            {systemStats.cpu.frequency_mhz && (
              <div className="flex justify-between">
                <span className="text-slate-400">Frequency:</span>
                <span className="text-white">
                  {systemStats.cpu.frequency_mhz} MHz
                </span>
              </div>
            )}
            {/* Progress bar */}
            <div className="mt-3">
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${systemStats.cpu.percent}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Memory */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center gap-3 mb-4">
            <MemoryStick className="text-green-500" size={24} />
            <h3 className="text-lg font-semibold text-white">Memory</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Used:</span>
              <span className="text-white font-medium">
                {systemStats.memory.used_mb.toFixed(0)} MB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Available:</span>
              <span className="text-white">
                {systemStats.memory.available_mb.toFixed(0)} MB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Total:</span>
              <span className="text-white">
                {systemStats.memory.total_mb.toFixed(0)} MB
              </span>
            </div>
            <div className="mt-3">
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${systemStats.memory.percent}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Disk */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center gap-3 mb-4">
            <HardDrive className="text-purple-500" size={24} />
            <h3 className="text-lg font-semibold text-white">Disk</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Used:</span>
              <span className="text-white font-medium">
                {systemStats.disk.used_gb.toFixed(1)} GB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Free:</span>
              <span className="text-white">
                {systemStats.disk.free_gb.toFixed(1)} GB
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Total:</span>
              <span className="text-white">
                {systemStats.disk.total_gb.toFixed(1)} GB
              </span>
            </div>
            <div className="mt-3">
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${systemStats.disk.percent}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Network */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center gap-3 mb-4">
            <Network className="text-orange-500" size={24} />
            <h3 className="text-lg font-semibold text-white">Network</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Sent:</span>
              <span className="text-white">
                {formatBytes(systemStats.network.bytes_sent)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Received:</span>
              <span className="text-white">
                {formatBytes(systemStats.network.bytes_recv)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Errors In:</span>
              <span className="text-white">{systemStats.network.errors_in}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Errors Out:</span>
              <span className="text-white">{systemStats.network.errors_out}</span>
            </div>
          </div>
        </div>

        {/* Uptime */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center gap-3 mb-4">
            <Clock className="text-yellow-500" size={24} />
            <h3 className="text-lg font-semibold text-white">Uptime</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">System:</span>
              <span className="text-white text-xl font-semibold">
                {formatUptime(systemStats.uptime_seconds)}
              </span>
            </div>
          </div>
        </div>

        {/* Temperature */}
        {systemStats.temperature && (
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="text-red-500 text-2xl">🌡️</div>
              <h3 className="text-lg font-semibold text-white">Temperature</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">CPU Temp:</span>
                <span className="text-white text-xl font-semibold">
                  {systemStats.temperature}°C
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
