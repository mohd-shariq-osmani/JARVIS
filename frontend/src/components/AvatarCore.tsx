import { useEffect, useRef } from 'react';

type VoiceState = 'SLEEPING' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'QUEUED';

interface AvatarCoreProps {
  voiceState: VoiceState;
}

/**
 * AvatarCore renders the Hiyori Live2D model inside a transparent iframe.
 * State changes are passed to the iframe via postMessage so the avatar reacts
 * to JARVIS's voice state (idle breathing → head tilt → lip sync → etc.).
 */
const AvatarCore: React.FC<AvatarCoreProps> = ({ voiceState }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const prevState = useRef<VoiceState>('SLEEPING');

  // Send state to iframe whenever voiceState changes
  useEffect(() => {
    if (voiceState === prevState.current) return;
    prevState.current = voiceState;

    const send = () => {
      iframeRef.current?.contentWindow?.postMessage(
        { type: 'JARVIS_STATE', state: voiceState },
        '*'
      );
    };

    // Retry a few times in case iframe hasn't finished loading yet
    send();
    const t1 = setTimeout(send, 300);
    const t2 = setTimeout(send, 700);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [voiceState]);

  // On iframe load, immediately sync current state
  const handleLoad = () => {
    setTimeout(() => {
      iframeRef.current?.contentWindow?.postMessage(
        { type: 'JARVIS_STATE', state: voiceState },
        '*'
      );
    }, 500);
  };

  // Glow color changes with state
  const glowColor =
    voiceState === 'LISTENING'  ? 'rgba(185,228,255,0.18)' :
    voiceState === 'SPEAKING'   ? 'rgba(16,185,129,0.15)'  :
    voiceState === 'PROCESSING' ? 'rgba(255,255,255,0.08)' :
    'transparent';

  return (
    <div
      className="relative flex items-end justify-center"
      style={{ width: '100%', height: '340px', maxWidth: '340px' }}
    >
      {/* Ambient glow ring behind avatar */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-48 h-12 rounded-full blur-2xl transition-all duration-700 pointer-events-none"
        style={{ background: glowColor }}
      />

      {/* Corner scan lines — subtle JARVIS aesthetic */}
      <div className="absolute top-0 left-0 w-5 h-5 border-t border-l border-white/10 pointer-events-none" />
      <div className="absolute top-0 right-0 w-5 h-5 border-t border-r border-white/10 pointer-events-none" />

      {/* The actual Live2D iframe */}
      <iframe
        ref={iframeRef}
        src="/live2d-viewer.html"
        onLoad={handleLoad}
        title="JARVIS Avatar"
        className="w-full h-full border-0 bg-transparent"
        style={{ background: 'transparent', pointerEvents: 'none' }}
        sandbox="allow-scripts allow-same-origin"
      />

      {/* State label badge */}
      {voiceState !== 'SLEEPING' && (
        <div
          className="absolute bottom-2 left-1/2 -translate-x-1/2 font-mono text-[8px] tracking-[0.2em] uppercase px-2 py-0.5 rounded-full border transition-all duration-500"
          style={{
            color: voiceState === 'LISTENING'  ? '#b9e4ff' :
                   voiceState === 'SPEAKING'   ? '#10b981' : '#74777d',
            borderColor: voiceState === 'LISTENING'  ? 'rgba(185,228,255,0.3)' :
                         voiceState === 'SPEAKING'   ? 'rgba(16,185,129,0.3)'  :
                         'rgba(255,255,255,0.08)',
            background: 'rgba(8,9,10,0.7)',
          }}
        >
          {voiceState}
        </div>
      )}
    </div>
  );
};

export default AvatarCore;
