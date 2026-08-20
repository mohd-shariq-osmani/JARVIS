import { useEffect, useRef } from 'react';
import * as PIXI from 'pixi.js';

type VoiceState = 'SLEEPING' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'QUEUED';

interface Props {
  voiceState: VoiceState;
}

/**
 * AvatarCore — renders the Hiyori Live2D model directly on a PIXI canvas.
 *
 * Sequencing:
 *  1. index.html loads /live2d/core/live2dcubismcore.min.js synchronously
 *     → window.Live2DCubismCore is available immediately
 *  2. This component sets window.PIXI = PIXI (required by pixi-live2d-display)
 *  3. pixi-live2d-display is imported dynamically so it runs after step 2
 *  4. Hiyori model is loaded from /public/live2d/hiyori/ (local, no CDN)
 */
const AvatarCore: React.FC<Props> = ({ voiceState }) => {
  const wrapRef    = useRef<HTMLDivElement>(null);
  const modelRef   = useRef<any>(null);
  const appRef     = useRef<any>(null);
  const speakTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Init ────────────────────────────────────────────────────────────────────
  useEffect(() => {
    let destroyed = false;

    const init = async () => {
      try {
        // pixi-live2d-display reads window.PIXI internally — must be set first
        (window as any).PIXI = PIXI;

        // Dynamic import so it runs *after* window.PIXI is set
        const { Live2DModel } = await import('pixi-live2d-display/cubism4');

        if (destroyed || !wrapRef.current) return;

        const wrap = wrapRef.current;
        const W = wrap.clientWidth  || 300;
        const H = wrap.clientHeight || 420;

        const app = new PIXI.Application({
          backgroundAlpha: 0,
          width:  W,
          height: H,
          resolution: window.devicePixelRatio || 1,
          autoDensity: true,
          antialias: true,
        });

        wrap.appendChild(app.view as HTMLCanvasElement);
        appRef.current = app;

        const model = await Live2DModel.from(
          '/live2d/hiyori/Hiyori.model3.json',
          { autoInteract: false }
        );

        if (destroyed) { model.destroy(); return; }

        app.stage.addChild(model);

        // Scale to fit height, anchor at bottom-centre
        const scale = (H / model.height) * 0.95;
        model.scale.set(scale);
        model.anchor.set(0.5, 1.0);
        model.x = W / 2;
        model.y = H;

        modelRef.current = model;
        model.motion('Idle', 0, 1);

      } catch (err) {
        console.error('[AvatarCore] init failed:', err);
      }
    };

    init();

    return () => {
      destroyed = true;
      clearInterval(speakTimer.current ?? undefined);
      appRef.current?.destroy(true, { children: true });
      appRef.current  = null;
      modelRef.current = null;
    };
  }, []);

  // ── React to voice state ─────────────────────────────────────────────────
  useEffect(() => {
    const model = modelRef.current;
    clearInterval(speakTimer.current ?? undefined);
    speakTimer.current = null;

    if (!model) return;

    if (voiceState === 'SPEAKING') {
      model.motion('TapBody', 0, 3);

      // Oscillate mouth parameter to simulate lip-sync
      let phase = 0;
      speakTimer.current = setInterval(() => {
        try {
          phase += 0.22;
          const v = Math.abs(Math.sin(phase)) * 0.85;
          model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', v);
        } catch { /* model may not be ready yet */ }
      }, 50);

    } else {
      // Reset mouth
      try {
        model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', 0);
      } catch {}

      const idxMap: Record<VoiceState, number> = {
        SLEEPING:   0,
        LISTENING:  1,
        PROCESSING: 2,
        QUEUED:     0,
        SPEAKING:   0,
      };
      model.motion('Idle', idxMap[voiceState], 1);
    }
  }, [voiceState]);

  // ── Glow colour ──────────────────────────────────────────────────────────
  const glowColor =
    voiceState === 'LISTENING'  ? 'rgba(185,228,255,0.22)' :
    voiceState === 'SPEAKING'   ? 'rgba(16,185,129,0.18)'  :
    voiceState === 'PROCESSING' ? 'rgba(255,255,255,0.07)' :
    'transparent';

  return (
    <div className="relative flex flex-col items-center" style={{ width: 300, height: 420 }}>
      {/* Ambient glow under feet */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-40 h-10 rounded-full blur-2xl pointer-events-none transition-all duration-700"
        style={{ background: glowColor }}
      />
      {/* Canvas mount point */}
      <div ref={wrapRef} className="w-full h-full" style={{ background: 'transparent' }} />
    </div>
  );
};

export default AvatarCore;
