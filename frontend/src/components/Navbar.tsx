import React from 'react';
import { 
  Terminal, PlayCircle, FileSearch, Activity, BarChart3, 
  Sun, Moon, Cpu 
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isDark: boolean;
  setIsDark: (dark: boolean) => void;
  activeJobId: string | null;
  jobStatus: string | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isDark,
  setIsDark,
  activeJobId,
  jobStatus
}) => {
  const navItems = [
    { id: 'submit', label: 'Submit Review', icon: PlayCircle },
    { id: 'live', label: 'Live Progress', icon: Terminal, badge: jobStatus === 'running_tools' || jobStatus === 'analyzing' ? 'LIVE' : undefined },
    { id: 'results', label: 'Findings', icon: FileSearch },
    { id: 'traces', label: 'Agent Observability', icon: Activity },
    { id: 'evaluation', label: 'Evaluation Suite', icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-border-subtle bg-bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        
        {/* Left: Brand & Engineer Watermark Badge */}
        <div className="flex items-center space-x-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 border border-accent/30 text-accent">
            <Cpu className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-2">
              <span className="font-semibold tracking-tight text-fg-primary text-sm sm:text-base">
                SPECTER
              </span>
              <span className="rounded bg-accent/10 px-1.5 py-0.5 text-[10px] font-mono font-medium text-accent border border-accent/20">
                AI REVIEWER
              </span>
            </div>
            <div className="flex items-center text-[10px] text-fg-muted space-x-1">
              <span>Engineered by</span>
              <strong className="text-accent font-mono font-medium">Divyansh Mishra</strong>
            </div>
          </div>
        </div>

        {/* Center: Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`relative flex items-center space-x-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-accent/10 text-accent border border-accent/30 shadow-sm'
                    : 'text-fg-secondary hover:bg-bg-overlay hover:text-fg-primary'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden md:inline">{item.label}</span>
                {item.badge && (
                  <span className="ml-1 rounded-full bg-sev-critical/20 border border-sev-critical/40 px-1 py-0.2 text-[9px] font-mono text-sev-critical animate-pulse">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right: Active Job Pill & Theme Switcher */}
        <div className="flex items-center space-x-2.5">
          {activeJobId && (
            <div className="hidden lg:flex items-center space-x-1.5 rounded-full border border-border-subtle bg-bg-base px-2.5 py-1 text-[11px] font-mono text-fg-muted">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
              <span>Job: {activeJobId.slice(0, 8)}...</span>
            </div>
          )}

          <button
            onClick={() => setIsDark(!isDark)}
            title="Toggle theme"
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border-subtle bg-bg-surface text-fg-secondary hover:bg-bg-overlay hover:text-fg-primary transition-colors"
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
