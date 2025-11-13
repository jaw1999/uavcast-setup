import { useEffect, useRef, useState } from 'react';
import { Play, AlertCircle } from 'lucide-react';

interface Props {
  videoUrl?: string;
}

export default function VideoPreview({ videoUrl = '/hls/stream.webm' }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Simple WebM video loading
    video.src = videoUrl + '?t=' + Date.now(); // Cache busting

    video.addEventListener('loadedmetadata', () => {
      setError(null);
      video.play().catch((err) => {
        console.error('Auto-play failed:', err);
        setIsPlaying(false);
      });
    });

    video.addEventListener('error', (e) => {
      console.error('Video error:', e);
      setError('Error loading video stream');
    });

    return () => {
      video.removeEventListener('loadedmetadata', () => {});
      video.removeEventListener('error', () => {});
    };
  }, [videoUrl]);

  const handlePlay = () => {
    if (videoRef.current) {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
      <div className="relative aspect-video bg-black">
        <video
          ref={videoRef}
          className="w-full h-full"
          controls
          muted
          playsInline
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80">
            <div className="text-center text-white">
              <AlertCircle size={48} className="mx-auto mb-2 text-red-400" />
              <div className="text-lg font-medium mb-2">{error}</div>
              <div className="text-sm text-slate-400">
                Make sure video streaming is started and HLS protocol is selected
              </div>
            </div>
          </div>
        )}

        {!isPlaying && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <button
              onClick={handlePlay}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 transition-colors"
            >
              <Play size={32} />
            </button>
          </div>
        )}
      </div>

      <div className="p-3 bg-slate-900 text-xs text-slate-400">
        <div>Video Stream: {videoUrl}</div>
        <div className="mt-1">
          Status: {isPlaying ? '▶ Playing' : error ? '✗ Error' : '⏸ Paused'}
        </div>
      </div>
    </div>
  );
}
