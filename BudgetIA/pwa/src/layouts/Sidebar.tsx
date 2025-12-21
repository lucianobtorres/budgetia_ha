import { Home, MessageSquare, CreditCard, PieChart, User, Bell, LogOut } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "../utils/cn";

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Chat IA', href: '/chat', icon: MessageSquare },
  { name: 'Transações', href: '/transactions', icon: CreditCard },
  { name: 'Orçamentos', href: '/budgets', icon: PieChart },
  { name: 'Notificações', href: '/notifications', icon: Bell },
  { name: 'Perfil', href: '/profile', icon: User },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <div className="flex h-screen w-64 flex-col bg-gray-900 text-white border-r border-gray-800">
      <div className="flex h-16 items-center px-6">
        <h1 className="text-xl font-bold text-emerald-400 font-sans tracking-tight">💰 BudgetIA</h1>
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
                        localStorage.removeItem('budgetia_user_id');
                        window.location.reload();
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
