import { useQuery } from '@tanstack/react-query';
import { networkApi } from '@/api/client';
import { Wifi, Signal, Globe } from 'lucide-react';

export default function NetworkStatus() {
  const { data: interfacesData } = useQuery({
    queryKey: ['network-interfaces'],
    queryFn: () => networkApi.getInterfaces(),
    refetchInterval: 5000,
  });

  const { data: modemData } = useQuery({
    queryKey: ['network-modem'],
    queryFn: () => networkApi.detectModem(),
  });

  const { data: signalData } = useQuery({
    queryKey: ['network-signal'],
    queryFn: () => networkApi.getSignalStrength(),
    refetchInterval: 5000,
    enabled: !!modemData?.data?.modem,
  });

  const { data: connectivityData } = useQuery({
    queryKey: ['network-connectivity'],
    queryFn: () => networkApi.testConnectivity(),
    refetchInterval: 10000,
  });

  const interfaces = interfacesData?.data?.interfaces || [];
  const modem = modemData?.data?.modem;
  const signal = signalData?.data?.signal;
  const connectivity = connectivityData?.data;

  const getInterfaceIcon = (type: string) => {
    switch (type) {
      case 'wifi':
        return <Wifi size={20} />;
      case 'cellular':
        return <Signal size={20} />;
      default:
        return <Globe size={20} />;
    }
  };

  const getInterfaceColor = (state: string) => {
    switch (state.toLowerCase()) {
      case 'up':
        return 'text-green-500';
      case 'down':
        return 'text-red-500';
      default:
        return 'text-slate-500';
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Network Status</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connectivity Test */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Internet Connectivity</h3>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Status:</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  connectivity?.status === 'online'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-red-500/20 text-red-400'
                }`}
              >
                {connectivity?.status === 'online' ? 'Online' : 'Offline'}
              </span>
            </div>

            {connectivity?.packet_loss !== undefined && (
              <div className="flex justify-between">
                <span className="text-slate-400">Packet Loss:</span>
                <span className="text-white">{connectivity.packet_loss}%</span>
              </div>
            )}

            {connectivity?.avg_rtt_ms && (
              <div className="flex justify-between">
                <span className="text-slate-400">Latency:</span>
                <span className="text-white">{connectivity.avg_rtt_ms.toFixed(1)} ms</span>
              </div>
            )}
          </div>
        </div>

        {/* Modem Information */}
        {modem && (
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">Cellular Modem</h3>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-400">Type:</span>
                <span className="text-white capitalize">{modem.type}</span>
              </div>

              {modem.manufacturer && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Manufacturer:</span>
                  <span className="text-white">{modem.manufacturer}</span>
                </div>
              )}

              {modem.model && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Model:</span>
                  <span className="text-white">{modem.model}</span>
                </div>
              )}

              {modem.signal_quality && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Signal:</span>
                  <span className="text-white">{modem.signal_quality}</span>
                </div>
              )}

              {signal && (
                <>
                  {signal.rssi && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">RSSI:</span>
                      <span className="text-white">{signal.rssi}</span>
                    </div>
                  )}
                  {signal.rsrp && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">RSRP:</span>
                      <span className="text-white">{signal.rsrp}</span>
                    </div>
                  )}
                  {signal.rsrq && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">RSRQ:</span>
                      <span className="text-white">{signal.rsrq}</span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Network Interfaces */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Network Interfaces</h3>

        <div className="space-y-3">
          {interfaces.length > 0 ? (
            interfaces.map((iface: any) => (
              <div
                key={iface.name}
                className="bg-slate-700 rounded-lg p-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <div className={getInterfaceColor(iface.state)}>
                    {getInterfaceIcon(iface.type)}
                  </div>
                  <div>
                    <div className="text-white font-medium">{iface.name}</div>
                    <div className="text-sm text-slate-400 capitalize">
                      {iface.type} • {iface.state}
                    </div>
                    {iface.mac && (
                      <div className="text-xs text-slate-500 font-mono">{iface.mac}</div>
                    )}
                  </div>
                </div>

                <div className="text-right">
                  {iface.ip_addresses && iface.ip_addresses.length > 0 ? (
                    iface.ip_addresses.map((ip: any, idx: number) => (
                      <div key={idx} className="text-sm text-white font-mono">
                        {ip.address}
                        {ip.prefix && `/${ip.prefix}`}
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-slate-500">No IP</div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-slate-400">
              No network interfaces detected
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
