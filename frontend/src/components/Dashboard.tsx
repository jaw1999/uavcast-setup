import { useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import SystemMonitor from './SystemMonitor';
import FlightController from './FlightController';
import VideoSettings from './VideoSettings';
import VPNConfig from './VPNConfig';
import NetworkStatus from './NetworkStatus';
import ConfigProfiles from './ConfigProfiles';
import { Activity, Plane, Video, Shield, Network } from 'lucide-react';

type Tab = 'system' | 'telemetry' | 'video' | 'vpn' | 'network';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('system');
  const { connected, systemStats, mavlinkStats } = useWebSocket();

  const tabs = [
    { id: 'system' as Tab, label: 'System', icon: Activity },
    { id: 'telemetry' as Tab, label: 'Telemetry', icon: Plane },
    { id: 'video' as Tab, label: 'Video', icon: Video },
    { id: 'vpn' as Tab, label: 'VPN', icon: Shield },
    { id: 'network' as Tab, label: 'Network', icon: Network },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="backdrop-blur-xl bg-slate-900/50 border-b border-slate-700/50 px-4 sm:px-6 py-4 sm:py-5 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-3xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent">
              UAVcast-Free
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm mt-1">
              Open-source UAV companion computer software
            </p>
          </div>
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 backdrop-blur border border-slate-700/50">
              <div className="relative">
                <div
                  className={`w-2.5 h-2.5 rounded-full ${
                    connected ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                {connected && (
                  <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-green-500 animate-ping opacity-75" />
                )}
              </div>
              <span className="text-xs sm:text-sm text-slate-200 font-medium">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {systemStats?.temperature && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 backdrop-blur border border-slate-700/50">
                <span className="text-xs sm:text-sm text-slate-400">Temp:</span>
                <span className="text-xs sm:text-sm text-slate-200 font-semibold">
                  {systemStats.temperature}°C
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="backdrop-blur-xl bg-slate-900/30 border-b border-slate-700/50 px-2 sm:px-6">
        <div className="flex gap-2 overflow-x-auto scrollbar-hide">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative flex items-center gap-2 px-4 sm:px-6 py-3 sm:py-4 transition-all duration-300 whitespace-nowrap group ${
                  activeTab === tab.id
                    ? 'text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon
                  size={18}
                  className={`transition-all duration-300 ${
                    activeTab === tab.id ? 'scale-110' : 'group-hover:scale-105'
                  }`}
                />
                <span className="text-sm sm:text-base font-medium">{tab.label}</span>
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500 rounded-full" />
                )}
                {activeTab !== tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-600 opacity-0 group-hover:opacity-50 transition-opacity rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 p-4 sm:p-6 overflow-auto">
        {activeTab === 'system' && (
          <div className="space-y-6">
            <SystemMonitor systemStats={systemStats} />
            <ConfigProfiles />
          </div>
        )}
        {activeTab === 'telemetry' && <FlightController mavlinkStats={mavlinkStats} />}
        {activeTab === 'video' && <VideoSettings />}
        {activeTab === 'vpn' && <VPNConfig />}
        {activeTab === 'network' && <NetworkStatus />}
      </main>
    </div>
  );
}
