import { Home, CreditCard, User, LogOut, Link as LinkIcon, Brain, Shield } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { AuthService } from "../services/auth";
import { DownloadCloud } from "lucide-react";
import { cn } from "../utils/cn";
import { telemetry } from "../services/telemetry";

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Transações', href: '/transactions', icon: CreditCard },
  { name: 'Inteligência', href: '/intelligence', icon: Brain },
  { name: 'Conexões', href: '/connections', icon: LinkIcon },
  { name: 'Perfil', href: '/profile', icon: User },
];

export function Sidebar() {
  const location = useLocation();
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  useEffect(() => {
    const handler = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  // Telemetria de Navegação
  useEffect(() => {
    telemetry.logAction('view_page', { path: location.pathname });
  }, [location.pathname]);

  const handleInstallClick = () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult: any) => {
            if (choiceResult.outcome === 'accepted') {
                setDeferredPrompt(null);
            }
        });
    }
  };

  return (
    <div className="hidden md:flex h-full w-auto min-w-[16rem] flex-col bg-surface-card text-text-primary border-r border-border transition-all duration-300">
      <div className="flex h-16 items-center px-6 gap-3 border-b border-border">
        <Link to="/landing" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="relative h-12 w-12 overflow-hidden rounded-xl shadow-black/50 shadow-md ring-1 ring-white/20 shrink-0 group">
                <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <img src="/pwa-512x512.png" alt="Icon" className="h-full w-full object-cover transform group-hover:scale-105 transition-transform duration-500" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight whitespace-nowrap drop-shadow-sm">
                <span className="text-transparent bg-clip-text bg-gradient-to-br from-white to-gray-400">Budget</span>
                <span className="text-emerald-400 drop-shadow-glow">IA</span>
            </h1>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
                  className={cn(
                    "flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all mb-1",
                    isActive
                      ? "bg-surface-hover text-emerald-400 shadow-sm ring-1 ring-border-hover"
                      : "text-text-secondary hover:text-text-primary hover:bg-surface-hover/50"
                  )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                  isActive ? "text-emerald-400 drop-shadow-glow-subtle" : "text-gray-400 group-hover:text-text-primary"
                )}
              />
              <span className={cn(isActive && "drop-shadow-glow-subtle")}>{item.name}</span>
            </Link>
          );
        })}
        {deferredPrompt && (
            <button
                onClick={handleInstallClick}
                className="group flex w-full items-center rounded-md px-3 py-2 text-sm font-medium text-emerald-400 hover:bg-emerald-900/20 hover:text-emerald-300 transition-colors mt-4 border border-emerald-500/20"
            >
                <DownloadCloud className="mr-3 h-5 w-5 flex-shrink-0" />
                Instalar App
            </button>
        )}

        {localStorage.getItem('budgetia_user_role') === 'admin' && (
            <Link
                to="/admin"
                className={cn(
                    "flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all mb-1 mt-4 border border-purple-500/20",
                    location.pathname === '/admin'
                        ? "bg-purple-500/20 text-purple-400 shadow-sm ring-1 ring-purple-500/30"
                        : "text-purple-400/70 hover:text-purple-400 hover:bg-purple-500/10"
                )}
            >
                <Shield className="mr-3 h-5 w-5 flex-shrink-0" />
                <span>Administração</span>
            </Link>
        )}

        

      </nav>
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center justify-between">
            <div className="flex items-center min-w-0">
                <div className="h-8 w-8 rounded-full bg-emerald-500 flex items-center justify-center text-xs font-bold text-white shrink-0">
                    {localStorage.getItem('budgetia_user_id')?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="ml-3 truncate">
                    <p className="text-sm font-medium text-text-primary truncate">
                        {localStorage.getItem('budgetia_user_id') || 'Usuário'}
                    </p>
                    <p className="text-xs text-gray-500">Online</p>
                </div>
            </div>
            <button 
                onClick={() => {
                    if(confirm("Deseja sair?")) {
                        AuthService.logout();
                    }
                }}
                className="text-gray-500 hover:text-red-400 p-1.5 rounded-md hover:bg-gray-800 transition-colors"
                title="Sair"
            >
                <LogOut size={16} />
            </button>
        </div>
      </div>
    </div>
  );
}
