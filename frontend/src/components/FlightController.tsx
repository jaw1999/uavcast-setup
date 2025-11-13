import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { telemetryApi } from '@/api/client';
import { MAVLinkStatus } from '@/types';
import { Play, Square, Plus, Trash2, Loader2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import TelemetryDisplay from './TelemetryDisplay';
import FlightMap from './FlightMap';

interface Props {
  mavlinkStats: MAVLinkStatus | null;
}

export default function FlightController({ mavlinkStats }: Props) {
  const [serialPort, setSerialPort] = useState('/dev/ttyACM0');
  const [baudRate, setBaudRate] = useState(57600);
  const [destName, setDestName] = useState('');
  const [destHost, setDestHost] = useState('');
  const [destPort, setDestPort] = useState(14550);
  const [destProtocol, setDestProtocol] = useState<'udp' | 'tcp'>('udp');

  const startMutation = useMutation({
    mutationFn: () => telemetryApi.start({ serial_port: serialPort, baud_rate: baudRate }),
    onSuccess: () => {
      showSuccess('MAVLink routing started successfully');
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to start MAVLink routing');
    },
  });

  const stopMutation = useMutation({
    mutationFn: () => telemetryApi.stop(),
    onSuccess: () => {
      showSuccess('MAVLink routing stopped');
      // Force a small delay to ensure backend has processed the stop
      setTimeout(() => {
        window.location.reload();
      }, 500);
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to stop MAVLink routing');
    },
  });

  const addDestMutation = useMutation({
    mutationFn: () =>
      telemetryApi.addDestination({
        name: destName,
        host: destHost,
        port: destPort,
        protocol: destProtocol,
      }),
    onSuccess: () => {
      setDestName('');
      setDestHost('');
      setDestPort(14550);
      setDestProtocol('udp');
      showSuccess(`Destination '${destName}' added successfully`);
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to add destination');
    },
  });

  const removeDestMutation = useMutation({
    mutationFn: (name: string) => telemetryApi.removeDestination(name),
    onSuccess: (_, name) => {
      showSuccess(`Destination '${name}' removed`);
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to remove destination');
    },
  });

  const handleStart = () => {
    startMutation.mutate();
  };

  const handleStop = () => {
    stopMutation.mutate();
  };

  const handleAddDestination = (e: React.FormEvent) => {
    e.preventDefault();
    addDestMutation.mutate();
  };

  const isRunning = mavlinkStats?.running;

  return (
    <div className="space-y-4 sm:space-y-6">
      <h2 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
        Flight Controller & Telemetry
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Connection Configuration */}
        <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 sm:p-6 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
          <h3 className="relative text-base sm:text-lg font-semibold text-white mb-4">Connection Settings</h3>

          <div className="relative space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Serial Port
              </label>
              <select
                value={serialPort}
                onChange={(e) => setSerialPort(e.target.value)}
                disabled={isRunning}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
              >
                <option value="/dev/ttyACM0">/dev/ttyACM0 (USB)</option>
                <option value="/dev/ttyAMA0">/dev/ttyAMA0 (GPIO)</option>
                <option value="/dev/ttyUSB0">/dev/ttyUSB0</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Baud Rate
              </label>
              <select
                value={baudRate}
                onChange={(e) => setBaudRate(Number(e.target.value))}
                disabled={isRunning}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
              >
                <option value={9600}>9600</option>
                <option value={57600}>57600</option>
                <option value={115200}>115200</option>
                <option value={921600}>921600</option>
              </select>
            </div>

            <div className="relative flex gap-3">
              <button
                onClick={handleStart}
                disabled={isRunning || startMutation.isPending}
                className="relative flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-lg font-semibold shadow-lg hover:shadow-green-500/50 disabled:shadow-none transition-all duration-300 overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-emerald-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300" />
                {startMutation.isPending ? (
                  <Loader2 size={18} className="animate-spin relative z-10" />
                ) : (
                  <Play size={18} className="relative z-10" />
                )}
                <span className="relative z-10">{startMutation.isPending ? 'Starting...' : 'Start'}</span>
              </button>
              <button
                onClick={handleStop}
                disabled={!isRunning || stopMutation.isPending}
                className="relative flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-lg font-semibold shadow-lg hover:shadow-red-500/50 disabled:shadow-none transition-all duration-300 overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-red-400 to-rose-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300" />
                {stopMutation.isPending ? (
                  <Loader2 size={18} className="animate-spin relative z-10" />
                ) : (
                  <Square size={18} className="relative z-10" />
                )}
                <span className="relative z-10">{stopMutation.isPending ? 'Stopping...' : 'Stop'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Status */}
        <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 sm:p-6 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-cyan-500/10 transition-all duration-300">
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
          <h3 className="relative text-base sm:text-lg font-semibold text-white mb-4">Status</h3>

          <div className="relative space-y-3">
            <div className="flex justify-between items-center p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
              <span className="text-slate-300 font-medium">Connection:</span>
              <span
                className={`px-3 py-1.5 rounded-full text-sm font-semibold shadow-lg ${
                  isRunning
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-green-500/50'
                    : 'bg-slate-700/50 text-slate-400'
                }`}
              >
                {isRunning ? 'Running' : 'Stopped'}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
              <span className="text-slate-300 font-medium">Heartbeat:</span>
              <span
                className={`px-3 py-1.5 rounded-full text-sm font-semibold shadow-lg ${
                  mavlinkStats?.heartbeat_received
                    ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-green-500/50'
                    : 'bg-slate-700/50 text-slate-400'
                }`}
              >
                {mavlinkStats?.heartbeat_received ? 'Received' : 'Not Received'}
              </span>
            </div>

            {mavlinkStats?.stats && (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-400">Messages Received:</span>
                  <span className="text-white font-medium">
                    {mavlinkStats.stats.messages_received}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Messages Forwarded:</span>
                  <span className="text-white font-medium">
                    {mavlinkStats.stats.messages_forwarded}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Errors:</span>
                  <span className="text-white font-medium">{mavlinkStats.stats.errors}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Telemetry Destinations */}
      <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-4 sm:p-6 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-300">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
        <h3 className="relative text-base sm:text-lg font-semibold text-white mb-4">Telemetry Destinations</h3>

        {/* Add Destination Form */}
        <form onSubmit={handleAddDestination} className="relative mb-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            <input
              type="text"
              placeholder="Name"
              value={destName}
              onChange={(e) => setDestName(e.target.value)}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
              required
            />
            <input
              type="text"
              placeholder="Host/IP"
              value={destHost}
              onChange={(e) => setDestHost(e.target.value)}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
              required
            />
            <input
              type="number"
              placeholder="Port"
              value={destPort}
              onChange={(e) => setDestPort(Number(e.target.value))}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
              required
            />
            <select
              value={destProtocol}
              onChange={(e) => setDestProtocol(e.target.value as 'udp' | 'tcp')}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
            >
              <option value="udp">UDP</option>
              <option value="tcp">TCP</option>
            </select>
            <button
              type="submit"
              disabled={addDestMutation.isPending}
              className="relative flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 disabled:from-slate-700 disabled:to-slate-700 text-white px-4 py-2.5 rounded-lg font-semibold shadow-lg hover:shadow-blue-500/50 disabled:shadow-none transition-all duration-300 overflow-hidden group"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-cyan-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300" />
              {addDestMutation.isPending ? (
                <Loader2 size={18} className="animate-spin relative z-10" />
              ) : (
                <Plus size={18} className="relative z-10" />
              )}
              <span className="relative z-10">{addDestMutation.isPending ? 'Adding...' : 'Add'}</span>
            </button>
          </div>
        </form>

        {/* Destinations List */}
        <div className="relative space-y-2">
          {mavlinkStats?.destinations && mavlinkStats.destinations.length > 0 ? (
            mavlinkStats.destinations.map((dest) => (
              <div
                key={dest.name}
                className="group/item relative flex items-center justify-between bg-slate-800/50 backdrop-blur rounded-lg p-3 border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/20"
              >
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div
                      className={`w-2.5 h-2.5 rounded-full ${
                        dest.connected ? 'bg-green-500' : 'bg-red-500'
                      }`}
                    />
                    {dest.connected && (
                      <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-green-500 animate-ping opacity-75" />
                    )}
                  </div>
                  <div>
                    <div className="text-white font-semibold">{dest.name}</div>
                    <div className="text-sm text-slate-400 font-mono">
                      {dest.protocol.toUpperCase()}://{dest.host}:{dest.port}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => removeDestMutation.mutate(dest.name)}
                  className="p-2 hover:bg-red-500/20 rounded-lg transition-all duration-300 text-red-400 hover:text-red-300 hover:scale-110"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-slate-400 font-medium">
              No destinations configured
            </div>
          )}
        </div>
      </div>

      {/* Live Telemetry Display */}
      {isRunning && (
        <>
          <div className="mt-4 sm:mt-6">
            <h3 className="text-base sm:text-lg font-semibold text-white mb-4">Live Telemetry</h3>
            {mavlinkStats?.heartbeat_received ? (
              <TelemetryDisplay telemetry={mavlinkStats.telemetry} />
            ) : (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
                <div className="text-slate-400">
                  Waiting for heartbeat from flight controller...
                </div>
                <div className="text-sm text-slate-500 mt-2">
                  Make sure your flight controller is connected and powered on
                </div>
              </div>
            )}
          </div>

          {/* Flight Map */}
          <div className="mt-4 sm:mt-6">
            <h3 className="text-base sm:text-lg font-semibold text-white mb-4">Flight Map</h3>
            {mavlinkStats?.heartbeat_received && mavlinkStats?.telemetry?.latitude ? (
              <FlightMap telemetry={mavlinkStats.telemetry} />
            ) : (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 text-center">
                <div className="text-slate-400">
                  Waiting for GPS data from flight controller...
                </div>
                <div className="text-sm text-slate-500 mt-2">
                  Map will appear once GPS coordinates are received
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
