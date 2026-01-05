import { Link as RouterLink, useLocation } from "react-router-dom";
import { cn } from "../../utils/cn";
import { navigationItems } from "../../config/navigation";

export function BottomNav() {
  const location = useLocation();

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-surface-card border-t border-border md:hidden pb-[env(safe-area-inset-bottom)]">
      <div className="grid h-full w-full grid-flow-col auto-cols-fr mx-auto font-medium">
        {navigationItems.map((item) => {
            const isActive = location.pathname === item.href;
            return (
                <RouterLink
                    key={item.name}
                    to={item.href}
                    className={cn(
                        "inline-flex flex-col items-center justify-center m-1 rounded-xl transition-all",
                         isActive 
                            ? "bg-surface-hover text-emerald-400 shadow-sm ring-1 ring-border-hover" 
                            : "text-text-secondary hover:text-text-primary hover:bg-surface-hover/50"
                    )}
                >
                    <item.icon 
                        className={cn("w-5 h-5 mb-1 transition-colors", isActive ? "text-emerald-500 drop-shadow-glow-subtle" : "text-text-secondary group-hover:text-text-primary")} 
                    />
                    <span className={cn("text-[10px] font-medium", isActive && "drop-shadow-glow-subtle")}>{item.name}</span>
                </RouterLink>
            )
        })}
      </div>
    </div>
  );
}
