import { LayoutDashboard, ArrowRightLeft, Link, User } from "lucide-react";
import { Link as RouterLink, useLocation } from "react-router-dom";
import { cn } from "../../utils/cn";

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Transações', href: '/transactions', icon: ArrowRightLeft },
  { name: 'Conexões', href: '/connections', icon: Link },
  { name: 'Perfil', href: '/profile', icon: User },
];

export function BottomNav() {
  const location = useLocation();

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-gray-900 border-t border-gray-800 md:hidden pb-[env(safe-area-inset-bottom)]">
      <div className="grid h-full max-w-lg grid-cols-4 mx-auto font-medium">
        {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
                <RouterLink
                    key={item.name}
                    to={item.href}
                    className={cn(
                        "inline-flex flex-col items-center justify-center m-1 rounded-xl transition-all",
                         isActive 
                            ? "bg-gray-800 text-white shadow-sm ring-1 ring-gray-700" 
                            : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                    )}
                >
                    <item.icon 
                        className={cn("w-5 h-5 mb-1 transition-colors", isActive ? "text-emerald-400" : "text-gray-400 group-hover:text-gray-300")} 
                    />
                    <span className="text-[10px] font-medium">{item.name}</span>
                </RouterLink>
            )
        })}
      </div>
    </div>
  );
}
