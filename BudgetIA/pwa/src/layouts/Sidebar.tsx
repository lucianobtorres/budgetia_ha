import { Home, CreditCard, User, LogOut, Link as LinkIcon } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { AuthService } from "../services/auth";
import { DownloadCloud } from "lucide-react";
import { cn } from "../utils/cn";
import { telemetry } from "../services/telemetry";

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Transações', href: '/transactions', icon: CreditCard },
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
    <div className="hidden md:flex h-screen w-auto min-w-[16rem] flex-col bg-gray-900 text-white border-r border-gray-800 transition-all duration-300">
      <div className="flex h-16 items-center px-6 gap-3 border-b border-gray-800/50">
        <div className="relative h-9 w-9 overflow-hidden rounded-lg shadow-black/50 shadow-sm ring-1 ring-white/10 shrink-0">
             <img src="/pwa-512x512.png" alt="Icon" className="h-full w-full object-cover" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-white whitespace-nowrap">
            Budget<span className="text-emerald-500">IA</span>
        </h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-800 text-emerald-400"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              )}
            >
              <item.icon
                className={cn(
                  "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                  isActive ? "text-emerald-400" : "text-gray-400 group-hover:text-white"
                )}
              />
              {item.name}
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

        

      </nav>
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center justify-between">
            <div className="flex items-center min-w-0">
                <div className="h-8 w-8 rounded-full bg-emerald-500 flex items-center justify-center text-xs font-bold text-white shrink-0">
                    {localStorage.getItem('budgetia_user_id')?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="ml-3 truncate">
                    <p className="text-sm font-medium text-white truncate">
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
