import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { videoApi } from '@/api/client';
import { Play, Square, RefreshCw, Loader2 } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';
import VideoPreview from './VideoPreview';

export default function VideoSettings() {
  const [cameraType, setCameraType] = useState('usb');
  const [device, setDevice] = useState('/dev/video0');
  const [resolution, setResolution] = useState('1280x720');
  const [fps, setFps] = useState(30);
  const [bitrate, setBitrate] = useState(2000);
  const [destination, setDestination] = useState('');
  const [protocol, setProtocol] = useState('udp');

  const { data: camerasData, refetch: refetchCameras } = useQuery({
    queryKey: ['cameras'],
    queryFn: () => videoApi.detectCameras(),
  });

  const { data: statusData } = useQuery({
    queryKey: ['video-status'],
    queryFn: () => videoApi.getStatus(),
    refetchInterval: 2000,
  });

  const startMutation = useMutation({
    mutationFn: () => {
      // For Pi Camera, use the detected camera's device field (rpicam-hello/libcamera-hello)
      // For USB, use the selected device path
      let deviceToUse = device;
      if (cameraType === 'picamera') {
        const piCamera = cameras.find((c: any) => c.type === 'picamera');
        deviceToUse = piCamera?.device || undefined;
      }

      return videoApi.start({
        camera_type: cameraType,
        device: deviceToUse,
        resolution,
        fps,
        bitrate,
        destination: destination || undefined,
        protocol,
      });
    },
    onSuccess: () => {
      showSuccess('Video streaming started successfully');
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to start video streaming');
    },
  });

  const stopMutation = useMutation({
    mutationFn: () => videoApi.stop(),
    onSuccess: () => {
      showSuccess('Video streaming stopped');
    },
    onError: (error: any) => {
      showError(error.response?.data?.message || 'Failed to stop video streaming');
    },
  });

  const isStreaming = statusData?.data?.running;
  const cameras = camerasData?.data?.cameras || [];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent">Video Streaming</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Camera Configuration */}
        <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-6 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-pink-500/10 transition-all duration-300">
          <div className="absolute inset-0 bg-gradient-to-br from-pink-500/5 to-rose-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
          <div className="relative flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Camera Settings</h3>
            <button
              onClick={() => refetchCameras()}
              className="p-2 hover:bg-slate-700 rounded transition-colors text-slate-400"
            >
              <RefreshCw size={18} />
            </button>
          </div>

          <div className="relative space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Camera Type
              </label>
              <select
                value={cameraType}
                onChange={(e) => setCameraType(e.target.value)}
                disabled={isStreaming}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
              >
                <option value="usb">USB Camera</option>
                <option value="picamera">Raspberry Pi Camera</option>
              </select>
            </div>

            {cameraType === 'usb' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Device
                </label>
                <select
                  value={device}
                  onChange={(e) => setDevice(e.target.value)}
                  disabled={isStreaming}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
                >
                  {cameras
                    .filter((c: any) => c.type === 'usb')
                    .map((camera: any) => (
                      <option key={camera.device} value={camera.device}>
                        {camera.name} ({camera.device})
                      </option>
                    ))}
                  <option value="/dev/video0">/dev/video0</option>
                  <option value="/dev/video1">/dev/video1</option>
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Resolution
              </label>
              <select
                value={resolution}
                onChange={(e) => setResolution(e.target.value)}
                disabled={isStreaming}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
              >
                <option value="1920x1080">1920x1080 (1080p)</option>
                <option value="1280x720">1280x720 (720p)</option>
                <option value="640x480">640x480 (480p)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  FPS
                </label>
                <input
                  type="number"
                  value={fps}
                  onChange={(e) => setFps(Number(e.target.value))}
                  disabled={isStreaming}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Bitrate (kbps)
                </label>
                <input
                  type="number"
                  value={bitrate}
                  onChange={(e) => setBitrate(Number(e.target.value))}
                  disabled={isStreaming}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Streaming Configuration */}
        <div className="group relative bg-gradient-to-br from-slate-800/90 to-slate-900/90 backdrop-blur rounded-xl p-6 border border-slate-700/50 shadow-xl hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-300">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
          <h3 className="relative text-lg font-semibold text-white mb-4">
            Streaming Configuration
          </h3>

          <div className="relative space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Protocol
              </label>
              <select
                value={protocol}
                onChange={(e) => setProtocol(e.target.value)}
                disabled={isStreaming}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
              >
                <option value="udp">UDP</option>
                <option value="tcp">TCP</option>
                <option value="hls">HLS</option>
              </select>
            </div>

            {protocol !== 'hls' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Destination (host:port)
                </label>
                <input
                  type="text"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g., 192.168.1.100:5600"
                  disabled={isStreaming}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white disabled:opacity-50"
                />
              </div>
            )}

            <div className="pt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400">Status:</span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    isStreaming
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {isStreaming ? 'Streaming' : 'Stopped'}
                </span>
              </div>
            </div>

            <div className="relative flex gap-3">
              <button
                onClick={() => startMutation.mutate()}
                disabled={isStreaming || startMutation.isPending}
                className="relative flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-lg font-semibold shadow-lg hover:shadow-green-500/50 disabled:shadow-none transition-all duration-300 overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-emerald-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300" />
                {startMutation.isPending ? (
                  <Loader2 size={18} className="animate-spin relative z-10" />
                ) : (
                  <Play size={18} className="relative z-10" />
                )}
                <span className="relative z-10">{startMutation.isPending ? 'Starting...' : 'Start Streaming'}</span>
              </button>
              <button
                onClick={() => stopMutation.mutate()}
                disabled={!isStreaming || stopMutation.isPending}
                className="relative flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-lg font-semibold shadow-lg hover:shadow-red-500/50 disabled:shadow-none transition-all duration-300 overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-red-400 to-rose-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300" />
                {stopMutation.isPending ? (
                  <Loader2 size={18} className="animate-spin relative z-10" />
                ) : (
                  <Square size={18} className="relative z-10" />
                )}
                <span className="relative z-10">{stopMutation.isPending ? 'Stopping...' : 'Stop Streaming'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Detected Cameras */}
      {cameras.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Detected Cameras</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {cameras.map((camera: any) => (
              <div key={camera.device} className="bg-slate-700 rounded p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <div className="font-medium text-white">{camera.name}</div>
                </div>
                <div className="text-sm text-slate-400">{camera.device}</div>
                <div className="text-xs text-slate-500 mt-1">
                  {camera.type === 'usb' ? 'USB Camera' : 'Raspberry Pi Camera'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Video Preview */}
      {isStreaming && (
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Live Preview</h3>
          {protocol === 'hls' ? (
            <VideoPreview />
          ) : (
            <div className="bg-slate-900 rounded p-6 text-center">
              <div className="text-slate-400 mb-2">
                Preview only available for HLS streaming
              </div>
              <div className="text-sm text-slate-500">
                Change protocol to "HLS" to see live preview in browser
              </div>
              <div className="text-xs text-slate-600 mt-4">
                For UDP/TCP streams, use a ground station like QGroundControl or Mission Planner
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
