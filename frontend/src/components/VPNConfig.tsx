import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { vpnApi } from '@/api/client';
import { Shield, Check, X } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';

type VPNProvider = 'zerotier' | 'tailscale' | 'wireguard';

export default function VPNConfig() {
  const [provider, setProvider] = useState<VPNProvider>('zerotier');
  const [networkId, setNetworkId] = useState('');
  const [authKey, setAuthKey] = useState('');
  const [wgConfig, setWgConfig] = useState('');

  const { data: statusData, refetch: refetchStatus } = useQuery({
    queryKey: ['vpn-status'],
    queryFn: () => vpnApi.getStatus(),
    refetchInterval: 3000,
  });

  const connectZeroTierMutation = useMutation({
    mutationFn: () => vpnApi.connectZeroTier(networkId),
    onSuccess: () => {
      refetchStatus();
      showSuccess('ZeroTier connection initiated. Check status for IP assignment.');
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to connect to ZeroTier');
    },
  });

  const connectTailscaleMutation = useMutation({
    mutationFn: () => vpnApi.connectTailscale(authKey),
    onSuccess: () => {
      refetchStatus();
      showSuccess('Tailscale connected successfully');
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to connect to Tailscale');
    },
  });

  const connectWireGuardMutation = useMutation({
    mutationFn: () => vpnApi.connectWireGuard(wgConfig),
    onSuccess: () => {
      refetchStatus();
      showSuccess('WireGuard connected successfully');
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to connect to WireGuard');
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: () => vpnApi.disconnect(),
    onSuccess: () => {
      refetchStatus();
      showSuccess('VPN disconnected');
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to disconnect VPN');
    },
  });

  const handleConnect = () => {
    if (provider === 'zerotier') {
      connectZeroTierMutation.mutate();
    } else if (provider === 'tailscale') {
      connectTailscaleMutation.mutate();
    } else if (provider === 'wireguard') {
      connectWireGuardMutation.mutate();
    }
  };

  const vpnStatus = statusData?.data;
  const isConnected = vpnStatus?.status === 'connected';

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">VPN Configuration</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* VPN Status */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="text-blue-500" size={24} />
            <h3 className="text-lg font-semibold text-white">VPN Status</h3>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Status:</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-2 ${
                  isConnected
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-slate-700 text-slate-400'
                }`}
              >
                {isConnected ? <Check size={16} /> : <X size={16} />}
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            {vpnStatus?.provider && (
              <div className="flex justify-between">
                <span className="text-slate-400">Provider:</span>
                <span className="text-white font-medium capitalize">
                  {vpnStatus.provider}
                </span>
              </div>
            )}

            {vpnStatus?.ip_address && (
              <div className="flex justify-between">
                <span className="text-slate-400">IP Address:</span>
                <span className="text-white font-mono">{vpnStatus.ip_address}</span>
              </div>
            )}

            {vpnStatus?.network_id && (
              <div className="flex justify-between">
                <span className="text-slate-400">Network ID:</span>
                <span className="text-white font-mono text-sm">
                  {vpnStatus.network_id}
                </span>
              </div>
            )}

            {isConnected && (
              <button
                onClick={() => disconnectMutation.mutate()}
                disabled={disconnectMutation.isPending}
                className="w-full bg-red-600 hover:bg-red-700 disabled:bg-slate-600 text-white px-4 py-2 rounded font-medium transition-colors mt-4"
              >
                Disconnect
              </button>
            )}
          </div>
        </div>

        {/* VPN Configuration */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Connect to VPN</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                VPN Provider
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => setProvider('zerotier')}
                  className={`px-4 py-2 rounded font-medium transition-colors ${
                    provider === 'zerotier'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  ZeroTier
                </button>
                <button
                  onClick={() => setProvider('tailscale')}
                  className={`px-4 py-2 rounded font-medium transition-colors ${
                    provider === 'tailscale'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  Tailscale
                </button>
                <button
                  onClick={() => setProvider('wireguard')}
                  className={`px-4 py-2 rounded font-medium transition-colors ${
                    provider === 'wireguard'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  WireGuard
                </button>
              </div>
            </div>

            {provider === 'zerotier' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Network ID
                </label>
                <input
                  type="text"
                  value={networkId}
                  onChange={(e) => setNetworkId(e.target.value)}
                  placeholder="e.g., a0cbf4b62a8e95f3"
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white font-mono"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Get from zerotier.com after creating a network
                </p>
              </div>
            )}

            {provider === 'tailscale' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Auth Key
                </label>
                <input
                  type="password"
                  value={authKey}
                  onChange={(e) => setAuthKey(e.target.value)}
                  placeholder="tskey-auth-..."
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white font-mono"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Generate from tailscale.com/admin/settings/keys
                </p>
              </div>
            )}

            {provider === 'wireguard' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  WireGuard Config
                </label>
                <textarea
                  value={wgConfig}
                  onChange={(e) => setWgConfig(e.target.value)}
                  placeholder="[Interface]&#10;PrivateKey = ...&#10;Address = ...&#10;&#10;[Peer]&#10;PublicKey = ...&#10;Endpoint = ...&#10;AllowedIPs = ..."
                  rows={8}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white font-mono text-sm"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Paste your WireGuard configuration file
                </p>
              </div>
            )}

            <button
              onClick={handleConnect}
              disabled={
                isConnected ||
                connectZeroTierMutation.isPending ||
                connectTailscaleMutation.isPending ||
                connectWireGuardMutation.isPending
              }
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded font-medium transition-colors"
            >
              Connect
            </button>
          </div>
        </div>
      </div>

      {/* Setup Instructions */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Setup Instructions</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h4 className="font-medium text-white mb-2">ZeroTier</h4>
            <ol className="text-sm text-slate-400 space-y-1 list-decimal list-inside">
              <li>Create account at zerotier.com</li>
              <li>Create a network</li>
              <li>Copy the Network ID</li>
              <li>Paste above and connect</li>
              <li>Authorize device in ZeroTier panel</li>
            </ol>
          </div>

          <div>
            <h4 className="font-medium text-white mb-2">Tailscale</h4>
            <ol className="text-sm text-slate-400 space-y-1 list-decimal list-inside">
              <li>Create account at tailscale.com</li>
              <li>Go to Settings → Keys</li>
              <li>Generate auth key</li>
              <li>Paste above and connect</li>
              <li>Device appears in admin panel</li>
            </ol>
          </div>

          <div>
            <h4 className="font-medium text-white mb-2">WireGuard</h4>
            <ol className="text-sm text-slate-400 space-y-1 list-decimal list-inside">
              <li>Set up WireGuard server</li>
              <li>Generate client config</li>
              <li>Paste config above</li>
              <li>Click connect</li>
              <li>Configure peer on server</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}
