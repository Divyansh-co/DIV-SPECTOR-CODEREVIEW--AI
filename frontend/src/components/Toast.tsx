import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface ToastProps {
  toast: ToastMessage | null;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ toast, onClose }) => {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      onClose();
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast, onClose]);

  if (!toast) return null;

  const bgStyle = {
    success: 'border-emerald-500/30 bg-emerald-950/90 text-emerald-300',
    error: 'border-rose-500/30 bg-rose-950/90 text-rose-300',
    info: 'border-accent/30 bg-slate-900/95 text-accent'
  }[toast.type];

  return (
    <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center space-x-2.5 rounded-lg border px-4 py-2.5 text-xs font-mono shadow-xl backdrop-blur-md transition-all ${bgStyle}`}>
      {toast.type === 'success' && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
      {toast.type === 'error' && <AlertCircle className="h-4 w-4 text-rose-400" />}
      <span>{toast.message}</span>
      <button onClick={onClose} className="ml-2 hover:opacity-75">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
};
