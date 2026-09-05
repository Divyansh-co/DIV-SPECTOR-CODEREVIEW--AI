import React from 'react';
import { ShieldCheck, Lock } from 'lucide-react';

export const WatermarkOverlay: React.FC = () => {
  // Generate 24 repeating watermark tokens to tile diagonally
  const stamps = Array.from({ length: 24 });

  return (
    <>
      {/* Repeating Diagonal Background Watermark */}
      <div className="watermark-overlay pointer-events-none" aria-hidden="true" />
      <div className="watermark-canvas-grid pointer-events-none" aria-hidden="true">
        {stamps.map((_, i) => (
          <div key={i} className="watermark-stamp select-none opacity-40">
            DIVYANSH MISHRA • SPECTER AI • PROPRIETARY
          </div>
        ))}
      </div>

      {/* Persistent Bottom Security & Ownership Badge */}
      <div className="fixed bottom-3 right-4 z-40 flex items-center space-x-2 rounded-full border border-border-subtle bg-bg-surface/90 px-3 py-1.5 text-xs text-fg-muted shadow-lg backdrop-blur-md select-none">
        <ShieldCheck className="h-3.5 w-3.5 text-accent" />
        <span className="font-mono text-[11px] tracking-wide">
          Engineered by <strong className="text-fg-primary font-semibold">Divyansh Mishra</strong>
        </span>
        <span className="text-border-highlight">|</span>
        <span className="inline-flex items-center text-[10px] text-accent">
          <Lock className="mr-1 h-2.5 w-2.5" /> All Rights Reserved
        </span>
      </div>
    </>
  );
};
